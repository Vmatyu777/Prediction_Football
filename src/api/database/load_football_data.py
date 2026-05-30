from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.init_db import init_db
from src.api.database.models import (
    Bookmaker,
    Country,
    League,
    Match,
    MatchResult,
    MatchSource,
    MatchStatus,
    Odds,
    Season,
    Team,
)
from src.api.database.session import SessionLocal


CLEANED_MATCHES_PATH = PROJECT_ROOT / "data" / "interim" / "matches_top5_2018_2025_clean.csv"
MARKET_AVERAGE_BOOKMAKER = "Market Average"

DIVISION_METADATA = {
    "E0": {"country": "England", "league": "Premier League"},
    "D1": {"country": "Germany", "league": "Bundesliga"},
    "SP1": {"country": "Spain", "league": "La Liga"},
    "I1": {"country": "Italy", "league": "Serie A"},
    "F1": {"country": "France", "league": "Ligue 1"},
}

OUTCOME_ENCODING = {"A": 0, "D": 1, "H": 2}
REQUIRED_COLUMNS = [
    "Division",
    "MatchDateParsed",
    "HomeTeam",
    "AwayTeam",
    "FTHome",
    "FTAway",
    "FTResult",
    "HomeCorners",
    "AwayCorners",
    "HomeYellow",
    "AwayYellow",
    "OddHome",
    "OddDraw",
    "OddAway",
]


def empty_summary(rows_read: int) -> dict[str, int]:
    return {
        "rows_read": rows_read,
        "countries_inserted": 0,
        "countries_found": 0,
        "leagues_inserted": 0,
        "leagues_found": 0,
        "seasons_inserted": 0,
        "seasons_found": 0,
        "teams_inserted": 0,
        "teams_found": 0,
        "matches_inserted": 0,
        "matches_found": 0,
        "results_inserted": 0,
        "results_found": 0,
        "odds_inserted": 0,
        "odds_found": 0,
        "skipped_rows": 0,
    }


def season_start_year(match_date: datetime) -> int:
    return match_date.year if match_date.month >= 7 else match_date.year - 1


def season_name(start_year: int) -> str:
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def parse_match_datetime(row: pd.Series) -> datetime:
    match_date = str(row["MatchDateParsed"])
    match_time = row.get("MatchTime")
    if pd.isna(match_time):
        return pd.to_datetime(match_date).to_pydatetime()
    return pd.to_datetime(f"{match_date} {match_time}").to_pydatetime()


def decimal_from_row(row: pd.Series, column: str) -> Decimal:
    return Decimal(str(row[column])).quantize(Decimal("0.01"))


def get_or_create_country(
    db: Session,
    cache: dict[str, Country],
    summary: dict[str, int],
    name: str,
) -> Country:
    if name in cache:
        return cache[name]

    country = db.query(Country).filter(Country.name == name).first()
    if country:
        summary["countries_found"] += 1
    else:
        country = Country(name=name)
        db.add(country)
        db.flush()
        summary["countries_inserted"] += 1

    cache[name] = country
    return country


def get_or_create_league(
    db: Session,
    cache: dict[tuple[str, int], League],
    summary: dict[str, int],
    name: str,
    country_id: int,
) -> League:
    key = (name, country_id)
    if key in cache:
        return cache[key]

    league = db.query(League).filter(League.name == name, League.country_id == country_id).first()
    if league:
        summary["leagues_found"] += 1
    else:
        league = League(name=name, country_id=country_id)
        db.add(league)
        db.flush()
        summary["leagues_inserted"] += 1

    cache[key] = league
    return league


def get_or_create_season(
    db: Session,
    cache: dict[tuple[str, int], Season],
    summary: dict[str, int],
    match_date: datetime,
    league_id: int,
) -> Season:
    start_year = season_start_year(match_date)
    name = season_name(start_year)
    key = (name, league_id)
    if key in cache:
        return cache[key]

    season = db.query(Season).filter(Season.name == name, Season.league_id == league_id).first()
    if season:
        summary["seasons_found"] += 1
    else:
        season = Season(
            name=name,
            start_date=date(start_year, 7, 1),
            end_date=date(start_year + 1, 6, 30),
            league_id=league_id,
        )
        db.add(season)
        db.flush()
        summary["seasons_inserted"] += 1

    cache[key] = season
    return season


def get_or_create_team(
    db: Session,
    cache: dict[tuple[str, int], Team],
    summary: dict[str, int],
    name: str,
    country_id: int,
) -> Team:
    key = (name, country_id)
    if key in cache:
        return cache[key]

    team = db.query(Team).filter(Team.name == name, Team.country_id == country_id).first()
    if team:
        summary["teams_found"] += 1
    else:
        team = Team(name=name, country_id=country_id)
        db.add(team)
        db.flush()
        summary["teams_inserted"] += 1

    cache[key] = team
    return team


def get_or_create_by_name(db: Session, model_class: type, name: str):
    existing = db.query(model_class).filter(model_class.name == name).first()
    if existing:
        return existing

    item = model_class(name=name)
    db.add(item)
    db.flush()
    return item


