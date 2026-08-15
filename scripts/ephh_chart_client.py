"""Run the local ephh calculator and normalize its output to Chart Facts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts.planetary_state import CLASSICAL
except ModuleNotFoundError:  # direct execution from the scripts directory
    from planetary_state import CLASSICAL


ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).resolve().with_name("ephh_worker.py")
DEFAULT_EPHH_ROOT = Path(r"C:\Users\xmls\Documents\Qcode\ephh")
DEFAULT_PY312 = Path(r"C:\Users\xmls\AppData\Local\Programs\Python\Python312\python.exe")
_CLASSICAL_ENGLISH = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
POINT_NAMES = dict(zip(_CLASSICAL_ENGLISH, CLASSICAL))
POINT_NAMES.update({
    "Uranus": "天王", "Neptune": "海王", "Pluto": "冥王",
    "North Node": "北交", "South Node": "南交", "Chiron": "凯龙",
    "Juno": "婚神", "Fortune": "福点",
})


def _sign_name(value: Any) -> Any:
    """Chart Facts uses bare Chinese sign names; ephh returns names ending in 座."""
    return value[:-1] if isinstance(value, str) and value.endswith("座") else value


def _interpreter(explicit: Path | None) -> Path:
    candidates = [explicit, Path(os.environ["EPHH_PYTHON"]) if os.environ.get("EPHH_PYTHON") else None, DEFAULT_PY312, Path(sys.executable)]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    raise FileNotFoundError("no compatible ephh Python interpreter found; set EPHH_PYTHON")


def resolve_location(place: str, lat: float | None, lon: float | None, timeout: int = 20) -> tuple[float, float, str]:
    """Resolve a place only when coordinates were not supplied explicitly."""
    if (lat is None) != (lon is None):
        raise ValueError("lat and lon must be supplied together")
    if lat is not None and lon is not None:
        return float(lat), float(lon), "user_declared_coordinates"
    endpoint = os.environ.get("EPHH_GEOCODER_URL", "https://nominatim.openstreetmap.org/search")
    query = urllib.parse.urlencode({"q": place, "format": "jsonv2", "limit": 1})
    request = urllib.request.Request(
        f"{endpoint}?{query}",
        headers={"User-Agent": "classical-astrology-consultation/0.1 (research adapter)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list) or not payload:
        raise RuntimeError(f"geocoder returned no result for {place!r}")
    result = payload[0]
    try:
        resolved_lat = float(result["lat"])
        resolved_lon = float(result["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("geocoder result has invalid coordinates") from exc
    display = result.get("display_name") or place
    return resolved_lat, resolved_lon, f"Nominatim:{display}"


def run_ephh(params: dict[str, Any], ephh_root: Path, interpreter: Path) -> dict[str, Any]:
    command = [str(interpreter), str(WORKER), "--root", str(ephh_root), "--params", json.dumps(params, ensure_ascii=False)]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
    stdout = completed.stdout.strip()
    if not stdout:
        raise RuntimeError(f"ephh worker returned no JSON (exit={completed.returncode}): {completed.stderr[-1000:]}")
    result = json.loads(stdout.splitlines()[-1])
    if completed.returncode != 0 or result.get("status") == "error":
        raise RuntimeError(result.get("error") or completed.stderr[-1000:] or "ephh worker failed")
    return result


def _point(raw: dict[str, Any]) -> dict[str, Any]:
    zodiac = raw.get("zodiac") or {}
    return {
        "sign": _sign_name(zodiac.get("name")),
        "degree": zodiac.get("degree"),
        "ecl_lon": raw.get("ecliptic_longitude"),
        "ecl_lat": raw.get("ecliptic_latitude"),
        "house": raw.get("house_number"),
        "speed": raw.get("speed"),
        "is_retrograde": raw.get("is_retrograde"),
    }


ASPECT_DEFS = (("合", 0.0), ("六合", 60.0), ("刑", 90.0), ("拱", 120.0), ("冲", 180.0))


def _angular_distance(a: float, b: float) -> float:
    delta = abs((a - b) % 360.0)
    return min(delta, 360.0 - delta)


def calculate_aspects(placements: dict[str, dict[str, Any]], max_orb: float = 8.0) -> list[dict[str, Any]]:
    """Generate transparent major-aspect candidates from ephh longitudes.

    Applying/separating is intentionally left unknown until a dedicated
    motion-policy layer is enabled; the facts validator therefore prevents
    these candidates from being treated as interpretive proof automatically.
    """
    rows: list[dict[str, Any]] = []
    items = [(name, value) for name, value in placements.items() if isinstance(value.get("ecl_lon"), (int, float))]
    for index, (left_name, left) in enumerate(items):
        for right_name, right in items[index + 1:]:
            distance = _angular_distance(float(left["ecl_lon"]), float(right["ecl_lon"]))
            candidates = [(abs(distance - angle), aspect, angle) for aspect, angle in ASPECT_DEFS]
            error, aspect, angle = min(candidates, key=lambda row: row[0])
            if error > max_orb:
                continue
            rows.append({
                "planet1": left_name,
                "planet2": right_name,
                "type": aspect,
                "angle": angle,
                "orb": round(error, 4),
                "applying": None,
                "motion_status": "unknown_without_motion_policy",
                "source": "computed_from_ephh_ecliptic_longitudes",
            })
    return sorted(rows, key=lambda row: (row["orb"], row["planet1"], row["planet2"]))


def normalize(envelope: dict[str, Any], request: dict[str, Any], location_source: str) -> dict[str, Any]:
    raw = envelope["raw_response"]
    points = dict(raw.get("ephemeris") or {})
    points.update(envelope.get("extra_points") or {})
    placements = {POINT_NAMES[name]: _point(value) for name, value in points.items() if name in POINT_NAMES}
    axes = {}
    for key, value in (raw.get("axes") or {}).items():
        zodiac = value.get("zodiac") or {}
        axes["asc" if key == "asc" else "mc" if key == "mc" else "des" if key == "des" else "ic"] = {
            "sign": _sign_name(zodiac.get("name")), "degree": zodiac.get("degree"), "ecl_lon": value.get("ecl_lon")
        }
    cusps = {}
    cusp_degrees = {}
    for item in raw.get("house_cusps_detail") or []:
        number = str(item.get("house_number"))
        zodiac = item.get("zodiac") or {}
        cusps[number] = _sign_name(zodiac.get("name"))
        cusp_degrees[number] = {"sign": _sign_name(zodiac.get("name")), "degree": zodiac.get("degree"), "ecl_lon": item.get("ecl_lon")}
    sun_house = placements.get(POINT_NAMES["Sun"], {}).get("house")
    sect = "night" if sun_house in {1, 2, 3, 4, 5, 6} else "day" if sun_house in {7, 8, 9, 10, 11, 12} else None
    inp = raw.get("input") or {}
    return {
        "chart_id": f"ephh-{request['year']:04d}{request['month']:02d}{request['day']:02d}-{request['hour']:02d}{request['minute']:02d}",
        "source": "local_ephh_project",
        "source_engine": envelope.get("engine"),
        "source_project_root": envelope.get("project_root"),
        "birth_date": f"{request['year']:04d}-{request['month']:02d}-{request['day']:02d}",
        "birth_time": f"{request['hour']:02d}:{request['minute']:02d}:{request.get('second', 0):02d}",
        "birth_place": request.get("place"),
        "lat": request["lat"], "lon": request["lon"], "tz": request["tz"],
        "zodiac": "tropical",
        "zodiac_source": "ephh Swiss Ephemeris default; sidereal mode not enabled by project",
        "house_system": inp.get("house_system", "Placidus"),
        "sect": sect,
        "sect_source": "inferred_from_ephh_sun_house",
        "rule_versions": {
            "terms": "egyptian",
            "triplicity": "dorotheus_style_three_rulers",
            "faces": "chaldean",
            "reception": "direction_plus_connection_required",
            "aspect": "application_separation_required",
        },
        "placements": placements,
        "axes": axes,
        "cusps": cusps,
        "cusp_degrees": cusp_degrees,
        "fly_ins": {},
        "aspects": calculate_aspects(placements),
        "aspect_policy": {
            "types": [name for name, _ in ASPECT_DEFS],
            "max_orb": 8.0,
            "source": "computed_from_ephh_ecliptic_longitudes",
            "applying_separating": "not_interpreted_until_motion_policy_is_enabled",
        },
        "receptions": [],
        "ephh_input": inp,
        "ephh_raw_response": raw,
        "calculation_diagnostics": envelope.get("diagnostics", ""),
        "location_source": location_source,
        "location_resolution": {
            "status": "resolved",
            "source": location_source,
            "precision_warning": "administrative centroid or geocoded place is not an exact birth address" if "Nominatim" in location_source else None,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Calculate a chart through local ephh")
    for name in ("year", "month", "day", "hour", "minute"):
        p.add_argument(f"--{name}", type=int, required=True)
    p.add_argument("--second", type=int, default=0)
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--tz", type=float, default=8.0)
    p.add_argument("--place", required=True)
    p.add_argument("--location-source")
    p.add_argument("--house-system", default="P")
    p.add_argument("--ephh-root", type=Path, default=DEFAULT_EPHH_ROOT)
    p.add_argument("--python", dest="python_path", type=Path)
    p.add_argument("--output", type=Path)
    return p


def main() -> int:
    args = build_parser().parse_args()
    lat, lon, resolved_source = resolve_location(args.place, args.lat, args.lon)
    request = {name: getattr(args, name) for name in ("year", "month", "day", "hour", "minute", "second", "lat", "lon", "tz")}
    request["lat"], request["lon"] = lat, lon
    request["place"] = args.place
    params = dict(year=args.year, month=args.month, day=args.day, hour=args.hour, minute=args.minute, second=args.second, city=None, lat=lat, lon=lon, tz=args.tz, house_system=args.house_system, natal_year=None, natal_month=None, natal_day=None, natal_hour=None, natal_minute=None, natal_second=None, natal_lat=None, natal_lon=None, natal_tz=None)
    envelope = run_ephh(params, args.ephh_root.resolve(), _interpreter(args.python_path))
    result = normalize(envelope, request, args.location_source or resolved_source)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
