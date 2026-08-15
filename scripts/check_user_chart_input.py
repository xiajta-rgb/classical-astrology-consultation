#!/usr/bin/env python3
"""Regression gate for the user-supplied 1996 Hunan natal summary.

This is an input-integrity check, not a chart interpretation. It ensures the
full supplied claim set survives normalization and that missing birth data
keeps the release decision on HOLD.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.build_natal_facts import build
    from scripts.render_natal_report import render
except ModuleNotFoundError:
    from build_natal_facts import build
    from render_natal_report import render


EXPECTED_PLACEMENTS = {
    "太阳": ("天蝎", 4), "月亮": ("天蝎", 5), "水星": ("天蝎", 5),
    "金星": ("天秤", 3), "火星": ("处女", 2), "木星": ("摩羯", 6),
    "土星": ("白羊", 9), "天王": ("水瓶", 7), "海王": ("摩羯", 6),
    "冥王": ("射手", 5), "北交": ("天秤", 3), "凯龙": ("天秤", 4),
    "婚神": ("白羊", 9), "南交": ("白羊", 9), "福点": ("巨蟹", 12),
}
EXPECTED_CUSPS = {"1": "巨蟹", "2": "狮子", "3": "处女", "4": "天秤", "5": "天蝎", "6": "射手", "7": "摩羯", "8": "水瓶", "9": "双鱼", "10": "白羊", "11": "金牛", "12": "双子"}


def check(payload: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    placements = payload.get("placements", {})
    if len(placements) != len(EXPECTED_PLACEMENTS):
        findings.append(f"placement_count={len(placements)} expected={len(EXPECTED_PLACEMENTS)}")
    for planet, expected in EXPECTED_PLACEMENTS.items():
        actual = placements.get(planet, {})
        if (actual.get("sign"), actual.get("house")) != expected:
            findings.append(f"placement_mismatch:{planet}")
    if payload.get("cusps") != EXPECTED_CUSPS:
        findings.append("cusp_signs_mismatch")
    if len(payload.get("aspects", [])) != 43:
        findings.append(f"aspect_count={len(payload.get('aspects', []))} expected=43")
    classical_names = {"太阳", "月亮", "水星", "金星", "火星", "木星", "土星"}
    if len(payload.get("receptions", [])) != 9:
        findings.append(f"reception_claim_count={len(payload.get('receptions', []))} expected=9")
    if set(payload.get("fly_ins", {})) != set(EXPECTED_CUSPS):
        findings.append("fly_in_house_coverage_incomplete")
    if payload.get("axes", {}).get("asc") != {"sign": "巨蟹", "degree": 29.0}:
        findings.append("ascendant_mismatch")

    facts = build(payload)
    gate = facts["release_gate"]
    if not gate["fact_inventory_ready"]:
        findings.append("fact_inventory_not_ready")
    if gate["decision"] != "hold":
        findings.append("incomplete_input_did_not_hold")
    required_missing = {"birth_date", "birth_time", "birth_place", "zodiac", "house_system", "planetary_degrees"}
    if not required_missing.issubset(set(facts["metadata"]["missing_contract_fields"])):
        findings.append("missing_contract_fields_not_explicit")
    if facts["metadata"].get("sect_confidence") != "low":
        findings.append("sect_inference_confidence_not_low")
    aspect_layers = facts["chart_facts"]["aspect_validation"]
    if sum(1 for item in aspect_layers if item.get("evidence_layer") == "classical_core") != 8:
        findings.append("classical_aspect_layer_count_mismatch")
    if any(item.get("evidence_layer") == "classical_core" and (item.get("planet1") not in classical_names or item.get("planet2") not in classical_names) for item in aspect_layers):
        findings.append("auxiliary_aspect_promoted_to_core")
    support_levels = {item.get("support_level") for item in aspect_layers}
    if support_levels != {"sector_supported", "boundary_only"}:
        findings.append(f"aspect_support_levels_unexpected:{sorted(support_levels)}")
    if sum(1 for item in aspect_layers if item.get("support_level") == "sector_supported") != 33 or sum(1 for item in aspect_layers if item.get("support_level") == "boundary_only") != 10:
        findings.append("aspect_support_level_counts_mismatch")
    if set(item.get("delivery_status") for item in aspect_layers) != {"sector_candidate_without_motion"}:
        findings.append("aspect_delivery_status_not_downgraded")
    classical_states = [item for item in facts["chart_facts"]["planetary_state"]["planets"] if item.get("layer") == "classical"]
    if classical_states and any(item.get("zodiac_confidence") != "provisional" for item in classical_states):
        findings.append("zodiac_confidence_not_provisional")
    provenance = facts["chart_facts"].get("provenance", {})
    if provenance.get("placements") != "user_declared_unrecomputed" or provenance.get("aspect_claims") != "user_declared_sector_validated":
        findings.append("input_provenance_not_isolated")
    candidates = facts["chart_facts"].get("rulership_candidates", {})
    if len(candidates.get("houses", [])) != 12 or len(candidates.get("topics", {})) != 7:
        findings.append("rulership_candidate_coverage_incomplete")
    if any(item.get("status") != "provisional_sign_only" for item in candidates.get("houses", [])):
        findings.append("missing_degree_candidate_status_not_provisional")
    if candidates.get("sect_confidence") != "low" or candidates.get("sect_source") != "inferred_from_sun_below_horizon":
        findings.append("rulership_candidate_sect_confidence_not_propagated")
    if not any(item.get("status") == "competing_candidates" for item in candidates.get("topics", {}).values()):
        findings.append("rulership_candidate_conflict_summary_empty")
    if provenance.get("rulership_candidates") != "computed_from_declared_cusp_signs_and_locked_dignity_versions":
        findings.append("rulership_candidate_provenance_missing")
    gates = facts.get("sensitive_topic_gates", {})
    if gates.get("creation_children") != "G2_context_only_no_reproductive_outcome" or gates.get("pressure_risk") != "G1_no_medical_or_mortality_claim":
        findings.append("sensitive_topic_gate_missing")
    if facts["chart_facts"]["supplied_fly_in_conflicts"]:
        findings.append("unexpected_fly_in_conflict")
    if len(facts["chart_facts"]["supplied_fly_in_duplicates"]) != 1:
        findings.append("fly_in_duplicate_not_detected")
    if len(facts["chart_facts"]["supplied_reception_duplicates"]) != 2:
        findings.append("reception_duplicates_not_detected")
    if facts["chart_facts"]["supplied_aspect_duplicates"] or facts["chart_facts"]["supplied_aspect_reverse_duplicates"]:
        findings.append("unexpected_aspect_duplicate")
    reception_validation = facts["chart_facts"]["supplied_reception_validation"]
    if reception_validation["unsupported_domicile_claims"] or reception_validation["mutual_missing_reverse"]:
        findings.append("unexpected_reception_mismatch")
    if reception_validation.get("connection_status_counts", {}).get("no_aspect_claim") != 9 or len(reception_validation.get("connection_required_unmet", [])) != 9:
        findings.append("reception_connection_audit_regression")
    tampered = json.loads(json.dumps(payload, ensure_ascii=False))
    tampered["aspects"].append({"planet1": "月亮", "planet2": "太阳", "type": "合"})
    tampered_facts = build(tampered)
    if len(tampered_facts["chart_facts"]["supplied_aspect_reverse_duplicates"]) != 1:
        findings.append("reverse_aspect_duplicate_regression")
    bad_reception = json.loads(json.dumps(payload, ensure_ascii=False))
    bad_reception["receptions"].append({"type": "reception", "planet1": "月亮", "planet2": "金星", "house1": 5, "house2": 3})
    bad_reception_facts = build(bad_reception)
    if len(bad_reception_facts["chart_facts"]["supplied_reception_validation"]["unsupported_domicile_claims"]) != 1:
        findings.append("reception_direction_regression")
    chains = facts.get("responsibility_chains", {}).get("topics", {})
    if set(chains) != {"self_decision", "money_income", "shared_resources", "career_public_role", "relationship_family", "creation_children", "pressure_risk"}:
        findings.append("responsibility_topic_coverage_incomplete")
    if "money_income" in chains and not chains["money_income"].get("path"):
        findings.append("money_responsibility_chain_empty")
    if not facts.get("responsibility_chains", {}).get("cross_topic_shared_rulers"):
        findings.append("cross_topic_dedup_index_empty")
    rendered = render(facts)
    if "责任链与共享证据审计" not in rendered or "跨主题共享宫主" not in rendered or "高风险主题输出闸门" not in rendered or "尊贵主宰候选审计" not in rendered or "主题级主宰分歧" not in rendered:
        findings.append("rendered_report_missing_dedup_audit")
    for marker in ("不可判断项", "未来时间技术", "医疗", "事件日期", "交付状态"):
        if marker not in rendered:
            findings.append(f"rendered_report_missing_boundary:{marker}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chart", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.chart.read_text(encoding="utf-8-sig"))
    findings = check(payload)
    if findings:
        print("FAIL")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("PASS user chart input integrity: 15 placements, 43 aspects, 9 reception claims, HOLD on missing contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
