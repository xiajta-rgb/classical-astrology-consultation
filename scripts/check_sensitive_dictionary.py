#!/usr/bin/env python3
"""Audit sensitive-dictionary changes against versioned regression samples."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_observations import _load_dictionary, detect_sensitive_markers
except ModuleNotFoundError:  # direct execution from the scripts directory
    from validate_observations import _load_dictionary, detect_sensitive_markers


ROOT = Path(__file__).resolve().parents[1]


def _rules(raw: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    return {str(category): tuple(str(marker) for marker in markers) for category, markers in raw.get("rules", {}).items()}


def audit(
    current_path: Path = ROOT / "references" / "sensitive-dictionary.json",
    previous_path: Path = ROOT / "references" / "fixtures" / "sensitive-dictionary-0.2.json",
    cases_path: Path = ROOT / "references" / "fixtures" / "sensitive-observation-cases.json",
) -> dict[str, Any]:
    current_raw = json.loads(current_path.read_text(encoding="utf-8"))
    previous_raw = json.loads(previous_path.read_text(encoding="utf-8"))
    cases = json.loads(cases_path.read_text(encoding="utf-8")).get("cases", [])
    current_version, current_rules, status, _ = _load_dictionary(current_path)
    previous_rules = _rules(previous_raw)
    findings: list[str] = []
    if status != "configured":
        findings.append("current_dictionary_not_configured")
    if current_version != current_raw.get("version"):
        findings.append("current_dictionary_version_mismatch")
    if current_raw.get("previous_version") != previous_raw.get("version"):
        findings.append("previous_version_chain_mismatch")
    old_markers = {f"{category}:{marker}" for category, markers in previous_rules.items() for marker in markers}
    new_markers = {f"{category}:{marker}" for category, markers in current_rules.items() for marker in markers}
    changed_cases: list[dict[str, Any]] = []
    for case in cases:
        old_hits = sorted({hit.split(":", 1)[0] for hit in detect_sensitive_markers(case["statement"], previous_rules)})
        new_hits = sorted({hit.split(":", 1)[0] for hit in detect_sensitive_markers(case["statement"], current_rules)})
        expected = [] if case.get("expected") == "none" else [case.get("expected")]
        if sorted(expected) != new_hits:
            findings.append(f"sample_mismatch:{case.get('id')}")
        if old_hits != new_hits:
            changed_cases.append({"id": case.get("id"), "old": old_hits, "new": new_hits})
        if case.get("expected") == "none" and old_hits != new_hits:
            findings.append(f"benign_sample_changed:{case.get('id')}")
    return {
        "status": "pass" if not findings else "fail",
        "current_version": current_raw.get("version"),
        "previous_version": previous_raw.get("version"),
        "added_markers": sorted(new_markers - old_markers),
        "removed_markers": sorted(old_markers - new_markers),
        "changed_cases": changed_cases,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit sensitive dictionary changes")
    parser.add_argument("--current", type=Path, default=ROOT / "references" / "sensitive-dictionary.json")
    parser.add_argument("--previous", type=Path, default=ROOT / "references" / "fixtures" / "sensitive-dictionary-0.2.json")
    parser.add_argument("--cases", type=Path, default=ROOT / "references" / "fixtures" / "sensitive-observation-cases.json")
    args = parser.parse_args()
    result = audit(args.current, args.previous, args.cases)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
