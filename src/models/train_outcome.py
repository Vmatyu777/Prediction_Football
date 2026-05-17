from __future__ import annotations

from pathlib import Path
import sys

import joblib
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.features.feature_registry import (  # noqa: E402
    OUTCOME_FEATURE_SETS,
    ROLLING_V2_FEATURES,
)
from src.models.evaluate_models import (  # noqa: E402
    classification_report_frame,
    confusion_matrix_frame,
    evaluate_classifier,
    save_confusion_matrix_figure,
)


FEATURE_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_features_v2.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "outcome"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables" / "outcome"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "outcome"

TARGET_COLUMN = "Target_Outcome"
CATEGORICAL_FEATURES = ["Division", "HomeTeam", "AwayTeam"]
RANDOM_STATE = 42


def build_time_split(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    train = data[data["SeasonStartYear"].between(2018, 2022)].copy()
    validation = data[data["SeasonStartYear"] == 2023].copy()
    test = data[data["SeasonStartYear"] == 2024].copy()
    return {"train": train, "validation": validation, "test": test}


def build_sklearn_preprocessor(feature_names: list[str]) -> ColumnTransformer:
    categorical_features = [feature for feature in CATEGORICAL_FEATURES if feature in feature_names]
    numeric_features = [feature for feature in feature_names if feature not in categorical_features]
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numeric", StandardScaler(), numeric_features),
        ],
        remainder="drop",
    )


def build_sklearn_models(feature_names: list[str]) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", build_sklearn_preprocessor(feature_names)),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest_reference": Pipeline(
            steps=[
                ("preprocessor", build_sklearn_preprocessor(feature_names)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=5,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def build_dummy_model(feature_names: list[str]) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_sklearn_preprocessor(feature_names)),
            ("model", DummyClassifier(strategy="most_frequent")),
        ]
    )


def build_catboost_model() -> CatBoostClassifier:
    return CatBoostClassifier(
        loss_function="MultiClass",
        eval_metric="TotalF1",
        iterations=300,
        learning_rate=0.05,
        depth=6,
        random_seed=RANDOM_STATE,
        verbose=False,
        allow_writing_files=False,
    )


