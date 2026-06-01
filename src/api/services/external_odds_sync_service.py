from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from src.api.database.models import Bookmaker, ExternalSource, Match, Odds
from src.api.services.external_match_sync_service import API_FOOTBALL_SOURCE


MATCH_WINNER_BET_NAMES = {"Match Winner", "Match Result", "1X2"}
OVER_UNDER_BET_NAMES = {"Goals Over/Under", "Over/Under", "Total Goals"}
HOME_VALUES = {"Home", "1"}
DRAW_VALUES = {"Draw", "X"}
AWAY_VALUES = {"Away", "2"}
OVER25_VALUES = {"Over 2.5", "Over2.5", "Over 2,5"}
UNDER25_VALUES = {"Under 2.5", "Under2.5", "Under 2,5"}
MAX_BOOKMAKER_NAME_LENGTH = 20


@dataclass
class OddsSyncSummary:
    odds_received: int = 0
    odds_inserted: int = 0
    odds_updated: int = 0
    odds_skipped: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    odds_ids: list[int] = field(default_factory=list)

    def as_dict(self) -> dict[str, int | list[int] | list[str]]:
        return {
            "odds_received": self.odds_received,
            "odds_inserted": self.odds_inserted,
            "odds_updated": self.odds_updated,
            "odds_skipped": self.odds_skipped,
            "warnings": self.warnings,
            "errors": self.errors,
            "odds_ids": self.odds_ids,
        }


def sync_api_football_odds(
    db: Session,
    *,
    odds_payloads: list[dict[str, Any]],
    dry_run: bool = False,
    collected_at: datetime | None = None,
) -> OddsSyncSummary:
    summary = OddsSyncSummary()
    collected_at = collected_at or datetime.now(timezone.utc).replace(tzinfo=None)

    for payload in odds_payloads:
        odds_items = extract_odds_items(payload)
        summary.odds_received += len(odds_items)
        for odds_item in odds_items:
            sync_odds_item(db, odds_item, summary, dry_run=dry_run, collected_at=collected_at)

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return summary


def extract_odds_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = payload.get("response", [])
    if not isinstance(response, list):
        raise ValueError("API-FOOTBALL odds payload must contain a response list")
    return [item for item in response if isinstance(item, dict)]


def sync_odds_item(
    db: Session,
    odds_item: dict[str, Any],
    summary: OddsSyncSummary,
    *,
    dry_run: bool,
    collected_at: datetime,
) -> None:
    try:
        fixture_id = str(read_fixture_id(odds_item))
        match = find_api_match(db, fixture_id)
        if match is None:
            summary.odds_skipped += count_bookmakers(odds_item)
            summary.warnings.append(f"Fixture {fixture_id}: API match was not found")
            return

        bookmakers = odds_item.get("bookmakers", [])
        if not isinstance(bookmakers, list):
            summary.odds_skipped += 1
            summary.warnings.append(f"Fixture {fixture_id}: bookmakers payload is invalid")
            return

        for bookmaker_payload in bookmakers:
            sync_bookmaker_odds(
                db,
                match,
                fixture_id,
                bookmaker_payload,
                summary,
                dry_run=dry_run,
                collected_at=collected_at,
            )
    except (KeyError, TypeError, ValueError) as error:
        summary.odds_skipped += 1
        summary.errors.append(f"Odds item skipped: {error}")


def sync_bookmaker_odds(
    db: Session,
    match: Match,
    fixture_id: str,
    bookmaker_payload: dict[str, Any],
    summary: OddsSyncSummary,
    *,
    dry_run: bool,
    collected_at: datetime,
) -> None:
    bookmaker_name = str(bookmaker_payload.get("name", "")).strip()
    if not bookmaker_name:
        summary.odds_skipped += 1
        summary.warnings.append(f"Fixture {fixture_id}: bookmaker name is missing")
        return
    if len(bookmaker_name) > MAX_BOOKMAKER_NAME_LENGTH:
        summary.odds_skipped += 1
        summary.warnings.append(f"Fixture {fixture_id}: bookmaker name is too long: {bookmaker_name}")
        return

    parsed = parse_required_odds(bookmaker_payload)
    if parsed is None:
        summary.odds_skipped += 1
        summary.warnings.append(f"Fixture {fixture_id}: complete 1X2 and Over/Under 2.5 odds were not found for {bookmaker_name}")
        return

    bookmaker = db.query(Bookmaker).filter(Bookmaker.name == bookmaker_name).first()
    existing = None
    if bookmaker is not None:
        existing = db.query(Odds).filter(Odds.match_id == match.id, Odds.bookmaker_id == bookmaker.id).first()

    if existing is None:
        summary.odds_inserted += 1
        if dry_run:
            return
        if bookmaker is None:
            bookmaker = Bookmaker(name=bookmaker_name)
            db.add(bookmaker)
            db.flush()
        odds = Odds(
            home_win_odds=parsed["home_win_odds"],
            draw_odds=parsed["draw_odds"],
            away_win_odds=parsed["away_win_odds"],
            over25_odds=parsed["over25_odds"],
            under25_odds=parsed["under25_odds"],
            collected_at=collected_at,
            match_id=match.id,
            bookmaker_id=bookmaker.id,
        )
        db.add(odds)
        db.flush()
        summary.odds_ids.append(odds.id)
        return

    summary.odds_updated += 1
    if dry_run:
        summary.odds_ids.append(existing.id)
        return

    existing.home_win_odds = parsed["home_win_odds"]
    existing.draw_odds = parsed["draw_odds"]
    existing.away_win_odds = parsed["away_win_odds"]
    existing.over25_odds = parsed["over25_odds"]
    existing.under25_odds = parsed["under25_odds"]
    existing.collected_at = collected_at
    summary.odds_ids.append(existing.id)


def parse_required_odds(bookmaker_payload: dict[str, Any]) -> dict[str, Decimal] | None:
    result: dict[str, Decimal] = {}
    bets = bookmaker_payload.get("bets", [])
    if not isinstance(bets, list):
        return None

    for bet in bets:
        bet_name = str(bet.get("name", ""))
        values = bet.get("values", [])
        if not isinstance(values, list):
            continue

        if bet_name in MATCH_WINNER_BET_NAMES:
            for item in values:
                value_name = str(item.get("value", ""))
                if value_name in HOME_VALUES:
                    result["home_win_odds"] = decimal_odds(item.get("odd"))
                elif value_name in DRAW_VALUES:
                    result["draw_odds"] = decimal_odds(item.get("odd"))
                elif value_name in AWAY_VALUES:
                    result["away_win_odds"] = decimal_odds(item.get("odd"))
        elif bet_name in OVER_UNDER_BET_NAMES:
            for item in values:
                value_name = str(item.get("value", ""))
                if value_name in OVER25_VALUES:
                    result["over25_odds"] = decimal_odds(item.get("odd"))
                elif value_name in UNDER25_VALUES:
                    result["under25_odds"] = decimal_odds(item.get("odd"))

    required = {"home_win_odds", "draw_odds", "away_win_odds", "over25_odds", "under25_odds"}
    if not required.issubset(result):
        return None
    return result


def decimal_odds(value: Any) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as error:
        raise ValueError(f"Invalid odds value: {value}") from error


def read_fixture_id(odds_item: dict[str, Any]) -> int:
    return int(odds_item["fixture"]["id"])


def find_api_match(db: Session, fixture_id: str) -> Match | None:
    external_source = db.query(ExternalSource).filter(ExternalSource.name == API_FOOTBALL_SOURCE).first()
    if external_source is None:
        return None
    return (
        db.query(Match)
        .filter(Match.external_source_id == external_source.id, Match.external_match_id == fixture_id)
        .first()
    )


def count_bookmakers(odds_item: dict[str, Any]) -> int:
    bookmakers = odds_item.get("bookmakers", [])
    if isinstance(bookmakers, list) and bookmakers:
        return len(bookmakers)
    return 1
