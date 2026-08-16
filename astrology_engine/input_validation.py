"""Shared validation for public astrological calculation inputs."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any


def validate_coordinates(lat: Any, lon: Any) -> tuple[float, float]:
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("纬度和经度必须是有限数字") from exc
    if not math.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
        raise ValueError(f"纬度必须在-90到90之间，收到: {lat!r}")
    if not math.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
        raise ValueError(f"经度必须在-180到180之间，收到: {lon!r}")
    return latitude, longitude


def validate_timezone(value: Any) -> float:
    try:
        timezone = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("时区偏移必须是有限数字") from exc
    # Fixed offsets outside the civil timezone range are almost always an
    # input error. IANA timezone_name remains available for historical/DST
    # transitions and is validated by zoneinfo separately.
    if not math.isfinite(timezone) or not -14.0 <= timezone <= 14.0:
        raise ValueError(f"时区偏移必须在-14到14之间，收到: {value!r}")
    return timezone


def parse_local_datetime(value: datetime | str, label: str = "时间") -> datetime:
    """Parse a naive local wall-clock value used with an explicit timezone.

    The public chart contract carries timezone/tz separately. Silently
    stripping an embedded ``+08:00`` or ``Z`` offset would change the instant,
    so aware values fail closed instead of being misread as local time.
    """
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{label}必须是ISO日期时间") from exc
    if parsed.tzinfo is not None:
        raise ValueError(f"{label}必须使用不带时区的当地时间；时区请通过tz或timezone_name传入")
    return parsed.replace(tzinfo=None)


def normalize_house_system(value: Any) -> str:
    requested = str(value or "P").strip().upper()
    allowed = {"P", "E", "W", "K", "R", "C"}
    if requested not in allowed:
        raise ValueError(f"unsupported house system {value!r}; choose from {sorted(allowed)}")
    return requested


HOUSE_SYSTEM_NAMES = {
    "P": "Placidus",
    "E": "Equal",
    "W": "Whole Sign",
    "K": "Koch",
    "R": "Regiomontanus",
    "C": "Campanus",
}


def house_system_name(value: Any) -> str:
    """Return the stable display name for a normalized house-system code."""
    return HOUSE_SYSTEM_NAMES[normalize_house_system(value)]


__all__ = [
    "HOUSE_SYSTEM_NAMES",
    "house_system_name",
    "normalize_house_system",
    "parse_local_datetime",
    "validate_coordinates",
    "validate_timezone",
]
