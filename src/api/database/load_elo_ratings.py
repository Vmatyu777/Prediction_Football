from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import func


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.init_db import init_db
from src.api.database.models import Team, TeamEloRating
from src.api.database.session import SessionLocal


ELO_RATINGS_PATH = PROJECT_ROOT / "data" / "raw" / "EloRatings.csv"
ROOT_ELO_RATINGS_FALLBACK_PATH = PROJECT_ROOT / "EloRatings.csv"
ELO_CHUNK_SIZE = 100_000


def empty_summary() -> dict[str, int]:
    return {
        "rows_read": 0,
        "elo_rows_inserted": 0,
        "elo_rows_found": 0,
        "skipped_rows": 0,
        "teams_with_elo_history": 0,
        "teams_without_elo_history": 0,
    }


def resolve_elo_ratings_path(csv_path: Path = ELO_RATINGS_PATH) -> Path:
    if csv_path.exists():
        return csv_path
    if csv_path == ELO_RATINGS_PATH and ROOT_ELO_RATINGS_FALLBACK_PATH.exists():
        return ROOT_ELO_RATINGS_FALLBACK_PATH
    raise FileNotFoundError(f"ELO ratings CSV not found: {csv_path}")


def load_elo_ratings(csv_path: Path = ELO_RATINGS_PATH) -> dict[str, int]:
    csv_path = resolve_elo_ratings_path(csv_path)

    init_db()
    summary = empty_summary()

    with SessionLocal() as db:
        teams = {team.name: team.id for team in db.query(Team).all()}
        existing = {
            (team_id, rating_date)
            for team_id, rating_date in db.query(TeamEloRating.team_id, TeamEloRating.rating_date).all()
        }

        for chunk in pd.read_csv(csv_path, usecols=["date", "club", "elo"], chunksize=ELO_CHUNK_SIZE):
            summary["rows_read"] += len(chunk)
            chunk = chunk[chunk["club"].isin(teams.keys())]

            new_rows = []
            for row in chunk.itertuples(index=False):
                if pd.isna(row.date) or pd.isna(row.club) or pd.isna(row.elo):
                    summary["skipped_rows"] += 1
                    continue

                team_id = teams.get(str(row.club))
                if team_id is None:
                    summary["skipped_rows"] += 1
                    continue

                rating_date = pd.to_datetime(row.date).date()
                key = (team_id, rating_date)
                if key in existing:
                    summary["elo_rows_found"] += 1
                    continue

                existing.add(key)
                new_rows.append(
                    TeamEloRating(
                        rating_date=rating_date,
                        elo_value=Decimal(str(row.elo)).quantize(Decimal("0.01")),
                        team_id=team_id,
                    )
                )

            if new_rows:
                db.add_all(new_rows)
                db.flush()
                summary["elo_rows_inserted"] += len(new_rows)

        db.commit()

        teams_with_elo = (
            db.query(func.count(func.distinct(TeamEloRating.team_id))).scalar()
            or 0
        )
        total_teams = db.query(func.count(Team.id)).scalar() or 0
        summary["teams_with_elo_history"] = int(teams_with_elo)
        summary["teams_without_elo_history"] = int(total_teams - teams_with_elo)

    return summary


def main() -> None:
    summary = load_elo_ratings()
    print("ELO ratings load summary")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
