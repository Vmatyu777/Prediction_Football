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
from src.api.services.external_match_sync_service import (
    API_FOOTBALL_TOP_LEAGUES,
    fetch_fixture_payloads,
    sync_api_football_fixtures,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync API-FOOTBALL fixtures into the application database.")
    parser.add_argument("--season", type=int, default=API_FOOTBALL_SEASON)
    parser.add_argument(
        "--league",
        action="append",
        help="API-FOOTBALL league id or configured top-5 league name. Can be passed more than once.",
    )
    parser.add_argument("--next", dest="next_matches", type=int)
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mock-fixtures-path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        fixture_payloads = load_fixture_payloads(args)
        with SessionLocal() as db:
            summary = sync_api_football_fixtures(
                db,
                fixture_payloads=fixture_payloads,
                dry_run=args.dry_run,
            )
        print_summary(summary.as_dict(), dry_run=args.dry_run)
        return 0
    except ValueError as error:
        print(f"Sync failed: {error}")
        return 1


def load_fixture_payloads(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.mock_fixtures_path is not None:
        return load_mock_fixture_payloads(args.mock_fixtures_path)

    if not API_FOOTBALL_API_KEY:
        raise ValueError("API_FOOTBALL_API_KEY is not configured. Set it in local .env or use --mock-fixtures-path.")

    league_ids = resolve_league_ids(args.league)
    client = ApiFootballClient()
    return fetch_fixture_payloads(
        client,
        league_ids=league_ids,
        season=args.season,
        next_matches=args.next_matches,
        from_date=args.from_date,
        to_date=args.to_date,
    )


def load_mock_fixture_payloads(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Mock fixtures file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise ValueError("Mock fixtures file must contain an API-FOOTBALL payload object or a list of payload objects")


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
    print(f"API-FOOTBALL fixtures sync completed. dry_run={dry_run}")
    for key in ["fixtures_received", "matches_inserted", "matches_updated", "matches_skipped"]:
        print(f"{key}: {summary[key]}")

    print("errors:")
    for error in summary["errors"]:
        print(f"- {error}")

    print("warnings:")
    for warning in summary["warnings"]:
        print(f"- {warning}")

    print("match_ids:")
    for match_id in summary["match_ids"]:
        print(f"- {match_id}")


if __name__ == "__main__":
    raise SystemExit(main())
