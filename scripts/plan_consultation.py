#!/usr/bin/env python3
"""Resolve the canonical consultation module route without doing interpretation.

The planner is intentionally deterministic.  It is the small "brain stem" of
the project: it tells the agent which local calculation and knowledge modules
must be called before any prose is written, and which timing modules must stay
inactive.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from astrology_engine.predictive import TECHNIQUES  # noqa: E402
DISPATCH = ROOT / "config/module_dispatch.yaml"
TOPIC_MAP = ROOT / "config/interpretation_routes.yaml"
PLUGIN_MANIFEST = ROOT / "references/knowledge-modules/plugins.json"


def _load() -> dict[str, Any]:
    return yaml.safe_load(DISPATCH.read_text(encoding="utf-8"))


def _load_topic_map() -> dict[str, Any]:
    return yaml.safe_load(TOPIC_MAP.read_text(encoding="utf-8"))


def _load_plugin_manifest() -> dict[str, Any]:
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


def _available_symbols() -> list[dict[str, Any]]:
    """Expose the callable symbol index without activating every plugin."""
    result = []
    for item in _load_plugin_manifest().get("plugins", []):
        invocation = item.get("invocation", {})
        if not invocation.get("symbol"):
            continue
        result.append({
            "symbol": invocation["symbol"],
            "plugin": item.get("id"),
            "status": item.get("status"),
            "activation": item.get("activation"),
            "priority": invocation.get("priority"),
        })
    return sorted(result, key=lambda item: item["symbol"])


def _conditional_plugins(data: dict[str, Any], topic: str) -> list[dict[str, Any]]:
    """Return declarative plugin triggers without pretending Chart Facts were scanned."""
    normalized = topic.strip().lower().replace("-", "_")
    manifest = _load_plugin_manifest()
    aliases: set[str] = set()
    for item in manifest.get("plugins", []):
        invocation = item.get("invocation", {})
        aliases.update(str(value).lower().replace("-", "_") for value in invocation.get("aliases", []))
    selected = []
    for item in data.get("natal_core_extensions", data.get("conditional_knowledge_plugins", [])):
        plugin_id = item.get("plugin")
        plugin = next((p for p in manifest.get("plugins", []) if p.get("id") == plugin_id), None)
        if not plugin:
            continue
        invocation = plugin.get("invocation", {})
        topic_hit = normalized in aliases or any(alias and alias in normalized for alias in aliases if len(alias) > 2)
        selected.append({
            "plugin": plugin_id,
            "symbol": item.get("symbol") or invocation.get("symbol"),
            "trigger": item.get("trigger"),
            "topic_hit": topic_hit,
            "status": "facts_registered_in_natal_pass_interpretation_activated_by_chart_or_topic_condition",
            "fallback": item.get("fallback"),
        })
    return selected


def _find_route(data: dict[str, Any], topic: str, timing: bool) -> tuple[str, dict[str, Any]]:
    normalized = topic.strip().lower().replace("-", "_")
    if timing:
        return "current_timing", data["routes"]["current_timing"]
    topic_map = _load_topic_map().get("routes", {})
    for route_id, route in data["routes"].items():
        if route_id == "current_timing":
            continue
        aliases = {str(item).lower().replace("-", "_") for item in topic_map.get(route_id, {}).get("match_topics", [])}
        if normalized == route_id or normalized in aliases:
            return route_id, route
    return "natal_structure", data["routes"]["natal_structure"]


def _canonical_timing_technique(value: str | None, allowed: list[str]) -> str | None:
    if value is None:
        return None
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    if key in allowed:
        return key
    implementation = TECHNIQUES.get(key)
    if implementation:
        for candidate in allowed:
            if TECHNIQUES.get(candidate) == implementation:
                return candidate
    return key


def plan(*, topic: str = "overall", has_birth_data: bool = True, timing: bool = False, timing_technique: str | None = None) -> dict[str, Any]:
    data = _load()
    if not has_birth_data:
        return {
            "schema_version": "CONSULTATION-PLAN-1.0",
            "status": "hold",
            "reason": "birth_data_required_before_chart_facts",
            "required_first": data["entrypoints"]["birth_data"]["required_first_pass"],
        }
    normalized = topic.strip().lower().replace("-", "_")
    timing_aliases = {
        str(item).lower().replace("-", "_")
        for item in _load_topic_map().get("routes", {}).get("current_timing", {}).get("match_topics", [])
    }
    if normalized in timing_aliases or normalized == "current_timing":
        if not timing:
            return {
                "schema_version": "CONSULTATION-PLAN-1.0",
                "status": "hold",
                "reason": "timing_question_requires_explicit_timing_flag",
                "required_next": "rerun_with_timing_and_one_technique",
                "allowed_techniques": data["routes"]["current_timing"].get("timing_techniques", []),
            }
    route_id, route = _find_route(data, topic, timing)
    allowed_techniques = route.get("timing_techniques", [])
    selected_technique = _canonical_timing_technique(
        timing_technique,
        allowed_techniques,
    ) or (allowed_techniques[0] if timing and allowed_techniques else None)
    if timing and selected_technique not in allowed_techniques:
        raise ValueError(f"unsupported timing technique {timing_technique!r}; choose from {allowed_techniques}")
    # Some modern insight layers are opt-in within a broad route.  They stay
    # out of ordinary natal runs, while an explicit personality/ability topic
    # gets the migrated MBTI module in the same trace as the classical pass.
    runtime_modules = list(route.get("required_modules", []))
    for alias, module_ids in route.get("topic_modules_runtime", {}).items():
        if normalized == str(alias).lower().replace("-", "_"):
            runtime_modules.extend(module_ids)
    runtime_modules = set(runtime_modules)
    modules = []
    for module_id in data["canonical_order"]:
        if module_id not in runtime_modules:
            continue
        module = data["modules"][module_id]
        status = "active"
        if module_id == "timing_extension" and not timing:
            status = "inactive_until_explicit_timing"
        if module_id == "release_gate":
            status = "blocked_until_composition"
        if module_id == "renderer":
            status = "blocked_until_release_gate"
        modules.append({
            "id": module_id,
            "version": module["version"],
            "owner": module["owner"],
            "source": module["source"],
            "technique": module.get("technique"),
            "activation": module.get("activation"),
            "status": status,
            "output": module["output"],
        })
    plugins = route.get("knowledge_plugins", [])
    conditional_plugins = _conditional_plugins(data, topic)
    normalized_topic = topic.strip().lower().replace("-", "_")
    topic_module = route.get("topic_modules", {}).get(
        normalized_topic,
        route.get("topic_module"),
    )
    return {
        "schema_version": "CONSULTATION-PLAN-1.0",
        "status": "ready",
        "route_id": route_id,
        "topic": topic,
        "timing": {
            "requested": timing,
            "technique": selected_technique,
            "policy": "natal_first_and_direct_activation_only",
        },
        "modules": modules,
        "knowledge_plugins": plugins,
        "natal_core_extensions": conditional_plugins,
        "knowledge_symbol_registry": "config/knowledge_symbols.yaml",
        "available_knowledge_symbols": _available_symbols(),
        "invocation_symbols": sorted({item.get("symbol") for item in conditional_plugins if item.get("symbol")}),
        "topic_module": topic_module,
        "guardrails": data["forbidden_shortcuts"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="overall")
    parser.add_argument("--no-birth-data", action="store_true")
    parser.add_argument("--timing", action="store_true")
    parser.add_argument("--technique")
    args = parser.parse_args()
    result = plan(topic=args.topic, has_birth_data=not args.no_birth_data, timing=args.timing, timing_technique=args.technique)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
