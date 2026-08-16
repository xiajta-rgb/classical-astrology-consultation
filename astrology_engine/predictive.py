"""Stable project-facing API for the vendored ephh predictive algorithms.

The copied modules calculate positions with Swiss Ephemeris and do not start
the ephh web server. Inputs are deliberately explicit: local birth/target
datetimes, timezone offset, and coordinates. A place name may be retained as
metadata, but coordinates must be supplied by the caller or a separate
geocoder before calculation.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import swisseph as swe

from .ephh_core import (
    calculate_essential_dignities,
    calculate_firdaria,
    calculate_lunar_return,
    calculate_mutual_reception,
    calculate_profection,
    calculate_secondary_progression,
    calculate_solar_arc_progression,
    calculate_solar_return,
    calculate_tertiary_progression,
    calculate_tertiary_progression_v1,
    calculate_tertiary_progression_v2,
    calculate_tertiary_progression_v3,
    calculate_transit,
)
from .location import resolve_place
from .identity import chart_id
from .input_validation import house_system_name, normalize_house_system, parse_local_datetime, validate_coordinates, validate_timezone


EPHEMERIS_PATH = Path(__file__).resolve().parent / "ephh_core" / "ephe"


def configure_ephemeris() -> str:
    """Point pyswisseph at the project-local data files and return the path."""
    if not EPHEMERIS_PATH.exists():
        raise FileNotFoundError(f"project ephemeris directory missing: {EPHEMERIS_PATH}")
    swe.set_ephe_path(str(EPHEMERIS_PATH))
    return str(EPHEMERIS_PATH)


TECHNIQUES: dict[str, str] = {
    "secondary": "calculate_secondary_progression",
    "secondary_progression": "calculate_secondary_progression",
    "tertiary": "calculate_tertiary_progression",
    "tertiary_progression": "calculate_tertiary_progression",
    "tertiary_v2": "calculate_tertiary_progression_v2",
    "tertiary_synodic": "calculate_tertiary_progression_v2",
    "tertiary_v3": "calculate_tertiary_progression_v3",
    "tertiary_sidereal": "calculate_tertiary_progression_v3",
    "tertiary_lunar": "calculate_tertiary_progression_v3",
    "tertiary_v1": "calculate_tertiary_progression_v1",
    "tertiary_calendar": "calculate_tertiary_progression_v1",
    "solar_arc": "calculate_solar_arc_progression",
    "solar_arc_progression": "calculate_solar_arc_progression",
    "solar_return": "calculate_solar_return",
    "lunar_return": "calculate_lunar_return",
    "firdaria": "calculate_firdaria",
    "profection": "calculate_profection",
    "annual_profection": "calculate_profection",
    "essential_dignities": "calculate_essential_dignities",
    "mutual_reception": "calculate_mutual_reception",
    "transit": "calculate_transit",
    "transits": "calculate_transit",
}
SIGNS = ("白羊", "金牛", "双子", "巨蟹", "狮子", "处女", "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼")


def _parse_datetime(value: datetime | str) -> datetime:
    return parse_local_datetime(value, "出生或目标时间")


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


def _coordinates(lat: float | None, lon: float | None, place: str | None) -> tuple[float, float, dict[str, Any]]:
    if lat is None and lon is None:
        if not place:
            raise ValueError("lat/lon or place is required")
        location = resolve_place(place)
        resolved_lat, resolved_lon = validate_coordinates(location["lat"], location["lon"])
        return resolved_lat, resolved_lon, location
    if lat is None or lon is None:
        raise ValueError("lat and lon must be supplied together")
    resolved_lat, resolved_lon = validate_coordinates(lat, lon)
    return resolved_lat, resolved_lon, {"source": "user_declared_coordinates", "precision_warning": None}


def _clean_zodiac(value: dict[str, Any] | None, longitude: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not isinstance(longitude, (int, float)):
        return value
    lon = float(longitude) % 360.0
    cleaned = dict(value)
    cleaned["index"] = int(lon // 30.0)
    cleaned["name"] = SIGNS[cleaned["index"]]
    cleaned["degree"] = round(lon % 30.0, 4)
    return cleaned


def _normalize_result(value: Any) -> Any:
    if isinstance(value, dict):
        result = {key: _normalize_result(item) for key, item in value.items()}
        if "ecliptic_longitude" in result and "zodiac" in result:
            result["zodiac"] = _clean_zodiac(result.get("zodiac"), result.get("ecliptic_longitude"))
        return result
    if isinstance(value, list):
        return [_normalize_result(item) for item in value]
    return value


def calculate_predictive(
    technique: str,
    birth_datetime: datetime | str,
    *,
    target_datetime: datetime | str | None = None,
    target_year: int | None = None,
    target_lat: float | None = None,
    target_lon: float | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tz: float = 8.0,
    timezone_name: str | None = None,
    house_system: str = "P",
    use_birth_location: bool = True,
    use_modern_rulers: bool = False,
    place: str | None = None,
) -> dict[str, Any]:
    """Run one vendored natal/predictive technique with a common envelope."""
    key = str(technique).strip().lower().replace("-", "_").replace(" ", "_")
    function_name = TECHNIQUES.get(key)
    if function_name is None:
        raise ValueError(f"unknown technique {technique!r}; choose from {sorted(TECHNIQUES)}")
    birth = _parse_datetime(birth_datetime)
    house_system = normalize_house_system(house_system)
    birth_tz = _effective_timezone(birth, tz, timezone_name)
    target_original = _parse_datetime(target_datetime) if target_datetime is not None else None
    target_tz = _effective_timezone(target_original, tz, timezone_name) if target_original is not None else birth_tz
    target_for_core = (
        target_original + timedelta(hours=birth_tz - target_tz)
        if target_original is not None and timezone_name
        else target_original
    )
    latitude, longitude, location = _coordinates(lat, lon, place)
    ephemeris_path = configure_ephemeris()
    fn: Callable[..., dict[str, Any]] = globals()[function_name]
    kwargs: dict[str, Any] = {
        "birth_dt": birth,
        "birth_lat": latitude,
        "birth_lon": longitude,
        "lat": latitude,
        "lon": longitude,
        "tz": float(birth_tz),
        "house_system": house_system,
    }
    # The source modules use different parameter names for natal-only methods.
    for key_to_remove in ("birth_lat", "birth_lon", "lat", "lon"):
        if function_name in {"calculate_essential_dignities", "calculate_firdaria", "calculate_profection", "calculate_mutual_reception"}:
            kwargs.pop("birth_lat", None)
            kwargs.pop("birth_lon", None)
        else:
            kwargs.pop("lat", None)
            kwargs.pop("lon", None)
    if function_name in {
        "calculate_secondary_progression",
        "calculate_tertiary_progression",
        "calculate_tertiary_progression_v1",
        "calculate_tertiary_progression_v2",
        "calculate_tertiary_progression_v3",
        "calculate_solar_arc_progression",
        "calculate_lunar_return",
        "calculate_transit",
    }:
        if target_datetime is None:
            raise ValueError(f"{key} requires target_datetime")
        kwargs["target_dt"] = target_for_core
        if function_name == "calculate_transit":
            if target_lat is not None or target_lon is not None:
                if target_lat is None or target_lon is None:
                    raise ValueError("target_lat and target_lon must be supplied together")
                kwargs["target_lat"], kwargs["target_lon"] = validate_coordinates(target_lat, target_lon)
    elif function_name == "calculate_solar_return":
        if target_year is None:
            raise ValueError("solar_return requires target_year")
        kwargs["target_year"] = int(target_year)
        kwargs["use_birth_location"] = bool(use_birth_location)
        if not use_birth_location:
            if target_lat is None or target_lon is None:
                raise ValueError("target_lat and target_lon are required for a relocated solar return")
            kwargs["return_lat"], kwargs["return_lon"] = validate_coordinates(target_lat, target_lon)
    elif function_name in {"calculate_firdaria", "calculate_profection"} and target_datetime is not None:
        kwargs["target_dt"] = target_for_core
    if function_name in {"calculate_essential_dignities", "calculate_mutual_reception"}:
        kwargs["use_modern_rulers"] = bool(use_modern_rulers)
    result = _normalize_result(fn(**kwargs))
    return {
        "engine": "project_local_ephh_predictive",
        "technique": key,
        "source_algorithm": function_name,
        "birth_datetime": birth.isoformat(),
        "birth_place": place,
        "chart_id": chart_id(
            birth,
            lat=latitude,
            lon=longitude,
            tz=float(birth_tz),
            timezone_name=timezone_name,
            house_system=house_system,
        ),
        "target_datetime": target_original.isoformat() if target_original is not None else None,
        "target_year": target_year,
        "place": place,
        "lat": latitude,
        "lon": longitude,
        "location_source": location["source"],
        "location_precision_warning": location.get("precision_warning"),
        "tz": float(birth_tz),
        "target_tz": float(target_tz) if target_original is not None else None,
        "timezone_name": timezone_name,
        "timezone_source": "iana_timezone" if timezone_name else "user_declared_fixed_offset",
        "house_system": house_system_name(house_system),
        "ephemeris_path": ephemeris_path,
        "result": result,
    }


def calculate_bundle(
    birth_datetime: datetime | str,
    techniques: list[str] | tuple[str, ...],
    **kwargs: Any,
) -> dict[str, Any]:
    """Run several techniques with identical natal input and preserve errors."""
    outputs: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for technique in techniques:
        try:
            outputs[technique] = calculate_predictive(technique, birth_datetime, **kwargs)
        except (TypeError, ValueError, FileNotFoundError) as exc:
            errors[str(technique)] = f"{type(exc).__name__}: {exc}"
    return {
        "engine": "project_local_ephh_predictive",
        "birth_datetime": str(birth_datetime),
        "chart_id": next(iter(outputs.values()), {}).get("chart_id"),
        "techniques": outputs,
        "errors": errors,
        "status": "partial" if errors else "ready",
    }


__all__ = ["TECHNIQUES", "calculate_predictive", "calculate_bundle"]
