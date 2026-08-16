"""Legacy payload adapter for older API callers.

New birth-data workflows must use :func:`astrology_engine.significations.calculate_responsibilities`,
which exposes the canonical Chart Facts envelope and provenance contract.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from .classical import calculate_mutual_reception
from .constants import ASPECT_NAMES_CN, PLANET_NAMES_CN, SIGN_RULERS_TRADITIONAL
from .utils import calc_natal_chart, resolve_location

SIGN_NAMES = ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]
POINT_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node", "South Node", "Chiron", "Juno", "Fortune"]

def calculate_significations(payload: Dict[str, Any]) -> Dict[str, Any]:
    if payload.get("birth_datetime"):
        birth = datetime.fromisoformat(str(payload["birth_datetime"]).replace("Z", "+00:00")).replace(tzinfo=None)
    else:
        birth = datetime(int(payload["year"]), int(payload["month"]), int(payload["day"]), int(payload.get("hour", 12)), int(payload.get("minute", 0)), int(payload.get("second", 0)))
    city = payload.get("city")
    lat = payload.get("lat", payload.get("latitude")); lon = payload.get("lon", payload.get("longitude")); tz = float(payload.get("tz", payload.get("timezone", 8.0)))
    lat, lon, tz, error = resolve_location(city, float(lat) if lat is not None else None, float(lon) if lon is not None else None, tz)
    if error: raise ValueError(error)
    house_system = str(payload.get("house_system", "P")).upper()
    chart = calc_natal_chart(birth, lat, lon, tz, house_system)
    planets = chart.get("planets", {})
    planet_houses = []
    for name in POINT_ORDER:
        if name in planets:
            data = planets[name]; zodiac = data.get("zodiac") or {}
            planet_houses.append(f"{PLANET_NAMES_CN.get(name, name)}{zodiac.get('name', '')}{zodiac.get('degree_str', '')}{data.get('house_number', '')}宫")
    aspects = []
    for item in chart.get("aspects", []):
        left = item.get("planet1_cn") or PLANET_NAMES_CN.get(item.get("planet1"), item.get("planet1")); right = item.get("planet2_cn") or PLANET_NAMES_CN.get(item.get("planet2"), item.get("planet2")); typ = item.get("type_cn") or ASPECT_NAMES_CN.get(item.get("type"), item.get("type"))
        aspects.append({**item, "text": f"{left} {typ} {right}", "orb_degrees": item.get("orb")})
    flying = []
    cusps = chart.get("houses", {}).get("house_cusps", [])
    for number, cusp in enumerate(cusps[:12], 1):
        ruler = SIGN_RULERS_TRADITIONAL.get(int(float(cusp) // 30) % 12); ruler_house = (planets.get(ruler) or {}).get("house_number")
        flying.append({"house": number, "sign": SIGN_NAMES[int(float(cusp) // 30) % 12], "cusp": cusp, "ruler": ruler, "ruler_cn": PLANET_NAMES_CN.get(ruler, ruler), "ruler_house": ruler_house, "flying": f"{number}飞{ruler_house}" if ruler_house else None})
    receptions = calculate_mutual_reception(birth, lat, lon, tz, house_system).get("receptions", [])
    return {"title": "个人星盘分析", "birth": {"datetime": birth.isoformat(), "city": city, "latitude": lat, "longitude": lon, "timezone": tz}, "house_system": house_system, "planet_houses": planet_houses, "planets": planets, "aspects": aspects, "aspect_relations": [x["text"] for x in aspects], "house_flying": flying, "receptions": receptions, "houses": chart.get("houses"), "is_day_chart": chart.get("is_day_chart")}
