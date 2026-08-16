#!/usr/bin/env python3
"""Fail-closed checks for locally extracted knowledge modules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_STATUS = {"candidate", "auxiliary", "inactive_until_timing_activation"}
FORBIDDEN_UNBOUNDED = ("必然", "一定", "躺赚", "大概率有钱有房", "大财格局")


def check(registry: dict[str, Any], source_registry: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    modules = registry.get("modules", [])
    if not modules:
        findings.append("no knowledge modules")
    ids: set[str] = set()
    sources = source_registry.get("sources", {})
    for module in modules:
        module_id = module.get("id")
        if not module_id:
            findings.append("module missing id")
            continue
        if module_id in ids:
            findings.append(f"duplicate module id: {module_id}")
        ids.add(module_id)
        if module.get("status") not in ALLOWED_STATUS:
            findings.append(f"{module_id}: unsupported status")
        for artifact in module.get("artifacts", []):
            if not (Path(__file__).resolve().parents[1] / "references/knowledge-modules" / artifact).exists():
                findings.append(f"{module_id}: missing artifact {artifact}")
        unknown = [sid for sid in module.get("source_ids", []) if sid not in sources]
        if unknown:
            findings.append(f"{module_id}: unknown source ids {unknown}")
        for key in ("operational_rule", "conditions", "counter_tests", "output_guardrail"):
            value = module.get(key)
            if not value:
                findings.append(f"{module_id}: missing {key}")
        text = json.dumps(module, ensure_ascii=False)
        if module.get("status") != "inactive_until_timing_activation" and "grade_cap" not in text:
            findings.append(f"{module_id}: active local module missing grade cap language")
        coverage = module.get("coverage", {})
        if module_id == "house-ruler-flow" and coverage.get("directed_house_flows") != 144:
            findings.append("house-ruler-flow: coverage must declare 144 directed flows")
        if module_id == "mutual-reception-matrix" and coverage.get("unordered_house_pairs") != 78:
            findings.append("mutual-reception-matrix: coverage must declare 78 unordered pairs")
        for phrase in FORBIDDEN_UNBOUNDED:
            offset = 0
            while True:
                index = text.find(phrase, offset)
                if index < 0:
                    break
                context = text[max(0, index - 8):index]
                if not any(marker in context for marker in ("不", "不能", "不得", "仅", "只")):
                    findings.append(f"{module_id}: unbounded phrase {phrase}")
                    break
                offset = index + len(phrase)
    distillation = registry.get("core_distillation") or registry.get("distillation", {})
    if distillation:
        root = Path(__file__).resolve().parents[1] / "references/knowledge-modules"
        canonical = root / str(distillation.get("canonical_store", ""))
        index_path = root / str(distillation.get("index", ""))
        readme = root / str(distillation.get("readme", ""))
        for path, label in ((canonical, "canonical_store"), (index_path, "index"), (readme, "readme")):
            if not path.exists():
                findings.append(f"distillation: missing {label} {path}")
        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
            expected = distillation.get("record_count")
            actual = index.get("counts", {}).get("all_records")
            if expected != actual:
                findings.append(f"distillation: registry/index record count mismatch {expected} != {actual}")
            if index.get("canonical_store") != distillation.get("canonical_store"):
                findings.append("distillation: index canonical store pointer mismatch")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "references/knowledge-modules/registry.json").read_text(encoding="utf-8"))
    source_registry = json.loads((root / "references/source-registry.json").read_text(encoding="utf-8"))
    findings = check(registry, source_registry)
    if findings:
        print("FAIL")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print(f"PASS knowledge modules: {len(registry['modules'])} modules, provenance and guardrails present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
