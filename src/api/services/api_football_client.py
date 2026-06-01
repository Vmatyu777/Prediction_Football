from __future__ import annotations

from typing import Any

import httpx

from src.api.config import (
    API_FOOTBALL_API_KEY,
    API_FOOTBALL_BASE_URL,
    API_FOOTBALL_TIMEOUT_SECONDS,
    API_FOOTBALL_SEASON,
)


class ApiFootballClient:
    """Small API-FOOTBALL client with no database writes.

    Planned sync flow:
    - upcoming fixtures: daily;
    - odds: daily for matches in the next 1-7 days;
    - results/statistics: 1-2 times daily after kickoff or after finished matches;
    - monthly retraining is future/admin-controlled work and is not automated here.
    """

    def __init__(
        self,
        *,
        api_key: str = API_FOOTBALL_API_KEY,
        base_url: str = API_FOOTBALL_BASE_URL,
        timeout_seconds: float = API_FOOTBALL_TIMEOUT_SECONDS,
        default_season: int = API_FOOTBALL_SEASON,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.default_season = default_season
        self.transport = transport

    def get_fixtures(
        self,
        *,
        league: int | None = None,
        season: int | None = None,
        fixture_id: int | None = None,
        next_matches: int | None = None,
        date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "league": league,
            "season": season if season is not None else self.default_season,
            "id": fixture_id,
            "next": next_matches,
            "date": date,
            "from": from_date,
            "to": to_date,
            "status": status,
        }
        return self._get("/fixtures", params)

    def get_fixture_statistics(self, *, fixture_id: int) -> dict[str, Any]:
        return self._get("/fixtures/statistics", {"fixture": fixture_id})

    def get_odds(
        self,
        *,
        fixture_id: int | None = None,
        league: int | None = None,
        season: int | None = None,
        date: str | None = None,
        bookmaker: int | None = None,
        bet: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "fixture": fixture_id,
            "league": league,
            "season": season if season is not None else self.default_season,
            "date": date,
            "bookmaker": bookmaker,
            "bet": bet,
        }
        return self._get("/odds", params)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError("API_FOOTBALL_API_KEY is not configured")

        filtered_params = {key: value for key, value in params.items() if value is not None}
        headers = {"x-apisports-key": self.api_key}
        with httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = client.get(path, params=filtered_params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("API-FOOTBALL response must be a JSON object")
        return payload
