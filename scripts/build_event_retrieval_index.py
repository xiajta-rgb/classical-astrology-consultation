#!/usr/bin/env python3
"""Build a bidirectional event<->significator retrieval layer.

The canonical card store remains cards.jsonl.  This layer adds conservative
candidate links based on explicit house metadata (house-flow cards and house
pairs).  It is a retrieval aid, not an interpretation or a proof engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARDS = ROOT / "references/knowledge-modules/core/cards.jsonl"
DEFAULT_CLUSTERS = ROOT / "references/knowledge-modules/event-clusters.json"
DEFAULT_LINKS = ROOT / "references/knowledge-modules/event-links.jsonl"
DEFAULT_INDEX = ROOT / "references/knowledge-modules/event-retrieval-index.json"


def _card_houses(card: dict[str, Any]) -> set[int]:
    houses: set[int] = set()
    for key in ("from_house", "to_house"):
        value = card.get(key)
        if isinstance(value, int):
            houses.add(value)
    pair = card.get("pair")
    if pair:
        for part in str(pair).replace("-", " ").split():
            if part.isdigit() and 1 <= int(part) <= 12:
                houses.add(int(part))
    return houses


def _load_cards(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            rows.append((line_no, json.loads(line)))
    return rows


def build(cards_path: Path, clusters_path: Path, links_path: Path, index_path: Path) -> dict[str, Any]:
    clusters_doc = json.loads(clusters_path.read_text(encoding="utf-8"))
    clusters = {item["id"]: item for item in clusters_doc["clusters"]}
    cards = _load_cards(cards_path)
    links: list[dict[str, Any]] = []
    by_event: dict[str, list[str]] = {event_id: [] for event_id in clusters}
    by_card: dict[str, list[str]] = {}

    for line_no, card in cards:
        houses = _card_houses(card)
        if not houses:
            continue
        for event_id, event in clusters.items():
            primary = set(event.get("primary_houses", []))
            secondary = set(event.get("secondary_houses", []))
            primary_overlap = sorted(houses & primary)
            secondary_overlap = sorted(houses & secondary)
            if not primary_overlap and not secondary_overlap:
                continue
            relation = "primary_house_overlap" if primary_overlap else "secondary_house_overlap"
            overlap = primary_overlap or secondary_overlap
            link_id = f"LINK-{event_id}-{card['id']}"
            link = {
                "link_id": link_id,
                "event_id": event_id,
                "card_id": card["id"],
                "card_line": line_no,
                "relation": relation,
                "overlapping_houses": overlap,
                "candidate_grade_cap": clusters_doc["policy"].get("default_grade_cap", "C"),
                "status": "candidate_retrieval_only",
                "independence_group": "event_house_overlap",
                "warning": "Do not treat event linkage as proof; recheck ruler state, independent testimony, and timing.",
            }
            links.append(link)
            by_event[event_id].append(card["id"])
            by_card.setdefault(card["id"], []).append(event_id)

    links_path.parent.mkdir(parents=True, exist_ok=True)
    links_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in links), encoding="utf-8")
    index = {
        "schema_version": "EVENT-RETRIEVAL-0.1",
        "canonical_cards": str(cards_path.relative_to(ROOT)),
        "event_registry": str(clusters_path.relative_to(ROOT)),
        "event_links": str(links_path.relative_to(ROOT)),
        "counts": {"cards": len(cards), "links": len(links), "events": len(clusters), "linked_cards": len(by_card)},
        "by_event": {key: sorted(set(value)) for key, value in by_event.items()},
        "by_card": {key: sorted(set(value)) for key, value in by_card.items()},
        "retrieval_guardrail": "Event-first retrieval proposes cards; chart facts and independent evidence decide the conclusion.",
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--clusters", type=Path, default=DEFAULT_CLUSTERS)
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    parser.add_argument("--output", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    index = build(args.cards, args.clusters, args.links, args.output)
    print(f"PASS event retrieval index: {index['counts']['events']} events, {index['counts']['links']} candidate links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
