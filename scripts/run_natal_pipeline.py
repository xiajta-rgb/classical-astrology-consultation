#!/usr/bin/env python3
"""Run the canonical natal-first calculation and optional timing extension.

This command is deliberately narrower than a prose generator.  It produces a
single traceable package that later interpretation/rendering stages consume.
No global knowledge file or client case is mutated unless ``--output`` is
provided explicitly.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLIENTS_ROOT = ROOT / "clients"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from astrology_engine import calculate_natal, calculate_responsibilities  # noqa: E402
from astrology_engine import calculate_mbti, calculate_tpes  # noqa: E402
from astrology_engine.predictive import calculate_predictive  # noqa: E402
from scripts.plan_consultation import plan  # noqa: E402
from scripts.query_knowledge_plugins import query  # noqa: E402
from scripts.expand_signification_map import expand as expand_signification_map  # noqa: E402


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _case_context(case_id: str | None) -> dict[str, Any]:
    if not case_id:
        return {"status": "input_declared", "case_id": None}
    if any(part in {"", ".", ".."} for part in Path(case_id).parts) or Path(case_id).name != case_id:
        raise ValueError("case_id must be a single canonical folder name")
    case_root = CLIENTS_ROOT / case_id
    profile_path = case_root / "profile.json"
    if not profile_path.exists():
        raise ValueError(f"case_id does not exist or has no profile.json: {case_id}")
    return {
        "status": "case_loaded",
        "case_id": case_id,
        "profile_path": str(profile_path.relative_to(ROOT)),
        "analysis_root": str((case_root / "analysis").relative_to(ROOT)),
    }


def run(
    *,
    birth_datetime: str,
    lat: float | None = None,
    lon: float | None = None,
    tz: float = 8.0,
    timezone_name: str | None = None,
    house_system: str = "P",
    place: str | None = None,
    topic: str = "overall",
    knowledge_limit: int = 12,
    timing: bool = False,
    timing_technique: str | None = None,
    target_datetime: str | None = None,
    target_year: int | None = None,
    case_id: str | None = None,
) -> dict[str, Any]:
    route_plan = plan(
        topic=topic,
        has_birth_data=True,
        timing=timing,
        timing_technique=timing_technique,
    )
    if route_plan.get("status") != "ready":
        raise ValueError(
            f"consultation route is not ready: {route_plan.get('reason', 'unknown')}"
        )
    client_context = _case_context(case_id)
    natal = calculate_natal(
        birth_datetime,
        lat=lat,
        lon=lon,
        tz=tz,
        timezone_name=timezone_name,
        house_system=house_system,
        place=place,
    )
    signification = calculate_responsibilities(
        birth_datetime,
        lat=lat,
        lon=lon,
        tz=tz,
        timezone_name=timezone_name,
        house_system=house_system,
        place=place,
        chart_facts=natal,
    )
    semantic_coverage = expand_signification_map(natal, signification)
    state = calculate_predictive(
        "essential_dignities",
        birth_datetime,
        lat=lat,
        lon=lon,
        tz=tz,
        timezone_name=timezone_name,
        house_system=house_system,
        place=place,
    )
    reception = calculate_predictive(
        "mutual_reception",
        birth_datetime,
        lat=lat,
        lon=lon,
        tz=tz,
        timezone_name=timezone_name,
        house_system=house_system,
        place=place,
    )
    knowledge = []
    for plugin_id in route_plan.get("knowledge_plugins", []):
        if plugin_id == "house-ruler-flow":
            knowledge.append(query(plugin=plugin_id, module="house_rulership_flow", limit=knowledge_limit))
            continue
        module = route_plan.get("topic_module")
        knowledge.append(query(plugin=plugin_id, module=module, limit=knowledge_limit))
    # Natal-core extensions are registered during every natal pass.  Their
    # interpretive cards remain bounded and topic-sensitive, but the route must
    # not treat them as isolated opt-in research files.
    for extension in route_plan.get("natal_core_extensions", []):
        extension_topic = topic if topic and topic != "overall" else None
        knowledge.append(query(symbol=extension.get("symbol"), topic=extension_topic, limit=knowledge_limit))
    status_by_module = {
        "client_context": client_context["status"],
        "chart_facts": "computed",
        "planetary_state": "computed",
        "responsibility_chain": "computed",
        "semantic_coverage": "computed",
        "reception_audit": "computed",
        "topic_knowledge": "retrieved",
        "mbti_personality": "computed_auxiliary_insight",
        "career_insight": "computed_auxiliary_insight",
        "composition": "awaiting_topic_evidence",
        "timing_extension": "computed" if timing else "inactive_until_explicit_timing",
        "release_gate": "hold_composition_required",
        "renderer": "blocked_until_release_gate",
    }
    module_trace = [
        {
            "module": item["id"],
            "version": item["version"],
            "status": status_by_module.get(item["id"], "completed"),
            "source": item["source"],
        }
        for item in route_plan.get("modules", [])
    ]
    timing_package = None
    if timing:
        timing_package = calculate_predictive(
            route_plan["timing"]["technique"],
            birth_datetime,
            target_datetime=target_datetime,
            target_year=target_year,
            lat=lat,
            lon=lon,
            tz=tz,
            timezone_name=timezone_name,
            house_system=house_system,
            place=place,
        )
    insight_modules = {item["id"] for item in route_plan.get("modules", [])}
    insights: dict[str, Any] = {}
    if "mbti_personality" in insight_modules:
        insights["mbti_personality"] = calculate_mbti(natal)
    if "career_insight" in insight_modules:
        insights["career_insight"] = calculate_tpes(natal)
    return {
        "schema_version": "NATAL-PIPELINE-1.1",
        "status": "ready_for_timing_composition" if timing else "ready_for_topic_composition",
        "route_id": route_plan.get("route_id"),
        "publication_status": "hold",
        "release_gate": {
            "decision": "hold",
            "publishable": False,
            "reasons": [
                "composition_not_run",
                "release_gate_not_run",
            ],
            "timing_status": "deferred" if timing else "not_requested",
        },
        "route_plan": route_plan,
        "client_context": client_context,
        "module_trace": module_trace,
        "chart_facts": natal,
        "responsibility_chain": signification,
        "semantic_coverage": semantic_coverage,
        "planetary_state": state,
        "typed_reception": reception,
        "knowledge": knowledge,
        "timing": timing_package,
        "insights": insights,
        "composition_contract": {
            "required_next": ["topic_evidence", "counter_testimony", "observable_translation"],
            "command": "python scripts/compose_significators.py <evidence.json>",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--birth-datetime", required=True)
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--tz", type=float, default=8.0)
    parser.add_argument("--timezone-name")
    parser.add_argument("--house-system", default="P")
    parser.add_argument("--place")
    parser.add_argument("--topic", default="overall")
    parser.add_argument("--knowledge-limit", type=int, default=12)
    parser.add_argument("--timing", action="store_true")
    parser.add_argument("--technique")
    parser.add_argument("--target-datetime")
    parser.add_argument("--target-year", type=int)
    parser.add_argument("--case-id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (args.lat is None) != (args.lon is None) or (args.lat is None and not args.place):
        parser.error("provide both --lat/--lon or --place")
    result = run(
        birth_datetime=args.birth_datetime,
        lat=args.lat,
        lon=args.lon,
        tz=args.tz,
        timezone_name=args.timezone_name,
        house_system=args.house_system,
        place=args.place,
        topic=args.topic,
        knowledge_limit=args.knowledge_limit,
        timing=args.timing,
        timing_technique=args.technique,
        target_datetime=args.target_datetime,
        target_year=args.target_year,
        case_id=args.case_id,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.case_id and args.output is None:
        args.output = CLIENTS_ROOT / args.case_id / "analysis" / "chart-facts" / f"NATAL-{result['chart_facts']['chart_id']}.json"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
