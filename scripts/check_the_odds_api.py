from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
TARGET_SPORTS = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one",
}


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def api_get(base_url: str, endpoint: str, params: dict | None = None) -> tuple[int, dict | list, dict]:
    query = f"?{urlencode(params or {})}" if params else ""
    request = Request(f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}{query}", method="GET")
    try:
        with urlopen(request, timeout=30) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload, headers
    except HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
        return exc.code, payload, {key.lower(): value for key, value in exc.headers.items()}


def quota_headers(headers: dict) -> dict:
    return {
        key: value
        for key, value in headers.items()
        if "requests" in key or "remaining" in key or "used" in key or "last" in key
    }


def match_winner_bookmakers(event: dict) -> list[dict]:
    rows = []
    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = market.get("outcomes", [])
            rows.append(
                {
                    "key": bookmaker.get("key"),
                    "title": bookmaker.get("title"),
                    "last_update": bookmaker.get("last_update"),
                    "outcomes": outcomes,
                }
            )
    return rows


def market_average(bookmakers: list[dict]) -> dict | None:
    prices: dict[str, list[float]] = {}
    for bookmaker in bookmakers:
        for outcome in bookmaker.get("outcomes", []):
            prices.setdefault(outcome.get("name"), []).append(float(outcome.get("price")))
    if not prices:
        return None
    return {name: round(sum(values) / len(values), 4) for name, values in prices.items() if values}


def summarize_event(event: dict | None) -> dict | None:
    if event is None:
        return None
    bookmakers = match_winner_bookmakers(event)
    return {
        "id": event.get("id"),
        "sport_key": event.get("sport_key"),
        "sport_title": event.get("sport_title"),
        "commence_time": event.get("commence_time"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "bookmakers_count": len(bookmakers),
        "bookmakers_sample": bookmakers[:3],
        "market_average": market_average(bookmakers),
    }


def main() -> None:
    load_env()
    api_key = os.environ.get("THE_ODDS_API_KEY")
    base_url = os.environ.get("THE_ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
    if not api_key:
        raise SystemExit("THE_ODDS_API_KEY is not set")

    sports_status, sports_payload, sports_headers = api_get(base_url, "sports", {"apiKey": api_key})
    active_keys = {sport.get("key"): sport for sport in sports_payload if isinstance(sports_payload, list)}
    report = {
        "base_url": base_url,
        "auth": "apiKey query parameter",
        "key_works": sports_status == 200,
        "sports_status": sports_status,
        "quota_headers": quota_headers(sports_headers),
        "target_sports": {},
    }

    for name, sport_key in TARGET_SPORTS.items():
        odds_status, odds_payload, odds_headers = api_get(
            base_url,
            f"sports/{sport_key}/odds",
            {
                "apiKey": api_key,
                "regions": "eu,uk",
                "markets": "h2h",
                "oddsFormat": "decimal",
            },
        )
        events = odds_payload if isinstance(odds_payload, list) else []
        report["target_sports"][name] = {
            "sport_key": sport_key,
            "listed": sport_key in active_keys,
            "sport": active_keys.get(sport_key),
            "odds_status": odds_status,
            "odds_errors": odds_payload if odds_status >= 400 else None,
            "quota_headers": quota_headers(odds_headers),
            "event_count": len(events),
            "sample_event": summarize_event(events[0] if events else None),
        }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
