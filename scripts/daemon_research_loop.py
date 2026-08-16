#!/usr/bin/env python3
"""Persistent research-loop supervisor.

Runs the bounded continuous loop repeatedly in a separate process. Every cycle
reuses the query cursor and source queue managed by continuous_research_loop,
so a restart is resumable and never promotes external material automatically.
Create the configured stop file to end the loop cleanly.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from continuous_research_loop import run as run_cycle


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "references/research-loop"
DEFAULT_STOP = LOOP / "STOP-DAEMON"
DEFAULT_LOG = LOOP / "daemon-loop.log.jsonl"
DEFAULT_STATE = LOOP / "daemon-loop-state.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the resumable research loop continuously.")
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--rounds-per-cycle", type=int, default=2)
    parser.add_argument("--pages-per-round", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--max-cycles", type=int, default=0, help="0 means run until the stop file appears")
    parser.add_argument("--stop-file", type=Path, default=DEFAULT_STOP)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    if args.interval_seconds < 10:
        parser.error("--interval-seconds must be at least 10")
    if not 1 <= args.rounds_per_cycle <= 6:
        parser.error("--rounds-per-cycle must be between 1 and 6")
    if args.max_cycles < 0:
        parser.error("--max-cycles cannot be negative")

    args.stop_file.parent.mkdir(parents=True, exist_ok=True)
    cycles = 0
    write_state(args.state_file, {
        "schema_version": "DAEMON-RESEARCH-LOOP-0.1",
        "status": "running",
        "started_at": now(),
        "pid": __import__("os").getpid(),
        "stop_file": str(args.stop_file),
        "interval_seconds": args.interval_seconds,
    })
    try:
        while not args.stop_file.exists() and (args.max_cycles == 0 or cycles < args.max_cycles):
            cycles += 1
            run_id = f"DAEMON-{datetime.now().strftime('%Y%m%d-%H%M%S')}-C{cycles:04d}"
            started = now()
            try:
                result = run_cycle(args.rounds_per_cycle, args.pages_per_round, args.timeout, run_id)
                record = {
                    "run_id": run_id,
                    "cycle": cycles,
                    "started_at": started,
                    "completed_at": now(),
                    "status": "completed",
                    "result": result,
                }
                write_state(args.state_file, {
                    "schema_version": "DAEMON-RESEARCH-LOOP-0.1",
                    "status": "running",
                    "last_cycle": cycles,
                    "last_run_id": run_id,
                    "last_completed_at": record["completed_at"],
                    "stop_file": str(args.stop_file),
                })
            except Exception as exc:  # keep the supervisor alive across transient network failures
                record = {
                    "run_id": run_id,
                    "cycle": cycles,
                    "started_at": started,
                    "completed_at": now(),
                    "status": "error_retryable",
                    "error": repr(exc),
                }
                write_state(args.state_file, {
                    "schema_version": "DAEMON-RESEARCH-LOOP-0.1",
                    "status": "retrying",
                    "last_cycle": cycles,
                    "last_run_id": run_id,
                    "last_error": repr(exc),
                    "last_error_at": record["completed_at"],
                    "stop_file": str(args.stop_file),
                })
            append_jsonl(args.log_file, record)
            for _ in range(args.interval_seconds):
                if args.stop_file.exists():
                    break
                time.sleep(1)
    finally:
        write_state(args.state_file, {
            "schema_version": "DAEMON-RESEARCH-LOOP-0.1",
            "status": "stopped",
            "stopped_at": now(),
            "cycles": cycles,
            "stop_file": str(args.stop_file),
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
