"""Exhaustive predictive-aspect scanning for the project timing layer.

This module deliberately keeps the raw predictive engine unchanged.  It adds
the missing audit layer: every returned moving body (including auxiliary
outer planets) is compared with every natal body and angle, then filtered by
the project's applying/separating policy ("入三出一").
"""
from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Any, Iterable

from .natal import calculate_natal
from .predictive import calculate_predictive
from .input_validation import parse_local_datetime


MAJOR_ASPECTS: dict[str, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

CORE_BODIES = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
AUXILIARY_BODIES = {
    "Uranus", "Neptune", "Pluto", "North Node", "South Node", "Chiron", "Juno"
}
ALGORITHM_PROFILES = {
    "transit": "project_local_ephh_transit_v1",
    "transits": "project_local_ephh_transit_v1",
    "secondary": "project_local_ephh_secondary_v1",
    "tertiary": "project_local_ephh_tertiary_v3_sidereal",
    "tertiary_progression": "project_local_ephh_tertiary_v3_sidereal",
    "tertiary_v3": "project_local_ephh_tertiary_v3_sidereal",
    "tertiary_sidereal": "project_local_ephh_tertiary_v3_sidereal",
    "tertiary_lunar": "project_local_ephh_tertiary_v3_sidereal",
    "tertiary_v2": "project_local_ephh_tertiary_v2_synodic_anchor1",
    "tertiary_synodic": "project_local_ephh_tertiary_v2_synodic_anchor1",
    "tertiary_v1": "project_local_ephh_tertiary_v1",
    "tertiary_calendar": "project_local_ephh_tertiary_v1",
    "solar_arc": "project_local_ephh_solar_arc_v1",
}
MOON_HARD_ASPECTS = {"conjunction", "square", "opposition"}


def _distance(longitude_a: float, longitude_b: float, aspect: float) -> float:
    separation = abs((float(longitude_a) - float(longitude_b)) % 360.0)
    separation = min(separation, 360.0 - separation)
    return abs(separation - aspect)


def _direction(current_orb: float, next_orb: float, exact_epsilon: float = 0.05) -> str:
    if current_orb <= exact_epsilon:
        return "exact"
    if next_orb < current_orb:
        return "applying"
    if next_orb > current_orb:
        return "separating"
    return "unknown"


def _body_layer(name: str) -> str:
    if name in CORE_BODIES:
        return "classical_core"
    if name in AUXILIARY_BODIES:
        return "auxiliary_context"
    return "technical_point"


def _boundary(value: datetime | str) -> datetime:
    # Keep the same local-wall-clock contract as natal/predictive.  Silently
    # stripping an embedded offset would shift a scan window by hours.
    return parse_local_datetime(value, "时限扫描时间")


def _nonnegative_finite(value: float, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}必须是有限的非负数") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label}必须是有限的非负数")
    return number


def _points(chart: dict[str, Any], *, include_fortune: bool = False) -> dict[str, float]:
    points: dict[str, float] = {}
    for name, row in chart.get("placements", {}).items():
        if not include_fortune and name == "Fortune":
            continue
        longitude = row.get("ecliptic_longitude")
        if isinstance(longitude, (int, float)):
            points[name] = float(longitude)
    houses = chart.get("houses", {})
    for name, key in (("Ascendant", "asc"), ("Midheaven", "mc")):
        longitude = houses.get(key)
        if isinstance(longitude, (int, float)):
            points[name] = float(longitude)
    return points


