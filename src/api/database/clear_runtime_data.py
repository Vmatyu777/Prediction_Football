from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.database.models import (
    Match,
    Model,
    ModelMetric,
    Odds,
    Prediction,
    PredictionCharacteristicValue,
    Team,
    TeamEloRating,
    User,
    UserQueryHistory,
)
from src.api.database.session import SessionLocal


RUNTIME_TABLES = [
    ("user_query_history", UserQueryHistory),
    ("prediction_characteristic_values", PredictionCharacteristicValue),
    ("predictions", Prediction),
    ("users", User),
]

DOMAIN_TABLES = [
    ("matches", Match),
    ("odds", Odds),
    ("teams", Team),
    ("models", Model),
    ("model_metrics", ModelMetric),
    ("team_elo_ratings", TeamEloRating),
]


def count_rows(db: Session, model: type) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def clear_runtime_data() -> None:
    print("Development-only cleanup: clearing runtime/demo data.")
    print("Domain football data, model metadata, metrics, odds, and ELO ratings are preserved.")

    with SessionLocal() as db:
        before_runtime = {name: count_rows(db, model) for name, model in RUNTIME_TABLES}
        before_domain = {name: count_rows(db, model) for name, model in DOMAIN_TABLES}

        for _, model in RUNTIME_TABLES:
            db.execute(delete(model))
        db.commit()

        after_runtime = {name: count_rows(db, model) for name, model in RUNTIME_TABLES}
        after_domain = {name: count_rows(db, model) for name, model in DOMAIN_TABLES}

    print("\nCleared runtime tables:")
    for table_name in before_runtime:
        removed = before_runtime[table_name] - after_runtime[table_name]
        print(f"- {table_name}: before={before_runtime[table_name]}, after={after_runtime[table_name]}, removed={removed}")

    print("\nPreserved domain tables:")
    for table_name in before_domain:
        unchanged = before_domain[table_name] == after_domain[table_name]
        status = "unchanged" if unchanged else "changed"
        print(f"- {table_name}: before={before_domain[table_name]}, after={after_domain[table_name]} ({status})")


if __name__ == "__main__":
    clear_runtime_data()
