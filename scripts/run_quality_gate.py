#!/usr/bin/env python3
"""Run the configured project quality gate as one deterministic command."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/quality_gate.yaml"


def load_config() -> dict[str, Any]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if data.get("version") != "QUALITY-GATE-1.0":
        raise ValueError("quality gate version is missing or unsupported")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("quality gate must declare at least one check")
    ids = [str(item.get("id", "")) for item in checks]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("quality gate check ids must be present and unique")
    for item in checks:
        raw_command = item.get("command", "")
        parts = [str(value) for value in raw_command] if isinstance(raw_command, list) else shlex.split(str(raw_command))
        if not parts:
            raise ValueError("quality gate command cannot be empty")
        command = Path(parts[0])
        if command.is_absolute() or ".." in command.parts:
            raise ValueError(f"quality gate command must stay inside project: {command}")
        if int(item.get("timeout_seconds", 60)) <= 0:
            raise ValueError(f"quality gate timeout must be positive: {item.get('id')}")
    return data


def run_gate(*, json_output: bool = False) -> dict[str, Any]:
    config = load_config()
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    for spec in config["checks"]:
        check_id = str(spec.get("id", ""))
        raw_command = spec.get("command", "")
        command_parts = [str(value) for value in raw_command] if isinstance(raw_command, list) else shlex.split(str(raw_command))
        command = ROOT / command_parts[0] if command_parts else ROOT / ""
        timeout = int(spec.get("timeout_seconds", 60))
        if not check_id or not command.is_file():
            results.append({"id": check_id, "status": "configuration_error", "command": str(command)})
            if spec.get("required", True):
                break
            continue
        began = time.monotonic()
        try:
            completed = subprocess.run(
                [config.get("python", sys.executable), str(command), *command_parts[1:]],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            status = "passed" if completed.returncode == 0 else "failed"
            row = {
                "id": check_id,
                "status": status,
                "returncode": completed.returncode,
                "duration_seconds": round(time.monotonic() - began, 3),
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        except subprocess.TimeoutExpired as exc:
            row = {
                "id": check_id,
                "status": "timeout",
                "duration_seconds": round(time.monotonic() - began, 3),
                "stdout": str(exc.stdout or "").strip(),
                "stderr": str(exc.stderr or "").strip(),
            }
        results.append(row)
        if row["status"] != "passed" and spec.get("required", True):
            break
    failed = [row for row in results if row["status"] != "passed"]
    report = {
        "schema_version": "QUALITY-GATE-REPORT-1.0",
        "started_at": started_at,
        "duration_seconds": round(time.monotonic() - started, 3),
        "status": "failed" if failed else "passed",
        "checks": results,
    }
    if json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in results:
            print(f"{row['status'].upper():<18} {row['id']}")
        print(f"QUALITY GATE: {report['status'].upper()}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_gate(json_output=args.json_output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
