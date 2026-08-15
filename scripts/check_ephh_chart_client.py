"""Regression checks for the local ephh chart adapter.

The self-test is offline: it exercises normalization and aspect generation
without requiring the external ephh project or a network request.  The actual
Swiss Ephemeris smoke run is performed separately and its JSON fixture is
versioned under references/fixtures.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ephh_chart_client as adapter  # noqa: E402


def main() -> int:
    placements = {
        "太阳": {"ecl_lon": 10.0, "house": 1},
        "月亮": {"ecl_lon": 12.0, "house": 1},
        "火星": {"ecl_lon": 70.0, "house": 2},
        "木星": {"ecl_lon": 200.0, "house": 8},
    }
    aspects = adapter.calculate_aspects(placements)
    assert any(row["planet1"] == "太阳" and row["planet2"] == "月亮" and row["type"] == "合" for row in aspects)
    assert any(row["planet1"] == "太阳" and row["planet2"] == "火星" and row["type"] == "六合" for row in aspects)
    assert all(row["applying"] is None and row["motion_status"] == "unknown_without_motion_policy" for row in aspects)
    assert adapter._sign_name("天蝎座") == "天蝎"
    assert adapter._sign_name(None) is None
    assert adapter.resolve_location("test", 27.8, 113.2) == (27.8, 113.2, "user_declared_coordinates")
    try:
        adapter.resolve_location("test", 27.8, None)
    except ValueError as exc:
        assert "supplied together" in str(exc)
    else:
        raise AssertionError("partial coordinates were accepted")

    raw = {
        "input": {"house_system": "Placidus"},
        "ephemeris": {
            "Sun": {"ecliptic_longitude": 229.48, "ecliptic_latitude": 0.0, "house_number": 4, "speed": 1.0, "is_retrograde": False, "zodiac": {"name": "天蝎座", "degree": 19.48}},
            "Moon": {"ecliptic_longitude": 234.82, "ecliptic_latitude": 3.8, "house_number": 4, "speed": 13.7, "is_retrograde": False, "zodiac": {"name": "天蝎座", "degree": 24.82}},
        },
        "axes": {"asc": {"ecl_lon": 119.5, "zodiac": {"name": "巨蟹座", "degree": 29.5}}},
        "house_cusps_detail": [{"house_number": 1, "ecl_lon": 119.5, "zodiac": {"name": "巨蟹座", "degree": 29.5}}],
    }
    normalized = adapter.normalize({"raw_response": raw, "engine": "test", "project_root": "test", "extra_points": {}}, {
        "year": 1996, "month": 11, "day": 11, "hour": 22, "minute": 25, "second": 0,
        "lat": 27.8, "lon": 113.2, "tz": 8.0, "place": "test",
    }, "test_coordinates")
    assert normalized["placements"]["太阳"]["sign"] == "天蝎"
    assert normalized["axes"]["asc"]["sign"] == "巨蟹"
    assert normalized["aspect_policy"]["max_orb"] == 8.0
    print("PASS ephh chart adapter self-test: normalization, sign cleanup and aspect candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
