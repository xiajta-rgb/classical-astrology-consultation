#!/usr/bin/env python3
"""Enumerate dignity-based candidates for a topical place.

This module intentionally does not collapse the five classical dignities into
one score.  It records which planets have which claims over each house cusp,
leaves terms/faces unavailable when the place degree is absent, and keeps the
traditional domicile ruler separate from the candidate set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.planetary_state import (
        CHALDEAN,
        CLASSICAL,
        DOMICILE,
        EGYPTIAN_TERMS,
        EXALTATION,
        TRIPLICITY,
    )
    from scripts.validate_chart_facts import RULERS
except ModuleNotFoundError:
    from planetary_state import CHALDEAN, CLASSICAL, DOMICILE, EGYPTIAN_TERMS, EXALTATION, TRIPLICITY
    from validate_chart_facts import RULERS


TOPIC_CHAINS = {
    "self_decision": (1,),
    "money_income": (2, 11, 10),
    "shared_resources": (8, 7, 2),
    "career_public_role": (10, 1, 6, 7, 11),
    "relationship_family": (7, 4, 1, 8),
    "creation_children": (5, 1, 4, 8),
    "pressure_risk": (6, 8, 12),
}


def _place(value: Any) -> tuple[str | None, float | None]:
    if isinstance(value, str):
        return value, None
    if isinstance(value, dict):
        sign = value.get("sign")
        degree = value.get("degree")
        try:
            degree = float(degree) if degree is not None else None
        except (TypeError, ValueError):
            degree = None
        if degree is not None and not 0 <= degree < 30:
            degree = None
        return sign, degree
    return None, None


def _term(sign: str | None, degree: float | None) -> tuple[str | None, list[float] | None]:
    if sign is None or degree is None or sign not in EGYPTIAN_TERMS:
        return None, None
    for start, end, ruler in EGYPTIAN_TERMS[sign]:
        if start <= degree < end:
            return ruler, [start, end]
    return None, None


def _face(sign: str | None, degree: float | None) -> tuple[str | None, list[float] | None]:
    if sign is None or degree is None:
        return None, None
    signs = tuple({sign})
    # Keep the calculation independent of any modern co-ruler table.  The
    # Chaldean sequence is applied by sign order, three faces per sign.
    sign_order = (
        "鐧界緤", "閲戠墰", "鍙屽瓙", "宸ㄨ煿", "鐙瓙", "澶勫コ",
        "澶╃Г", "澶╄潕", "灏勬墜", "鎽╃警", "姘寸摱", "鍙岄奔",
    )
    if sign not in sign_order:
        return None, None
    index = int(degree // 10)
    ruler = CHALDEAN[(sign_order.index(sign) * 3 + index) % 7]
    return ruler, [index * 10, (index + 1) * 10]


def _triplicity_claims(sign: str | None, sect: str) -> list[tuple[str, str]]:
    if not sign:
        return []
    for data in TRIPLICITY.values():
        if sign not in data["signs"]:
            continue
        claims: list[tuple[str, str]] = []
        if sect in {"day", "night"}:
            role = "day" if sect == "day" else "night"
            claims.append((data[role], f"triplicity_{role}"))
        claims.append((data["participating"], "triplicity_participating"))
        return claims
    return []


def _candidate_claims(sign: str | None, degree: float | None, sect: str) -> tuple[dict[str, list[str]], dict[str, Any]]:
    claims: dict[str, list[str]] = {planet: [] for planet in CLASSICAL}
    if sign:
        for planet in CLASSICAL:
            if sign in DOMICILE.get(planet, ()):
                claims[planet].append("domicile")
            if EXALTATION.get(planet) == sign:
                claims[planet].append("exaltation")
        for planet, role in _triplicity_claims(sign, sect):
            if planet in claims:
                claims[planet].append(role)
    term_ruler, term_interval = _term(sign, degree)
    face_ruler, face_interval = _face(sign, degree)
    if term_ruler in claims:
        claims[term_ruler].append("term")
    if face_ruler in claims:
        claims[face_ruler].append("face")
    claims = {planet: values for planet, values in claims.items() if values}
    unavailable = [] if degree is not None else ["term", "face"]
    return claims, {
        "term_ruler": term_ruler,
        "term_interval": term_interval,
        "face_ruler": face_ruler,
        "face_interval": face_interval,
        "unavailable_claim_types": unavailable,
    }


def calculate(
    payload: dict[str, Any],
    rulership_fly_ins: list[dict[str, Any]] | None = None,
    topic_chains: dict[str, tuple[int, ...]] | None = None,
    sect: str | None = None,
    sect_source: str | None = None,
    sect_confidence: str | None = None,
) -> dict[str, Any]:
    cusps = payload.get("cusps", {})
    fly_by_house = {int(item["house"]): item for item in (rulership_fly_ins or [])}
    sect_value = sect or payload.get("sect") or "unknown"
    houses: list[dict[str, Any]] = []
    for raw_house, raw_place in sorted(cusps.items(), key=lambda pair: int(pair[0])):
        house = int(raw_house)
        sign, degree = _place(raw_place)
        claims, detail = _candidate_claims(sign, degree, sect_value)
        candidates = [
            {"planet": planet, "claims": values, "claim_count": len(values)}
            for planet, values in sorted(claims.items())
        ]
        traditional = fly_by_house.get(house, {})
        houses.append({
            "house": house,
            "place": {"sign": sign, "degree": degree},
            "traditional_domicile_ruler": traditional.get("ruler") or RULERS.get(sign),
            "traditional_ruler_house": traditional.get("ruler_house"),
            "candidates": candidates,
            "candidate_claim_detail": detail,
            "status": "resolved" if degree is not None else "provisional_sign_only",
            "selection_rule": "retain claims by dignity; do not sum them into a single fortune score",
        })
    topic_map = topic_chains or TOPIC_CHAINS
    topics: dict[str, Any] = {}
    by_house = {item["house"]: item for item in houses}
    for topic, chain in topic_map.items():
        entries = []
        for house in chain:
            item = by_house.get(house)
            if item:
                entries.append({
                    "house": house,
                    "traditional_domicile_ruler": item.get("traditional_domicile_ruler"),
                    "candidates": item.get("candidates", []),
                    "status": item.get("status"),
                })
        domicile_rulers = sorted({entry.get("traditional_domicile_ruler") for entry in entries if entry.get("traditional_domicile_ruler")})
        candidate_planets = sorted({candidate.get("planet") for entry in entries for candidate in entry.get("candidates", []) if candidate.get("planet")})
        competing = sorted(set(candidate_planets) - set(domicile_rulers))
        conflict_houses = sorted(entry.get("house") for entry in entries if any(candidate.get("planet") != entry.get("traditional_domicile_ruler") for candidate in entry.get("candidates", [])))
        topics[topic] = {
            "houses": list(chain),
            "places": entries,
            "traditional_domicile_rulers": domicile_rulers,
            "candidate_planets": candidate_planets,
            "competing_candidate_planets": competing,
            "conflict_houses": conflict_houses,
            "status": "competing_candidates" if competing else "domicile_only_candidate_set",
            "selection_rule": "report the disagreement and missing discriminators; do not select a winner by claim_count",
        }
    return {
        "version": "RULERSHIP-CANDIDATES-0.1",
        "sect": sect_value,
        "sect_source": sect_source or ("declared" if payload.get("sect") in {"day", "night"} else "not_provided_to_candidate_layer"),
        "sect_confidence": sect_confidence or ("high" if sect_source == "declared" else "unknown"),
        "rule_versions": {"terms": "egyptian", "faces": "chaldean", "triplicity": "dorotheus_style_three_rulers"},
        "houses": houses,
        "topics": topics,
        "rule": "traditional domicile ruler remains the responsibility-chain anchor; other dignities are candidate claims, not additive points",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Enumerate dignity-based rulership candidates")
    parser.add_argument("chart", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        sample = {"cusps": {"1": "巨蟹", "2": "狮子"}}
        provisional = calculate(sample, sect="night", sect_source="inferred", sect_confidence="low")
        if any(item.get("status") != "provisional_sign_only" for item in provisional["houses"]):
            print("FAIL sign-only candidate status")
            return 1
        resolved = calculate({"cusps": {"1": {"sign": "巨蟹", "degree": 15.0}}}, sect="night", sect_source="declared", sect_confidence="high")
        if resolved["houses"][0].get("status") != "resolved" or resolved["houses"][0]["candidate_claim_detail"]["unavailable_claim_types"]:
            print("FAIL degree-bearing candidate status")
            return 1
        if not resolved["topics"]["self_decision"].get("competing_candidate_planets"):
            print("FAIL competing-candidate summary")
            return 1
        print("PASS rulership-candidate self-test")
        return 0
    if args.chart is None:
        parser.error("chart is required unless --self-test is used")
    result = calculate(json.loads(args.chart.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
