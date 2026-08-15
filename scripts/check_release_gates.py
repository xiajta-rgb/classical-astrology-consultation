#!/usr/bin/env python3
"""Adversarial regression tests for the natal release gates.

The important negative case is deliberate: a chart may declare every rule
version, yet it must remain HOLD when birth metadata, house system, or degrees
are missing.  This prevents a downstream inference layer from treating a
locked rule table as a substitute for chart-specific facts.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

try:
    from scripts.build_hypothesis_cards import build as build_cards
    from scripts.build_natal_facts import build as build_facts
    from scripts.render_natal_report import compare_scores, render as render_report
    from scripts.score_hypothesis_cards import score
    from scripts.compare_score_outputs import compare as compare_score_outputs
    from scripts.build_release_manifest import build_manifest
    from scripts.validate_observations import _load_dictionary, detect_sensitive_markers
except ModuleNotFoundError:  # direct execution from the scripts directory
    from build_hypothesis_cards import build as build_cards
    from build_natal_facts import build as build_facts
    from render_natal_report import compare_scores, render as render_report
    from score_hypothesis_cards import score
    from compare_score_outputs import compare as compare_score_outputs
    from build_release_manifest import build_manifest
    from validate_observations import _load_dictionary, detect_sensitive_markers


REQUIRED_LOCK = {
    "terms": True,
    "triplicity": True,
    "faces": True,
    "reception": True,
    "aspect": True,
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _locked_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rule_versions"] = {
        "terms": "egyptian",
        "triplicity": "dorotheus_style_three_rulers",
        "faces": "chaldean",
        "reception": "direction_plus_connection_required",
        "aspect": "application_separation_required",
    }
    return payload


def run(fixture: Path) -> dict[str, Any]:
    sensitive_cases_path = Path(__file__).resolve().parents[1] / "references" / "fixtures" / "sensitive-observation-cases.json"
    sensitive_cases = json.loads(sensitive_cases_path.read_text(encoding="utf-8"))
    for case in sensitive_cases.get("cases", []):
        categories = {hit.split(":", 1)[0] for hit in detect_sensitive_markers(case["statement"])}
        expected = case["expected"]
        _assert((not categories) if expected == "none" else expected in categories, f"sensitive case mismatch: {case['id']}")
    fallback_version, _, fallback_status, fallback_audit = _load_dictionary(Path("__missing_sensitive_dictionary__.json"))
    _assert(fallback_status == "fallback" and fallback_version == "SENSITIVE-BUILTIN-FALLBACK" and not fallback_audit["changed_categories"], "missing dictionary did not fail closed")
    baseline = _locked_payload(fixture)
    baseline_facts = build_facts(baseline)
    _assert(baseline_facts["release_gate"]["publishable"], "locked baseline must publish")
    _assert(baseline_facts["metadata"]["rule_version_lock"] == REQUIRED_LOCK, "baseline lock mismatch")

    cases: list[tuple[str, dict[str, Any], str]] = []
    missing_time = copy.deepcopy(baseline)
    missing_time["birth_time"] = ""
    cases.append(("missing_birth_time", missing_time, "chart_contract_incomplete"))
    missing_house_system = copy.deepcopy(baseline)
    missing_house_system["house_system"] = "unknown"
    cases.append(("missing_house_system", missing_house_system, "chart_contract_incomplete"))
    missing_degrees = copy.deepcopy(baseline)
    for item in missing_degrees["placements"].values():
        item.pop("degree", None)
    cases.append(("missing_planetary_degrees", missing_degrees, "chart_contract_incomplete"))
    unlocked = copy.deepcopy(baseline)
    unlocked["rule_versions"].pop("terms")
    cases.append(("unlocked_terms", unlocked, "rule_versions_unlocked"))

    findings = []
    for name, payload, expected_blocker in cases:
        facts = build_facts(payload)
        gate = facts["release_gate"]
        _assert(not gate["publishable"], f"{name} unexpectedly publishable")
        _assert(expected_blocker in gate["blockers"], f"{name} missing blocker {expected_blocker}")
        cards = build_cards(facts)
        _assert(cards["status"] == "hold", f"{name} produced candidate cards")
        _assert(not cards["cards"], f"{name} produced non-empty cards")
        report = render_report(facts, {"version_gate": "publish", "conflict_status": []})
        _assert("BLOCKED" in report, f"{name} report lacks paragraph BLOCKED labels")
        findings.append(name)

    source_hold = {"version_gate": "hold", "version_gate_blockers": ["terms_version"], "conflict_status": []}
    cards = build_cards(baseline_facts, source_hold)
    _assert(cards["status"] == "hold", "source HOLD was not propagated to cards")

    scoring_payload = {
        "status": "candidate",
        "rule_version_lock": REQUIRED_LOCK,
        "cards": [{
            "topic": "independence_test",
            "Counter_test": ["结构性资源限制需复核"],
            "evidence_ids": ["e1", "e2"],
            "evidence_items": [
                {"id": "e1", "source_ids": ["R01"], "source_cluster": "classical"},
                {"id": "e2", "source_ids": ["R19"], "source_cluster": "reception"},
            ],
        }],
    }
    eligible_registry = {
        "sources": {
            "R25": {"status": "verified", "layer": "secondary_technical", "limits": ""},
            "R26": {"status": "verified", "layer": "secondary_technical", "limits": ""},
        },
        "conflict_clusters": [],
    }
    scoring_payload["cards"][0]["evidence_items"][0]["source_ids"] = ["R25"]
    scoring_payload["cards"][0]["evidence_items"][1]["source_ids"] = ["R26"]
    locked_score = score(scoring_payload, eligible_registry, {"metadata": {"rule_version_lock": REQUIRED_LOCK}})
    _assert(locked_score["cards"][0]["natural_grade_cap"] == "A", "independent locked evidence should reach natural A cap")
    _assert(locked_score["cards"][0]["grade_cap"] == "A", "locked evidence should retain A cap")
    _assert("structural_counter_test_present" in locked_score["cards"][0]["publication_reasons"], "structural counter-test was not classified")
    unlocked_score = score(scoring_payload, eligible_registry, {"metadata": {"rule_version_lock": {**REQUIRED_LOCK, "terms": False}}})
    _assert(unlocked_score["cards"][0]["natural_grade_cap"] == "A", "negative scoring fixture lost natural cap")
    _assert(unlocked_score["cards"][0]["grade_cap"] == "B", "unlocked evidence escaped B cap")
    _assert("version_gate_hold" in unlocked_score["cards"][0]["publication_reasons"], "unlocked score lacks version publication reason")
    limited_registry = copy.deepcopy(eligible_registry)
    limited_registry["sources"]["R25"]["status"] = "auxiliary"
    limited_score = score(scoring_payload, limited_registry, {"metadata": {"rule_version_lock": REQUIRED_LOCK}})
    _assert(limited_score["cards"][0]["source_upgrade_eligibility"] == "limited", "auxiliary source was not marked limited")
    _assert(limited_score["cards"][0]["grade_cap"] == "B", "auxiliary source escaped B cap")
    _assert("source_qualification_limited" in limited_score["cards"][0]["publication_reasons"], "limited score lacks source publication reason")
    registered_registry = copy.deepcopy(eligible_registry)
    registered_registry["sources"]["R25"]["status"] = "registered"
    registered_score = score(scoring_payload, registered_registry, {"metadata": {"rule_version_lock": REQUIRED_LOCK}})
    _assert(registered_score["cards"][0]["source_upgrade_eligibility"] == "limited" and registered_score["cards"][0]["grade_cap"] == "B", "registered source escaped upgrade cap")
    tampered_score = copy.deepcopy(limited_score)
    tampered_score["cards"][0]["grade_cap"] = "A"
    _assert(compare_scores(tampered_score, limited_score), "tampered grade cap was not detected")

    benign_isolation = copy.deepcopy(baseline)
    benign_isolation["observations"] = {"career_public_role": [{
        "id": "OBS-ISOLATION-001",
        "record_version": "OBS-ISOLATION-001.v1",
        "state": "active",
        "statement": "项目周期变长，交付边界需要重新划分",
        "source_type": "user_report",
        "source_locator": "consultation-intake-isolation",
        "relation": "neutral",
        "confidence": "reported",
    }]}
    benign_isolation_facts = build_facts(benign_isolation)
    _assert(benign_isolation_facts["release_gate"]["publishable"], "benign observation blocked chart layer")
    baseline_score = score(build_cards(baseline_facts), facts=baseline_facts)
    benign_isolation_score = score(build_cards(benign_isolation_facts), facts=benign_isolation_facts)
    baseline_caps = [(item["topic"], item["natural_grade_cap"], item["grade_cap"]) for item in baseline_score["cards"]]
    isolation_caps = [(item["topic"], item["natural_grade_cap"], item["grade_cap"]) for item in benign_isolation_score["cards"]]
    _assert(baseline_caps == isolation_caps, "observation dictionary leaked into chart score caps")

    observed_payload = copy.deepcopy(baseline)
    observed_payload["observations"] = {
        "money_income": [{
            "id": "OBS-MONEY-001",
            "record_version": "OBS-MONEY-001.v1",
            "state": "active",
            "statement": "共同资金曾与个人收入发生实际争议",
            "source_type": "user_report",
            "source_locator": "consultation-intake-001",
            "period": "2024-2025",
            "relation": "contradicts_H1",
            "confidence": "reported",
        }]
    }
    observed_facts = build_facts(observed_payload)
    _assert(observed_facts["release_gate"]["publishable"], "valid observation should not block chart facts")
    observed_cards = build_cards(observed_facts)
    money_card = next(card for card in observed_cards["cards"] if card["topic"] == "money_income")
    _assert(money_card["observation_contract"]["status"] == "collected", "valid observation was not attached to topic card")
    observed_score = score(observed_cards, eligible_registry, observed_facts)
    money_score = next(card for card in observed_score["cards"] if card["topic"] == "money_income")
    _assert(money_score["observation_summary"]["competing_observation_ids"] == ["OBS-MONEY-001"], "competing observation was not preserved")
    _assert("observed_competing_evidence" in money_score["publication_reasons"], "competing observation reason missing")

    withdrawn_payload = copy.deepcopy(baseline)
    withdrawn_payload["observations"] = {"money_income": [{
        "id": "OBS-MONEY-WITHDRAWN",
        "record_version": "OBS-MONEY-WITHDRAWN.v1",
        "state": "withdrawn",
        "withdrawal_reason": "来源无法复核，撤回该记录",
    }]}
    withdrawn_facts = build_facts(withdrawn_payload)
    _assert(withdrawn_facts["release_gate"]["publishable"], "valid withdrawn tombstone blocked chart facts")
    withdrawn_cards = build_cards(withdrawn_facts)
    withdrawn_money = next(card for card in withdrawn_cards["cards"] if card["topic"] == "money_income")
    _assert(withdrawn_money["observation_contract"]["status"] == "withdrawn_only", "withdrawn observation remained active")
    _assert(not withdrawn_money["observation_contract"]["items"], "withdrawn observation entered active items")
    withdrawn_tombstone = withdrawn_facts["observations"]["money_income"][0]
    _assert("statement" not in withdrawn_tombstone and "source_locator" not in withdrawn_tombstone, "withdrawn raw fields were not removed")
    withdrawn_score = score(withdrawn_cards, facts=withdrawn_facts)
    withdrawn_money_score = next(card for card in withdrawn_score["cards"] if card["topic"] == "money_income")
    _assert("observation_tombstone_present" in withdrawn_money_score["publication_reasons"], "withdrawal reason was not surfaced")
    withdrawn_diff = compare_score_outputs(baseline_score, withdrawn_score)
    _assert(withdrawn_diff["status"] == "pass", "withdrawal score diff changed topic set")
    _assert(withdrawn_diff["changed_topics"] == ["money_income"], "withdrawal score diff escaped target topic")
    baseline_money_score = next(card for card in baseline_score["cards"] if card["topic"] == "money_income")
    _assert(baseline_money_score["natural_grade_cap"] == withdrawn_money_score["natural_grade_cap"], "withdrawal changed natural chart cap")
    _assert(baseline_money_score["grade_cap"] == withdrawn_money_score["grade_cap"], "withdrawal changed actual chart cap")
    withdrawn_manifest = build_manifest(withdrawn_facts, withdrawn_score, score_diff=withdrawn_diff)
    _assert(withdrawn_manifest["publishable"], "valid withdrawn score diff blocked release manifest")
    _assert(withdrawn_manifest["score_diff"]["changed_topics"] == ["money_income"], "release manifest lost score diff topic")
    polluted_diff = dict(withdrawn_diff)
    polluted_diff["status"] = "fail"
    polluted_diff["findings"] = ["topic_added_or_removed:career_public_role"]
    polluted_manifest = build_manifest(withdrawn_facts, withdrawn_score, score_diff=polluted_diff)
    _assert(not polluted_manifest["publishable"] and "score_diff_failed" in polluted_manifest["blockers"], "cross-topic score diff escaped release manifest")
    missing_observation_validation = copy.deepcopy(baseline_facts)
    missing_observation_validation.pop("observation_validation", None)
    missing_observation_manifest = build_manifest(missing_observation_validation)
    _assert(not missing_observation_manifest["publishable"] and "observation_validation_missing" in missing_observation_manifest["blockers"], "missing observation validation escaped release manifest")
    dictionary_mismatch_manifest = build_manifest(baseline_facts, dictionary_audit={"status": "pass", "current_version": "SENSITIVE-0.2"})
    _assert(not dictionary_mismatch_manifest["publishable"] and "sensitive_dictionary_version_mismatch" in dictionary_mismatch_manifest["blockers"], "dictionary version mismatch escaped release manifest")
    source_hold_manifest = build_manifest(baseline_facts, source_audit={"version_gate": "hold"})
    _assert(not source_hold_manifest["publishable"] and "source_version_gate_hold" in source_hold_manifest["blockers"], "source audit HOLD escaped release manifest")
    tampered_lock_score = copy.deepcopy(baseline_score)
    tampered_lock_score["rule_version_lock"] = {**REQUIRED_LOCK, "terms": False}
    tampered_lock_manifest = build_manifest(baseline_facts, tampered_lock_score)
    _assert(not tampered_lock_manifest["publishable"] and "score_rule_version_mismatch" in tampered_lock_manifest["blockers"], "score/facts rule lock mismatch escaped release manifest")
    tampered_cards = build_cards(baseline_facts)
    tampered_cards["cards"] = tampered_cards["cards"][:-1]
    tampered_cards_manifest = build_manifest(baseline_facts, baseline_score, cards=tampered_cards)
    _assert(not tampered_cards_manifest["publishable"] and "score_cards_topic_mismatch" in tampered_cards_manifest["blockers"], "score/cards topic mismatch escaped release manifest")
    conflict_mismatch_manifest = build_manifest(baseline_facts, baseline_score, source_audit={"version_gate": "publish", "conflict_status": [{"id": "CONFLICT-TAMPERED"}]})
    _assert(not conflict_mismatch_manifest["publishable"] and "source_score_conflict_mismatch" in conflict_mismatch_manifest["blockers"], "source/score conflict mismatch escaped release manifest")
    inconsistent_gate_facts = copy.deepcopy(baseline_facts)
    inconsistent_gate_facts["release_gate"]["publishable"] = True
    inconsistent_gate_facts["release_gate"]["natal_interpretation_ready"] = False
    inconsistent_gate_manifest = build_manifest(inconsistent_gate_facts)
    _assert(not inconsistent_gate_manifest["publishable"] and "release_gate_interpretation_inconsistent" in inconsistent_gate_manifest["blockers"], "inconsistent release gate escaped manifest")
    research_assets_fail_manifest = build_manifest(baseline_facts, research_assets={"status": "fail"})
    _assert(not research_assets_fail_manifest["publishable"] and "research_assets_failed" in research_assets_fail_manifest["blockers"], "research asset failure escaped release manifest")
    research_fingerprint_manifest = build_manifest(
        baseline_facts,
        source_audit={"registry_fingerprint": "registry-A"},
        research_assets={"status": "pass", "registry_fingerprint": "registry-B"},
    )
    _assert(not research_fingerprint_manifest["publishable"] and "research_source_registry_fingerprint_mismatch" in research_fingerprint_manifest["blockers"], "stale research registry fingerprint escaped release manifest")

    superseded_payload = copy.deepcopy(baseline)
    superseded_payload["observations"] = {"career_public_role": [
        {"id": "OBS-CAREER-001", "record_version": "OBS-CAREER-001.v1", "state": "superseded", "supersedes": "OBS-CAREER-001.v2", "withdrawal_reason": "由新版访谈替代"},
        {"id": "OBS-CAREER-001", "record_version": "OBS-CAREER-001.v2", "state": "active", "statement": "项目周期与交付边界重新定义", "source_type": "user_report", "source_locator": "consultation-intake-v2", "relation": "supports_H1", "confidence": "reported"},
    ]}
    superseded_facts = build_facts(superseded_payload)
    _assert(superseded_facts["release_gate"]["publishable"], "valid superseded/active chain blocked chart facts")
    superseded_cards = build_cards(superseded_facts)
    career_card = next(card for card in superseded_cards["cards"] if card["topic"] == "career_public_role")
    _assert(len(career_card["observation_contract"]["items"]) == 1 and career_card["observation_contract"]["items"][0]["record_version"].endswith("v2"), "superseded record was not excluded")

    multi_chain_payload = copy.deepcopy(baseline)
    multi_chain_payload["observations"] = {
        "career_public_role": [
            {"id": "OBS-MULTI-CAREER", "record_version": "OBS-MULTI-CAREER.v1", "state": "superseded", "supersedes": "OBS-MULTI-CAREER.v2", "withdrawal_reason": "新版替代"},
            {"id": "OBS-MULTI-CAREER", "record_version": "OBS-MULTI-CAREER.v2", "state": "active", "statement": "项目职责发生变化", "source_type": "user_report", "source_locator": "multi-career-v2", "relation": "supports_H1", "confidence": "reported"},
        ],
        "money_income": [
            {"id": "OBS-MULTI-MONEY", "record_version": "OBS-MULTI-MONEY.v1", "state": "withdrawn", "withdrawal_reason": "来源无法复核"},
            {"id": "OBS-MULTI-MONEY", "record_version": "OBS-MULTI-MONEY.v2", "state": "active", "statement": "共同资金与个人收入边界发生争议", "source_type": "user_report", "source_locator": "multi-money-v2", "relation": "contradicts_H1", "confidence": "reported"},
        ],
    }
    multi_chain_facts = build_facts(multi_chain_payload)
    _assert(multi_chain_facts["release_gate"]["publishable"], "valid multi-topic replacement chains blocked chart facts")
    multi_chain_cards = build_cards(multi_chain_facts)
    multi_chain_score = score(multi_chain_cards, facts=multi_chain_facts)
    multi_chain_diff = compare_score_outputs(baseline_score, multi_chain_score)
    _assert(multi_chain_diff["status"] == "pass", "multi-topic replacement diff changed topic set unexpectedly")
    _assert(multi_chain_diff["changed_topics"] == ["career_public_role", "money_income"], "multi-topic replacement diff lost a changed topic")
    multi_chain_manifest = build_manifest(multi_chain_facts, multi_chain_score, score_diff=multi_chain_diff)
    _assert(multi_chain_manifest["publishable"], "valid multi-topic replacement chains blocked manifest")
    multi_chain_report = render_report(multi_chain_facts, score_output=multi_chain_score, score_diff=multi_chain_diff)
    _assert("career_public_role" in multi_chain_report and "money_income" in multi_chain_report, "multi-topic score diff missing from report")
    reordered_multi_payload = copy.deepcopy(multi_chain_payload)
    reordered_multi_payload["observations"] = {
        "money_income": list(reversed(reordered_multi_payload["observations"]["money_income"])),
        "career_public_role": list(reversed(reordered_multi_payload["observations"]["career_public_role"])),
    }
    reordered_multi_facts = build_facts(reordered_multi_payload)
    reordered_multi_score = score(build_cards(reordered_multi_facts), facts=reordered_multi_facts)
    order_diff = compare_score_outputs(multi_chain_score, reordered_multi_score)
    _assert(order_diff["status"] == "pass" and not order_diff["changed_topics"], "observation input order changed score output")

    transitioned_payload = copy.deepcopy(multi_chain_payload)
    transitioned_payload["observations"]["career_public_role"] = [{
        "id": "OBS-MULTI-CAREER", "record_version": "OBS-MULTI-CAREER.v2", "state": "withdrawn", "withdrawal_reason": "回访后撤回，无法复核原陈述",
    }]
    transitioned_facts = build_facts(transitioned_payload)
    _assert(transitioned_facts["release_gate"]["publishable"], "active-to-withdrawn state transition blocked chart facts")
    transitioned_score = score(build_cards(transitioned_facts), facts=transitioned_facts)
    transition_diff = compare_score_outputs(multi_chain_score, transitioned_score)
    _assert(transition_diff["status"] == "pass" and transition_diff["changed_topics"] == ["career_public_role"], "state transition changed unrelated topics")
    transitioned_manifest = build_manifest(transitioned_facts, transitioned_score, score_diff=transition_diff)
    _assert(transitioned_manifest["publishable"], "valid state transition blocked release manifest")
    transitioned_report = render_report(transitioned_facts, score_output=transitioned_score, score_diff=transition_diff)
    _assert("回访后撤回" not in transitioned_report and "career_public_role" in transitioned_report, "withdrawn raw observation leaked into report")

    resurrection_payload = copy.deepcopy(baseline)
    resurrection_payload["observations"] = {"career_public_role": [
        {"id": "OBS-RESURRECT-001", "record_version": "OBS-RESURRECT-001.v2", "state": "withdrawn", "withdrawal_reason": "旧版本撤回"},
        {"id": "OBS-RESURRECT-001", "record_version": "OBS-RESURRECT-001.v2", "state": "active", "statement": "同版本重新激活", "source_type": "user_report", "source_locator": "resurrection", "relation": "supports_H1", "confidence": "reported"},
    ]}
    resurrection_facts = build_facts(resurrection_payload)
    _assert(not resurrection_facts["release_gate"]["publishable"], "withdrawn record was silently resurrected at same version")
    _assert("observation_contract_invalid" in resurrection_facts["release_gate"]["warnings"], "same-version resurrection warning missing")

    recovery_payload = copy.deepcopy(baseline)
    recovery_payload["observations"] = {"career_public_role": [
        {"id": "OBS-RECOVERY-001", "record_version": "OBS-RECOVERY-001.v2", "state": "withdrawn", "withdrawal_reason": "旧版本撤回"},
        {"id": "OBS-RECOVERY-001", "record_version": "OBS-RECOVERY-001.v3", "state": "active", "statement": "新版本恢复后的职业观察", "source_type": "user_report", "source_locator": "recovery-v3", "relation": "supports_H1", "confidence": "reported"},
    ]}
    recovery_facts = build_facts(recovery_payload)
    _assert(recovery_facts["release_gate"]["publishable"], "new-version recovery was unexpectedly blocked")
    recovery_score = score(build_cards(recovery_facts), facts=recovery_facts)
    recovery_diff = compare_score_outputs(baseline_score, recovery_score)
    _assert(recovery_diff["status"] == "pass" and recovery_diff["changed_topics"] == ["career_public_role"], "new-version recovery changed unrelated topics")
    recovery_manifest = build_manifest(recovery_facts, recovery_score, score_diff=recovery_diff)
    _assert(recovery_manifest["publishable"] and recovery_manifest["score_diff"]["changed_topics"] == ["career_public_role"], "recovery manifest mismatch")
    _assert(recovery_manifest["observations"]["active_count"] == 1 and recovery_manifest["observations"]["tombstone_count"] == 1, "recovery manifest observation counts mismatch")
    recovery_manifest_text = json.dumps(recovery_manifest, ensure_ascii=False)
    _assert("statement" not in recovery_manifest_text and "source_locator" not in recovery_manifest_text, "raw observation fields leaked into release manifest")

    withdrawal_bad = copy.deepcopy(baseline)
    withdrawal_bad["observations"] = {"money_income": [{"id": "OBS-BAD-WITHDRAWAL", "record_version": "OBS-BAD-WITHDRAWAL.v1", "state": "withdrawn"}]}
    withdrawal_bad_facts = build_facts(withdrawal_bad)
    _assert(not withdrawal_bad_facts["release_gate"]["publishable"], "withdrawn record without reason unexpectedly publishable")
    _assert("observation_contract_invalid" in withdrawal_bad_facts["release_gate"]["warnings"], "missing withdrawal reason warning missing")

    active_conflict = copy.deepcopy(baseline)
    active_conflict["observations"] = {"career_public_role": [
        {"id": "OBS-CONFLICT-001", "record_version": "OBS-CONFLICT-001.v1", "state": "active", "statement": "旧版本观察", "source_type": "user_report", "source_locator": "obs-v1", "relation": "supports_H1", "confidence": "reported"},
        {"id": "OBS-CONFLICT-001", "record_version": "OBS-CONFLICT-001.v2", "state": "active", "statement": "新版本观察", "source_type": "user_report", "source_locator": "obs-v2", "relation": "supports_H2", "confidence": "reported"},
    ]}
    active_conflict_facts = build_facts(active_conflict)
    _assert(not active_conflict_facts["release_gate"]["publishable"], "multiple active versions unexpectedly publishable")
    _assert("observation_contract_invalid" in active_conflict_facts["release_gate"]["warnings"], "multiple active version warning missing")

    cross_topic_conflict = copy.deepcopy(baseline)
    cross_topic_conflict["observations"] = {
        "career_public_role": [{"id": "OBS-CROSS-TOPIC-001", "record_version": "OBS-CROSS-TOPIC-001.v1", "state": "active", "statement": "跨主题工作观察", "source_type": "user_report", "source_locator": "obs-career", "relation": "supports_H1", "confidence": "reported"}],
        "money_income": [{"id": "OBS-CROSS-TOPIC-001", "record_version": "OBS-CROSS-TOPIC-001.v2", "state": "active", "statement": "跨主题收入观察", "source_type": "user_report", "source_locator": "obs-money", "relation": "supports_H1", "confidence": "reported"}],
    }
    cross_topic_facts = build_facts(cross_topic_conflict)
    _assert(not cross_topic_facts["release_gate"]["publishable"], "same observation ID across topics unexpectedly publishable")
    _assert("observation_contract_invalid" in cross_topic_facts["release_gate"]["warnings"], "cross-topic duplicate observation warning missing")

    supersedes_missing = copy.deepcopy(baseline)
    supersedes_missing["observations"] = {"career_public_role": [{"id": "OBS-SUPERSEDE-BAD", "record_version": "OBS-SUPERSEDE-BAD.v1", "state": "superseded", "withdrawal_reason": "缺少替代链接"}]}
    supersedes_missing_facts = build_facts(supersedes_missing)
    _assert(not supersedes_missing_facts["release_gate"]["publishable"], "superseded record without link unexpectedly publishable")

    supersedes_unknown = copy.deepcopy(baseline)
    supersedes_unknown["observations"] = {"career_public_role": [{"id": "OBS-SUPERSEDE-UNKNOWN", "record_version": "OBS-SUPERSEDE-UNKNOWN.v1", "state": "superseded", "supersedes": "OBS-SUPERSEDE-UNKNOWN.v9", "withdrawal_reason": "目标版本不存在"}]}
    supersedes_unknown_facts = build_facts(supersedes_unknown)
    _assert(not supersedes_unknown_facts["release_gate"]["publishable"], "supersedes link to unknown version unexpectedly publishable")
    _assert(any("supersedes target not found" in finding for finding in supersedes_unknown_facts["observation_validation"]["findings"]), "unknown supersedes target finding missing")

    invalid_payload = copy.deepcopy(baseline)
    invalid_payload["observations"] = {"money_income": [{"id": "OBS-BAD", "statement": "缺定位"}]}
    invalid_facts = build_facts(invalid_payload)
    _assert(not invalid_facts["release_gate"]["publishable"], "invalid observation unexpectedly publishable")
    _assert("observation_contract_invalid" in invalid_facts["release_gate"]["warnings"], "invalid observation warning missing")
    sensitive_payload = copy.deepcopy(baseline)
    sensitive_payload["observations"] = {"relationship_family": [{
        "id": "OBS-SENSITIVE-G3",
        "record_version": "OBS-SENSITIVE-G3.v1",
        "state": "active",
        "statement": "怀孕结果是否确定",
        "source_type": "user_report",
        "source_locator": "consultation-intake-sensitive",
        "relation": "neutral",
        "confidence": "reported",
        "risk_level": "G3",
        "user_initiated": True,
        "data_minimized": True,
    }]}
    sensitive_facts = build_facts(sensitive_payload)
    _assert(not sensitive_facts["release_gate"]["publishable"], "G3 sensitive observation unexpectedly publishable")
    _assert("observation_contract_invalid" in sensitive_facts["release_gate"]["warnings"], "G3 sensitive warning missing")
    safe_sensitive = sensitive_facts["observations"]["relationship_family"][0]
    _assert(safe_sensitive["statement"] == "[redacted_sensitive_observation]", "sensitive observation was not minimized")
    sensitive_manifest_text = json.dumps(build_manifest(sensitive_facts), ensure_ascii=False)
    _assert("强奸" not in sensitive_manifest_text and "[redacted_sensitive_observation]" not in sensitive_manifest_text, "sensitive observation text leaked into release manifest")

    multilingual_sensitive = copy.deepcopy(baseline)
    multilingual_sensitive["observations"] = {"pressure_risk": [{
        "id": "OBS-EN-G3",
        "record_version": "OBS-EN-G3.v1",
        "state": "active",
        "statement": "Could this be a pregnancy outcome or a miscarriage?",
        "source_type": "user_report",
        "source_locator": "consultation-intake-en",
        "relation": "neutral",
        "confidence": "reported",
        "risk_level": "G3",
        "user_initiated": True,
        "data_minimized": True,
    }]}
    multilingual_facts = build_facts(multilingual_sensitive)
    _assert("observation_contract_invalid" in multilingual_facts["release_gate"]["warnings"], "English sensitive marker was missed")
    _assert(multilingual_facts["observations"]["pressure_risk"][0]["statement"] == "[redacted_sensitive_observation]", "English sensitive observation was not redacted")
    euphemistic_sensitive = copy.deepcopy(baseline)
    euphemistic_sensitive["observations"] = {"pressure_risk": [{
        "id": "OBS-CN-G3",
        "record_version": "OBS-CN-G3.v1",
        "state": "active",
        "statement": "我是不是已经到了大限？",
        "source_type": "user_report",
        "source_locator": "consultation-intake-euphemism",
        "relation": "neutral",
        "confidence": "reported",
        "risk_level": "G3",
        "user_initiated": True,
        "data_minimized": True,
    }]}
    euphemistic_facts = build_facts(euphemistic_sensitive)
    _assert("observation_contract_invalid" in euphemistic_facts["release_gate"]["warnings"], "Chinese euphemistic marker was missed")
    benign = copy.deepcopy(baseline)
    benign["observations"] = {"career_public_role": [{
        "id": "OBS-BENIGN-001",
        "record_version": "OBS-BENIGN-001.v1",
        "state": "active",
        "statement": "项目周期变长，交付边界需要重新划分",
        "source_type": "user_report",
        "source_locator": "consultation-intake-benign",
        "relation": "neutral",
        "confidence": "reported",
    }]}
    benign_facts = build_facts(benign)
    _assert(benign_facts["observation_validation"]["status"] == "collected", "benign observation was falsely marked sensitive")
    _assert(benign_facts["observation_validation"]["sensitive_dictionary_version"] == "SENSITIVE-0.3", "sensitive dictionary version was not recorded")
    dictionary_audit = benign_facts["observation_validation"]["sensitive_dictionary_audit"]
    _assert(dictionary_audit["previous_version"] == "SENSITIVE-0.2" and dictionary_audit["changed_categories"], "dictionary change audit was not recorded")
    mismatch_report = render_report(benign_facts, None, None, [], {"status": "pass", "current_version": "SENSITIVE-0.2", "previous_version": "SENSITIVE-0.1"})
    _assert("FAIL_VERSION_MISMATCH" in mismatch_report, "dictionary audit version mismatch was not visible")

    return {"status": "pass", "negative_cases": findings, "scoring_gate": "locked=A; unlocked=B"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Adversarial regression tests for natal release gates")
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.fixture), ensure_ascii=False, indent=2))
    except (AssertionError, KeyError, ValueError) as exc:
        print(f"FAIL release-gate regression: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
