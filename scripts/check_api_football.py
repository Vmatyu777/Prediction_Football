from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
TOP_LEAGUES = [
    ("Premier League", "England"),
    ("La Liga", "Spain"),
    ("Serie A", "Italy"),
    ("Bundesliga", "Germany"),
    ("Ligue 1", "France"),
]


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def api_get(base_url: str, api_key: str, endpoint: str, params: dict | None = None) -> tuple[dict, dict]:
    query = f"?{urlencode(params or {})}" if params else ""
    request = Request(
        f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}{query}",
        headers={
            "x-apisports-key": api_key,
            "Accept": "application/json",
        },
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        payload = json.loads(response.read().decode("utf-8"))
    return payload, headers


def quota_headers(headers: dict) -> dict:
    interesting = {}
    for key, value in headers.items():
        lowered = key.lower()
        if "rate" in lowered or "limit" in lowered or "request" in lowered or "remaining" in lowered:
            interesting[key] = value
    return interesting


def first_current_season(league: dict) -> int | None:
    for season in league.get("seasons", []):
        if season.get("current"):
            return season.get("year")
    seasons = [season.get("year") for season in league.get("seasons", []) if season.get("year")]
    return max(seasons) if seasons else None


def find_match_winner_bet(bookmaker: dict) -> dict | None:
    for bet in bookmaker.get("bets", []):
        name = str(bet.get("name", "")).lower()
        if name in {"match winner", "1x2"}:
            return bet
    return None


def summarize_fixture(fixture: dict | None) -> dict | None:
    if fixture is None:
        return None
    return {
        "fixture_id": fixture.get("fixture", {}).get("id"),
        "timezone": fixture.get("fixture", {}).get("timezone"),
        "date": fixture.get("fixture", {}).get("date"),
        "timestamp": fixture.get("fixture", {}).get("timestamp"),
        "status": fixture.get("fixture", {}).get("status"),
        "league": fixture.get("league"),
        "home_team": fixture.get("teams", {}).get("home"),
        "away_team": fixture.get("teams", {}).get("away"),
        "goals": fixture.get("goals"),
        "score": fixture.get("score"),
    }


def summarize_odds(odds_row: dict | None) -> dict | None:
    if odds_row is None:
        return None
    bookmakers = odds_row.get("bookmakers", [])
    summarized_bookmakers = []
    for bookmaker in bookmakers[:5]:
        bet = find_match_winner_bet(bookmaker)
        summarized_bookmakers.append(
            {
                "id": bookmaker.get("id"),
                "name": bookmaker.get("name"),
                "match_winner": bet,
            }
        )
    return {
        "league": odds_row.get("league"),
        "fixture": odds_row.get("fixture"),
        "update": odds_row.get("update"),
        "bookmakers_count": len(bookmakers),
        "bookmakers_sample": summarized_bookmakers,
    }


def main() -> None:
    load_env(ENV_PATH)
    api_key = os.environ.get("API_FOOTBALL_KEY")
    base_url = os.environ.get("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
    if not api_key:
        raise SystemExit("API_FOOTBALL_KEY is not set")

    report: dict = {
        "base_url": base_url,
        "auth_header": "x-apisports-key",
        "status": None,
        "quota_headers": {},
        "leagues": [],
        "fixtures": {},
        "odds": {},
        "odds_bets": {},
        "historical_fixture_sample": {},
    }

    status_payload, status_headers = api_get(base_url, api_key, "status")
    report["status"] = {
        "errors": status_payload.get("errors"),
        "response": status_payload.get("response"),
    }
    report["quota_headers"] = quota_headers(status_headers)

    for league_name, country in TOP_LEAGUES:
        league_payload, _ = api_get(base_url, api_key, "leagues", {"name": league_name, "country": country})
        responses = league_payload.get("response", [])
        selected = responses[0] if responses else None
        if not selected:
            report["leagues"].append({"name": league_name, "country": country, "found": False})
            continue

        league = selected["league"]
        country_info = selected["country"]
        season = first_current_season(selected)
        league_item = {
            "name": league_name,
            "id": league.get("id"),
            "api_name": league.get("name"),
            "country": country_info.get("name"),
            "current_season": season,
        }
        report["leagues"].append(league_item)

        if season is None:
            report["fixtures"][league_name] = {"count": 0, "sample": None}
            continue

        fixtures_payload, _ = api_get(
            base_url,
            api_key,
            "fixtures",
            {"league": league.get("id"), "season": season, "next": 10},
        )
        fixtures = fixtures_payload.get("response", [])
        report["fixtures"][league_name] = {
            "errors": fixtures_payload.get("errors"),
            "count": len(fixtures),
            "sample": summarize_fixture(fixtures[0] if fixtures else None),
        }

        if fixtures and not report["odds"]:
            fixture_id = fixtures[0]["fixture"]["id"]
            try:
                odds_payload, odds_headers = api_get(base_url, api_key, "odds", {"fixture": fixture_id})
                odds_rows = odds_payload.get("response", [])
                bookmakers = odds_rows[0].get("bookmakers", []) if odds_rows else []
                match_winner_bookmakers = [
                    bookmaker for bookmaker in bookmakers if find_match_winner_bet(bookmaker) is not None
                ]
                report["odds"] = {
                    "fixture_id": fixture_id,
                    "errors": odds_payload.get("errors"),
                    "count": len(odds_rows),
                    "quota_headers": quota_headers(odds_headers),
                    "bookmakers_count": len(bookmakers),
                    "match_winner_bookmakers_count": len(match_winner_bookmakers),
                    "sample": summarize_odds(odds_rows[0] if odds_rows else None),
                }
            except Exception as exc:  # noqa: BLE001
                report["odds"] = {"fixture_id": fixture_id, "error": str(exc)}

    bets_payload, _ = api_get(base_url, api_key, "odds/bets")
    report["odds_bets"] = {
        "errors": bets_payload.get("errors"),
        "match_winner": next(
            (bet for bet in bets_payload.get("response", []) if bet.get("name") == "Match Winner"),
            None,
        ),
        "sample": bets_payload.get("response", [])[:5],
    }

    if report["leagues"]:
        premier_league = next((item for item in report["leagues"] if item.get("name") == "Premier League"), None)
        if premier_league:
            historical_payload, _ = api_get(
                base_url,
                api_key,
                "fixtures",
                {"league": premier_league["id"], "season": 2024},
            )
            historical_fixtures = historical_payload.get("response", [])
            historical_sample = historical_fixtures[0] if historical_fixtures else None
            report["historical_fixture_sample"] = {
                "errors": historical_payload.get("errors"),
                "count": len(historical_fixtures),
                "sample": summarize_fixture(historical_sample),
            }
            if not report["odds"] and historical_sample:
                fixture_id = historical_sample["fixture"]["id"]
                odds_payload, odds_headers = api_get(base_url, api_key, "odds", {"fixture": fixture_id, "bet": 1})
                odds_rows = odds_payload.get("response", [])
                bookmakers = odds_rows[0].get("bookmakers", []) if odds_rows else []
                match_winner_bookmakers = [
                    bookmaker for bookmaker in bookmakers if find_match_winner_bet(bookmaker) is not None
                ]
                report["odds"] = {
                    "fixture_id": fixture_id,
                    "errors": odds_payload.get("errors"),
                    "count": len(odds_rows),
                    "quota_headers": quota_headers(odds_headers),
                    "bookmakers_count": len(bookmakers),
                    "match_winner_bookmakers_count": len(match_winner_bookmakers),
                    "sample": summarize_odds(odds_rows[0] if odds_rows else None),
                }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
