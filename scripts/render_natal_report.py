#!/usr/bin/env python3
"""Render an evidence-first natal audit/report from build_natal_facts output.

The renderer never fills missing facts with prose. A hold-case is rendered as
an audit document and can be rejected with ``--require-publish``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.score_hypothesis_cards import score as score_cards
except ModuleNotFoundError:  # direct execution from the scripts directory
    from score_hypothesis_cards import score as score_cards


def _read_json(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"cannot decode JSON: {path}")


PLANET_LABELS = {
    "太阳": "太阳", "月亮": "月亮", "水星": "水星", "金星": "金星", "火星": "火星",
    "木星": "木星", "土星": "土星", "天王": "天王星", "海王": "海王星", "冥王": "冥王星",
    "北交": "北交点", "南交": "南交点", "凯龙": "凯龙", "婚神": "婚神", "福点": "福点",
}


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "／") for value in row) + " |")
    return lines


def _paragraph_evidence_rows(package: dict[str, Any], source_audit: dict[str, Any] | None) -> list[list[str]]:
    gate = package.get("release_gate", {})
    source_gate = (source_audit or {}).get("version_gate", "not_evaluated")
    publishable = bool(gate.get("publishable")) and source_gate in ("publish", "not_evaluated")
    status = "UNLOCKED" if publishable else "BLOCKED"
    if publishable:
        scope = "可进入 Evidence→Rule→Inference，但仍需反证"
        blockers = "无"
    else:
        scope = "仅可报告事实、缺失项和限制；不得写生活结论"
        blockers = "；".join(gate.get("blockers", [])) or "source_version_gate_hold"
    rows = []
    for section in ("核心判断", "结构性优势", "结构性矛盾", "风险边界", "咨询建议"):
        rows.append([section, status, scope, blockers])
    return rows


def compare_scores(supplied: dict[str, Any], recomputed: dict[str, Any]) -> list[str]:
    """Return material differences so a hand-edited score cannot be trusted."""
    findings: list[str] = []
    for key in ("rule_version_gate", "version_gate_blockers"):
        if supplied.get(key) != recomputed.get(key):
            findings.append(f"score mismatch: {key}")
    expected = {item.get("topic"): item for item in recomputed.get("cards", [])}
    actual = {item.get("topic"): item for item in supplied.get("cards", [])}
    for topic in sorted(set(expected) | set(actual)):
        if topic not in expected or topic not in actual:
            findings.append(f"score mismatch: topic {topic}")
            continue
        for key in ("natural_grade_cap", "grade_cap", "source_upgrade_eligibility", "source_profiles", "source_limits", "publication_reasons", "counter_test_summary", "observation_summary", "effective_evidence_weight", "independent_groups", "independent_source_clusters", "version_gate", "version_gate_blockers", "shared_evidence_ids", "source_ids", "source_layers", "source_conflict_clusters", "source_quality", "reception_connection_statuses"):
            if actual[topic].get(key) != expected[topic].get(key):
                findings.append(f"score mismatch: {topic}.{key}")
    return findings


def render(
    package: dict[str, Any],
    source_audit: dict[str, Any] | None = None,
    score_output: dict[str, Any] | None = None,
    score_mismatches: list[str] | None = None,
    dictionary_audit: dict[str, Any] | None = None,
    score_diff: dict[str, Any] | None = None,
) -> str:
    metadata = package["metadata"]
    facts = package["chart_facts"]
    gate = package["release_gate"]
    lines = [
        "# 本命盘事实与发布审计报告",
        "",
        f"- chart_id：`{package.get('chart_id')}`",
        f"- 来源：`{metadata.get('source', 'undeclared')}`",
        f"- 发布决策：**{gate.get('decision', 'hold').upper()}**",
        "",
        "> 本文档只发布已验证的事实、状态和缺失项；它不是在数据不足时自动生成的命理结论。",
        "",
        "## 数据契约",
        "",
    ]
    contract_rows = [
        ["黄道体系", metadata.get("zodiac")],
        ["宫制", metadata.get("house_system")],
        ["日夜盘", f"{metadata.get('sect')}（{metadata.get('sect_source')}，confidence={metadata.get('sect_confidence', 'none')}）"],
        ["行星度数", "已提供" if metadata.get("degrees_available") else "缺失"],
        ["上升边界风险", metadata.get("ascendant_boundary_risk")],
        ["规则版本", json.dumps(metadata.get("rule_versions", {}), ensure_ascii=False)],
        ["规则版本锁", "已锁定" if all(metadata.get("rule_version_lock", {}).values()) else "未锁定"],
        ["缺失字段", ", ".join(metadata.get("missing_contract_fields", [])) or "无"],
    ]
    lines += _table(["字段", "状态"], contract_rows)
    lines += ["", "## Chart Facts：行星与宫位", ""]
    placement_rows = []
    for planet, item in facts.get("placements", {}).items():
        placement_rows.append([PLANET_LABELS.get(planet, planet), item.get("sign", "N/A"), item.get("degree", "N/A"), item.get("house", "N/A")])
    lines += _table(["对象", "星座", "度数", "宫位"], placement_rows)
    provenance_rows = [[key, value] for key, value in facts.get("provenance", {}).items()]
    if provenance_rows:
        lines += ["", "### 事实来源层", ""]
        lines += _table(["字段", "来源/计算状态"], provenance_rows)
    lines += ["", "## 宫位责任与飞宫", ""]
    fly_rows = [[item.get("house"), item.get("cusp_sign"), item.get("ruler"), item.get("ruler_house", "N/A")] for item in facts.get("rulership_fly_ins", [])]
    lines += _table(["宫位", "宫头", "传统宫主", "宫主落宫"], fly_rows)
    lines += ["", "## 行星状态", ""]
    state_rows = []
    for item in facts.get("planetary_state", {}).get("planets", []):
        if item.get("layer") != "classical":
            continue
        essential = ", ".join(item.get("essential_dignity", [])) or "未发现已确认本质尊贵"
        motion = item.get("motion_visibility", {})
        speed = motion.get("speed") if motion.get("speed_status") == "declared" else motion.get("speed_status", "unknown")
        retrograde = motion.get("is_retrograde") if motion.get("retrograde_status") == "declared" else motion.get("retrograde_status", "unknown")
        visibility = motion.get("visibility") if motion.get("visibility_status") == "declared" else motion.get("visibility_status", "unknown")
        state_rows.append([item.get("planet"), essential, item.get("sect"), item.get("angularity"), item.get("term", {}).get("status"), item.get("face", {}).get("status"), speed, retrograde, visibility])
    lines += _table(["行星", "本质状态", "sect", "角性", "界", "面", "速度", "逆行", "可见性"], state_rows)
    lines += ["", "## 相位验证", ""]
    aspect_rows = []
    for item in facts.get("aspect_validation", []):
        aspect_rows.append([item.get("planet1"), item.get("planet2"), item.get("type") or item.get("aspect_name"), item.get("evidence_layer", "unknown"), item.get("aspect_character", "unknown"), item.get("status"), item.get("support_level", "unknown"), item.get("delivery_status", "unknown"), item.get("orb", "N/A"), "是" if item.get("needs_degrees") else "否"])
    lines += _table(["对象1", "对象2", "相位", "证据层", "几何性质", "状态", "支持等级", "交付状态", "orb", "需度数"], aspect_rows or [["N/A", "N/A", "N/A", "unknown", "unknown", "未提供相位", "unknown", "unknown", "N/A", "否"]])
    if facts.get("supplied_aspect_duplicates") or facts.get("supplied_aspect_reverse_duplicates"):
        lines += [f"- 相位重复审计：完全重复 {len(facts.get('supplied_aspect_duplicates', []))} 条；反向重复 {len(facts.get('supplied_aspect_reverse_duplicates', []))} 条。"]
    lines += ["", "## 接纳与互容验证", ""]
    reception_rows = [[item.get("direction"), item.get("type"), item.get("from_sign"), item.get("to_sign")] for item in facts.get("expected_domicile_receptions", [])]
    lines += _table(["方向", "类型", "出发星座", "接收星座"], reception_rows or [["N/A", "未提供", "N/A", "N/A"]])
    reception_audit = facts.get("supplied_reception_validation", {})
    if reception_audit:
        lines += [f"- 接纳方向审计：支持宫主接纳 {reception_audit.get('supported_domicile_claims', 0)} 条；未匹配 {len(reception_audit.get('unsupported_domicile_claims', []))} 条；互容缺反向 {len(reception_audit.get('mutual_missing_reverse', []))} 条；连接状态 {json.dumps(reception_audit.get('connection_status_counts', {}), ensure_ascii=False)}；规则版本 `{reception_audit.get('version', 'unknown')}`。"]
    if facts.get("mutual_domicile_pairs"):
        lines += ["", "已识别双向守护互容：" + "、".join("—".join(pair) for pair in facts["mutual_domicile_pairs"])]
    lines += ["", "## 主题覆盖", ""]
    topic_rows = []
    for topic, item in package.get("topic_coverage", {}).items():
        topic_rows.append([topic, ", ".join(map(str, item.get("houses", []))), ", ".join(map(str, item.get("covered", []))), item.get("status")])
    lines += _table(["主题", "责任宫位", "已有宫位事实", "状态"], topic_rows)
    chains = package.get("responsibility_chains", {})
    chain_rows = []
    for topic, item in chains.get("topics", {}).items():
        path = " → ".join(f"{step.get('house')}:{step.get('ruler')}→{step.get('ruler_house', 'N/A')}" for step in item.get("path", []))
        chain_rows.append([topic, path or "N/A", ", ".join(item.get("unique_rulers", [])) or "N/A", ", ".join(item.get("within_topic_reused_rulers", [])) or "无"])
    if chain_rows:
        lines += ["", "## 责任链与共享证据审计", ""]
        lines += _table(["主题", "宫位→宫主→落宫", "去重后宫主", "主题内重复"], chain_rows)
        shared = ", ".join(chains.get("cross_topic_shared_rulers", [])) or "无"
        lines += [f"- 跨主题共享宫主：{shared}。相同宫主的行星状态在评分层只计一次；宫位责任链仍分别保留。"]
    candidate_data = facts.get("rulership_candidates", {})
    candidate_rows = []
    for item in candidate_data.get("houses", []):
        claims = []
        for candidate in item.get("candidates", []):
            claims.append(f"{candidate.get('planet')}[{','.join(candidate.get('claims', []))}]")
        detail = item.get("candidate_claim_detail", {})
        unavailable = ",".join(detail.get("unavailable_claim_types", [])) or "无"
        candidate_rows.append([
            item.get("house"),
            item.get("place", {}).get("sign", "N/A"),
            item.get("traditional_domicile_ruler", "N/A"),
            "; ".join(claims) or "N/A",
            item.get("status", "unknown"),
            unavailable,
        ])
    if candidate_rows:
        lines += ["", "## 尊贵主宰候选审计", "", "此表保留各项尊贵主张，不把它们相加为单一吉凶分数；传统宫主仍是责任链锚点。", f"三分主宰依赖 sect：{candidate_data.get('sect')}（{candidate_data.get('sect_source')}，confidence={candidate_data.get('sect_confidence', 'unknown')}）；低置信度只作候选，不作裁决。", ""]
        lines += _table(["位置", "星座", "传统宫主", "尊贵候选（主张）", "状态", "未能核验"], candidate_rows)
        candidate_topic_rows = []
        for topic, item in candidate_data.get("topics", {}).items():
            candidate_topic_rows.append([
                topic,
                ", ".join(item.get("traditional_domicile_rulers", [])) or "N/A",
                ", ".join(item.get("competing_candidate_planets", [])) or "无",
                ", ".join(map(str, item.get("conflict_houses", []))) or "无",
                item.get("status", "unknown"),
            ])
        if candidate_topic_rows:
            lines += ["", "### 主题级主宰分歧", "", "分歧本身是结果：在缺少区分证据时保留并列，不把候选数量当作结论强度。", ""]
            lines += _table(["主题", "传统宫主", "其他候选", "分歧宫位", "状态"], candidate_topic_rows)
    sensitive_gates = package.get("sensitive_topic_gates", {})
    if sensitive_gates:
        lines += ["", "### 高风险主题输出闸门", ""]
        lines += _table(["主题", "前置限制"], [[topic, gate_name] for topic, gate_name in sensitive_gates.items()])
    lines += ["", "## 证据层级", "", "- 古典七曜：太阳、月亮、水星、金星、火星、木星、土星建立宫位责任、sect、尊贵与核心交付判断。", "- 现代辅助：天王星、海王星、冥王星、交点、凯龙、婚神和现代相位不能独立升级本命结论。", "- 来源与版本：R25（本质/偶然尊贵）、R26（三分主宰）、R19（接纳）、R21（相位）；具体规则仍需与 Chart Facts 一起调用。", "", "## 核心判断", "", "N/A：发布闸门未通过时只报告事实，不生成生活结论。" if not gate.get("publishable") else "结构性判断必须在下游咨询层按 Evidence → Rule → Inference → Counter-test 生成。", "", "## 结构性优势", "", "N/A：当前报告不是解释层，避免把单一状态包装成能力结论。", "", "## 结构性矛盾", "", "N/A：当前报告不是解释层，矛盾假设需在完整度数和主题责任链齐备后生成。", "", "## 风险边界", "", "当前主要风险是数据边界而非命理结论：缺失度数、宫制或上升临界资料会改变相位与宫位判断。", "", "## 咨询建议", "", "先补齐出生日期、准确时间、地点/经纬度、黄道体系、宫制和行星度数，再进入本命解释。", "", "## 证据链与发布闸门", ""]
    if source_audit:
        lines += ["", "## 来源冲突簇状态", ""]
        lines += _table(["冲突簇", "版本键", "状态", "当前值"], [[item.get("id"), ", ".join(item.get("version_keys", [])) or "N/A", item.get("state"), json.dumps(item.get("values", {}), ensure_ascii=False)] for item in source_audit.get("conflict_status", [])])
        lines += ["", f"- 来源版本闸门：**{source_audit.get('version_gate', 'not_evaluated').upper()}**", f"- 来源闸门阻塞：{', '.join(source_audit.get('version_gate_blockers', [])) or '无'}"]
    lines += ["", "## 段落级证据标签", "", "下表是正文写作的硬闸门；`BLOCKED` 段落只能写事实与边界，不能用模板句替代推断。"]
    lines += _table(["段落", "证据状态", "允许范围", "阻塞项"], _paragraph_evidence_rows(package, source_audit))
    observation_validation = package.get("observation_validation", {})
    if observation_validation:
        lines += ["", "## 现实观察与隐私状态", "", "现实观察只作为 H1/H2 判别层，不等同于星盘事实；敏感陈述只保留最小必要字段。`uncollected` 不等于没有反证，`withdrawn` 不等于支持任何假设。"]
        lines += _table(
            ["状态", "总记录", "active", "撤回/删除墓碑", "校验发现", "隐私处理", "词典版本", "词典变更"],
            [[
                observation_validation.get("status", "not_collected"),
                observation_validation.get("count", 0),
                observation_validation.get("active_count", 0),
                observation_validation.get("tombstone_count", 0),
                "；".join(observation_validation.get("findings", [])) or "无",
                "敏感记录脱敏" if any("redacted_sensitive_observation" in str(item) for items in observation_validation.get("observations", {}).values() for item in items) else "未发现敏感记录",
                observation_validation.get("sensitive_dictionary_version", "not_recorded"),
                observation_validation.get("sensitive_dictionary_audit", {}).get("change_note", "未记录"),
            ]],
        )
        if dictionary_audit:
            validation_version = observation_validation.get("sensitive_dictionary_version")
            audit_version = dictionary_audit.get("current_version")
            audit_status = dictionary_audit.get("status", "unknown")
            if validation_version != audit_version:
                audit_status = "fail_version_mismatch"
            lines += [
                f"- 词典差异审计：**{audit_status.upper()}**；当前/前一版本：`{audit_version}` / `{dictionary_audit.get('previous_version', 'N/A')}`；新增 {len(dictionary_audit.get('added_markers', []))} 条，删除 {len(dictionary_audit.get('removed_markers', []))} 条，样本变化 {len(dictionary_audit.get('changed_cases', []))} 条。",
                f"- 差异审计发现：{', '.join(dictionary_audit.get('findings', [])) or '无'}",
            ]
    if score_diff:
        diff_status = score_diff.get("status", "unknown")
        changed_topics = ", ".join(score_diff.get("changed_topics", [])) or "无"
        lines += [
            "",
            "## 观察撤回/替代评分差异审计",
            "",
            f"- 评分差异审计：**{diff_status.upper()}**；变化主题：{changed_topics}。",
            f"- 审计发现：{', '.join(score_diff.get('findings', [])) or '无'}",
        ]
    if score_output:
        lines += ["", "## 证据升级资格", "", "评分器的自然上限不是最终等级；来源限制、版本闸门和共享证据扣重共同决定可升级范围。"]
        if score_mismatches:
            lines += [f"- 评分输出一致性：**FAIL**；已忽略外部评分字段并使用重算结果。差异：{', '.join(score_mismatches)}"]
        else:
            lines += ["- 评分输出一致性：**PASS/未重算**；若要作为发布证据，必须同时提供原始卡片和来源注册表重算。"]
        score_rows = []
        for item in score_output.get("cards", []):
            observation = item.get("observation_summary", {})
            observation_label = f"{observation.get('status', 'not_evaluated')}({observation.get('count', 0)})"
            if observation.get("relations"):
                observation_label += ":" + ",".join(observation["relations"])
            score_rows.append([
                item.get("topic"),
                item.get("natural_grade_cap", "N/A"),
                item.get("grade_cap", "N/A"),
                item.get("source_upgrade_eligibility", "not_evaluated"),
                "；".join(item.get("source_limits", [])) or "无",
                "、".join(item.get("publication_reasons", [])) or "未提供",
                observation_label,
                ", ".join(item.get("reception_connection_statuses", [])) or "无",
            ])
        lines += _table(["主题", "自然上限", "实际上限", "来源资格", "来源限制", "发布理由", "现实观察", "接纳连接状态"], score_rows or [["N/A", "N/A", "N/A", "not_evaluated", "未提供评分输出", "未提供", "not_evaluated", "无"]])
    lines.append("- 事实库存：" + ("通过" if gate.get("fact_inventory_ready") else "不完整"))
    lines.append("- 本命解释就绪：" + ("通过" if gate.get("natal_interpretation_ready") else "未通过"))
    lines.append("- 阻塞项：" + ("；".join(gate.get("blockers", [])) or "无"))
    lines.append("- 警告项：" + ("；".join(gate.get("warnings", [])) or "无"))
    lines += ["", "### 证据链状态", "", "在发布闸门通过前，不生成‘主体—机制—可观察表现’的生活结论；每条结论仍需补充 Evidence → Rule → Inference → Counter-test。"]
    lines += ["", "## 不可判断项", "", "- 缺失出生资料、黄道/宫制或度数时，不能确认精确相位、应用/分离、界/面、燃烧、速度、可见性或事件时间/事件日期。", "- 未来时间技术尚未激活；本命盘不输出年份、月份或日期。", "- 本命事实不能单独确认具体婚期、投资结果、医疗结论、疾病、法律结果或他人行为。", ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an evidence-first natal audit")
    parser.add_argument("package", type=Path, help="JSON from build_natal_facts.py")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-audit", type=Path, help="source registry audit JSON")
    parser.add_argument("--score", type=Path, help="hypothesis-card score JSON")
    parser.add_argument("--cards", type=Path, help="hypothesis-card JSON used to recompute score")
    parser.add_argument("--registry", type=Path, help="source registry used to recompute score")
    parser.add_argument("--dictionary-audit", type=Path, help="sensitive dictionary diff audit JSON")
    parser.add_argument("--score-diff", type=Path, help="before/after score diff audit JSON")
    parser.add_argument("--require-publish", action="store_true", help="refuse to render when the release gate is hold")
    args = parser.parse_args()
    package = _read_json(args.package)
    if args.require_publish and not package.get("release_gate", {}).get("publishable"):
        print("REFUSED: natal release gate is HOLD", flush=True)
        return 2
    source_audit = _read_json(args.source_audit) if args.source_audit else None
    score_output = _read_json(args.score) if args.score else None
    dictionary_audit = _read_json(args.dictionary_audit) if args.dictionary_audit else None
    score_diff = _read_json(args.score_diff) if args.score_diff else None
    score_mismatches: list[str] = []
    if args.cards and args.registry:
        recomputed = score_cards(_read_json(args.cards), _read_json(args.registry), package, source_audit)
        if score_output:
            score_mismatches = compare_scores(score_output, recomputed)
        score_output = recomputed
    text = render(package, source_audit, score_output, score_mismatches, dictionary_audit, score_diff)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
