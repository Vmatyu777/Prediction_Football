from __future__ import annotations

from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.features.feature_registry import EXACT_SCORE_FEATURE_SETS  # noqa: E402


FEATURE_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_features_v2.csv"
MODELS_DIR = PROJECT_ROOT / "models" / "exact_score"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables" / "exact_score"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "exact_score"

HOME_TARGET = "Target_HomeGoals"
AWAY_TARGET = "Target_AwayGoals"
TARGET_COLUMNS = [HOME_TARGET, AWAY_TARGET]
CATEGORICAL_FEATURES = ["Division", "HomeTeam", "AwayTeam"]
RANDOM_STATE = 42
MIN_GOALS = 0
MAX_GOALS = 6


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
        "dummy_mean": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(feature_names)),
                ("model", DummyRegressor(strategy="mean")),
            ]
        ),
        "ridge_regression": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(feature_names)),
                ("model", Ridge(alpha=1.0)),
            ]
        ),
        "random_forest_reference": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(feature_names)),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        min_samples_leaf=5,
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def build_catboost_model() -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function="RMSE",
        eval_metric="MAE",
        iterations=300,
        learning_rate=0.05,
        depth=6,
        random_seed=RANDOM_STATE,
        verbose=False,
        allow_writing_files=False,
    )


def clip_round_goals(predictions: pd.Series) -> pd.Series:
    return predictions.round().clip(MIN_GOALS, MAX_GOALS).astype(int)


def outcome_from_scores(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return pd.Series(
        ["H" if home > away else "A" if away > home else "D" for home, away in zip(home_goals, away_goals)],
        index=home_goals.index,
    )


def btts_from_scores(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return ((home_goals > 0) & (away_goals > 0)).astype(int)


def over25_from_scores(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return ((home_goals + away_goals) > 2.5).astype(int)


def score_series(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return home_goals.astype(str) + ":" + away_goals.astype(str)


def evaluate_target_predictions(
    *,
    feature_set: str,
    model_name: str,
    target_name: str,
    split_name: str,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> dict[str, float | str]:
    return {
        "feature_set": feature_set,
        "model": model_name,
        "target": target_name,
        "split": split_name,
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred) ** 0.5,
    }


def evaluate_score_predictions(
    *,
    feature_set: str,
    model_name: str,
    split_name: str,
    split_data: pd.DataFrame,
    home_pred_continuous: pd.Series,
    away_pred_continuous: pd.Series,
) -> tuple[dict[str, float | str], pd.DataFrame]:
    true_home = split_data[HOME_TARGET].astype(int)
    true_away = split_data[AWAY_TARGET].astype(int)
    pred_home = clip_round_goals(home_pred_continuous)
    pred_away = clip_round_goals(away_pred_continuous)

    true_score = score_series(true_home, true_away)
    pred_score = score_series(pred_home, pred_away)
    true_total_goals = true_home + true_away
    pred_total_goals = pred_home + pred_away

    true_outcome = outcome_from_scores(true_home, true_away)
    pred_outcome = outcome_from_scores(pred_home, pred_away)
    true_btts = btts_from_scores(true_home, true_away)
    pred_btts = btts_from_scores(pred_home, pred_away)
    true_over25 = over25_from_scores(true_home, true_away)
    pred_over25 = over25_from_scores(pred_home, pred_away)

    metrics = {
        "feature_set": feature_set,
        "model": model_name,
        "split": split_name,
        "exact_score_accuracy": accuracy_score(true_score, pred_score),
        "home_goals_mae": mean_absolute_error(true_home, pred_home),
        "away_goals_mae": mean_absolute_error(true_away, pred_away),
        "total_goals_mae": mean_absolute_error(true_total_goals, pred_total_goals),
        "outcome_accuracy_from_score": accuracy_score(true_outcome, pred_outcome),
        "btts_accuracy_from_score": accuracy_score(true_btts, pred_btts),
        "over25_accuracy_from_score": accuracy_score(true_over25, pred_over25),
    }

    predictions = pd.DataFrame(
        {
            "feature_set": feature_set,
            "model": model_name,
            "split": split_name,
            "true_home_goals": true_home,
            "true_away_goals": true_away,
            "pred_home_goals": pred_home,
            "pred_away_goals": pred_away,
            "true_score": true_score,
            "pred_score": pred_score,
            "true_total_goals": true_total_goals,
            "pred_total_goals": pred_total_goals,
            "true_outcome": true_outcome,
            "pred_outcome": pred_outcome,
            "true_btts": true_btts,
            "pred_btts": pred_btts,
            "true_over25": true_over25,
            "pred_over25": pred_over25,
        }
    )
    return metrics, predictions


def fit_model_pair(
    *,
    feature_set: str,
    model_name: str,
    home_model,
    away_model,
    splits: dict[str, pd.DataFrame],
    feature_names: list[str],
) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]], list[pd.DataFrame]]:
    X_train = splits["train"][feature_names]
    y_home_train = splits["train"][HOME_TARGET]
    y_away_train = splits["train"][AWAY_TARGET]

    if isinstance(home_model, CatBoostRegressor):
        cat_features = [feature for feature in CATEGORICAL_FEATURES if feature in feature_names]
        home_model.fit(
            X_train,
            y_home_train,
            cat_features=cat_features,
            eval_set=(splits["validation"][feature_names], splits["validation"][HOME_TARGET]),
            use_best_model=True,
        )
        away_model.fit(
            X_train,
            y_away_train,
            cat_features=cat_features,
            eval_set=(splits["validation"][feature_names], splits["validation"][AWAY_TARGET]),
            use_best_model=True,
        )
        home_model.save_model(MODELS_DIR / f"{feature_set}__{model_name}__home_goals.cbm")
        away_model.save_model(MODELS_DIR / f"{feature_set}__{model_name}__away_goals.cbm")
    else:
        home_model.fit(X_train, y_home_train)
        away_model.fit(X_train, y_away_train)
        joblib.dump(home_model, MODELS_DIR / f"{feature_set}__{model_name}__home_goals.joblib")
        joblib.dump(away_model, MODELS_DIR / f"{feature_set}__{model_name}__away_goals.joblib")

    target_metrics = []
    score_metrics = []
    prediction_frames = []

    for split_name, split_data in splits.items():
        X_split = split_data[feature_names]
        home_pred = pd.Series(home_model.predict(X_split), index=split_data.index)
        away_pred = pd.Series(away_model.predict(X_split), index=split_data.index)

        target_metrics.append(
            evaluate_target_predictions(
                feature_set=feature_set,
                model_name=model_name,
                target_name=HOME_TARGET,
                split_name=split_name,
                y_true=split_data[HOME_TARGET],
                y_pred=home_pred,
            )
        )
        target_metrics.append(
            evaluate_target_predictions(
                feature_set=feature_set,
                model_name=model_name,
                target_name=AWAY_TARGET,
                split_name=split_name,
                y_true=split_data[AWAY_TARGET],
                y_pred=away_pred,
            )
        )

        metrics, predictions = evaluate_score_predictions(
            feature_set=feature_set,
            model_name=model_name,
            split_name=split_name,
            split_data=split_data,
            home_pred_continuous=home_pred,
            away_pred_continuous=away_pred,
        )
        score_metrics.append(metrics)
        prediction_frames.append(predictions)

    return target_metrics, score_metrics, prediction_frames


def save_feature_lists() -> None:
    rows = []
    for feature_set, features in EXACT_SCORE_FEATURE_SETS.items():
        rows.extend({"feature_set": feature_set, "feature": feature} for feature in features)
    pd.DataFrame(rows).to_csv(TABLES_DIR / "exact_score_feature_sets.csv", index=False)


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
                "home_goals_mean": split_data[HOME_TARGET].mean(),
                "away_goals_mean": split_data[AWAY_TARGET].mean(),
                "total_goals_mean": (split_data[HOME_TARGET] + split_data[AWAY_TARGET]).mean(),
            }
        )
    pd.DataFrame(rows).to_csv(TABLES_DIR / "exact_score_time_split.csv", index=False)