def get_or_create_match(
    db: Session,
    summary: dict[str, int],
    match_date: datetime,
    season_id: int,
    home_team_id: int,
    away_team_id: int,
    status_id: int,
    source_id: int,
) -> Match:
    match = (
        db.query(Match)
        .filter(
            Match.match_date == match_date,
            Match.season_id == season_id,
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id,
        )
        .first()
    )
    if match:
        summary["matches_found"] += 1
        return match

    match = Match(
        match_date=match_date,
        season_id=season_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        status_id=status_id,
        source_id=source_id,
    )
    db.add(match)
    db.flush()
    summary["matches_inserted"] += 1
    return match


def get_or_create_result(db: Session, summary: dict[str, int], row: pd.Series, match_id: int) -> None:
    existing = db.query(MatchResult).filter(MatchResult.match_id == match_id).first()
    if existing:
        summary["results_found"] += 1
        return

    db.add(
        MatchResult(
            actual_outcome=OUTCOME_ENCODING[str(row["FTResult"])],
            home_goals=int(row["FTHome"]),
            away_goals=int(row["FTAway"]),
            total_corners=int(row["HomeCorners"]) + int(row["AwayCorners"]),
            total_yellow_cards=int(row["HomeYellow"]) + int(row["AwayYellow"]),
            match_id=match_id,
        )
    )
    summary["results_inserted"] += 1


def get_or_create_odds(
    db: Session,
    summary: dict[str, int],
    row: pd.Series,
    match_id: int,
    bookmaker_id: int,
    collected_at: datetime,
) -> None:
    existing = db.query(Odds).filter(Odds.match_id == match_id, Odds.bookmaker_id == bookmaker_id).first()
    if existing:
        summary["odds_found"] += 1
        return

    db.add(
        Odds(
            home_win_odds=decimal_from_row(row, "OddHome"),
            draw_odds=decimal_from_row(row, "OddDraw"),
            away_win_odds=decimal_from_row(row, "OddAway"),
            collected_at=collected_at,
            match_id=match_id,
            bookmaker_id=bookmaker_id,
        )
    )
    summary["odds_inserted"] += 1


def row_has_required_values(row: pd.Series) -> bool:
    return not row[REQUIRED_COLUMNS].isna().any()


def load_football_data(csv_path: Path = CLEANED_MATCHES_PATH) -> dict[str, int]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Cleaned matches CSV not found: {csv_path}")

    init_db()
    data = pd.read_csv(csv_path)
    summary = empty_summary(rows_read=len(data))

    country_cache: dict[str, Country] = {}
    league_cache: dict[tuple[str, int], League] = {}
    season_cache: dict[tuple[str, int], Season] = {}
    team_cache: dict[tuple[str, int], Team] = {}

    with SessionLocal() as db:
        finished_status = get_or_create_by_name(db, MatchStatus, "finished")
        historical_source = get_or_create_by_name(db, MatchSource, "historical")
        bookmaker = get_or_create_by_name(db, Bookmaker, MARKET_AVERAGE_BOOKMAKER)

        for _, row in data.iterrows():
            division = str(row["Division"])
            if division not in DIVISION_METADATA or str(row["FTResult"]) not in OUTCOME_ENCODING:
                summary["skipped_rows"] += 1
                continue
            if not row_has_required_values(row):
                summary["skipped_rows"] += 1
                continue

            metadata = DIVISION_METADATA[division]
            match_date = parse_match_datetime(row)

            country = get_or_create_country(db, country_cache, summary, metadata["country"])
            league = get_or_create_league(db, league_cache, summary, metadata["league"], country.id)
            season = get_or_create_season(db, season_cache, summary, match_date, league.id)
            home_team = get_or_create_team(db, team_cache, summary, str(row["HomeTeam"]), country.id)
            away_team = get_or_create_team(db, team_cache, summary, str(row["AwayTeam"]), country.id)
            match = get_or_create_match(
                db=db,
                summary=summary,
                match_date=match_date,
                season_id=season.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                status_id=finished_status.id,
                source_id=historical_source.id,
            )
            get_or_create_result(db, summary, row, match.id)
            get_or_create_odds(db, summary, row, match.id, bookmaker.id, match_date)

        db.commit()

    return summary


def build_database_checks() -> dict[str, int]:
    with SessionLocal() as db:
        match_count = db.query(func.count(Match.id)).scalar()
        result_count = db.query(func.count(MatchResult.id)).scalar()
        odds_count = db.query(func.count(Odds.id)).scalar()
        matches_without_result = (
            db.query(func.count(Match.id))
            .outerjoin(MatchResult, MatchResult.match_id == Match.id)
            .filter(MatchResult.id.is_(None))
            .scalar()
        )
        matches_without_odds = (
            db.query(func.count(Match.id))
            .outerjoin(Odds, Odds.match_id == Match.id)
            .filter(Odds.id.is_(None))
            .scalar()
        )

    return {
        "matches_in_db": int(match_count or 0),
        "results_in_db": int(result_count or 0),
        "odds_in_db": int(odds_count or 0),
        "matches_without_result": int(matches_without_result or 0),
        "matches_without_odds": int(matches_without_odds or 0),
    }


def print_summary(title: str, values: dict[str, int]) -> None:
    print(title)
    for key, value in values.items():
        print(f"{key}: {value}")


def main() -> None:
    summary = load_football_data()
    checks = build_database_checks()
    print_summary("Football data load summary", summary)
    print_summary("Football data database checks", checks)


if __name__ == "__main__":
    main()
