#!/usr/bin/env python3
"""Build a curated core store from the two user-provided DOCX files.

Unlike the earlier exploratory extractor, this command intentionally does not
persist the full manual. It keeps only selected classical/natal method ranges,
the cleaned fly-star and house-pair core cards, and their provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from docx import Document

from build_knowledge_index import build as build_retrieval_index


MANUAL = Path(r"C:\Users\xiajt\Desktop\看盘手册(综合最终）.docx")
MATRIX = Path(r"C:\Users\xiajt\Desktop\1互容特征汇总表.docx")

# Ranges are selected for natal method, planetary state, aspects, flow,
# reception and topic frameworks. Generic sign/personality, medical, MBTI,
# outer-planet and case-heavy ranges are deliberately omitted.
CORE_RANGES = (
    (0, 57, "natal_framework"),
    (1847, 2052, "planetary_state_and_aspects"),
    (2761, 3215, "house_rulership_flow"),
    (3216, 3505, "natal_method_and_reception"),
    (3898, 3934, "supporting_techniques"),
    (5368, 5636, "wealth_and_career_topics"),
)

DROP_TERMS = (
    "癌", "疾病", "抑郁", "精神病", "自杀", "死亡", "寿命", "犯罪", "暴力", "强奸",
    "性取向", "怀孕", "流产", "不孕", "灵体", "附体", "牢狱", "出轨", "不伦",
    "MBTI", "天王星", "海王星", "冥王星", "凯龙", "小行星", "北交点", "南交点",
    "星盘举例", "案例", "这个盘", "图中", "例如",
)
REDACT_TERMS = (
    "疾病", "精神疾病", "犯罪", "灵体", "牢狱", "婚外", "不伦", "出轨", "暗病",
)
TIMING_TERMS = ("法达", "太阳弧", "次限", "三限", "太阳返照", "月返", "行运", "推运", "小限", "校时", "年限")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def core_text(text: str) -> str:
    value = clean(text)
    for term in REDACT_TERMS:
        value = value.replace(term, "敏感主题")
    return value


def range_module(index: int) -> str | None:
    for start, end, module in CORE_RANGES:
        if start <= index < end:
            return module
    return None


def parse_flow_cards(path: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- H(\d+)→H(\d+)：(.+)$", line.strip())
        if not match:
            continue
        a, b, text = int(match.group(1)), int(match.group(2)), core_text(match.group(3))
        cards.append({
            "id": f"FS-{a}-{b}",
            "source_ids": ["R38"],
            "source_locator": "R38 paragraphs 2761-3214 and 3346-3463",
            "module": "house_rulership_flow",
            "kind": "house_flow_hypothesis",
            "from_house": a,
            "to_house": b,
            "text": text,
            "conditions": ["validated Chart Facts rulership_fly_ins", "house system and cusp risk recorded"],
            "counter_test": "same ruler may carry multiple house responsibilities; do not double count",
            "grade_cap": "C",
            "status": "candidate",
            "safety_gate": "G0",
            "version": "CORE-DISTILL-2026-08-15-1",
        })
    return cards


def parse_matrix_cards(path: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\| (\d+)-(\d+) \| (.+?) \| (.+?) \|$", line.strip())
        if not match:
            continue
        a, b = int(match.group(1)), int(match.group(2))
        cards.append({
            "id": f"MR-{a}-{b}",
            "source_ids": ["R38", "R39"],
            "source_locator": "R38 mutual-reception sections; R39 tables 0-1",
            "module": "mutual_reception_matrix",
            "kind": "house_pair_hypothesis",
            "pair": [a, b],
            "source_summary": core_text(match.group(3)),
            "observable_translation": core_text(match.group(4)),
            "conditions": ["complete topic responsibility chain", "typed planetary reception remains separate"],
            "counter_test": "house-pair labels do not prove wealth, marriage, health or an event",
            "grade_cap": "C",
            "status": "candidate",
            "safety_gate": "G0",
            "version": "CORE-DISTILL-2026-08-15-1",
        })
    return cards


def extract_manual_core(path: Path) -> list[dict[str, Any]]:
    doc = Document(path)
    cards: list[dict[str, Any]] = []
    for index, paragraph in enumerate(doc.paragraphs):
        module = range_module(index)
        text = clean(paragraph.text)
        if not module or not text or any(term in text for term in DROP_TERMS) or any(term in text for term in TIMING_TERMS):
            continue
        status = "auxiliary"
        cards.append({
            "id": f"R38-P{index:04d}",
            "source_ids": ["R38"],
            "source_locator": {"paragraph_index": index, "style": paragraph.style.name},
            "module": module,
            "kind": "curated_source_extract",
            "text": text,
            "conditions": ["source is a user-provided secondary note", "do not treat as independent classical proof"],
            "counter_test": "must be reconciled with Chart Facts, independent testimony and the project evidence gate",
            "grade_cap": "C" if module in ("natal_method_and_reception", "house_rulership_flow", "supporting_techniques") else "N/A",
            "status": status,
            "safety_gate": "G0",
            "version": "CORE-DISTILL-2026-08-15-1",
        })
    return cards


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", type=Path, default=MANUAL)
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--output-dir", type=Path, default=Path("references/knowledge-modules/core"))
    parser.add_argument("--update-registry", action="store_true")
    args = parser.parse_args()
    if not args.manual.exists() or not args.matrix.exists():
        raise SystemExit("both source DOCX files must exist")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    flow = parse_flow_cards(Path("references/knowledge-modules/fly-star-corpus.md"))
    matrix = parse_matrix_cards(Path("references/knowledge-modules/mutual-reception-matrix.md"))
    manual_core = extract_manual_core(args.manual)
    records = flow + matrix + manual_core
    write_jsonl(args.output_dir / "cards.jsonl", records)
    retrieval_path = args.output_dir / "retrieval-index.json"
    build_retrieval_index(args.output_dir / "cards.jsonl", retrieval_path)
    manifest = {
        "schema_version": "CORE-KNOWLEDGE-0.1",
        "version": "CORE-DISTILL-2026-08-15-1",
        "canonical_store": "core/cards.jsonl",
        "index": "core/index.json",
        "retrieval_index": "core/retrieval-index.json",
        "readme": "core/README.md",
        "sources": {
            "R38": {"file_name": args.manual.name, "sha256": hashlib.sha256(args.manual.read_bytes()).hexdigest()},
            "R39": {"file_name": args.matrix.name, "sha256": hashlib.sha256(args.matrix.read_bytes()).hexdigest()},
        },
        "counts": {
            "total": len(records),
            "flow_cards": len(flow),
            "matrix_cards": len(matrix),
            "manual_core_extracts": len(manual_core),
            "by_module": dict(Counter(item["module"] for item in records)),
            "by_status": dict(Counter(item["status"] for item in records)),
        },
        "excluded": {
            "full_manual_extract": True,
            "reason": "user requested key core only; ambiguous, modern, medical, identity-label, case-heavy and timing-extension material is not retained",
            "drop_terms": list(DROP_TERMS),
        },
    }
    (args.output_dir / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "README.md").write_text(
        "# 核心知识库\n\n"
        "本目录只保留两份用户资料中筛选出的核心结构：144 条有向飞宫、78 条宫位对互容，以及经过敏感/现代/案例过滤的 R38 方法摘录。\n\n"
        "规范调用文件：`cards.jsonl`；统计和哈希：`index.json`。完整原手册抽取物不保留。\n",
        encoding="utf-8",
    )
    if args.update_registry:
        registry_path = Path("references/knowledge-modules/registry.json")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry.pop("distillation", None)
        registry["core_distillation"] = manifest
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
