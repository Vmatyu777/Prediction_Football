from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")

FINAL_APP_METADATA_PATH = PROJECT_ROOT / "configs" / "final_app_models.json"
FINAL_APP_MODELS_DIR = PROJECT_ROOT / "models" / "final_app"
DATABASE_PATH = PROJECT_ROOT / "data" / "app" / "football.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
BACKUP_DIR = PROJECT_ROOT / os.getenv("BACKUP_DIR", "backups")
BACKUP_FILE_TEMPLATE = os.getenv("BACKUP_FILE_TEMPLATE", "football_backup_%Y%m%d_%H%M%S.sql")

APP_TITLE = "Prediction Football API"
APP_VERSION = "0.1.0"

AUTH_SECRET_KEY = os.getenv("PREDICTION_FOOTBALL_AUTH_SECRET", "change-this-development-secret")
AUTH_ALGORITHM = "HS256"
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("PREDICTION_FOOTBALL_TOKEN_MINUTES", "1440"))
ADMIN_SESSION_SECRET = os.getenv("PREDICTION_FOOTBALL_ADMIN_SESSION_SECRET", AUTH_SECRET_KEY)

API_FOOTBALL_API_KEY = os.getenv("API_FOOTBALL_API_KEY", "")
API_FOOTBALL_BASE_URL = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
API_FOOTBALL_TIMEOUT_SECONDS = float(os.getenv("API_FOOTBALL_TIMEOUT_SECONDS", "20"))
API_FOOTBALL_SEASON = int(os.getenv("API_FOOTBALL_SEASON", "2026"))


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


API_FOOTBALL_SCHEDULER_ENABLED = _env_bool("API_FOOTBALL_SCHEDULER_ENABLED", True)
API_FOOTBALL_SCHEDULER_TIMEZONE = os.getenv("API_FOOTBALL_SCHEDULER_TIMEZONE", "Europe/Moscow")
API_FOOTBALL_FIXTURES_SYNC_TIME = os.getenv("API_FOOTBALL_FIXTURES_SYNC_TIME", "03:00")
API_FOOTBALL_ODDS_SYNC_TIME = os.getenv("API_FOOTBALL_ODDS_SYNC_TIME", "06:00")
API_FOOTBALL_RESULTS_SYNC_TIME = os.getenv("API_FOOTBALL_RESULTS_SYNC_TIME", "23:30")
API_FOOTBALL_FIXTURES_DAYS_AHEAD = int(os.getenv("API_FOOTBALL_FIXTURES_DAYS_AHEAD", "14"))
API_FOOTBALL_ODDS_DAYS_AHEAD = int(os.getenv("API_FOOTBALL_ODDS_DAYS_AHEAD", "7"))
API_FOOTBALL_RESULTS_LOOKBACK_DAYS = int(os.getenv("API_FOOTBALL_RESULTS_LOOKBACK_DAYS", "2"))
API_FOOTBALL_MAX_SYNC_FIXTURES = int(os.getenv("API_FOOTBALL_MAX_SYNC_FIXTURES", "25"))
