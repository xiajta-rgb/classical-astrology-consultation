#!/usr/bin/env python3
"""Validate optional real-world observation records used as discriminators.

Observations are not silently treated as chart evidence.  They are a separate
layer that can support H1, support H2, contradict H1, or remain neutral.  A
record must say what was observed, when/where it came from, and how directly it
was obtained before it can influence a counter-test.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


RELATIONS = {"supports_H1", "supports_H2", "contradicts_H1", "neutral"}
CONFIDENCE = {"direct", "reported", "documented", "inferred"}
RISK_LEVELS = {"G0", "G1", "G2", "G3"}
OBSERVATION_STATES = {"active", "withdrawn", "superseded", "deleted"}
SENSITIVE_DICTIONARY_VERSION = "SENSITIVE-0.2"
SENSITIVE_DICTIONARY_PATH = Path(__file__).resolve().parents[1] / "references" / "sensitive-dictionary.json"
SENSITIVE_RULES = {
    "mortality": ("死亡", "寿命", "大限", "离开人世", "不在了", "活不过", "death", "mortality", "end of life"),
    "self_harm": ("自杀", "自残", "不想活", "suicide", "self-harm", "self harm", "end my life"),
    "medical": ("疾病", "癌", "精神病", "抑郁", "病症", "cancer", "diagnosis", "diagnose", "depression", "mental illness"),
    "violence_crime": ("暴力", "犯罪", "被捕", "入狱", "施暴", "强奸", "乱伦", "violence", "crime", "arrest", "assault", "abuse"),
    "reproduction": ("怀孕", "流产", "不孕", "生不了", "孩子保不住", "pregnancy", "miscarriage", "infertility"),
    "sexual_identity": ("性取向", "sexual orientation", "sexuality", "gay", "lesbian"),
    "curse_possession": ("诅咒", "附体", "下蛊", "中邪", "curse", "possessed", "possession"),
    "addiction": ("成瘾", "酗酒", "毒品", "addiction", "drug abuse", "alcoholism"),
}

_BUILTIN_SENSITIVE_RULES = SENSITIVE_RULES


def _load_dictionary(path: Path | None = None) -> tuple[str, dict[str, tuple[str, ...]], str, dict[str, Any]]:
    """Load the versioned dictionary; fallback is explicit and fail-closed."""
    try:
        dictionary_path = path or SENSITIVE_DICTIONARY_PATH
        raw = json.loads(dictionary_path.read_text(encoding="utf-8"))
        version = str(raw["version"])
        previous_version = str(raw.get("previous_version", ""))
        change_note = str(raw.get("change_note", "")).strip()
        changed_categories = [str(category) for category in raw.get("changed_categories", [])]
        if not previous_version or not change_note or not changed_categories:
            raise ValueError("missing dictionary change audit")
        rules = {str(category): tuple(str(marker) for marker in markers) for category, markers in raw["rules"].items()}
        if not version or not rules or any(not markers for markers in rules.values()):
            raise ValueError("empty sensitive dictionary")
        audit = {"previous_version": previous_version, "change_note": change_note, "changed_categories": changed_categories}
        return version, rules, "configured", audit
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return "SENSITIVE-BUILTIN-FALLBACK", _BUILTIN_SENSITIVE_RULES, "fallback", {"previous_version": "", "change_note": "", "changed_categories": []}


SENSITIVE_DICTIONARY_VERSION, SENSITIVE_RULES, SENSITIVE_DICTIONARY_STATUS, SENSITIVE_DICTIONARY_AUDIT = _load_dictionary()


def detect_sensitive_markers(statement: str, rules: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    """Return canonical category/marker pairs using case/spacing-insensitive matching."""
    rules = rules or SENSITIVE_RULES
    lowered = statement.lower()
    compact = re.sub(r"[\s\-_]+", "", lowered)
    matches: list[str] = []
    for category, markers in rules.items():
        for marker in markers:
            marker_lower = marker.lower()
            marker_compact = re.sub(r"[\s\-_]+", "", marker_lower)
            if marker_lower in lowered or marker_compact in compact:
                matches.append(f"{category}:{marker}")
    return sorted(set(matches))


def validate(observations: dict[str, Any] | None) -> dict[str, Any]:
    observations = observations or {}
    findings: list[str] = []
    if SENSITIVE_DICTIONARY_STATUS != "configured":
        findings.append("sensitive_dictionary_fallback")
    normalized: dict[str, list[dict[str, Any]]] = {}
    count = 0
    active_count = 0
    tombstone_count = 0
    global_keys: set[tuple[str, str]] = set()
    global_active_ids: set[str] = set()
    available_versions: set[tuple[str, str]] = {
        (str(item.get("id", "")), str(item.get("record_version", "")))
        for raw_items in observations.values()
        if isinstance(raw_items, list)
        for item in raw_items
        if isinstance(item, dict)
    }
    for topic, raw_items in observations.items():
        if not isinstance(raw_items, list):
            findings.append(f"{topic}: observations must be a list")
            continue
        normalized[str(topic)] = []
        seen_keys: set[tuple[str, str]] = set()
        for index, item in enumerate(raw_items):
            prefix = f"{topic}[{index}]"
            if not isinstance(item, dict):
                findings.append(f"{prefix}: observation must be an object")
                continue
            state = item.get("state")
            required_fields = ("id", "record_version", "state")
            if state == "active":
                required_fields += ("statement", "source_type", "source_locator", "relation", "confidence")
            for field in required_fields:
                if not str(item.get(field, "")).strip():
                    findings.append(f"{prefix}: missing {field}")
            item_id = str(item.get("id", ""))
            record_version = str(item.get("record_version", ""))
            record_key = (item_id, record_version)
            if record_key in seen_keys:
                findings.append(f"{prefix}: duplicate id/version {item_id}/{record_version}")
            seen_keys.add(record_key)
            if record_key in global_keys:
                findings.append(f"{prefix}: duplicate global id/version {item_id}/{record_version}")
            global_keys.add(record_key)
            if state not in OBSERVATION_STATES:
                findings.append(f"{prefix}: invalid state {state}")
            if state in {"withdrawn", "superseded", "deleted"} and not str(item.get("withdrawal_reason", "")).strip():
                findings.append(f"{prefix}: withdrawn/superseded/deleted record requires withdrawal_reason")
            if state in {"withdrawn", "superseded", "deleted"}:
                tombstone_count += 1
            elif state == "active":
                active_count += 1
                if item_id in global_active_ids:
                    findings.append(f"{prefix}: multiple active versions for id {item_id}")
                global_active_ids.add(item_id)
            if state == "superseded" and not str(item.get("supersedes", "")).strip():
                findings.append(f"{prefix}: superseded record requires supersedes")
            if state == "superseded" and str(item.get("supersedes", "")).strip():
                superseded_version = str(item.get("supersedes"))
                if (item_id, superseded_version) not in available_versions:
                    findings.append(f"{prefix}: supersedes target not found {item_id}/{superseded_version}")
                if superseded_version == record_version:
                    findings.append(f"{prefix}: supersedes cannot point to itself {item_id}/{record_version}")
            if state == "active" and item.get("relation") not in RELATIONS:
                findings.append(f"{prefix}: invalid relation {item.get('relation')}")
            if state == "active" and item.get("confidence") not in CONFIDENCE:
                findings.append(f"{prefix}: invalid confidence {item.get('confidence')}")
            statement = str(item.get("statement", ""))
            sensitive = detect_sensitive_markers(statement)
            if sensitive:
                risk_level = item.get("risk_level")
                if risk_level not in {"G1", "G2", "G3"}:
                    findings.append(f"{prefix}: sensitive observation requires risk_level G1/G2/G3")
                if item.get("user_initiated") is not True:
                    findings.append(f"{prefix}: sensitive observation requires user_initiated=true")
                if item.get("data_minimized") is not True:
                    findings.append(f"{prefix}: sensitive observation requires data_minimized=true")
                if risk_level == "G3":
                    findings.append(f"{prefix}: G3 observation cannot enter publishable evidence")
            safe_item = dict(item)
            if state in {"withdrawn", "superseded", "deleted"}:
                safe_item["active"] = False
                safe_item.pop("statement", None)
                safe_item.pop("source_locator", None)
                safe_item["tombstone"] = True
            else:
                safe_item["active"] = True
            if sensitive:
                safe_item["statement"] = "[redacted_sensitive_observation]"
                safe_item["sensitive_markers"] = sensitive
            normalized[str(topic)].append(safe_item)
            count += 1
    status = "not_collected" if not observations else "invalid" if findings else "collected" if active_count else "withdrawn_only"
    return {
        "status": status,
        "count": count,
        "active_count": active_count,
        "tombstone_count": tombstone_count,
        "findings": findings,
        "observations": normalized,
        "sensitive_dictionary_version": SENSITIVE_DICTIONARY_VERSION,
        "sensitive_dictionary_status": SENSITIVE_DICTIONARY_STATUS,
        "sensitive_dictionary_audit": SENSITIVE_DICTIONARY_AUDIT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate optional real-world observation records")
    parser.add_argument("observations", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.observations.read_text(encoding="utf-8"))
    result = validate(raw)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
