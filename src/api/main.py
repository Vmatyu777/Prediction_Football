from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text

from src.api.config import APP_TITLE, APP_VERSION
from src.api.database.session import SessionLocal, engine
from src.api.schemas import (
    AuthTokenResponse,
    AuthUserResponse,
    DatabaseHealthResponse,
    HealthResponse,
    LoginRequest,
    MatchDetailResponse,
    MatchSummaryResponse,
    ModelSummary,
    PredictionDetailResponse,
    PredictionHistoryResponse,
    PredictionRequest,
    PredictionResponse,
    PredictionStoredResponse,
    RegisterRequest,
)
from src.api.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_optional_current_user,
    register_user,
    user_response,
)
from src.api.services.match_service import (
    get_match_detail,
    list_matches,
    list_recent_matches,
    list_sampled_recent_matches,
    list_showcase_matches,
    list_upcoming_matches,
)
from src.api.services.model_registry import get_model_summaries
from src.api.services.prediction_service import (
    build_and_store_prediction_for_match,
    build_prediction,
    get_stored_prediction,
    get_user_prediction_history,
)
from src.api.database.models import User


app = FastAPI(title=APP_TITLE, version=APP_VERSION)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=APP_TITLE, version=APP_VERSION)


@app.get("/db/health", response_model=DatabaseHealthResponse)
def db_health() -> DatabaseHealthResponse:
    with SessionLocal() as db:
        db.execute(text("select 1"))
    return DatabaseHealthResponse(status="ok", database=engine.dialect.name)


@app.get("/models", response_model=list[ModelSummary])
def models() -> list[ModelSummary]:
    return get_model_summaries()


@app.post("/auth/register", response_model=AuthUserResponse)
def auth_register(request: RegisterRequest) -> AuthUserResponse:
    with SessionLocal() as db:
        user = register_user(db, request)
        return user_response(user)


@app.post("/auth/login", response_model=AuthTokenResponse)
def auth_login(request: LoginRequest) -> AuthTokenResponse:
    with SessionLocal() as db:
        user = authenticate_user(db, request.username_or_email, request.password)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthTokenResponse(
            access_token=create_access_token(user),
            user=user_response(user),
        )


@app.get("/auth/me", response_model=AuthUserResponse)
def auth_me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
    return user_response(current_user)


@app.get("/users/me/history", response_model=list[PredictionHistoryResponse])
def user_history(current_user: User = Depends(get_current_user)) -> list[PredictionHistoryResponse]:
    with SessionLocal() as db:
        return get_user_prediction_history(db, current_user.id)


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


@app.get("/matches/recent/sampled", response_model=list[MatchSummaryResponse])
def sampled_recent_matches(
    per_league_season: int = Query(default=5, ge=1, le=10),
) -> list[MatchSummaryResponse]:
    with SessionLocal() as db:
        return list_sampled_recent_matches(db, per_league_season=per_league_season)


@app.get("/matches/showcase", response_model=list[MatchSummaryResponse])
def showcase_matches(
    per_league_season: int = Query(default=5, ge=1, le=10),
) -> list[MatchSummaryResponse]:
    with SessionLocal() as db:
        try:
            return list_showcase_matches(db, per_league_season=per_league_season)
        except FileNotFoundError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error


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
def predict_match(
    match_id: int,
    current_user: User | None = Depends(get_optional_current_user),
) -> PredictionStoredResponse:
    with SessionLocal() as db:
        try:
            user_id = current_user.id if current_user is not None else None
            return build_and_store_prediction_for_match(db, match_id, user_id=user_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/predictions/{prediction_id}", response_model=PredictionDetailResponse)
def prediction_detail(prediction_id: int) -> PredictionDetailResponse:
    with SessionLocal() as db:
        prediction = get_stored_prediction(db, prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction
