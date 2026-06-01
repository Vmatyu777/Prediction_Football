from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.config import API_FOOTBALL_API_KEY, API_FOOTBALL_SEASON
from src.api.database.session import SessionLocal
from src.api.services.api_football_client import ApiFootballClient
from src.api.services.external_match_sync_service import API_FOOTBALL_TOP_LEAGUES
from src.api.services.external_odds_sync_service import sync_api_football_odds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync API-FOOTBALL odds into the application database.")
    parser.add_argument("--fixture-id", action="append", type=int)
    parser.add_argument(
        "--league",
        action="append",
        help="API-FOOTBALL league id or configured top-5 league name. Can be passed more than once.",
    )
    parser.add_argument("--season", type=int, default=API_FOOTBALL_SEASON)
    parser.add_argument("--date")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mock-odds-path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        odds_payloads = load_odds_payloads(args)
        with SessionLocal() as db:
            summary = sync_api_football_odds(
                db,
                odds_payloads=odds_payloads,
                dry_run=args.dry_run,
            )
        print_summary(summary.as_dict(), dry_run=args.dry_run)
        return 0
    except ValueError as error:
        print(f"Odds sync failed: {error}")
        return 1


def load_odds_payloads(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.mock_odds_path is not None:
        return load_mock_odds_payloads(args.mock_odds_path)

    if not API_FOOTBALL_API_KEY:
        raise ValueError("API_FOOTBALL_API_KEY is not configured. Set it in local .env or use --mock-odds-path.")

    client = ApiFootballClient()
    payloads = []
    if args.fixture_id:
        for fixture_id in args.fixture_id:
            payloads.append(client.get_odds(fixture_id=fixture_id, season=args.season))
        return payloads

    league_ids = resolve_league_ids(args.league)
    for league_id in league_ids:
        payloads.append(client.get_odds(league=league_id, season=args.season, date=args.date))
    return payloads


def load_mock_odds_payloads(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Mock odds file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise ValueError("Mock odds file must contain an API-FOOTBALL payload object or a list of payload objects")


def resolve_league_ids(values: list[str] | None) -> list[int]:
    if not values:
        return [int(item["api_id"]) for item in API_FOOTBALL_TOP_LEAGUES.values()]

    league_ids = []
    for value in values:
        if value.isdigit():
            league_ids.append(int(value))
            continue

        mapping = API_FOOTBALL_TOP_LEAGUES.get(value)
        if mapping is None:
            valid_names = ", ".join(API_FOOTBALL_TOP_LEAGUES)
            raise ValueError(f"Unknown league: {value}. Use an API id or one of: {valid_names}")
        league_ids.append(int(mapping["api_id"]))
    return league_ids


def print_summary(summary: dict[str, Any], *, dry_run: bool) -> None:
    print(f"API-FOOTBALL odds sync completed. dry_run={dry_run}")
    for key in [
        "odds_received",
        "bookmakers_checked",
        "bookmakers_with_complete_markets",
        "odds_inserted",
        "odds_updated",
        "odds_skipped",
    ]:
        print(f"{key}: {summary[key]}")

    print("warnings:")
    for warning in summary["warnings"]:
        print(f"- {warning}")

    print("errors:")
    for error in summary["errors"]:
        print(f"- {error}")

    print("odds_ids:")
    for odds_id in summary["odds_ids"]:
        print(f"- {odds_id}")


if __name__ == "__main__":
    raise SystemExit(main())
