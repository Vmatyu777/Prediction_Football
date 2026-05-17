from __future__ import annotations

from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.features.feature_registry import V1_FEATURES  # noqa: E402
from src.models.evaluate_models import evaluate_classifier  # noqa: E402
from src.models.train_outcome import build_time_split  # noqa: E402


FEATURE_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_features_v2.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "outcome"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables" / "outcome"

TARGET_COLUMN = "Target_Outcome"
CATEGORICAL_FEATURES = ["Division", "HomeTeam", "AwayTeam"]
RANDOM_STATE = 42

C_VALUES = [0.05, 0.1, 0.3, 1.0, 3.0]
CLASS_WEIGHT_CONFIGS = {
    "none": None,
    "balanced": "balanced",
    "draw_1_2": {"H": 1.0, "D": 1.2, "A": 1.0},
    "draw_1_4": {"H": 1.0, "D": 1.4, "A": 1.0},
    "draw_1_6": {"H": 1.0, "D": 1.6, "A": 1.0},
}
DRAW_BOOST_VALUES = [1.0, 1.05, 1.10, 1.15, 1.20, 1.30]
DRAW_THRESHOLD_VALUES = [None, 0.25, 0.28, 0.30, 0.32, 0.35, 0.38, 0.40]


def build_preprocessor() -> ColumnTransformer:
    numeric_features = [feature for feature in V1_FEATURES if feature not in CATEGORICAL_FEATURES]
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), numeric_features),
        ],
        remainder="drop",
    )


