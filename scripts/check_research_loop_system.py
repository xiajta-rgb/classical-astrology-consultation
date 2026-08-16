#!/usr/bin/env python3
"""Fail-closed checks for the external research-loop layer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "references/research-loop"
REQUIRED = (
    LOOP / "README.md",
    LOOP / "gap-registry.json",
    LOOP / "source-queue.jsonl",
    LOOP / "candidate-extracts.jsonl",
    LOOP / "rounds/LOOP-20260815-01.json",
    LOOP / "auto-loop-config.json",
    LOOP / "auto-loop-state.json",
    LOOP / "auto-extracts.jsonl",
)


def jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no} is not an object")
        rows.append(value)
    return rows


def run() -> list[str]:
    findings: list[str] = []
    for path in REQUIRED:
        if not path.exists():
            findings.append(f"missing artifact: {path.relative_to(ROOT)}")
    if findings:
        return findings
    gap = json.loads((LOOP / "gap-registry.json").read_text(encoding="utf-8"))
    if not gap.get("gaps"):
        findings.append("gap registry is empty")
    if len(gap.get("gaps", [])) < 5:
        findings.append("gap registry must contain at least five research targets")
    sources = jsonl(LOOP / "source-queue.jsonl")
    extracts = jsonl(LOOP / "candidate-extracts.jsonl")
    auto_extracts = jsonl(LOOP / "auto-extracts.jsonl")
    source_ids = {row.get("source_id") for row in sources}
    for row in sources:
        for field in ("source_id", "source_type", "source_tier", "url", "status", "upgrade_rule"):
            if not row.get(field):
                findings.append(f"source missing {field}: {row.get('source_id')}")
    for row in extracts:
        for field in ("extract_id", "source_id", "claim", "status", "grade_cap", "counter_test"):
            if not row.get(field):
                findings.append(f"extract missing {field}: {row.get('extract_id')}")
        if row.get("source_id") not in source_ids:
            findings.append(f"extract references unknown source: {row.get('extract_id')}")
        if row.get("grade_cap") not in {"C", "B", "A", "S"}:
            findings.append(f"invalid grade cap: {row.get('extract_id')}")
    auto_state = json.loads((LOOP / "auto-loop-state.json").read_text(encoding="utf-8"))
    if not isinstance(auto_state.get("cursor"), int) or not 0 <= auto_state["cursor"] <= len(sources):
        findings.append("auto-loop cursor is outside source queue")
    for row in auto_extracts:
        for field in ("extract_id", "source_id", "retrieved_at", "status", "grade_cap", "promotion"):
            if not row.get(field):
                findings.append(f"auto extract missing {field}: {row.get('extract_id')}")
        if row.get("grade_cap") != "C":
            findings.append(f"auto extract is not capped at C: {row.get('extract_id')}")
        if row.get("promotion") != "blocked_until_manual_source_review":
            findings.append(f"auto extract promotion gate missing: {row.get('extract_id')}")
    round_manifest = json.loads((LOOP / "rounds/LOOP-20260815-01.json").read_text(encoding="utf-8"))
    if not round_manifest.get("focus_clusters"):
        findings.append("round has no focus clusters")
    if any(stage.get("status") == "complete" for stage in round_manifest.get("stages", [])) and not round_manifest.get("guardrails"):
        findings.append("completed round has no guardrails")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    findings = run()
    if findings:
        print("FAIL research loop system")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("PASS research loop system: sources, extracts, gaps and round manifest are traceable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
