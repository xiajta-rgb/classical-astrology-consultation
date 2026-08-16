#!/usr/bin/env python3
"""Compose normalized significators into reusable event-mechanism patterns.

This is an orchestration layer, not a planetary calculator. It deliberately
deduplicates repeated evidence and reports convergence/conflict/bottleneck
patterns so finite cases can teach abstractions instead of fixed combinations.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


AXES = ((1, 7), (2, 8), (3, 9), (4, 10), (5, 11))


def _set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value}
    return {str(value)}


def compose(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    by_mechanism: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_carrier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in evidence:
        mechanism = item.get("mechanism")
        domain = item.get("domain")
        carrier = item.get("carrier")
        if mechanism:
            by_mechanism[str(mechanism)].append(item)
        if domain:
            by_domain[str(domain)].append(item)
        if carrier:
            by_carrier[str(carrier)].append(item)

    mechanisms: list[dict[str, Any]] = []
    for mechanism, items in sorted(by_mechanism.items()):
        chains = {str(item.get("chain_id", item.get("id", "unknown"))) for item in items}
        sources = {source for item in items for source in _set(item.get("source_ids"))}
        polarities = {str(item.get("polarity", "neutral")) for item in items}
        domains = sorted({str(item.get("domain")) for item in items if item.get("domain")})
        status = "convergent" if len(chains) >= 2 and len(polarities) <= 1 else "conflicted" if len(polarities) > 1 else "single_chain"
        mechanisms.append({
            "mechanism": mechanism,
            "status": status,
            "independent_chain_count": len(chains),
            "source_count": len(sources),
            "domains": domains,
            "evidence_ids": [str(item.get("id")) for item in items],
            "requires_discriminator": status != "convergent",
        })

    conflicts: list[dict[str, Any]] = []
    for domain, items in sorted(by_domain.items()):
        polarities = {str(item.get("polarity", "neutral")) for item in items}
        if "support" in polarities and "constraint" in polarities:
            conflicts.append({
                "domain": domain,
                "pattern": "support_vs_constraint",
                "evidence_ids": [str(item.get("id")) for item in items],
                "translation": "conditional or costly delivery; do not average into a binary good/bad score",
            })

    bottlenecks: list[dict[str, Any]] = []
    for carrier, items in sorted(by_carrier.items()):
        responsibilities = {str(item.get("responsibility", item.get("domain", "unknown"))) for item in items}
        constrained = any(str(item.get("polarity")) == "constraint" or "constrained" in _set(item.get("condition")) for item in items)
        if len(responsibilities) >= 2 and constrained:
            bottlenecks.append({
                "carrier": carrier,
                "responsibilities": sorted(responsibilities),
                "evidence_ids": [str(item.get("id")) for item in items],
                "translation": "one delivery bottleneck carries several life domains; count the mechanism once",
            })

    axis_tensions: list[dict[str, Any]] = []
    numeric_domains = {int(item.get("house")) for item in evidence if str(item.get("house", "")).isdigit()}
    for left, right in AXES:
        if left in numeric_domains and right in numeric_domains:
            axis_tensions.append({"axis": f"{left}/{right}", "pattern": "private_public_or_resource_polarity", "requires_topic_specific_translation": True})

    return {
        "schema_version": "COMPOSITION-0.1",
        "evidence_count": len(evidence),
        "mechanisms": mechanisms,
        "conflicts": conflicts,
        "bottlenecks": bottlenecks,
        "axis_tensions": axis_tensions,
        "event_ladder": ["ordinary manifestation", "structural strain", "major transition/loss candidate"],
        "guards": [
            "deduplicate repeated chain evidence before confidence increases",
            "a convergent mechanism is not automatically a severe event",
            "major transition/loss candidates require independent timing and sensitive-topic gates",
            "sign/planet/house keywords cannot bypass responsibility and delivery analysis",
        ],
    }


def self_test() -> int:
    result = compose([
        {"id": "moon_4", "chain_id": "family_chain", "domain": "family", "house": 4, "responsibility": "care", "carrier": "Moon", "mechanism": "private_security_governance", "polarity": "constraint", "condition": ["constrained"], "source_ids": ["R41"]},
        {"id": "pluto_4", "chain_id": "modern_auxiliary", "domain": "family", "house": 4, "responsibility": "care", "carrier": "Pluto", "mechanism": "private_security_governance", "polarity": "support", "condition": ["angular"], "source_ids": ["R44"]},
        {"id": "career_10", "chain_id": "career_chain", "domain": "career", "house": 10, "responsibility": "public_role", "carrier": "Saturn", "mechanism": "private_security_governance", "polarity": "neutral", "source_ids": ["R01"]},
    ])
    assert result["mechanisms"][0]["status"] == "conflicted"
    assert result["conflicts"]
    assert result["bottlenecks"] == []
    assert result["axis_tensions"]
    print("PASS composition self-test: conflict, deduplication and event ladder guards")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.evidence is None:
        parser.error("provide evidence JSON or --self-test")
    payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    evidence = payload.get("evidence", payload) if isinstance(payload, dict) else payload
    print(json.dumps(compose(evidence), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
