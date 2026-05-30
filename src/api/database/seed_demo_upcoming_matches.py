from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.init_db import init_db
from src.api.database.models import Bookmaker, League, Match, MatchSource, MatchStatus, Odds, Season, Team
from src.api.database.session import SessionLocal


DEMO_BOOKMAKER = "Market Average"
DEMO_SEASON_NAME = "2025/26"
DEMO_SEASON_START = date(2025, 7, 1)
DEMO_SEASON_END = date(2026, 6, 30)
DEMO_MATCHES = [
    {
        "league": "Premier League",
        "home_team": "Liverpool",
        "away_team": "Arsenal",
        "days_ahead": 7,
        "hour": 18,
        "odds": ("2.35", "3.45", "2.80", "1.70", "2.12"),
    },
    {
        "league": "La Liga",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        "days_ahead": 8,
        "hour": 21,
        "odds": ("2.20", "3.60", "3.05", "1.55", "2.42"),
    },
    {
        "league": "Serie A",
        "home_team": "Inter",
        "away_team": "Milan",
        "days_ahead": 9,
        "hour": 20,
        "odds": ("2.05", "3.25", "3.70", "1.86", "1.96"),
    },
    {
        "league": "Bundesliga",
        "home_team": "Bayern Munich",
        "away_team": "Dortmund",
        "days_ahead": 10,
        "hour": 19,
        "odds": ("1.70", "4.10", "4.35", "1.48", "2.65"),
    },
    {
        "league": "Ligue 1",
        "home_team": "Paris SG",
        "away_team": "Marseille",
        "days_ahead": 11,
        "hour": 21,
        "odds": ("1.65", "4.00", "4.80", "1.62", "2.30"),
    },
]


def demo_match_datetime(days_ahead: int, hour: int) -> datetime:
    target_date = datetime.utcnow().date() + timedelta(days=days_ahead)
    return datetime(target_date.year, target_date.month, target_date.day, hour, 0, 0)


def decimal_odds(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def get_required_by_name(db: Session, model_class: type, name: str):
    item = db.query(model_class).filter(model_class.name == name).first()
    if item is None:
        raise ValueError(f"{model_class.__name__} not found: {name}")
    return item


def get_or_create_demo_season(db: Session, league_name: str) -> Season:
    league = get_required_by_name(db, League, league_name)
    season = (
        db.query(Season)
        .filter(Season.name == DEMO_SEASON_NAME, Season.league_id == league.id)
        .first()
    )
    if season is not None:
        return season

    season = Season(
        name=DEMO_SEASON_NAME,
        start_date=DEMO_SEASON_START,
        end_date=DEMO_SEASON_END,
        league_id=league.id,
    )
    db.add(season)
    db.flush()
    return season


def get_or_create_bookmaker(db: Session) -> Bookmaker:
    bookmaker = db.query(Bookmaker).filter(Bookmaker.name == DEMO_BOOKMAKER).first()
    if bookmaker is not None:
        return bookmaker
    bookmaker = Bookmaker(name=DEMO_BOOKMAKER)
    db.add(bookmaker)
    db.flush()
    return bookmaker


def get_or_create_match_source(db: Session) -> MatchSource:
    source = db.query(MatchSource).filter(MatchSource.name == "demo").first()
    if source is not None:
        return source
    source = MatchSource(name="demo")
    db.add(source)
    db.flush()
    return source


def find_existing_demo_match(
    db: Session,
    home_team_id: int,
    away_team_id: int,
    scheduled_status_id: int,
    demo_source_id: int,
) -> Match | None:
    return (
        db.query(Match)
        .filter(
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id,
            Match.status_id == scheduled_status_id,
            Match.source_id == demo_source_id,
            ~Match.result.has(),
        )
        .first()
    )


def get_or_create_demo_match(
    db: Session,
    item: dict,
    scheduled_status: MatchStatus,
    demo_source: MatchSource,
) -> tuple[Match, bool]:
    season = get_or_create_demo_season(db, item["league"])
    home_team = get_required_by_name(db, Team, item["home_team"])
    away_team = get_required_by_name(db, Team, item["away_team"])
    match = find_existing_demo_match(db, home_team.id, away_team.id, scheduled_status.id, demo_source.id)
    if match is not None:
        match.season_id = season.id
        match.match_date = demo_match_datetime(item["days_ahead"], item["hour"])
        return match, False

    match = Match(
        match_date=demo_match_datetime(item["days_ahead"], item["hour"]),
        season_id=season.id,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        status_id=scheduled_status.id,
        source_id=demo_source.id,
    )
    db.add(match)
    db.flush()
    return match, True


def ensure_demo_odds(
    db: Session,
    match: Match,
    bookmaker: Bookmaker,
    odds_values: tuple[str, str, str, str, str],
) -> bool:
    existing = (
        db.query(Odds)
        .filter(
            Odds.match_id == match.id,
            Odds.bookmaker_id == bookmaker.id,
        )
        .first()
    )
    if existing is not None:
        return False

    home_odds, draw_odds, away_odds, over25_odds, under25_odds = odds_values
    db.add(
        Odds(
            home_win_odds=decimal_odds(home_odds),
            draw_odds=decimal_odds(draw_odds),
            away_win_odds=decimal_odds(away_odds),
            over25_odds=decimal_odds(over25_odds),
            under25_odds=decimal_odds(under25_odds),
            collected_at=datetime.utcnow(),
            match_id=match.id,
            bookmaker_id=bookmaker.id,
        )
    )
    return True


def seed_demo_upcoming_matches() -> dict[str, int | list[int]]:
    init_db()
    summary: dict[str, int | list[int]] = {
        "matches_inserted": 0,
        "matches_found": 0,
        "odds_inserted": 0,
        "odds_found": 0,
        "match_ids": [],
    }

    with SessionLocal() as db:
        scheduled_status = get_required_by_name(db, MatchStatus, "scheduled")
        demo_source = get_or_create_match_source(db)
        bookmaker = get_or_create_bookmaker(db)

        for item in DEMO_MATCHES:
            match, inserted = get_or_create_demo_match(db, item, scheduled_status, demo_source)
            summary["match_ids"].append(match.id)
            summary["matches_inserted" if inserted else "matches_found"] += 1
            odds_inserted = ensure_demo_odds(db, match, bookmaker, item["odds"])
            summary["odds_inserted" if odds_inserted else "odds_found"] += 1

        db.commit()

    return summary


def main() -> None:
    summary = seed_demo_upcoming_matches()
    print("Demo upcoming matches seed completed.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
