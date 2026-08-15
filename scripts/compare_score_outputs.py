#!/usr/bin/env python3
"""Compare two score outputs without treating any score as authoritative alone."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


COMPARE_FIELDS = (
    "natural_grade_cap", "grade_cap", "source_upgrade_eligibility", "source_profiles", "source_limits",
    "publication_reasons", "counter_test_summary", "observation_summary", "raw_evidence_count",
    "unique_evidence_count", "shared_evidence_count", "effective_evidence_weight", "independent_groups",
    "independent_source_clusters", "version_gate", "version_gate_blockers", "shared_evidence_ids",
    "source_ids", "source_layers", "source_conflict_clusters", "source_quality",
)


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_cards = {item.get("topic"): item for item in before.get("cards", [])}
    after_cards = {item.get("topic"): item for item in after.get("cards", [])}
    changes: list[dict[str, Any]] = []
    findings: list[str] = []
    for topic in sorted(set(before_cards) | set(after_cards)):
        if topic not in before_cards or topic not in after_cards:
            findings.append(f"topic_added_or_removed:{topic}")
            changes.append({"topic": topic, "before": before_cards.get(topic), "after": after_cards.get(topic)})
            continue
        field_changes = {}
        for field in COMPARE_FIELDS:
            if before_cards[topic].get(field) != after_cards[topic].get(field):
                field_changes[field] = {"before": before_cards[topic].get(field), "after": after_cards[topic].get(field)}
        if field_changes:
            changes.append({"topic": topic, "changes": field_changes})
    return {"status": "pass" if not findings else "fail", "changed_topics": [item["topic"] for item in changes], "changes": changes, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two hypothesis score outputs")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    before = json.loads(args.before.read_text(encoding="utf-8"))
    after = json.loads(args.after.read_text(encoding="utf-8"))
    result = compare(before, after)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
