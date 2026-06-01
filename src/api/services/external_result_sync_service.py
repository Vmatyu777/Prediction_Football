from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from src.api.database.models import ExternalSource, Match, MatchResult, MatchStatus
from src.api.services.external_match_sync_service import API_FOOTBALL_SOURCE


FINISHED_STATUSES = {"FT", "AET", "PEN"}
POSTPONED_STATUSES = {"PST"}
CANCELLED_STATUSES = {"CANC", "ABD", "AWD", "WO"}
OUTCOME_ENCODING = {"A": 0, "D": 1, "H": 2}


@dataclass
class ResultSyncSummary:
    fixtures_received: int = 0
    results_inserted: int = 0
    results_updated: int = 0
    results_skipped: int = 0
    statuses_updated: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    match_ids: list[int] = field(default_factory=list)

    def as_dict(self) -> dict[str, int | list[int] | list[str]]:
        return {
            "fixtures_received": self.fixtures_received,
            "results_inserted": self.results_inserted,
            "results_updated": self.results_updated,
            "results_skipped": self.results_skipped,
            "statuses_updated": self.statuses_updated,
            "warnings": self.warnings,
            "errors": self.errors,
            "match_ids": self.match_ids,
        }


def sync_api_football_results(
    db: Session,
    *,
    fixture_payloads: list[dict[str, Any]],
    statistics_payloads: list[dict[str, Any]],
    dry_run: bool = False,
) -> ResultSyncSummary:
    summary = ResultSyncSummary()
    statistics_by_fixture_id = build_statistics_index(statistics_payloads)

    for fixture_item in extract_fixture_items(fixture_payloads):
        summary.fixtures_received += 1
        sync_fixture_result(
            db,
            fixture_item,
            statistics_by_fixture_id,
            summary,
            dry_run=dry_run,
        )

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return summary


def extract_fixture_items(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for payload in payloads:
        response = payload.get("response", [])
        if not isinstance(response, list):
            raise ValueError("API-FOOTBALL fixtures payload must contain a response list")
        items.extend(item for item in response if isinstance(item, dict))
    return items


def build_statistics_index(payloads: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        fixture_id = payload.get("parameters", {}).get("fixture")
        if fixture_id is None:
            continue
        response = payload.get("response", [])
        if isinstance(response, list):
            index[str(fixture_id)] = [item for item in response if isinstance(item, dict)]
    return index


def sync_fixture_result(
    db: Session,
    fixture_item: dict[str, Any],
    statistics_by_fixture_id: dict[str, list[dict[str, Any]]],
    summary: ResultSyncSummary,
    *,
    dry_run: bool,
) -> None:
    try:
        fixture_id = str(read_fixture_id(fixture_item))
        match = find_api_match(db, fixture_id)
        if match is None:
            summary.results_skipped += 1
            summary.warnings.append(f"Fixture {fixture_id}: API match was not found")
            return

        status_short = read_status_short(fixture_item)
        if status_short in FINISHED_STATUSES:
            parsed = parse_finished_result(fixture_item, statistics_by_fixture_id.get(fixture_id))
            if parsed is None:
                summary.results_skipped += 1
                summary.warnings.append(f"Fixture {fixture_id}: finished fixture has incomplete score or statistics")
                return
            upsert_match_result(db, match, parsed, summary, dry_run=dry_run)
            update_match_status(db, match, "finished", summary, dry_run=dry_run)
            summary.match_ids.append(match.id)
            return

        if status_short in POSTPONED_STATUSES:
            update_match_status(db, match, "postponed", summary, dry_run=dry_run)
            summary.match_ids.append(match.id)
            return

        if status_short in CANCELLED_STATUSES:
            update_match_status(db, match, "cancelled", summary, dry_run=dry_run)
            summary.match_ids.append(match.id)
            return

        summary.results_skipped += 1
        summary.warnings.append(f"Fixture {fixture_id}: status is not supported for result sync: {status_short}")
    except (KeyError, TypeError, ValueError) as error:
        summary.results_skipped += 1
        summary.errors.append(f"Fixture skipped: {error}")


def parse_finished_result(
    fixture_item: dict[str, Any],
    statistics_items: list[dict[str, Any]] | None,
) -> dict[str, int] | None:
    goals = fixture_item.get("goals", {})
    home_goals = goals.get("home")
    away_goals = goals.get("away")
    if home_goals is None or away_goals is None:
        return None

    totals = parse_statistics_totals(statistics_items)
    if totals is None:
        return None

    home_goals = int(home_goals)
    away_goals = int(away_goals)
    outcome = "H" if home_goals > away_goals else "A" if away_goals > home_goals else "D"
    return {
        "actual_outcome": OUTCOME_ENCODING[outcome],
        "home_goals": home_goals,
        "away_goals": away_goals,
        "total_corners": totals["total_corners"],
        "total_yellow_cards": totals["total_yellow_cards"],
    }


def parse_statistics_totals(statistics_items: list[dict[str, Any]] | None) -> dict[str, int] | None:
    if not statistics_items:
        return None

    corner_values = []
    yellow_values = []
    for item in statistics_items:
        stats = item.get("statistics", [])
        if not isinstance(stats, list):
            continue
        corners = find_stat_value(stats, "Corner Kicks")
        yellows = find_stat_value(stats, "Yellow Cards")
        if corners is None or yellows is None:
            return None
        corner_values.append(corners)
        yellow_values.append(yellows)

    if len(corner_values) < 2 or len(yellow_values) < 2:
        return None

    return {
        "total_corners": sum(corner_values),
        "total_yellow_cards": sum(yellow_values),
    }


def find_stat_value(stats: list[dict[str, Any]], stat_type: str) -> int | None:
    for item in stats:
        if item.get("type") == stat_type:
            value = item.get("value")
            if value is None:
                return None
            return int(value)
    return None


def upsert_match_result(
    db: Session,
    match: Match,
    values: dict[str, int],
    summary: ResultSyncSummary,
    *,
    dry_run: bool,
) -> None:
    existing = db.query(MatchResult).filter(MatchResult.match_id == match.id).first()
    if existing is None:
        summary.results_inserted += 1
        if dry_run:
            return
        db.add(MatchResult(match_id=match.id, **values))
        return

    summary.results_updated += 1
    if dry_run:
        return

    existing.actual_outcome = values["actual_outcome"]
    existing.home_goals = values["home_goals"]
    existing.away_goals = values["away_goals"]
    existing.total_corners = values["total_corners"]
    existing.total_yellow_cards = values["total_yellow_cards"]


def update_match_status(
    db: Session,
    match: Match,
    status_name: str,
    summary: ResultSyncSummary,
    *,
    dry_run: bool,
) -> None:
    status = db.query(MatchStatus).filter(MatchStatus.name == status_name).first()
    if status is None:
        raise ValueError(f"MatchStatus not found: {status_name}")
    if match.status_id != status.id:
        summary.statuses_updated += 1
        if not dry_run:
            match.status_id = status.id


def read_fixture_id(fixture_item: dict[str, Any]) -> int:
    return int(fixture_item["fixture"]["id"])


def read_status_short(fixture_item: dict[str, Any]) -> str:
    return str(fixture_item.get("fixture", {}).get("status", {}).get("short", "")).upper()


def find_api_match(db: Session, fixture_id: str) -> Match | None:
    external_source = db.query(ExternalSource).filter(ExternalSource.name == API_FOOTBALL_SOURCE).first()
    if external_source is None:
        return None
    return (
        db.query(Match)
        .filter(Match.external_source_id == external_source.id, Match.external_match_id == fixture_id)
        .first()
    )
