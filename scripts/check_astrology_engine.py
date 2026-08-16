"""Regression checks for the project-local natal and predictive engine."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "astrology_engine" / "MANIFEST.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from astrology_engine import calculate_bundle, calculate_natal, refine_aspect_contacts  # noqa: E402
from astrology_engine.predictive import calculate_predictive, configure_ephemeris  # noqa: E402
from astrology_engine.predictive_events import scan_progressive_window  # noqa: E402


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ephe_dir = ROOT / "astrology_engine" / "ephh_core" / "ephe"
    configure_ephemeris()
    for name, expected in manifest["ephemeris"]["sha256"].items():
        path = ephe_dir / name
        if not path.exists():
            raise SystemExit(f"FAIL missing ephemeris file: {path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"FAIL ephemeris hash mismatch: {name}")

    natal = calculate_natal("1996-11-11T22:25:00", lat=27.83, lon=113.13, tz=8.0, house_system="P")
    if natal["zodiac"] != "tropical" or natal["house_system"] != "Placidus":
        raise SystemExit("FAIL natal policy envelope")
    if not natal["placements"] or not natal["houses"].get("house_cusps"):
        raise SystemExit("FAIL natal placements or cusps missing")
    if not {"chart_id", "birth_place", "provenance"}.issubset(natal):
        raise SystemExit("FAIL natal identity/provenance contract")
    if not all("motion" in aspect for aspect in natal["aspects"]):
        raise SystemExit("FAIL natal aspect motion metadata missing")

    whole_sign = calculate_natal("1996-11-11T22:25:00", lat=27.83, lon=113.13, tz=8.0, house_system="W")
    other_location = calculate_natal("1996-11-11T22:25:00", lat=31.23, lon=121.47, tz=8.0, house_system="P")
    if natal["chart_id"] == other_location["chart_id"]:
        raise SystemExit("FAIL chart identity ignored location")
    asc_sign_start = int(whole_sign["houses"]["asc"] // 30.0) * 30.0
    if whole_sign["houses"]["house_cusps"][0] != asc_sign_start:
        raise SystemExit("FAIL Whole Sign first cusp was not normalized to Ascendant sign start")
    dst_chart = calculate_natal(
        "2026-07-01T12:00:00",
        lat=31.23,
        lon=121.47,
        timezone_name="Asia/Shanghai",
    )
    if dst_chart["timezone_source"] != "iana_timezone" or dst_chart["tz"] != 8.0:
        raise SystemExit("FAIL IANA timezone normalization")
    try:
        calculate_natal("1996-11-11T22:25:00", lat=27.83, lon=113.13, tz=8.0, house_system="BAD")
    except ValueError:
        pass
    else:
        raise SystemExit("FAIL unsupported house system silently fell back")

    bundle = calculate_bundle(
        "1996-11-11T22:25:00",
        ["secondary", "tertiary", "solar_arc", "solar_return", "lunar_return", "firdaria", "profection", "transit"],
        target_datetime="2026-08-15T12:00:00",
        target_year=2026,
        lat=27.83,
        lon=113.13,
        tz=8.0,
        house_system="P",
    )
    expected_types = {"secondary", "tertiary", "solar_arc", "solar_return", "lunar_return", "firdaria", "profection", "transit"}
    if set(bundle["techniques"]) != expected_types:
        raise SystemExit("FAIL predictive technique bundle")
    if any(item.get("chart_id") != natal["chart_id"] for item in bundle["techniques"].values()):
        raise SystemExit("FAIL predictive envelopes lost shared chart identity")
    partial = calculate_bundle("1996-11-11T22:25:00", ["not_a_real_technique"], lat=27.83, lon=113.13)
    if partial["status"] != "partial" or "not_a_real_technique" not in partial["errors"]:
        raise SystemExit("FAIL predictive bundle did not preserve per-technique errors")

    # Regression guard for the exhaustive timing layer: auxiliary outer
    # planets must not disappear from the candidate scan.  This catches the
    # previous manual-filter bug that omitted secondary Moon--natal Pluto.
    candidates = scan_progressive_window(
        "secondary",
        "1996-11-11T22:25:00",
        start_datetime=datetime(2024, 10, 1, 12),
        end_datetime=datetime(2024, 11, 30, 12),
        lat=27.83,
        lon=113.13,
        tz=8.0,
        house_system="P",
    )
    if not any(
        row["moving_body"] == "Moon"
        and row["natal_point"] == "Pluto"
        and row["aspect"] == "conjunction"
        and row["natal_layer"] == "auxiliary_context"
        for row in candidates
    ):
        raise SystemExit("FAIL exhaustive timing scan omitted secondary Moon-Pluto")

    # The calibrated tertiary profile must reproduce both declared reference
    # windows: conjunction near 2024-12-20 and square near 2026-07-05.
    tertiary = calculate_predictive(
        "tertiary",
        "1996-11-11T22:25:00",
        target_datetime="2024-12-20T23:59:00",
        lat=27.83,
        lon=113.13,
        tz=8.0,
        house_system="P",
    )["result"]
    if tertiary.get("calculation_profile") != "project_local_ephh_tertiary_v3_sidereal":
        raise SystemExit("FAIL tertiary profile was not upgraded to calibrated v3")
    moon_lon = float(tertiary["planets"]["Moon"]["ecliptic_longitude"])
    mars_lon = float(natal["placements"]["Mars"]["ecliptic_longitude"])
    moon_mars_orb = abs(((moon_lon - mars_lon + 180.0) % 360.0) - 180.0)
    if moon_mars_orb > 3.0:
        raise SystemExit(f"FAIL calibrated tertiary Moon-Mars reference orb: {moon_mars_orb:.4f}")
    tertiary_2026 = calculate_predictive(
        "tertiary",
        "1996-11-11T22:25:00",
        target_datetime="2026-07-05T12:00:00",
        lat=27.83,
        lon=113.13,
        tz=8.0,
        house_system="P",
    )["result"]
    moon_2026 = float(tertiary_2026["planets"]["Moon"]["ecliptic_longitude"])
    square_orb_2026 = abs(
        abs(((moon_2026 - mars_lon + 180.0) % 360.0) - 180.0) - 90.0
    )
    if square_orb_2026 > 3.0:
        raise SystemExit(f"FAIL calibrated tertiary 2026 Moon-Mars square orb: {square_orb_2026:.4f}")

    refined = refine_aspect_contacts(
        "transit",
        "1996-11-11T22:25:00",
        start_datetime=datetime(2026, 8, 1),
        end_datetime=datetime(2026, 8, 3),
        lat=27.83,
        lon=113.13,
        tz=8.0,
        step_hours=12.0,
        max_contacts=1,
    )
    if refined and "exact_datetime" not in refined[0]:
        raise SystemExit("FAIL transit refinement did not return exact_datetime")
    print(f"PASS local astrology engine: natal + {len(expected_types)} predictive techniques; bundled ephemeris hashes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
