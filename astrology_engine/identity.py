"""Stable identifiers shared by natal and predictive calculation envelopes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime


def chart_id(
    birth_datetime: datetime,
    *,
    lat: float,
    lon: float,
    tz: float,
    timezone_name: str | None,
    house_system: str,
) -> str:
    """Build an identity that changes when any chart-defining input changes."""
    payload = {
        "identity_version": "CHART-ID-1.0",
        "birth_datetime": birth_datetime.isoformat(timespec="seconds"),
        "lat": round(float(lat), 6),
        "lon": round(float(lon), 6),
        "tz": round(float(tz), 6),
        "timezone_name": timezone_name or None,
        "zodiac": "tropical",
        "house_system": str(house_system).upper(),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]
    return f"local-{birth_datetime:%Y%m%d-%H%M%S}-{str(house_system).upper()}-{digest}"


__all__ = ["chart_id"]
