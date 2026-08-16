#!/usr/bin/env python3
"""Choose a retrieval route for a consultation task.

This planner decides whether to enter through significators, event clusters,
or both. It does not interpret a chart and does not score evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLUSTERS = ROOT / "references/knowledge-modules/event-clusters.json"
DEFAULT_INDEX = ROOT / "references/knowledge-modules/event-retrieval-index.json"

TASK_ROUTES = {
    "natal_structure": {
        "entry": "significator_first",
        "steps": ["validate_chart_facts", "retrieve_house_and_ruler_cards", "retrieve_matching_event_clusters_as_enrichment", "cross_check_independent_testimonies"],
    },
    "event_validation": {
        "entry": "event_first",
        "steps": ["normalize_real_world_event", "retrieve_event_cluster_links", "map_links_back_to_houses_and_rulers", "check_chart_facts_and_counter_testimonies"],
    },
    "comparison": {
        "entry": "dual_entry",
        "steps": ["retrieve_significator_cards", "retrieve_event_cluster_links", "compare_system_or_chart_variants", "keep_convergent_and_conflicting_evidence_separate"],
    },
    "timing": {
        "entry": "event_first_then_timing",
        "steps": ["normalize_event_and_exact_date", "retrieve_event_cluster_links", "activate_only_documented_timing_method", "require_natal_and_timing_convergence"],
    },
}


def plan(task: str, event_ids: list[str], houses: list[int], clusters_path: Path, index_path: Path) -> dict[str, Any]:
    clusters_doc = json.loads(clusters_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    definitions = {item["id"]: item for item in clusters_doc["clusters"]}
    selected = []
    for event_id in event_ids:
        if event_id not in definitions:
            raise ValueError(f"unknown event cluster: {event_id}")
        selected.append({
            "event_id": event_id,
            "label": definitions[event_id].get("label"),
            "candidate_card_ids": index.get("by_event", {}).get(event_id, []),
        })
    return {
        "task": task,
        "route": TASK_ROUTES[task],
        "event_clusters": selected,
        "house_entry": sorted(set(house for house in houses if 1 <= house <= 12)),
        "guardrails": [
            "candidate retrieval only",
            "do not count an event link as independent testimony",
            "retain source, grade cap, ruler state, sect, and timing status",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=sorted(TASK_ROUTES), required=True)
    parser.add_argument("--event", action="append", default=[])
    parser.add_argument("--house", action="append", type=int, default=[])
    parser.add_argument("--clusters", type=Path, default=DEFAULT_CLUSTERS)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    print(json.dumps(plan(args.task, args.event, args.house, args.clusters, args.index), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
