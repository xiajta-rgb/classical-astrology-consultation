#!/usr/bin/env python3
"""Adversarial regression tests for reception-direction/connection separation."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_chart_facts import validate
    from scripts.score_hypothesis_cards import score
except ModuleNotFoundError:
    from validate_chart_facts import validate
    from score_hypothesis_cards import score


ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "references" / "fixtures" / name).read_text(encoding="utf-8"))


def self_test() -> int:
    user = _read("user-chart-1996-supplied.json")
    user_result = validate(user)
    user_counts = user_result["supplied_reception_validation"]["connection_status_counts"]
    if user_counts != {"no_aspect_claim": 9}:
        print(f"FAIL direction-only baseline: {user_counts}")
        return 1

    confirmed = _read("synthetic-chart-delivery-evidence.json")
    confirmed_result = validate(confirmed)
    confirmed_counts = confirmed_result["supplied_reception_validation"]["connection_status_counts"]
    if confirmed_counts != {"degree_confirmed_connection": 2}:
        print(f"FAIL degree-confirmed connection: {confirmed_counts}")
        return 1

    sector = copy.deepcopy(confirmed)
    for planet in ("水星", "火星"):
        sector["placements"][planet].pop("degree", None)
    sector_result = validate(sector)
    sector_counts = sector_result["supplied_reception_validation"]["connection_status_counts"]
    if sector_counts != {"sector_connection_unconfirmed": 2}:
        print(f"FAIL sector-only connection: {sector_counts}")
        return 1

    reversed_claim = copy.deepcopy(confirmed)
    reversed_claim["receptions"] = [{"type": "reception", "planet1": "月亮", "planet2": "火星"}]
    reversed_result = validate(reversed_claim)
    validation = reversed_result["supplied_reception_validation"]
    if len(validation["unsupported_domicile_claims"]) != 1 or validation["connection_status_counts"] != {"no_aspect_claim": 1}:
        print(f"FAIL unsupported direction: {validation}")
        return 1

    scoring_payload = {
        "status": "candidate",
        "rule_version_lock": {"terms": True, "triplicity": True, "faces": True, "reception": True, "aspect": True},
        "cards": [{
            "topic": "connection_gate",
            "evidence_ids": ["reception-1"],
            "evidence_items": [{"id": "reception-1", "source_ids": ["R25", "R26"], "source_cluster": "reception_validation", "connection_status": "no_aspect_claim"}],
            "Counter_test": ["需要度数与应用/分离核验"],
            "observation_contract": {"status": "uncollected", "items": [], "tombstones": []},
        }],
    }
    scoring_registry = {"sources": {"R25": {"status": "verified", "layer": "secondary_technical"}, "R26": {"status": "verified", "layer": "secondary_technical"}}}
    scored = score(scoring_payload, scoring_registry, {"metadata": {"rule_version_lock": scoring_payload["rule_version_lock"]}})
    card = scored["cards"][0]
    if card["grade_cap"] != "B" or "reception_connection_unconfirmed" not in card["publication_reasons"]:
        print(f"FAIL unconfirmed reception escaped score cap: {card}")
        return 1

    print("PASS reception-connection self-test: direction-only, sector-only, degree-confirmed and unsupported branches")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
