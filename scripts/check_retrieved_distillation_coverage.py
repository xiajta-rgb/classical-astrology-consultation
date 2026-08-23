#!/usr/bin/env python3
"""Audit whether every successfully retrieved article has a persisted disposition.

This is an article-level completeness check, not a truth or core-promotion check:
each retrieved body must end up in either a candidate card or an explicit
exclusion record. Verification failures and parser failures remain pending.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL = ROOT / "references/knowledge-modules/distilled/retrieval/article-bodies.jsonl"
DISTILLED = ROOT / "references/knowledge-modules/distilled/retrieved-distilled"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    results = load_jsonl(RETRIEVAL)
    cards = load_jsonl(DISTILLED / "cards.jsonl")
    exclusions = load_jsonl(DISTILLED / "exclusions.jsonl")

    retrieved = {str(row.get("url")): row for row in results if row.get("status") == "retrieved" and row.get("body")}
    disposition_urls = {str(row.get("url")) for row in cards + exclusions if row.get("url")}
    missing = sorted(url for url in retrieved if url not in disposition_urls)
    claim_count = sum(len(card.get("claims") or []) for card in cards)
    statuses: dict[str, int] = {}
    for row in results:
        status = str(row.get("status", ""))
        statuses[status] = statuses.get(status, 0) + 1
    report = {
        "retrieval_results": len(results),
        "retrieval_statuses": statuses,
        "retrieved_bodies": len(retrieved),
        "candidate_cards": len(cards),
        "explicit_exclusions": len(exclusions),
        "persisted_claim_spans": claim_count,
        "retrieved_without_disposition": len(missing),
        "missing_urls_sample": missing[:20],
        "pending_nonretrieved": sum(count for status, count in statuses.items() if status != "retrieved"),
        "status": "pass" if not missing else "fail",
        "interpretation": "article-level disposition coverage only; does not validate astrological truth or promote any card to core knowledge",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
