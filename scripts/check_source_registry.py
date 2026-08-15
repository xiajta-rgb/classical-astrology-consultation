#!/usr/bin/env python3
"""Validate provenance IDs and source-conflict references."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"cannot decode JSON: {path}")


ALLOWED_STATUSES = {"verified", "auxiliary", "registered", "internal", "per_chart", "已摘录", "已交叉验证"}


def check(registry: dict[str, Any], cards: dict[str, Any] | None = None, facts: dict[str, Any] | None = None) -> dict[str, Any]:
    sources = registry.get("sources", {})
    findings: list[str] = []
    conflict_refs: list[str] = []
    conflict_status: list[dict[str, Any]] = []
    version_lock = (facts or {}).get("metadata", {}).get("rule_version_lock", {})
    version_values = (facts or {}).get("metadata", {}).get("rule_versions", {})
    for cluster in registry.get("conflict_clusters", []):
        for source_id in cluster.get("sources", []):
            if source_id not in sources:
                findings.append(f"conflict cluster {cluster.get('id')} references unknown source {source_id}")
        conflict_refs.append(cluster.get("id", "unknown"))
        keys = cluster.get("version_keys", [])
        if not keys:
            state = "not_versioned"
        elif not facts:
            state = "unknown_no_chart_facts"
        elif all(version_lock.get(key) is True for key in keys):
            state = "locked"
        elif any(version_lock.get(key) is False for key in keys):
            state = "unlocked"
        else:
            state = "unknown_missing_key"
        conflict_status.append({"id": cluster.get("id"), "version_keys": keys, "state": state, "values": {key: version_values.get(key) for key in keys}})
    profiles = []
    if cards:
        for card in cards.get("cards", []):
            ids = sorted({source_id for item in card.get("evidence_items", []) for source_id in item.get("source_ids", [])})
            unknown = [source_id for source_id in ids if source_id not in sources]
            if unknown:
                findings.append(f"card {card.get('topic')} has unknown source ids: {unknown}")
            inactive = [source_id for source_id in ids if source_id in sources and sources[source_id].get("status") not in ALLOWED_STATUSES]
            if inactive:
                findings.append(f"card {card.get('topic')} has non-upgradeable source statuses: {inactive}")
            profiles.append({
                "topic": card.get("topic"),
                "source_ids": ids,
                "layers": sorted({sources[source_id].get("layer") for source_id in ids if source_id in sources}),
                "unknown": unknown,
            })
    unlocked = [item["id"] for item in conflict_status if item["state"] == "unlocked"]
    unknown = [item["id"] for item in conflict_status if item["state"].startswith("unknown")]
    version_gate = "publish" if facts and not unlocked and not unknown else "hold" if facts else "not_evaluated"
    registry_fingerprint = hashlib.sha256(json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"findings": findings, "conflict_clusters": conflict_refs, "conflict_status": conflict_status, "version_gate": version_gate, "version_gate_blockers": unlocked + unknown, "card_source_profiles": profiles, "source_count": len(sources), "registry_fingerprint": registry_fingerprint, "status": "pass" if not findings else "fail"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source registry and card provenance")
    parser.add_argument("registry", type=Path)
    parser.add_argument("cards", type=Path, nargs="?")
    parser.add_argument("--facts", type=Path, help="pipeline JSON with metadata.rule_version_lock")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    registry = _read_json(args.registry)
    cards = _read_json(args.cards) if args.cards else None
    facts = _read_json(args.facts) if args.facts else None
    result = check(registry, cards, facts)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
