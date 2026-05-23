from __future__ import annotations

from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
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

from src.features.feature_registry import CORNERS_FEATURE_SETS  # noqa: E402


FEATURE_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_features_v2.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "corners"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables" / "corners"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "corners"

TARGET_COLUMN = "Target_Corners_Over95"
CATEGORICAL_FEATURES = ["Division", "HomeTeam", "AwayTeam"]
RANDOM_STATE = 42
CORNERS_LABELS = [0, 1]


def build_time_split(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    train = data[data["SeasonStartYear"].between(2018, 2022)].copy()
    validation = data[data["SeasonStartYear"] == 2023].copy()
    test = data[data["SeasonStartYear"] == 2024].copy()
    return {"train": train, "validation": validation, "test": test}


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


def build_sklearn_models(feature_names: list[str]) -> dict[str, Pipeline]:
    return {
        "dummy_most_frequent": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(feature_names)),
                ("model", DummyClassifier(strategy="most_frequent")),
            ]
        ),
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(feature_names)),
                (
                    "model",
                    LogisticRegression(
                        solver="lbfgs",
                        penalty="l2",
                        max_iter=2000,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest_reference": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(feature_names)),
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


def build_catboost_model() -> CatBoostClassifier:
    return CatBoostClassifier(
        loss_function="Logloss",
        eval_metric="BalancedAccuracy",
        iterations=300,
        learning_rate=0.05,
        depth=6,
        random_seed=RANDOM_STATE,
        verbose=False,
        allow_writing_files=False,
    )


def evaluate_binary_classifier(
    *,
    feature_set: str,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict[str, float | str]:
    matrix = confusion_matrix(y_true, y_pred, labels=CORNERS_LABELS)
    no_recall = matrix[0, 0] / matrix[0].sum() if matrix[0].sum() else 0.0
    yes_recall = matrix[1, 1] / matrix[1].sum() if matrix[1].sum() else 0.0
    return {
        "feature_set": feature_set,
        "model": model_name,
        "split": split_name,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "no_recall": no_recall,
        "yes_recall": yes_recall,
    }


def classification_report_frame(
    *,
    feature_set: str,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> pd.DataFrame:
    report = classification_report(
        y_true,
        y_pred,
        labels=CORNERS_LABELS,
        target_names=["No", "Yes"],
        output_dict=True,
        zero_division=0,
    )
    frame = pd.DataFrame(report).transpose().reset_index(names="label")
    frame.insert(0, "split", split_name)
    frame.insert(0, "model", model_name)
    frame.insert(0, "feature_set", feature_set)
    return frame


def confusion_matrix_frame(
    *,
    feature_set: str,
    model_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> pd.DataFrame:
    matrix = confusion_matrix(y_true, y_pred, labels=CORNERS_LABELS)
    rows = []
    for true_index, true_label in enumerate(["No", "Yes"]):
        for pred_index, pred_label in enumerate(["No", "Yes"]):
            rows.append(
                {
                    "feature_set": feature_set,
                    "model": model_name,
                    "split": split_name,
                    "true_label": true_label,
                    "predicted_label": pred_label,
                    "count": int(matrix[true_index, pred_index]),
                }
            )
    return pd.DataFrame(rows)


def save_confusion_matrix_figure(
    *,
    y_true: pd.Series,
    y_pred: pd.Series,
    output_path: Path,
    title: str,
) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=CORNERS_LABELS)
    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks([0, 1], ["No", "Yes"])
    ax.set_yticks([0, 1], ["No", "Yes"])
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title(title)

    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            ax.text(
                column_index,
                row_index,
                str(value),
                ha="center",
                va="center",
                color="white" if value > matrix.max() / 2 else "black",
            )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def get_sklearn_feature_names(pipeline: Pipeline) -> list[str]:
    return pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()


def save_feature_importance(model_name: str, model, feature_names: list[str]) -> None:
    importance = None
    if isinstance(model, Pipeline):
        estimator = model.named_steps["model"]
        transformed_feature_names = get_sklearn_feature_names(model)
        if hasattr(estimator, "feature_importances_"):
            importance = pd.DataFrame(
                {"feature": transformed_feature_names, "importance": estimator.feature_importances_}
            )
        elif hasattr(estimator, "coef_"):
            importance = pd.DataFrame(
                {"feature": transformed_feature_names, "importance": abs(estimator.coef_[0])}
            )
    elif hasattr(model, "get_feature_importance"):
        importance = pd.DataFrame(
            {"feature": feature_names, "importance": model.get_feature_importance()}
        )

    if importance is not None:
        importance.sort_values("importance", ascending=False).to_csv(
            TABLES_DIR / f"{model_name}_feature_importance.csv",
            index=False,
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
                "corners_over95_yes_rate": split_data[TARGET_COLUMN].mean(),
                "corners_over95_no_rate": 1 - split_data[TARGET_COLUMN].mean(),
            }
        )
    pd.DataFrame(rows).to_csv(TABLES_DIR / "corners_time_split.csv", index=False)


def save_feature_lists() -> None:
    rows = []
    for feature_set, features in CORNERS_FEATURE_SETS.items():
        rows.extend({"feature_set": feature_set, "feature": feature} for feature in features)
    pd.DataFrame(rows).to_csv(TABLES_DIR / "corners_feature_sets.csv", index=False)


def run_model(
    *,
    feature_set: str,
    model_name: str,
    model,
    splits: dict[str, pd.DataFrame],
    feature_names: list[str],
) -> tuple[list[dict[str, float | str]], list[pd.DataFrame], list[pd.DataFrame]]:
    X_train = splits["train"][feature_names]
    y_train = splits["train"][TARGET_COLUMN]

    if isinstance(model, CatBoostClassifier):
        cat_features = [feature for feature in CATEGORICAL_FEATURES if feature in feature_names]
        model.fit(
            X_train,
            y_train,
            cat_features=cat_features,
            eval_set=(splits["validation"][feature_names], splits["validation"][TARGET_COLUMN]),
            use_best_model=True,
        )
        model.save_model(MODELS_DIR / f"{feature_set}__{model_name}.cbm")
    else:
        model.fit(X_train, y_train)
        joblib.dump(model, MODELS_DIR / f"{feature_set}__{model_name}.joblib")

    save_feature_importance(f"{feature_set}__{model_name}", model, feature_names)

    metrics = []
    reports = []
    matrices = []
    for split_name, split_data in splits.items():
        X_split = split_data[feature_names]
        y_split = split_data[TARGET_COLUMN]
        raw_pred = model.predict(X_split)
        y_pred = pd.Series(
            raw_pred.reshape(-1) if hasattr(raw_pred, "reshape") else raw_pred,
            index=y_split.index,
        ).astype(int)

        metrics.append(
            evaluate_binary_classifier(
                feature_set=feature_set,
                model_name=model_name,
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
            )
        )
        reports.append(
            classification_report_frame(
                feature_set=feature_set,
                model_name=model_name,
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
            )
        )
        matrices.append(
            confusion_matrix_frame(
                feature_set=feature_set,
                model_name=model_name,
                split_name=split_name,
                y_true=y_split,
                y_pred=y_pred,
            )
        )
        if split_name == "test":
            save_confusion_matrix_figure(
                y_true=y_split,
                y_pred=y_pred,
                output_path=FIGURES_DIR / f"{feature_set}__{model_name}_test_confusion_matrix.png",
                title=f"{feature_set} {model_name} test confusion matrix",
            )

    return metrics, reports, matrices


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(FEATURE_DATA_PATH, parse_dates=["MatchDateParsed"])
    required_columns = sorted(
        {TARGET_COLUMN, "MatchDateParsed", "SeasonStartYear"}
        | {feature for features in CORNERS_FEATURE_SETS.values() for feature in features}
    )
    missing_columns = sorted(set(required_columns) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    data = data.sort_values("MatchDateParsed").reset_index(drop=True)
    splits = build_time_split(data)
    save_split_report(splits)
    save_feature_lists()

    metric_rows = []
    report_frames = []
    matrix_frames = []

    for feature_set, feature_names in CORNERS_FEATURE_SETS.items():
        for model_name, model in build_sklearn_models(feature_names).items():
            metrics, reports, matrices = run_model(
                feature_set=feature_set,
                model_name=model_name,
                model=model,
                splits=splits,
                feature_names=feature_names,
            )
            metric_rows.extend(metrics)
            report_frames.extend(reports)
            matrix_frames.extend(matrices)

        metrics, reports, matrices = run_model(
            feature_set=feature_set,
            model_name="catboost_classifier",
            model=build_catboost_model(),
            splits=splits,
            feature_names=feature_names,
        )
        metric_rows.extend(metrics)
        report_frames.extend(reports)
        matrix_frames.extend(matrices)

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(TABLES_DIR / "corners_model_metrics.csv", index=False)
    pd.concat(report_frames, ignore_index=True).to_csv(
        TABLES_DIR / "corners_classification_reports.csv",
        index=False,
    )
    pd.concat(matrix_frames, ignore_index=True).to_csv(
        TABLES_DIR / "corners_confusion_matrices.csv",
        index=False,
    )

    validation_metrics = metrics[metrics["split"] == "validation"].sort_values(
        ["balanced_accuracy", "f1"],
        ascending=False,
    )
    best = validation_metrics.iloc[0]

    print("Corners Over9.5 training completed.")
    print("Time split:")
    print(pd.read_csv(TABLES_DIR / "corners_time_split.csv").to_string(index=False))
    print("Metrics:")
    print(metrics.sort_values(["split", "balanced_accuracy"], ascending=[True, False]).to_string(index=False))
    print(
        f"Best validation model by balanced accuracy: {best['feature_set']} / {best['model']} "
        f"({best['balanced_accuracy']:.4f})"
    )


if __name__ == "__main__":
    main()
