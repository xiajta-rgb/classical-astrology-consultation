#!/usr/bin/env python3
"""Validate a supplied natal Chart Facts JSON without inventing degrees.

The validator checks traditional house rulers, deduplicates reception claims,
and classifies aspects as exact, sign-supported, boundary-sensitive, or
requiring degrees. Missing degrees are a review state, not an excuse to call a
geometrically possible aspect impossible.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SIGNS = ("白羊", "金牛", "双子", "巨蟹", "狮子", "处女", "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼")
SIGN_INDEX = {sign: i for i, sign in enumerate(SIGNS)}
RULERS = {
    "白羊": "火星", "金牛": "金星", "双子": "水星", "巨蟹": "月亮",
    "狮子": "太阳", "处女": "水星", "天秤": "金星", "天蝎": "火星",
    "射手": "木星", "摩羯": "土星", "水瓶": "土星", "双鱼": "木星",
}
ASPECT_ANGLES = {"合": 0.0, "六合": 60.0, "刑": 90.0, "拱": 120.0, "冲": 180.0}
ASPECT_CHARACTER = {"合": "merge_neutral", "六合": "flow", "拱": "flow", "刑": "friction", "冲": "polarity"}
CLASSICAL = ("太阳", "月亮", "水星", "金星", "火星", "木星", "土星")


def _circular_distance(a: float, b: float) -> float:
    delta = abs((a - b) % 360.0)
    return min(delta, 360.0 - delta)


def _longitude(placement: dict[str, Any]) -> float | None:
    if "ecl_lon" in placement:
        return float(placement["ecl_lon"]) % 360.0
    if "degree" not in placement or "sign" not in placement:
        return None
    sign = placement["sign"]
    if sign not in SIGN_INDEX:
        return None
    return (SIGN_INDEX[sign] * 30.0 + float(placement["degree"])) % 360.0


def _sign_potential(sign_a: str, sign_b: str, target: float, max_orb: float) -> tuple[str, float]:
    """Classify whether two 30-degree sign sectors can host a target aspect."""
    if sign_a not in SIGN_INDEX or sign_b not in SIGN_INDEX:
        return "unknown_sign", math.inf
    base_a, base_b = SIGN_INDEX[sign_a] * 30.0, SIGN_INDEX[sign_b] * 30.0
    best = math.inf
    # A coarse quarter-degree scan is enough to distinguish a real possibility
    # from a sector pair that cannot reach the target even at the boundaries.
    for step_a in range(0, 121):
        a = base_a + step_a * 0.25
        for step_b in range(0, 121):
            b = base_b + step_b * 0.25
            best = min(best, abs(_circular_distance(a, b) - target))
    if best <= max_orb:
        whole_delta = min((SIGN_INDEX[sign_a] - SIGN_INDEX[sign_b]) % 12, (SIGN_INDEX[sign_b] - SIGN_INDEX[sign_a]) % 12)
        expected_delta = min(round(target / 30.0), 12 - round(target / 30.0))
        return ("sign_supported" if whole_delta == expected_delta else "boundary_sensitive"), round(best, 2)
    return "no_sector_potential", round(best, 2)


def _aspect_result(aspect: dict[str, Any], placements: dict[str, Any], max_orb: float) -> dict[str, Any]:
    kind = aspect.get("type") or aspect.get("aspect_name")
    target = ASPECT_ANGLES.get(kind)
    a = placements.get(aspect.get("planet1"), {})
    b = placements.get(aspect.get("planet2"), {})
    evidence_layer = "classical_core" if aspect.get("planet1") in CLASSICAL and aspect.get("planet2") in CLASSICAL else "auxiliary_context"
    if target is None:
        return {**aspect, "evidence_layer": evidence_layer, "status": "unknown_aspect_type", "support_level": "unknown", "aspect_character": "unknown", "delivery_status": "unknown_without_geometry"}
    lon_a, lon_b = _longitude(a), _longitude(b)
    if lon_a is not None and lon_b is not None:
        separation = _circular_distance(lon_a, lon_b)
        orb = abs(separation - target)
        status = "exact" if orb <= max_orb else "outside_orb"
        applying = aspect.get("applying")
        if status == "exact" and applying in {True, False}:
            delivery_status = "application" if applying else "separation"
        elif status == "exact":
            delivery_status = "unknown_without_motion"
        else:
            delivery_status = "outside_orb"
        return {**aspect, "evidence_layer": evidence_layer, "separation": round(separation, 2), "orb": round(orb, 2), "status": status, "support_level": "degree_confirmed" if status == "exact" else "degree_rejected", "aspect_character": ASPECT_CHARACTER.get(kind, "unknown"), "delivery_status": delivery_status}
    status, boundary_error = _sign_potential(a.get("sign", ""), b.get("sign", ""), target, max_orb)
    support_level = {"sign_supported": "sector_supported", "boundary_sensitive": "boundary_only", "no_sector_potential": "not_supported", "unknown_sign": "unknown"}.get(status, "unknown")
    return {**aspect, "evidence_layer": evidence_layer, "status": status, "support_level": support_level, "minimum_sector_error": boundary_error, "needs_degrees": True, "aspect_character": ASPECT_CHARACTER.get(kind, "unknown"), "delivery_status": "sector_candidate_without_motion"}


def _reception_key(item: dict[str, Any]) -> tuple[str, str, str, str]:
    return (item.get("type", ""), item.get("planet1", ""), item.get("planet2", ""), str(item.get("house1", "")) + ":" + str(item.get("house2", "")))


def _validate_supplied_fly_ins(supplied: dict[str, Any], computed: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Check user fly-in claims without forcing one rulership school.

    A modern co-ruler may add a target (for example 8th -> 7th) while the
    traditional ruler remains 8th -> 9th. Such an addition is retained as a
    claim, not treated as a contradiction. A contradiction exists only when
    the supplied list omits the computed traditional destination.
    """
    duplicates, conflicts = [], []
    for item in computed:
        house = str(item["house"])
        raw = supplied.get(house, []) if isinstance(supplied, dict) else []
        targets = [int(x) for x in raw] if isinstance(raw, list) and all(str(x).isdigit() for x in raw) else []
        if len(targets) != len(set(targets)):
            duplicates.append({"house": item["house"], "targets": targets})
        if targets and item.get("ruler_house") not in targets:
            conflicts.append({"house": item["house"], "traditional_target": item.get("ruler_house"), "supplied_targets": targets})
    return duplicates, conflicts