def scan_progressive_window(
    technique: str,
    birth_datetime: datetime | str,
    *,
    start_datetime: datetime | str,
    end_datetime: datetime | str,
    lat: float | None = None,
    lon: float | None = None,
    tz: float = 8.0,
    timezone_name: str | None = None,
    house_system: str = "P",
    step_days: float = 1.0,
    step_hours: float | None = None,
    applying_orb: float = 3.0,
    separating_orb: float = 1.0,
    include_fortune: bool = False,
    place: str | None = None,
) -> list[dict[str, Any]]:
    """Return all qualifying moving-to-natal aspect rows in a time window.

    ``applying_orb=3`` and ``separating_orb=1`` implement the agreed
    "入三出一" rule.  The scan never drops Uranus/Neptune/Pluto; they are
    returned as auxiliary context and cannot independently upgrade a judgment.
    """
    start_datetime = _boundary(start_datetime)
    end_datetime = _boundary(end_datetime)
    if (lat is None) != (lon is None) or (lat is None and not place):
        raise ValueError("provide both lat/lon or place")
    if end_datetime < start_datetime:
        raise ValueError("end_datetime must be on or after start_datetime")
    normalized_technique = str(technique).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_technique not in ALGORITHM_PROFILES:
        raise ValueError(
            f"unsupported timing profile {technique!r}; choose from {sorted(ALGORITHM_PROFILES)}"
        )
    algorithm_profile = ALGORITHM_PROFILES[normalized_technique]
    applying_orb = _nonnegative_finite(applying_orb, "applying_orb")
    separating_orb = _nonnegative_finite(separating_orb, "separating_orb")
    natal = calculate_natal(
        birth_datetime, lat=lat, lon=lon, place=place, tz=tz, timezone_name=timezone_name, house_system=house_system
    )
    lat, lon = natal["lat"], natal["lon"]
    natal_points = _points(natal, include_fortune=include_fortune)
    dates: list[datetime] = []
    cursor = start_datetime
    if step_hours is not None:
        step_hours = _nonnegative_finite(step_hours, "step_hours")
        if step_hours == 0:
            raise ValueError("step_hours must be positive")
    if step_hours is not None:
        step = timedelta(hours=step_hours)
    else:
        step_days = _nonnegative_finite(step_days, "step_days")
        if step_days == 0:
            raise ValueError("step_days must be positive")
        step = timedelta(days=step_days)
    while cursor <= end_datetime:
        dates.append(cursor)
        cursor += step
    if not dates or dates[-1] < end_datetime:
        dates.append(end_datetime)

    snapshots: list[dict[str, Any]] = []
    for moment in dates:
        package = calculate_predictive(
            technique,
            birth_datetime,
            target_datetime=moment,
            lat=lat,
            lon=lon,
            tz=tz,
            timezone_name=timezone_name,
            house_system=house_system,
        )
        result = package["result"]
        moving = _points(
            {"placements": result.get("planets", {}), "houses": result.get("houses", {})},
            include_fortune=include_fortune,
        )
        snapshots.append({"datetime": moment, "moving": moving, "raw": result})

    rows: list[dict[str, Any]] = []
    for index, snapshot in enumerate(snapshots):
        next_snapshot = snapshots[min(index + 1, len(snapshots) - 1)]
        for moving_name, moving_longitude in snapshot["moving"].items():
            for natal_name, natal_longitude in natal_points.items():
                if moving_name == natal_name:
                    continue
                for aspect_name, aspect_angle in MAJOR_ASPECTS.items():
                    orb = _distance(moving_longitude, natal_longitude, aspect_angle)
                    next_longitude = next_snapshot["moving"].get(moving_name, moving_longitude)
                    next_orb = _distance(next_longitude, natal_longitude, aspect_angle)
                    direction = _direction(orb, next_orb)
                    limit = applying_orb if direction in {"applying", "exact"} else separating_orb
                    if orb <= limit:
                        rows.append({
                            "datetime": snapshot["datetime"].isoformat(),
                            "chart_id": natal["chart_id"],
                            "location_source": natal.get("location_source"),
                            "location_precision_warning": natal.get("location_precision_warning"),
                            "technique": normalized_technique,
                            "calculation_profile": algorithm_profile,
                            "moving_body": moving_name,
                            "natal_point": natal_name,
                            "aspect": aspect_name,
                            "orb": round(orb, 4),
                            "direction": direction,
                            "moving_layer": _body_layer(moving_name),
                            "natal_layer": _body_layer(natal_name),
                            "priority": (
                                0
                                if moving_name == "Moon" and aspect_name in MOON_HARD_ASPECTS
                                else 1
                                if moving_name == "Moon"
                                else 2
                            ),
                        })
    return sorted(rows, key=lambda row: (row["priority"], row["datetime"], row["orb"]))


