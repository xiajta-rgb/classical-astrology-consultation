#!/usr/bin/env python3
"""Fail-soft, resumable metadata crawler for the research-loop queue.

It never stores full webpages and never promotes a claim. Each run processes a
bounded number of sources, checkpoints after every source, and continues after
timeouts, HTTP errors, binary PDFs, or malformed pages.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "references/research-loop"
QUEUE = LOOP / "source-queue.jsonl"
STATE = LOOP / "auto-loop-state.json"
EXTRACTS = LOOP / "auto-extracts.jsonl"

KEYWORDS = {
    "house": ["house", "宫", "houses"],
    "career": ["career", "profession", "employment", "事业", "职业"],
    "relationship": ["marriage", "love", "relationship", "婚姻", "关系"],
    "friendship": ["friend", "friendship", "allies", "友情", "朋友"],
    "travel": ["travel", "journey", "foreign", "migration", "旅行", "迁移"],
    "timing": ["timing", "profection", "transit", "time-lord", "时限", "推运"],
    "fixed_stars": ["fixed star", "fixed stars", "恒星"],
    "lots": ["lot of fortune", "lot", "parts", "福点", "阿拉伯点"],
}


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.description = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "meta":
            name = data.get("name", "").lower()
            prop = data.get("property", "").lower()
            if name in {"description", "og:description"} or prop == "og:description":
                self.description = data.get("content", "")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.title_parts))).strip()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def keyword_hits(text: str) -> dict[str, list[str]]:
    lowered = text.lower()
    hits: dict[str, list[str]] = {}
    for group, terms in KEYWORDS.items():
        found = [term for term in terms if term.lower() in lowered]
        if found:
            hits[group] = sorted(set(found))
    return hits


def fetch_metadata(url: str, timeout: int) -> dict:
    request = Request(url, headers={"User-Agent": "classical-astrology-research-loop/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
            if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                return {"status": "deferred_binary", "content_type": content_type, "final_url": final_url}
            raw = response.read(300_000)
            parser = MetaParser()
            parser.feed(raw.decode("utf-8", errors="replace"))
            title = parser.title
            description = re.sub(r"\s+", " ", html.unescape(parser.description)).strip()[:500]
            hits = keyword_hits(" ".join((title, description, final_url)))
            return {
                "status": "candidate_metadata",
                "content_type": content_type,
                "final_url": final_url,
                "title": title,
                "description": description,
                "keyword_hits": hits,
            }
    except HTTPError as exc:
        return {"status": "http_error", "error": f"HTTP {exc.code}"}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": "fetch_error", "error": str(exc)[:240]}
    except Exception as exc:  # fail-soft: one malformed page must not stop the queue
        return {"status": "parse_error", "error": str(exc)[:240]}


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"schema_version": "AUTO-LOOP-STATE-0.1", "cursor": 0, "processed": {}, "runs": []}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_extract(row: dict) -> None:
    with EXTRACTS.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(max_pages: int, timeout: int, run_id: str) -> dict:
    sources = load_jsonl(QUEUE)
    state = load_state()
    state["queue_sha256"] = hashlib.sha256(QUEUE.read_bytes()).hexdigest()
    cursor = int(state.get("cursor", 0))
    processed = state.setdefault("processed", {})
    outcomes = []
    inspected = 0
    while cursor < len(sources) and inspected < max_pages:
        source = sources[cursor]
        source_id = str(source.get("source_id", f"row-{cursor}"))
        cursor += 1
        if source_id in processed and processed[source_id].get("status") in {"candidate_metadata", "deferred_binary", "http_error", "fetch_error", "parse_error"}:
            continue
        result = fetch_metadata(str(source.get("url", "")), timeout)
        record = {
            "extract_id": f"AUTO-{run_id}-{inspected + 1:03d}",
            "source_id": source_id,
            "retrieved_at": now(),
            "status": result.get("status", "unknown"),
            "grade_cap": "C",
            "title": result.get("title", source.get("title", "")),
            "description": result.get("description", ""),
            "keyword_hits": result.get("keyword_hits", {}),
            "url": result.get("final_url", source.get("url")),
            "source_tier": source.get("source_tier"),
            "error": result.get("error"),
            "promotion": "blocked_until_manual_source_review",
        }
        append_extract(record)
        processed[source_id] = {"status": record["status"], "retrieved_at": record["retrieved_at"], "url": record["url"]}
        outcomes.append(record)
        inspected += 1
        state["cursor"] = cursor
        save_state(state)
        time.sleep(0.2)
    state["cursor"] = cursor
    state["runs"].append({"run_id": run_id, "started_at": now(), "max_pages": max_pages, "processed": len(outcomes), "outcomes": [{"source_id": r["source_id"], "status": r["status"]} for r in outcomes]})
    save_state(state)
    return {"run_id": run_id, "processed": len(outcomes), "cursor": cursor, "queue_size": len(sources), "outcomes": outcomes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now().strftime("AUTO-%Y%m%d-%H%M%S"))
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 20:
        parser.error("--max-pages must be between 1 and 20")
    result = run(args.max_pages, args.timeout, args.run_id)
    print(f"PASS auto research loop: processed {result['processed']} sources; cursor {result['cursor']}/{result['queue_size']}")
    for row in result["outcomes"]:
        print(f"- {row['source_id']}: {row['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
