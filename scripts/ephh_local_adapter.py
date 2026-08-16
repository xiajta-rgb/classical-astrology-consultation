"""Run the local ephh Swiss-Ephemeris core for tropical natal charts.

The desktop ephh project currently exposes Placidus/Equal/Koch through its
FastAPI backend, but not whole-sign houses.  This adapter calls that backend
directly (without starting a web server) and derives whole-sign house numbers
from the returned Ascendant sign.  The derivation is intentionally explicit
so the result remains auditable and can be compared with the source output.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SIGNS = tuple(bytes(item, "ascii").decode("unicode_escape") for item in (
    "\\u767d\\u7f8a", "\\u91d1\\u725b", "\\u53cc\\u5b50", "\\u5de8\\u87f9", "\\u72ee\\u5b50", "\\u5904\\u5973",
    "\\u5929\\u79e4", "\\u5929\\u874e", "\\u5c04\\u624b", "\\u6469\\u7faf", "\\u6c34\\u74f6", "\\u53cc\\u9c7c",
))
def _u(value: str) -> str:
    return bytes(value, "ascii").decode("unicode_escape")


ENGLISH_TO_CHINESE = {
    "Sun": _u("\\u592a\\u9633"), "Moon": _u("\\u6708\\u4eae"), "Mercury": _u("\\u6c34\\u661f"), "Venus": _u("\\u91d1\\u661f"),
    "Mars": _u("\\u706b\\u661f"), "Jupiter": _u("\\u6728\\u661f"), "Saturn": _u("\\u571f\\u661f"), "Uranus": _u("\\u5929\\u738b\\u661f"),
    "Neptune": _u("\\u6d77\\u738b\\u661f"), "Pluto": _u("\\u51a5\\u738b\\u661f"),
}


def _find_backend(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("EPHH_BACKEND"):
        candidates.append(Path(os.environ["EPHH_BACKEND"]))
    # Keep the user-specific desktop source discoverable without embedding
    # its mojibake path in the command line or in generated facts.
    for base in (Path.home() / "Desktop", Path.home() / "OneDrive" / "Desktop"):
        if base.exists():
            candidates.extend(sorted(base.rglob("backend.py")))
    for candidate in candidates:
        if candidate.exists() and "ephh" in str(candidate).lower():
            return candidate.resolve()
    raise FileNotFoundError(
        "local ephh backend.py not found; pass --backend or set EPHH_BACKEND"
    )


def _load_backend(path: Path) -> tuple[Any, str]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    module_name = f"ephh_backend_{digest[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ephh backend: {path}")
    module = importlib.util.module_from_spec(spec)
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
        spec.loader.exec_module(module)
    return module, digest


def _sign_index(longitude: float) -> int:
    return int(float(longitude) % 360.0 // 30.0)


def _sign_name(value: Any) -> Any:
    if isinstance(value, str) and value.endswith("座"):
        return value[:-1]
    return value


def _position(longitude: float) -> dict[str, Any]:
    normalized = float(longitude) % 360.0
    return {"sign": SIGNS[_sign_index(normalized)], "degree": round(normalized % 30.0, 4), "ecl_lon": round(normalized, 4)}


def _point(raw: dict[str, Any], house: int | None = None) -> dict[str, Any]:
    zodiac = raw.get("zodiac") or {}
    longitude = raw.get("ecliptic_longitude")
    return {
        # Derive the normalized sign from longitude.  The desktop source's
        # display-name table is stored with a legacy console-encoding issue;
        # the numerical longitude remains authoritative.
        "sign": SIGNS[_sign_index(float(longitude))] if isinstance(longitude, (int, float)) else _sign_name(zodiac.get("name")),
        "degree": zodiac.get("degree"),
        "ecl_lon": longitude,
        "ecl_lat": raw.get("ecliptic_latitude"),
        "house": house if house is not None else raw.get("house_number"),
    }


def _aspects(placements: dict[str, dict[str, Any]], max_orb: float = 8.0) -> list[dict[str, Any]]:
    definitions = ((_u("\\u5408\\u76f8"), 0.0), (_u("\\u516d\\u5408"), 60.0), (_u("\\u5211\\u76f8"), 90.0), (_u("\\u62f1\\u76f8"), 120.0), (_u("\\u5bf9\\u51b2"), 180.0))
    names = list(placements)
    rows: list[dict[str, Any]] = []
    for index, left_name in enumerate(names):
        left = placements[left_name]
        if not isinstance(left.get("ecl_lon"), (int, float)):
            continue
        for right_name in names[index + 1:]:
            right = placements[right_name]
            if not isinstance(right.get("ecl_lon"), (int, float)):
                continue
            distance = abs((float(left["ecl_lon"]) - float(right["ecl_lon"])) % 360.0)
            distance = min(distance, 360.0 - distance)
            orb, aspect, angle = min(
                ((abs(distance - target), label, target) for label, target in definitions),
                key=lambda item: item[0],
            )
            if orb <= max_orb:
                rows.append({
                    "planet1": left_name,
                    "planet2": right_name,
                    "type": aspect,
                    "angle": angle,
                    "orb": round(orb, 4),
                    "source": "computed_from_local_ephh_longitudes",
                })
    return sorted(rows, key=lambda item: (item["orb"], item["planet1"], item["planet2"]))


def _house_from_cusps(longitude: float, cusps: list[float]) -> int:
    value = float(longitude) % 360.0
    for index in range(12):
        current = float(cusps[index]) % 360.0
        following = float(cusps[(index + 1) % 12]) % 360.0
        if (current <= value < following) if current < following else (value >= current or value < following):
            return index + 1
    return 1


def _normalize(raw: dict[str, Any], request: dict[str, Any], backend: Path, source_hash: str, diagnostics: str, house_system: str) -> dict[str, Any]:
    if raw.get("status") != "success":
        raise RuntimeError(raw.get("errors") or "ephh returned non-success status")
    asc_lon = float(raw["axes"]["asc"]["ecl_lon"])
    asc_sign = _sign_index(asc_lon)
    placements: dict[str, dict[str, Any]] = {}
    for english_name, value in (raw.get("ephemeris") or {}).items():
        if english_name not in ENGLISH_TO_CHINESE:
            continue
        house = int(value.get("house_number"))
        if house_system == "whole_sign":
            house = ((_sign_index(float(value["ecliptic_longitude"])) - asc_sign) % 12) + 1
        placements[ENGLISH_TO_CHINESE[english_name]] = _point(value, house)

    axes = {}
    for key, value in (raw.get("axes") or {}).items():
        if key in {"asc", "mc", "des", "ic"}:
            axes[key] = {
                "sign": SIGNS[_sign_index(float(value["ecl_lon"]))] if isinstance(value.get("ecl_lon"), (int, float)) else _sign_name((value.get("zodiac") or {}).get("name")),
                "degree": (value.get("zodiac") or {}).get("degree"),
                "ecl_lon": value.get("ecl_lon"),
            }
    # Swiss Ephemeris returns ASC and MC at indices 0 and 1.  The desktop
    # backend labels ascmc[2]/[3] as DESC/IC, although those slots are not the
    # opposite angles.  Derive the opposite angles from the authoritative ASC
    # and MC so the project facts do not inherit that source display bug.
    if isinstance(asc_lon, (int, float)):
        axes["des"] = _position(asc_lon + 180.0)
    if isinstance(raw.get("axes", {}).get("mc", {}).get("ecl_lon"), (int, float)):
        axes["ic"] = _position(float(raw["axes"]["mc"]["ecl_lon"]) + 180.0)
    # Keep the angle point and the house-cusp convention separate.  In
    # quadrant houses MC/IC are the 10th/4th cusps; in whole-sign houses the
    # MC point is independent and may fall in a different sign-house.
    axes["asc"]["house"] = 1
    axes["des"]["house"] = 7
    axes["mc"]["house"] = 10 if house_system != "whole_sign" else ((_sign_index(float(axes["mc"]["ecl_lon"])) - asc_sign) % 12) + 1
    axes["ic"]["house"] = 4 if house_system != "whole_sign" else ((_sign_index(float(axes["ic"]["ecl_lon"])) - asc_sign) % 12) + 1
    cusps: dict[str, Any] = {}
    cusp_degrees: dict[str, Any] = {}
    if house_system == "whole_sign":
        for house in range(1, 13):
            sign_index = (asc_sign + house - 1) % 12
            longitude = sign_index * 30.0
            cusps[str(house)] = SIGNS[sign_index]
            cusp_degrees[str(house)] = {"sign": SIGNS[sign_index], "degree": 0.0, "ecl_lon": longitude}
    else:
        for item in raw.get("house_cusps_detail") or []:
            number = str(item["house_number"])
            zodiac = item.get("zodiac") or {}
            cusp_lon = item.get("ecl_lon")
            cusp_sign = SIGNS[_sign_index(float(cusp_lon))] if isinstance(cusp_lon, (int, float)) else _sign_name(zodiac.get("name"))
            cusps[number] = cusp_sign
            cusp_degrees[number] = {"sign": cusp_sign, "degree": zodiac.get("degree"), "ecl_lon": cusp_lon}

    sun_house = placements.get(_u("\\u592a\\u9633"), {}).get("house")
    sect = "night" if sun_house in {1, 2, 3, 4, 5, 6} else "day" if sun_house in {7, 8, 9, 10, 11, 12} else None
    sun_lon = next((v.get("ecl_lon") for k, v in placements.items() if k == _u("\\u592a\\u9633")), None)
    moon_lon = next((v.get("ecl_lon") for k, v in placements.items() if k == _u("\\u6708\\u4eae")), None)
    asc_lon_value = axes.get("asc", {}).get("ecl_lon")
    fortune = None
    if all(isinstance(value, (int, float)) for value in (sun_lon, moon_lon, asc_lon_value)) and sect:
        fortune_lon = (float(asc_lon_value) + (float(sun_lon) - float(moon_lon) if sect == "night" else float(moon_lon) - float(sun_lon))) % 360.0
        fortune_house = _house_from_cusps(fortune_lon, raw.get("house_cusps") or []) if house_system != "whole_sign" else ((_sign_index(fortune_lon) - asc_sign) % 12) + 1
        fortune = {**_position(fortune_lon), "house": fortune_house, "sect_formula": "night: ASC + Sun - Moon" if sect == "night" else "day: ASC + Moon - Sun"}
    return {
        "chart_id": f"ephh-{request['year']:04d}{request['month']:02d}{request['day']:02d}-{request['hour']:02d}{request['minute']:02d}-{house_system}",
        "source": "local_ephh_project",
        "source_engine": "ephh.backend.calculate_ephemeris",
        "source_backend": str(backend),
        "source_backend_sha256": source_hash,
        "birth_date": f"{request['year']:04d}-{request['month']:02d}-{request['day']:02d}",
        "birth_time": f"{request['hour']:02d}:{request['minute']:02d}:{request.get('second', 0):02d}",
        "birth_place": request["place"],
        "lat": request["lat"], "lon": request["lon"], "tz": request["tz"],
        "zodiac": "tropical",
        "house_system": "Whole Sign" if house_system == "whole_sign" else "Placidus",
        "house_assignment_source": "ascendant_sign_derivation_from_ephh_axes" if house_system == "whole_sign" else "ephh_swiss_ephemeris_houses",
        "axis_policy": "ASC/MC from ephh; DESC/IC derived as exact opposites because the desktop backend mislabels ascmc[2]/[3]. In whole-sign mode MC remains an angle point separate from the 10th house cusp.",
        "sect": sect,
        "lot_of_fortune": fortune,
        "rule_versions": {
            "zodiac": "tropical",
            "terms": "egyptian",
            "triplicity": "dorotheus_style_three_rulers",
            "faces": "chaldean",
            "reception": "direction_plus_connection_required",
            "aspect": "geometry_only; motion_status_not_available_from_backend",
        },
        "placements": placements,
        "axes": axes,
        "cusps": cusps,
        "cusp_degrees": cusp_degrees,
        "aspects": _aspects(placements),
        "raw_ephh_input": raw.get("input"),
        "raw_ephh_response": raw,
        "calculation_diagnostics": diagnostics,
    }


def calculate(request: dict[str, Any], backend_path: Path, house_system: str) -> dict[str, Any]:
    backend, source_hash = _load_backend(backend_path)
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
        raw = backend.calculate_ephemeris(
            year=request["year"], month=request["month"], day=request["day"],
            hour=request["hour"], minute=request["minute"], second=request.get("second", 0),
            city=None, lat=request["lat"], lon=request["lon"], tz=request["tz"],
            # The source backend has no whole-sign mode.  P supplies the
            # authoritative axes/longitudes; whole-sign houses are derived.
            house_system="P",
        )
    return _normalize(raw, request, backend_path, source_hash, diagnostics.getvalue(), house_system)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local ephh for the project-default Placidus natal houses; whole-sign is research-only")
    for name in ("year", "month", "day", "hour", "minute"):
        parser.add_argument(f"--{name}", type=int, required=True)
    parser.add_argument("--second", type=int, default=0)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, default=8.0)
    parser.add_argument("--place", required=True)
    parser.add_argument("--backend", type=Path)
    parser.add_argument("--house-system", choices=("placidus", "both", "whole_sign"), default="placidus")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    backend_path = _find_backend(args.backend)
    request = {name: getattr(args, name) for name in ("year", "month", "day", "hour", "minute", "second", "lat", "lon", "tz", "place")}
    systems = ("placidus", "whole_sign") if args.house_system == "both" else (args.house_system,)
    charts = {system: calculate(request, backend_path, system) for system in systems}
    result = {
        "request": request,
        "backend": str(backend_path),
        "charts": charts,
        "comparison": {
            "same_ecliptic_longitudes": True,
            "same_axes": True,
            "house_difference": "whole_sign derives one sign per house from the same Ascendant; this case is compared explicitly in each chart",
        },
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
