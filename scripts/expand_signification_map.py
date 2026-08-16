#!/usr/bin/env python3
"""Expand validated Chart Facts into a complete, bounded signification map.

The map is an internal coverage layer. It deliberately enumerates available
meanings before composition selects the leading mechanism, so depth does not
depend on whichever keyword the renderer happens to remember first.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = ROOT / "references/signification-ontology.yaml"
PLANET_ALIASES = {
    "太阳": "Sun", "月亮": "Moon", "水星": "Mercury", "金星": "Venus", "火星": "Mars",
    "木星": "Jupiter", "土星": "Saturn", "天王星": "Uranus", "海王星": "Neptune", "冥王星": "Pluto",
}
ASPECT_ALIASES = {
    "合": "conjunction", "合相": "conjunction", "conj": "conjunction", "conjunction": "conjunction",
    "六合": "sextile", "六分": "sextile", "sextile": "sextile",
    "刑": "square", "刑相": "square", "square": "square",
    "拱": "trine", "三合": "trine", "trine": "trine",
    "冲": "opposition", "对冲": "opposition", "opposition": "opposition",
    "梅花": "quincunx", "quincunx": "quincunx",
}


def _normalise_planet(value: Any) -> str:
    raw = str(value or "")
    return PLANET_ALIASES.get(raw, raw)


def _normalise_aspect(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return ASPECT_ALIASES.get(raw, raw)


def _house_number(item: dict[str, Any]) -> int | None:
    raw = item.get("house_number", item.get("house"))
    try:
        number = int(raw)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _conditions(item: dict[str, Any]) -> list[str]:
    values = []
    for key in ("dignity", "status", "sect", "angularity", "motion", "visibility"):
        value = item.get(key)
        if value not in (None, "", "unknown", "unknown_due_to_missing_motion", "unknown_due_to_missing_visibility"):
            values.append(str(value))
    if item.get("retrograde") is True:
        values.append("retrograde")
    return values


def expand(chart_facts: dict[str, Any], responsibility_chain: dict[str, Any] | None = None) -> dict[str, Any]:
    ontology = yaml.safe_load(ONTOLOGY.read_text(encoding="utf-8"))
    planets = ontology.get("planets", {})
    houses = {int(key): value for key, value in ontology.get("houses", {}).items()}
    signs = {int(key): value for key, value in ontology.get("signs", {}).items()}
    aspects = ontology.get("aspects", {})
    placements = chart_facts.get("placements") or chart_facts.get("planets") or {}
    nodes: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for name, raw in placements.items():
        item = dict(raw or {})
        planet = _normalise_planet(name)
        house = _house_number(item)
        zodiac = item.get("zodiac") or {}
        sign_index = zodiac.get("index") if isinstance(zodiac, dict) else None
        try:
            sign_index = int(sign_index)
        except (TypeError, ValueError):
            sign_index = None
        planet_map = planets.get(planet, {})
        house_map = houses.get(house, {}) if house else {}
        sign_map = signs.get(sign_index, {}) if sign_index is not None else {}
        if not planet_map:
            unresolved.append(f"planet_ontology_missing:{planet}")
        if house is None:
            unresolved.append(f"house_missing:{planet}")
        if sign_index is None:
            unresolved.append(f"sign_missing:{planet}")
        elif not sign_map:
            unresolved.append(f"sign_ontology_missing:{sign_index}")
        nodes.append({
            "id": f"planet:{planet}",
            "kind": "planet_placement",
            "planet": planet,
            "sign": sign_map.get("name") or zodiac.get("name") or item.get("sign"),
            "sign_index": sign_index,
            "house": house,
            "keywords": sorted(set(
                planet_map.get("functions", [])
                + house_map.get("domain", [])
                + sign_map.get("mode", [])
            )),
            "event_verbs": sorted(set(
                planet_map.get("event_verbs", [])
                + house_map.get("event_verbs", [])
                + sign_map.get("event_verbs", [])
            )),
            "conditions": _conditions(item),
            "source": "Chart_Facts",
        })

    edges: list[dict[str, Any]] = []
    for index, raw in enumerate(chart_facts.get("aspects", []) or [], start=1):
        item = dict(raw or {})
        left = _normalise_planet(item.get("planet1"))
        right = _normalise_planet(item.get("planet2"))
        aspect = _normalise_aspect(item.get("type", item.get("aspect")))
        relation = aspects.get(aspect, {})
        if not relation:
            unresolved.append(f"aspect_ontology_missing:{aspect}")
        edges.append({
            "id": f"aspect:{index}",
            "kind": "planetary_relation",
            "planet1": left,
            "planet2": right,
            "aspect": aspect,
            "orb": item.get("orb"),
            "keywords": relation.get("relation", []),
            "risks": relation.get("risk", []),
            "source": "Chart_Facts",
        })

    responsibility = []
    for item in (responsibility_chain or {}).get("house_flying", []):
        responsibility.append({
            "house": item.get("house"),
            "ruler": item.get("ruler"),
            "ruler_house": item.get("ruler_house"),
            "direction": item.get("direction"),
            "source": "responsibility_chain",
        })

    return {
        "schema_version": "SEMANTIC-COVERAGE-0.2",
        "chart_id": chart_facts.get("chart_id"),
        "ontology_version": ontology.get("version"),
        "nodes": nodes,
        "edges": edges,
        "responsibility_links": responsibility,
        "coverage": {
            "planet_nodes": len(nodes),
            "sign_covered_nodes": sum(1 for node in nodes if node.get("sign_index") in signs),
            "aspect_edges": len(edges),
            "responsibility_links": len(responsibility),
            "ontology_planets": sorted(planets),
            "ontology_houses": sorted(houses),
            "ontology_signs": sorted(signs),
            "ontology_aspects": sorted(aspects),
        },
        "unresolved": sorted(set(unresolved)),
        "output_policy": {
            "exhaustive_internal_map": True,
            "prioritized_external_render": "composition_and_evidence_gate",
            "never_treat_keywords_as_conclusions": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chart_facts", type=Path)
    parser.add_argument("--responsibilities", type=Path)
    args = parser.parse_args()
    chart = json.loads(args.chart_facts.read_text(encoding="utf-8"))
    responsibilities = json.loads(args.responsibilities.read_text(encoding="utf-8")) if args.responsibilities else None
    print(json.dumps(expand(chart, responsibilities), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
