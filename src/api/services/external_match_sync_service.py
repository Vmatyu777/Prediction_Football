from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.api.database.models import Country, ExternalSource, League, Match, MatchSource, MatchStatus, Season, Team
from src.api.services.api_football_client import ApiFootballClient


API_FOOTBALL_SOURCE = "API-FOOTBALL"
API_MATCH_SOURCE = "api"

API_FOOTBALL_TOP_LEAGUES = {
    "Premier League": {"api_id": 39, "country": "England", "local_name": "Premier League"},
    "La Liga": {"api_id": 140, "country": "Spain", "local_name": "La Liga"},
    "Serie A": {"api_id": 135, "country": "Italy", "local_name": "Serie A"},
    "Bundesliga": {"api_id": 78, "country": "Germany", "local_name": "Bundesliga"},
    "Ligue 1": {"api_id": 61, "country": "France", "local_name": "Ligue 1"},
}

TEAM_ALIASES = {
    ("England", "Manchester City"): "Man City",
    ("England", "Manchester United"): "Man United",
    ("England", "Nottingham Forest"): "Nottm Forest",
    ("Spain", "Athletic Club"): "Ath Bilbao",
    ("Spain", "Atletico Madrid"): "Ath Madrid",
    ("Spain", "Celta Vigo"): "Celta",
    ("Spain", "Espanyol"): "Espanol",
    ("Spain", "Rayo Vallecano"): "Vallecano",
    ("Spain", "Real Betis"): "Betis",
    ("Spain", "Real Sociedad"): "Sociedad",
    ("Italy", "AC Milan"): "Milan",
    ("Italy", "AS Roma"): "Roma",
    ("Italy", "Hellas Verona"): "Verona",
    ("Germany", "1. FC Heidenheim"): "Heidenheim",
    ("Germany", "1899 Hoffenheim"): "Hoffenheim",
    ("Germany", "Bayer Leverkusen"): "Leverkusen",
    ("Germany", "Bayern München"): "Bayern Munich",
    ("Germany", "Borussia Dortmund"): "Dortmund",
    ("Germany", "Borussia Mönchengladbach"): "MGladbach",
    ("Germany", "Eintracht Frankfurt"): "Ein Frankfurt",
    ("Germany", "FC Augsburg"): "Augsburg",
    ("Germany", "FC St. Pauli"): "St Pauli",
    ("Germany", "FSV Mainz 05"): "Mainz",
    ("Germany", "SC Freiburg"): "Freiburg",
    ("Germany", "VfB Stuttgart"): "Stuttgart",
    ("Germany", "VfL Bochum"): "Bochum",
    ("Germany", "VfL Wolfsburg"): "Wolfsburg",
    ("France", "Paris Saint Germain"): "Paris SG",
    ("France", "Saint Etienne"): "St Etienne",
    ("France", "Stade Brestois 29"): "Brest",
}

API_STATUS_TO_LOCAL = {
    "TBD": "scheduled",
    "NS": "scheduled",
    "PST": "postponed",
    "CANC": "cancelled",
    "ABD": "cancelled",
    "AWD": "cancelled",
    "WO": "cancelled",
}


@dataclass
class FixtureSyncSummary:
    fixtures_received: int = 0
    matches_inserted: int = 0
    matches_updated: int = 0
    matches_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    match_ids: list[int] = field(default_factory=list)

    def as_dict(self) -> dict[str, int | list[str] | list[int]]:
        return {
            "fixtures_received": self.fixtures_received,
            "matches_inserted": self.matches_inserted,
            "matches_updated": self.matches_updated,
            "matches_skipped": self.matches_skipped,
            "errors": self.errors,
            "warnings": self.warnings,
            "match_ids": self.match_ids,
        }