def get_sklearn_feature_names(pipeline: Pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocessor"]
    return preprocessor.get_feature_names_out().tolist()


def save_feature_importance(model_name: str, model, feature_names: list[str]) -> None:
    importance = None

    if isinstance(model, Pipeline):
        estimator = model.named_steps["model"]
        transformed_feature_names = get_sklearn_feature_names(model)
        if hasattr(estimator, "feature_importances_"):
            importance = pd.DataFrame(
                {
                    "feature": transformed_feature_names,
                    "importance": estimator.feature_importances_,
                }
            )
        elif hasattr(estimator, "coef_"):
            importance = pd.DataFrame(
                {
                    "feature": transformed_feature_names,
                    "importance": abs(estimator.coef_).mean(axis=0),
                }
            )
    elif hasattr(model, "get_feature_importance"):
        importance = pd.DataFrame(
            {
                "feature": feature_names,
                "importance": model.get_feature_importance(),
            }
        )

    if importance is not None:
        importance = importance.sort_values("importance", ascending=False)
        importance.to_csv(TABLES_DIR / f"{model_name}_feature_importance.csv", index=False)


def save_model_feature_list(feature_set_name: str, feature_names: list[str]) -> None:
    pd.DataFrame({"feature_set": feature_set_name, "feature": feature_names}).to_csv(
        TABLES_DIR / f"outcome_{feature_set_name}_features.csv", index=False
    )


def save_split_report(splits: dict[str, pd.DataFrame]) -> None:
    rows = []
    for split_name, split_data in splits.items():
        rows.append(
            {
                "split": split_name,
                "rows": len(split_data),
                "date_min": split_data["MatchDateParsed"].min().date(),
                "date_max": split_data["MatchDateParsed"].max().date(),
                "seasons": ",".join(str(value) for value in sorted(split_data["SeasonStartYear"].unique())),
                "home_win_rate": (split_data[TARGET_COLUMN] == "H").mean(),
                "draw_rate": (split_data[TARGET_COLUMN] == "D").mean(),
                "away_win_rate": (split_data[TARGET_COLUMN] == "A").mean(),
            }
        )
    pd.DataFrame(rows).to_csv(TABLES_DIR / "outcome_time_split.csv", index=False)


def save_feature_correlation_report(data: pd.DataFrame) -> None:
    numeric_v2_features = [
        feature
        for feature in ROLLING_V2_FEATURES
        if feature in data.columns and pd.api.types.is_numeric_dtype(data[feature])
    ]
    correlations = data[numeric_v2_features].corr().abs()
    rows = []
    for index, left_feature in enumerate(numeric_v2_features):
        for right_feature in numeric_v2_features[index + 1 :]:
            value = correlations.loc[left_feature, right_feature]
            if value >= 0.85:
                rows.append(
                    {
                        "feature_left": left_feature,
                        "feature_right": right_feature,
                        "abs_correlation": value,
                    }
                )
    correlation_report = pd.DataFrame(
        rows,
        columns=["feature_left", "feature_right", "abs_correlation"],
    )
    if not correlation_report.empty:
        correlation_report = correlation_report.sort_values("abs_correlation", ascending=False)
    correlation_report.to_csv(TABLES_DIR / "outcome_v2_high_correlations.csv", index=False)


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(FEATURE_DATA_PATH, parse_dates=["MatchDateParsed"])
    all_config_features = sorted({feature for features in OUTCOME_FEATURE_SETS.values() for feature in features})
    missing_features = sorted(set(all_config_features + [TARGET_COLUMN]) - set(data.columns))
    if missing_features:
        raise ValueError(f"Missing required columns: {missing_features}")

    data = data.sort_values("MatchDateParsed").reset_index(drop=True)
    splits = build_time_split(data)
    save_split_report(splits)
    save_feature_correlation_report(splits["train"])

    metric_rows = []
    report_frames = []
    confusion_frames = []

    for feature_set_name, feature_names in OUTCOME_FEATURE_SETS.items():
        save_model_feature_list(feature_set_name, feature_names)

        X_train = splits["train"][feature_names]
        y_train = splits["train"][TARGET_COLUMN]
        X_validation = splits["validation"][feature_names]
        y_validation = splits["validation"][TARGET_COLUMN]
        X_test = splits["test"][feature_names]
        y_test = splits["test"][TARGET_COLUMN]

        models = build_sklearn_models(feature_names)
        if feature_set_name == "v1_only":
            models = {"dummy_most_frequent": build_dummy_model(feature_names), **models}

        for model_name, model in models.items():
            experiment_name = f"{feature_set_name}__{model_name}"
            model.fit(X_train, y_train)
            joblib.dump(model, MODELS_DIR / f"{experiment_name}.joblib")
            save_feature_importance(experiment_name, model, feature_names)

            for split_name, X_split, y_split in [
                ("train", X_train, y_train),
                ("validation", X_validation, y_validation),
                ("test", X_test, y_test),
            ]:
                y_pred = pd.Series(model.predict(X_split), index=y_split.index)
                metric = evaluate_classifier(
                    model_name=model_name,
                    split_name=split_name,
                    y_true=y_split,
                    y_pred=y_pred,
                )
                metric["feature_set"] = feature_set_name
                metric_rows.append(metric)
                report = classification_report_frame(
                    model_name=model_name,
                    split_name=split_name,
                    y_true=y_split,
                    y_pred=y_pred,
                )
                report.insert(0, "feature_set", feature_set_name)
                report_frames.append(report)
                matrix_frame = confusion_matrix_frame(
                    model_name=model_name,
                    split_name=split_name,
                    y_true=y_split,
                    y_pred=y_pred,
                )
                matrix_frame.insert(0, "feature_set", feature_set_name)
                confusion_frames.append(matrix_frame)
                if split_name == "test":
                    save_confusion_matrix_figure(
                        y_true=y_split,
                        y_pred=y_pred,
                        output_path=FIGURES_DIR / f"{experiment_name}_test_confusion_matrix.png",
                        title=f"{experiment_name} test confusion matrix",
                    )

        catboost_model = build_catboost_model()
        cat_features = [feature for feature in CATEGORICAL_FEATURES if feature in feature_names]
        catboost_model.fit(
            X_train,
            y_train,
            cat_features=cat_features,
            eval_set=(X_validation, y_validation),
            use_best_model=True,
        )
        catboost_experiment_name = f"{feature_set_name}__catboost_classifier"
        catboost_model.save_model(MODELS_DIR / f"{catboost_experiment_name}.cbm")
        save_feature_importance(catboost_experiment_name, catboost_model, feature_names)

        for split_name, X_split, y_split in [
            ("train", X_train, y_train),
            ("validation", X_validation, y_validation),
            ("test", X_test, y_test),
        ]:
            y_pred = pd.Series(catboost_model.predict(X_split).reshape(-1), index=y_split.index)
            metric = evaluate_classifier(
                model_name="catboost_classifier",
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
            )
            metric["feature_set"] = feature_set_name
            metric_rows.append(metric)
            report = classification_report_frame(
                model_name="catboost_classifier",
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
            )
            report.insert(0, "feature_set", feature_set_name)
            report_frames.append(report)
            matrix_frame = confusion_matrix_frame(
                model_name="catboost_classifier",
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
            )
            matrix_frame.insert(0, "feature_set", feature_set_name)
            confusion_frames.append(matrix_frame)
            if split_name == "test":
                save_confusion_matrix_figure(
                    y_true=y_split,
                    y_pred=y_pred,
                    output_path=FIGURES_DIR / f"{catboost_experiment_name}_test_confusion_matrix.png",
                    title=f"{catboost_experiment_name} test confusion matrix",
                )

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(TABLES_DIR / "outcome_model_metrics.csv", index=False)
    pd.concat(report_frames, ignore_index=True).to_csv(
        TABLES_DIR / "outcome_classification_reports.csv", index=False
    )
    pd.concat(confusion_frames, ignore_index=True).to_csv(
        TABLES_DIR / "outcome_confusion_matrices.csv", index=False
    )

    validation_metrics = metrics[metrics["split"] == "validation"].sort_values(
        "macro_f1", ascending=False
    )
    best_model = validation_metrics.iloc[0]

    print("Outcome training completed.")
    print("Time split:")
    print(pd.read_csv(TABLES_DIR / "outcome_time_split.csv").to_string(index=False))
    print("Metrics:")
    print(
        metrics.sort_values(["split", "macro_f1"], ascending=[True, False]).to_string(index=False)
    )
    print(
        f"Best validation model by macro F1: {best_model['feature_set']} / {best_model['model']} "
        f"({best_model['macro_f1']:.4f})"
    )


if __name__ == "__main__":
    main()
