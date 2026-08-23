#!/usr/bin/env python3
"""Build bounded, non-promoting module drafts from the article exploration map."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARDS = ROOT / "references/knowledge-modules/distilled/cards.jsonl"
DEFAULT_EXPLORATION = ROOT / "references/knowledge-modules/distilled/exploration.json"
DEFAULT_JSON = ROOT / "references/knowledge-modules/distilled/module-drafts.json"
DEFAULT_MD = ROOT / "references/knowledge-modules/distilled/module-drafts.md"


DRAFTS: dict[str, dict[str, Any]] = {
    "timing_deferred": {
        "title": "时限与激活边界候选",
        "layer": "deferred_research",
        "include_boundary": "只登记行运、返照、推运、法达、校时等方法的条件与资料需求。",
        "exclude_boundary": "不从本命候选卡直接生成年份、月份、日期或确定事件。",
        "next_test": "用户明确时间问题后，锁定出生时间精度、方法版本、计算数据，并加入反例。",
    },
    "modern_extension": {
        "title": "现代外行星与小行星扩展候选",
        "layer": "research_extension",
        "include_boundary": "保留天王、海王、冥王、凯龙、莉莉丝、小行星等现代术语的来源片段。",
        "exclude_boundary": "不并入古典核心，不用现代标签覆盖宫主、尊贵、sect 或相位责任链。",
        "next_test": "为每类现代对象补至少两份独立来源，并与古典基线做隔离对照。",
    },
    "house_rulership": {
        "title": "宫位、轴点与宫主责任链候选",
        "layer": "candidate_structure",
        "include_boundary": "把宫位、角点、宫主和飞宫片段整理为责任主体—承载宫位的待验证链条。",
        "exclude_boundary": "宫位标签不能单独推出身份、健康、灾难或社会结果；不混用未锁定宫制。",
        "next_test": "用至少两份独立来源和合成 Chart Facts 检验责任链、重复计数与反例。",
    },
    "aspect_synthesis": {
        "title": "相位、接纳与组合机制候选",
        "layer": "candidate_structure",
        "include_boundary": "保留相位组合、接纳和状态互动作为待验证机制入口。",
        "exclude_boundary": "单一刑、拱、冲或‘正负相位’不能直接转成固定人格或事件结论。",
        "next_test": "锁定相位容许度、应用/分离、sect、尊贵与接纳类型，并进行正反例回归。",
    },
    "planet_sign_translation": {
        "title": "行星—星座符号翻译候选",
        "layer": "candidate_signification",
        "include_boundary": "把行星和星座词组作为初步符号翻译，等待宫位责任和状态补全。",
        "exclude_boundary": "星座或行星单标签不能覆盖宫主责任、落宫、尊贵、可见性和现实观察。",
        "next_test": "加入完整 Chart Facts、行星状态、宫主链和反向案例，检查泛化程度。",
    },
    "relationship_adapter": {
        "title": "关系、家庭与合盘适配候选",
        "layer": "domain_adapter",
        "include_boundary": "将关系、家庭、伴侣和合盘词汇作为领域适配入口，不改变底层责任链。",
        "exclude_boundary": "不输出伴侣定性、必然婚姻/分离或家庭身份判断；敏感关系内容继续受门禁约束。",
        "next_test": "至少区分双方 Chart Facts、七宫/宫主、金星/月亮等责任，并加入不支持案例。",
    },
    "career_money_adapter": {
        "title": "事业、工作与资源适配候选",
        "layer": "domain_adapter",
        "include_boundary": "把事业、工作、收入和资产词汇作为主题检索入口，拆分取得、交付与持续性。",
        "exclude_boundary": "不把财富、晋升、成名或房产表述升级为保证式结果。",
        "next_test": "用宫主链、行星能力、现实条件和正负对照盘检验资源取得与持续性的区分。",
    },
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build(cards: list[dict[str, Any]], exploration: dict[str, Any]) -> dict[str, Any]:
    cards_by_id = {str(card["id"]): card for card in cards}
    assignments = {str(row["card_id"]): row for row in exploration.get("assignments", [])}
    modules: list[dict[str, Any]] = []
    for cluster_id, policy in DRAFTS.items():
        cluster = exploration.get("clusters", {}).get(cluster_id, {})
        card_ids = [str(card_id) for card_id in cluster.get("card_ids", [])]
        ranked = sorted(
            (assignments[card_id] for card_id in card_ids if card_id in assignments),
            key=lambda row: (-int(row.get("review_score", 0)), row["card_id"]),
        )
        samples = []
        for assignment in ranked[:5]:
            card = cards_by_id[assignment["card_id"]]
            samples.append({
                "card_id": assignment["card_id"],
                "title": card.get("title"),
                "review_score": assignment.get("review_score", 0),
                "review_status": assignment.get("review_status"),
                "quality_flags": assignment.get("quality_flags", []),
            })
        modules.append({
            "id": cluster_id,
            **policy,
            "status": "candidate_only",
            "grade_cap": "C",
            "card_count": len(card_ids),
            "representative_cards": samples,
            "source_constraint": "all retained cards currently come from one user-provided公众号 account; independent-source support is absent",
            "promotion_gate": [
                "source locator and original span remain auditable",
                "at least two independent sources support the mechanism",
                "a disconfirming case or counterexample is recorded",
                "Chart Facts, house system, aspect version and sensitive-topic gate pass",
                "machine regression confirms no duplicate counting or runtime leakage",
            ],
        })
    return {
        "schema_version": "ARTICLE-DISTILLATION-MODULE-DRAFTS-0.1",
        "method": "cluster_policy_plus_ranked_representative_cards",
        "status": "candidate_only",
        "grade_cap": "C",
        "source_id": "R60",
        "source_concentration_warning": "All module drafts inherit the single-account limitation of the article corpus.",
        "modules": modules,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 公众号占星候选模块草案",
        "",
        "本文件是从 `exploration.json` 生成的边界草案，不是核心规则库。所有模块均为 candidate-only / C 级；来源集中于一个公众号账号，必须经过独立来源、反例和机器回归。",
        "",
    ]
    for module in result["modules"]:
        lines.extend([
            f"## {module['title']} (`{module['id']}`)",
            "",
            f"- 层级：`{module['layer']}`；卡片数：{module['card_count']}；状态：`{module['status']}`；证据上限：`{module['grade_cap']}`。",
            f"- 纳入边界：{module['include_boundary']}",
            f"- 排除边界：{module['exclude_boundary']}",
            f"- 下一测试：{module['next_test']}",
            "- 代表卡：" + "；".join(f"`{item['card_id']}` {item['title']}" for item in module["representative_cards"]),
            "",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--exploration", type=Path, default=DEFAULT_EXPLORATION)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    result = build(load_jsonl(args.cards), json.loads(args.exploration.read_text(encoding="utf-8")))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({"modules": len(result["modules"]), "cards": sum(module["card_count"] for module in result["modules"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
