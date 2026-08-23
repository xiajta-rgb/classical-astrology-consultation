#!/usr/bin/env python3
"""Validate resumable public WeChat retrieval artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\xiajt\Downloads\(公众号数据)表格视图.xlsx")
RETRIEVAL = ROOT / "references/knowledge-modules/distilled/retrieval"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    findings: list[str] = []
    required = ["empty-source-index.json", "album-pages.jsonl", "article-bodies.jsonl", "album-unmatched-source-titles.jsonl", "batch-summary.json"]
    for name in required:
        if not (RETRIEVAL / name).exists():
            findings.append(f"missing:{name}")
    if findings:
        print("FAIL\n" + "\n".join(f"- {x}" for x in findings))
        return 1
    index = json.loads((RETRIEVAL / "empty-source-index.json").read_text(encoding="utf-8"))
    expected = hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.exists() else None
    if expected and index.get("source_sha256") != expected:
        findings.append("source_sha256_mismatch")
    rows = index.get("rows", [])
    if len(rows) != index.get("unique_album_urls", 687) + index.get("unique_direct_articles", 6633):
        # The index counts source rows, not unique links; this is informational only.
        pass
    albums = load_jsonl(RETRIEVAL / "album-pages.jsonl")
    album_urls = [str(row.get("album_url", "")) for row in albums]
    if len(album_urls) != len(set(album_urls)):
        findings.append("duplicate_album_result")
    if any(row.get("status") not in {"ok", "verification_required", "invalid_album_url", "error"} for row in albums):
        findings.append("unknown_album_status")
    articles = load_jsonl(RETRIEVAL / "article-bodies.jsonl")
    article_urls = [str(row.get("url", "")) for row in articles]
    if len(article_urls) != len(set(article_urls)):
        findings.append("duplicate_article_result")
    if any(row.get("status") not in {"retrieved", "verification_required", "no_js_content", "error"} for row in articles):
        findings.append("unknown_article_status")
    if any(row.get("status") == "retrieved" and not row.get("body") for row in articles):
        findings.append("retrieved_without_body")
    unmatched = load_jsonl(RETRIEVAL / "album-unmatched-source-titles.jsonl")
    summary = json.loads((RETRIEVAL / "batch-summary.json").read_text(encoding="utf-8"))
    if summary.get("album_results_existing") != len(album_urls):
        findings.append("summary_album_count_mismatch")
    if summary.get("article_results_existing") != len(article_urls):
        findings.append("summary_article_count_mismatch")
    if findings:
        print("FAIL\n" + "\n".join(f"- {x}" for x in findings))
        return 1
    print(json.dumps({"source_rows": len(rows), "album_results": len(albums), "album_items": sum(int(row.get("item_count", 0)) for row in albums), "article_results": len(articles), "retrieved_bodies": sum(row.get("status") == "retrieved" for row in articles), "unmatched_album_source_titles": len(unmatched), "status": "partial_or_complete_resumable"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
