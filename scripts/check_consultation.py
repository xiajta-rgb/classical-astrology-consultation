#!/usr/bin/env python3
"""Lightweight QA for a draft classical astrology consultation.

Usage: python check_consultation.py draft.md
Returns non-zero when generic-advice phrases are found or evidence markers are absent.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

BLOCKLIST = (
    "不断成长", "找到平衡", "发挥优势", "提高认知", "保持稳定", "抓住机会",
    "长期主义", "不要过度焦虑", "人生会经历变化", "相信自己", "突破舒适区",
    "你适合动态发展", "你要学会放下", "你需要更稳定", "你需要提升自己",
)
EVIDENCE_MARKERS = ("Evidence:", "证据", "宫主", "宫位", "相位")
CERTAINTY_MARKERS = ("S级", "A级", "B级", "C级", "N/A", "S-level", "A-level", "B-level", "C-level", "明确表现为", "本命盘无法确认")
LAYER_MARKERS = ("结构性", "结构含义", "咨询建议", "Astrology fact", "Structural meaning")
SECT_MARKERS = ("日夜盘", "昼夜盘", "sect", "日盘", "夜盘", "无法确认昼夜盘")
LAYERING_MARKERS = ("古典七曜", "现代辅助", "辅助征象", "现代外行星", "classical seven")
AI_TELL_PATTERNS = (
    ("em/en dash or double hyphen", re.compile(r"[—–]|(?<!\w)--(?!\w)")),
    (
        "collaboration or meta-introduction",
        re.compile(r"当然可以|希望(?:这|以上)能帮助|如果你愿意.{0,20}(我可以|可以继续)|下面将从几个方面"),
    ),
    ("formulaic contrast", re.compile(r"不是.{0,40}而是|不仅.{0,40}而且")),
    (
        "generic conclusion",
        re.compile(r"综上所述|总的来说|未来可期|开启(?:新的)?篇章|迈向更好的自己"),
    ),
    ("filler insight marker", re.compile(r"值得注意的是|更重要的是|从某种意义上说")),
)


CONDITIONAL_FILLER = ("并非没有", "有机会", "可以考虑", "需要注意", "取决于")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    text = args.draft.read_text(encoding="utf-8")
    findings = []
    for phrase in CONDITIONAL_FILLER:
        if phrase in text:
            findings.append(f"conditional filler: {phrase}")
    if re.search(r"只要.{0,80}就", text):
        findings.append("conditional filler: 只要……就……")
    for phrase in BLOCKLIST:
        if phrase in text:
            findings.append(f"generic phrase: {phrase}")
    for label, pattern in AI_TELL_PATTERNS:
        if pattern.search(text):
            findings.append(f"AI-style tell: {label}")
    if not any(marker in text for marker in EVIDENCE_MARKERS):
        findings.append("no chart-evidence marker found")
    if not any(marker in text for marker in CERTAINTY_MARKERS):
        findings.append("no certainty/boundary marker found")
    if not any(marker in text for marker in LAYER_MARKERS):
        findings.append("no astrology-to-structure-to-advice layer marker found")
    if not any(marker in text for marker in SECT_MARKERS):
        findings.append("no sect/day-night marker found")
    if not any(marker in text for marker in LAYERING_MARKERS):
        findings.append("no classical-versus-modern evidence-layer marker found")
    if findings:
        print("FAIL")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("PASS: evidence and certainty markers found; no blocklisted generic phrase detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
