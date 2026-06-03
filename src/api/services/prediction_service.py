from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.api.database.models import (
    Match,
    Model as StoredModel,
    Prediction,
    PredictionCharacteristic,
    PredictionCharacteristicValue,
    User,
    UserQueryHistory,
)
from src.api.schemas import (
    MatchResultResponse,
    PredictionCharacteristicResponse,
    PredictionDetailResponse,
    PredictionHistoryResponse,
    PredictionHistoryUnreadCountResponse,
    PredictionHistoryViewedResponse,
    PredictionRequest,
    PredictionResponse,
    PredictionStoredResponse,
)
from src.api.services.feature_service import RuntimeFeatureBundle, build_runtime_feature_bundle
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
OUTCOME_TO_INT = {"A": 0, "D": 1, "H": 2}


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


def build_and_store_prediction_for_match(
    db: Session,
    match_id: int,
    user_id: int | None = None,
) -> PredictionStoredResponse:
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise ValueError(f"Match not found: {match_id}")
    if not match.odds:
        raise ValueError(f"Match has no odds: {match_id}")

    feature_bundle = build_runtime_feature_bundle(db, match)
    outcome_model = stored_model_by_path(db, get_model_config("outcome")["local_model_path"])
    existing_prediction = find_prediction_for_match_and_model(db, match.id, outcome_model.id)
    if existing_prediction is not None:
        add_user_query_history(db, user_id, existing_prediction.id)
        if user_id is not None:
            db.commit()
        return build_stored_prediction_response(existing_prediction, feature_bundle.debug)

    response = build_prediction_from_runtime_features(feature_bundle)
    prediction = store_prediction(db, match, response)
    add_user_query_history(db, user_id, prediction.id)
    db.commit()
    return PredictionStoredResponse(
        prediction_id=prediction.id,
        match_id=match.id,
        created_at=prediction.created_at,
        feature_debug=feature_bundle.debug,
        **response.model_dump(),
    )


def build_prediction_from_runtime_features(feature_bundle: RuntimeFeatureBundle) -> PredictionResponse:
    models = load_models()

    outcome_result = predict_multiclass_from_features(
        models["outcome"],
        feature_bundle.frames["v1_only"],
    )
    btts_result = predict_binary_from_features(
        "btts",
        models["btts"],
        feature_bundle.frames["v1_only"],
    )
    over25_result = predict_binary_from_features(
        "over25",
        models["over25"],
        feature_bundle.frames["v1_only"],
    )
    corners_result = predict_binary_from_features(
        "corners_over95",
        models["corners_over95"],
        feature_bundle.frames["v1_only"],
    )
    yellow_result = predict_binary_from_features(
        "yellow_cards_over35",
        models["yellow_cards_over35"],
        feature_bundle.frames["v1_yellow_related"],
    )
    home_goals, away_goals = predict_exact_score_from_features(
        models,
        feature_bundle.frames["v1_score_related"],
    )
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


def get_stored_prediction(db: Session, prediction_id: int) -> PredictionDetailResponse | None:
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if prediction is None:
        return None

    return PredictionDetailResponse(
        id=prediction.id,
        created_at=prediction.created_at,
        match_id=prediction.match_id,
        predicted_outcome=prediction.predicted_outcome,
        home_win_probability=float(prediction.home_win_probability),
        draw_probability=float(prediction.draw_probability),
        away_win_probability=float(prediction.away_win_probability),
        characteristics=[
            PredictionCharacteristicResponse(
                name=value.characteristic.name,
                predicted_value=value.predicted_value,
                probability=float(value.probability) if value.probability is not None else None,
            )
            for value in prediction.characteristic_values
        ],
    )


def get_user_prediction_history(db: Session, user_id: int) -> list[PredictionHistoryResponse]:
    rows = (
        db.query(UserQueryHistory)
        .options(
            joinedload(UserQueryHistory.prediction)
            .joinedload(Prediction.match)
            .joinedload(Match.home_team),
            joinedload(UserQueryHistory.prediction)
            .joinedload(Prediction.match)
            .joinedload(Match.away_team),
            joinedload(UserQueryHistory.prediction)
            .joinedload(Prediction.match)
            .joinedload(Match.season),
        )
        .join(UserQueryHistory.prediction)
        .filter(UserQueryHistory.user_id == user_id)
        .order_by(UserQueryHistory.query_date.desc(), UserQueryHistory.id.desc())
        .all()
    )

    return [build_prediction_history_response(row) for row in rows]


