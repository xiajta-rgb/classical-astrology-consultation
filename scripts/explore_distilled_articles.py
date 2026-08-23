#!/usr/bin/env python3
"""Build a second-pass, non-promoting exploration map for article cards."""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "references/knowledge-modules/distilled/cards.jsonl"
DEFAULT_OUTPUT = ROOT / "references/knowledge-modules/distilled/exploration.json"
DEFAULT_QUEUE_OUTPUT = ROOT / "references/knowledge-modules/distilled/review-queue.jsonl"

MARKETING_RESIDUE = re.compile(r"PS\.|推荐阅读|往期|For more|留言若|加微信|课程|本周付费|专属通道", re.I)
SENSATIONAL_TITLE = re.compile(r"最|第一|硬核|极限|撕裂|暴富|王炸|天选|爆发|必然|注定")

CLUSTERS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("timing_deferred", "时限与激活边界（延后）", re.compile(r"行运|水逆|流年|推运|法达|太阳弧|次限|三限|返照|年限|小限|择时|校时")),
    ("modern_extension", "现代外行星与小行星扩展", re.compile(r"天王星|海王星|冥王星|凯龙|莉莉丝|小行星|婚神星|北交点|南交点")),
    ("house_rulership", "宫位、轴点与宫主责任链", re.compile(r"宫主|飞宫|宫位|落宫|一宫|二宫|三宫|四宫|五宫|六宫|七宫|八宫|九宫|十宫|十一宫|十二宫|上升|下降|中天|天底|福点")),
    ("aspect_synthesis", "相位、接纳与组合机制", re.compile(r"相位|合相|六合|刑|拱|冲|对冲|互容|接纳|尊贵|空相|格局")),
    ("planet_sign_translation", "行星—星座符号翻译", re.compile(r"太阳|月亮|水星|金星|火星|木星|土星|白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼|星座")),
    ("relationship_adapter", "关系、家庭与合盘适配", re.compile(r"爱情|恋爱|婚姻|伴侣|关系|合盘|家庭|父母|母亲|孩子|子女")),
    ("career_money_adapter", "事业、工作与资源适配", re.compile(r"事业|职业|工作|领导|晋升|成名|创业|财富|金钱|赚钱|生财|收入|财务|房产|资产")),
)


