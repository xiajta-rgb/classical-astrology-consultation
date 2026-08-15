#!/usr/bin/env python3
"""QA for bounded natal hypothesis cards.

It treats repeated evidence across topics as a visible dependency rather than
silently counting it as independent support, and rejects generic cards that
lack a chart-specific anchor.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


GENERIC_PHRASES = ("有潜力", "比较敏感", "找到平衡", "发挥优势", "关系复杂", "能量很强", "不断成长")
REQUIRED_FIELDS = ("topic", "H1_leading", "H2_runner_up", "Evidence", "evidence_items", "chart_specific_anchor", "Counter_test", "Missing_discriminator", "grade", "rule_version_gate", "rule_version_lock")


def check(payload: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    cards = payload.get("cards", [])
    if payload.get("status") == "hold":
        if cards:
            findings.append("hold package must not contain hypothesis cards")
        return {"findings": findings, "shared_evidence": {}, "source_reuse": {}, "cards": len(cards), "status": "pass"}
    seen_topics: set[str] = set()
    shared: dict[str, list[str]] = defaultdict(list)
    source_reuse: dict[str, list[str]] = defaultdict(list)
    for index, card in enumerate(cards):
        prefix = f"card[{index}]"
        for field in REQUIRED_FIELDS:
            if not card.get(field):
                findings.append(f"{prefix} missing {field}")
        topic = card.get("topic")
        if topic in seen_topics:
            findings.append(f"duplicate topic: {topic}")
        seen_topics.add(topic)
        ids = card.get("evidence_ids", [])
        if len(ids) != len(set(ids)):
            findings.append(f"{prefix} duplicates evidence within card")
        item_ids = [item.get("id") for item in card.get("evidence_items", [])]
        if ids != item_ids:
            findings.append(f"{prefix} evidence_ids do not match evidence_items")
        for item in card.get("evidence_items", []):
            if not item.get("source_ids") or not item.get("source_cluster"):
                findings.append(f"{prefix} evidence item lacks source provenance: {item.get('id')}")
            else:
                source_reuse[item["source_cluster"]].append(str(topic))
        for evidence_id in ids:
            shared[evidence_id].append(str(topic))
        if card.get("H1_leading") == card.get("H2_runner_up"):
            findings.append(f"{prefix} H1 and H2 are identical")
        if card.get("grade") in ("S", "A"):
            findings.append(f"{prefix} auto-generated card cannot be S/A")
        combined = " ".join(str(card.get(key, "")) for key in ("H1_leading", "H2_runner_up", "chart_specific_anchor", "Observable_translation_candidate"))
        for phrase in GENERIC_PHRASES:
            if phrase in combined:
                findings.append(f"{prefix} generic phrase: {phrase}")
        if len(card.get("evidence_items", [])) < 1:
            findings.append(f"{prefix} has no chart-specific evidence")
    shared = {key: topics for key, topics in shared.items() if len(topics) > 1}
    source_reuse = {key: topics for key, topics in source_reuse.items() if len(topics) > 1}
    return {"findings": findings, "shared_evidence": shared, "source_reuse": source_reuse, "cards": len(cards), "status": "pass_with_shared_dependencies" if shared else "pass"}


def compare_anchors(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    left_map = {card.get("topic"): card.get("chart_specific_anchor") for card in left.get("cards", [])}
    right_map = {card.get("topic"): card.get("chart_specific_anchor") for card in right.get("cards", [])}
    findings = []
    for topic in sorted(set(left_map) & set(right_map)):
        if left_map[topic] == right_map[topic]:
            findings.append(f"swap-test anchor unchanged: {topic}")
    return findings


GOOD = {
    "status": "candidate",
    "cards": [{
        "topic": "money_income", "H1_leading": "收入通过2宫主落点交付", "H2_runner_up": "家庭责任牵动现金流",
        "Evidence": ["2宫宫头狮子，宫主太阳落4宫天蝎"],
        "evidence_items": [{"id": "HOUSE_2_RULER_PLACEMENT", "fact": "2宫宫头狮子，宫主太阳落4宫天蝎", "source_ids": ["house-matrix"], "source_cluster": "house_responsibility"}],
        "evidence_ids": ["HOUSE_2_RULER_PLACEMENT"], "chart_specific_anchor": "2宫宫头狮子，宫主太阳落4宫天蝎",
        "Counter_test": ["太阳状态与8宫链仍需复核"], "Missing_discriminator": ["精确度数"], "grade": "B",
        "rule_version_gate": "locked", "rule_version_lock": {"terms": True, "triplicity": True, "faces": True, "reception": True, "aspect": True},
    }],
}


def self_test() -> int:
    good = check(GOOD)
    if good["findings"]:
        print("FAIL good fixture:", good["findings"])
        return 1
    bad = json.loads(json.dumps(GOOD, ensure_ascii=False))
    bad["cards"][0]["H1_leading"] = "有潜力"
    bad["cards"][0]["H2_runner_up"] = "有潜力"
    bad["cards"][0]["evidence_ids"] = ["HOUSE_2_RULER_PLACEMENT", "HOUSE_2_RULER_PLACEMENT"]
    if not check(bad)["findings"]:
        print("FAIL bad fixture accepted")
        return 1
    provenance_bad = json.loads(json.dumps(GOOD, ensure_ascii=False))
    provenance_bad["cards"][0]["evidence_items"][0].pop("source_ids")
    if not check(provenance_bad)["findings"]:
        print("FAIL provenance fixture accepted")
        return 1
    changed = json.loads(json.dumps(GOOD, ensure_ascii=False))
    changed["cards"][0]["chart_specific_anchor"] = "2宫宫头白羊，宫主火星落10宫白羊"
    if compare_anchors(GOOD, changed):
        print("FAIL swap fixture incorrectly rejected")
        return 1
    same = json.loads(json.dumps(GOOD, ensure_ascii=False))
    if not compare_anchors(GOOD, same):
        print("FAIL unchanged swap fixture accepted")
        return 1
    print("PASS hypothesis-card self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cards", type=Path, nargs="?")
    parser.add_argument("--compare", type=Path, help="compare chart-specific anchors against a second cards JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.cards is None:
        parser.error("provide cards JSON or --self-test")
    result = check(json.loads(args.cards.read_text(encoding="utf-8")))
    if args.compare:
        result["swap_test_findings"] = compare_anchors(json.loads(args.cards.read_text(encoding="utf-8")), json.loads(args.compare.read_text(encoding="utf-8")))
        result["findings"].extend(result["swap_test_findings"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["findings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
