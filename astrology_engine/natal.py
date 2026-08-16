"""Project-local tropical natal chart calculation."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .predictive import EPHEMERIS_PATH, SIGNS, configure_ephemeris
from .ephh_core.astro.utils import calc_natal_chart
from .location import resolve_place
from .identity import chart_id
from .input_validation import normalize_house_system, parse_local_datetime, validate_coordinates, validate_timezone


def _parse_datetime(value: datetime | str) -> datetime:
    return parse_local_datetime(value, "出生时间")


def _effective_timezone(dt: datetime, tz: float, timezone_name: str | None) -> float:
    fixed_tz = validate_timezone(tz)
    if not timezone_name:
        return fixed_tz
    try:
        aware = dt.replace(tzinfo=ZoneInfo(timezone_name))
    except Exception as exc:
        raise ValueError(f"invalid timezone_name {timezone_name!r}") from exc
    offset = aware.utcoffset()
    if offset is None:
        raise ValueError(f"timezone_name {timezone_name!r} has no UTC offset")
    return offset.total_seconds() / 3600.0


def _clean_chart(chart: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(chart)
    placements = {}
    for name, item in chart.get("planets", {}).items():
        row = dict(item)
        longitude = row.get("ecliptic_longitude")
        if isinstance(longitude, (int, float)):
            lon = float(longitude) % 360.0
            zodiac = dict(row.get("zodiac") or {})
            zodiac.update({"index": int(lon // 30.0), "name": SIGNS[int(lon // 30.0)], "degree": round(lon % 30.0, 4)})
            row["zodiac"] = zodiac
        placements[name] = row
    cleaned["planets"] = placements
    return cleaned


def calculate_natal(
    birth_datetime: datetime | str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: float = 8.0,
    timezone_name: str | None = None,
    house_system: str = "P",
    place: str | None = None,
) -> dict[str, Any]:
    """Calculate a Chart Facts-compatible natal package without external ephh."""
    configure_ephemeris()
    location = {"source": "user_declared_coordinates", "precision_warning": None}
    if lat is None and lon is None:
        if not place:
            raise ValueError("lat/lon or place is required")
        location = resolve_place(place)
        lat, lon = location["lat"], location["lon"]
    elif lat is None or lon is None:
        raise ValueError("lat and lon must be supplied together")
    lat, lon = validate_coordinates(lat, lon)
    house_system = normalize_house_system(house_system)
    birth = _parse_datetime(birth_datetime)
    effective_tz = _effective_timezone(birth, tz, timezone_name)
    chart = _clean_chart(calc_natal_chart(birth, float(lat), float(lon), float(effective_tz), house_system))
    return {
        "engine": "project_local_ephh_natal",
        "chart_id": chart_id(
            birth,
            lat=float(lat),
            lon=float(lon),
            tz=float(effective_tz),
            timezone_name=timezone_name,
            house_system=house_system,
        ),
        "birth_datetime": birth.isoformat(),
        "place": place,
        "birth_place": place,
        "lat": float(lat),
        "lon": float(lon),
        "tz": float(effective_tz),
        "timezone_name": timezone_name,
        "timezone_source": "iana_timezone" if timezone_name else "user_declared_fixed_offset",
        "location_source": location["source"],
        "location_precision_warning": location.get("precision_warning"),
        "zodiac": "tropical",
        "house_system": chart["houses"]["house_system"],
        "placements": chart["planets"],
        "houses": chart["houses"],
        "aspects": chart["aspects"],
        "is_day_chart": chart["is_day_chart"],
        "ephemeris_path": str(EPHEMERIS_PATH),
        "source_policy": "vendored_ephh_algorithm_subset",
        "provenance": {
            "calculator": "astrology_engine.natal.calculate_natal",
            "identity": "astrology_engine.identity.chart_id",
            "location_source": location["source"],
            "timezone_source": "iana_timezone" if timezone_name else "user_declared_fixed_offset",
            "house_system": chart["houses"]["house_system"],
        },
    }


__all__ = ["calculate_natal"]
