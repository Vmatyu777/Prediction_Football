from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FINAL_APP_METADATA_PATH = PROJECT_ROOT / "configs" / "final_app_models.json"
FINAL_APP_MODELS_DIR = PROJECT_ROOT / "models" / "final_app"
DATABASE_PATH = PROJECT_ROOT / "data" / "app" / "football.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

APP_TITLE = "Prediction Football API"
APP_VERSION = "0.1.0"
