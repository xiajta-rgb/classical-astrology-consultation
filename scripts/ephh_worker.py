"""Small subprocess worker for the local ephh Swiss Ephemeris project.

The worker is intentionally isolated from the main Python runtime because the
ephh wheel is currently compatible with Python 3.12, while the main workspace
may run another Python version.  It emits one JSON object on stdout and keeps
ephh's diagnostic prints out of the data channel.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any


def _chiron(root: Path, raw: dict[str, Any]) -> dict[str, Any]:
    """Calculate Chiron with the same JD/house functions used by ephh."""
    sys.path.insert(0, str(root))
    import swisseph as swe
    from api.house import determine_planet_house
    from api.utils import longitude_to_zodiac

    jd = float(raw["input"]["jd_ut"])
    ecl = swe.calc_ut(jd, swe.CHIRON, swe.FLG_SPEED)
    values = ecl[0]
    lon = float(values[0]) % 360.0
    lat = float(values[1])
    speed = float(values[3])
    cusps = raw["house_cusps"]
    house = determine_planet_house(lon, cusps)
    return {
        "name": "Chiron",
        "ecliptic_longitude": round(lon, 4),
        "ecliptic_latitude": round(lat, 4),
        "zodiac": longitude_to_zodiac(lon),
        "house_number": house,
        "is_retrograde": speed < 0,
        "speed": round(speed, 6),
    }


def calculate(root: Path, params: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
        from api.swisseph_init import ensure_swisseph_init

        if not ensure_swisseph_init():
            raise RuntimeError("ephh Swiss Ephemeris initialization failed")
        from api.ephemeris import calculate_ephemeris

        raw = calculate_ephemeris(**params)
        if raw.get("status") != "success":
            raise RuntimeError(f"ephh returned non-success status: {raw.get('status')!r}")
        extra_points = {"Chiron": _chiron(root, raw)}
    return {
        "engine": "ephh.api.ephemeris.calculate_ephemeris",
        "project_root": str(root),
        "diagnostics": diagnostics.getvalue(),
        "raw_response": raw,
        "extra_points": extra_points,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--params", required=True, help="JSON object accepted by ephh calculate_ephemeris")
    args = parser.parse_args()
    try:
        result = calculate(args.root.resolve(), json.loads(args.params))
    except Exception as exc:  # one structured error for the parent adapter
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
