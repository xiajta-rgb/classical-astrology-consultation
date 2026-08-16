#!/usr/bin/env python3
"""Continuous, bounded discovery + crawl + cluster loop.

Each invocation runs several resumable rounds. It discovers a small number of
URLs from a query pool, deduplicates them into the source queue, crawls a
bounded batch, and records state. It never promotes external material.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from auto_research_loop import run as crawl_run
from cluster_research_extracts import DEFAULT_AUTO_INPUT, cluster, load_jsonl, normalize_auto_rows, rejected_source_ids


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "references/research-loop"
QUERY_FILE = LOOP / "discovery-queries.jsonl"
QUEUE_FILE = LOOP / "source-queue.jsonl"
STATE_FILE = LOOP / "continuous-loop-state.json"
CLUSTER_FILE = LOOP / "clustered-auto-extracts.json"

TRUSTED_HOSTS = {
    "skyscript.co.uk", "theastrologypodcast.com", "gutenberg.org", "archive.org",
    "reddit.com", "traditional-astrology.com", "augurine.com", "keplercollege.org",
    "dejathejovian.com", "constellationsofwords.com", "medievalastrologyguide.com",
}
BLOCKED_HOSTS = {
    "yahoo.com", "yahoo.co.jp", "youtube.com", "music.youtube.com", "facebook.com",
    "instagram.com", "marketwatch.com", "investing.com", "tradingview.com",
    "sports.yahoo.com", "finance.yahoo.com", "weather.yahoo.com", "astrology.com",
    "astro.com", "cafeastrology.com", "wikipedia.org", "astrosage.com", "astro-seek.com",
    "horoscope.com", "astrologyzone.com",
}
TOPIC_HINTS = (
    "astro", "zodiac", "horoscope", "ephemer", "fixed-star", "astrology",
    "hellenistic", "profection", "reception", "dignit", "bonification",
    "maltreatment", "lot-of", "lots", "traditional-astrology", "time-lord",
    "firdaria", "primary-text",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"schema_version": "CONTINUOUS-LOOP-STATE-0.1", "query_cursor": 0, "runs": [], "seen_urls": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relevant_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    if any(host == blocked or host.endswith("." + blocked) for blocked in BLOCKED_HOSTS):
        return False
    if any(host == trusted or host.endswith("." + trusted) for trusted in TRUSTED_HOSTS):
        return True
    haystack = (host + parsed.path).lower()
    return any(term in haystack for term in TOPIC_HINTS)


def quarantine_existing() -> int:
    """Mark previously discovered off-topic URLs without deleting them."""
    rows = load_jsonl(QUEUE_FILE)
    changed = 0
    for row in rows:
        if row.get("source_tier") == "discovery" and row.get("status") == "candidate" and not relevant_url(str(row.get("url", ""))):
            row["status"] = "rejected_noise"
            row["rejection_reason"] = "automatic discovery relevance gate"
            changed += 1
    if changed:
        QUEUE_FILE.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return changed


def discover(query: str, timeout: int) -> list[str]:
    found: list[str] = []
    engines = [
        "https://www.bing.com/search?q=" + quote_plus(query) + "&count=10",
        "https://www.google.com/search?q=" + quote_plus(query),
    ]
    for search_url in engines:
        request = Request(search_url, headers={"User-Agent": "Mozilla/5.0 (compatible; research-loop/0.1)"})
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read(500_000).decode("utf-8", errors="replace")
        except Exception:
            continue
        hrefs = re.findall(r'<li class="b_algo".*?<a href="([^"]+)"', body, flags=re.IGNORECASE | re.DOTALL)
        hrefs += re.findall(r'href="([^"]+)"', body)
        for href in hrefs:
            if len(found) >= 8:
                break
            candidate = href
            if candidate.startswith("/url?"):
                candidate = parse_qs(urlparse(candidate).query).get("q", [""])[0]
            candidate = unquote(candidate)
            if "bing.com/ck/a" in candidate:
                encoded = parse_qs(urlparse(html.unescape(candidate)).query).get("u", [""])[0]
                if encoded.startswith("a1"):
                    try:
                        candidate = base64.b64decode(encoded[2:] + "===").decode("utf-8", errors="ignore")
                    except Exception:
                        continue
            parsed = urlparse(candidate)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc.lower().endswith(("google.com", "bing.com", "microsoft.com")):
                continue
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if not relevant_url(clean):
                continue
            if clean not in found:
                found.append(clean)
        if found:
            break
    return found


def append_sources(urls: list[str], query_id: str, seen_urls: set[str]) -> list[dict]:
    existing_rows = load_jsonl(QUEUE_FILE)
    existing_urls = {str(row.get("url", "")).rstrip("/") for row in existing_rows}
    added: list[dict] = []
    with QUEUE_FILE.open("a", encoding="utf-8", newline="\n") as handle:
        for url in urls:
            normalized = url.rstrip("/")
            if normalized in existing_urls or normalized in seen_urls or not relevant_url(normalized):
                continue
            parsed = urlparse(normalized)
            source_id = "DISC-" + hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
            row = {
                "source_id": source_id,
                "source_type": "discovered_web",
                "source_tier": "discovery",
                "title": parsed.netloc + parsed.path,
                "url": normalized,
                "status": "candidate",
                "discovered_by": query_id,
                "upgrade_rule": "manual source identification, locator, counter-test and chart regression required",
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            existing_urls.add(normalized)
            seen_urls.add(normalized)
            added.append(row)
    return added


def run(rounds: int, pages_per_round: int, timeout: int, run_id: str) -> dict:
    queries = load_jsonl(QUERY_FILE)
    quarantined = quarantine_existing()
    state = load_state()
    seen_urls = set(state.get("seen_urls", []))
    query_cursor = int(state.get("query_cursor", 0))
    round_records: list[dict] = []
    for round_no in range(1, rounds + 1):
        if not queries:
            break
        query = queries[query_cursor % len(queries)]
        query_cursor += 1
        discovered = discover(str(query.get("query", "")), timeout)
        added = append_sources(discovered, str(query.get("query_id", "unknown")), seen_urls)
        crawl = crawl_run(pages_per_round, timeout, f"{run_id}-R{round_no:02d}")
        manual_rows = load_jsonl(LOOP / "candidate-extracts.jsonl")
        rejected = rejected_source_ids()
        auto_rows = [
            row for row in normalize_auto_rows(load_jsonl(DEFAULT_AUTO_INPUT))
            if str(row.get("source_id", "")) not in rejected
        ] if DEFAULT_AUTO_INPUT.exists() else []
        rows = manual_rows + auto_rows
        clustered = cluster(rows)
        CLUSTER_FILE.write_text(json.dumps(clustered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        round_records.append({
            "round": round_no,
            "query_id": query.get("query_id"),
            "discovered_urls": len(discovered),
            "new_sources": len(added),
            "crawled_sources": crawl.get("processed", 0),
            "cluster_counts": clustered.get("counts", {}),
            "completed_at": now(),
        })
        state["query_cursor"] = query_cursor
        state["seen_urls"] = sorted(seen_urls)
        state["runs"].append({"run_id": run_id, **round_records[-1]})
        save_state(state)
        time.sleep(0.5)
    state["query_cursor"] = query_cursor
    state["seen_urls"] = sorted(seen_urls)
    save_state(state)
    return {"run_id": run_id, "rounds": round_records, "query_cursor": query_cursor, "query_count": len(queries), "quarantined_noise": quarantined}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now().strftime("CONT-%Y%m%d-%H%M%S"))
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--pages-per-round", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 6:
        parser.error("--rounds must be between 1 and 6")
    result = run(args.rounds, args.pages_per_round, args.timeout, args.run_id)
    print(f"PASS continuous research loop: {len(result['rounds'])} rounds; query cursor {result['query_cursor']}/{result['query_count']}; quarantined {result['quarantined_noise']} noise URLs")
    for record in result["rounds"]:
        print(f"- {record['query_id']}: +{record['new_sources']} sources, crawled {record['crawled_sources']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
