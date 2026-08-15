#!/usr/bin/env python3
"""QA for the NATAL-1.0 layer.

The checker prevents a natal-only document from silently turning into a timing
prediction. Timing language is allowed only when the draft explicitly marks a
timing extension as enabled.
"""
from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED = ("Chart Facts", "宫位责任", "行星状态", "结构性矛盾", "不可判断项")
TIMING_TERMS = (
    "推运", "行运", "主限", "profection", "transit", "secondary progression",
    "zodiacal releasing", "太阳回归", "今年", "明年", "本年度", "具体日期",
)
ENABLE_MARKERS = ("timing_extension: enabled", "激活时限插件", "用户明确要求未来")
LIMIT_MARKERS = ("本命盘无法确认", "需要时限", "不能给出日期", "N/A")


def check_text(text: str) -> list[str]:
    findings: list[str] = []
    for marker in REQUIRED:
        if marker not in text:
            findings.append(f"missing natal marker: {marker}")

    timing_present = any(term.lower() in text.lower() for term in TIMING_TERMS)
    timing_enabled = any(marker.lower() in text.lower() for marker in ENABLE_MARKERS)
    if timing_present and not timing_enabled:
        findings.append("timing extension appears in natal-only draft without explicit activation")
    if timing_present and not any(marker in text for marker in LIMIT_MARKERS):
        findings.append("timing language lacks natal limitation or N/A boundary")
    return findings


GOOD_NATAL = """
## Chart Facts
## 宫位责任
## 行星状态
## 结构性矛盾
## 不可判断项
本命盘无法确认事件时间。
"""

BAD_TIMING = GOOD_NATAL + "今年会发生推运事件。"

ENABLED_TIMING = GOOD_NATAL + "timing_extension: enabled；用户明确要求未来；需要时限。"


def self_test() -> int:
    if check_text(GOOD_NATAL):
        print("FAIL natal fixture rejected")
        return 1
    if not check_text(BAD_TIMING):
        print("FAIL timing leakage accepted")
        return 1
    if check_text(ENABLED_TIMING):
        print("FAIL explicitly enabled timing fixture rejected")
        return 1
    print("PASS natal-first self-test")
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
    print("PASS: NATAL-1.0 layer is clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
