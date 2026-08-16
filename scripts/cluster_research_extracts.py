#!/usr/bin/env python3
"""Deterministic first-pass clustering for external research extracts.

This is intentionally lexical and auditable. It proposes clusters; it does not
promote a claim into the core knowledge store.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "references/research-loop/candidate-extracts.jsonl"
DEFAULT_OUTPUT = ROOT / "references/research-loop/clustered-extracts.json"
DEFAULT_AUTO_INPUT = ROOT / "references/research-loop/auto-extracts.jsonl"
DEFAULT_QUEUE = ROOT / "references/research-loop/source-queue.jsonl"

TERM_MAP = {
    "EVT-SELF-BODY-IDENTITY": ["self", "body", "identity", "agency", "主体", "身体"],
    "EVT-COMMUNICATION-LEARNING": ["communication", "learning", "education", "3rd", "沟通", "教育"],
    "EVT-TRAVEL-RELOCATION-FOREIGN": ["travel", "migration", "relocation", "foreign", "远行", "迁移"],
    "EVT-LEGAL-DISPUTE-ENEMIES": ["legal", "litigation", "dispute", "enemy", "诉讼", "法律"],
    "EVT-ISOLATION-INSTITUTION-CONFINEMENT": ["isolation", "institution", "confinement", "隔离", "机构"],
    "EVT-ACUTE-ACCIDENT-CRISIS": ["accident", "emergency", "crisis", "事故", "急性", "危机"],
    "EVT-DEBT-INHERITANCE-SHARED-FINANCE": ["debt", "inheritance", "tax", "shared finance", "债务", "继承"],
    "EVT-CREATIVE-PLEASURE-SPECULATION": ["creative", "pleasure", "speculation", "创作", "投机"],
    "EVT-LOVE-ROMANCE": ["love", "romance", "dating", "爱情", "恋爱"],
    "EVT-MARRIAGE-COMMITMENT": ["marriage", "commitment", "婚姻"],
    "EVT-RELATIONSHIP-CONFLICT-SEPARATION": ["conflict", "separation", "divorce", "冲突", "分离"],
    "EVT-FRIENDSHIP-SOCIAL-NETWORK": ["friendship", "friends", "network", "友情", "朋友", "社交"],
    "EVT-WORK-EMPLOYMENT-ROUTINE": ["work", "employment", "labor", "daily", "工作", "雇佣"],
    "EVT-CAREER-PUBLIC-STATUS": ["career", "public", "reputation", "authority", "事业", "名望"],
    "EVT-ACADEMIC-CAREER": ["academic", "research", "teaching", "professor", "学术", "科研"],
}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row must be an object at {path}:{line_no}")
        rows.append(row)
    return rows


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def lexical_matches(row: dict) -> list[tuple[str, list[str]]]:
    haystack = normalize(" ".join(str(row.get(key, "")) for key in ("claim", "faithful_summary", "candidate_mechanism")))
    explicit = {str(item) for item in row.get("event_clusters", []) if item}
    matches: list[tuple[str, list[str]]] = []
    for cluster_id, terms in TERM_MAP.items():
        hit_terms = [term for term in terms if normalize(term) in haystack]
        if cluster_id in explicit or hit_terms:
            matches.append((cluster_id, sorted(set(hit_terms))))
    return matches


def cluster(rows: list[dict]) -> dict:
    by_cluster: dict[str, list[dict]] = defaultdict(list)
    unassigned: list[str] = []
    for row in rows:
        extract_id = str(row.get("extract_id", ""))
        matches = lexical_matches(row)
        if not matches:
            unassigned.append(extract_id)
            continue
        for cluster_id, hit_terms in matches:
            by_cluster[cluster_id].append({
                "extract_id": extract_id,
                "source_id": row.get("source_id"),
                "status": row.get("status", "candidate"),
                "grade_cap": row.get("grade_cap", "C"),
                "hit_terms": hit_terms,
                "counter_test": row.get("counter_test"),
            })
    return {
        "schema_version": "RESEARCH-CLUSTER-0.1",
        "method": "explicit_event_tags_plus_auditable_lexical_proposal",
        "promotion_policy": "clusters_propose_research_targets; they do not prove chart events",
        "counts": {
            "extracts": len(rows),
            "clusters_with_hits": len(by_cluster),
            "unassigned": len(unassigned),
            "candidate_links": sum(len(items) for items in by_cluster.values()),
        },
        "clusters": {key: value for key, value in sorted(by_cluster.items())},
        "unassigned_extracts": unassigned,
    }


def normalize_auto_rows(rows: list[dict]) -> list[dict]:
    """Map crawler metadata into the same candidate schema without promotion."""
    normalized = []
    for row in rows:
        item = dict(row)
        item.setdefault("claim", item.get("title", ""))
        item.setdefault("faithful_summary", item.get("description", ""))
        item.setdefault("candidate_mechanism", "auto_metadata_keyword_lead")
        item.setdefault("event_clusters", [])
        normalized.append(item)
    return normalized


def rejected_source_ids(path: Path = DEFAULT_QUEUE) -> set[str]:
    """Return source IDs quarantined by the discovery relevance gate."""
    if not path.exists():
        return set()
    return {
        str(row.get("source_id"))
        for row in load_jsonl(path)
        if row.get("status") == "rejected_noise" and row.get("source_id")
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-auto", action="store_true", help="include metadata-only crawler extracts as C-grade candidates")
    args = parser.parse_args()
    rows = load_jsonl(args.input)
    if args.include_auto and DEFAULT_AUTO_INPUT.exists():
        rejected = rejected_source_ids()
        rows.extend(
            row for row in normalize_auto_rows(load_jsonl(DEFAULT_AUTO_INPUT))
            if str(row.get("source_id", "")) not in rejected
        )
    result = cluster(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS research clustering: {result['counts']['extracts']} extracts -> {result['counts']['clusters_with_hits']} clusters, {result['counts']['candidate_links']} candidate links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
