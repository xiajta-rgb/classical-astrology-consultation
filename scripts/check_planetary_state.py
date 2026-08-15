"""Regression checks for declared motion, retrograde and visibility evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from planetary_state import calculate  # noqa: E402


def _by_name(result: dict, name: str) -> dict:
    return next(item for item in result["planets"] if item["planet"] == name)


def main() -> int:
    sparse = calculate({
        "zodiac": "tropical",
        "sect": "night",
        "placements": {"水星": {"sign": "天蝎", "house": 5}},
    })
    unknown = _by_name(sparse, "水星")["motion_visibility"]
    assert unknown["speed_status"] == "unknown_due_to_missing_motion"
    assert unknown["retrograde_status"] == "unknown_due_to_missing_motion"
    assert unknown["visibility_status"] == "unknown_due_to_missing_visibility"
    assert unknown["is_retrograde"] is None

    declared = calculate({
        "zodiac": "tropical",
        "sect": "night",
        "placements": {
            "水星": {
                "sign": "天蝎",
                "house": 5,
                "degree": 14.5,
                "speed": -1.2,
                "is_retrograde": True,
                "visibility": "under_beams",
            }
        },
    })
    motion = _by_name(declared, "水星")["motion_visibility"]
    assert motion["speed_status"] == "declared" and motion["speed"] == -1.2
    assert motion["retrograde_status"] == "declared" and motion["is_retrograde"] is True
    assert motion["visibility_status"] == "declared" and motion["visibility"] == "under_beams"

    # A numeric speed alone must not be converted into a retrograde claim.
    speed_only = calculate({
        "zodiac": "tropical",
        "sect": "day",
        "placements": {"火星": {"sign": "处女", "house": 2, "speed": -0.4}},
    })
    speed_only_motion = _by_name(speed_only, "火星")["motion_visibility"]
    assert speed_only_motion["speed_status"] == "declared"
    assert speed_only_motion["retrograde_status"] == "unknown_due_to_missing_motion"
    assert speed_only_motion["is_retrograde"] is None

    print("PASS planetary-state self-test: motion, retrograde and visibility stay declared-or-unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
