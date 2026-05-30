from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
COMPETITIONS = {
    "Premier League": "PL",
    "La Liga": "PD",
    "Serie A": "SA",
    "Bundesliga": "BL1",
    "Ligue 1": "FL1",
}


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def api_get(base_url: str, api_key: str, endpoint: str, params: dict | None = None) -> tuple[int, dict, dict]:
    query = f"?{urlencode(params or {})}" if params else ""
    request = Request(
        f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}{query}",
        headers={"X-Auth-Token": api_key, "Accept": "application/json"},
        method="GET",
    )
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
        if "request" in key or "limit" in key or "remaining" in key or "reset" in key
    }


def summarize_match(match: dict | None) -> dict | None:
    if match is None:
        return None
    return {
        "id": match.get("id"),
        "utcDate": match.get("utcDate"),
        "status": match.get("status"),
        "matchday": match.get("matchday"),
        "stage": match.get("stage"),
        "season": match.get("season"),
        "homeTeam": match.get("homeTeam"),
        "awayTeam": match.get("awayTeam"),
        "score": match.get("score"),
    }


def main() -> None:
    load_env()
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    base_url = os.environ.get("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4")
    if not api_key:
        raise SystemExit("FOOTBALL_DATA_API_KEY is not set")

    status, competitions_payload, headers = api_get(base_url, api_key, "competitions")
    report = {
        "base_url": base_url,
        "auth_header": "X-Auth-Token",
        "key_works": status == 200,
        "status": status,
        "quota_headers": quota_headers(headers),
        "competitions": {},
        "odds": {"available": False, "note": "football-data.org v4 match responses do not include bookmaker odds."},
    }

    for name, code in COMPETITIONS.items():
        comp_status, comp_payload, _ = api_get(base_url, api_key, f"competitions/{code}")
        scheduled_status, scheduled_payload, _ = api_get(
            base_url,
            api_key,
            f"competitions/{code}/matches",
            {"status": "SCHEDULED"},
        )
        matches = scheduled_payload.get("matches", []) if scheduled_status == 200 else []
        report["competitions"][name] = {
            "code": code,
            "competition_status": comp_status,
            "competition": {
                "id": comp_payload.get("id"),
                "name": comp_payload.get("name"),
                "area": comp_payload.get("area"),
                "currentSeason": comp_payload.get("currentSeason"),
            },
            "scheduled_status": scheduled_status,
            "scheduled_errors": scheduled_payload if scheduled_status >= 400 else None,
            "scheduled_count": len(matches),
            "sample_match": summarize_match(matches[0] if matches else None),
        }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
