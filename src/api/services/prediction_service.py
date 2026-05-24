from __future__ import annotations

import numpy as np
import pandas as pd

from src.api.schemas import PredictionRequest, PredictionResponse
from src.api.services.model_registry import get_model_config, load_metadata, load_models
from src.features.feature_registry import (
    BTTS_FEATURE_SETS,
    CORNERS_FEATURE_SETS,
    EXACT_SCORE_FEATURE_SETS,
    OUTCOME_FEATURE_SETS,
    OVER25_FEATURE_SETS,
    YELLOW_CARDS_FEATURE_SETS,
)
from src.postprocessing.consistency_layer import nearest_consistent_score


FEATURE_SETS = {
    "outcome": OUTCOME_FEATURE_SETS,
    "btts": BTTS_FEATURE_SETS,
    "over25": OVER25_FEATURE_SETS,
    "corners_over95": CORNERS_FEATURE_SETS,
    "yellow_cards_over35": YELLOW_CARDS_FEATURE_SETS,
    "exact_score_home_goals": EXACT_SCORE_FEATURE_SETS,
    "exact_score_away_goals": EXACT_SCORE_FEATURE_SETS,
}

BINARY_LABELS = {0: "No", 1: "Yes"}


def build_prediction(request: PredictionRequest) -> PredictionResponse:
    models = load_models()

    outcome_result = predict_multiclass("outcome", models["outcome"], request)
    btts_result = predict_binary("btts", models["btts"], request)
    over25_result = predict_binary("over25", models["over25"], request)
    corners_result = predict_binary("corners_over95", models["corners_over95"], request)
    yellow_result = predict_binary("yellow_cards_over35", models["yellow_cards_over35"], request)
    home_goals, away_goals = predict_exact_score(models, request)
    reconciled = reconcile_prediction(
        outcome=outcome_result["prediction"],
        btts=btts_result["prediction"],
        over25=over25_result["prediction"],
        home_goals=home_goals,
        away_goals=away_goals,
    )

    return PredictionResponse(
        outcome=reconciled["outcome"],
        outcome_probabilities=outcome_result["probabilities"],
        btts=BINARY_LABELS[reconciled["btts"]],
        btts_probabilities=btts_result["probabilities"],
        over25=BINARY_LABELS[reconciled["over25"]],
        over25_probabilities=over25_result["probabilities"],
        corners_over95=BINARY_LABELS[corners_result["prediction"]],
        corners_over95_probabilities=corners_result["probabilities"],
        yellow_cards_over35=BINARY_LABELS[yellow_result["prediction"]],
        yellow_cards_over35_probabilities=yellow_result["probabilities"],
        exact_score=f"{reconciled['home_goals']}:{reconciled['away_goals']}",
    )


def prepare_features(task: str, request: PredictionRequest) -> pd.DataFrame:
    model_config = get_model_config(task)
    feature_names = FEATURE_SETS[task][model_config["feature_set"]]
    row = {feature: 0.0 for feature in feature_names}
    row.update(
        {
            "Division": request.division,
            "HomeTeam": request.home_team,
            "AwayTeam": request.away_team,
            "SeasonStartYear": request.season_start_year,
            "MatchMonth": request.match_month,
        }
    )
    row.update(request.features)
    return pd.DataFrame([{feature: row.get(feature, 0.0) for feature in feature_names}])


def predict_multiclass(task: str, model: object, request: PredictionRequest) -> dict:
    features = prepare_features(task, request)
    prediction = str(model.predict(features)[0])
    probabilities = probability_map(model, features)
    return {"prediction": prediction, "probabilities": probabilities}


def predict_binary(task: str, model: object, request: PredictionRequest) -> dict:
    features = prepare_features(task, request)
    threshold = float(get_model_config(task)["threshold"])
    probabilities = probability_map(model, features)
    yes_probability = probabilities.get("1", probabilities.get("Yes", 0.0))
    prediction = int(yes_probability >= threshold)
    return {
        "prediction": prediction,
        "probabilities": {"No": round(1 - yes_probability, 4), "Yes": round(yes_probability, 4)},
    }


def probability_map(model: object, features: pd.DataFrame) -> dict[str, float]:
    probabilities = np.asarray(model.predict_proba(features)[0], dtype=float)
    classes = getattr(model, "classes_", None)
    if classes is None and hasattr(model, "get_param"):
        classes = model.get_param("classes")
    if classes is None:
        classes = list(range(len(probabilities)))
    return {str(label): round(float(probability), 4) for label, probability in zip(classes, probabilities)}


def predict_exact_score(models: dict[str, object], request: PredictionRequest) -> tuple[int, int]:
    metadata = load_metadata()
    min_goals, max_goals = metadata["reconciliation"]["exact_score_clip_range"]
    home_features = prepare_features("exact_score_home_goals", request)
    away_features = prepare_features("exact_score_away_goals", request)
    home_goals = int(np.clip(round(float(models["exact_score_home_goals"].predict(home_features)[0])), min_goals, max_goals))
    away_goals = int(np.clip(round(float(models["exact_score_away_goals"].predict(away_features)[0])), min_goals, max_goals))
    return home_goals, away_goals


def reconcile_prediction(
    *,
    outcome: str,
    btts: int,
    over25: int,
    home_goals: int,
    away_goals: int,
) -> dict[str, int | str]:
    row = pd.Series(
        {
            "pred_home_goals": home_goals,
            "pred_away_goals": away_goals,
            "direct_outcome": outcome,
            "direct_btts": btts,
            "direct_over25": over25,
        }
    )
    correction = nearest_consistent_score(row)
    final_over25 = over25
    if correction["relaxed_constraints"] == "over25":
        final_over25 = int(correction["final_score_derived_over25"])

    return {
        "outcome": outcome,
        "btts": btts,
        "over25": final_over25,
        "home_goals": int(correction["final_home_goals"]),
        "away_goals": int(correction["final_away_goals"]),
    }
