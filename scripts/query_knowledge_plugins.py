#!/usr/bin/env python3
"""Read-only plugin query for fast, bounded retrieval of local knowledge cards."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "references/knowledge-modules"
INTERPRETATION_REGISTRY = ROOT / "references/interpretation-modules/registry.json"

TOPIC_MODULE_ALIASES = {
    "natal": ["identity_core"],
    "overall": ["identity_core"],
    "personality": ["identity_core"],
    "ability": ["identity_core"],
    "identity": ["identity_core"],
    "money": ["wealth_income"],
    "wealth": ["wealth_income"],
    "income": ["wealth_income"],
    "property": ["wealth_income", "family_home"],
    "home": ["wealth_income", "family_home"],
    "house_purchase": ["wealth_income"],
    "real_estate": ["wealth_income"],
    "wealth_from_property": ["wealth_income"],
    "career": ["career_public_role"],
    "work": ["work_execution"],
    "relationship": ["love_relationship"],
    "love": ["love_relationship"],
    "marriage": ["love_relationship"],
    "partner": ["love_relationship"],
    "family": ["family_home"],
    "household": ["family_home"],
    "parents": ["family_home"],
    "children": ["children_education"],
    "education": ["children_education"],
    "schooling": ["children_education"],
    "parenting": ["children_education"],
    "timing": ["life_timing"],
}


def resolve_plugin_symbol(manifest: dict[str, Any], value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    for item in manifest.get("plugins", []):
        if raw == item.get("id"):
            return raw
        invocation = item.get("invocation", {})
        aliases = {str(alias).lower() for alias in invocation.get("aliases", [])}
        symbol = invocation.get("symbol")
        if symbol:
            aliases.add(str(symbol).lower())
        if raw.lower() in aliases:
            return item.get("id")
    return raw


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_plugins(manifest: dict[str, Any], plugin: str | None, topic: str | None, include_inactive: bool) -> tuple[list[dict[str, Any]], list[str]]:
    by_id = {item["id"]: item for item in manifest.get("plugins", [])}
    requested: list[dict[str, Any]] = []
    deferred: list[str] = []
    if plugin and plugin not in by_id:
        return [], [f"unknown plugin {plugin!r}; choose from {sorted(by_id)}"]
    for item in manifest.get("plugins", []):
        if plugin and item["id"] != plugin:
            continue
        topics = set(item.get("retrieval", {}).get("topics", []))
        if topic and topic not in topics and item["id"] != topic:
            continue
        if item.get("activation") == "timing_only" and not include_inactive:
            deferred.append(f"{item['id']}: timing plugin inactive; explicit timing activation required")
            continue
        if item.get("status") in {"inactive", "retired"} and not include_inactive:
            deferred.append(f"{item['id']}: plugin inactive")
            continue
        requested.append(item)
    selected_ids: set[str] = set()

    def add_with_dependencies(item: dict[str, Any]) -> None:
        if item["id"] in selected_ids:
            return
        for dependency in item.get("depends_on", []):
            dependency_item = by_id.get(dependency)
            if dependency_item is None:
                deferred.append(f"{item['id']}: missing dependency {dependency}")
                continue
            add_with_dependencies(dependency_item)
        selected_ids.add(item["id"])

    for item in requested:
        add_with_dependencies(item)
    selected = [item for item in manifest.get("plugins", []) if item["id"] in selected_ids]
    return selected, deferred


def read_cards(cards_path: Path, lines: set[int]) -> list[dict[str, Any]]:
    if not lines:
        return []
    result: list[dict[str, Any]] = []
    with cards_path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line_no in lines:
                card = json.loads(line)
                if "card_id" not in card and card.get("id"):
                    card["card_id"] = card["id"]
                if "text" not in card:
                    card["text"] = card.get("source_summary") or card.get("observable_translation") or ""
                result.append(card)
    return result


def read_topic_modules(topic: str | None, *, include_inactive: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
    """Return bounded topic templates even when no evidence-card index matches.

    Topic templates are orchestration contracts, not extra planetary facts.
    Keeping them separate from cards prevents an empty card search from being
    mistaken for a missing route or from silently falling back to free-form
    interpretation.
    """
    if not INTERPRETATION_REGISTRY.exists():
        return [], ["interpretation registry missing"]
    registry = load_json(INTERPRETATION_REGISTRY)
    modules = {item.get("id"): item for item in registry.get("modules", [])}
    selected_ids = TOPIC_MODULE_ALIASES.get(topic or "", [])
    if topic and not selected_ids:
        return [], [f"no interpretation topic module mapped for topic={topic}"]
    if not topic:
        selected_ids = list(modules)
    selected: list[dict[str, Any]] = []
    deferred: list[str] = []
    for module_id in selected_ids:
        item = modules.get(module_id)
        if not item:
            deferred.append(f"interpretation module missing: {module_id}")
            continue
        status = item.get("status")
        if status == "inactive_until_timing_activation" and not include_inactive:
            deferred.append(f"{module_id}: timing module inactive; explicit timing activation required")
            continue
        selected.append({
            "id": module_id,
            "title": item.get("title"),
            "house_chain": item.get("house_chain", []),
            "priority_policy": item.get("priority_policy"),
            "safety_gate": item.get("safety_gate"),
            "rules": item.get("rules", []),
            "counter_tests": item.get("counter_tests", []),
            "observable_tests": item.get("observable_tests", []),
            "fixed_statement": item.get("fixed_statement"),
            "status": status,
        })
    return selected, deferred


def query(*, plugin: str | None = None, symbol: str | None = None, topic: str | None = None, module: str | None = None, house: int | None = None, limit: int = 20, include_inactive: bool = False) -> dict[str, Any]:
    if limit < 0:
        raise ValueError("limit must be >= 0")
    manifest = load_json(MODULE_ROOT / "plugins.json")
    plugin = resolve_plugin_symbol(manifest, symbol) or resolve_plugin_symbol(manifest, plugin)
    index = load_json(MODULE_ROOT / "core/retrieval-index.json")
    cards_path = MODULE_ROOT / "core/cards.jsonl"
    topic = topic.strip().lower().replace("-", "_") if topic else None
    module = module.strip().lower().replace("-", "_") if module else None
    selected, deferred = select_plugins(manifest, plugin, topic, include_inactive)
    lines: set[int] | None = None
    for item in selected:
        retrieval = item.get("retrieval", {})
        constraints: list[set[int]] = []
        modules = retrieval.get("modules", [])
        if module:
            if module not in modules and module not in index.get("by_module", {}):
                deferred.append(f"{item['id']}: module={module} is not indexed")
                continue
            modules = [module]
        if modules:
            constraints.append({line for module_name in modules for line in index.get("by_module", {}).get(module_name, [])})
        if topic:
            topic_lines = set(index.get("by_topic", {}).get(topic, []))
            if not topic_lines:
                deferred.append(f"{item['id']}: no indexed cards for topic={topic}; use an explicit module route")
            constraints.append(topic_lines)
        if house is not None:
            constraints.append(set(index.get("by_house", {}).get(str(house), [])))
        if not constraints:
            if item["id"] == "natal-core":
                deferred.append("natal-core: base facts are already supplied by the chart engine; no knowledge cards loaded")
                continue
            constraints.append({line for module_name in modules for line in index.get("by_module", {}).get(module_name, [])})
        candidate = constraints[0]
        for constraint in constraints[1:]:
            candidate = candidate.intersection(constraint)
        lines = candidate if lines is None else lines.union(candidate)
    cards = read_cards(cards_path, lines or set())
    topic_modules, topic_deferred = read_topic_modules(topic, include_inactive=include_inactive)
    deferred.extend(topic_deferred)
    # A topic adapter can be valid even when the evidence-card index has no
    # direct topic tag.  Keep that as one bounded diagnostic instead of
    # repeating the same warning for every dependency in the selected graph.
    if topic_modules:
        deferred = [
            message for message in deferred
            if not message.startswith("interpretation-topic-adapters: no indexed cards for topic=")
        ]
    deferred = list(dict.fromkeys(deferred))
    if limit > 0:
        cards = cards[:limit]
    return {
        "schema_version": "KNOWLEDGE-QUERY-0.1",
        "plugins": [{
            "id": p["id"],
            "version": p["version"],
            "status": p["status"],
            "grade_cap": p["grade_cap"],
            "judgment_utility": p.get("judgment_utility"),
            "event_domains": p.get("event_domains", []),
            "event_mechanism": p.get("event_mechanism"),
            "non_judgment_use": p.get("non_judgment_use"),
            "module_policy": p.get("module_policy", {}),
            "artifacts": p.get("artifacts", []),
            "invocation": p.get("invocation", {}),
            "retrieval": p.get("retrieval", {}),
        } for p in selected],
        "cards": cards,
        "topic_modules": topic_modules,
        "deferred": deferred,
        "guardrails": [
            "natal-core runs first",
            "plugin evidence cannot override Chart Facts or typed reception",
            "all cards remain bounded by their declared grade_cap",
            "sign/planet/house meanings are intermediate variables; use only with an event mechanism and observable translation",
            "context_only/deferred material cannot enter a core judgment",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin")
    parser.add_argument("--symbol", help="high-efficiency invocation symbol, e.g. @PLO")
    parser.add_argument("--topic")
    parser.add_argument("--module")
    parser.add_argument("--house", type=int)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--include-inactive", action="store_true")
    args = parser.parse_args()
    print(json.dumps(query(plugin=args.plugin, symbol=args.symbol, topic=args.topic, module=args.module, house=args.house, limit=args.limit, include_inactive=args.include_inactive), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
