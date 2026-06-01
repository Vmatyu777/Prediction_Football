from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from src.api.config import (
    API_FOOTBALL_API_KEY,
    API_FOOTBALL_FIXTURES_DAYS_AHEAD,
    API_FOOTBALL_FIXTURES_SYNC_TIME,
    API_FOOTBALL_MAX_SYNC_FIXTURES,
    API_FOOTBALL_ODDS_DAYS_AHEAD,
    API_FOOTBALL_ODDS_SYNC_TIME,
    API_FOOTBALL_RESULTS_LOOKBACK_DAYS,
    API_FOOTBALL_RESULTS_SYNC_TIME,
    API_FOOTBALL_SCHEDULER_ENABLED,
    API_FOOTBALL_SCHEDULER_TIMEZONE,
    API_FOOTBALL_SEASON,
)
from src.api.database.models import ExternalSource, Match, MatchStatus
from src.api.database.session import SessionLocal
from src.api.services.api_football_client import ApiFootballClient
from src.api.services.external_match_sync_service import (
    API_FOOTBALL_SOURCE,
    API_FOOTBALL_TOP_LEAGUES,
    fetch_fixture_payloads,
    sync_api_football_fixtures,
)
from src.api.services.external_odds_sync_service import sync_api_football_odds
from src.api.services.external_result_sync_service import sync_api_football_results


logger = logging.getLogger(__name__)

