#!/usr/bin/env python3
"""Build an auditable natal Chart Facts package and release-readiness gate.

This is deliberately a facts pipeline, not an interpretation generator. It
combines the existing geometry/reception checks with planetary state output and
keeps missing birth metadata as explicit blockers.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.planetary_state import CLASSICAL, calculate as calculate_state
    from scripts.rulership_candidates import calculate as calculate_rulership_candidates
    from scripts.validate_chart_facts import validate as validate_facts
    from scripts.validate_observations import validate as validate_observations
except ModuleNotFoundError:  # direct execution from the scripts directory
    from planetary_state import CLASSICAL, calculate as calculate_state
    from rulership_candidates import calculate as calculate_rulership_candidates
    from validate_chart_facts import validate as validate_facts
    from validate_observations import validate as validate_observations


TOPIC_CHAINS = {
    "self_decision": (1,),
    "money_income": (2, 11, 10),
    "shared_resources": (8, 7, 2),
    "career_public_role": (10, 1, 6, 7, 11),
    "relationship_family": (7, 4, 1, 8),
    "creation_children": (5, 1, 4, 8),
    "pressure_risk": (6, 8, 12),
}

SENSITIVE_TOPIC_GATES = {
    "creation_children": "G2_context_only_no_reproductive_outcome",
    "pressure_risk": "G1_no_medical_or_mortality_claim",
    "shared_resources": "financial_due_diligence_required",
    "relationship_family": "no_deterministic_relationship_or_family_outcome",
}


def _metadata(payload: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    placements = payload.get("placements", {})
    degrees_available = all("degree" in placements.get(p, {}) or "ecl_lon" in placements.get(p, {}) for p in CLASSICAL)
    asc = payload.get("axes", {}).get("asc", {})
    asc_degree = asc.get("degree")
    boundary_risk = "unknown"
    if asc_degree is not None:
        boundary_risk = "high" if float(asc_degree) <= 1 or float(asc_degree) >= 29 else "low"
    missing = []
    for key in ("birth_date", "birth_time", "birth_place", "zodiac", "house_system"):
        if not payload.get(key) or payload.get(key) == "unknown":
            missing.append(key)
    if not degrees_available:
        missing.append("planetary_degrees")
    for version_key in ("terms", "triplicity", "faces", "reception", "aspect"):
        if not state.get("version_lock", {}).get(version_key):
            missing.append(f"rule_versions.{version_key}")
    return {
        "chart_id": payload.get("chart_id"),
        "source": payload.get("source", "undeclared"),
        "zodiac": payload.get("zodiac", "unknown"),
        "house_system": payload.get("house_system", "unknown"),
        "sect": state["sect"],
        "sect_source": state["sect_source"],
        "sect_confidence": state.get("sect_confidence", "none"),
        "degrees_available": degrees_available,
        "ascendant_boundary_risk": boundary_risk,
        "rule_versions": state.get("rule_versions", {}),
        "rule_version_lock": state.get("version_lock", {}),
        "missing_contract_fields": missing,
    }


def _topic_coverage(payload: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    houses = {int(item["house"]): item for item in facts["rulership_fly_ins"]}
    coverage = {}
    for topic, chain in TOPIC_CHAINS.items():
        covered = [house for house in chain if house in houses and houses[house].get("ruler")]
        coverage[topic] = {"houses": list(chain), "covered": covered, "status": "available" if covered else "N/A"}
    return coverage


def _responsibility_chains(facts: dict[str, Any]) -> dict[str, Any]:
    """Materialize house responsibility and cross-topic de-duplication data."""
    fly = {int(item["house"]): item for item in facts["rulership_fly_ins"]}
    chains: dict[str, Any] = {}
    ruler_topics: dict[str, list[str]] = {}
    for topic, houses in TOPIC_CHAINS.items():
        path = []
        for house in houses:
            item = fly.get(house)
            if not item or not item.get("ruler"):
                continue
            ruler = item["ruler"]
            path.append({"house": house, "ruler": ruler, "ruler_house": item.get("ruler_house")})
            ruler_topics.setdefault(ruler, []).append(topic)
        ruler_counts = Counter(item["ruler"] for item in path)
        chains[topic] = {
            "houses": list(houses),
            "path": path,
            "unique_rulers": sorted(ruler_counts),
            "within_topic_reused_rulers": sorted(ruler for ruler, count in ruler_counts.items() if count > 1),
            "deduplication": "same ruler is one planetary dependency; house responsibility remains separately visible",
        }
    return {
        "topics": chains,
        "cross_topic_ruler_index": {ruler: sorted(set(topics)) for ruler, topics in ruler_topics.items()},
        "cross_topic_shared_rulers": sorted(ruler for ruler, topics in ruler_topics.items() if len(set(topics)) > 1),
        "rule": "house chains are retained; repeated planetary state is discounted once when scoring cross-topic evidence",
    }


def build(payload: dict[str, Any]) -> dict[str, Any]:
    facts = validate_facts(payload)
    state = calculate_state(payload)
    observation_validation = validate_observations(payload.get("observations"))
    metadata = _metadata(payload, state)
    blockers: list[str] = []
    warnings: list[str] = []
    if metadata["missing_contract_fields"]:
        blockers.append("chart_contract_incomplete")
    if not all(metadata.get("rule_version_lock", {}).values()):
        blockers.append("rule_versions_unlocked")
    if facts["supplied_reception_duplicates"]:
        warnings.append("duplicate_reception_claims")
    if facts["supplied_fly_in_duplicates"]:
        warnings.append("duplicate_fly_in_claims")
    if facts["supplied_fly_in_conflicts"]:
        warnings.append("fly_in_claim_conflict")
    if facts["supplied_aspect_duplicates"]:
        warnings.append("duplicate_aspect_claims")
    if facts["supplied_aspect_reverse_duplicates"]:
        warnings.append("reverse_aspect_claims")
    reception_validation = facts["supplied_reception_validation"]
    if reception_validation["unsupported_domicile_claims"] or reception_validation["mutual_missing_reverse"]:
        warnings.append("reception_claim_unmatched")
    if reception_validation.get("connection_required_unmet"):
        warnings.append("reception_connection_requires_degree_validation")
    if any(item.get("needs_degrees") for item in facts["aspects"]):
        warnings.append("aspect_degrees_required")
    if any(item.get("status") in ("outside_orb", "no_sector_potential", "unknown_aspect_type") for item in facts["aspects"]):
        warnings.append("aspect_data_conflict")
    if metadata["ascendant_boundary_risk"] == "high":
        warnings.append("ascendant_boundary_risk_high")
    if not payload.get("source"):
        warnings.append("source_not_declared")
    if observation_validation["findings"]:
        warnings.append("observation_contract_invalid")
    interpretation_ready = not blockers and not warnings
    topic_coverage = _topic_coverage(payload, facts)
    responsibility_chains = _responsibility_chains(facts)
    rulership_candidates = calculate_rulership_candidates(
        payload,
        facts["rulership_fly_ins"],
        TOPIC_CHAINS,
        state["sect"],
        state.get("sect_source"),
        state.get("sect_confidence"),
    )
    sensitive_topic_gates = {topic: SENSITIVE_TOPIC_GATES.get(topic, "standard_structural_language") for topic in TOPIC_CHAINS}
    return {
        "chart_id": payload.get("chart_id"),
        "metadata": metadata,
        "chart_facts": {
            "provenance": {
                "placements": "user_declared_unrecomputed",
                "cusps": "user_declared_unrecomputed",
                "aspect_claims": "user_declared_sector_validated",
                "rulership_fly_ins": "computed_traditional_from_declared_cusps",
                "reception_validation": "computed_from_declared_signs_and_locked_rule_version",
                "planetary_state": "computed_from_declared_signs_houses_with_provisional_zodiac",
                "rulership_candidates": "computed_from_declared_cusp_signs_and_locked_dignity_versions",
            },
            "placements": payload.get("placements", {}),
            "cusps": payload.get("cusps", {}),
            "rulership_fly_ins": facts["rulership_fly_ins"],
            "supplied_fly_ins": payload.get("fly_ins", {}),
            "supplied_fly_in_duplicates": facts["supplied_fly_in_duplicates"],
            "supplied_fly_in_conflicts": facts["supplied_fly_in_conflicts"],
            "supplied_reception_duplicates": facts["supplied_reception_duplicates"],
            "supplied_reception_validation": facts["supplied_reception_validation"],
            "supplied_aspect_duplicates": facts["supplied_aspect_duplicates"],
            "supplied_aspect_reverse_duplicates": facts["supplied_aspect_reverse_duplicates"],
            "expected_domicile_receptions": facts["expected_domicile_receptions"],
            "mutual_domicile_pairs": facts["mutual_domicile_pairs"],
            "aspect_validation": facts["aspects"],
            "planetary_state": state,
            "rulership_candidates": rulership_candidates,
        },
        "topic_coverage": topic_coverage,
        "responsibility_chains": responsibility_chains,
        "sensitive_topic_gates": sensitive_topic_gates,
        "observations": observation_validation.get("observations", {}),
        "observation_validation": observation_validation,
        "release_gate": {
            "fact_inventory_ready": bool(payload.get("placements") and payload.get("cusps")),
            "natal_interpretation_ready": interpretation_ready,
            "publishable": interpretation_ready,
            "blockers": blockers,
            "warnings": warnings,
            "decision": "publish" if interpretation_ready else "hold",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build auditable natal Chart Facts JSON")
    parser.add_argument("chart", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build(json.loads(args.chart.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
