#!/usr/bin/env python3
"""Check quote-card provenance against the source registry.

This checker validates the research layer only; it never upgrades a card or
source. Registered-but-unverified sources remain explicitly non-upgradeable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CARD_RE = re.compile(r"^###\s+(QI-[0-9]+)", re.MULTILINE)
SOURCE_RE = re.compile(r"\bR[0-9]{2}\b")
ALLOWED_CARD_STATUSES = {"draft", "verified", "auxiliary", "retired"}
REQUIRED_CARD_FIELDS = ("paraphrase", "operational_rule", "conditions", "counter_test", "output_guardrail")
TAG_ANCHORS = {
    "@chart_validation": ("Chart Facts", "度数", "相位"),
    "@sect": ("sect", "日夜"),
    "@reception": ("接纳", "reception"),
    "@aspects": ("相位", "aspect"),
    "@terms": ("terms", "界"),
    "@lots": ("Lots", "福点", "灵魂点"),
    "@sensitive": ("G1", "G2", "G3", "敏感"),
    "@source_criticism": ("传承", "来源", "译本", "source"),
    "@methodology": ("现代", "modern", "方法", "边界"),
    "@dignity": ("尊贵", "dignity"),
    "@triplicity": ("triplicity", "三分"),
}
TAG_SCRIPT_LINKS = {
    "@chart_validation": ("build_natal_facts.py", "validate_chart_facts.py"),
    "@sect": ("planetary_state.py",),
    "@reception": ("validate_chart_facts.py",),
    "@aspects": ("validate_chart_facts.py",),
    "@terms": ("planetary_state.py",),
    "@lots": ("build_natal_facts.py",),
    "@sensitive": ("validate_observations.py",),
    "@source_criticism": ("check_source_registry.py",),
    "@methodology": ("check_research_loop.py",),
    "@dignity": ("planetary_state.py",),
    "@triplicity": ("planetary_state.py",),
    "@planetary_state": ("planetary_state.py",),
    "@wealth": ("build_modular_interpretation.py",),
}
TAG_CAPABILITY_STATUS = {
    "@antiscia": "auxiliary_candidate",
    "@hidden_technique": "auxiliary_candidate",
    "@formula_control": "auxiliary_candidate",
    "@visibility": "auxiliary_candidate",
    "@orb": "auxiliary_candidate",
    "@delivery": "auxiliary_candidate",
    "@house_rulership": "governance_only",
    "@timing": "timing_extension_only",
    "@hypothesis": "governance_only",
    "@medical_history": "sensitive_context_only",
    "@source_conflict": "governance_only",
    "@version_control": "governance_only",
    "@anti_overfit": "governance_only",
    "@ethics": "governance_only",
    "@history": "context_only",
    "@evidence": "governance_only",
    "@planetary_state": "implemented",
    "@wealth": "implemented",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _card_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(CARD_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.start():end]))
    return blocks


def check(registry: dict[str, Any], cards_text: str) -> dict[str, Any]:
    sources = registry.get("sources", {})
    findings: list[str] = []
    warnings: list[str] = []
    card_ids: set[str] = set()
    referenced_sources: set[str] = set()
    script_links: dict[str, list[str]] = {}
    capability_status: dict[str, str] = {}
    card_fingerprints: dict[str, str] = {}
    upgrade_profiles: dict[str, dict[str, Any]] = {}
    card_count = 0
    for card_id, block in _card_blocks(cards_text):
        card_count += 1
        if card_id in card_ids:
            findings.append(f"duplicate card id: {card_id}")
        card_ids.add(card_id)
        card_fingerprints[card_id] = hashlib.sha256(block.encode("utf-8")).hexdigest()
        source_match = re.search(r"^source_id:\s*(.+)$", block, re.MULTILINE)
        if not source_match:
            findings.append(f"{card_id}: missing source_id")
            continue
        source_ids = sorted(set(SOURCE_RE.findall(source_match.group(1))))
        if not source_ids:
            findings.append(f"{card_id}: source_id has no registry ID")
        for source_id in source_ids:
            referenced_sources.add(source_id)
            if source_id not in sources:
                findings.append(f"{card_id}: unknown source {source_id}")
        status_match = re.search(r"^status:\s*(\S+)", block, re.MULTILINE)
        status = status_match.group(1) if status_match else ""
        if status not in ALLOWED_CARD_STATUSES:
            findings.append(f"{card_id}: invalid status {status or 'missing'}")
        if status in {"draft", "auxiliary"}:
            warnings.append(f"{card_id}: non-upgradeable card status {status}")
        for field in REQUIRED_CARD_FIELDS:
            if not re.search(rf"^{re.escape(field)}:\s*\S", block, re.MULTILINE):
                findings.append(f"{card_id}: missing required research field {field}")
        tags_match = re.search(r"^tags:\s*\[([^]]*)\]", block, re.MULTILINE)
        rule_match = re.search(r"^operational_rule:\s*(.+)$", block, re.MULTILINE)
        if tags_match and rule_match:
            operational_rule = rule_match.group(1)
            tags = [tag.strip() for tag in tags_match.group(1).split(",")]
            if status == "verified":
                overclaim_tags = [tag for tag in tags if TAG_CAPABILITY_STATUS.get(tag) in {"auxiliary_candidate", "timing_extension_only"}]
                if overclaim_tags:
                    findings.append(f"{card_id}: verified status overclaims capability tags {overclaim_tags}")
            for tag in tags:
                anchors = TAG_ANCHORS.get(tag)
                if anchors and not any(anchor in operational_rule for anchor in anchors):
                    findings.append(f"{card_id}: operational_rule missing anchor for {tag}")
                linked_scripts = TAG_SCRIPT_LINKS.get(tag)
                if linked_scripts:
                    script_links.setdefault(card_id, []).extend(linked_scripts)
                    for script_name in linked_scripts:
                        if not (Path(__file__).resolve().parent / script_name).exists():
                            findings.append(f"{card_id}: linked executor missing {script_name}")
                elif tag.startswith("@"):
                    warnings.append(f"{card_id}: no dedicated executor mapping for {tag}")
                if tag.startswith("@"):
                    capability_status[tag] = "implemented" if linked_scripts else TAG_CAPABILITY_STATUS.get(tag, "unmapped")
            reasons: list[str] = []
            if status != "verified":
                reasons.append(f"card_status:{status or 'missing'}")
            source_statuses = {source_id: sources.get(source_id, {}).get("status", "unknown") for source_id in source_ids}
            limited_sources = sorted(source_id for source_id, source_status in source_statuses.items() if source_status != "verified")
            if limited_sources:
                reasons.append(f"source_status_limited:{','.join(limited_sources)}")
            candidate_tags = sorted(tag for tag in tags if TAG_CAPABILITY_STATUS.get(tag) in {"auxiliary_candidate", "timing_extension_only"})
            if candidate_tags:
                reasons.append(f"capability_limited:{','.join(candidate_tags)}")
            counter_match = re.search(r"^counter_test:\s*(.+)$", block, re.MULTILINE)
            counter_text = counter_match.group(1).strip() if counter_match else ""
            counter_test_present = len(counter_text) >= 12 and any(marker in counter_text for marker in ("不能", "不", "若", "无", "限制", "反", "可能", "需要"))
            if not counter_test_present:
                reasons.append("counter_test_insufficient")
            locator_match = re.search(r"^locator:\s*(.+)$", block, re.MULTILINE)
            locator_text = locator_match.group(1).strip() if locator_match else ""
            locator_precise = bool(locator_text) and not any(marker in locator_text.lower() for marker in ("pending", "待", "lead", "待逐条复核"))
            if not locator_precise:
                reasons.append("locator_not_precise")
            eligibility = "blocked" if status in {"draft", "retired", ""} else "limited" if reasons else "eligible_candidate"
            core_eligibility = "eligible_candidate" if eligibility == "eligible_candidate" and len(source_ids) >= 2 else "blocked_independent_source" if eligibility == "eligible_candidate" else eligibility
            upgrade_profiles[card_id] = {
                "eligibility": eligibility,
                "core_rule_eligibility": core_eligibility,
                "counter_test_present": counter_test_present,
                "locator_quality": "precise" if locator_precise else "needs_locator_review",
                "reasons": reasons,
                "source_statuses": source_statuses,
            }

    pending = re.findall(r"^\|\s*(QI-[0-9]+)\s*\|\s*([^|]+)\|", cards_text, re.MULTILINE)
    pending_count = 0
    pending_queue: list[dict[str, Any]] = []
    for card_id, source_cell in pending:
        if card_id in card_ids:
            continue
        pending_count += 1
        source_ids = sorted(set(SOURCE_RE.findall(source_cell)))
        for source_id in source_ids:
            referenced_sources.add(source_id)
            if source_id not in sources:
                findings.append(f"{card_id}: pending card references unknown source {source_id}")
        warnings.append(f"{card_id}: pending card not yet fully extracted")
        blocking_reasons: list[str] = []
        for source_id in source_ids:
            source = sources.get(source_id, {})
            fulltext_status = str(source.get("fulltext_status", "unknown"))
            abstract_status = str(source.get("abstract_status", "unknown"))
            if fulltext_status not in {"retrieved", "open_access_fulltext"}:
                blocking_reasons.append(f"{source_id}:fulltext_not_available_or_not_retrieved")
            if abstract_status in {"not_available_in_crossref_response", "unknown"}:
                blocking_reasons.append(f"{source_id}:abstract_not_available")
        if any(source_id in {"R13", "R14", "R15"} for source_id in source_ids):
            priority, priority_reason = "P0", "anti_overfit_and_methodology_boundary"
        elif any(source_id in {"R09", "R10", "R11", "R12"} for source_id in source_ids):
            priority, priority_reason = "P1", "historical_context_and_primary_locator"
        else:
            priority, priority_reason = "P2", "contextual_follow_up"
        alternative_paths = sorted({path for source_id in source_ids for path in sources.get(source_id, {}).get("alternative_paths", [])})
        upgrade_stop_conditions = sorted({condition for source_id in source_ids for condition in [sources.get(source_id, {}).get("upgrade_stop_condition")] if condition})
        if not alternative_paths:
            findings.append(f"{card_id}: pending card missing alternative research path")
        if not upgrade_stop_conditions:
            findings.append(f"{card_id}: pending card missing upgrade stop condition")
        pending_queue.append({
            "card_id": card_id,
            "source_ids": source_ids,
            "source_works": [sources[source_id].get("work") for source_id in source_ids if source_id in sources],
            "status": "draft",
            "priority": priority,
            "priority_reason": priority_reason,
            "blocking_reasons": blocking_reasons,
            "completion_gate": "blocked_source_access" if blocking_reasons else "awaiting_extraction",
            "alternative_paths": alternative_paths,
            "upgrade_stop_conditions": upgrade_stop_conditions,
            "required_actions": ["full_text_or_primary_locator", "translator/edition verification", "counter-test extraction", "upgrade decision"],
        })

    return {
        "status": "pass" if not findings else "fail",
        "card_count": card_count,
        "complete_card_count": max(0, card_count - sum(1 for item in findings if ": missing required research field " in item)),
        "pending_card_count": pending_count,
        "pending_queue": pending_queue,
        "pending_priority_counts": {priority: sum(1 for item in pending_queue if item.get("priority") == priority) for priority in ("P0", "P1", "P2")},
        "pending_blocker_counts": {
            "blocked_source_access": sum(1 for item in pending_queue if item.get("completion_gate") == "blocked_source_access"),
            "awaiting_extraction": sum(1 for item in pending_queue if item.get("completion_gate") == "awaiting_extraction"),
        },
        "pending_stop_condition_count": sum(len(item.get("upgrade_stop_conditions", [])) for item in pending_queue),
        "pending_queue_quality": {
            "all_have_alternative_paths": all(bool(item.get("alternative_paths")) for item in pending_queue),
            "all_have_upgrade_stop_conditions": all(bool(item.get("upgrade_stop_conditions")) for item in pending_queue),
        },
        "referenced_sources": sorted(referenced_sources),
        "registered_source_count": len(sources),
        "registry_fingerprint": hashlib.sha256(json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "script_links": {key: sorted(set(value)) for key, value in sorted(script_links.items())},
        "capability_status": dict(sorted(capability_status.items())),
        "upgrade_profiles": dict(sorted(upgrade_profiles.items())),
        "card_fingerprints": dict(sorted(card_fingerprints.items())),
        "warnings": warnings,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check research-card provenance")
    parser.add_argument("registry", type=Path)
    parser.add_argument("cards", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        sample = "### QI-001\nsource_id: R01\nparaphrase: sample\noperational_rule: sample\nconditions: sample\ncounter_test: sample\noutput_guardrail: sample\nstatus: verified\n"
        result = check({"sources": {"R01": {"status": "verified"}}}, sample)
        if result["status"] != "pass":
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        changed = check({"sources": {"R01": {"status": "verified"}}}, sample.replace("conditions: sample", "conditions: changed"))
        if changed["status"] != "pass" or changed["card_fingerprints"] == result["card_fingerprints"]:
            print("FAIL fingerprint did not change with card content")
            return 1
        registry_changed = check({"sources": {"R01": {"status": "registered"}}}, sample)
        if registry_changed["status"] != "pass" or registry_changed["registry_fingerprint"] == result["registry_fingerprint"]:
            print("FAIL registry fingerprint did not change with source status")
            return 1
        pending_sample = "| QI-002 | R01 |\n"
        pending_result = check({"sources": {"R01": {"status": "registered", "upgrade_stop_condition": "locator required"}}}, pending_sample)
        if pending_result["pending_stop_condition_count"] != 1:
            print("FAIL pending stop-condition count missing")
            return 1
        missing_controls = check({"sources": {"R01": {"status": "registered"}}}, pending_sample)
        if missing_controls["status"] != "fail" or not any("missing alternative" in finding for finding in missing_controls["findings"]):
            print("FAIL pending queue control gap was not blocked")
            return 1
        bad = check({"sources": {"R01": {"status": "verified"}}}, sample.replace("R01", "R99"))
        if bad["status"] != "fail":
            print(json.dumps(bad, ensure_ascii=False, indent=2))
            return 1
        print("PASS research-assets self-test")
        return 0
    result = check(_read_json(args.registry), args.cards.read_text(encoding="utf-8"))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