def fetch_fixture_payloads(
    client: ApiFootballClient,
    *,
    league_ids: list[int],
    season: int | None = None,
    next_matches: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    payloads = []
    for league_id in league_ids:
        payloads.append(
            client.get_fixtures(
                league=league_id,
                season=season,
                next_matches=next_matches,
                from_date=from_date,
                to_date=to_date,
            )
        )
    return payloads


def sync_api_football_fixtures(
    db: Session,
    *,
    fixture_payloads: list[dict[str, Any]],
    dry_run: bool = False,
    synced_at: datetime | None = None,
) -> FixtureSyncSummary:
    summary = FixtureSyncSummary()
    synced_at = synced_at or datetime.now(timezone.utc).replace(tzinfo=None)

    for payload in fixture_payloads:
        fixtures = extract_fixtures(payload)
        summary.fixtures_received += len(fixtures)
        for fixture_item in fixtures:
            sync_fixture(db, fixture_item, summary, dry_run=dry_run, synced_at=synced_at)

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return summary


def extract_fixtures(payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = payload.get("response", [])
    if not isinstance(response, list):
        raise ValueError("API-FOOTBALL fixtures payload must contain a response list")
    return [item for item in response if isinstance(item, dict)]


def sync_fixture(
    db: Session,
    fixture_item: dict[str, Any],
    summary: FixtureSyncSummary,
    *,
    dry_run: bool,
    synced_at: datetime,
) -> None:
    try:
        fixture_id = read_fixture_id(fixture_item)
        local_status_name = map_status(fixture_item)
        if local_status_name is None:
            summary.matches_skipped += 1
            summary.warnings.append(f"Fixture {fixture_id}: status is not supported for fixtures sync")
            return

        league = resolve_league(db, fixture_item)
        if league is None:
            summary.matches_skipped += 1
            summary.warnings.append(f"Fixture {fixture_id}: league was not matched")
            return

        home_team = resolve_team(db, fixture_item, side="home")
        away_team = resolve_team(db, fixture_item, side="away")
        if home_team is None or away_team is None:
            summary.matches_skipped += 1
            missing = []
            if home_team is None:
                missing.append(read_team_name(fixture_item, "home"))
            if away_team is None:
                missing.append(read_team_name(fixture_item, "away"))
            summary.warnings.append(f"Fixture {fixture_id}: team was not matched: {', '.join(missing)}")
            return

        status = get_required_by_name(db, MatchStatus, local_status_name)
        match_source = get_required_by_name(db, MatchSource, API_MATCH_SOURCE)
        external_source = get_required_by_name(db, ExternalSource, API_FOOTBALL_SOURCE)
        existing = (
            db.query(Match)
            .filter(
                Match.external_source_id == external_source.id,
                Match.external_match_id == str(fixture_id),
            )
            .first()
        )

        if existing is None:
            summary.matches_inserted += 1
            if dry_run:
                return
            season = get_or_create_season(db, league, parse_match_datetime(fixture_item))
            match = Match(
                match_date=parse_match_datetime(fixture_item),
                season_id=season.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                status_id=status.id,
                source_id=match_source.id,
                external_source_id=external_source.id,
                external_match_id=str(fixture_id),
                last_synced_at=synced_at,
            )
            db.add(match)
            db.flush()
            summary.match_ids.append(match.id)
            return

        summary.matches_updated += 1
        if dry_run:
            summary.match_ids.append(existing.id)
            return

        season = get_or_create_season(db, league, parse_match_datetime(fixture_item))
        existing.match_date = parse_match_datetime(fixture_item)
        existing.season_id = season.id
        existing.home_team_id = home_team.id
        existing.away_team_id = away_team.id
        existing.status_id = status.id
        existing.source_id = match_source.id
        existing.last_synced_at = synced_at
        summary.match_ids.append(existing.id)
    except (KeyError, TypeError, ValueError) as error:
        summary.matches_skipped += 1
        summary.errors.append(f"Fixture skipped: {error}")


def read_fixture_id(fixture_item: dict[str, Any]) -> int:
    return int(fixture_item["fixture"]["id"])


def map_status(fixture_item: dict[str, Any]) -> str | None:
    status_short = str(fixture_item.get("fixture", {}).get("status", {}).get("short", "")).upper()
    return API_STATUS_TO_LOCAL.get(status_short)


def resolve_league(db: Session, fixture_item: dict[str, Any]) -> League | None:
    league_payload = fixture_item.get("league", {})
    api_league_name = str(league_payload.get("name", ""))
    country_name = str(league_payload.get("country", ""))
    mapping = API_FOOTBALL_TOP_LEAGUES.get(api_league_name)
    local_league_name = str(mapping["local_name"]) if mapping else api_league_name
    local_country_name = str(mapping["country"]) if mapping else country_name

    return (
        db.query(League)
        .join(Country)
        .filter(League.name == local_league_name, Country.name == local_country_name)
        .first()
    )


def resolve_team(db: Session, fixture_item: dict[str, Any], *, side: str) -> Team | None:
    team_name = read_team_name(fixture_item, side)
    country_name = str(fixture_item.get("league", {}).get("country", ""))
    exact = (
        db.query(Team)
        .join(Country)
        .filter(Team.name == team_name, Country.name == country_name)
        .first()
    )
    if exact is not None:
        return exact

    alias_name = TEAM_ALIASES.get((country_name, team_name))
    if alias_name is None:
        return None

    return (
        db.query(Team)
        .join(Country)
        .filter(Team.name == alias_name, Country.name == country_name)
        .first()
    )


def read_team_name(fixture_item: dict[str, Any], side: str) -> str:
    return str(fixture_item["teams"][side]["name"])


def parse_match_datetime(fixture_item: dict[str, Any]) -> datetime:
    value = str(fixture_item["fixture"]["date"])
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def get_or_create_season(db: Session, league: League, match_date: datetime) -> Season:
    start_year = match_date.year if match_date.month >= 7 else match_date.year - 1
    name = f"{start_year}/{str(start_year + 1)[-2:]}"
    season = db.query(Season).filter(Season.name == name, Season.league_id == league.id).first()
    if season is not None:
        return season

    season = Season(
        name=name,
        start_date=date(start_year, 7, 1),
        end_date=date(start_year + 1, 6, 30),
        league_id=league.id,
    )
    db.add(season)
    db.flush()
    return season


def get_required_by_name(db: Session, model_class: type, name: str):
    item = db.query(model_class).filter(model_class.name == name).first()
    if item is None:
        raise ValueError(f"{model_class.__name__} not found: {name}")
    return item
