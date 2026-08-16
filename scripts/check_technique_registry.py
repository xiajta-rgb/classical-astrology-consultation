"""Fail-closed audit for the cross-system technique registry."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "astrology_engine" / "technique_registry.json"


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    policy = data["production_policy"]
    assert policy["zodiac"] == "tropical"
    assert policy["house_system"] == "Placidus"
    assert policy["chart_significators_are_primary"] is True
    assert policy["external_systems_may_not_override_chart_facts"] is True
    assert set(policy["borrowed_logic_scope"]) == {"association", "composition", "validation", "timing_resolution"}
    assert policy["predictive_requires_explicit_activation"] is True

    techniques = data["techniques"]
    assert techniques["natal"]["status"] == "production"
    for name, item in techniques.items():
        assert item["required_inputs"], name
        if item["kind"] == "predictive":
            assert item["requires_target"] is True, name
            assert "target_datetime" in item["required_inputs"] or "target_year" in item["required_inputs"], name
        if item["status"] != "production":
            assert item["implementation"] is None, name
            assert item["source_policy"] != "local_ephh_vendored", name
        if item["source_policy"].startswith("vedic"):
            assert item["status"] != "production", name

    print(f"PASS technique registry: {len(techniques)} methods; predictive activation and source isolation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
