import logging
import swisseph as real_swe
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .constants import PLANETS, PLANET_NAMES_CN, ASPECT_DEFS, ASPECT_NAMES_CN, HOUSE_MEANINGS
from .house import calculate_house_cusps, determine_planet_house
from ..core.utils import longitude_to_zodiac, get_lnglat_by_city

logger = logging.getLogger(__name__)


def datetime_to_jd(dt: datetime, tz: float = 8.0) -> float:
    utc_dt = dt - timedelta(hours=float(tz))
    ut_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    Y = utc_dt.year
    M = utc_dt.month
    D = utc_dt.day
    if M < 3:
        Y -= 1
        M += 12
    A = Y // 100
    B = 2 - A + A // 4
    return 367 * Y - int(7 * (Y + int((M + 9) / 12)) / 4) + int(275 * M / 9) + D + 1721013.5 + ut_hour / 24


def resolve_location(
    city: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    tz: Optional[float]
) -> tuple:
    if city:
        result = get_lnglat_by_city(city)
        if "error" in result:
            return None, None, None, result["error"]
        lat = result["lat"]
        lon = result["lon"]
        if tz is None:
            tz = result.get("timezone_offset", 8.0)
    if lat is None or lon is None:
        return None, None, None, "必须提供 city 或同时提供 lat+lon"
    if tz is None:
        tz = 8.0
    return lat, lon, tz, None


def calc_planet_positions(jd_ut: float, house_cusps: list) -> Dict[str, Any]:
    results = {}
    for pname, pconst in PLANETS:
        if pname == "Fortune":
            continue
        try:
            if pname == "North Node":
                ecl = real_swe.calc_ut(jd_ut, real_swe.TRUE_NODE, real_swe.FLG_SPEED)
            elif pname == "Chiron":
                ecl = real_swe.calc_ut(jd_ut, real_swe.CHIRON, real_swe.FLG_SPEED)
            elif pname == "Juno":
                ecl = real_swe.calc_ut(jd_ut, real_swe.JUNO, real_swe.FLG_SPEED)
            else:
                ecl = real_swe.calc_ut(jd_ut, pconst, real_swe.FLG_SPEED)
            if isinstance(ecl, tuple) and isinstance(ecl[0], (list, tuple)) and len(ecl[0]) >= 4:
                lon_ecl = float(ecl[0][0]) % 360.0
                lat_ecl = float(ecl[0][1])
                speed = float(ecl[0][3])
                is_retro = speed < 0 and pname not in ["Sun", "Moon", "North Node", "South Node", "Juno", "Chiron"]
                zodiac = longitude_to_zodiac(lon_ecl)
                house_number = determine_planet_house(lon_ecl, house_cusps)
                results[pname] = {
                    "name": pname,
                    "name_cn": PLANET_NAMES_CN.get(pname, pname),
                    "ecliptic_longitude": round(lon_ecl, 4),
                    "ecliptic_latitude": round(lat_ecl, 4),
                    "zodiac": zodiac,
                    "house_number": house_number,
                    "house_meaning": HOUSE_MEANINGS.get(house_number, ""),
                    "is_retrograde": is_retro,
                    "speed": round(speed, 6),
                }
        except Exception as e:
            logger.warning(f"计算行星 {pname} 位置时出错: {e}")
            continue

    if "North Node" in results:
        nn = results["North Node"]
        sn_lon = (nn["ecliptic_longitude"] + 180.0) % 360.0
        results["South Node"] = {
            "name": "South Node",
            "name_cn": "南交点",
            "ecliptic_longitude": round(sn_lon, 4),
            "ecliptic_latitude": 0.0,
            "zodiac": longitude_to_zodiac(sn_lon),
            "house_number": determine_planet_house(sn_lon, house_cusps),
            "house_meaning": HOUSE_MEANINGS.get(determine_planet_house(sn_lon, house_cusps), ""),
            "is_retrograde": False,
            "speed": nn["speed"],
        }

    sun_lon = results.get("Sun", {}).get("ecliptic_longitude", 0)
    moon_lon = results.get("Moon", {}).get("ecliptic_longitude", 0)
    asc_lon = house_cusps[0]
    is_day_chart = (asc_lon - sun_lon) % 360 < 180
    if is_day_chart:
        fortune_lon = (asc_lon + moon_lon - sun_lon) % 360.0
    else:
        fortune_lon = (asc_lon + sun_lon - moon_lon) % 360.0
    results["Fortune"] = {
        "name": "Fortune",
        "name_cn": "福点",
        "ecliptic_longitude": round(fortune_lon, 4),
        "ecliptic_latitude": 0.0,
        "zodiac": longitude_to_zodiac(fortune_lon),
        "house_number": determine_planet_house(fortune_lon, house_cusps),
        "house_meaning": HOUSE_MEANINGS.get(determine_planet_house(fortune_lon, house_cusps), ""),
        "is_retrograde": False,
        "speed": 0.0,
    }

    return results


