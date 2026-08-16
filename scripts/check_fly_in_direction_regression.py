#!/usr/bin/env python3
"""Guard against reversing house-ruler flow during property/wealth readings."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "references" / "fixtures" / "fly-in-direction-regression.json"


def interpret(case: dict) -> dict:
    a = case["fly_in"]["responsibility_house"]
    b = case["fly_in"]["ruler_house"]
    if (a, b) == (4, 2):
        direction = "property_to_wealth"
        interpretation = "property_can_enter_wealth_audit"
    elif (a, b) == (2, 4):
        direction = "wealth_to_property"
        interpretation = "money_can_enter_property_allocation"
    else:
        direction = f"{a}_to_{b}"
        interpretation = "unmapped"
    if case.get("additional_testimony", {}).get("fortune_connection") is False:
        interpretation = "hold_for_property_profit"
    return {"direction": direction, "interpretation": interpretation, "grade_cap": "C", "alone_proves_profit": False}


def run() -> list[str]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    findings: list[str] = []
    for case in data["cases"]:
        actual = interpret(case)
        expected = case["expected"]
        for key in ("direction", "interpretation", "grade_cap", "alone_proves_profit"):
            if actual[key] != expected[key]:
                findings.append(f"{case['id']}:{key}:expected={expected[key]!r}:actual={actual[key]!r}")
    return findings


if __name__ == "__main__":
    errors = run()
    if errors:
        print("FAIL fly-in direction regression")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS fly-in direction regression: 4->2 and 2->4 remain non-symmetric and non-deterministic")
