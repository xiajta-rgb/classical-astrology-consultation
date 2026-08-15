#!/usr/bin/env python3
"""Create bounded, machine-readable natal hypothesis cards.

This layer is intentionally conservative: it refuses to create life
interpretations while the natal release gate is HOLD, and it never produces an
S-grade conclusion automatically. A downstream consultation writer must still
choose the leading hypothesis and write the observable translation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TOPICS = {
    "self_decision": {"label": "自我与决策", "primary": (1,), "scan": (1, 5, 10)},
    "money_income": {"label": "金钱与收入", "primary": (2, 11, 10), "scan": (2, 4, 5, 8, 10, 11)},
    "shared_resources": {"label": "共享资源与债务", "primary": (8, 7, 2), "scan": (8, 7, 2, 4)},
    "career_public_role": {"label": "职业与公共角色", "primary": (10, 1, 6, 7, 11), "scan": (10, 1, 6, 7, 11)},
    "relationship_family": {"label": "关系与家庭", "primary": (7, 4, 1, 8), "scan": (7, 4, 1, 8)},
    "creation_children": {"label": "创作与子女", "primary": (5, 1, 4, 8), "scan": (5, 1, 4, 8)},
    "pressure_risk": {"label": "压力与风险", "primary": (6, 8, 12), "scan": (6, 8, 12, 2)},
}


def _read_json(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"cannot decode JSON: {path}")


def _house_map(package: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(item["house"]): item for item in package["chart_facts"]["rulership_fly_ins"]}


def _state_map(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["planet"]: item for item in package["chart_facts"]["planetary_state"]["planets"]}


def _state_evidence(package: dict[str, Any], houses: tuple[int, ...]) -> list[dict[str, Any]]:
    fly = _house_map(package)
    state = _state_map(package)
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for house in houses:
        ruler = fly.get(house, {}).get("ruler")
        if not ruler or ruler in seen or ruler not in state:
            continue
        seen.add(ruler)
        item = state[ruler]
        essential = ",".join(item.get("essential_dignity", [])) or "无已确认本质尊贵"
        fact = f"{ruler}：本质状态[{essential}]，sect={item.get('sect')}，角性={item.get('angularity')}"
        items.append({
            "id": f"STATE_{ruler}",
            "fact": fact,
            "house": house,
            "ruler": ruler,
            "independence_group": "planetary_state",
            "dependency_key": f"state:{ruler}:{essential}:{item.get('sect')}:{item.get('angularity')}",
            "source_ids": ["judgment-algorithm", "R01", "R25", "R26"],
            "source_cluster": "planetary_state_rules",
        })
    return items


def _facts_for_houses(package: dict[str, Any], houses: tuple[int, ...]) -> list[dict[str, Any]]:
    fly = _house_map(package)
    placement = package["chart_facts"]["placements"]
    facts: list[dict[str, Any]] = []
    for house in houses:
        item = fly.get(house)
        if not item:
            continue
        ruler = item.get("ruler")
        p = placement.get(ruler, {})
        facts.append({
            "id": f"HOUSE_{house}_RULER_PLACEMENT",
            "fact": f"{house}宫宫头{item.get('cusp_sign')}，宫主{ruler}落{p.get('house', 'N/A')}宫{p.get('sign', 'N/A')}",
            "house": house,
            "ruler": ruler,
            "independence_group": "house_rulership",
            "dependency_key": f"{ruler}:{p.get('house', 'N/A')}:{p.get('sign', 'N/A')}",
            "source_ids": ["house-matrix", "Chart_Facts"],
            "source_cluster": "house_responsibility",
        })
    return facts


def _candidate_evidence(package: dict[str, Any], topic: str) -> dict[str, Any] | None:
    topic_data = package.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {}).get(topic, {})
    if not topic_data:
        return None
    traditional = ", ".join(topic_data.get("traditional_domicile_rulers", [])) or "N/A"
    competing = ", ".join(topic_data.get("competing_candidate_planets", [])) or "无"
    conflict_houses = ", ".join(map(str, topic_data.get("conflict_houses", []))) or "无"
    fact = f"主题候选审计：传统宫主[{traditional}]；其他尊贵候选[{competing}]；分歧宫位[{conflict_houses}]；状态={topic_data.get('status', 'unknown')}"
    return {
        "id": f"CANDIDATE_{topic}",
        "fact": fact,
        "house": topic_data.get("houses", [None])[0],
        "ruler": traditional,
        "independence_group": "rulership_candidate",
        "dependency_key": f"candidate:{topic}:{traditional}:{competing}:{conflict_houses}",
        "source_ids": ["judgment-algorithm", "R01"],
        "source_cluster": "dignity_candidate_rules",
        "rule_card_ids": ["QI-017"],
    }


def _relationship_evidence(package: dict[str, Any], topic: str) -> list[dict[str, Any]]:
    topic_data = package.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {}).get(topic, {})
    primary = set(TOPICS.get(topic, {}).get("primary", ()))
    fly = {int(item.get("house")): item for item in package.get("chart_facts", {}).get("rulership_fly_ins", [])}
    primary_rulers = {fly.get(house, {}).get("ruler") for house in primary if fly.get(house, {}).get("ruler")}
    evidence: list[dict[str, Any]] = []
    aspects = []
    for item in package.get("chart_facts", {}).get("aspect_validation", []):
        if item.get("planet1") not in primary_rulers and item.get("planet2") not in primary_rulers:
            continue
        if item.get("evidence_layer") != "classical_core":
            continue
        aspects.append(item)
    aspects.sort(key=lambda item: (item.get("support_level", "unknown"), str(item.get("planet1")), str(item.get("planet2"))))
    for index, item in enumerate(aspects[:3], start=1):
        p1, p2 = item.get("planet1"), item.get("planet2")
        kind = item.get("type") or item.get("aspect_name") or "unknown"
        evidence.append({
            "id": f"ASPECT_{topic}_{index}_{p1}_{p2}_{kind}",
            "fact": f"相位候选：{p1} {kind} {p2}；character={item.get('aspect_character')}; evidence_layer={item.get('evidence_layer')}; support_level={item.get('support_level')}; delivery_status={item.get('delivery_status')}",
            "house": None,
            "ruler": p1 if p1 in primary_rulers else p2,
            "independence_group": "aspect_validation",
            "dependency_key": f"aspect:{p1}:{p2}:{kind}:{item.get('support_level')}",
            "source_ids": ["Chart_Facts", "R21"],
            "source_cluster": "aspect_validation",
        })
    reception_audit = {
        item.get("direction"): item.get("connection_status")
        for item in package.get("chart_facts", {}).get("supplied_reception_validation", {}).get("connection_audit", [])
    }
    supported_receptions = package.get("chart_facts", {}).get("supplied_reception_validation", {}).get("supported_domicile_claims", 0)
    if supported_receptions:
        for index, item in enumerate(package.get("chart_facts", {}).get("expected_domicile_receptions", []), start=1):
            direction = item.get("direction", "")
            left, _, right = direction.partition("->")
            if left not in primary_rulers and right not in primary_rulers:
                continue
            evidence.append({
                "id": f"RECEPTION_{topic}_{index}_{left}_{right}",
                "fact": f"接纳方向候选：{direction}；当前只确认尊贵方向，连接与应用/分离仍需度数核验",
                "house": None,
                "ruler": left,
                "independence_group": "reception_validation",
                "dependency_key": f"reception:{direction}:direction_only",
                "source_ids": ["Chart_Facts", "R19"],
                "source_cluster": "reception_validation",
                "connection_status": reception_audit.get(direction, "not_supplied"),
            })
            if len(evidence) >= 5:
                break
    return evidence


def _dynamic_hypotheses(package: dict[str, Any], topic: str, fallback: tuple[str, str, str]) -> tuple[str, str, str, dict[str, Any] | None]:
    topic_data = package.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {}).get(topic, {})
    candidate = _candidate_evidence(package, topic)
    if not topic_data:
        return fallback[0], fallback[1], fallback[2], candidate
    traditional = ", ".join(topic_data.get("traditional_domicile_rulers", [])) or "N/A"
    competing = ", ".join(topic_data.get("competing_candidate_planets", [])) or "无"
    houses = ", ".join(map(str, topic_data.get("conflict_houses", []))) or "无"
    h1 = f"主线先看{topic}责任链的传统宫主：{traditional}；再沿宫主落宫判断交付领域。"
    if competing != "无":
        h2 = f"竞争解释来自其他尊贵候选：{competing}，分歧集中在第{houses}宫；没有度数/相位区分时不选胜者。"
    else:
        h2 = "当前没有超出传统宫主链的尊贵候选；仍需用相位、接纳和现实观察检验主线。"
    observable = f"现实观察应围绕{topic}责任链的具体交付、候选分歧和可复核记录，而不是抽象性格标签。"
    return h1, h2, observable, candidate


def _limitations(package: dict[str, Any], houses: tuple[int, ...]) -> list[str]:
    state = _state_map(package)
    fly = _house_map(package)
    limits = []
    for house in houses:
        ruler = fly.get(house, {}).get("ruler")
        item = state.get(ruler, {})
        if "fall" in item.get("essential_dignity", []) or item.get("angularity") == "cadent":
            limits.append(f"{ruler}的状态包含" + ("失势" if "fall" in item.get("essential_dignity", []) else "果宫落点"))
    if any(item.get("needs_degrees") for item in package["chart_facts"].get("aspect_validation", [])):
        limits.append("相位缺少度数，不能确认应用/分离和精确容许度")
    return limits or ["未发现可在当前状态层确认的限制；仍需主题级反证"]


def _observation_contract(package: dict[str, Any], topic: str) -> dict[str, Any]:
    all_observations = package.get("observations", {}).get(topic, [])
    observations = [item for item in all_observations if item.get("active") is True]
    tombstones = [
        {key: item.get(key) for key in ("id", "record_version", "state", "withdrawal_reason")}
        for item in all_observations
        if item.get("tombstone") is True
    ]
    validation = package.get("observation_validation", {})
    topic_findings = [finding for finding in validation.get("findings", []) if finding.startswith(f"{topic}[") or finding.startswith(f"{topic}:")]
    if topic_findings:
        status = "invalid"
    elif observations:
        status = "collected"
    elif tombstones:
        status = "withdrawn_only"
    else:
        status = "uncollected"
    return {
        "status": status,
        "interpretation_boundary": "uncollected_is_not_counterevidence; withdrawn_is_not_support",
        "items": observations,
        "tombstones": tombstones,
        "findings": topic_findings,
        "required_fields": ["id", "statement", "source_type", "source_locator", "relation", "confidence"],
    }


def _templates(topic: str) -> tuple[str, str, str]:
    templates = {
        "self_decision": ("主体行动会沿1宫主落宫的领域交付", "自我决策会被5/10宫事务重新定向", "现实中先观察再把个人判断投入具体作品、职责或项目"),
        "money_income": ("收入通过2/10/11宫主链和可交付技能形成", "家庭、创作、债务或共享资源会争夺同一现金流", "把收入来源、固定支出和共同资金分开记录"),
        "shared_resources": ("共同资源通过7/8宫责任链进入契约与分配机制", "共同资源更容易表现为义务、延迟或退出条件", "在合作前明确授权、分账、债务和退出条款"),
        "career_public_role": ("职业通过10宫主落点和6/11宫链转化为可交付工作", "职业发展受工作负荷、客户关系或组织授权限制", "先定义交付边界，再扩大职责范围"),
        "relationship_family": ("关系议题沿7/4/1宫主链进入生活安排", "关系承诺会与家庭责任、共同资源或个人自主权冲突", "把居住、家庭责任和共同财务写成可核对规则"),
        "creation_children": ("创作/子女议题通过5宫主落点连接资源与个人投入", "创作/子女议题会带来持续成本或情绪牵引", "区分作品投入、子女责任和投机风险，不混算为一项"),
        "pressure_risk": ("压力来自6/8/12宫责任链对时间与资源的占用", "压力会通过工作负荷、债务或隐性消耗累积", "先做现实负荷盘点，再讨论象征层的改善方案"),
    }
    return templates[topic]


def _version_gate(package: dict[str, Any], source_audit: dict[str, Any] | None = None) -> tuple[str, dict[str, bool], list[str], list[dict[str, Any]]]:
    metadata = package.get("metadata", {})
    lock = {str(key): bool(value) for key, value in metadata.get("rule_version_lock", {}).items()}
    required = ("terms", "triplicity", "faces", "reception", "aspect")
    blockers = [key for key in required if lock.get(key) is not True]
    conflict_status = (source_audit or {}).get("conflict_status", [])
    audit_blockers = list((source_audit or {}).get("version_gate_blockers", []))
    blockers = sorted(set(blockers + audit_blockers))
    gate = "locked" if not blockers and (not source_audit or source_audit.get("version_gate") == "publish") else "hold"
    return gate, lock, blockers, conflict_status


def build(package: dict[str, Any], source_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    gate = package.get("release_gate", {})
    version_gate, version_lock, version_blockers, conflict_status = _version_gate(package, source_audit)
    if not gate.get("publishable") or version_gate != "locked":
        reasons = gate.get("blockers", []) + gate.get("warnings", [])
        if version_blockers:
            reasons.append("rule_version_gate_hold:" + ",".join(version_blockers))
        return {
            "version": "INFERENCE-0.1-candidate",
            "chart_id": package.get("chart_id"),
            "status": "hold",
            "reason": reasons,
            "rule_version_gate": version_gate,
            "rule_version_lock": version_lock,
            "version_gate_blockers": version_blockers,
            "source_conflict_status": conflict_status,
            "observation_validation": package.get("observation_validation", {"status": "not_collected"}),
            "cards": [],
        }
    cards = []
    for topic, config in TOPICS.items():
        h1, h2, observable = _templates(topic)
        h1, h2, observable, candidate_item = _dynamic_hypotheses(package, topic, (h1, h2, observable))
        evidence_items = _facts_for_houses(package, config["scan"])
        evidence_items += _state_evidence(package, config["primary"])
        evidence_items += _relationship_evidence(package, topic)
        if candidate_item:
            evidence_items.append(candidate_item)
        facts = [item["fact"] for item in evidence_items]
        cards.append({
            "topic": topic,
            "label": config["label"],
            "status": "candidate",
            "grade": "B",
            "rule_version_gate": version_gate,
            "rule_version_lock": version_lock,
            "source_conflict_status": conflict_status,
            "observation_contract": _observation_contract(package, topic),
            "H1_leading": h1,
            "H2_runner_up": h2,
            "Evidence": facts,
            "evidence_items": evidence_items,
            "evidence_ids": [item["id"] for item in evidence_items],
            "chart_specific_anchor": "；".join(facts[:3]),
            "Rule": "先按主题责任链读取宫位，再看宫主落点、行星状态、相位和接纳；不把占据宫位等同于宫主责任。",
            "Inference": "待下游咨询层结合独立证据选择领先假设；本卡不自动写成命运断言。",
            "Observable_translation_candidate": observable,
            "Counter_test": _limitations(package, config["scan"]) + (["主宰候选存在并列；必须用宫位度数、sect、相位或接纳区分"] if candidate_item and package.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {}).get(topic, {}).get("competing_candidate_planets") else []),
            "Missing_discriminator": ["精确度数与应用/分离", "主题相关现实资料", "若涉及时间问题则需单独时限技术"] + (["主宰候选分歧的区分证据"] if candidate_item and package.get("chart_facts", {}).get("rulership_candidates", {}).get("topics", {}).get(topic, {}).get("competing_candidate_planets") else []),
            "source_refs": ["references/house-matrix.md", "references/judgment-algorithm.md", "references/evidence-and-language.md"],
        })
    dependency_index: dict[str, list[str]] = {}
    for card in cards:
        for evidence_id in card["evidence_ids"]:
            dependency_index.setdefault(evidence_id, []).append(card["topic"])
    return {
        "version": "INFERENCE-0.1-candidate",
        "chart_id": package.get("chart_id"),
        "status": "candidate",
        "rule_version_gate": version_gate,
        "rule_version_lock": version_lock,
        "version_gate_blockers": version_blockers,
        "source_conflict_status": conflict_status,
        "observation_validation": package.get("observation_validation", {"status": "not_collected"}),
        "cards": cards,
        "evidence_dependency_index": {key: topics for key, topics in dependency_index.items() if len(topics) > 1},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build bounded natal hypothesis cards")
    parser.add_argument("package", type=Path)
    parser.add_argument("--source-audit", type=Path, help="source-registry audit JSON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_audit = _read_json(args.source_audit) if args.source_audit else None
    result = build(_read_json(args.package), source_audit)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