def _aspect_motion(
    lon1: float,
    lon2: float,
    aspect_angle: float,
    speed1: Optional[float],
    speed2: Optional[float],
) -> str:
    """Classify a natal aspect using the instantaneous ecliptic speeds.

    This is deliberately conservative: angles and points without a speed are
    returned as ``unknown`` rather than being labelled applying/separating by
    guesswork.  A short forward step is sufficient for a natal snapshot and
    avoids pretending that a linear ephemeris is an exact future solver.
    """
    if speed1 is None or speed2 is None:
        return "unknown"

    def orb(a: float, b: float) -> float:
        separation = abs((a - b) % 360.0)
        separation = min(separation, 360.0 - separation)
        return abs(separation - aspect_angle)

    current = orb(lon1, lon2)
    step = 0.25
    next_orb = orb(lon1 + float(speed1) * step, lon2 + float(speed2) * step)
    if next_orb < current - 1e-6:
        return "applying"
    if next_orb > current + 1e-6:
        return "separating"
    return "stationary"


def calc_aspects(
    planet_lons: Dict[str, float],
    orb_override: Optional[Dict[str, float]] = None,
    speeds: Optional[Dict[str, float]] = None,
) -> list:
    aspects = []
    planet_names = list(planet_lons.keys())
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]
            lon1 = planet_lons[p1]
            lon2 = planet_lons[p2]
            angle_diff = abs(lon1 - lon2) % 360
            angle_diff = min(angle_diff, 360 - angle_diff)
            for asp_name, asp_def in ASPECT_DEFS.items():
                asp_angle = asp_def["angle"]
                asp_orb = (orb_override or {}).get(asp_name, asp_def["orb"])
                if abs(angle_diff - asp_angle) <= asp_orb:
                    aspects.append({
                        "planet1": p1,
                        "planet1_cn": PLANET_NAMES_CN.get(p1, p1),
                        "planet2": p2,
                        "planet2_cn": PLANET_NAMES_CN.get(p2, p2),
                        "type": asp_name,
                        "type_cn": ASPECT_NAMES_CN.get(asp_name, asp_name),
                        "angle": asp_angle,
                        "orb": round(abs(angle_diff - asp_angle), 2),
                        "motion": _aspect_motion(
                            lon1,
                            lon2,
                            asp_angle,
                            (speeds or {}).get(p1),
                            (speeds or {}).get(p2),
                        ),
                    })
                    break
    return aspects


def calc_natal_chart(dt: datetime, lat: float, lon: float, tz: float = 8.0, house_system: str = "P") -> Dict[str, Any]:
    jd_ut = datetime_to_jd(dt, tz)
    house_data = calculate_house_cusps(jd_ut, lat, lon, house_system)
    house_cusps = house_data["house_cusps"]

    planets = calc_planet_positions(jd_ut, house_cusps)

    planet_lons = {}
    for pname, pdata in planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    aspects = calc_aspects(
        planet_lons,
        speeds={name: data.get("speed") for name, data in planets.items()},
    )

    sun_lon = planets.get("Sun", {}).get("ecliptic_longitude", 0)
    asc_lon = house_data["asc"]
    is_day_chart = (asc_lon - sun_lon) % 360 < 180

    return {
        "planets": planets,
        "houses": {
            "house_cusps": house_cusps,
            "asc": house_data["asc"],
            "mc": house_data["mc"],
            "des": house_data["des"],
            "ic": house_data["ic"],
            "house_system": house_data["house_system"],
        },
        "aspects": aspects,
        "is_day_chart": is_day_chart,
    }