def _validate_aspect_duplicates(aspects: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exact_seen: dict[tuple[str, str, str], int] = {}
    unordered_seen: dict[tuple[str, str, str], int] = {}
    exact_duplicates, reverse_duplicates = [], []
    for item in aspects:
        key = (str(item.get("planet1", "")), str(item.get("planet2", "")), str(item.get("type") or item.get("aspect_name") or ""))
        unordered_key = (*sorted(key[:2]), key[2])
        if exact_seen.get(key, 0):
            exact_duplicates.append(item)
        elif unordered_seen.get(unordered_key, 0):
            reverse_duplicates.append(item)
        exact_seen[key] = exact_seen.get(key, 0) + 1
        unordered_seen[unordered_key] = unordered_seen.get(unordered_key, 0) + 1
    return exact_duplicates, reverse_duplicates


def _validate_supplied_receptions(supplied: list[dict[str, Any]], expected: list[dict[str, Any]]) -> dict[str, Any]:
    expected_dirs = {item.get("direction") for item in expected}
    unsupported, mutual_missing_reverse = [], []
    for item in supplied:
        direction = f"{item.get('planet1', '')}->{item.get('planet2', '')}"
        if item.get("type") == "mutual":
            reverse = f"{item.get('planet2', '')}->{item.get('planet1', '')}"
            if direction not in expected_dirs or reverse not in expected_dirs:
                mutual_missing_reverse.append(item)
        elif direction not in expected_dirs:
            unsupported.append(item)
    return {
        "supported_domicile_claims": len(supplied) - len(unsupported) - len(mutual_missing_reverse),
        "unsupported_domicile_claims": unsupported,
        "mutual_missing_reverse": mutual_missing_reverse,
        "version": "direction_plus_connection_required",
    }


def _reception_connection_audit(supplied: list[dict[str, Any]], aspects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Audit whether a reception direction has a separately declared aspect.

    Directional dignity is retained even when no connection is present, but
    the locked reception rule must not call it a completed delivery.
    """
    result: list[dict[str, Any]] = []
    for item in supplied:
        left, right = item.get("planet1"), item.get("planet2")
        matches = [
            aspect for aspect in aspects
            if {aspect.get("planet1"), aspect.get("planet2")} == {left, right}
        ]
        if not matches:
            status = "no_aspect_claim"
        else:
            levels = {match.get("support_level") for match in matches}
            if "degree_confirmed" in levels:
                status = "degree_confirmed_connection"
            elif "sector_supported" in levels:
                status = "sector_connection_unconfirmed"
            elif "boundary_only" in levels:
                status = "boundary_connection_unconfirmed"
            else:
                status = "unknown_connection"
        result.append({
            "direction": f"{left}->{right}",
            "type": item.get("type"),
            "connection_status": status,
            "matching_aspect_count": len(matches),
        })
    return result


def validate(payload: dict[str, Any], max_orb: float = 8.0) -> dict[str, Any]:
    placements = payload.get("placements", {})
    cusps = payload.get("cusps", {})
    fly_ins = []
    for house, sign in sorted(cusps.items(), key=lambda pair: int(pair[0])):
        ruler = RULERS.get(sign)
        placement = placements.get(ruler, {})
        fly_ins.append({"house": int(house), "cusp_sign": sign, "ruler": ruler, "ruler_house": placement.get("house")})

    expected_receptions = []
    names = [name for name in placements if name in CLASSICAL]
    for left in names:
        sign_left = placements[left].get("sign")
        for right in names:
            if left == right:
                continue
            sign_right = placements[right].get("sign")
            if RULERS.get(sign_left) == right:
                expected_receptions.append({"direction": f"{left}->{right}", "type": "domicile_reception", "from_sign": sign_left, "to_sign": sign_right})
    mutual_pairs = []
    for item in expected_receptions:
        left, right = item["direction"].split("->")
        if any(x["direction"] == f"{right}->{left}" for x in expected_receptions) and tuple(sorted((left, right))) not in mutual_pairs:
            mutual_pairs.append(tuple(sorted((left, right))))

    supplied = payload.get("receptions", [])
    seen: set[tuple[str, str, str, str]] = set()
    duplicates = []
    for item in supplied:
        key = _reception_key(item)
        if key in seen:
            duplicates.append(item)
        seen.add(key)
    aspects = [_aspect_result(item, placements, max_orb) for item in payload.get("aspects", [])]
    reception_validation = _validate_supplied_receptions(supplied, expected_receptions)
    reception_connection_audit = _reception_connection_audit(supplied, aspects)
    reception_validation["connection_audit"] = reception_connection_audit
    reception_validation["connection_status_counts"] = {
        status: sum(1 for item in reception_connection_audit if item.get("connection_status") == status)
        for status in sorted({item.get("connection_status") for item in reception_connection_audit})
    }
    reception_validation["connection_required_unmet"] = [
        item for item in reception_connection_audit
        if item.get("connection_status") not in {"degree_confirmed_connection"}
    ]
    aspect_duplicates, aspect_reverse_duplicates = _validate_aspect_duplicates(payload.get("aspects", []))
    fly_in_duplicates, fly_in_conflicts = _validate_supplied_fly_ins(payload.get("fly_ins", {}), fly_ins)
    review_required = bool(duplicates or reception_validation["unsupported_domicile_claims"] or reception_validation["mutual_missing_reverse"] or aspect_duplicates or aspect_reverse_duplicates or fly_in_duplicates or fly_in_conflicts or any(x.get("needs_degrees") for x in aspects) or payload.get("zodiac") in (None, "unknown") or payload.get("house_system") in (None, "unknown"))
    return {
        "chart_id": payload.get("chart_id"),
        "rulership_fly_ins": fly_ins,
        "expected_domicile_receptions": expected_receptions,
        "mutual_domicile_pairs": [list(pair) for pair in mutual_pairs],
        "supplied_reception_duplicates": duplicates,
        "supplied_reception_validation": reception_validation,
        "supplied_aspect_duplicates": aspect_duplicates,
        "supplied_aspect_reverse_duplicates": aspect_reverse_duplicates,
        "supplied_fly_in_duplicates": fly_in_duplicates,
        "supplied_fly_in_conflicts": fly_in_conflicts,
        "aspects": aspects,
        "review_required": review_required or bool(reception_validation["connection_required_unmet"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate natal Chart Facts JSON")
    parser.add_argument("chart", type=Path)
    parser.add_argument("--max-orb", type=float, default=8.0)
    args = parser.parse_args()
    payload = json.loads(args.chart.read_text(encoding="utf-8"))
    print(json.dumps(validate(payload, args.max_orb), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
