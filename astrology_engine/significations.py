"""Canonical responsibility-chain derivation from one natal Chart Facts pass."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .natal import calculate_natal
from .ephh_core.astro.constants import PLANET_NAMES_CN, SIGN_RULERS_TRADITIONAL, ZODIAC_NAMES


def calculate_responsibilities(
    birth_datetime: datetime | str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: float = 8.0,
    timezone_name: str | None = None,
    house_system: str = "P",
    place: str | None = None,
    chart_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive house rulers and directed flows without recalculating the chart.

    This wrapper is the production responsibility-chain interface.  The older
    ``ephh_core.astro.significations`` function remains available for legacy
    payloads, but new birth-date input must use this single Chart Facts source.
    """
    # Callers that already ran the canonical natal engine must pass its
    # envelope here.  This keeps every downstream module on the same chart
    # id and avoids silently calculating a second Chart Facts object.
    if chart_facts is not None:
        required = {"chart_id", "placements", "houses", "aspects", "engine"}
        missing = sorted(required - set(chart_facts))
        if missing:
            raise ValueError(f"chart_facts is not a canonical natal package; missing {missing}")
    natal = chart_facts or calculate_natal(
        birth_datetime,
        lat=lat,
        lon=lon,
        tz=tz,
        timezone_name=timezone_name,
        house_system=house_system,
        place=place,
    )
    placements = natal["placements"]
    flying: list[dict[str, Any]] = []
    for number, cusp in enumerate(natal["houses"]["house_cusps"][:12], start=1):
        sign_index = int(float(cusp) // 30.0) % 12
        ruler = SIGN_RULERS_TRADITIONAL[sign_index]
        ruler_data = placements.get(ruler, {})
        flying.append({
            "house": number,
            "cusp": cusp,
            "cusp_sign": ZODIAC_NAMES[sign_index],
            "ruler": ruler,
            "ruler_cn": PLANET_NAMES_CN.get(ruler, ruler),
            "ruler_house": ruler_data.get("house_number"),
            "ruler_sign": (ruler_data.get("zodiac") or {}).get("name"),
            "direction": f"{number}->{ruler_data.get('house_number')}" if ruler_data.get("house_number") else None,
        })
    return {
        "schema_version": "RESPONSIBILITY-1.0",
        "chart_id": natal["chart_id"],
        "source_chart_facts": natal["chart_id"],
        "engine": natal["engine"],
        "birth_datetime": natal["birth_datetime"],
        "place": natal.get("place"),
        "birth_place": natal.get("birth_place", natal.get("place")),
        "lat": natal["lat"],
        "lon": natal["lon"],
        "tz": natal["tz"],
        "timezone_name": natal.get("timezone_name"),
        "zodiac": natal["zodiac"],
        "house_system": natal["house_system"],
        "house_flying": flying,
        "aspects": natal["aspects"],
        "is_day_chart": natal["is_day_chart"],
        "provenance": {
            "chart_facts": "astrology_engine.natal.calculate_natal",
            "rulership": "traditional_sign_rulers_from_chart_facts",
            "direction_rule": "A ruler in B means A responsibility enters B",
        },
    }


__all__ = ["calculate_responsibilities"]
