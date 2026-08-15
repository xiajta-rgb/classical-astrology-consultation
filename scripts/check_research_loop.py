#!/usr/bin/env python3
"""Fail-closed QA for LOOP-1.0 astrology documents.

Usage:
    python -X utf8 scripts/check_research_loop.py draft.md
    python -X utf8 scripts/check_research_loop.py --self-test

This checker does not judge whether astrology is true. It checks whether a
draft is traceable, specific, bounded, evidence-layered and safe for sensitive
topics.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_SECTIONS = (
    "核心判断",
    "证据结构",
    "结构性矛盾",
    "风险边界",
    "不可判断项",
)

EVIDENCE_MARKERS = ("Evidence:", "证据", "宫位", "宫主", "相位")
RULE_MARKERS = ("Rule:", "规则", "机制")
INFERENCE_MARKERS = ("Inference:", "推断", "因此", "表现为")
COUNTER_MARKERS = ("Counter", "反证", "限制", "竞争假设")
SOURCE_MARKERS = (r"R\d+", r"QI-\d+", "Book", "Chapter", "DOI", "https://")
CERTAINTY_MARKERS = (
    "S级", "A级", "B级", "C级", "N/A", "明确表现为", "明显倾向于",
    "可能涉及", "本命盘无法确认",
)
DIRECTNESS_MARKERS = ("指向", "机制", "主要矛盾", "受限于", "不足以", "现实中")
DOMAIN_MARKERS = (
    ("自我/决策", "自我", "决策"),
    ("职业/公共角色", "职业", "公共角色"),
    ("金钱/共享资源", "金钱", "共享资源", "债务"),
    ("关系/家庭", "关系", "家庭"),
    ("创作/子女", "创作", "子女"),
    ("压力/风险", "压力", "风险"),
    ("时限边界", "时限", "不可判断项"),
)

GENERIC_PHRASES = (
    "不断成长", "找到平衡", "发挥优势", "提高认知", "保持稳定", "抓住机会",
    "适合长期主义", "不要过度焦虑", "人生会经历变化", "相信自己",
    "突破舒适区", "有潜力", "比较敏感", "能量很强", "关系复杂",
    "注意情绪", "有贵人", "某种程度", "一些方面",
)

SENSITIVE_TERMS = (
    "死亡", "寿命", "自杀", "疾病", "癌", "癌症", "精神病", "抑郁", "出轨", "通奸", "暴力", "犯罪",
    "被捕", "强奸", "乱伦", "性取向", "怀孕", "流产", "不孕", "诅咒", "附体",
    "奴役", "绑架", "成瘾",
)

BOUNDARY_MARKERS = (
    "无法确认", "不能确认", "不等于", "禁止", "仅可", "现实", "专业",
    "不能诊断", "不预测", "不能作为证据", "需核验",
)

DETERMINISTIC_SENSITIVE = re.compile(
    r"(?:一定会|必然|注定|肯定会|你会)(?:.{0,18})(?:死亡|自杀|犯罪|患病|癌|癌症|出轨|通奸|被捕|怀孕|流产|不孕|诅咒|附体)",
    re.IGNORECASE,
)


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(re.search(marker, text, re.IGNORECASE) for marker in markers)


def check_text(text: str, name: str = "draft") -> list[str]:
    findings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            findings.append(f"missing section: {section}")

    if not _has_any(text, EVIDENCE_MARKERS):
        findings.append("no chart-evidence marker")
    if not _has_any(text, RULE_MARKERS):
        findings.append("no rule/mechanism marker")
    if not _has_any(text, INFERENCE_MARKERS):
        findings.append("no inference/observable-translation marker")
    if not _has_any(text, COUNTER_MARKERS):
        findings.append("no counter-testimony marker")
    if not _has_any(text, SOURCE_MARKERS):
        findings.append("no source locator")
    if not _has_any(text, CERTAINTY_MARKERS):
        findings.append("no calibrated certainty marker")
    if not _has_any(text, DIRECTNESS_MARKERS):
        findings.append("no directness/mechanism marker")

    for phrase in GENERIC_PHRASES:
        if phrase in text:
            findings.append(f"generic/vague phrase: {phrase}")

    present_domains = 0
    for domain in DOMAIN_MARKERS:
        if any(term in text for term in domain):
            present_domains += 1
    if present_domains < 5:
        findings.append(f"full-picture coverage too narrow: {present_domains}/7 domains")

    if any(term in text for term in SENSITIVE_TERMS):
        if not any(marker in text for marker in BOUNDARY_MARKERS):
            findings.append("sensitive topic lacks explicit boundary or professional-reality marker")
        match = DETERMINISTIC_SENSITIVE.search(text)
        if match:
            context = text[max(0, match.start() - 18):match.end()]
            if not re.search(r"不能|无法|不预测|不等于|禁止", context):
                findings.append("deterministic sensitive-topic claim detected")

    # A line that hedges without naming a condition is usually non-actionable.
    for line_no, line in enumerate(text.splitlines(), start=1):
        if re.search(r"可能|也许|或许|比较", line) and not re.search(
            r"条件|如果|取决|因为|由于|具体|在.+时|受限|不足以|不能", line
        ):
            findings.append(f"unbounded hedge on line {line_no}")

    if name == "draft" and not text.strip():
        findings.append("empty draft")
    return findings


GOOD_FIXTURE = """
## 核心判断
这组结构首先指向共享资源与控制权绑定，机制是7/8宫主牵动2宫；现实中表现为分账、债务与退出条件反复拉扯（A级）。
## 证据结构
Evidence: R02 Book II，8宫主落2宫并与7宫主形成应用相位。
Rule: 7/8负责契约与共享资源，2宫负责个人资源。
Inference: 关系议题会通过资源分配而不是抽象情绪表现出来。
Counter: 2宫主尊贵且有吉星接纳，限制了“必然破财”的解释。
## 结构性优势
能把复杂资源拆成合同、权限和责任节点。
## 结构性矛盾
关系/家庭与金钱/共享资源之间存在授权冲突。
## 风险边界
职业/公共角色与压力/风险需补充时限；不能把本命结构当作事件日期。
## 不可判断项
自我/决策、创作/子女和时限边界：本命盘无法确认具体事件。
## 研究轮次
LOOP-20260814-03；来源 R01/R02；测试 T01-T07 通过。
"""

BAD_FIXTURE = """
## 核心判断
你很有潜力，也比较敏感，人生会经历变化。
## 证据结构
证据：某颗星很强。
## 结构性优势
发挥优势，找到平衡。
"""

SENSITIVE_BAD_FIXTURE = GOOD_FIXTURE.replace(
    "本命盘无法确认具体事件。", "你一定会死亡，而且会被诅咒。"
)
SENSITIVE_RELATION_MEDICAL_BAD_FIXTURE = GOOD_FIXTURE.replace(
    "本命盘无法确认具体事件。", "你一定会出轨，而且你一定会得癌症。"
)


def self_test() -> int:
    good = check_text(GOOD_FIXTURE, "good-fixture")
    bad = check_text(BAD_FIXTURE, "bad-fixture")
    sensitive_bad = check_text(SENSITIVE_BAD_FIXTURE, "sensitive-bad-fixture")
    sensitive_relation_medical_bad = check_text(SENSITIVE_RELATION_MEDICAL_BAD_FIXTURE, "sensitive-relation-medical-bad-fixture")
    if good:
        print("FAIL self-test good fixture:")
        print("\n".join(f"- {item}" for item in good))
        return 1
    if not bad:
        print("FAIL self-test bad fixture was accepted")
        return 1
    if not any("deterministic sensitive-topic" in item for item in sensitive_bad):
        print("FAIL self-test sensitive deterministic fixture was accepted")
        return 1
    if not any("deterministic sensitive-topic" in item for item in sensitive_relation_medical_bad):
        print("FAIL self-test relation/medical deterministic fixture was accepted")
        return 1
    print("PASS self-test: good fixture accepted; generic and sensitive bad fixtures rejected")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.draft is None:
        parser.error("provide draft path or --self-test")
    findings = check_text(args.draft.read_text(encoding="utf-8"))
    if findings:
        print("FAIL")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("PASS: LOOP-1.0 traceability, directness, coverage and safety gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