def load_cards(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def haystack(card: dict[str, Any]) -> str:
    return " ".join([str(card.get("title", "")), str(card.get("text", "")), " ".join(str(t) for t in card.get("topics", []))])


def canonical_cluster(card: dict[str, Any]) -> tuple[str, str]:
    text = haystack(card)
    topic_set = set(str(topic) for topic in card.get("topics", []))
    if card.get("timing_extension") or "timing" in topic_set or re.search(r"行运|水逆|流年|推运|法达|返照|次限|三限|年限|小限|择时|校时", text):
        return "timing_deferred", "时限与激活边界（延后）"
    if card.get("modern_extension") or "modern_extension" in topic_set:
        return "modern_extension", "现代外行星与小行星扩展"
    if "relationship" in topic_set and re.search(r"爱情|恋爱|婚姻|伴侣|关系|合盘|家庭|父母|母亲|孩子|子女", text):
        return "relationship_adapter", "关系、家庭与合盘适配"
    if ("career_work" in topic_set or "money_property" in topic_set) and re.search(r"事业|职业|工作|领导|晋升|成名|创业|财富|金钱|赚钱|生财|收入|财务|房产|资产", text):
        return "career_money_adapter", "事业、工作与资源适配"
    if "houses" in topic_set and re.search(r"宫主|飞宫|落宫|宫位|上升|下降|中天|天底|福点", text):
        return "house_rulership", "宫位、轴点与宫主责任链"
    if "aspects" in topic_set and re.search(r"相位|合相|六合|刑|拱|冲|对冲|互容|接纳|尊贵|空相|格局", text):
        return "aspect_synthesis", "相位、接纳与组合机制"
    if "houses" in topic_set:
        return "house_rulership", "宫位、轴点与宫主责任链"
    if "aspects" in topic_set:
        return "aspect_synthesis", "相位、接纳与组合机制"
    if "signs" in topic_set or "planetary_signification" in topic_set:
        return "planet_sign_translation", "行星—星座符号翻译"
    return "general_candidate", "一般占星候选"


def normalized(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()


def exact_duplicate_spans(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for card in cards:
        for claim in card.get("claims", []):
            key = normalized(str(claim.get("source_span", "")))
            if key:
                groups[key].append(str(card.get("id")))
    return [
        {"normalized_span": key, "card_ids": sorted(set(ids))}
        for key, ids in groups.items()
        if len(set(ids)) > 1
    ]


def near_duplicate_titles(cards: list[dict[str, Any]], threshold: float = 0.86) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for i, left in enumerate(cards):
        a = normalized(str(left.get("title", "")))
        if len(a) < 6:
            continue
        for right in cards[i + 1 :]:
            b = normalized(str(right.get("title", "")))
            if len(b) < 6:
                continue
            score = difflib.SequenceMatcher(None, a, b).ratio()
            if score >= threshold:
                pairs.append({"score": round(score, 3), "card_ids": [left.get("id"), right.get("id")], "titles": [left.get("title"), right.get("title")]})
    return sorted(pairs, key=lambda row: -row["score"])


def review_score(card: dict[str, Any], cluster_id: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    claim_count = len(card.get("claims", []))
    if cluster_id in {"house_rulership", "aspect_synthesis"}:
        score += 4
        reasons.append("可连接责任链/相位机制")
    if claim_count >= 5:
        score += 2
        reasons.append(f"含{claim_count}条可复核片段")
    elif claim_count >= 3:
        score += 1
        reasons.append(f"含{claim_count}条可复核片段")
    if re.search(r"宫主|飞宫|福点|接纳|尊贵|互容", haystack(card)):
        score += 2
        reasons.append("出现责任链或状态审计词")
    if card.get("modern_extension"):
        score -= 3
        reasons.append("现代扩展证据上限")
    if card.get("timing_extension"):
        score -= 5
        reasons.append("时限资料需显式激活")
    if cluster_id == "planet_sign_translation" and claim_count <= 2:
        score -= 1
        reasons.append("较接近单一符号标签")
    return score, reasons


def quality_flags(card: dict[str, Any]) -> list[str]:
    """Flag review friction without rewriting source-bound card text."""
    spans = [str(claim.get("source_span", "")) for claim in card.get("claims", [])]
    flags: list[str] = []
    if any(MARKETING_RESIDUE.search(span) for span in spans):
        flags.append("marketing_residue")
    if len(spans) <= 1:
        flags.append("single_claim")
    if sum(len(span) for span in spans) < 55:
        flags.append("low_information")
    if SENSATIONAL_TITLE.search(str(card.get("title", ""))):
        flags.append("sensational_title")
    if card.get("modern_extension"):
        flags.append("modern_extension")
    if card.get("timing_extension"):
        flags.append("timing_deferred")
    return flags


def review_status(card: dict[str, Any], flags: list[str]) -> tuple[str, str]:
    if "marketing_residue" in flags:
        return "hold_marketing_residue", "清理或人工确认残余营销文本后再复核"
    if "timing_deferred" in flags:
        return "deferred_timing", "仅登记方法与所需数据；用户明确时间问题后再激活"
    if "modern_extension" in flags:
        return "candidate_modern_review", "补充古典体系边界与独立来源，不能并入古典核心"
    return "pending_manual_review", "锁定 Chart Facts 后做独立来源、反例和可观察事件复核"


def build(cards: list[dict[str, Any]]) -> dict[str, Any]:
    cluster_cards: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    assignments: list[dict[str, Any]] = []
    for card in cards:
        cluster_id, title = canonical_cluster(card)
        score, reasons = review_score(card, cluster_id)
        flags = quality_flags(card)
        status, next_action = review_status(card, flags)
        if "marketing_residue" in flags:
            score -= 4
            reasons.append("原文含营销残片，先清理/人工确认")
        cluster_cards[cluster_id].append(card)
        assignments.append({"card_id": card.get("id"), "title": card.get("title"), "canonical_cluster": cluster_id, "cluster_title": title, "review_score": score, "review_reasons": reasons, "quality_flags": flags, "review_status": status, "next_action": next_action, "secondary_topics": card.get("topics", [])})

    clusters: dict[str, Any] = {}
    for cluster_id, title, _ in CLUSTERS:
        items = cluster_cards.get(cluster_id, [])
        if not items:
            continue
        clusters[cluster_id] = {
            "title": title,
            "card_count": len(items),
            "card_ids": [card.get("id") for card in items],
            "sample_titles": [card.get("title") for card in items[:8]],
            "routing_policy": "one canonical cluster per card; secondary topics are retrieval hints only",
        }
    if cluster_cards.get("general_candidate"):
        items = cluster_cards["general_candidate"]
        clusters["general_candidate"] = {"title": "一般占星候选", "card_count": len(items), "card_ids": [card.get("id") for card in items], "sample_titles": [card.get("title") for card in items[:8]], "routing_policy": "manual review before module assignment"}

    account_counts = collections.Counter(str(card.get("source_metadata", {}).get("account", "")) for card in cards)
    topics = collections.Counter(str(topic) for card in cards for topic in card.get("topics", []))
    ranked = sorted(assignments, key=lambda row: (-row["review_score"], row["card_id"]))
    queue_rows: list[dict[str, Any]] = []
    cards_by_id = {str(card.get("id")): card for card in cards}
    for assignment in ranked[:40]:
        card = cards_by_id[str(assignment["card_id"])]
        queue_rows.append({
            "card_id": assignment["card_id"],
            "title": assignment["title"],
            "canonical_cluster": assignment["canonical_cluster"],
            "review_score": assignment["review_score"],
            "review_status": assignment["review_status"],
            "quality_flags": assignment["quality_flags"],
            "claims": [claim.get("source_span") for claim in card.get("claims", [])],
            "conditions": card.get("conditions", []),
            "counter_test": card.get("counter_test"),
            "next_action": assignment["next_action"],
            "independent_source_required": True,
        })
    return {
        "schema_version": "ARTICLE-DISTILLATION-EXPLORATION-0.1",
        "method": "single_canonical_cluster_plus_secondary_retrieval_topics",
        "promotion_policy": "exploration map only; no card promotion or runtime activation",
        "source_concentration": {
            "accounts": dict(account_counts),
            "unique_accounts": len(account_counts),
            "warning": "all retained cards currently come from one公众号 account; independent-source support is absent",
        },
        "counts": {
            "cards": len(cards),
            "clusters": len(clusters),
            "exact_duplicate_span_groups": len(exact_duplicate_spans(cards)),
            "near_duplicate_title_pairs": len(near_duplicate_titles(cards)),
        },
        "topic_counts": dict(topics),
        "clusters": clusters,
        "assignments": assignments,
        "review_queue": queue_rows,
        "duplicate_audit": {
            "exact_span_groups": exact_duplicate_spans(cards),
            "near_duplicate_title_pairs": near_duplicate_titles(cards)[:100],
        },
        "next_tests": [
            "为 house_rulership 和 aspect_synthesis 各抽取至少两条独立来源进行交叉核验",
            "对 review_queue 前 20 张卡补 Chart Facts 责任链、反证和可观察事件翻译",
            "把 modern_extension 与 timing_deferred 保持为独立候选层，不并入古典核心",
            "对近重复标题和重复原文先合并检索入口，不重复计算证据",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--queue-output", type=Path, default=DEFAULT_QUEUE_OUTPUT)
    args = parser.parse_args()
    result = build(load_cards(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    queue_lines = [json.dumps(row, ensure_ascii=False) for row in result["review_queue"]]
    args.queue_output.write_text("\n".join(queue_lines) + ("\n" if queue_lines else ""), encoding="utf-8")
    print(json.dumps({"cards": result["counts"]["cards"], "clusters": result["counts"]["clusters"], "top_review_ids": [row["card_id"] for row in result["review_queue"][:10]], "exact_duplicate_span_groups": result["counts"]["exact_duplicate_span_groups"], "near_duplicate_title_pairs": result["counts"]["near_duplicate_title_pairs"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
