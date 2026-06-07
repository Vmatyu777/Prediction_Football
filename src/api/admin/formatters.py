from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


MOSCOW_TIMEZONE = ZoneInfo("Europe/Moscow")


def format_moscow_datetime(value: datetime | None) -> str:
    if value is None:
        return ""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(MOSCOW_TIMEZONE).strftime("%d.%m.%Y %H:%M МСК")


def format_admin_date(value: date | None) -> str:
    if value is None:
        return ""

    return value.strftime("%d.%m.%Y")


def format_admin_datetime_property(obj: Any, prop: str) -> str:
    return format_moscow_datetime(getattr(obj, prop, None))


def format_admin_date_property(obj: Any, prop: str) -> str:
    return format_admin_date(getattr(obj, prop, None))
