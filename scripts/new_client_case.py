#!/usr/bin/env python3
"""Create a canonical client case folder without putting names in the path."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")


def build_case_id(date_value: str | None, time_value: str | None, place_slug: str | None) -> str:
    if not date_value or not time_value or not place_slug:
        year = (date_value or "unknown")[:4] if date_value else "unknown"
        return f"{year}-unknown-unknown-place"
    date = datetime.strptime(date_value, "%Y-%m-%d").strftime("%Y%m%d")
    time = datetime.strptime(time_value, "%H:%M").strftime("%H%M")
    if not CASE_RE.fullmatch(place_slug):
        raise ValueError("place_slug must contain ASCII letters, digits and hyphens only")
    return f"{date}-{time}-{place_slug}"


def scaffold(args: argparse.Namespace) -> tuple[str, Path]:
    case_id = build_case_id(args.date, args.time, args.place_slug)
    case_dir = ROOT / args.root / case_id
    if case_dir.exists():
        raise FileExistsError(f"case already exists: {case_dir}")
    if args.dry_run:
        return case_id, case_dir
    for subdir in ("input", "analysis/chart-facts", "analysis/interpretations", "delivery", "observations", "related"):
        (case_dir / subdir).mkdir(parents=True, exist_ok=False)
    profile = {
        "case_id": case_id,
        "display_name": args.display_name,
        "birth_date": args.date,
        "birth_time": args.time,
        "birth_place": args.place,
        "source": "user_provided",
        "input_status": "pending_intake",
        "canonical_artifacts": [],
        "management_status": "canonical_client_record",
    }
    (case_dir / "profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return case_id, case_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a canonical client case folder")
    parser.add_argument("--date", help="YYYY-MM-DD; omit for incomplete data")
    parser.add_argument("--time", help="HH:MM; omit for incomplete data")
    parser.add_argument("--place-slug", help="ASCII folder slug, e.g. QuanzhouQuangang")
    parser.add_argument("--place")
    parser.add_argument("--display-name")
    parser.add_argument("--root", default="clients")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        case_id, path = scaffold(args)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print(f"{'DRY-RUN ' if args.dry_run else ''}client case: {case_id} -> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