def save_score_distribution(predictions: pd.DataFrame) -> None:
    rows = []
    for (feature_set, model_name, split_name), group in predictions.groupby(
        ["feature_set", "model", "split"]
    ):
        for score_type, column in [("actual", "true_score"), ("predicted", "pred_score")]:
            counts = group[column].value_counts().reset_index()
            counts.columns = ["score", "count"]
            counts["rate"] = counts["count"] / len(group)
            counts.insert(0, "score_type", score_type)
            counts.insert(0, "split", split_name)
            counts.insert(0, "model", model_name)
            counts.insert(0, "feature_set", feature_set)
            rows.append(counts)
    distribution = pd.concat(rows, ignore_index=True)
    distribution.to_csv(TABLES_DIR / "exact_score_score_distribution.csv", index=False)

    common_scores = (
        distribution.sort_values(["feature_set", "model", "split", "score_type", "count"], ascending=[True, True, True, True, False])
        .groupby(["feature_set", "model", "split", "score_type"])
        .head(10)
        .reset_index(drop=True)
    )
    common_scores.to_csv(TABLES_DIR / "exact_score_common_scores.csv", index=False)


def save_final_figures(final_predictions: pd.DataFrame, final_name: str) -> None:
    test_predictions = final_predictions[final_predictions["split"] == "test"].copy()

    actual_top = test_predictions["true_score"].value_counts().head(10)
    predicted_top = test_predictions["pred_score"].value_counts().head(10)
    all_scores = sorted(set(actual_top.index) | set(predicted_top.index))

    comparison = pd.DataFrame(
        {
            "actual": [actual_top.get(score, 0) for score in all_scores],
            "predicted": [predicted_top.get(score, 0) for score in all_scores],
        },
        index=all_scores,
    )
    ax = comparison.plot(kind="bar", figsize=(9, 4.5), color=["#4c78a8", "#f58518"])
    ax.set_xlabel("Score")
    ax.set_ylabel("Count")
    ax.set_title(f"{final_name} test score distribution")
    ax.legend(loc="upper right")
    ax.figure.tight_layout()
    ax.figure.savefig(FIGURES_DIR / "exact_score_final_score_distribution.png", dpi=160)
    plt.close(ax.figure)

    total_error = test_predictions["pred_total_goals"] - test_predictions["true_total_goals"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(total_error, bins=range(int(total_error.min()) - 1, int(total_error.max()) + 2), color="#54a24b")
    ax.set_xlabel("Predicted total goals - true total goals")
    ax.set_ylabel("Matches")
    ax.set_title(f"{final_name} test total-goals error")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "exact_score_final_total_goals_error.png", dpi=160)
    plt.close(fig)


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(FEATURE_DATA_PATH, parse_dates=["MatchDateParsed"])
    required_columns = sorted(
        {"MatchDateParsed", "SeasonStartYear", HOME_TARGET, AWAY_TARGET}
        | {feature for features in EXACT_SCORE_FEATURE_SETS.values() for feature in features}
    )
    missing_columns = sorted(set(required_columns) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    data = data.sort_values("MatchDateParsed").reset_index(drop=True)
    splits = build_time_split(data)
    save_split_report(splits)
    save_feature_lists()

    all_target_metrics = []
    all_score_metrics = []
    all_prediction_frames = []

    for feature_set, feature_names in EXACT_SCORE_FEATURE_SETS.items():
        for model_name, home_model in build_sklearn_models(feature_names).items():
            _, away_model = next(
                (name, model)
                for name, model in build_sklearn_models(feature_names).items()
                if name == model_name
            )
            target_metrics, score_metrics, prediction_frames = fit_model_pair(
                feature_set=feature_set,
                model_name=model_name,
                home_model=home_model,
                away_model=away_model,
                splits=splits,
                feature_names=feature_names,
            )
            all_target_metrics.extend(target_metrics)
            all_score_metrics.extend(score_metrics)
            all_prediction_frames.extend(prediction_frames)

        target_metrics, score_metrics, prediction_frames = fit_model_pair(
            feature_set=feature_set,
            model_name="catboost_regressor",
            home_model=build_catboost_model(),
            away_model=build_catboost_model(),
            splits=splits,
            feature_names=feature_names,
        )
        all_target_metrics.extend(target_metrics)
        all_score_metrics.extend(score_metrics)
        all_prediction_frames.extend(prediction_frames)

    target_metrics = pd.DataFrame(all_target_metrics)
    score_metrics = pd.DataFrame(all_score_metrics)
    predictions = pd.concat(all_prediction_frames, ignore_index=True)

    target_metrics.to_csv(TABLES_DIR / "exact_score_target_metrics.csv", index=False)
    score_metrics.to_csv(TABLES_DIR / "exact_score_model_metrics.csv", index=False)
    save_score_distribution(predictions)

    validation_metrics = score_metrics[score_metrics["split"] == "validation"].copy()
    best_validation = validation_metrics.sort_values(
        ["exact_score_accuracy", "total_goals_mae", "outcome_accuracy_from_score"],
        ascending=[False, True, False],
    ).iloc[0]

    final_comparison = score_metrics[
        score_metrics["split"].isin(["validation", "test"])
    ].copy()
    final_comparison["selection"] = "reference"
    final_mask = (
        (final_comparison["feature_set"] == best_validation["feature_set"])
        & (final_comparison["model"] == best_validation["model"])
    )
    final_comparison.loc[final_mask, "selection"] = "selected"
    final_comparison.to_csv(TABLES_DIR / "exact_score_final_controlled_comparison.csv", index=False)

    final_predictions = predictions[
        (predictions["feature_set"] == best_validation["feature_set"])
        & (predictions["model"] == best_validation["model"])
    ].copy()
    final_predictions.to_csv(TABLES_DIR / "exact_score_final_predictions.csv", index=False)
    save_final_figures(
        final_predictions,
        f"{best_validation['feature_set']} / {best_validation['model']}",
    )

    print("Exact score training completed.")
    print("Time split:")
    print(pd.read_csv(TABLES_DIR / "exact_score_time_split.csv").to_string(index=False))
    print("Target metrics:")
    print(
        target_metrics.sort_values(["split", "target", "mae"], ascending=[True, True, True]).to_string(index=False)
    )
    print("Score metrics:")
    print(
        score_metrics.sort_values(["split", "exact_score_accuracy"], ascending=[True, False]).to_string(index=False)
    )
    print("Selected validation configuration:")
    print(best_validation.to_frame().transpose().to_string(index=False))


if __name__ == "__main__":
    main()
