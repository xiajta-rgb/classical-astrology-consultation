import logging
import swisseph as real_swe
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .constants import PLANETS, ASPECT_DEFS, PLANET_NAMES_CN, ASPECT_NAMES_CN
from .house import calculate_house_cusps, determine_planet_house
from .utils import datetime_to_jd, calc_planet_positions, calc_aspects, calc_natal_chart
from ..core.utils import longitude_to_zodiac

logger = logging.getLogger(__name__)


def calculate_synastry(
    birth1_dt: datetime, lat1: float, lon1: float, tz1: float,
    birth2_dt: datetime, lat2: float, lon2: float, tz2: float,
    house_system: str = "P"
) -> Dict[str, Any]:
    chart1 = calc_natal_chart(birth1_dt, lat1, lon1, tz1, house_system)
    chart2 = calc_natal_chart(birth2_dt, lat2, lon2, tz2, house_system)

    cross_aspects = _calc_cross_aspects(chart1["planets"], chart2["planets"])

    compatibility = _calc_compatibility(chart1["planets"], chart2["planets"], cross_aspects)

    return {
        "chart_type": "synastry",
        "person1": {
            "birth_datetime": birth1_dt.isoformat(),
            "lat": lat1, "lon": lon1,
            "planets": chart1["planets"],
            "houses": chart1["houses"],
        },
        "person2": {
            "birth_datetime": birth2_dt.isoformat(),
            "lat": lat2, "lon": lon2,
            "planets": chart2["planets"],
            "houses": chart2["houses"],
        },
        "cross_aspects": cross_aspects,
        "compatibility": compatibility,
    }


def calculate_composite(
    birth1_dt: datetime, lat1: float, lon1: float, tz1: float,
    birth2_dt: datetime, lat2: float, lon2: float, tz2: float,
    house_system: str = "P"
) -> Dict[str, Any]:
    chart1 = calc_natal_chart(birth1_dt, lat1, lon1, tz1, house_system)
    chart2 = calc_natal_chart(birth2_dt, lat2, lon2, tz2, house_system)

    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0

    composite_planets = {}
    for pname in chart1["planets"]:
        if pname in chart2["planets"]:
            lon1 = chart1["planets"][pname]["ecliptic_longitude"]
            lon2 = chart2["planets"][pname]["ecliptic_longitude"]
            mid_lon_val = _midpoint_longitude(lon1, lon2)
            zodiac = longitude_to_zodiac(mid_lon_val)
            composite_planets[pname] = {
                "name": pname,
                "ecliptic_longitude": round(mid_lon_val, 4),
                "zodiac": zodiac,
                "is_retrograde": chart1["planets"][pname].get("is_retrograde", False) or chart2["planets"][pname].get("is_retrograde", False),
            }

    asc1 = chart1["houses"]["asc"]
    asc2 = chart2["houses"]["asc"]
    composite_asc = _midpoint_longitude(asc1, asc2)

    mc1 = chart1["houses"]["mc"]
    mc2 = chart2["houses"]["mc"]
    composite_mc = _midpoint_longitude(mc1, mc2)

    jd1 = datetime_to_jd(birth1_dt, tz1)
    jd2 = datetime_to_jd(birth2_dt, tz2)
    ref_jd = (jd1 + jd2) / 2.0
    house_data = calculate_house_cusps(ref_jd, mid_lat, mid_lon, house_system)

    planet_lons = {}
    for pname, pdata in composite_planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = composite_asc
    planet_lons["Midheaven"] = composite_mc

    aspects = calc_aspects(planet_lons)

    return {
        "chart_type": "composite",
        "reference_location": {"lat": mid_lat, "lon": mid_lon},
        "person1": {
            "birth_datetime": birth1_dt.isoformat(),
            "planets": chart1["planets"],
        },
        "person2": {
            "birth_datetime": birth2_dt.isoformat(),
            "planets": chart2["planets"],
        },
        "composite_planets": composite_planets,
        "composite_houses": {
            "house_cusps": house_data["house_cusps"],
            "asc": round(composite_asc, 4),
            "mc": round(composite_mc, 4),
            "des": round((composite_asc + 180) % 360, 4),
            "ic": round((composite_mc + 180) % 360, 4),
            "house_system": house_data["house_system"],
        },
        "aspects": aspects,
    }


def _midpoint_longitude(lon1: float, lon2: float) -> float:
    diff = lon2 - lon1
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return (lon1 + diff / 2.0) % 360.0


