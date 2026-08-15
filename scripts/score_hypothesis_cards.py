#!/usr/bin/env python3
"""Apply transparent shared-evidence weighting to hypothesis cards.

This is a candidate scoring aid, not a truth score. Evidence reused across
topic cards receives 0.5 weight and cannot by itself support an A/S upgrade.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
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


def _version_gate(payload: dict[str, Any], facts: dict[str, Any] | None, source_audit: dict[str, Any] | None) -> tuple[str, dict[str, bool], list[str]]:
    metadata = (facts or {}).get("metadata", {})
    lock = {str(key): bool(value) for key, value in metadata.get("rule_version_lock", {}).items()}
    if not lock:
        lock = {str(key): bool(value) for key, value in payload.get("rule_version_lock", {}).items()}
    required = ("terms", "triplicity", "faces", "reception", "aspect")
    blockers = [key for key in required if lock.get(key) is not True]
    if source_audit:
        blockers.extend(source_audit.get("version_gate_blockers", []))
    blockers = sorted(set(blockers))
    if facts is None and not payload.get("rule_version_lock"):
        return "not_evaluated", lock, blockers
    return ("locked" if not blockers else "hold"), lock, blockers


def _source_qualification(registry: dict[str, Any] | None, source_ids: list[str]) -> tuple[str, list[dict[str, Any]], list[str]]:
    if not registry:
        return "not_evaluated", [], []
    sources = registry.get("sources", {})
    profiles: list[dict[str, Any]] = []
    limits: list[str] = []
    unknown = False
    limiting = False
    verified_external = False
    for source_id in source_ids:
        source = sources.get(source_id)
        if not source:
            unknown = True
            profiles.append({"source_id": source_id, "status": "unknown", "layer": "unknown", "limit": "unregistered source"})
            limits.append(f"{source_id}:unregistered source")
            continue
        status = source.get("status", "unknown")
        profiles.append({"source_id": source_id, "status": status, "layer": source.get("layer"), "limit": source.get("limits")})
        if source.get("limits"):
            limits.append(f"{source_id}:{source['limits']}")
        if status in {"auxiliary", "registered", "draft", "已摘录"}:
            limiting = True
        elif status not in {"verified", "已交叉验证", "internal", "per_chart"}:
            unknown = True
        elif status in {"verified", "已交叉验证"} and source.get("layer") not in {"internal_rule", "chart_data"}:
            verified_external = True
    if unknown:
        return "blocked", profiles, sorted(set(limits))
    if limiting or not verified_external:
        return "limited", profiles, sorted(set(limits))
    return "eligible", profiles, sorted(set(limits))


def _counter_test_summary(card: dict[str, Any]) -> dict[str, Any]:
    items = [str(item) for item in card.get("Counter_test", []) if str(item).strip()]
    data_markers = ("缺少", "需要", "未提供", "精确", "待核", "N/A", "资料")
    structural = [item for item in items if not any(marker in item for marker in data_markers)]
    data_limits = [item for item in items if item not in structural]
    types: list[str] = []
    if data_limits:
        types.append("data_or_technique_limit")
    if structural:
        types.append("structural_counter_test")
    if not types:
        types.append("missing")
    return {"count": len(items), "types": types, "items": items, "data_limits": data_limits, "structural_limits": structural}


def _observation_summary(card: dict[str, Any]) -> dict[str, Any]:
    contract = card.get("observation_contract", {})
    items = [item for item in contract.get("items", []) if isinstance(item, dict)]
    relations = sorted({str(item.get("relation")) for item in items if item.get("relation")})
    competing = [item.get("id") for item in items if item.get("relation") in {"supports_H2", "contradicts_H1"}]
    status = contract.get("status", "uncollected")
    if status not in {"uncollected", "collected", "invalid"}:
        status = "invalid"
    return {
        "status": status,
        "interpretation_boundary": contract.get("interpretation_boundary", "uncollected_is_not_counterevidence; withdrawn_is_not_support"),
        "count": len(items),
        "tombstone_count": len(contract.get("tombstones", [])),
        "relations": relations,
        "competing_observation_ids": competing,
        "findings": list(contract.get("findings", [])),
        "required_fields": list(contract.get("required_fields", [])),
    }


def score(
    payload: dict[str, Any],
    registry: dict[str, Any] | None = None,
    facts: dict[str, Any] | None = None,
    source_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    version_gate, version_lock, version_blockers = _version_gate(payload, facts, source_audit)
    cards = payload.get("cards", [])
    frequencies = Counter(evidence_id for card in cards for evidence_id in card.get("evidence_ids", []))
    scored = []
    for card in cards:
        ids = card.get("evidence_ids", [])
        items = {item.get("id"): item for item in card.get("evidence_items", [])}
        unique_ids = [evidence_id for evidence_id in ids if frequencies[evidence_id] == 1]
        shared_ids = [evidence_id for evidence_id in ids if frequencies[evidence_id] > 1]
        effective_weight = round(len(unique_ids) + 0.5 * len(shared_ids), 2)
        independent_groups = sorted({items[evidence_id].get("independence_group") for evidence_id in unique_ids if evidence_id in items})
        independent_source_clusters = sorted({items[evidence_id].get("source_cluster") for evidence_id in unique_ids if evidence_id in items})
        source_ids = sorted({source_id for item in card.get("evidence_items", []) for source_id in item.get("source_ids", [])})
        source_layers = sorted({layer for source_id in source_ids for layer in [registry.get("sources", {}).get(source_id, {}).get("layer")] if layer}) if registry else []
        source_qualification, source_profiles, source_limits = _source_qualification(registry, source_ids)
        counter_test_summary = _counter_test_summary(card)
        observation_summary = _observation_summary(card)
        reception_connection_statuses = sorted({
            str(item.get("connection_status"))
            for item in card.get("evidence_items", [])
            if item.get("source_cluster") == "reception_validation"
        })
        reception_connection_unconfirmed = any(status != "degree_confirmed_connection" for status in reception_connection_statuses)
        conflict_hits = []
        if registry:
            for cluster in registry.get("conflict_clusters", []):
                if len(set(source_ids) & set(cluster.get("sources", []))) >= 2:
                    conflict_hits.append(cluster.get("id"))
        natural_cap = "A" if len(independent_source_clusters) >= 2 else "B"
        grade_cap = natural_cap if version_gate == "locked" and source_qualification == "eligible" and counter_test_summary["types"] != ["missing"] and observation_summary["status"] != "invalid" and not reception_connection_unconfirmed else "B"
        publication_reasons: list[str] = []
        if version_gate != "locked":
            publication_reasons.append("version_gate_hold")
        if source_qualification != "eligible":
            publication_reasons.append(f"source_qualification_{source_qualification}")
        if shared_ids:
            publication_reasons.append("shared_evidence_discount")
        if natural_cap == "B":
            publication_reasons.append("insufficient_independent_source_clusters")
        if "structural_counter_test" in counter_test_summary["types"]:
            publication_reasons.append("structural_counter_test_present")
        if "data_or_technique_limit" in counter_test_summary["types"]:
            publication_reasons.append("data_or_technique_limit_present")
        if counter_test_summary["types"] == ["missing"]:
            publication_reasons.append("counter_test_missing")
        if observation_summary["status"] == "uncollected":
            publication_reasons.append("observation_uncollected")
        elif observation_summary["status"] == "invalid":
            publication_reasons.append("observation_invalid")
        elif observation_summary["status"] == "withdrawn_only":
            publication_reasons.append("observation_withdrawn_only")
        if observation_summary["tombstone_count"]:
            publication_reasons.append("observation_tombstone_present")
        if observation_summary["competing_observation_ids"]:
            publication_reasons.append("observed_competing_evidence")
        if reception_connection_unconfirmed:
            publication_reasons.append("reception_connection_unconfirmed")
        if not publication_reasons:
            publication_reasons.append("eligible_for_natural_A_cap")
        scored.append({
            "topic": card.get("topic"),
            "raw_evidence_count": len(ids),
            "unique_evidence_count": len(unique_ids),
            "shared_evidence_count": len(shared_ids),
            "effective_evidence_weight": effective_weight,
            "independent_groups": independent_groups,
            "independent_source_clusters": independent_source_clusters,
            "grade_cap": grade_cap,
            "natural_grade_cap": natural_cap,
            "source_upgrade_eligibility": source_qualification,
            "source_profiles": source_profiles,
            "source_limits": source_limits,
            "publication_reasons": publication_reasons,
            "counter_test_summary": counter_test_summary,
            "observation_summary": observation_summary,
            "version_gate": version_gate,
            "version_gate_blockers": version_blockers,
            "shared_evidence_ids": shared_ids,
            "source_ids": source_ids,
            "source_layers": source_layers,
            "source_conflict_clusters": conflict_hits,
            "source_quality": "mixed_layers" if len(source_layers) >= 2 else "single_layer_or_unknown",
            "reception_connection_statuses": reception_connection_statuses,
        })
    return {
        "version": "EVIDENCE-WEIGHT-0.1",
        "status": payload.get("status", "unknown"),
        "rule_version_gate": version_gate,
        "rule_version_lock": version_lock,
        "version_gate_blockers": version_blockers,
        "source_conflict_status": (source_audit or {}).get("conflict_status", payload.get("source_conflict_status", [])),
        "cards": scored,
        "evidence_frequency": dict(frequencies),
        "rule": "unique evidence=1.0; evidence reused across topics=0.5; shared evidence alone cannot upgrade to A/S; auxiliary/registered/unregistered source limits cap grade at B",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score hypothesis cards with shared-evidence discount")
    parser.add_argument("cards", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--facts", type=Path, help="pipeline JSON with metadata.rule_version_lock")
    parser.add_argument("--source-audit", type=Path, help="source-registry audit JSON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    registry = _read_json(args.registry) if args.registry else None
    facts = _read_json(args.facts) if args.facts else None
    source_audit = _read_json(args.source_audit) if args.source_audit else None
    result = score(_read_json(args.cards), registry, facts, source_audit)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
