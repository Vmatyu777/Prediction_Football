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

APP_TITLE = "Prediction Football API"
APP_VERSION = "0.1.0"

AUTH_SECRET_KEY = os.getenv("PREDICTION_FOOTBALL_AUTH_SECRET", "change-this-development-secret")
AUTH_ALGORITHM = "HS256"
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("PREDICTION_FOOTBALL_TOKEN_MINUTES", "1440"))

API_FOOTBALL_API_KEY = os.getenv("API_FOOTBALL_API_KEY", "")
API_FOOTBALL_BASE_URL = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
API_FOOTBALL_TIMEOUT_SECONDS = float(os.getenv("API_FOOTBALL_TIMEOUT_SECONDS", "20"))
API_FOOTBALL_SEASON = int(os.getenv("API_FOOTBALL_SEASON", "2026"))