def get_user_history_unread_count(db: Session, user_id: int) -> PredictionHistoryUnreadCountResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return PredictionHistoryUnreadCountResponse(new_predictions_count=0)

    query = db.query(func.count(func.distinct(UserQueryHistory.prediction_id))).filter(
        UserQueryHistory.user_id == user_id
    )
    if user.last_history_viewed_at is not None:
        query = query.filter(UserQueryHistory.query_date > user.last_history_viewed_at)

    return PredictionHistoryUnreadCountResponse(new_predictions_count=int(query.scalar() or 0))


def mark_user_history_viewed(db: Session, user_id: int) -> PredictionHistoryViewedResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ValueError(f"User not found: {user_id}")

    latest_query_date = (
        db.query(func.max(UserQueryHistory.query_date))
        .filter(UserQueryHistory.user_id == user_id)
        .scalar()
    )
    user.last_history_viewed_at = latest_query_date or datetime.utcnow()
    db.commit()
    db.refresh(user)

    return PredictionHistoryViewedResponse(last_history_viewed_at=user.last_history_viewed_at)


def build_prediction_history_response(row: UserQueryHistory) -> PredictionHistoryResponse:
    prediction = row.prediction
    match = prediction.match
    characteristics = {value.characteristic.name: value for value in prediction.characteristic_values}
    btts = characteristics.get("BTTS")
    over25 = characteristics.get("Over2.5")
    corners = characteristics.get("Corners Over9.5")
    yellow_cards = characteristics.get("Yellow Cards Over3.5")
    exact_score = characteristics.get("Exact Score")
    return PredictionHistoryResponse(
        id=row.id,
        query_date=row.query_date,
        prediction_id=prediction.id,
        match_id=prediction.match_id,
        match_date=match.match_date,
        league=match.season.league.name,
        season=match.season.name,
        home_team=match.home_team.name,
        away_team=match.away_team.name,
        prediction_created_at=prediction.created_at,
        outcome={0: "A", 1: "D", 2: "H"}[prediction.predicted_outcome],
        btts=btts.predicted_value if btts is not None else None,
        over25=over25.predicted_value if over25 is not None else None,
        corners_over95=corners.predicted_value if corners is not None else None,
        yellow_cards_over35=yellow_cards.predicted_value if yellow_cards is not None else None,
        exact_score=exact_score.predicted_value if exact_score is not None else None,
        result=(
            MatchResultResponse(
                actual_outcome=match.result.actual_outcome,
                home_goals=match.result.home_goals,
                away_goals=match.result.away_goals,
                total_corners=match.result.total_corners,
                total_yellow_cards=match.result.total_yellow_cards,
            )
            if match.result is not None
            else None
        ),
    )


def find_prediction_for_match_and_model(db: Session, match_id: int, model_id: int) -> Prediction | None:
    return (
        db.query(Prediction)
        .filter(
            Prediction.match_id == match_id,
            Prediction.model_id == model_id,
        )
        .order_by(Prediction.created_at.desc())
        .first()
    )


def add_user_query_history(db: Session, user_id: int | None, prediction_id: int) -> None:
    if user_id is None:
        return
    db.add(
        UserQueryHistory(
            query_date=datetime.utcnow(),
            user_id=user_id,
            prediction_id=prediction_id,
        )
    )


def build_stored_prediction_response(
    prediction: Prediction,
    feature_debug: dict[str, dict[str, int | bool | list[str]]],
) -> PredictionStoredResponse:
    characteristics = {value.characteristic.name: value for value in prediction.characteristic_values}
    btts_value = characteristics["BTTS"]
    over25_value = characteristics["Over2.5"]
    corners_value = characteristics["Corners Over9.5"]
    yellow_value = characteristics["Yellow Cards Over3.5"]
    exact_score_value = characteristics["Exact Score"]

    return PredictionStoredResponse(
        prediction_id=prediction.id,
        match_id=prediction.match_id,
        created_at=prediction.created_at,
        outcome={0: "A", 1: "D", 2: "H"}[prediction.predicted_outcome],
        outcome_probabilities={
            "A": float(prediction.away_win_probability),
            "D": float(prediction.draw_probability),
            "H": float(prediction.home_win_probability),
        },
        btts=btts_value.predicted_value,
        btts_probabilities=stored_binary_probabilities(btts_value),
        over25=over25_value.predicted_value,
        over25_probabilities=stored_binary_probabilities(over25_value),
        corners_over95=corners_value.predicted_value,
        corners_over95_probabilities=stored_binary_probabilities(corners_value),
        yellow_cards_over35=yellow_value.predicted_value,
        yellow_cards_over35_probabilities=stored_binary_probabilities(yellow_value),
        exact_score=exact_score_value.predicted_value,
        feature_debug=feature_debug,
    )