def build_logistic_model(c_value: float, class_weight) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "model",
                LogisticRegression(
                    C=c_value,
                    class_weight=class_weight,
                    solver="lbfgs",
                    penalty="l2",
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def predict_with_draw_rule(
    *,
    probabilities: pd.DataFrame,
    draw_boost: float,
    draw_threshold: float | None,
) -> pd.Series:
    adjusted = probabilities.copy()
    adjusted["D"] = adjusted["D"] * draw_boost

    predictions = adjusted.idxmax(axis=1)
    if draw_threshold is not None:
        predictions = predictions.where(probabilities["D"] < draw_threshold, "D")
    return predictions


def evaluate_model_on_splits(
    *,
    model_name: str,
    model: Pipeline,
    splits: dict[str, pd.DataFrame],
    feature_names: list[str],
    draw_boost: float = 1.0,
    draw_threshold: float | None = None,
) -> list[dict[str, float | str]]:
    rows = []
    for split_name, split_data in splits.items():
        X_split = split_data[feature_names]
        y_split = split_data[TARGET_COLUMN]
        probabilities = pd.DataFrame(
            model.predict_proba(X_split),
            columns=model.named_steps["model"].classes_,
            index=y_split.index,
        )
        y_pred = predict_with_draw_rule(
            probabilities=probabilities,
            draw_boost=draw_boost,
            draw_threshold=draw_threshold,
        )
        row = evaluate_classifier(
            model_name=model_name,
            split_name=split_name,
            y_true=y_split,
            y_pred=y_pred,
        )
        row["draw_boost"] = draw_boost
        row["draw_threshold"] = "none" if draw_threshold is None else draw_threshold
        rows.append(row)
    return rows


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(FEATURE_DATA_PATH, parse_dates=["MatchDateParsed"])
    data = data.sort_values("MatchDateParsed").reset_index(drop=True)
    splits = build_time_split(data)

    X_train = splits["train"][V1_FEATURES]
    y_train = splits["train"][TARGET_COLUMN]
    X_validation = splits["validation"][V1_FEATURES]
    y_validation = splits["validation"][TARGET_COLUMN]

    tuning_rows = []
    fitted_models: dict[str, Pipeline] = {}

    for c_value in C_VALUES:
        for class_weight_name, class_weight in CLASS_WEIGHT_CONFIGS.items():
            model_name = f"logistic_c_{str(c_value).replace('.', '_')}__{class_weight_name}"
            model = build_logistic_model(c_value, class_weight)
            model.fit(X_train, y_train)
            fitted_models[model_name] = model

            for row in evaluate_model_on_splits(
                model_name=model_name,
                model=model,
                splits={"train": splits["train"], "validation": splits["validation"]},
                feature_names=V1_FEATURES,
            ):
                row["C"] = c_value
                row["class_weight"] = class_weight_name
                row["experiment_type"] = "logistic_tuning"
                tuning_rows.append(row)

    tuning_metrics = pd.DataFrame(tuning_rows)
    tuning_metrics.to_csv(TABLES_DIR / "outcome_logistic_tuning_metrics.csv", index=False)

    validation_metrics = tuning_metrics[tuning_metrics["split"] == "validation"].copy()
    eligible = validation_metrics[
        (validation_metrics["macro_f1"] >= 0.485)
        & (validation_metrics["draw_recall"] >= 0.30)
    ]
    selection_pool = eligible if not eligible.empty else validation_metrics
    selected_models = (
        selection_pool.sort_values(["macro_f1", "accuracy"], ascending=False)
        .head(5)["model"]
        .tolist()
    )

    threshold_rows = []
    for model_name in selected_models:
        model = fitted_models[model_name]
        validation_probabilities = pd.DataFrame(
            model.predict_proba(X_validation),
            columns=model.named_steps["model"].classes_,
            index=y_validation.index,
        )

        for draw_boost in DRAW_BOOST_VALUES:
            for draw_threshold in DRAW_THRESHOLD_VALUES:
                y_pred = predict_with_draw_rule(
                    probabilities=validation_probabilities,
                    draw_boost=draw_boost,
                    draw_threshold=draw_threshold,
                )
                row = evaluate_classifier(
                    model_name=model_name,
                    split_name="validation",
                    y_true=y_validation,
                    y_pred=y_pred,
                )
                row["draw_boost"] = draw_boost
                row["draw_threshold"] = "none" if draw_threshold is None else draw_threshold
                row["experiment_type"] = "threshold_tuning"
                threshold_rows.append(row)

    threshold_metrics = pd.DataFrame(threshold_rows)
    threshold_metrics.to_csv(TABLES_DIR / "outcome_logistic_threshold_validation.csv", index=False)

    threshold_eligible = threshold_metrics[
        (threshold_metrics["accuracy"] >= 0.506)
        & (threshold_metrics["macro_f1"] >= 0.486)
        & (threshold_metrics["draw_recall"] >= 0.30)
    ]
    threshold_pool = threshold_eligible if not threshold_eligible.empty else threshold_metrics
    best_threshold = threshold_pool.sort_values(
        ["macro_f1", "accuracy", "draw_recall"],
        ascending=False,
    ).iloc[0]

    best_model_name = best_threshold["model"]
    best_model = fitted_models[best_model_name]
    draw_threshold = best_threshold["draw_threshold"]
    draw_threshold_value = None if draw_threshold == "none" else float(draw_threshold)

    final_rows = evaluate_model_on_splits(
        model_name=f"{best_model_name}__threshold_tuned",
        model=best_model,
        splits=splits,
        feature_names=V1_FEATURES,
        draw_boost=float(best_threshold["draw_boost"]),
        draw_threshold=draw_threshold_value,
    )
    final_metrics = pd.DataFrame(final_rows)
    final_metrics["experiment_type"] = "selected_threshold_tuned"
    final_metrics.to_csv(TABLES_DIR / "outcome_logistic_selected_threshold_metrics.csv", index=False)

    best_base_name = (
        validation_metrics.sort_values(["macro_f1", "accuracy"], ascending=False)
        .iloc[0]["model"]
    )
    best_base_model = fitted_models[best_base_name]
    best_base_rows = evaluate_model_on_splits(
        model_name=f"{best_base_name}__untuned_threshold",
        model=best_base_model,
        splits=splits,
        feature_names=V1_FEATURES,
    )
    best_base_metrics = pd.DataFrame(best_base_rows)
    best_base_metrics["experiment_type"] = "selected_logistic_tuned"

    comparison = pd.concat([best_base_metrics, final_metrics], ignore_index=True)
    existing_metrics_path = TABLES_DIR / "outcome_model_metrics.csv"
    if existing_metrics_path.exists():
        existing = pd.read_csv(existing_metrics_path)
        selected_existing = existing[
            (existing["split"].isin(["validation", "test"]))
            & (
                (
                    (existing["feature_set"] == "v1_only")
                    & (existing["model"].isin(["logistic_regression", "catboost_classifier"]))
                )
                | (
                    (existing["feature_set"] == "v1_corners_yellow")
                    & (existing["model"] == "catboost_classifier")
                )
            )
        ].copy()
        selected_existing["experiment_type"] = "previous_reference"
        selected_existing["draw_boost"] = 1.0
        selected_existing["draw_threshold"] = "none"
        comparison = pd.concat([selected_existing, comparison], ignore_index=True, sort=False)

    comparison.to_csv(TABLES_DIR / "outcome_final_controlled_comparison.csv", index=False)
    joblib.dump(best_model, MODELS_DIR / "logistic_regression_controlled_best.joblib")

    print("Logistic controlled tuning completed.")
    print("Best untuned LogisticRegression:")
    print(
        validation_metrics.sort_values(["macro_f1", "accuracy"], ascending=False)
        .head(5)
        .to_string(index=False)
    )
    print("Best threshold rule on validation:")
    print(best_threshold.to_frame().transpose().to_string(index=False))
    print("Final comparison:")
    print(
        comparison[
            [
                "experiment_type",
                "model",
                "split",
                "accuracy",
                "balanced_accuracy",
                "macro_f1",
                "draw_recall",
                "draw_boost",
                "draw_threshold",
            ]
        ]
        .sort_values(["split", "macro_f1"], ascending=[True, False])
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
