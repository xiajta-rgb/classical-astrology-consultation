#!/usr/bin/env python3
"""Build a decoupled natal interpretation report from Chart Facts.

The module registry owns topic knowledge and safety language. This script only
matches registry rules against computed facts, attaches evidence IDs, and
renders a report. It never calculates planetary positions or activates timing
techniques.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SALIENCE_RANK = {"context": 0, "supporting": 1, "high": 2, "critical": 3}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _state(package: dict[str, Any], planet: str) -> dict[str, Any]:
    return next((item for item in package["chart_facts"]["planetary_state"]["planets"] if item.get("planet") == planet), {})


def _placement(package: dict[str, Any], planet: str) -> dict[str, Any]:
    return package["chart_facts"].get("placements", {}).get(planet, {})


def _ruler(package: dict[str, Any], house: int) -> dict[str, Any]:
    return next((item for item in package["chart_facts"].get("rulership_fly_ins", []) if int(item.get("house", 0)) == house), {})


def _aspect(package: dict[str, Any], p1: str, p2: str, aspect: str, max_orb: float) -> dict[str, Any] | None:
    for item in package["chart_facts"].get("aspect_validation", []):
        if {item.get("planet1"), item.get("planet2")} != {p1, p2}:
            continue
        if item.get("type") != aspect:
            continue
        if float(item.get("orb", 999)) <= max_orb:
            return item
    return None


def _match(package: dict[str, Any], rule: dict[str, Any]) -> tuple[bool, list[str]]:
    kind = rule.get("kind")
    if kind == "ruler_in_house":
        item = _ruler(package, int(rule["house"]))
        return bool(item) and item.get("ruler_house") == rule.get("ruler_house"), [f"HOUSE_{rule['house']}_RULER_{item.get('ruler', 'unknown')}"]
    if kind == "placement":
        p = _placement(package, rule["planet"])
        state = _state(package, rule["planet"])
        ok = bool(p)
        if "house" in rule:
            ok = ok and p.get("house") == rule["house"]
        if "sign" in rule:
            ok = ok and p.get("sign") == rule["sign"]
        if "dignity" in rule:
            ok = ok and rule["dignity"] in state.get("essential_dignity", [])
        if "retrograde" in rule:
            ok = ok and p.get("is_retrograde") is rule["retrograde"]
        return ok, [f"PLACEMENT_{rule['planet']}", f"STATE_{rule['planet']}"]
    if kind == "cluster":
        houses = [int(_placement(package, planet).get("house", -1)) for planet in rule["planets"]]
        return bool(houses) and all(house == rule["house"] for house in houses), [f"PLACEMENT_{planet}" for planet in rule["planets"]]
    if kind == "aspect":
        item = _aspect(package, rule["planet1"], rule["planet2"], rule["aspect"], float(rule.get("max_orb", 8)))
        if not item:
            return False, []
        return True, [f"ASPECT_{item['planet1']}_{item['planet2']}_{item['type']}"]
    raise ValueError(f"unsupported module rule kind: {kind}")


def _fact_snapshot(package: dict[str, Any], ids: list[str]) -> list[str]:
    placements = package["chart_facts"].get("placements", {})
    lines: list[str] = []
    for evidence_id in ids:
        if evidence_id.startswith("PLACEMENT_"):
            planet = evidence_id.removeprefix("PLACEMENT_")
            item = placements.get(planet, {})
            lines.append(f"{planet}={item.get('sign', 'unknown')} {item.get('degree', '?')}° / H{item.get('house', '?')}")
        elif evidence_id.startswith("STATE_"):
            planet = evidence_id.removeprefix("STATE_")
            item = _state(package, planet)
            lines.append(f"{planet}.state={','.join(item.get('essential_dignity', [])) or 'none'}; sect={item.get('sect')}; angularity={item.get('angularity')}; retrograde={item.get('motion_visibility', {}).get('is_retrograde')}")
        elif evidence_id.startswith("HOUSE_"):
            number = evidence_id.split("_")[1]
            item = _ruler(package, int(number))
            lines.append(f"H{number}: {item.get('cusp_sign')} -> {item.get('ruler')} in H{item.get('ruler_house')}")
        elif evidence_id.startswith("ASPECT_"):
            parts = evidence_id.split("_")
            item = _aspect(package, parts[1], parts[2], parts[3], 8)
            if item:
                lines.append(f"{item['planet1']} {item['type']} {item['planet2']}; orb={item['orb']}°; delivery={item.get('delivery_status')}")
    return list(dict.fromkeys(lines))


def _select_by_salience(matched: list[dict[str, Any]], policy: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep only high-salience evidence in the primary narrative.

    Lower-salience matches remain in ``deferred_evidence`` for audit and later
    expansion, but they cannot dilute the few chart signatures that define a
    topic.  Missing salience is fail-closed to ``supporting``.
    """
    minimum = str(policy.get("minimum_salience", "high"))
    minimum_rank = SALIENCE_RANK.get(minimum, SALIENCE_RANK["high"])
    eligible = [item for item in matched if SALIENCE_RANK.get(item.get("salience", "supporting"), 1) >= minimum_rank]
    max_primary = policy.get("max_primary_rules")
    if isinstance(max_primary, int) and max_primary > 0:
        primary = eligible[:max_primary]
    else:
        primary = eligible
    primary_ids = {item["rule_id"] for item in primary}
    deferred = [item for item in matched if item["rule_id"] not in primary_ids]
    return primary, deferred


