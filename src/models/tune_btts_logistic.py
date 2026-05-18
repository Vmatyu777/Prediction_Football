from __future__ import annotations

from pathlib import Path
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.features.feature_registry import BTTS_FEATURE_SETS  # noqa: E402
from src.models.train_btts import TARGET_COLUMN, build_time_split  # noqa: E402


FEATURE_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_features_v2.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "btts"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables" / "btts"

CATEGORICAL_FEATURES = ["Division", "HomeTeam", "AwayTeam"]
RANDOM_STATE = 42

C_VALUES = [0.05, 0.1, 0.3, 1.0, 3.0]
CLASS_WEIGHT_CONFIGS = {
    "none": None,
    "balanced": "balanced",
    "no_1_2": {0: 1.2, 1: 1.0},
    "no_1_4": {0: 1.4, 1: 1.0},
    "yes_1_2": {0: 1.0, 1: 1.2},
}
THRESHOLD_VALUES = [0.40, 0.45, 0.48, 0.50, 0.52, 0.55, 0.60]


def build_preprocessor(feature_names: list[str]) -> ColumnTransformer:
    categorical_features = [feature for feature in CATEGORICAL_FEATURES if feature in feature_names]
    numeric_features = [feature for feature in feature_names if feature not in categorical_features]
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numeric", StandardScaler(), numeric_features),
        ],
        remainder="drop",
    )


def build_logistic_model(c_value: float, class_weight) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(BTTS_FEATURE_SETS["v1_only"])),
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


def predict_by_threshold(model: Pipeline, X: pd.DataFrame, threshold: float) -> pd.Series:
    probabilities = model.predict_proba(X)[:, 1]
    return pd.Series((probabilities >= threshold).astype(int), index=X.index)


def evaluate_predictions(
    *,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
    threshold: float,
) -> dict[str, float | str]:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    no_recall = matrix[0, 0] / matrix[0].sum() if matrix[0].sum() else 0.0
    yes_recall = matrix[1, 1] / matrix[1].sum() if matrix[1].sum() else 0.0
    return {
        "model": model_name,
        "split": split_name,
        "threshold": threshold,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "no_recall": no_recall,
        "yes_recall": yes_recall,
        "true_no_pred_no": int(matrix[0, 0]),
        "true_no_pred_yes": int(matrix[0, 1]),
        "true_yes_pred_no": int(matrix[1, 0]),
        "true_yes_pred_yes": int(matrix[1, 1]),
    }


