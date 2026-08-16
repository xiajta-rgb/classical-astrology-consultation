#!/usr/bin/env python3
"""Fail-closed audit for the declarative knowledge-plugin layer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "references/knowledge-modules"
VALID_STATUS = {"base", "active", "candidate", "auxiliary", "inactive", "retired"}
VALID_ACTIVATION = {"always", "natal_default", "explicit_topic", "explicit_plugin", "timing_only"}
VALID_GRADES = {"S", "A", "B", "C", "N/A"}
REQUIRED = {
    "id", "version", "status", "layer", "activation", "depends_on", "source_ids", "artifacts",
    "input_contract", "output_contract", "grade_cap", "safety_gate", "override_core", "retrieval",
    "judgment_utility", "event_domains", "event_mechanism", "non_judgment_use", "invocation",
}
VALID_UTILITY = {"primary_judgment", "supporting_inference", "context_only", "deferred"}


def check() -> list[str]:
    findings: list[str] = []
    manifest_path = MODULE_ROOT / "plugins.json"
    contract_path = MODULE_ROOT / "plugin-contract.json"
    if not manifest_path.exists():
        return ["missing plugins.json"]
    if not contract_path.exists():
        findings.append("missing plugin-contract.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8")) if contract_path.exists() else {}
    plugins = manifest.get("plugins", [])
    if manifest.get("contract") != contract_path.name:
        findings.append("manifest contract pointer mismatch")
    if not plugins:
        findings.append("no plugins")
    ids = {p.get("id") for p in plugins}
    if not plugins or plugins[0].get("id") != "natal-core":
        findings.append("natal-core must be the first plugin")
    # Dependencies must form a DAG so a new plugin can be added without
    # creating an impossible activation order.
    graph = {p.get("id"): set(p.get("depends_on", [])) for p in plugins}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            findings.append(f"dependency_cycle:{node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, set()):
            if dependency in graph:
                visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    source_registry = json.loads((ROOT / "references/source-registry.json").read_text(encoding="utf-8"))
    known_sources = set(source_registry.get("sources", {}))
    invocation_symbols: dict[str, str] = {}
    for plugin in plugins:
        pid = plugin.get("id", "<missing>")
        missing = sorted(REQUIRED - set(plugin))
        if missing:
            findings.append(f"{pid}: missing {missing}")
        if plugin.get("status") not in VALID_STATUS:
            findings.append(f"{pid}: invalid status")
        if plugin.get("activation") not in VALID_ACTIVATION:
            findings.append(f"{pid}: invalid activation")
        if plugin.get("grade_cap") not in VALID_GRADES:
            findings.append(f"{pid}: invalid grade cap")
        if plugin.get("judgment_utility") not in VALID_UTILITY:
            findings.append(f"{pid}: invalid judgment utility")
        if plugin.get("override_core") is not False:
            findings.append(f"{pid}: override_core must be false")
        if plugin.get("status") in {"candidate", "auxiliary"} and plugin.get("grade_cap") not in {"C", "N/A"}:
            findings.append(f"{pid}: candidate/auxiliary grade cap must be C or N/A")
        unknown_deps = sorted(set(plugin.get("depends_on", [])) - ids)
        if unknown_deps:
            findings.append(f"{pid}: unknown dependencies {unknown_deps}")
        unknown_sources = sorted(set(plugin.get("source_ids", [])) - known_sources)
        if unknown_sources:
            findings.append(f"{pid}: unknown sources {unknown_sources}")
        for artifact in plugin.get("artifacts", []):
            if not (ROOT / artifact).exists():
                findings.append(f"{pid}: missing artifact {artifact}")
        invocation = plugin.get("invocation", {})
        if plugin.get("status") not in {"inactive", "retired"} and not invocation:
            findings.append(f"{pid}: callable plugin must declare invocation symbol/aliases/trigger/fallback")
        if invocation:
            symbol = invocation.get("symbol")
            if not symbol or not str(symbol).startswith("@"):
                findings.append(f"{pid}: invocation symbol must start with @")
            elif symbol in invocation_symbols:
                findings.append(f"duplicate_invocation_symbol:{symbol}:{invocation_symbols[symbol]}:{pid}")
            else:
                invocation_symbols[symbol] = pid
            registry = invocation.get("registry")
            if registry and not (ROOT / registry).exists():
                findings.append(f"{pid}: invocation registry missing {registry}")
            if not isinstance(invocation.get("aliases", []), list) or not invocation.get("aliases"):
                findings.append(f"{pid}: invocation aliases must be a non-empty list")
            if not invocation.get("trigger") and not invocation.get("auto_conditions"):
                findings.append(f"{pid}: invocation must declare trigger or auto_conditions")
            if not invocation.get("fallback"):
                findings.append(f"{pid}: invocation must declare fallback")
        if plugin.get("activation") == "timing_only" and plugin.get("status") not in {"inactive", "retired"}:
            findings.append(f"{pid}: timing_only plugin must be inactive/retired")
        if plugin.get("activation") == "timing_only" and plugin.get("grade_cap") != "N/A":
            findings.append(f"{pid}: timing_only plugin must have N/A grade cap")
        if plugin.get("status") in {"base", "active", "candidate"} and plugin.get("judgment_utility") != "deferred":
            if not plugin.get("event_domains") or not plugin.get("event_mechanism"):
                findings.append(f"{pid}: judgment plugin must declare event domains and mechanism")
        if plugin.get("judgment_utility") in {"context_only", "deferred"} and plugin.get("grade_cap") not in {"C", "N/A"}:
            findings.append(f"{pid}: context/deferred utility cannot exceed C or N/A")
        retrieval = plugin.get("retrieval", {})
        if not isinstance(retrieval.get("topics", []), list) or not isinstance(retrieval.get("modules", []), list):
            findings.append(f"{pid}: retrieval topics/modules must be lists")
        for module_name, policy in plugin.get("module_policy", {}).items():
            if policy.get("judgment_utility") not in VALID_UTILITY:
                findings.append(f"{pid}/{module_name}: invalid module judgment utility")
            if policy.get("judgment_utility") != "context_only" and not policy.get("event_domains"):
                findings.append(f"{pid}/{module_name}: non-context module needs event domains")
    expected = set(contract.get("required_fields", []))
    if expected and expected != REQUIRED:
        findings.append("contract required_fields diverge from checker contract")

    index_path = MODULE_ROOT / "core/retrieval-index.json"
    cards_path = MODULE_ROOT / "core/cards.jsonl"
    if not index_path.exists():
        findings.append("missing core/retrieval-index.json; run build_knowledge_index.py")
    elif cards_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(cards_path.read_bytes()).hexdigest()
        if index.get("card_fingerprint_sha256") != digest:
            findings.append("retrieval index fingerprint is stale")
        actual = sum(1 for line in cards_path.read_text(encoding="utf-8").splitlines() if line.strip())
        if index.get("counts", {}).get("all_records") != actual:
            findings.append("retrieval index card count is stale")
        card_required = contract.get("output_contract", {}).get("card_required", [])
        for line_no, line in enumerate(cards_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            card = json.loads(line)
            missing_card = [
                key for key in card_required
                if key not in card
                and not (key == "card_id" and card.get("id"))
                and not (key == "text" and (card.get("source_summary") or card.get("observable_translation")))
            ]
            if missing_card:
                findings.append(f"card_contract_missing:{line_no}:{missing_card}")
                break
        indexed_modules = set(index.get("by_module", {}))
        for plugin in plugins:
            for module_name in plugin.get("retrieval", {}).get("modules", []):
                if module_name not in indexed_modules:
                    findings.append(f"plugin_module_not_indexed:{plugin.get('id')}:{module_name}")
    return findings


def main() -> int:
    findings = check()
    if findings:
        print("FAIL")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    manifest = json.loads((MODULE_ROOT / "plugins.json").read_text(encoding="utf-8"))
    print(f"PASS plugin architecture: {len(manifest['plugins'])} plugins, contract/index/dependencies valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
