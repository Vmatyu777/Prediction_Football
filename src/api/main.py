from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
import logging

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.config import APP_TITLE, APP_VERSION
from src.api.admin import setup_admin
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
    PredictionHistoryUnreadCountResponse,
    PredictionHistoryViewedResponse,
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
    get_user_history_unread_count,
    get_user_prediction_history,
    mark_user_history_viewed,
)
from src.api.services.scheduler_service import get_scheduler_health, shutdown_scheduler, start_scheduler
from src.api.database.models import User


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        start_scheduler()
    except Exception:
        logger.exception("API-FOOTBALL scheduler failed to start")
    try:
        yield
    finally:
        shutdown_scheduler()


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan, docs_url=None)
setup_admin(app)


def _is_browser_html_request(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept.lower()


def _production_page(
    title: str,
    heading: str,
    description: str,
    badge: str,
    lead_label: str = "Доступные разделы:",
    links: list[tuple[str, str, str]] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    if links is None:
        links = [
            ("/", "Главная", "Общая информация о системе"),
            ("/health", "Проверка состояния", "Быстрая проверка доступности backend"),
            ("/docs", "Документация API", "Swagger UI для проверки endpoints"),
            ("/admin/login", "Административная панель", "SQLAdmin для управления данными"),
        ]
    nav_links = "\n".join(
        f'      <a href="{href}"><span>{label}</span><code>{href}</code><small>{hint}</small></a>'
        for href, label, hint in links
    )
    html = f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Информационная система машинного обучения для прогнозирования результатов футбольных матчей">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07120d;
      --panel: #0f1f16;
      --text: #eef8f0;
      --muted: #a7b7ad;
      --accent: #9be15d;
      --border: #263a2d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 32px;
      background: radial-gradient(circle at top, #17351f 0, var(--bg) 52%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(760px, 100%);
      padding: 36px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(15, 31, 22, 0.94);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 5vw, 3.5rem);
      line-height: 1.05;
    }}
    p {{
      margin: 0;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.6;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 24px 0;
      padding: 8px 12px;
      border: 1px solid rgba(155, 225, 93, 0.35);
      border-radius: 999px;
      color: var(--accent);
      font-weight: 700;
      background: rgba(155, 225, 93, 0.08);
    }}
    .status::before {{
      content: "";
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 18px var(--accent);
    }}
    nav {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
      margin-top: 24px;
    }}
    a {{
      display: block;
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      text-decoration: none;
      background: #0b1911;
    }}
    a span {{
      display: block;
      font-weight: 700;
    }}
    a code {{
      display: block;
      margin-top: 6px;
      color: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 0.95rem;
    }}
    a small {{
      display: block;
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.35;
    }}
    a:hover, a:focus {{
      border-color: var(--accent);
      color: var(--accent);
      outline: none;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{heading}</h1>
    <p>{description}</p>
    <div class="status">{badge}</div>
    <p>{lead_label}</p>
    <nav aria-label="Доступные разделы">
{nav_links}
    </nav>
  </main>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=status_code)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and _is_browser_html_request(request) and not request.url.path.startswith("/admin"):
        return _production_page(
            title="Страница не найдена",
            heading="Страница не найдена",
            description="Запрошенный адрес отсутствует в системе",
            badge="Система прогнозирования футбольных матчей",
            lead_label="Выберите доступный раздел:",
            links=[
                ("/", "Вернуться на главную", "Общая информация о системе"),
                ("/docs", "Документация API", "Swagger UI для проверки endpoints"),
                ("/admin/login", "Административная панель", "SQLAdmin для управления данными"),
            ],
            status_code=404,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page() -> HTMLResponse:
    return _production_page(
        title="Система прогнозирования футбольных матчей",
        heading="Система прогнозирования футбольных матчей",
        description="Информационная система машинного обучения для прогнозирования результатов футбольных матчей",
        badge="Статус системы: работает",
    )


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui() -> HTMLResponse:
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Документация API",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )
    html = response.body.decode("utf-8")
    home_link = """
<div style="padding: 12px 20px; background: #0f1f16; border-bottom: 1px solid #263a2d;">
  <a href="/" style="color: #9be15d; font-family: sans-serif; font-weight: 700; text-decoration: none;">← На главную</a>
</div>
"""
    html = html.replace("<body>", f"<body>{home_link}", 1)
    return HTMLResponse(content=html)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=APP_TITLE, version=APP_VERSION)


@app.get("/db/health", response_model=DatabaseHealthResponse)
def db_health() -> DatabaseHealthResponse:
    with SessionLocal() as db:
        db.execute(text("select 1"))
    return DatabaseHealthResponse(status="ok", database=engine.dialect.name)


@app.get("/scheduler/health")
def scheduler_health() -> dict:
    return get_scheduler_health()


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


@app.get("/users/me/history/unread-count", response_model=PredictionHistoryUnreadCountResponse)
def user_history_unread_count(
    current_user: User = Depends(get_current_user),
) -> PredictionHistoryUnreadCountResponse:
    with SessionLocal() as db:
        return get_user_history_unread_count(db, current_user.id)


@app.post("/users/me/history/mark-viewed", response_model=PredictionHistoryViewedResponse)
def user_history_mark_viewed(
    current_user: User = Depends(get_current_user),
) -> PredictionHistoryViewedResponse:
    with SessionLocal() as db:
        return mark_user_history_viewed(db, current_user.id)


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
