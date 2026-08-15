#!/usr/bin/env python3
"""End-to-end release-bundle consistency and hash verification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.build_release_manifest import build_manifest
    from scripts.check_natal_first import check_text as check_natal_text
except ModuleNotFoundError:
    from build_release_manifest import build_manifest
    from check_natal_first import check_text as check_natal_text


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _hash_findings(manifest: dict[str, Any]) -> list[str]:
    findings = []
    for item in manifest.get("artifacts", []):
        path = Path(item["path"])
        if not path.exists():
            findings.append(f"missing_artifact:{path.as_posix()}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item.get("sha256"):
            findings.append(f"hash_mismatch:{path.as_posix()}")
        if path.suffix.lower() == ".md":
            findings.extend(f"report:{finding}" for finding in check_natal_text(path.read_text(encoding="utf-8")))
    return findings


def check(facts: dict[str, Any], source_audit: dict[str, Any], research_assets: dict[str, Any], supplied_manifest: dict[str, Any], artifact_manifest: dict[str, Any], status_summary: str | None = None) -> dict[str, Any]:
    expected = build_manifest(facts, source_audit=source_audit, research_assets=research_assets)
    findings = _hash_findings(artifact_manifest)
    for key in ("decision", "publishable", "blockers", "warnings", "chart_contract", "chart_layers", "research_assets"):
        if supplied_manifest.get(key) != expected.get(key):
            findings.append(f"manifest_mismatch:{key}")
    fact_gate = facts.get("release_gate", {})
    if (fact_gate.get("decision") == "hold") != (supplied_manifest.get("decision") == "hold"):
        findings.append("dual_hold_decision_mismatch")
    if bool(fact_gate.get("natal_interpretation_ready")) != bool(supplied_manifest.get("chart_layers", {}).get("natal_interpretation_ready")):
        findings.append("dual_hold_interpretation_mismatch")
    if status_summary is not None:
        state_markers = ("decision=hold", "publishable=false") if supplied_manifest.get("decision") == "hold" else ("decision=publish", "publishable=true")
        for marker in state_markers:
            if marker not in status_summary:
                findings.append(f"status_summary_state_mismatch:{marker}")
    if status_summary is not None:
        for marker in ("HOLD", "当前能解读", "不能解读", "解除 HOLD"):
            if marker not in status_summary:
                findings.append(f"status_summary_missing:{marker}")
    return {
        "status": "pass" if not findings else "fail",
        "decision": supplied_manifest.get("decision"),
        "publishable": supplied_manifest.get("publishable"),
        "artifact_count": len(artifact_manifest.get("artifacts", [])),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("facts", type=Path)
    parser.add_argument("source_audit", type=Path)
    parser.add_argument("research_assets", type=Path)
    parser.add_argument("release_manifest", type=Path)
    parser.add_argument("artifact_manifest", type=Path)
    parser.add_argument("--status-summary", type=Path)
    args = parser.parse_args()
    status_summary = args.status_summary.read_text(encoding="utf-8") if args.status_summary else None
    result = check(_read(args.facts), _read(args.source_audit), _read(args.research_assets), _read(args.release_manifest), _read(args.artifact_manifest), status_summary)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
