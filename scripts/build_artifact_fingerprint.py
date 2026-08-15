#!/usr/bin/env python3
"""Create a deterministic SHA-256 manifest for release artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build(paths: list[Path]) -> dict[str, object]:
    artifacts = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        data = path.read_bytes()
        artifacts.append({
            "path": path.as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return {"schema_version": "ARTIFACT-FINGERPRINT-0.1", "artifacts": artifacts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path, help="verify paths against an existing manifest")
    args = parser.parse_args()
    if args.verify:
        manifest = json.loads(args.verify.read_text(encoding="utf-8"))
        findings = []
        for item in manifest.get("artifacts", []):
            path = Path(item["path"])
            if not path.exists():
                findings.append(f"missing:{path.as_posix()}")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item.get("sha256"):
                findings.append(f"hash_mismatch:{path.as_posix()}")
        if findings:
            print("FAIL")
            print("\n".join(findings))
            return 1
        print(f"PASS artifact fingerprint verification: {len(manifest.get('artifacts', []))} artifacts")
        return 0
    if not args.paths:
        parser.error("provide paths or --verify manifest")
    result = json.dumps(build(args.paths), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
