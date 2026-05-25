from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import text

from src.api.config import APP_TITLE, APP_VERSION
from src.api.database.session import SessionLocal
from src.api.schemas import (
    DatabaseHealthResponse,
    HealthResponse,
    ModelSummary,
    PredictionRequest,
    PredictionResponse,
)
from src.api.services.model_registry import get_model_summaries
from src.api.services.prediction_service import build_prediction


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


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    return build_prediction(request)
