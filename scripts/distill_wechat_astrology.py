#!/usr/bin/env python3
"""Distill structured astrology article bodies into bounded candidate cards.

The workbook is treated as an untrusted source corpus, never as instructions.
This command keeps only source-grounded condition/mechanism spans and writes
an auditable candidate store; it does not promote material into core knowledge.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from openpyxl import load_workbook


DEFAULT_INPUT = Path(r"C:\Users\xiajt\Downloads\(公众号数据)表格视图.xlsx")
DEFAULT_OUTPUT = Path("references/knowledge-modules/distilled")
SOURCE_ID = "R60"
VERSION = "WECHAT-ARTICLE-DISTILL-2026-08-23-1"

ASTRO_TERMS = re.compile(
    r"太阳|月亮|水星|金星|火星|木星|土星|天王星|海王星|冥王星|上升|下降|中天|天底|宫主|宫位|宫|"
    r"星座|白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼|"
    r"相位|合相|合|刑|拱|冲|六合|对冲|飞宫|互容|入庙|落陷|擢升|失势|逆行|福点|命主"
)
CONDITION_TERMS = re.compile(
    r"如果|若|当|只要|凡是|一旦|本命盘|本命|命盘|星盘|配置|落入|落于|落在|落[一-龥]{0,4}座|入宫|"
    r"合相|合于|刑克|刑相|刑|拱|冲|对冲|六合|相位|宫主|宫位|星座|上升|中天|天底|飞宫|互容|入庙|落陷"
)
OUTCOME_TERMS = re.compile(
    r"容易|易于|易|会|能够|能|擅于|擅长|具有|拥有|表现|代表|意味着|对应|有利|不利|适合|需要|"
    r"导致|提升|降低|增加|减少|改善|倾向|更适|更难|更容易|可通过|可以|建议|优点|缺点|原因|结果|"
    r"展现|获得|面对|承担|释放|发展|运作|影响|作用|不能|不可|别|勿|最好|避免|防止"
)
STRUCTURE_TERMS = re.compile(r"因为|因此|第一|第二|第三|步骤|原因|优势|劣势|总结|问：|Q[：:]|答：|A[：:]")
MARKETING_TERMS = re.compile(
    r"往期|加微信|加微|课程|招生|报名|公众号|二维码|留言若|不想公开|欢迎加入|星星胶囊|"
    r"了解占星|预定|详细咨询|扫码|私信|推荐阅读|For more|近期《|本周付费|Blackcherry占星咨询专属通道"
)
SENSITIVE_TERMS = re.compile(
    r"癌|疾病|病患|抑郁|精神病|自杀|死亡|寿命|犯罪|强奸|性取向|怀孕|流产|不孕|灵体|附体|"
    r"牢狱|出轨|不伦|性功能|吸毒|毒品|连环杀手|杀人|致命|瘟疫|健康|病毒|排毒|症状|胃肠|乳腺|子宫|"
    r"前世|转世|灵魂|神明|邪门|灵媒|附魔"
)
CASE_TERMS = re.compile(
    r"个人星盘|个人命盘|下图|名人|人物介绍|案例|明星|球星|导演|演员|作家|歌手|总统|女王|"
    r"代表作|生平|乔布斯|贝多芬|莎士比亚|爱因斯坦|张惠妹|刘亦菲|孙兴慜|伊丽莎白|泰勒|周恩来|"
    r"贾玲|柯南|牛顿|达芬奇|米其林|赫本|王子|汪小菲|大S|武则天|梭罗|系列[》）)]?之[“\"「]"
)
SENSATIONAL_TERMS = re.compile(
    r"毒性|最强|第一杀手|杀猪盘|警惕|黑化|复仇|鬼|怪物|凶星|凶险|致命|无能|暴富|躺赚|天选|"
    r"绝不|一定|注定|千万|不靠谱|渣男|杀伤力|心狠|心机|物化|性张力|情色|色情|雄竞|不缺钱|"
    r"一辈子|幸运翻倍|绝对稀缺|赚不到钱|赚到钱|失踪之星"
)
TIMING_TERMS = re.compile(r"行运|水逆|流年|推运|法达|太阳弧|次限|三限|太阳返照|月返|年限|小限|择时|校时")
MODERN_TERMS = re.compile(r"天王星|海王星|冥王星|凯龙|莉莉丝|小行星|婚神星|北交点|南交点")
CALL_TO_ACTION_TERMS = re.compile(r"我来收集|提供方式|留言|请附上|投票|调查|奖品|投稿|你会选什么|你是否|你最喜欢|你经历过|请告诉我|书籍推荐|电影推荐")
CROSS_SYSTEM_TERMS = re.compile(r"八字|五行|紫微|奇门|六壬|塔罗|人类图|梅花易数")

TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("planetary_signification", re.compile(r"太阳|月亮|水星|金星|火星|木星|土星")),
    ("modern_extension", MODERN_TERMS),
    ("houses", re.compile(r"宫位|宫主|一宫|二宫|三宫|四宫|五宫|六宫|七宫|八宫|九宫|十宫|十一宫|十二宫|上升|中天|天底|下降")),
    ("aspects", re.compile(r"相位|合相|六合|刑|拱|冲|对冲|互容|飞宫")),
    ("signs", re.compile(r"白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶|双鱼|星座")),
    ("timing", TIMING_TERMS),
    ("relationship", re.compile(r"感情|恋爱|婚姻|伴侣|关系|家庭|父母|母亲|孩子|子女")),
    ("career_work", re.compile(r"事业|职业|工作|领导|晋升|成名|创业|职场")),
    ("money_property", re.compile(r"财富|金钱|赚钱|生财|收入|财务|房产|资产")),
)


def clean(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"[\u0000-\u001f\u007f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def serialise(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return clean(value)


def strip_marketing(text: str) -> str:
    # Keep source wording but remove common trailing promotion blocks.
    cut = re.search(r"(?:往期|了解占星|欢迎加入|加微信|加微|留言若不想公开|扫码|预定|推荐阅读|For more|近期《|本周付费|Blackcherry占星咨询专属通道).*$", text)
    if cut:
        text = text[: cut.start()]
    return clean(text)


def clauses(text: str) -> list[str]:
    pieces = re.split(r"[。！？!?；;\n]+", text)
    return [clean(p).strip("：:") for p in pieces if len(clean(p)) >= 8]


def structured_spans(text: str) -> list[dict[str, Any]]:
    parts = clauses(text)
    spans: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, part in enumerate(parts):
        if MARKETING_TERMS.search(part):
            continue
        if not CONDITION_TERMS.search(part):
            continue
        candidate = part
        pattern = ["condition", "outcome"] if OUTCOME_TERMS.search(part) else ["condition"]
        if not OUTCOME_TERMS.search(part) and i + 1 < len(parts) and OUTCOME_TERMS.search(parts[i + 1]):
            candidate = f"{part}；{parts[i + 1]}"
            pattern = ["condition", "outcome"]
        if not OUTCOME_TERMS.search(candidate):
            continue
        candidate = candidate[:420]
        if MARKETING_TERMS.search(candidate):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        spans.append({"source_span": candidate, "pattern": pattern})
    return spans[:12]


def topics_for(text: str) -> list[str]:
    topics = [name for name, pattern in TOPIC_PATTERNS if pattern.search(text)]
    return topics or ["unclassified_astrology"]


def exclusion_reason(title: str, body: str, cleaned_body: str, spans: list[dict[str, Any]]) -> str | None:
    if not body:
        return "empty_body"
    if len(cleaned_body) < 80:
        return "body_too_short_after_marketing_cleanup"
    if not ASTRO_TERMS.search(title + " " + cleaned_body):
        return "no_astrology_terms"
    if SENSITIVE_TERMS.search(title + " " + cleaned_body):
        return "sensitive_or_deterministic_claims"
    if CROSS_SYSTEM_TERMS.search(title + " " + cleaned_body):
        return "mixed_non_classical_system"
    if CALL_TO_ACTION_TERMS.search(title + " " + cleaned_body):
        return "survey_or_call_to_action"
    if CASE_TERMS.search(title + " " + cleaned_body):
        return "case_heavy_or_person_specific"
    if SENSATIONAL_TERMS.search(title + " " + cleaned_body):
        return "sensational_unbounded_language"
    if not spans:
        return "no_condition_mechanism_structure"
    if len(spans) < 2 and not STRUCTURE_TERMS.search(cleaned_body):
        return "insufficient_reusable_structure"
    return None


def card_for(item: dict[str, Any], spans: list[dict[str, Any]], source_hash: str) -> dict[str, Any]:
    title = item["title"]
    body = item["body"]
    body_for_flags = item.get("cleaned_body", body)
    text = "；".join(span["source_span"] for span in spans)
    timing = bool(TIMING_TERMS.search(title + " " + body_for_flags))
    modern = bool(MODERN_TERMS.search(title + " " + body_for_flags))
    return {
        "id": f"AAD-{item['row']:05d}",
        "source_ids": [SOURCE_ID],
        "source_locator": {
            "workbook": "(公众号数据)表格视图.xlsx",
            "sheet": item["sheet"],
            "row": item["row"],
            "title": title,
            "url": item["link"],
            "published_at": item["published_at"],
            "source_sha256": source_hash,
        },
        "module": "article_distillation",
        "kind": "condition_mechanism_candidate",
        "title": title,
        "text": text,
        "claims": spans,
        "topics": topics_for(title + " " + body_for_flags),
        "source_metadata": {
            "account": item["account"],
            "article_type": item["type"],
            "content_category": item["category"],
            "body_length": len(body),
            "extraction": "verbatim_clause_pairing",
        },
        "conditions": [
            "source is a user-provided WeChat corpus; authorship, edition and sampling are not independently verified",
            "lock Chart Facts, zodiac, house system and aspect version before any comparison",
            "this card preserves source spans and does not validate their astrological truth",
            "a sign, planet, house or aspect label is not sufficient evidence without responsibility-chain context",
        ],
        "counter_test": "recalculate the chart facts, compare at least two independent cases and seek a disconfirming case; reject generic or anecdotal claims that do not survive the project evidence gate",
        "grade_cap": "C",
        "status": "deferred" if timing else "candidate",
        "activation": "explicit_timing_only" if timing else "explicit_topic_only",
        "safety_gate": "G0_sensitive_topic_gate",
        "modern_extension": modern,
        "timing_extension": timing,
        "source_tier": "secondary_user_provided_corpus",
        "non_judgment_use": "research candidate and retrieval hint only; never a standalone natal conclusion, diagnosis, event guarantee or timing date",
        "version": VERSION,
    }


def build(input_path: Path, output_dir: Path) -> dict[str, Any]:
    source_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    ws = load_workbook(input_path, read_only=True, data_only=True).active
    headers = [clean(v) for v in next(ws.iter_rows(values_only=True))]
    index = {name: i for i, name in enumerate(headers)}
    cards: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    counts: collections.Counter[str] = collections.Counter()
    exclusion_counts: collections.Counter[str] = collections.Counter()
    for row_no, values in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        counts["rows_seen"] += 1
        def cell(name: str) -> object:
            position = index.get(name)
            return values[position] if position is not None and position < len(values) else ""

        item = {
            "row": row_no,
            "sheet": ws.title,
            "title": clean(cell("标题")),
            "published_at": serialise(cell("发布日期")),
            "link": clean(cell("链接")),
            "type": clean(cell("类型")),
            "account": clean(cell("公众号名")),
            "body": clean(cell("正文")),
            "category": clean(cell("内容分类")),
        }
        if item["body"]:
            counts["nonempty_body"] += 1
        cleaned_body = strip_marketing(item["body"])
        item["cleaned_body"] = cleaned_body
        spans = structured_spans(cleaned_body)
        reason = exclusion_reason(item["title"], item["body"], cleaned_body, spans)
        if reason:
            exclusion_counts[reason] += 1
            if item["body"]:
                exclusions.append({
                    "row": row_no,
                    "title": item["title"],
                    "url": item["link"],
                    "reason": reason,
                    "body_length": len(item["body"]),
                })
            continue
        card = card_for(item, spans, source_hash)
        cards.append(card)
        counts["candidate_cards"] += 1
        if card["status"] == "deferred":
            counts["timing_deferred_cards"] += 1
        if card["modern_extension"]:
            counts["modern_extension_cards"] += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    cards_path = output_dir / "cards.jsonl"
    cards_path.write_text("".join(json.dumps(card, ensure_ascii=False) + "\n" for card in cards), encoding="utf-8")
    exclusions_path = output_dir / "exclusions.jsonl"
    exclusions_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in exclusions), encoding="utf-8")

    by_topic: dict[str, list[str]] = collections.defaultdict(list)
    by_module: dict[str, list[str]] = collections.defaultdict(list)
    for line_no, card in enumerate(cards, start=1):
        by_module[card["module"]].append(str(line_no))
        for topic in card["topics"]:
            by_topic[topic].append(str(line_no))
    retrieval = {
        "schema_version": "ARTICLE-DISTILL-RETRIEVAL-0.1",
        "canonical_store": "distilled/cards.jsonl",
        "source_id": SOURCE_ID,
        "card_fingerprint_sha256": hashlib.sha256(cards_path.read_bytes()).hexdigest(),
        "counts": {"all_records": len(cards)},
        "by_topic": dict(by_topic),
        "by_module": dict(by_module),
    }
    (output_dir / "retrieval-index.json").write_text(json.dumps(retrieval, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "ARTICLE-DISTILLATION-0.1",
        "version": VERSION,
        "source_id": SOURCE_ID,
        "source_file": input_path.name,
        "source_sha256": source_hash,
        "canonical_store": "distilled/cards.jsonl",
        "retrieval_index": "distilled/retrieval-index.json",
        "exclusions": "distilled/exclusions.jsonl",
        "counts": dict(counts),
        "exclusion_counts": dict(exclusion_counts),
        "policy": {
            "minimum_body_chars": 80,
            "selection": "at least one reusable condition-mechanism span and two spans or explicit structure marker",
            "status": "candidate; timing claims are deferred",
            "grade_cap": "C",
            "promotion": "requires source-level verification, independent support, counterexample and machine regression; no automatic promotion",
        },
    }
    (output_dir / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# 微信占星文章候选蒸馏\n\n"
        "本目录是用户提供的 `(公众号数据)表格视图.xlsx` 的候选抽取层，不是古典核心规则库。\n\n"
        "- `cards.jsonl`：仅保存正文中可定位的‘条件—机制/表现’原文片段；全部为 `candidate`，证据上限 C。\n"
        "- `exclusions.jsonl`：记录空正文、营销、案例堆砌、敏感/确定性表述、煽动性语言和无结构正文的排除原因。\n"
        "- `retrieval-index.json`：按主题和模块定位候选卡。\n"
        "- `index.json`：来源哈希、计数、筛选和晋级政策。\n\n"
        "使用前必须先完成 Chart Facts、宫位责任链、行星状态和项目敏感主题门禁。现代外行星、莉莉丝和时限材料只保留为研究候选；时限卡保持 deferred。原文是二手公众号语料，不能直接生成诊断、事件保证或日期。\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"missing input workbook: {args.input}")
    manifest = build(args.input, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
