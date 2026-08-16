#!/usr/bin/env python3
"""Fail-closed audit for architectural boundaries and orchestration size.

This check is intentionally narrower than the functional test suite: it guards
the seams between calculation, routing and knowledge, where accidental coupling
is otherwise easy to introduce while every individual module still passes.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "config/module_dispatch.yaml"
SYMBOLS = ROOT / "config/knowledge_symbols.yaml"
PLUGINS = ROOT / "references/knowledge-modules/plugins.json"
ONTOLOGY = ROOT / "references/signification-ontology.yaml"
RUNTIME_ORCHESTRATORS = {
    "scripts/run_natal_pipeline.py": 320,
    "scripts/plan_consultation.py": 300,
    "scripts/query_knowledge_plugins.py": 320,
}


def _top_level_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.append(("." * node.level) + (node.module or ""))
    return result


def check() -> list[str]:
    findings: list[str] = []
    dispatch: dict[str, Any] = yaml.safe_load(DISPATCH.read_text(encoding="utf-8"))
    symbols: dict[str, Any] = yaml.safe_load(SYMBOLS.read_text(encoding="utf-8"))
    manifest: dict[str, Any] = json.loads(PLUGINS.read_text(encoding="utf-8"))
    ontology: dict[str, Any] = yaml.safe_load(ONTOLOGY.read_text(encoding="utf-8"))

    if dispatch.get("knowledge_symbol_registry") != "config/knowledge_symbols.yaml":
        findings.append("dispatch_symbol_registry_pointer_drift")
    if symbols.get("authority") != "plugins.json.invocation":
        findings.append("symbol_registry_has_no_single_authority")
    if len(ontology.get("houses", {})) != 12:
        findings.append("signification_ontology_house_coverage_incomplete")
    if len(ontology.get("signs", {})) != 12:
        findings.append("signification_ontology_sign_coverage_incomplete")
    if not {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}.issubset(ontology.get("planets", {})):
        findings.append("signification_ontology_classical_planet_coverage_incomplete")
    if not {"conjunction", "sextile", "square", "trine", "opposition"}.issubset(ontology.get("aspects", {})):
        findings.append("signification_ontology_major_aspect_coverage_incomplete")

    manifest_symbols = {
        item.get("invocation", {}).get("symbol"): item.get("id")
        for item in manifest.get("plugins", [])
        if item.get("invocation", {}).get("symbol")
    }
    index_symbols = {
        symbol: item.get("plugin_id")
        for symbol, item in symbols.get("symbols", {}).items()
    }
    if manifest_symbols != index_symbols:
        findings.append("plugin_symbol_index_drift")

    for relative, limit in RUNTIME_ORCHESTRATORS.items():
        path = ROOT / relative
        if path.exists() and len(path.read_text(encoding="utf-8").splitlines()) > limit:
            findings.append(f"orchestrator_too_large:{relative}:{limit}")

    for path in (ROOT / "astrology_engine").rglob("*.py"):
        for imported in _top_level_imports(path):
            if imported.startswith("scripts"):
                findings.append(f"engine_depends_on_scripts:{path.relative_to(ROOT)}:{imported}")

    facade = ROOT / "astrology_engine/__init__.py"
    for imported in _top_level_imports(facade):
        if imported in {".mbti", ".tpes"}:
            findings.append(f"core_facade_eager_auxiliary_import:{imported}")

    if "conditional_knowledge_plugins" in dispatch:
        findings.append("legacy_conditional_plugin_section_still_present")
    return findings


def main() -> int:
    findings = check()
    if findings:
        print("FAIL architecture coupling")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("PASS architecture coupling: registries, engine boundaries and orchestration budgets agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
