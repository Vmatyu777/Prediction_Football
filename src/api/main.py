from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from src.api.config import APP_TITLE, APP_VERSION
from src.api.database.session import SessionLocal
from src.api.schemas import (
    DatabaseHealthResponse,
    HealthResponse,
    MatchDetailResponse,
    MatchSummaryResponse,
    ModelSummary,
    PredictionDetailResponse,
    PredictionRequest,
    PredictionResponse,
    PredictionStoredResponse,
)
from src.api.services.match_service import (
    get_match_detail,
    list_matches,
    list_recent_matches,
    list_upcoming_matches,
)
from src.api.services.model_registry import get_model_summaries
from src.api.services.prediction_service import (
    build_and_store_prediction_for_match,
    build_prediction,
    get_stored_prediction,
)


app = FastAPI(title=APP_TITLE, version=APP_VERSION)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=APP_TITLE, version=APP_VERSION)


@app.get("/db/health", response_model=DatabaseHealthResponse)
def db_health() -> DatabaseHealthResponse:
    with SessionLocal() as db:
        db.execute(text("select 1"))
    return DatabaseHealthResponse(status="ok", database="sqlite")


@app.get("/models", response_model=list[ModelSummary])
def models() -> list[ModelSummary]:
    return get_model_summaries()


@app.get("/matches", response_model=list[MatchSummaryResponse])
def matches(
    league: str | None = None,
    season: str | None = None,
    date_filter: date | None = Query(default=None, alias="date"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MatchSummaryResponse]:
    with SessionLocal() as db:
        return list_matches(
            db,
            league=league,
            season=season,
            match_date=date_filter,
            limit=limit,
            offset=offset,
        )


@app.get("/matches/upcoming", response_model=list[MatchSummaryResponse])
def upcoming_matches(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MatchSummaryResponse]:
    with SessionLocal() as db:
        return list_upcoming_matches(db, limit=limit, offset=offset)


@app.get("/matches/recent", response_model=list[MatchSummaryResponse])
def recent_matches(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MatchSummaryResponse]:
    with SessionLocal() as db:
        return list_recent_matches(db, limit=limit, offset=offset)


@app.get("/matches/{match_id}", response_model=MatchDetailResponse)
def match_detail(match_id: int) -> MatchDetailResponse:
    with SessionLocal() as db:
        match = get_match_detail(db, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    return build_prediction(request)


@app.post("/predict/{match_id}", response_model=PredictionStoredResponse)
def predict_match(match_id: int) -> PredictionStoredResponse:
    with SessionLocal() as db:
        try:
            return build_and_store_prediction_for_match(db, match_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/predictions/{prediction_id}", response_model=PredictionDetailResponse)
def prediction_detail(prediction_id: int) -> PredictionDetailResponse:
    with SessionLocal() as db:
        prediction = get_stored_prediction(db, prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction
