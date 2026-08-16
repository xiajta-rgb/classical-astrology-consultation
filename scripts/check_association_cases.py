"""Regression checks for chart-first association and counterfactual guards."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compose_significators import compose  # noqa: E402


FIXTURE = ROOT / "references" / "fixtures" / "association-regression-cases.json"


def main() -> int:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = {item["id"]: item for item in payload["cases"]}
    for case in cases.values():
        assert case["evidence"], case["id"]
        assert all(item.get("chart_anchor") for item in case["evidence"]), case["id"]

    sibling = compose(cases["mother_1973_siblings"]["evidence"])
    sibling_mechanism = next(item for item in sibling["mechanisms"] if item["mechanism"] == "sibling_health_loss_route")
    assert sibling_mechanism["independent_chain_count"] == 3
    assert sibling_mechanism["status"] == "conflicted"
    assert sibling_mechanism["requires_discriminator"] is True

    without_11th = [item for item in cases["mother_1973_siblings"]["evidence"] if item["id"] != "jupiter_ruler_11th_12th"]
    reduced = compose(without_11th)
    reduced_mechanism = next(item for item in reduced["mechanisms"] if item["mechanism"] == "sibling_health_loss_route")
    assert reduced_mechanism["independent_chain_count"] == 2
    assert reduced_mechanism["status"] == "conflicted"
    assert reduced_mechanism["requires_discriminator"] is True

    wealth = compose(cases["mother_1973_wealth"]["evidence"])
    wealth_mechanism = next(item for item in wealth["mechanisms"] if item["mechanism"] == "large_shared_resource_opportunity")
    assert wealth_mechanism["independent_chain_count"] == 3
    assert wealth_mechanism["status"] == "convergent"
    assert "a convergent mechanism is not automatically a severe event" in wealth["guards"]

    print("PASS association cases: sibling conflict, counterfactual downgrade and wealth convergence guards verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