FIXTURES_JOB_ID = "api_football_fixtures_sync"
ODDS_JOB_ID = "api_football_odds_sync"
RESULTS_JOB_ID = "api_football_results_sync"

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    """Start daily API-FOOTBALL sync jobs inside the FastAPI process."""
    global _scheduler
    if not API_FOOTBALL_SCHEDULER_ENABLED:
        logger.info("API-FOOTBALL scheduler is disabled")
        return
    if _scheduler is not None and _scheduler.running:
        return

    scheduler = BackgroundScheduler(
        timezone=resolve_timezone(),
        job_defaults={"coalesce": True, "max_instances": 1},
    )
    add_daily_job(
        scheduler,
        job_id=FIXTURES_JOB_ID,
        job_name="API-FOOTBALL fixtures sync",
        time_value=API_FOOTBALL_FIXTURES_SYNC_TIME,
        func=run_fixtures_sync_job,
    )
    add_daily_job(
        scheduler,
        job_id=ODDS_JOB_ID,
        job_name="API-FOOTBALL odds sync",
        time_value=API_FOOTBALL_ODDS_SYNC_TIME,
        func=run_odds_sync_job,
    )
    add_daily_job(
        scheduler,
        job_id=RESULTS_JOB_ID,
        job_name="API-FOOTBALL results sync",
        time_value=API_FOOTBALL_RESULTS_SYNC_TIME,
        func=run_results_sync_job,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("API-FOOTBALL scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("API-FOOTBALL scheduler stopped")
    _scheduler = None


def get_scheduler_health() -> dict[str, Any]:
    return {
        "scheduler_enabled": API_FOOTBALL_SCHEDULER_ENABLED,
        "scheduler_running": _scheduler.running if _scheduler is not None else False,
        "timezone": API_FOOTBALL_SCHEDULER_TIMEZONE,
        "next_run_fixtures": get_next_run_time(FIXTURES_JOB_ID),
        "next_run_odds": get_next_run_time(ODDS_JOB_ID),
        "next_run_results": get_next_run_time(RESULTS_JOB_ID),
    }


def run_fixtures_sync_job() -> dict[str, Any]:
    return run_with_logging("fixtures", run_fixtures_sync_once)


def run_odds_sync_job() -> dict[str, Any]:
    return run_with_logging("odds", run_odds_sync_once)


def run_results_sync_job() -> dict[str, Any]:
    return run_with_logging("results", run_results_sync_once)


def run_fixtures_sync_once(*, dry_run: bool = False) -> dict[str, Any]:
    if not API_FOOTBALL_API_KEY:
        return skipped_summary("API_FOOTBALL_API_KEY is not configured")

    client = ApiFootballClient()
    league_ids = [int(item["api_id"]) for item in API_FOOTBALL_TOP_LEAGUES.values()]
    from_date, to_date = scheduler_date_window(days_ahead=API_FOOTBALL_FIXTURES_DAYS_AHEAD)
    payloads = fetch_fixture_payloads(
        client,
        league_ids=league_ids,
        season=API_FOOTBALL_SEASON,
        from_date=from_date,
        to_date=to_date,
    )
    with SessionLocal() as db:
        return sync_api_football_fixtures(db, fixture_payloads=payloads, dry_run=dry_run).as_dict()


def run_odds_sync_once(*, dry_run: bool = False) -> dict[str, Any]:
    if not API_FOOTBALL_API_KEY:
        return skipped_summary("API_FOOTBALL_API_KEY is not configured")

    fixture_ids = list_upcoming_api_fixture_ids(
        days_ahead=API_FOOTBALL_ODDS_DAYS_AHEAD,
        limit=API_FOOTBALL_MAX_SYNC_FIXTURES,
    )
    if not fixture_ids:
        return skipped_summary("No upcoming API fixtures found for odds sync")

    client = ApiFootballClient()
    payloads = [client.get_odds(fixture_id=int(fixture_id), season=API_FOOTBALL_SEASON) for fixture_id in fixture_ids]
    with SessionLocal() as db:
        return sync_api_football_odds(db, odds_payloads=payloads, dry_run=dry_run).as_dict()


def run_results_sync_once(*, dry_run: bool = False) -> dict[str, Any]:
    if not API_FOOTBALL_API_KEY:
        return skipped_summary("API_FOOTBALL_API_KEY is not configured")

    fixture_ids = list_recent_api_fixture_ids(
        lookback_days=API_FOOTBALL_RESULTS_LOOKBACK_DAYS,
        limit=API_FOOTBALL_MAX_SYNC_FIXTURES,
    )
    if not fixture_ids:
        return skipped_summary("No recent API fixtures found for results sync")

    client = ApiFootballClient()
    fixture_payloads = [client.get_fixtures(fixture_id=int(fixture_id), season=None) for fixture_id in fixture_ids]
    statistics_payloads = [client.get_fixture_statistics(fixture_id=int(fixture_id)) for fixture_id in fixture_ids]
    with SessionLocal() as db:
        return sync_api_football_results(
            db,
            fixture_payloads=fixture_payloads,
            statistics_payloads=statistics_payloads,
            dry_run=dry_run,
        ).as_dict()


def run_with_logging(task_name: str, func: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    logger.info("API-FOOTBALL %s sync started", task_name)
    try:
        summary = func()
        logger.info("API-FOOTBALL %s sync finished: %s", task_name, summary)
        return summary
    except Exception:
        logger.exception("API-FOOTBALL %s sync failed", task_name)
        return {"errors": [f"{task_name} sync failed; see backend logs"]}


def list_upcoming_api_fixture_ids(*, days_ahead: int, limit: int) -> list[str]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end = now + timedelta(days=days_ahead)
    with SessionLocal() as db:
        return list_api_fixture_ids(
            db,
            status_names=["scheduled", "postponed"],
            from_datetime=now,
            to_datetime=end,
            limit=limit,
        )


def list_recent_api_fixture_ids(*, lookback_days: int, limit: int) -> list[str]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = now - timedelta(days=lookback_days)
    with SessionLocal() as db:
        return list_api_fixture_ids(
            db,
            status_names=["scheduled", "postponed", "cancelled", "finished"],
            from_datetime=start,
            to_datetime=now,
            limit=limit,
        )


def list_api_fixture_ids(
    db: Session,
    *,
    status_names: list[str],
    from_datetime: datetime,
    to_datetime: datetime,
    limit: int,
) -> list[str]:
    rows = (
        db.query(Match.external_match_id)
        .join(ExternalSource, Match.external_source_id == ExternalSource.id)
        .join(MatchStatus, Match.status_id == MatchStatus.id)
        .filter(
            ExternalSource.name == API_FOOTBALL_SOURCE,
            Match.external_match_id.isnot(None),
            MatchStatus.name.in_(status_names),
            Match.match_date >= from_datetime,
            Match.match_date <= to_datetime,
        )
        .order_by(Match.match_date.asc())
        .limit(limit)
        .all()
    )
    return [str(row[0]) for row in rows if row[0] is not None]


def scheduler_date_window(*, days_ahead: int) -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=days_ahead)
    return today.isoformat(), end_date.isoformat()


def add_daily_job(
    scheduler: BackgroundScheduler,
    *,
    job_id: str,
    job_name: str,
    time_value: str,
    func: Callable[[], dict[str, Any]],
) -> None:
    hour, minute = parse_schedule_time(time_value)
    scheduler.add_job(
        func,
        CronTrigger(hour=hour, minute=minute),
        id=job_id,
        name=job_name,
        replace_existing=True,
    )


def parse_schedule_time(value: str) -> tuple[int, int]:
    try:
        hour_value, minute_value = value.split(":", maxsplit=1)
        hour = int(hour_value)
        minute = int(minute_value)
    except ValueError as error:
        raise ValueError(f"Invalid scheduler time: {value}") from error
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid scheduler time: {value}")
    return hour, minute


def resolve_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(API_FOOTBALL_SCHEDULER_TIMEZONE)
    except ZoneInfoNotFoundError:
        logger.warning("Unknown scheduler timezone %s, using UTC", API_FOOTBALL_SCHEDULER_TIMEZONE)
        return ZoneInfo("UTC")


def get_next_run_time(job_id: str) -> str | None:
    if _scheduler is None:
        return None
    job = _scheduler.get_job(job_id)
    if job is None or job.next_run_time is None:
        return None
    return job.next_run_time.isoformat()


def skipped_summary(reason: str) -> dict[str, Any]:
    return {"skipped": True, "reason": reason}
