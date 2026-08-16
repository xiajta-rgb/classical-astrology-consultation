#!/usr/bin/env python3
"""Build a compact retrieval index for the canonical knowledge-card JSONL store."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARDS = ROOT / "references/knowledge-modules/core/cards.jsonl"
DEFAULT_OUTPUT = ROOT / "references/knowledge-modules/core/retrieval-index.json"


def add(mapping: dict[str, list[int]], key: Any, line_no: int) -> None:
    if key is None or key == "":
        return
    value = str(key)
    if line_no not in mapping.setdefault(value, []):
        mapping[value].append(line_no)


def build(cards_path: Path, output_path: Path) -> dict[str, Any]:
    by_id: dict[str, int] = {}
    by_module: dict[str, list[int]] = {}
    by_kind: dict[str, list[int]] = {}
    by_source: dict[str, list[int]] = {}
    by_topic: dict[str, list[int]] = {}
    by_house: dict[str, list[int]] = {}
    counts: dict[str, int] = defaultdict(int)
    digest = hashlib.sha256()

    with cards_path.open("rb") as raw:
        for line_no, raw_line in enumerate(raw, start=1):
            digest.update(raw_line)
            if not raw_line.strip():
                continue
            card = json.loads(raw_line.decode("utf-8"))
            card_id = card.get("id")
            if not card_id:
                raise ValueError(f"card line {line_no} missing id")
            if card_id in by_id:
                raise ValueError(f"duplicate card id: {card_id}")
            by_id[card_id] = line_no
            counts["all_records"] += 1
            add(by_module, card.get("module"), line_no)
            add(by_kind, card.get("kind"), line_no)
            for source_id in card.get("source_ids", []):
                add(by_source, source_id, line_no)
            topics = set(card.get("topics", []))
            module = card.get("module")
            if module:
                topics.add(module)
            if card.get("kind") == "house_flow_hypothesis":
                topics.update({"house_flow", "rulership", "fly_in"})
            if card.get("kind") == "mutual_reception_house_pair":
                topics.update({"mutual_reception", "house_pair"})
            for topic in topics:
                add(by_topic, topic, line_no)
            for house_key in ("from_house", "to_house"):
                if card.get(house_key) is not None:
                    add(by_house, card[house_key], line_no)
            pair = card.get("pair")
            if pair:
                for part in str(pair).replace("–", "-").split("-"):
                    if part.isdigit():
                        add(by_house, part, line_no)

    index = {
        "schema_version": "KNOWLEDGE-RETRIEVAL-0.1",
        "canonical_store": "core/cards.jsonl",
        "card_fingerprint_sha256": digest.hexdigest(),
        "counts": dict(counts),
        "by_id": by_id,
        "by_module": by_module,
        "by_kind": by_kind,
        "by_source": by_source,
        "by_topic": by_topic,
        "by_house": by_house,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    index = build(args.cards, args.output)
    print(f"PASS retrieval index: {index['counts']['all_records']} cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