def evaluate_model_on_splits(
    *,
    model_name: str,
    model: Pipeline,
    splits: dict[str, pd.DataFrame],
    feature_names: list[str],
    threshold: float,
) -> list[dict[str, float | str]]:
    rows = []
    for split_name, split_data in splits.items():
        X_split = split_data[feature_names]
        y_split = split_data[TARGET_COLUMN]
        y_pred = predict_by_threshold(model, X_split, threshold)
        rows.append(
            evaluate_predictions(
                model_name=model_name,
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
                threshold=threshold,
            )
        )
    return rows


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    feature_names = BTTS_FEATURE_SETS["v1_only"]
    data = pd.read_csv(FEATURE_DATA_PATH, parse_dates=["MatchDateParsed"])
    data = data.sort_values("MatchDateParsed").reset_index(drop=True)
    splits = build_time_split(data)

    X_train = splits["train"][feature_names]
    y_train = splits["train"][TARGET_COLUMN]
    X_validation = splits["validation"][feature_names]
    y_validation = splits["validation"][TARGET_COLUMN]

    fitted_models: dict[str, Pipeline] = {}
    tuning_rows = []

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
                feature_names=feature_names,
                threshold=0.50,
            ):
                row["C"] = c_value
                row["class_weight"] = class_weight_name
                row["experiment_type"] = "logistic_tuning"
                tuning_rows.append(row)

    tuning_metrics = pd.DataFrame(tuning_rows)
    tuning_metrics.to_csv(TABLES_DIR / "btts_logistic_tuning_metrics.csv", index=False)

    validation_metrics = tuning_metrics[tuning_metrics["split"] == "validation"].copy()
    eligible = validation_metrics[
        (validation_metrics["balanced_accuracy"] >= 0.52)
        & (validation_metrics["no_recall"] >= 0.35)
        & (validation_metrics["yes_recall"] >= 0.50)
    ]
    selection_pool = eligible if not eligible.empty else validation_metrics
    selected_models = (
        selection_pool.sort_values(["balanced_accuracy", "f1"], ascending=False)
        .head(5)["model"]
        .tolist()
    )

    threshold_rows = []
    for model_name in selected_models:
        model = fitted_models[model_name]
        for threshold in THRESHOLD_VALUES:
            y_pred = predict_by_threshold(model, X_validation, threshold)
            row = evaluate_predictions(
                model_name=model_name,
                split_name="validation",
                y_true=y_validation,
                y_pred=y_pred,
                threshold=threshold,
            )
            row["experiment_type"] = "threshold_tuning"
            threshold_rows.append(row)

    threshold_metrics = pd.DataFrame(threshold_rows)
    threshold_metrics.to_csv(TABLES_DIR / "btts_logistic_threshold_validation.csv", index=False)

    threshold_eligible = threshold_metrics[
        (threshold_metrics["balanced_accuracy"] >= 0.53)
        & (threshold_metrics["no_recall"] >= 0.40)
        & (threshold_metrics["yes_recall"] >= 0.50)
    ]
    threshold_pool = threshold_eligible if not threshold_eligible.empty else threshold_metrics
    best_threshold = threshold_pool.sort_values(
        ["balanced_accuracy", "f1", "accuracy"],
        ascending=False,
    ).iloc[0]

    best_model_name = best_threshold["model"]
    best_model = fitted_models[best_model_name]
    best_threshold_value = float(best_threshold["threshold"])

    final_rows = evaluate_model_on_splits(
        model_name=f"{best_model_name}__threshold_tuned",
        model=best_model,
        splits=splits,
        feature_names=feature_names,
        threshold=best_threshold_value,
    )
    final_metrics = pd.DataFrame(final_rows)
    final_metrics["experiment_type"] = "selected_threshold_tuned"
    final_metrics.to_csv(TABLES_DIR / "btts_logistic_selected_threshold_metrics.csv", index=False)

    best_base = validation_metrics.sort_values(["balanced_accuracy", "f1"], ascending=False).iloc[0]
    best_base_model = fitted_models[best_base["model"]]
    best_base_rows = evaluate_model_on_splits(
        model_name=f"{best_base['model']}__default_threshold",
        model=best_base_model,
        splits=splits,
        feature_names=feature_names,
        threshold=0.50,
    )
    best_base_metrics = pd.DataFrame(best_base_rows)
    best_base_metrics["experiment_type"] = "selected_logistic_tuned"

    comparison = pd.concat([best_base_metrics, final_metrics], ignore_index=True)

    existing_metrics_path = TABLES_DIR / "btts_model_metrics.csv"
    if existing_metrics_path.exists():
        existing = pd.read_csv(existing_metrics_path)
        selected_existing = existing[
            (existing["split"].isin(["validation", "test"]))
            & (
                (
                    (existing["feature_set"] == "v1_only")
                    & (
                        existing["model"].isin(
                            [
                                "logistic_regression",
                                "catboost_classifier",
                                "random_forest_reference",
                                "dummy_most_frequent",
                            ]
                        )
                    )
                )
            )
        ].copy()
        selected_existing["experiment_type"] = "previous_reference"
        selected_existing["threshold"] = 0.50
        selected_existing["no_recall"] = pd.NA
        selected_existing["yes_recall"] = selected_existing["recall"]
        comparison = pd.concat([selected_existing, comparison], ignore_index=True, sort=False)

    comparison.to_csv(TABLES_DIR / "btts_final_controlled_comparison.csv", index=False)
    joblib.dump(best_model, MODELS_DIR / "logistic_regression_controlled_best.joblib")

    print("BTTS LogisticRegression controlled tuning completed.")
    print("Best LogisticRegression configs by validation balanced accuracy:")
    print(
        validation_metrics.sort_values(["balanced_accuracy", "f1"], ascending=False)
        .head(10)
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
                "threshold",
                "accuracy",
                "balanced_accuracy",
                "f1",
                "precision",
                "recall",
                "no_recall",
                "yes_recall",
            ]
        ]
        .sort_values(["split", "balanced_accuracy"], ascending=[True, False])
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
