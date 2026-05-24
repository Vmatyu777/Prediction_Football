from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ModelSummary(BaseModel):
    task: str
    model_type: str
    feature_set: str
    input_feature_count: int
    threshold: float | None
    post_processing: str


class PredictionRequest(BaseModel):
    home_team: str = "Arsenal"
    away_team: str = "Chelsea"
    division: str = "E0"
    season_start_year: int = 2024
    match_month: int = 8
    features: dict[str, float | int | str] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    outcome: str
    outcome_probabilities: dict[str, float]
    btts: str
    btts_probabilities: dict[str, float]
    over25: str
    over25_probabilities: dict[str, float]
    corners_over95: str
    corners_over95_probabilities: dict[str, float]
    yellow_cards_over35: str
    yellow_cards_over35_probabilities: dict[str, float]
    exact_score: str