def refine_aspect_contacts(
    technique: str,
    birth_datetime: datetime | str,
    *,
    start_datetime: datetime | str,
    end_datetime: datetime | str,
    lat: float | None = None,
    lon: float | None = None,
    tz: float = 8.0,
    timezone_name: str | None = None,
    house_system: str = "P",
    step_hours: float = 24.0,
    max_contacts: int | None = None,
    place: str | None = None,
) -> list[dict[str, Any]]:
    """Refine each scanned contact to the nearest local aspect minimum.

    The coarse scan remains the exhaustive discovery layer.  This function
    adds a bounded golden-section refinement around each discovered minimum,
    returning an approximate exact time and a fresh orb.  It is intentionally
    separate from the raw engine so a timing claim always carries its scan
    step and profile.
    """
    if max_contacts is not None and (not isinstance(max_contacts, int) or max_contacts < 0):
        raise ValueError("max_contacts must be a non-negative integer or None")
    step_hours = _nonnegative_finite(step_hours, "step_hours")
    if step_hours == 0:
        raise ValueError("step_hours must be positive")
    coarse = scan_progressive_window(
        technique,
        birth_datetime,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        lat=lat,
        lon=lon,
        place=place,
        tz=tz,
        timezone_name=timezone_name,
        house_system=house_system,
        step_hours=step_hours,
    )
    if not coarse:
        return []
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in coarse:
        key = (row["moving_body"], row["natal_point"], row["aspect"])
        if key not in grouped or row["orb"] < grouped[key]["orb"]:
            grouped[key] = row

    natal = calculate_natal(birth_datetime, lat=lat, lon=lon, place=place, tz=tz, timezone_name=timezone_name, house_system=house_system)
    lat, lon = natal["lat"], natal["lon"]
    natal_points = _points(natal)
    angle_by_name = {name: angle for name, angle in MAJOR_ASPECTS.items()}
    span = timedelta(hours=max(0.25, float(step_hours)))
    refined: list[dict[str, Any]] = []

    def moving_longitude(moment: datetime, body: str) -> float | None:
        package = calculate_predictive(
            technique,
            birth_datetime,
            target_datetime=moment,
            lat=lat,
            lon=lon,
            tz=tz,
            timezone_name=timezone_name,
            house_system=house_system,
        )
        result = package["result"]
        moving = _points({"placements": result.get("planets", {}), "houses": result.get("houses", {})})
        return moving.get(body)

    def orb_at(moment: datetime, body: str, natal_point: str, aspect: str) -> float:
        moving = moving_longitude(moment, body)
        if moving is None or natal_point not in natal_points:
            return 999.0
        return _distance(moving, natal_points[natal_point], angle_by_name[aspect])

    for key, row in grouped.items():
        body, natal_point, aspect = key
        center = datetime.fromisoformat(row["datetime"])
        left = max(start_datetime, center - span)
        right = min(end_datetime, center + span)
        # Golden-section search for the local minimum of angular distance.
        phi = (1 + 5 ** 0.5) / 2
        for _ in range(18):
            x1 = right - (right - left) / phi
            x2 = left + (right - left) / phi
            if orb_at(x1, body, natal_point, aspect) <= orb_at(x2, body, natal_point, aspect):
                right = x2
            else:
                left = x1
        exact = left + (right - left) / 2
        before = max(start_datetime, exact - timedelta(hours=0.5))
        after = min(end_datetime, exact + timedelta(hours=0.5))
        exact_orb = orb_at(exact, body, natal_point, aspect)
        before_orb = orb_at(before, body, natal_point, aspect)
        after_orb = orb_at(after, body, natal_point, aspect)
        direction = "applying" if before_orb > after_orb else "separating" if before_orb < after_orb else "stationary"
        refined.append({
            **row,
            "datetime": exact.isoformat(),
            "exact_datetime": exact.isoformat(),
            "orb": round(exact_orb, 6),
            "direction": direction,
            "scan_step_hours": float(step_hours),
            "refinement": "golden_section_local_minimum",
        })
    refined.sort(key=lambda row: (row["priority"], row["datetime"], row["orb"]))
    return refined if max_contacts is None else refined[:max_contacts]


scan_timing_window = scan_progressive_window

__all__ = ["MAJOR_ASPECTS", "scan_progressive_window", "scan_timing_window", "refine_aspect_contacts"]
