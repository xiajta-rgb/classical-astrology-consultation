#!/usr/bin/env python3
"""Fail-closed audit for the single consultation dispatch graph."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DISPATCH = ROOT / "config/module_dispatch.yaml"
PLUGINS = ROOT / "references/knowledge-modules/plugins.json"
KNOWLEDGE_INDEX = ROOT / "references/knowledge-modules/core/retrieval-index.json"
KNOWLEDGE_REGISTRY = ROOT / "references/knowledge-modules/registry.json"
INTERPRETATION_REGISTRY = ROOT / "references/interpretation-modules/registry.json"
INTERPRETATION_ROUTES = ROOT / "config/interpretation_routes.yaml"
KNOWLEDGE_SCOPE = ROOT / "config/knowledge_scope.yaml"
KNOWLEDGE_SYMBOLS = ROOT / "config/knowledge_symbols.yaml"


def check() -> list[str]:
    findings: list[str] = []
    try:
        data: dict[str, Any] = yaml.safe_load(DISPATCH.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"dispatch_parse_error:{exc}"]
    if data.get("version") != "DISPATCH-1.0":
        findings.append("dispatch_version_missing_or_wrong")
    if data.get("knowledge_symbol_registry") != "config/knowledge_symbols.yaml":
        findings.append("knowledge_symbol_registry_pointer_missing")
    if data.get("plugin_manifest") != "references/knowledge-modules/plugins.json":
        findings.append("plugin_manifest_pointer_missing")
    modules = data.get("modules", {})
    order = data.get("canonical_order", [])
    if len(order) != len(set(order)):
        findings.append("canonical_order_has_duplicates")
    if set(order) != set(modules):
        findings.append("canonical_order_and_modules_disagree")
    for entrypoint in ("topic_question", "timing_question"):
        if data.get("entrypoints", {}).get(entrypoint, {}).get("topic_map") != "config/interpretation_routes.yaml":
            findings.append(f"entrypoint_topic_map_pointer_missing:{entrypoint}")
    for module_id, spec in modules.items():
        for key in ("version", "owner", "source", "activation", "output"):
            if not spec.get(key):
                findings.append(f"module_missing_{key}:{module_id}")
    for route_id, route in data.get("routes", {}).items():
        required = route.get("required_modules", [])
        unknown = sorted(set(required) - set(modules))
        if unknown:
            findings.append(f"route_unknown_modules:{route_id}:{unknown}")
        if route_id != "current_timing" and "chart_facts" not in required:
            findings.append(f"route_missing_chart_facts:{route_id}")
        if route_id == "current_timing" and "timing_extension" not in required:
            findings.append("timing_route_missing_timing_extension")
    plugin_data = json.loads(PLUGINS.read_text(encoding="utf-8"))
    plugin_ids = {item.get("id") for item in plugin_data.get("plugins", [])}
    symbol_data = yaml.safe_load(KNOWLEDGE_SYMBOLS.read_text(encoding="utf-8"))
    symbol_map = symbol_data.get("symbols", {})
    if symbol_data.get("registry") != "references/knowledge-modules/plugins.json":
        findings.append("knowledge_symbol_registry_target_missing")
    if symbol_data.get("authority") != "plugins.json.invocation":
        findings.append("knowledge_symbol_registry_authority_missing")
    manifest_symbols = {}
    for plugin in plugin_data.get("plugins", []):
        invocation = plugin.get("invocation", {})
        if invocation.get("symbol"):
            manifest_symbols[invocation["symbol"]] = plugin.get("id")
    if set(symbol_map) != set(manifest_symbols):
        findings.append("knowledge_symbol_registry_manifest_drift")
    for symbol, plugin_id in manifest_symbols.items():
        if symbol_map.get(symbol, {}).get("plugin_id") != plugin_id:
            findings.append(f"knowledge_symbol_target_mismatch:{symbol}:{plugin_id}")
    knowledge_index = json.loads(KNOWLEDGE_INDEX.read_text(encoding="utf-8"))
    indexed_modules = set(knowledge_index.get("by_module", {}))
    for item in data.get("natal_core_extensions", []):
        plugin_id = item.get("plugin")
        plugin = next((candidate for candidate in plugin_data.get("plugins", []) if candidate.get("id") == plugin_id), None)
        if plugin_id not in plugin_ids:
            findings.append(f"natal_core_extension_unknown_plugin:{plugin_id}")
        elif plugin.get("activation") not in {"always", "natal_default"}:
            findings.append(f"natal_core_extension_not_natal_default:{plugin_id}")
        if not item.get("symbol"):
            findings.append(f"natal_core_extension_missing_symbol:{plugin_id}")
        if not item.get("trigger"):
            findings.append(f"natal_core_extension_missing_trigger:{plugin_id}")
    for route_id, route in data.get("routes", {}).items():
        unknown_plugins = sorted(set(route.get("knowledge_plugins", [])) - plugin_ids)
        if unknown_plugins:
            findings.append(f"route_unknown_knowledge_plugins:{route_id}:{unknown_plugins}")
        for label, module_name in {"default": route.get("topic_module"), **route.get("topic_modules", {})}.items():
            if module_name and module_name not in indexed_modules:
                findings.append(f"route_topic_module_not_indexed:{route_id}:{label}:{module_name}")
    knowledge_registry = json.loads(KNOWLEDGE_REGISTRY.read_text(encoding="utf-8"))
    if knowledge_registry.get("role") != "source_extraction_audit_only":
        findings.append("knowledge_registry_must_be_source_audit_only")
    if knowledge_registry.get("runtime_activation") != "references/knowledge-modules/plugins.json":
        findings.append("knowledge_registry_runtime_pointer_mismatch")
    interpretation_registry = json.loads(INTERPRETATION_REGISTRY.read_text(encoding="utf-8"))
    if interpretation_registry.get("role") != "case_independent_topic_templates":
        findings.append("interpretation_registry_role_missing")
    if interpretation_registry.get("runtime_activation") != "config/module_dispatch.yaml":
        findings.append("interpretation_registry_runtime_pointer_mismatch")
    interpretation_routes = yaml.safe_load(INTERPRETATION_ROUTES.read_text(encoding="utf-8"))
    if interpretation_routes.get("role") != "topic_responsibility_map_only":
        findings.append("interpretation_routes_must_be_topic_map_only")
    dispatch_routes = set(data.get("routes", {}))
    topic_routes = set(interpretation_routes.get("routes", {}))
    if dispatch_routes - topic_routes:
        findings.append(f"dispatch_routes_missing_topic_map:{sorted(dispatch_routes - topic_routes)}")
    if topic_routes - dispatch_routes:
        findings.append(f"topic_map_routes_missing_dispatch:{sorted(topic_routes - dispatch_routes)}")
    for route_id, route in data.get("routes", {}).items():
        if "topic" in route:
            findings.append(f"duplicate_topic_alias_storage:{route_id}")
    for route_id in dispatch_routes & topic_routes:
        if route_id == "current_timing":
            continue
        if not interpretation_routes["routes"][route_id].get("match_topics"):
            findings.append(f"topic_map_missing_match_topics:{route_id}")
    knowledge_scope = yaml.safe_load(KNOWLEDGE_SCOPE.read_text(encoding="utf-8"))
    if knowledge_scope.get("canonical_runtime_registry") != "references/knowledge-modules/plugins.json":
        findings.append("knowledge_scope_runtime_registry_mismatch")
    if not knowledge_scope.get("retain") or not knowledge_scope.get("exclude_or_route_elsewhere"):
        findings.append("knowledge_scope_missing_retain_or_exclude_policy")
    promotion = knowledge_scope.get("promotion", {})
    for key in ("require_source_locator", "require_counter_test", "require_two_independent_cases", "require_machine_regression"):
        if promotion.get(key) is not True:
            findings.append(f"knowledge_scope_promotion_gate_missing:{key}")
    # A global interpretation registry must not carry a client's concrete
    # chart facts.  Generic boundary language is allowed; case names/degrees
    # and administrative-place assumptions are not.
    registry_text = INTERPRETATION_REGISTRY.read_text(encoding="utf-8")
    for marker in ("ASC为巨蟹", "行政区中心", "这个盘", "图中", "案例"): 
        if marker in registry_text:
            findings.append(f"case_specific_text_in_global_registry:{marker}")
    if "model_memory_as_source" not in set(data.get("forbidden_shortcuts", [])):
        findings.append("model_memory_shortcut_not_forbidden")
    if "knowledge_card_before_chart_facts" not in set(data.get("forbidden_shortcuts", [])):
        findings.append("knowledge_before_facts_shortcut_not_forbidden")
    expected_sources = {
        "chart_facts": "astrology_engine.natal.calculate_natal",
        "responsibility_chain": "astrology_engine.significations.calculate_responsibilities",
    }
    for module_id, expected in expected_sources.items():
        if modules.get(module_id, {}).get("source") != expected:
            findings.append(f"canonical_source_mismatch:{module_id}")
    # Exercise the planner's public contract without calculating a chart.  This
    # catches alias drift and accidental timing fall-through during config edits.
    try:
        from scripts.plan_consultation import plan
        checks = (
            (plan(topic="property"), "property_wealth"),
            (plan(topic="reception"), "reception_audit"),
            (plan(topic="future"), "timing_question_requires_explicit_timing_flag"),
            (plan(topic="future", timing=True, timing_technique="transit"), "current_timing"),
        )
        for result, expected in checks:
            actual = result.get("reason") if result.get("status") == "hold" else result.get("route_id")
            if actual != expected:
                findings.append(f"planner_contract_mismatch:{actual}!={expected}")
        alias_plan = plan(topic="future", timing=True, timing_technique="transits")
        if alias_plan.get("timing", {}).get("technique") != "transit":
            findings.append("planner_timing_alias_not_canonicalized")
    except Exception as exc:
        findings.append(f"planner_contract_error:{type(exc).__name__}:{exc}")
    return findings


def main() -> int:
    findings = check()
    if findings:
        print("FAIL module dispatch")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    data = yaml.safe_load(DISPATCH.read_text(encoding="utf-8"))
    print(f"PASS module dispatch: {len(data['modules'])} modules, {len(data['routes'])} routes, case hygiene verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
