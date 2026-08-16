"""Explicit place-to-coordinate resolution for the local calculation engine."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLACE_ALIASES = ROOT / "config" / "place_aliases.json"


def _normalise_place(value: str) -> str:
    return "".join(str(value).strip().lower().split())


def _local_alias(place: str) -> dict[str, Any] | None:
    """Return a bounded offline alias before network geocoding is attempted."""
    try:
        payload = json.loads(PLACE_ALIASES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    wanted = _normalise_place(place)
    for label, item in payload.get("places", {}).items():
        if _normalise_place(label) != wanted:
            continue
        try:
            return {
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "source": "local_place_alias",
                "display_name": label,
                "precision_warning": item.get("precision_warning", "administrative_centroid"),
                "timezone": item.get("timezone"),
            }
        except (KeyError, TypeError, ValueError):
            return None
    return None


def resolve_place(place: str, timeout: int = 20) -> dict[str, Any]:
    if not str(place).strip():
        raise ValueError("place must not be empty")
    local = _local_alias(place)
    if local is not None:
        return local
    endpoint = os.environ.get("EPHH_GEOCODER_URL", "https://nominatim.openstreetmap.org/search")
    query = urllib.parse.urlencode({"q": place, "format": "jsonv2", "limit": 1})
    request = urllib.request.Request(
        f"{endpoint}?{query}",
        headers={"User-Agent": "classical-astrology-consultation-local-engine/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"could not resolve place {place!r}; provide explicit lat/lon or configure EPHH_GEOCODER_URL"
        ) from exc
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"geocoder returned no result for {place!r}")
    item = payload[0]
    try:
        lat, lon = float(item["lat"]), float(item["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("geocoder returned invalid coordinates") from exc
    return {
        "lat": lat,
        "lon": lon,
        "source": "Nominatim",
        "display_name": item.get("display_name") or place,
        "precision_warning": "geocoded place centroid is not an exact birth address",
    }


__all__ = ["resolve_place"]
