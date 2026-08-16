#!/usr/bin/env python3
"""Fail-closed audit for the project's information architecture."""
from __future__ import annotations

import json
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "information_architecture.yaml"


def _paths(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _exists(root: Path, raw: str) -> bool:
    if any(mark in raw for mark in "*?["):
        return any(root.glob(raw))
    return (root / raw).exists()


def run() -> list[str]:
    findings: list[str] = []
    if yaml is None:
        return ["pyyaml_missing"]
    try:
        data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"manifest_parse_error:{exc}"]
    for key in ("version", "canonical_roots", "artifact_contract", "lifecycle", "routing_rules", "forbidden_cross_writes"):
        if key not in data:
            findings.append(f"missing_manifest_key:{key}")
    roots = data.get("canonical_roots", {})
    seen: dict[str, str] = {}
    for name, spec in roots.items():
        for raw in _paths(spec.get("path")) + [p for p in _paths(spec.get("paths")) if p not in _paths(spec.get("path"))]:
            if raw in seen and seen[raw] != name:
                findings.append(f"duplicate_path_owner:{raw}:{seen[raw]}:{name}")
            seen[raw] = name
            if not _exists(ROOT, raw):
                findings.append(f"missing_architecture_path:{name}:{raw}")
        if not spec.get("owner"):
            findings.append(f"missing_owner:{name}")
        if not spec.get("write_policy"):
            findings.append(f"missing_write_policy:{name}")
    contracts = data.get("artifact_contract", {})
    for name, spec in contracts.items():
        for key in ("canonical", "required"):
            if not spec.get(key):
                findings.append(f"incomplete_artifact_contract:{name}:{key}")
    lifecycle = data.get("lifecycle", [])
    if len(lifecycle) < 6:
        findings.append("lifecycle_too_short")
    route_config = ROOT / "config" / "interpretation_routes.yaml"
    try:
        routes = yaml.safe_load(route_config.read_text(encoding="utf-8"))
        nodes = routes.get("nodes", {})
        route_extensions = {
            "house_ruler_flow", "typed_reception", "mutual_reception_matrix", "timing",
            "solar_return", "secondary_progression", "solar_arc", "profection", "firdaria",
        }
        for route_id, route in routes.get("routes", {}).items():
            for node in route.get("required_nodes", []) + route.get("optional_nodes", []):
                if node not in nodes and node not in route_extensions and node not in {"responsibility_chain", "property_chain", "wealth_chain", "career_chain", "pressure_chain", "children_chain", "property_chain_when_home_is_in_scope", "natal_structure_first", "predictive_technique", "timing_activation_gate", "composition"}:
                    findings.append(f"route_node_undefined:{route_id}:{node}")
    except Exception as exc:
        findings.append(f"route_parse_error:{exc}")
    try:
        registry = json.loads((ROOT / "clients.json").read_text(encoding="utf-8"))
        if not isinstance(registry, list) or not registry:
            findings.append("client_registry_empty")
    except Exception as exc:
        findings.append(f"client_registry_parse_error:{exc}")
    return findings


if __name__ == "__main__":
    errors = run()
    if errors:
        print("FAIL project architecture")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS project architecture: canonical roots, artifact contracts, lifecycle and route nodes agree")