def build(package: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    gate = package.get("release_gate", {})
    modules = []
    for module in registry.get("modules", []):
        if module.get("status") == "inactive_until_timing_activation":
            modules.append({
                "id": module["id"], "title": module["title"], "status": "inactive",
                "house_chain": module.get("house_chain", []), "interpretation": [module.get("fixed_statement", "")],
                "evidence": [], "counter_tests": module.get("counter_tests", []), "observable_tests": module.get("observable_tests", []),
                "safety_gate": module.get("safety_gate", ""),
            })
            continue
        matched = []
        for rule in module.get("rules", []):
            ok, evidence_ids = _match(package, rule)
            if ok:
                matched.append({"rule_id": rule["id"], "salience": rule.get("salience", "supporting"), "text": rule["text"], "evidence_ids": evidence_ids, "facts": _fact_snapshot(package, evidence_ids)})
        primary, deferred = _select_by_salience(matched, module.get("priority_policy", {}))
        status = "provisional_hold" if not gate.get("publishable") else "candidate"
        modules.append({
            "id": module["id"], "title": module["title"], "status": status,
            "house_chain": module.get("house_chain", []), "interpretation": [item["text"] for item in primary],
            "evidence": primary, "deferred_evidence": deferred,
            "priority_policy": module.get("priority_policy", {"minimum_salience": "high", "defer_supporting": True}),
            "selection": {"matched_count": len(matched), "primary_count": len(primary), "deferred_count": len(deferred), "deferred_rule_ids": [item["rule_id"] for item in deferred]},
            "counter_tests": module.get("counter_tests", []),
            "observable_tests": module.get("observable_tests", []), "safety_gate": module.get("safety_gate", ""),
        })
    return {
        "schema_version": "MODULAR-NATAL-REPORT-0.1",
        "chart_id": package.get("chart_id"),
        "status": "hold" if not gate.get("publishable") else "candidate",
        "release_gate": gate,
        "module_registry_version": registry.get("version"),
        "timing_scope": "inactive",
        "modules": modules,
    }


def render(report: dict[str, Any], package: dict[str, Any]) -> str:
    gate = report["release_gate"]
    metadata = package.get("metadata", {})
    lines = [
        "# 本命盘模块化解读报告",
        "",
        f"图表：`{report.get('chart_id')}`；状态：`{report['status'].upper()}`；资料层门禁：`{gate.get('decision', 'unknown').upper()}`。",
        f"黄道：{metadata.get('zodiac')}；宫制：{metadata.get('house_system')}；夜昼盘：{metadata.get('sect')}；ASC边界风险：{metadata.get('ascendant_boundary_risk')}。",
        "",
        "## 使用说明",
        "",
        "本报告把本命事实、主题规则、结构性推断、现实验证和限制分开。当前坐标为行政区中心且 ASC 接近 30°，所以所有主题均以条件式/暂定式输出；关键人生时间模块未启用，不提供具体年份或事件日期。",
        "",
        "## 总览",
        "",
    ]
    active = [m for m in report["modules"] if m["status"] != "inactive"]
    strongest = sorted(active, key=lambda item: len(item["evidence"]), reverse=True)[:3]
    for module in strongest:
        if module["interpretation"]:
            lines.append(f"- **{module['title']}**：{module['interpretation'][0]}")
    for module in report["modules"]:
        selection = module.get("selection", {})
        lines.extend(["", f"## {module['title']}", "", f"状态：`{module['status']}`；责任链：" + " → ".join(f"H{h}" for h in module["house_chain"]), f"优先级筛选：主征象 {selection.get('primary_count', 0)} 条；延后征象 {selection.get('deferred_count', 0)} 条。", ""])
        if module["interpretation"]:
            lines.append("### 结构性解读")
            lines.extend(f"- {text}" for text in module["interpretation"])
        else:
            lines.append("暂无满足条件的规则，保留为 N/A，不补写泛化内容。")
        if module["evidence"]:
            lines.extend(["", "### 事实锚点"])
            for evidence in module["evidence"]:
                lines.append(f"- `{evidence['rule_id']}`：" + "；".join(evidence["facts"]))
        lines.extend(["", "### 反证与限制"])
        lines.extend(f"- {item}" for item in module["counter_tests"])
        lines.extend(["", "### 现实验证"])
        lines.extend(f"- {item}" for item in module["observable_tests"])
        lines.extend(["", f"### 门禁：{module['safety_gate']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build decoupled modular natal interpretation")
    parser.add_argument("package", type=Path)
    parser.add_argument("--registry", type=Path, default=Path("references/interpretation-modules/registry.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    package = _read(args.package)
    registry = _read(args.registry)
    report = build(package, registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(render(report, package), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
