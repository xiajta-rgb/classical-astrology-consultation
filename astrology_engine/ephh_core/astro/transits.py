"""Transit chart and natal-contact calculations.

Transit positions are a separate timing layer: the natal chart remains the
significator source, while the moving chart only supplies activation and
window information.  The result keeps both snapshots and never collapses a
transit into a natal judgement.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .house import calculate_house_cusps
from .utils import calc_aspects, calc_natal_chart, calc_planet_positions, datetime_to_jd


def _distance(lon_a: float, lon_b: float, angle: float) -> float:
    separation = abs((float(lon_a) - float(lon_b)) % 360.0)
    separation = min(separation, 360.0 - separation)
    return abs(separation - float(angle))


def calculate_transit(
    birth_dt: datetime,
    birth_lat: float,
    birth_lon: float,
    target_dt: datetime,
    tz: float = 8.0,
    house_system: str = "P",
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
) -> dict[str, Any]:
    natal = calc_natal_chart(birth_dt, birth_lat, birth_lon, tz, house_system)
    transit_lat = birth_lat if target_lat is None else float(target_lat)
    transit_lon = birth_lon if target_lon is None else float(target_lon)
    target_jd = datetime_to_jd(target_dt, tz)
    target_houses = calculate_house_cusps(target_jd, transit_lat, transit_lon, house_system)
    transit_planets = calc_planet_positions(target_jd, target_houses["house_cusps"])

    natal_points = {
        name: data["ecliptic_longitude"]
        for name, data in natal["planets"].items()
        if isinstance(data.get("ecliptic_longitude"), (int, float))
    }
    natal_points.update({
        "Ascendant": natal["houses"]["asc"],
        "Midheaven": natal["houses"]["mc"],
    })
    transit_points = {
        name: data["ecliptic_longitude"]
        for name, data in transit_planets.items()
        if isinstance(data.get("ecliptic_longitude"), (int, float))
    }
    transit_points.update({
        "Ascendant": target_houses["asc"],
        "Midheaven": target_houses["mc"],
    })

    contacts: list[dict[str, Any]] = []
    major_angles = {
        "conjunction": 0.0,
        "sextile": 60.0,
        "square": 90.0,
        "trine": 120.0,
        "opposition": 180.0,
    }
    for moving_name, moving_lon in transit_points.items():
        if moving_name in {"Ascendant", "Midheaven"}:
            continue
        for natal_name, natal_lon in natal_points.items():
            for aspect_name, angle in major_angles.items():
                orb = _distance(moving_lon, natal_lon, angle)
                if orb <= 3.0:
                    contacts.append({
                        "moving_body": moving_name,
                        "natal_point": natal_name,
                        "aspect": aspect_name,
                        "angle": angle,
                        "orb": round(orb, 4),
                        "moving_layer": "classical_core" if moving_name in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"} else "auxiliary_context",
                        "natal_layer": "classical_core" if natal_name in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"} else "auxiliary_context",
                    })

    transit_lons = dict(transit_points)
    aspects = calc_aspects(
        transit_lons,
        speeds={name: data.get("speed") for name, data in transit_planets.items()},
    )
    return {
        "progression_type": "transit",
        "calculation_profile": "project_local_ephh_transit_v1",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "target_location": {
            "latitude": round(transit_lat, 6),
            "longitude": round(transit_lon, 6),
            "used_birth_location": target_lat is None and target_lon is None,
        },
        "planets": transit_planets,
        "houses": {
            "house_cusps": target_houses["house_cusps"],
            "asc": target_houses["asc"],
            "mc": target_houses["mc"],
            "des": target_houses["des"],
            "ic": target_houses["ic"],
            "house_system": target_houses["house_system"],
        },
        "aspects": aspects,
        "natal_contacts": sorted(contacts, key=lambda row: row["orb"]),
        "natal_snapshot": {
            "planets": natal["planets"],
            "houses": natal["houses"],
        },
    }


__all__ = ["calculate_transit"]
