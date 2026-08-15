"""Read-only adapter for the public CET ephemeris endpoint.

It stores the raw response alongside a small normalized view. It does not
interpret modern points or trust the site's reception text as classical fact.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests


ENDPOINT = "https://cet.pythonanywhere.com/api/calculate-ephemeris"


def fetch_chart(params: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    response = requests.get(ENDPOINT, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"CET returned non-object JSON: {type(payload).__name__}")
    if payload.get("status") != "success":
        raise RuntimeError(f"CET returned non-success status: {payload.get('status')!r}")
    return payload


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    """Return stable analysis-layer fields while preserving the raw payload."""
    if not isinstance(payload, dict):
        raise TypeError(f"CET payload must be an object, got {type(payload).__name__}")
    ephemeris = payload.get("ephemeris")
    if ephemeris is None:
        ephemeris = {}
    if not isinstance(ephemeris, dict):
        raise TypeError("CET ephemeris must be an object when present")
    houses = payload.get("house_cusps_detail")
    if houses is None:
        houses = payload.get("house_cusps")
    if houses is None:
        houses = []
    if not isinstance(houses, list):
        raise TypeError("CET house cusps must be a list when present")
    aspects = payload.get("aspects")
    if aspects is None:
        aspects = []
    if not isinstance(aspects, list):
        raise TypeError("CET aspects must be a list when present")
    receptions = payload.get("mutual_receptions")
    if receptions is None:
        receptions = []
    if not isinstance(receptions, list):
        raise TypeError("CET mutual receptions must be a list when present")
    return {
        "input": payload.get("input", {}),
        "planets": ephemeris,
        "axes": payload.get("axes", {}),
        "houses": houses,
        "aspects": aspects,
        "fortune": ephemeris.get("Fortune"),
        "site_mutual_receptions": receptions,
        "raw_response": payload,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read CET's public ephemeris API")
    for name in ("year", "month", "day", "hour", "minute"):
        parser.add_argument(f"--{name}", type=int, required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, default=8)
    parser.add_argument("--house-system", default="P")
    parser.add_argument("--city")
    parser.add_argument("--output", type=Path, help="Write normalized JSON to this path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    params = {
        "year": args.year,
        "month": args.month,
        "day": args.day,
        "hour": args.hour,
        "minute": args.minute,
        "lat": args.lat,
        "lon": args.lon,
        "tz": args.tz,
        "house_system": args.house_system,
    }
    if args.city:
        params["city"] = args.city
    result = normalize(fetch_chart(params))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
