#!/usr/bin/env python3
"""Build a fail-closed, machine-readable natal release manifest."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _read(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"cannot decode JSON: {path}")


def build_manifest(
    facts: dict[str, Any],
    score: dict[str, Any] | None = None,
    source_audit: dict[str, Any] | None = None,
    dictionary_audit: dict[str, Any] | None = None,
    score_diff: dict[str, Any] | None = None,
    cards: dict[str, Any] | None = None,
    research_assets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate = facts.get("release_gate", {})
    blockers = list(gate.get("blockers", []))
    warnings = list(gate.get("warnings", []))
    if source_audit and source_audit.get("version_gate") == "hold":
        blockers.append("source_version_gate_hold")
    if dictionary_audit and dictionary_audit.get("status") not in ("pass", "not_evaluated"):
        blockers.append("sensitive_dictionary_audit_failed")
    observation_dictionary_version = facts.get("observation_validation", {}).get("sensitive_dictionary_version")
    audit_dictionary_version = dictionary_audit.get("current_version") if dictionary_audit else None
    if dictionary_audit and observation_dictionary_version and audit_dictionary_version and observation_dictionary_version != audit_dictionary_version:
        blockers.append("sensitive_dictionary_version_mismatch")
    if score_diff:
        if score_diff.get("status") != "pass":
            blockers.append("score_diff_failed")
        warnings.extend(f"score_diff:{item}" for item in score_diff.get("findings", []))
    if research_assets and research_assets.get("status") != "pass":
        blockers.append("research_assets_failed")
    if research_assets and research_assets.get("pending_card_count", 0):
        warnings.append(f"research_assets_pending:{research_assets.get('pending_card_count')}")
    if source_audit and research_assets:
        source_fingerprint = source_audit.get("registry_fingerprint")
        research_fingerprint = research_assets.get("registry_fingerprint")
        if source_fingerprint and research_fingerprint and source_fingerprint != research_fingerprint:
            blockers.append("research_source_registry_fingerprint_mismatch")
    if score and score.get("rule_version_gate") == "hold":
        blockers.append("score_version_gate_hold")
    fact_lock = facts.get("metadata", {}).get("rule_version_lock")
    score_lock = score.get("rule_version_lock") if score else None
    if score and fact_lock and score_lock and fact_lock != score_lock:
        blockers.append("score_rule_version_mismatch")
    if score is not None and cards is not None:
        score_topics = {item.get("topic") for item in score.get("cards", [])}
        card_topics = {item.get("topic") for item in cards.get("cards", [])}
        if score_topics != card_topics:
            blockers.append("score_cards_topic_mismatch")
    if score is not None and source_audit is not None:
        source_conflicts = source_audit.get("conflict_status")
        score_conflicts = score.get("source_conflict_status")
        if source_conflicts is not None and score_conflicts is not None and source_conflicts != score_conflicts:
            blockers.append("source_score_conflict_mismatch")
    if "observation_validation" not in facts:
        blockers.append("observation_validation_missing")
    if gate.get("publishable") and not gate.get("fact_inventory_ready"):
        blockers.append("release_gate_fact_inventory_inconsistent")
    if gate.get("publishable") and not gate.get("natal_interpretation_ready"):
        blockers.append("release_gate_interpretation_inconsistent")
    unique_blockers = sorted(set(blockers))
    observation_validation = facts.get("observation_validation", {})
    aspect_support_levels = Counter(item.get("support_level", "unknown") for item in facts.get("chart_facts", {}).get("aspect_validation", []))
    upgrade_profiles = (research_assets or {}).get("upgrade_profiles", {})
    upgrade_profile_counts: dict[str, int] = {}
    core_upgrade_profile_counts: dict[str, int] = {}
    for profile in upgrade_profiles.values():
        eligibility = profile.get("eligibility", "unknown")
        upgrade_profile_counts[eligibility] = upgrade_profile_counts.get(eligibility, 0) + 1
        core_eligibility = profile.get("core_rule_eligibility", "unknown")
        core_upgrade_profile_counts[core_eligibility] = core_upgrade_profile_counts.get(core_eligibility, 0) + 1
    return {
        "schema_version": "RELEASE-0.1",
        "chart_id": facts.get("chart_id"),
        "decision": "publish" if gate.get("publishable") and not unique_blockers else "hold",
        "publishable": bool(gate.get("publishable")) and not unique_blockers,
        "artifact_status": {
            "facts": "present",
            "score": "present" if score is not None else "absent",
            "source_audit": "present" if source_audit is not None else "absent",
            "dictionary_audit": dictionary_audit.get("status", "unknown") if dictionary_audit else "absent",
            "score_diff": score_diff.get("status", "unknown") if score_diff else "absent",
            "research_assets": research_assets.get("status", "unknown") if research_assets else "absent",
        },
        "chart_contract": {
            "zodiac": facts.get("metadata", {}).get("zodiac"),
            "house_system": facts.get("metadata", {}).get("house_system"),
            "birth_time_present": bool(str(facts.get("metadata", {}).get("birth_time", "")).strip()),
            "degrees_available": bool(facts.get("metadata", {}).get("degrees_available")),
            "sect": facts.get("metadata", {}).get("sect"),
            "sect_source": facts.get("metadata", {}).get("sect_source"),
            "sect_confidence": facts.get("metadata", {}).get("sect_confidence", "none"),
            "missing_contract_fields": list(facts.get("metadata", {}).get("missing_contract_fields", [])),
            "rule_version_lock": facts.get("metadata", {}).get("rule_version_lock", {}),
            "ascendant_boundary_risk": facts.get("metadata", {}).get("ascendant_boundary_risk"),
        },
        "chart_layers": {
            "provenance": facts.get("chart_facts", {}).get("provenance", {}),
            "sensitive_topic_gates": facts.get("sensitive_topic_gates", {}),
            "fact_inventory_ready": bool(facts.get("release_gate", {}).get("fact_inventory_ready")),
            "natal_interpretation_ready": bool(facts.get("release_gate", {}).get("natal_interpretation_ready")),
            "rulership_chain_count": len(facts.get("chart_facts", {}).get("rulership_fly_ins", [])),
            "aspect_validation_count": len(facts.get("chart_facts", {}).get("aspect_validation", [])),
            "classical_core_aspect_count": sum(1 for item in facts.get("chart_facts", {}).get("aspect_validation", []) if item.get("evidence_layer") == "classical_core"),
            "auxiliary_aspect_count": sum(1 for item in facts.get("chart_facts", {}).get("aspect_validation", []) if item.get("evidence_layer") == "auxiliary_context"),
            "aspect_support_levels": dict(sorted(aspect_support_levels.items())),
            "aspect_delivery_status_counts": dict(sorted(Counter(item.get("delivery_status", "unknown") for item in facts.get("chart_facts", {}).get("aspect_validation", [])).items())),
            "aspect_character_counts": dict(sorted(Counter(item.get("aspect_character", "unknown") for item in facts.get("chart_facts", {}).get("aspect_validation", [])).items())),
            "reception_pair_count": len(facts.get("chart_facts", {}).get("mutual_domicile_pairs", [])),
            "reception_connection_status_counts": facts.get("chart_facts", {}).get("supplied_reception_validation", {}).get("connection_status_counts", {}),
            "reception_connection_required_unmet_count": len(facts.get("chart_facts", {}).get("supplied_reception_validation", {}).get("connection_required_unmet", [])),
            "planetary_state_status": facts.get("chart_facts", {}).get("planetary_state", {}).get("status", "unknown"),
            "topic_count": len(facts.get("topic_coverage", {})),
            "responsibility_topic_count": len(facts.get("responsibility_chains", {}).get("topics", {})),
            "cross_topic_shared_ruler_count": len(facts.get("responsibility_chains", {}).get("cross_topic_shared_rulers", [])),
            "rulership_candidate_house_count": len(facts.get("chart_facts", {}).get("rulership_candidates", {}).get("houses", [])),
            "rulership_candidate_topic_count": len(facts.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {})),
            "rulership_candidate_provisional_house_count": sum(1 for item in facts.get("chart_facts", {}).get("rulership_candidates", {}).get("houses", []) if item.get("status") != "resolved"),
            "rulership_candidate_sect_confidence": facts.get("chart_facts", {}).get("rulership_candidates", {}).get("sect_confidence", "unknown"),
            "rulership_candidate_competing_topic_count": sum(1 for item in facts.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {}).values() if item.get("status") == "competing_candidates"),
        },
        "score_diff": {
            "changed_topics": list(score_diff.get("changed_topics", [])) if score_diff else [],
            "findings": list(score_diff.get("findings", [])) if score_diff else [],
        },
        "observations": {
            "status": observation_validation.get("status", "not_collected"),
            "count": observation_validation.get("count", 0),
            "active_count": observation_validation.get("active_count", 0),
            "tombstone_count": observation_validation.get("tombstone_count", 0),
            "findings": list(observation_validation.get("findings", [])),
            "sensitive_dictionary_version": observation_validation.get("sensitive_dictionary_version", "not_recorded"),
        },
        "research_assets": {
            "status": research_assets.get("status", "not_evaluated") if research_assets else "absent",
            "card_count": research_assets.get("card_count", 0) if research_assets else 0,
            "pending_card_count": research_assets.get("pending_card_count", 0) if research_assets else 0,
            "pending_priority_counts": research_assets.get("pending_priority_counts", {}) if research_assets else {},
            "pending_blocker_counts": research_assets.get("pending_blocker_counts", {}) if research_assets else {},
            "pending_stop_condition_count": sum(len(item.get("upgrade_stop_conditions", [])) for item in research_assets.get("pending_queue", [])) if research_assets else 0,
            "pending_queue_quality": research_assets.get("pending_queue_quality", {}) if research_assets else {},
            "capability_status": research_assets.get("capability_status", {}) if research_assets else {},
            "upgrade_profile_counts": upgrade_profile_counts,
            "core_upgrade_profile_counts": core_upgrade_profile_counts,
        },
        "blockers": unique_blockers,
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a natal release manifest")
    parser.add_argument("facts", type=Path)
    parser.add_argument("--score", type=Path)
    parser.add_argument("--source-audit", type=Path)
    parser.add_argument("--dictionary-audit", type=Path)
    parser.add_argument("--score-diff", type=Path)
    parser.add_argument("--cards", type=Path)
    parser.add_argument("--research-assets", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = build_manifest(_read(args.facts) or {}, _read(args.score), _read(args.source_audit), _read(args.dictionary_audit), _read(args.score_diff), _read(args.cards), _read(args.research_assets))
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if manifest["publishable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
