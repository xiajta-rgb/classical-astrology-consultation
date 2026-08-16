"""Validate the reusable chart-first association operator catalog."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references" / "calculation-methods" / "association-operators.json"


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert data["principle"].startswith("Chart significators")
    operators = data["operators"]
    ids = [item["id"] for item in operators]
    assert len(ids) == len(set(ids))
    required_roles = {"association", "composition", "validation", "timing_resolution"}
    seen_roles = set()
    for item in operators:
        assert item["chart_anchors"]
        assert item["blocked_without"]
        assert item["not_allowed"]
        seen_roles.add(item["external_logic_role"])
    assert required_roles <= seen_roles
    assert "event_ladder" in ids
    assert "temporal_activation" in ids
    assert "counterfactual_removal" in ids
    print(f"PASS association operators: {len(operators)} chart-first operators and external-logic boundaries verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
