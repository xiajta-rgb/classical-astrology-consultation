#!/usr/bin/env python3
"""Versioned classical planetary-state calculation for natal Chart Facts.

This layer deliberately reports evidence fields rather than collapsing them
into a single score. Egyptian terms and Chaldean faces require degrees; when
degrees are absent they remain ``unknown_due_to_missing_degree``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CLASSICAL = ("太阳", "月亮", "水星", "金星", "火星", "木星", "土星")
SIGN_INDEX = {s: i for i, s in enumerate(("白羊", "金牛", "双子", "巨蟹", "狮子", "处女", "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"))}
DOMICILE = {"太阳": ("狮子",), "月亮": ("巨蟹",), "水星": ("双子", "处女"), "金星": ("金牛", "天秤"), "火星": ("白羊", "天蝎"), "木星": ("射手", "双鱼"), "土星": ("摩羯", "水瓶")}
EXALTATION = {"太阳": "白羊", "月亮": "金牛", "火星": "摩羯", "金星": "双鱼", "木星": "巨蟹", "土星": "天秤"}
DETRIMENT = {"太阳": ("水瓶",), "月亮": ("摩羯",), "水星": ("射手", "双鱼"), "金星": ("白羊", "天蝎"), "火星": ("天秤", "金牛"), "木星": ("双子", "处女"), "土星": ("巨蟹", "狮子")}
FALL = {"太阳": "天秤", "月亮": "天蝎", "火星": "巨蟹", "金星": "处女", "木星": "摩羯", "土星": "白羊"}

# Dorotheus-style three-ruler triplicity scheme: day ruler, night ruler,
# participating ruler. This is intentionally versioned instead of merged
# with later two-ruler tables.
TRIPLICITY = {
    "火": {"signs": ("白羊", "狮子", "射手"), "day": "太阳", "night": "木星", "participating": "土星"},
    "土": {"signs": ("金牛", "处女", "摩羯"), "day": "金星", "night": "月亮", "participating": "火星"},
    "风": {"signs": ("双子", "天秤", "水瓶"), "day": "土星", "night": "水星", "participating": "木星"},
    "水": {"signs": ("巨蟹", "天蝎", "双鱼"), "day": "金星", "night": "火星", "participating": "月亮"},
}

# Egyptian bounds/terms, degree intervals are half-open [start, end).
EGYPTIAN_TERMS = {
    "白羊": ((0, 6, "木星"), (6, 12, "金星"), (12, 20, "水星"), (20, 25, "火星"), (25, 30, "土星")),
    "金牛": ((0, 8, "金星"), (8, 14, "水星"), (14, 22, "木星"), (22, 27, "土星"), (27, 30, "火星")),
    "双子": ((0, 6, "水星"), (6, 12, "木星"), (12, 17, "金星"), (17, 24, "火星"), (24, 30, "土星")),
    "巨蟹": ((0, 7, "火星"), (7, 13, "金星"), (13, 19, "水星"), (19, 26, "木星"), (26, 30, "土星")),
    "狮子": ((0, 6, "木星"), (6, 11, "金星"), (11, 18, "土星"), (18, 24, "水星"), (24, 30, "火星")),
    "处女": ((0, 7, "水星"), (7, 17, "金星"), (17, 21, "木星"), (21, 28, "火星"), (28, 30, "土星")),
    "天秤": ((0, 6, "土星"), (6, 14, "水星"), (14, 21, "木星"), (21, 28, "金星"), (28, 30, "火星")),
    "天蝎": ((0, 7, "火星"), (7, 11, "金星"), (11, 19, "水星"), (19, 24, "木星"), (24, 30, "土星")),
    "射手": ((0, 12, "木星"), (12, 17, "金星"), (17, 21, "水星"), (21, 26, "土星"), (26, 30, "火星")),
    "摩羯": ((0, 7, "水星"), (7, 14, "木星"), (14, 22, "金星"), (22, 26, "土星"), (26, 30, "火星")),
    "水瓶": ((0, 7, "水星"), (7, 13, "金星"), (13, 20, "木星"), (20, 25, "火星"), (25, 30, "土星")),
    "双鱼": ((0, 12, "金星"), (12, 16, "木星"), (16, 19, "水星"), (19, 28, "火星"), (28, 30, "土星")),
}

CHALDEAN = ("火星", "太阳", "金星", "水星", "月亮", "土星", "木星")
HOUSE_KIND = {1: "angular", 4: "angular", 7: "angular", 10: "angular", 2: "succedent", 5: "succedent", 8: "succedent", 11: "succedent", 3: "cadent", 6: "cadent", 9: "cadent", 12: "cadent"}
DEFAULT_RULE_VERSIONS = {
    "terms": "egyptian",
    "triplicity": "dorotheus_style_three_rulers",
    "faces": "chaldean",
    "reception": "direction_plus_connection_required",
    "aspect": "application_separation_required",
}
SUPPORTED_RULE_VERSIONS = {
    "terms": {"egyptian"},
    "triplicity": {"dorotheus_style_three_rulers"},
    "faces": {"chaldean"},
    "reception": {"direction_plus_connection_required"},
    "aspect": {"application_separation_required"},
}


def _sect(payload: dict[str, Any]) -> tuple[str, str]:
    if payload.get("sect") in ("day", "night"):
        return payload["sect"], payload.get("sect_source") or "declared"
    sun_house = payload.get("placements", {}).get("太阳", {}).get("house")
    if isinstance(sun_house, int) and sun_house in (1, 2, 3, 4, 5, 6):
        return "night", "inferred_from_sun_below_horizon"
    if isinstance(sun_house, int) and sun_house in (7, 8, 9, 10, 11, 12):
        return "day", "inferred_from_sun_above_horizon"
    return "unknown", "missing_sect_and_sun_position"


def _sect_confidence(source: str) -> str:
    return "high" if source == "declared" else "low" if source.startswith("inferred") else "none"


def _degree(placement: dict[str, Any]) -> float | None:
    if "degree" not in placement:
        return None
    value = float(placement["degree"])
    return value if 0 <= value < 30 else None


def _triplicity(sign: str, version: str) -> dict[str, Any] | None:
    if version != "dorotheus_style_three_rulers":
        return None
    for element, data in TRIPLICITY.items():
        if sign in data["signs"]:
            return {"element": element, **data}
    return None


def _term(sign: str, degree: float | None, version: str) -> dict[str, Any]:
    if version != "egyptian":
        return {"status": "unsupported_version", "version": version}
    if degree is None:
        return {"status": "unknown_due_to_missing_degree", "version": version}
    for start, end, ruler in EGYPTIAN_TERMS[sign]:
        if start <= degree < end:
            return {"status": "term", "ruler": ruler, "version": "egyptian", "interval": [start, end]}
    return {"status": "invalid_degree"}


def _face(sign: str, degree: float | None, version: str) -> dict[str, Any]:
    if version != "chaldean":
        return {"status": "unsupported_version", "version": version}
    if degree is None:
        return {"status": "unknown_due_to_missing_degree", "version": version}
    index = int(degree // 10)
    sign_index = SIGN_INDEX[sign]
    ruler = CHALDEAN[(sign_index * 3 + index) % 7]
    return {"status": "face", "ruler": ruler, "version": "chaldean", "interval": [index * 10, (index + 1) * 10]}


def _motion_visibility(placement: dict[str, Any]) -> dict[str, Any]:
    """Expose only declared motion/visibility facts; never infer either one."""
    speed = placement.get("speed")
    speed_known = isinstance(speed, (int, float)) and not isinstance(speed, bool)
    retrograde = placement.get("is_retrograde")
    if retrograde is None:
        retrograde = placement.get("retrograde")
    retrograde_known = isinstance(retrograde, bool)
    visibility = placement.get("visibility")
    if visibility is None and "visible" in placement:
        visibility = placement.get("visible")
    visibility_known = isinstance(visibility, (bool, str))
    return {
        "speed": float(speed) if speed_known else None,
        "speed_status": "declared" if speed_known else "unknown_due_to_missing_motion",
        "is_retrograde": retrograde if retrograde_known else None,
        "retrograde_status": "declared" if retrograde_known else "unknown_due_to_missing_motion",
        "visibility": visibility if visibility_known else None,
        "visibility_status": "declared" if visibility_known else "unknown_due_to_missing_visibility",
    }


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    sect, sect_source = _sect(payload)
    configured_versions = payload.get("rule_versions", {})
    versions = {key: configured_versions.get(key, default) for key, default in DEFAULT_RULE_VERSIONS.items()}
    version_lock = {key: key in configured_versions and versions[key] in SUPPORTED_RULE_VERSIONS[key] for key in DEFAULT_RULE_VERSIONS}
    planets = []
    for name, placement in payload.get("placements", {}).items():
        sign, house = placement.get("sign"), placement.get("house")
        if name not in CLASSICAL:
            planets.append({"planet": name, "layer": "auxiliary", "sign": sign, "house": house, "motion_visibility": _motion_visibility(placement)})
            continue
        trip = _triplicity(sign, versions["triplicity"])
        essential = []
        if sign in DOMICILE[name]:
            essential.append("domicile")
        if EXALTATION.get(name) == sign:
            essential.append("exaltation")
        if FALL.get(name) == sign:
            essential.append("fall")
        if sign in DETRIMENT.get(name, ()):
            essential.append("detriment")
        if trip and trip["day"] == name and sect == "day":
            essential.append("triplicity_day")
        if trip and trip["night"] == name and sect == "night":
            essential.append("triplicity_night")
        if trip and trip["participating"] == name:
            essential.append("triplicity_participating")
        if sect == "day":
            sect_status = "in_sect" if name in ("太阳", "木星", "土星") else "out_of_sect" if name in ("月亮", "金星", "火星") else "variable"
        elif sect == "night":
            sect_status = "in_sect" if name in ("月亮", "金星", "火星") else "out_of_sect" if name in ("太阳", "木星", "土星") else "variable"
        else:
            sect_status = "unknown"
        planets.append({
            "planet": name, "layer": "classical", "sign": sign, "house": house,
            "essential_dignity": essential,
            "triplicity": {"element": trip["element"], "day": trip["day"], "night": trip["night"], "participating": trip["participating"]} if trip else None,
            "term": _term(sign, _degree(placement), versions["terms"]), "face": _face(sign, _degree(placement), versions["faces"]),
            "sect": sect_status, "angularity": HOUSE_KIND.get(house, "unknown"),
            "confidence": "partial" if _degree(placement) is None else "degree_ready",
            "zodiac_confidence": "high" if payload.get("zodiac") not in (None, "unknown") else "provisional",
            "motion_visibility": _motion_visibility(placement),
        })
    return {"sect": sect, "sect_source": sect_source, "sect_confidence": _sect_confidence(sect_source), "rule_versions": versions, "version_lock": version_lock, "planets": planets}


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate versioned classical planetary state")
    parser.add_argument("chart", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.chart.read_text(encoding="utf-8"))
    print(json.dumps(calculate(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
