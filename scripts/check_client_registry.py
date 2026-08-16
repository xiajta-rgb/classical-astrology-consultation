#!/usr/bin/env python3
"""Validate the canonical client-folder registry and naming contract."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "clients.json"
CLIENTS = ROOT / "clients"
NAME_RE = re.compile(r"^(?:\d{8}-\d{4}-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*|\d{4}-unknown-unknown-place)$")


def run() -> list[str]:
    findings: list[str] = []
    try:
        rows = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"registry_parse_error:{exc}"]
    if not isinstance(rows, list):
        return ["registry_must_be_array"]
    seen: set[str] = set()
    for row in rows:
        case_id = row.get("case_id")
        folder = row.get("folder")
        if not case_id or case_id in seen:
            findings.append(f"duplicate_or_missing_case_id:{case_id}")
            continue
        seen.add(case_id)
        if not NAME_RE.fullmatch(case_id):
            findings.append(f"invalid_case_id:{case_id}")
        expected = CLIENTS / case_id
        if folder != f"clients/{case_id}":
            findings.append(f"folder_not_canonical:{case_id}:{folder}")
        if not expected.is_dir():
            findings.append(f"missing_case_folder:{case_id}")
            continue
        profile = expected / "profile.json"
        if not profile.is_file():
            findings.append(f"missing_profile:{case_id}")
            continue
        try:
            profile_data = json.loads(profile.read_text(encoding="utf-8"))
            if profile_data.get("case_id") != case_id:
                findings.append(f"profile_case_id_mismatch:{case_id}")
            for artifact in profile_data.get("canonical_artifacts", []):
                artifact_path = expected / artifact
                if not artifact_path.is_file():
                    findings.append(f"missing_canonical_artifact:{case_id}:{artifact}")
                allowed_prefixes = ("input/", "analysis/chart-facts/", "analysis/interpretations/", "delivery/", "observations/", "related/")
                if not artifact.startswith(allowed_prefixes):
                    findings.append(f"unclassified_analysis_artifact:{case_id}:{artifact}")
        except Exception as exc:
            findings.append(f"profile_parse_error:{case_id}:{exc}")
    return findings


if __name__ == "__main__":
    errors = run()
    if errors:
        print("FAIL client registry")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS client registry: canonical time-place folders, profiles and index agree")
