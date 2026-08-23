#!/usr/bin/env python3
"""Validate the source-bound candidate article distillation artifacts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISTILLED = ROOT / "references/knowledge-modules/distilled"
SOURCE = Path(r"C:\Users\xiajt\Downloads\(公众号数据)表格视图.xlsx")
MARKETING = re.compile(r"往期|加微信|课程|推荐阅读|For more|留言若|本周付费|Blackcherry占星咨询专属通道")


def main() -> int:
    findings: list[str] = []
    manifest_path = DISTILLED / "index.json"
    cards_path = DISTILLED / "cards.jsonl"
    retrieval_path = DISTILLED / "retrieval-index.json"
    exclusions_path = DISTILLED / "exclusions.jsonl"
    exploration_path = DISTILLED / "exploration.json"
    queue_path = DISTILLED / "review-queue.jsonl"
    drafts_path = DISTILLED / "module-drafts.json"
    drafts_md_path = DISTILLED / "module-drafts.md"
    ledger_index_path = DISTILLED / "judgment-ledger-index.json"
    coverage_path = DISTILLED / "article-coverage.jsonl"
    judgments_path = DISTILLED / "judgment-ledger.jsonl"
    for path in (manifest_path, cards_path, retrieval_path, exclusions_path, exploration_path, queue_path, drafts_path, drafts_md_path, ledger_index_path, coverage_path, judgments_path):
        if not path.exists():
            findings.append(f"missing:{path.relative_to(ROOT)}")
    cards: list[dict[str, object]] = []
    if not findings:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cards = [json.loads(line) for line in cards_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        expected_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest() if SOURCE.exists() else None
        if expected_hash and manifest.get("source_sha256") != expected_hash:
            findings.append("source_sha256_mismatch")
        if manifest.get("counts", {}).get("candidate_cards") != len(cards):
            findings.append("manifest_candidate_count_mismatch")
        ids = [card.get("id") for card in cards]
        if any(not card_id for card_id in ids) or len(ids) != len(set(ids)):
            findings.append("missing_or_duplicate_card_id")
        for line_no, card in enumerate(cards, start=1):
            for field in ("source_ids", "source_locator", "text", "conditions", "counter_test", "grade_cap", "status", "safety_gate"):
                if field not in card:
                    findings.append(f"card_contract:{line_no}:{field}")
            if card.get("grade_cap") != "C":
                findings.append(f"card_grade_cap:{line_no}")
            if card.get("status") not in {"candidate", "deferred"}:
                findings.append(f"card_status:{line_no}")
            for claim in card.get("claims", []):
                if MARKETING.search(str(claim.get("source_span", ""))):
                    findings.append(f"marketing_span:{line_no}")
                    break
        retrieval = json.loads(retrieval_path.read_text(encoding="utf-8"))
        if retrieval.get("counts", {}).get("all_records") != len(cards):
            findings.append("retrieval_count_mismatch")
        if retrieval.get("card_fingerprint_sha256") != hashlib.sha256(cards_path.read_bytes()).hexdigest():
            findings.append("retrieval_fingerprint_mismatch")
        exploration = json.loads(exploration_path.read_text(encoding="utf-8"))
        if exploration.get("counts", {}).get("cards") != len(cards):
            findings.append("exploration_card_count_mismatch")
        assignments = exploration.get("assignments", [])
        assigned_ids = [row.get("card_id") for row in assignments]
        if len(assigned_ids) != len(cards) or set(assigned_ids) != set(ids):
            findings.append("exploration_assignments_not_one_per_card")
        for field in ("quality_flags", "review_status", "next_action", "title"):
            if any(field not in row for row in assignments):
                findings.append(f"exploration_assignment_missing:{field}")
        queue = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        queue_ids = [row.get("card_id") for row in queue]
        if len(queue_ids) > 40 or len(queue_ids) != len(set(queue_ids)):
            findings.append("review_queue_size_or_duplicate_id")
        if not set(queue_ids).issubset(set(ids)):
            findings.append("review_queue_unknown_card_id")
        for line_no, row in enumerate(queue, start=1):
            for field in ("card_id", "title", "canonical_cluster", "review_score", "review_status", "quality_flags", "claims", "conditions", "counter_test", "next_action", "independent_source_required"):
                if field not in row:
                    findings.append(f"review_queue_contract:{line_no}:{field}")
        drafts = json.loads(drafts_path.read_text(encoding="utf-8"))
        modules = drafts.get("modules", [])
        cluster_ids = set(exploration.get("clusters", {}))
        draft_ids = {module.get("id") for module in modules}
        if draft_ids != cluster_ids:
            findings.append("module_drafts_cluster_mismatch")
        if drafts.get("status") != "candidate_only" or drafts.get("grade_cap") != "C":
            findings.append("module_drafts_promotion_guardrail")
        for module in modules:
            for field in ("id", "title", "include_boundary", "exclude_boundary", "next_test", "representative_cards", "promotion_gate"):
                if field not in module:
                    findings.append(f"module_draft_contract:{module.get('id')}:{field}")
        ledger = json.loads(ledger_index_path.read_text(encoding="utf-8"))
        if expected_hash and ledger.get("source_sha256") != expected_hash:
            findings.append("ledger_source_sha256_mismatch")
        coverage = [json.loads(line) for line in coverage_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        judgments = [json.loads(line) for line in judgments_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(coverage) != ledger.get("counts", {}).get("rows_seen"):
            findings.append("coverage_row_count_mismatch")
        if len(judgments) != ledger.get("counts", {}).get("judgments"):
            findings.append("judgment_count_mismatch")
        coverage_ids = [row.get("article_id") for row in coverage]
        judgment_ids = [row.get("judgment_id") for row in judgments]
        if len(coverage_ids) != len(set(coverage_ids)) or any(not value for value in coverage_ids):
            findings.append("coverage_missing_or_duplicate_article_id")
        if len(judgment_ids) != len(set(judgment_ids)) or any(not value for value in judgment_ids):
            findings.append("judgment_missing_or_duplicate_id")
        if sum(int(row.get("judgment_count", 0)) for row in coverage) != len(judgments):
            findings.append("coverage_judgment_count_sum_mismatch")
        for line_no, row in enumerate(judgments, start=1):
            for field in ("judgment_id", "article_id", "source_locator", "source_span", "pattern", "extraction_mode", "topics", "article_disposition", "runtime_eligible", "status", "grade_cap", "safety_gate"):
                if field not in row:
                    findings.append(f"judgment_contract:{line_no}:{field}")
            if row.get("grade_cap") != "C":
                findings.append(f"judgment_grade_cap:{line_no}")
            if row.get("runtime_eligible") and row.get("modern_extension"):
                findings.append(f"modern_runtime_leak:{line_no}")
            if row.get("extraction_mode") == "broad_review" and row.get("runtime_eligible"):
                findings.append(f"broad_runtime_leak:{line_no}")
            if row.get("status") not in {"candidate", "deferred", "quarantined", "review_needed"}:
                findings.append(f"judgment_status:{line_no}")
    if findings:
        print("FAIL")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print(f"PASS article distillation: {len(cards)} candidate cards, source hash and guardrails valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
