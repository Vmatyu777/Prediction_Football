from __future__ import annotations

from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
LATIN_PASSWORD_PATTERN = re.compile(r"^[\x21-\x7E]+$")


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
    source: str
    result: MatchResultResponse | None


class MatchDetailResponse(BaseModel):
    id: int
    match_date: datetime
    league: LeagueResponse
    season: SeasonResponse
    home_team: TeamResponse
    away_team: TeamResponse
    status: str
    source: str
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


class RegisterRequest(BaseModel):
    username: str = Field(max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Username is required")
        if not USERNAME_PATTERN.match(normalized):
            raise ValueError("Username may contain only Latin letters, digits, underscore, and hyphen")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Invalid email")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must contain at least 8 characters, a Latin letter, and a digit")
        if not LATIN_PASSWORD_PATTERN.match(value):
            raise ValueError("Password must contain at least 8 characters, a Latin letter, and a digit")
        if not any("A" <= character <= "Z" or "a" <= character <= "z" for character in value):
            raise ValueError("Password must contain at least 8 characters, a Latin letter, and a digit")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must contain at least 8 characters, a Latin letter, and a digit")
        return value


class LoginRequest(BaseModel):
    username_or_email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class AuthUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class PredictionHistoryResponse(BaseModel):
    id: int
    query_date: datetime
    prediction_id: int
    match_id: int
    match_date: datetime
    league: str
    season: str
    home_team: str
    away_team: str
    prediction_created_at: datetime
    outcome: str
    btts: str | None
    over25: str | None
    corners_over95: str | None
    yellow_cards_over35: str | None
    exact_score: str | None
    result: MatchResultResponse | None
