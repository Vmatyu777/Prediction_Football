from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.init_db import init_db
from src.api.database.models import (
    Bookmaker,
    MatchSource,
    MatchStatus,
    Metric,
    ModelType,
    PredictionCharacteristic,
    UserRole,
)
from src.api.database.session import SessionLocal


MATCH_STATUSES = ["scheduled", "finished", "postponed", "cancelled"]
MATCH_SOURCES = ["historical", "demo", "api"]
USER_ROLES = ["user", "admin"]
MODEL_TYPES = ["LogisticRegression", "CatBoostClassifier", "Ridge"]
METRICS = [
    "accuracy",
    "macro_f1",
    "balanced_accuracy",
    "draw_recall",
    "f1",
    "yes_recall",
    "no_recall",
    "mae",
    "rmse",
]
PREDICTION_CHARACTERISTICS = [
    "BTTS",
    "Over2.5",
    "Corners Over9.5",
    "Yellow Cards Over3.5",
    "Exact Score",
]
BOOKMAKERS = ["Market Average"]


def get_or_create_by_name(db: Session, model_class: type, name: str) -> bool:
    existing = db.query(model_class).filter(model_class.name == name).first()
    if existing:
        return False

    db.add(model_class(name=name))
    return True


def seed_db() -> dict[str, int]:
    init_db()
    inserted_counts = {
        "match_statuses": 0,
        "match_sources": 0,
        "user_roles": 0,
        "model_types": 0,
        "metrics": 0,
        "prediction_characteristics": 0,
        "bookmakers": 0,
    }

    with SessionLocal() as db:
        for name in MATCH_STATUSES:
            inserted_counts["match_statuses"] += int(get_or_create_by_name(db, MatchStatus, name))
        for name in MATCH_SOURCES:
            inserted_counts["match_sources"] += int(get_or_create_by_name(db, MatchSource, name))
        for name in USER_ROLES:
            inserted_counts["user_roles"] += int(get_or_create_by_name(db, UserRole, name))
        for name in MODEL_TYPES:
            inserted_counts["model_types"] += int(get_or_create_by_name(db, ModelType, name))
        for name in METRICS:
            inserted_counts["metrics"] += int(get_or_create_by_name(db, Metric, name))
        for name in PREDICTION_CHARACTERISTICS:
            inserted_counts["prediction_characteristics"] += int(
                get_or_create_by_name(db, PredictionCharacteristic, name)
            )
        for name in BOOKMAKERS:
            inserted_counts["bookmakers"] += int(get_or_create_by_name(db, Bookmaker, name))

        db.commit()

    return inserted_counts


def main() -> None:
    inserted_counts = seed_db()
    print("Reference data seed completed.")
    for table_name, count in inserted_counts.items():
        print(f"{table_name}: inserted {count}")


if __name__ == "__main__":
    main()
