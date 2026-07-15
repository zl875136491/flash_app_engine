"""应用时区：库内以 UTC 存储，对外 API 统一转为 Asia/Shanghai。"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Asia/Shanghai")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware_utc(value: datetime) -> datetime:
    """Mongo/Beanie 读出的 naive datetime 视为 UTC。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_app_timezone(value: datetime) -> datetime:
    return ensure_aware_utc(value).astimezone(APP_TZ)


def format_app_iso(value: datetime) -> str:
    """序列化为带 +08:00 的 ISO 字符串。"""
    return to_app_timezone(value).isoformat()
