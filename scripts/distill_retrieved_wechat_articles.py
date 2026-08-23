#!/usr/bin/env python3
"""Distill successfully retrieved public article bodies without replacing R60 cards."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any

import distill_wechat_astrology as base


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "references/knowledge-modules/distilled/retrieval/article-bodies.jsonl"
DEFAULT_OUTPUT = ROOT / "references/knowledge-modules/distilled/retrieved-distilled"


def source_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def build(input_path: Path, output_dir: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        url = str(row.get("url", ""))
        if row.get("status") != "retrieved" or not row.get("body") or not url or url in seen_urls:
            continue
        seen_urls.add(url)
        body = base.clean(str(row.get("body", "")))
        cleaned = base.strip_marketing(body)
        spans = base.structured_spans(cleaned)
        title = base.clean(row.get("title") or row.get("title_from_page") or "")
        reason = base.exclusion_reason(title, body, cleaned, spans)
        source_rows = row.get("source_rows") or ([row.get("row")] if row.get("row") else [])
        records.append({"row": source_rows[0] if source_rows else 0, "source_rows": source_rows, "title": title, "body": body, "cleaned_body": cleaned, "link": url, "account": row.get("account", ""), "published_at": row.get("published_at", ""), "spans": spans, "reason": reason, "retrieval_status": row.get("status"), "album_id": row.get("album_id", "")})

    source_sha = hashlib.sha256(input_path.read_bytes()).hexdigest()
    cards: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    exclusion_counts: collections.Counter[str] = collections.Counter()
    for item in records:
        if item["reason"]:
            exclusion_counts[item["reason"]] += 1
            exclusions.append({"id": f"R60R-{source_hash(item['link'])}", "title": item["title"], "url": item["link"], "source_rows": item["source_rows"], "reason": item["reason"], "span_count": len(item["spans"]), "retrieval_status": item["retrieval_status"]})
            continue
        timing = bool(base.TIMING_TERMS.search(item["title"] + " " + item["cleaned_body"]))
        modern = bool(base.MODERN_TERMS.search(item["title"] + " " + item["cleaned_body"]))
        cards.append({
            "id": f"R60R-{source_hash(item['link'])}",
            "source_ids": ["R60"],
            "source_locator": {"workbook": "(公众号数据)表格视图.xlsx", "sheet": "retrieved_public_article", "rows": item["source_rows"], "title": item["title"], "url": item["link"], "published_at": item["published_at"], "retrieval_status": item["retrieval_status"], "retrieval_sha256": source_sha},
            "module": "article_distillation_retrieved",
            "kind": "condition_mechanism_candidate",
            "title": item["title"],
            "text": "；".join(span["source_span"] for span in item["spans"]),
            "claims": item["spans"],
            "topics": base.topics_for(item["title"] + " " + item["cleaned_body"]),
            "source_metadata": {"account": item["account"], "body_length": len(item["body"]), "source_rows": item["source_rows"], "album_id": item["album_id"], "extraction": "retrieved_public_html_verbatim_clause_pairing"},
            "conditions": ["source is a publicly retrieved WeChat article body; provenance and edition remain external to this workbook", "lock Chart Facts, zodiac, house system and aspect version before comparison", "this card preserves retrieved source spans and does not validate their astrological truth", "a sign, planet, house or aspect label is not sufficient evidence without responsibility-chain context"],
            "counter_test": "recalculate the chart facts, compare at least two independent cases and seek a disconfirming case; reject generic or anecdotal claims that do not survive the project evidence gate",
            "grade_cap": "C",
            "status": "deferred" if timing else "candidate",
            "activation": "explicit_timing_only" if timing else "explicit_topic_only",
            "safety_gate": "G0_sensitive_topic_gate",
            "modern_extension": modern,
            "timing_extension": timing,
            "source_tier": "secondary_user_provided_corpus_retrieved_publicly",
            "non_judgment_use": "research candidate and retrieval hint only; never a standalone natal conclusion, diagnosis, event guarantee or timing date",
            "version": "WECHAT-ARTICLE-RETRIEVED-DISTILL-2026-08-23-1",
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "cards.jsonl").write_text("".join(json.dumps(card, ensure_ascii=False) + "\n" for card in cards), encoding="utf-8")
    (output_dir / "exclusions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in exclusions), encoding="utf-8")
    manifest = {"schema_version": "ARTICLE-DISTILLATION-RETRIEVED-0.1", "source_id": "R60", "input": str(input_path), "input_sha256": source_sha, "counts": {"retrieved_records_seen": len(records), "candidate_cards": len(cards), "excluded_records": len(exclusions), "exclusion_counts": dict(exclusion_counts)}, "status": "candidate_only", "grade_cap": "C", "policy": "This store supplements, never overwrites, the original workbook distillation; no automatic core/runtime promotion."}
    (output_dir / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.input, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
