"""Regression checks for decoupled natal interpretation modules."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_modular_interpretation import build  # noqa: E402


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    package = json.loads((root / "references/loop-runs/ROUND122-EPHH-FACTS.json").read_text(encoding="utf-8"))
    registry = json.loads((root / "references/interpretation-modules/registry.json").read_text(encoding="utf-8"))
    report = build(package, registry)
    assert report["status"] == "hold"
    by_id = {item["id"]: item for item in report["modules"]}
    assert len(by_id) == 8
    assert by_id["life_timing"]["status"] == "inactive"
    assert "某年" in by_id["life_timing"]["interpretation"][0]
    assert by_id["wealth_income"]["status"] == "provisional_hold"
    assert any(item["rule_id"] == "W-1" for item in by_id["wealth_income"]["evidence"])
    assert any(item["rule_id"] == "C-1" for item in by_id["career_public_role"]["evidence"])
    assert any(item["rule_id"] == "J-1" for item in by_id["work_execution"]["evidence"])
    assert any(item["rule_id"] == "R-1" for item in by_id["love_relationship"]["evidence"])
    assert all(item.get("salience") in ("critical", "high") for item in by_id["wealth_income"]["evidence"])
    assert by_id["wealth_income"]["selection"]["deferred_count"] >= 0
    assert all(item["counter_tests"] for item in report["modules"])
    print("PASS modular interpretation self-test: eight modules, salience gate, timing gate and evidence anchors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