def _calc_cross_aspects(planets1: Dict, planets2: Dict) -> List[Dict[str, Any]]:
    cross_aspects = []
    ASPECT_ORB_SYNASTRY = {
        "conjunction": 8.0,
        "opposition": 8.0,
        "trine": 8.0,
        "square": 7.0,
        "sextile": 6.0,
        "quincunx": 5.0,
        "semisquare": 3.0,
        "sesquisquare": 3.0,
    }

    KEY_PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars",
                   "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
                   "North Node", "Chiron", "Ascendant", "Midheaven"]

    for p1_name in KEY_PLANETS:
        if p1_name not in planets1:
            continue
        lon1 = planets1[p1_name]["ecliptic_longitude"]

        for p2_name in KEY_PLANETS:
            if p2_name not in planets2:
                continue
            lon2 = planets2[p2_name]["ecliptic_longitude"]

            angle_diff = abs(lon1 - lon2) % 360
            angle_diff = min(angle_diff, 360 - angle_diff)

            for asp_name, asp_def in ASPECT_DEFS.items():
                asp_orb = ASPECT_ORB_SYNASTRY.get(asp_name, asp_def["orb"])
                if abs(angle_diff - asp_def["angle"]) <= asp_orb:
                    cross_aspects.append({
                        "person1_planet": p1_name,
                        "person2_planet": p2_name,
                        "type": asp_name,
                        "angle": asp_def["angle"],
                        "orb": round(abs(angle_diff - asp_def["angle"]), 2),
                        "person1_planet_cn": PLANET_NAMES_CN.get(p1_name, p1_name),
                        "person2_planet_cn": PLANET_NAMES_CN.get(p2_name, p2_name),
                        "aspect_cn": ASPECT_NAMES_CN.get(asp_name, asp_name),
                    })
                    break

    return cross_aspects


def _calc_compatibility(planets1: Dict, planets2: Dict, cross_aspects: List) -> Dict[str, Any]:
    ASPECT_WEIGHTS = {
        "conjunction": 10,
        "opposition": 7,
        "trine": 10,
        "square": 5,
        "sextile": 8,
        "quincunx": 4,
    }

    PLANET_WEIGHTS = {
        "Sun": 10, "Moon": 10, "Venus": 9, "Mars": 7,
        "Mercury": 6, "Jupiter": 5, "Saturn": 4,
        "Uranus": 3, "Neptune": 3, "Pluto": 3,
        "North Node": 5, "Chiron": 4,
    }

    HARMONIOUS = {"trine", "sextile"}
    CHALLENGING = {"square", "opposition", "quincunx"}
    NEUTRAL = {"conjunction"}

    harmony_score = 0
    challenge_score = 0
    total_weight = 0
    key_dynamics = []

    for aspect in cross_aspects:
        p1 = aspect["person1_planet"]
        p2 = aspect["person2_planet"]
        asp_type = aspect["type"]

        weight = (PLANET_WEIGHTS.get(p1, 1) + PLANET_WEIGHTS.get(p2, 1)) / 2.0
        asp_weight = ASPECT_WEIGHTS.get(asp_type, 3)

        total_weight += weight

        if asp_type in HARMONIOUS:
            harmony_score += weight * asp_weight
            key_dynamics.append({
                "type": "harmonious",
                "description": f"{PLANET_NAMES_CN.get(p1, p1)}{ASPECT_NAMES_CN.get(asp_type, asp_type)}{PLANET_NAMES_CN.get(p2, p2)}",
            })
        elif asp_type in CHALLENGING:
            challenge_score += weight * asp_weight
            key_dynamics.append({
                "type": "challenging",
                "description": f"{PLANET_NAMES_CN.get(p1, p1)}{ASPECT_NAMES_CN.get(asp_type, asp_type)}{PLANET_NAMES_CN.get(p2, p2)}",
            })
        elif asp_type in NEUTRAL:
            harmony_score += weight * asp_weight * 0.5
            challenge_score += weight * asp_weight * 0.5

    if total_weight == 0:
        compatibility_pct = 50
    else:
        raw = (harmony_score - challenge_score * 0.6) / (harmony_score + challenge_score + 1) * 100
        compatibility_pct = max(10, min(95, 50 + raw))

    if compatibility_pct >= 80:
        level = "高度契合"
        summary = "两人星盘之间有大量和谐相位，关系自然流畅"
    elif compatibility_pct >= 65:
        level = "良好匹配"
        summary = "两人之间有较好的互动基础，虽有挑战但可调和"
    elif compatibility_pct >= 50:
        level = "中等匹配"
        summary = "两人之间有和谐也有挑战，需要彼此理解和妥协"
    elif compatibility_pct >= 35:
        level = "需要磨合"
        summary = "两人之间挑战相位较多，需要更多耐心和沟通"
    else:
        level = "差异较大"
        summary = "两人星盘差异较大，需要深刻的理解和包容"

    return {
        "score": round(compatibility_pct, 1),
        "level": level,
        "summary": summary,
        "harmony_score": round(harmony_score, 2),
        "challenge_score": round(challenge_score, 2),
        "key_dynamics": key_dynamics[:10],
    }
