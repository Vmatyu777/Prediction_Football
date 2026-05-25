from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str


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


class TeamResponse(BaseModel):
    id: int
    name: str
    country: str


class LeagueResponse(BaseModel):
    id: int
    name: str
    country: str


class SeasonResponse(BaseModel):
    id: int
    name: str


class MatchResultResponse(BaseModel):
    actual_outcome: int
    home_goals: int
    away_goals: int
    total_corners: int
    total_yellow_cards: int


class OddsResponse(BaseModel):
    id: int
    bookmaker: str
    home_win_odds: float
    draw_odds: float
    away_win_odds: float
    collected_at: datetime


class MatchSummaryResponse(BaseModel):
    id: int
    match_date: datetime
    league: str
    season: str
    home_team: str
    away_team: str
    status: str
    result: MatchResultResponse | None


class MatchDetailResponse(BaseModel):
    id: int
    match_date: datetime
    league: LeagueResponse
    season: SeasonResponse
    home_team: TeamResponse
    away_team: TeamResponse
    status: str
    result: MatchResultResponse | None
    odds: list[OddsResponse]


class PredictionStoredResponse(PredictionResponse):
    prediction_id: int
    match_id: int
    created_at: datetime
    feature_debug: dict[str, dict[str, int | bool | list[str]]]


class PredictionCharacteristicResponse(BaseModel):
    name: str
    predicted_value: str
    probability: float | None


class PredictionDetailResponse(BaseModel):
    id: int
    created_at: datetime
    match_id: int
    predicted_outcome: int
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    characteristics: list[PredictionCharacteristicResponse]