def stored_binary_probabilities(value: PredictionCharacteristicValue) -> dict[str, float]:
    selected_probability = float(value.probability) if value.probability is not None else 0.0
    if value.predicted_value == "Yes":
        return {"No": round(1 - selected_probability, 4), "Yes": selected_probability}
    return {"No": selected_probability, "Yes": round(1 - selected_probability, 4)}


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
    return predict_binary_from_features(task, model, features)


def predict_multiclass_from_features(model: object, features: pd.DataFrame) -> dict:
    prediction = str(model.predict(features)[0])
    probabilities = probability_map(model, features)
    return {"prediction": prediction, "probabilities": probabilities}


def predict_binary_from_features(task: str, model: object, features: pd.DataFrame) -> dict:
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
    home_goals = int(
        np.clip(round(float(models["exact_score_home_goals"].predict(home_features)[0])), min_goals, max_goals)
    )
    away_goals = int(
        np.clip(round(float(models["exact_score_away_goals"].predict(away_features)[0])), min_goals, max_goals)
    )
    return home_goals, away_goals


def predict_exact_score_from_features(models: dict[str, object], features: pd.DataFrame) -> tuple[int, int]:
    metadata = load_metadata()
    min_goals, max_goals = metadata["reconciliation"]["exact_score_clip_range"]
    home_goals = int(
        np.clip(round(float(models["exact_score_home_goals"].predict(features)[0])), min_goals, max_goals)
    )
    away_goals = int(
        np.clip(round(float(models["exact_score_away_goals"].predict(features)[0])), min_goals, max_goals)
    )
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


def store_prediction(db: Session, match: Match, response: PredictionResponse) -> Prediction:
    outcome_model = stored_model_by_path(db, get_model_config("outcome")["local_model_path"])
    prediction = Prediction(
        created_at=datetime.utcnow(),
        predicted_outcome=OUTCOME_TO_INT[response.outcome],
        home_win_probability=decimal_probability(response.outcome_probabilities.get("H", 0.0)),
        draw_probability=decimal_probability(response.outcome_probabilities.get("D", 0.0)),
        away_win_probability=decimal_probability(response.outcome_probabilities.get("A", 0.0)),
        model_id=outcome_model.id,
        match_id=match.id,
    )
    db.add(prediction)
    db.flush()

    add_characteristic_value(
        db,
        prediction.id,
        "BTTS",
        response.btts,
        response.btts_probabilities.get(response.btts),
    )
    add_characteristic_value(
        db,
        prediction.id,
        "Over2.5",
        response.over25,
        response.over25_probabilities.get(response.over25),
    )
    add_characteristic_value(
        db,
        prediction.id,
        "Corners Over9.5",
        response.corners_over95,
        response.corners_over95_probabilities.get(response.corners_over95),
    )
    add_characteristic_value(
        db,
        prediction.id,
        "Yellow Cards Over3.5",
        response.yellow_cards_over35,
        response.yellow_cards_over35_probabilities.get(response.yellow_cards_over35),
    )
    add_characteristic_value(db, prediction.id, "Exact Score", response.exact_score, None)
    return prediction


def stored_model_by_path(db: Session, file_path: str) -> StoredModel:
    model = db.query(StoredModel).filter(StoredModel.file_path == file_path).first()
    if model is None:
        raise ValueError(f"Stored final model metadata not found: {file_path}")
    return model


def add_characteristic_value(
    db: Session,
    prediction_id: int,
    characteristic_name: str,
    predicted_value: str,
    probability: float | None,
) -> None:
    characteristic = (
        db.query(PredictionCharacteristic)
        .filter(PredictionCharacteristic.name == characteristic_name)
        .first()
    )
    if characteristic is None:
        raise ValueError(f"Prediction characteristic not found: {characteristic_name}")

    db.add(
        PredictionCharacteristicValue(
            prediction_id=prediction_id,
            characteristic_id=characteristic.id,
            predicted_value=predicted_value,
            probability=decimal_probability(probability) if probability is not None else None,
        )
    )


def decimal_probability(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"))
