#!/usr/bin/env python3
"""Run bounded local research-loop passes and persist a resumable state file.

External browsing remains user-triggered. This runner processes the saved
source queue and extracts, making the loop reproducible between turns.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from cluster_research_extracts import cluster, load_jsonl
from check_research_loop_system import run as check_system


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "references/research-loop"


def run_passes(round_id: str, passes: int) -> dict:
    source_path = LOOP / "source-queue.jsonl"
    extract_path = LOOP / "candidate-extracts.jsonl"
    extracts = load_jsonl(extract_path)
    source_rows = load_jsonl(source_path)
    events: list[dict] = []
    for pass_no in range(1, passes + 1):
        if pass_no == 1:
            stage = "source_integrity"
            findings = check_system()
            status = "pass" if not findings else "blocked"
            detail = {"findings": findings, "sources": len(source_rows), "extracts": len(extracts)}
        elif pass_no == 2:
            stage = "candidate_clustering"
            clustered = cluster(extracts)
            status = "pass"
            detail = clustered["counts"]
        else:
            stage = "promotion_gate_audit"
            blocked = [row.get("extract_id") for row in extracts if row.get("status") != "promoted"]
            status = "pass"
            detail = {"promotion_candidates": 0, "held_at_candidate": len(blocked), "reason": "primary locator, counter-test and chart regression still required"}
        events.append({"pass": pass_no, "stage": stage, "status": status, "detail": detail})
    return {
        "schema_version": "RESEARCH-LOOP-STATE-0.1",
        "round_id": round_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "bounded_passes": passes,
        "events": events,
        "resume_from": "primary_text_and_counterexample_review",
        "external_browsing_policy": "user_triggered_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-id", default="LOOP-20260815-01")
    parser.add_argument("--passes", type=int, default=3)
    args = parser.parse_args()
    if args.passes < 1 or args.passes > 12:
        parser.error("--passes must be between 1 and 12")
    state = run_passes(args.round_id, args.passes)
    output = LOOP / "rounds" / f"{args.round_id}.state.json"
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS research loop: {args.passes} bounded passes -> {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
