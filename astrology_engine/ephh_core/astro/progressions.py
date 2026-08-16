import logging
import swisseph as real_swe
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .constants import PLANETS, ASPECT_DEFS
from .house import calculate_house_cusps, determine_planet_house
from .utils import datetime_to_jd, calc_planet_positions, calc_aspects
from ..core.utils import longitude_to_zodiac

logger = logging.getLogger(__name__)


def _jd_to_datetime(jd: float) -> datetime:
    try:
        year, month, day, hour, minute, second = real_swe.jdut1_to_utc(jd)
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    except Exception:
        return datetime.now()


def calculate_secondary_progression(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    natal_jd = datetime_to_jd(birth_dt, tz)
    # 次限推进：1天 = 1年（"Day for a Year"原则）
    # 年龄(年) = 出生后天数 / 365.25
    # progressed_jd = natal_jd + 年龄(年)，即出生后 N 天对应 N 岁
    diff_days = (target_dt - birth_dt).total_seconds() / 86400.0
    age_years = diff_days / 365.25
    progressed_jd = natal_jd + age_years

    house_data = calculate_house_cusps(progressed_jd, birth_lat, birth_lon, house_system)
    house_cusps = house_data["house_cusps"]

    planets = calc_planet_positions(progressed_jd, house_cusps)

    planet_lons = {}
    for pname, pdata in planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    aspects = calc_aspects(planet_lons)

    return {
        "progression_type": "secondary",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "progressed_jd": round(progressed_jd, 6),
        "years_progressed": round(age_years, 4),
        "description": f"次限推进：出生后{age_years:.2f}天 = {age_years:.2f}年推进",
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
    }


def calculate_tertiary_progression_v1(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    natal_jd = datetime_to_jd(birth_dt, tz)
    # 三限推进：1天 = 1月（"Day for a Month"原则）
    # 年龄(月) = 出生后天数 / (365.25/12) = 出生后天数 × 12 / 365.25
    # progressed_jd = natal_jd + 年龄(月)，即出生后 N 天对应 N 月
    # 注：使用日历月(30.4375天)而非朔望月(29.53天)，与知识库定义一致：
    #   "30岁（即出生后360个月）→ 计算出生后第360天"
    diff_days = (target_dt - birth_dt).total_seconds() / 86400.0
    age_months = diff_days * 12.0 / 365.25
    progressed_jd = natal_jd + age_months

    house_data = calculate_house_cusps(progressed_jd, birth_lat, birth_lon, house_system)
    house_cusps = house_data["house_cusps"]

    planets = calc_planet_positions(progressed_jd, house_cusps)

    planet_lons = {}
    for pname, pdata in planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    aspects = calc_aspects(planet_lons)

    return {
        "progression_type": "tertiary",
        "calculation_profile": "project_local_ephh_tertiary_v1",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "progressed_jd": round(progressed_jd, 6),
        "progressed_days": round(age_months, 6),
        "months_progressed": round(age_months, 4),
        "tertiary_month_days": 365.25 / 12.0,
        "anchor_days": 0.0,
        "description": f"三限推进：出生后{age_months:.2f}天 = {age_months:.2f}月推进",
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
    }


TERTIARY_SYNODIC_MONTH_DAYS = 29.530588853
TERTIARY_SIDEREAL_MONTH_DAYS = 27.321661
TERTIARY_V2_ANCHOR_DAYS = 1.0


def calculate_tertiary_progression_v2(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    """Intermediate synodic-month profile retained for comparison.

    The previous calendar-month implementation remains available as
    ``calculate_tertiary_progression_v1`` for comparison and auditability.
    """
    natal_jd = datetime_to_jd(birth_dt, tz)
    diff_days = (target_dt - birth_dt).total_seconds() / 86400.0
    months_progressed = diff_days / TERTIARY_SYNODIC_MONTH_DAYS
    progressed_days = months_progressed + TERTIARY_V2_ANCHOR_DAYS
    progressed_jd = natal_jd + progressed_days

    house_data = calculate_house_cusps(progressed_jd, birth_lat, birth_lon, house_system)
    house_cusps = house_data["house_cusps"]
    planets = calc_planet_positions(progressed_jd, house_cusps)

    planet_lons = {pname: pdata["ecliptic_longitude"] for pname, pdata in planets.items()}
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    return {
        "progression_type": "tertiary",
        "calculation_profile": "project_local_ephh_tertiary_v2_synodic_anchor1",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "progressed_jd": round(progressed_jd, 6),
        "progressed_days": round(progressed_days, 6),
        "months_progressed": round(months_progressed, 6),
        "tertiary_month_days": TERTIARY_SYNODIC_MONTH_DAYS,
        "anchor_days": TERTIARY_V2_ANCHOR_DAYS,
        "description": (
            f"三限朔望月法：实际年龄{diff_days:.4f}日 ÷ "
            f"{TERTIARY_SYNODIC_MONTH_DAYS:.9f}日/月 + 起算锚点1日"
        ),
        "planets": planets,
        "houses": {
            "house_cusps": house_cusps,
            "asc": house_data["asc"],
            "mc": house_data["mc"],
            "des": house_data["des"],
            "ic": house_data["ic"],
            "house_system": house_data["house_system"],
        },
        "aspects": calc_aspects(planet_lons),
    }


def calculate_tertiary_progression_v3(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    """Calibrated tertiary profile: sidereal lunar month, no artificial anchor."""
    natal_jd = datetime_to_jd(birth_dt, tz)
    diff_days = (target_dt - birth_dt).total_seconds() / 86400.0
    months_progressed = diff_days / TERTIARY_SIDEREAL_MONTH_DAYS
    progressed_jd = natal_jd + months_progressed

    house_data = calculate_house_cusps(progressed_jd, birth_lat, birth_lon, house_system)
    house_cusps = house_data["house_cusps"]
    planets = calc_planet_positions(progressed_jd, house_cusps)

    planet_lons = {pname: pdata["ecliptic_longitude"] for pname, pdata in planets.items()}
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    return {
        "progression_type": "tertiary",
        "calculation_profile": "project_local_ephh_tertiary_v3_sidereal",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "progressed_jd": round(progressed_jd, 6),
        "progressed_days": round(months_progressed, 6),
        "months_progressed": round(months_progressed, 6),
        "tertiary_month_days": TERTIARY_SIDEREAL_MONTH_DAYS,
        "anchor_days": 0.0,
        "description": (
            f"三限恒星月法：实际年龄{diff_days:.4f}日 ÷ "
            f"{TERTIARY_SIDEREAL_MONTH_DAYS:.6f}日/月，无额外锚点"
        ),
        "planets": planets,
        "houses": {
            "house_cusps": house_cusps,
            "asc": house_data["asc"],
            "mc": house_data["mc"],
            "des": house_data["des"],
            "ic": house_data["ic"],
            "house_system": house_data["house_system"],
        },
        "aspects": calc_aspects(planet_lons),
    }


def calculate_tertiary_progression(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    """Default tertiary profile; kept explicit and separate from v1/v2."""
    return calculate_tertiary_progression_v3(
        birth_dt, birth_lat, birth_lon, target_dt, tz, house_system
    )


def calculate_solar_arc_progression(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    natal_jd = datetime_to_jd(birth_dt, tz)
    diff_years = (target_dt - birth_dt).total_seconds() / 86400.0 / 365.25

    natal_sun_ecl = real_swe.calc_ut(natal_jd, 0, real_swe.FLG_SPEED)
    natal_sun_lon = float(natal_sun_ecl[0][0]) % 360.0

    # Solar Arc uses the Sun's motion over the equivalent number of *days*
    # after birth (one day for one year), not the Sun's real position decades
    # later. Multiplying by 365.25 would collapse the arc near 0° every year.
    progressed_sun_jd = natal_jd + diff_years
    prog_sun_ecl = real_swe.calc_ut(progressed_sun_jd, 0, real_swe.FLG_SPEED)
    prog_sun_lon = float(prog_sun_ecl[0][0]) % 360.0

    solar_arc = (prog_sun_lon - natal_sun_lon) % 360.0

    natal_house_data = calculate_house_cusps(natal_jd, birth_lat, birth_lon, house_system)
    natal_cusps = natal_house_data["house_cusps"]

    natal_planets = calc_planet_positions(natal_jd, natal_cusps)

    arc_house_cusps = [(cusp + solar_arc) % 360.0 for cusp in natal_cusps]
    arc_asc = (natal_house_data["asc"] + solar_arc) % 360.0
    arc_mc = (natal_house_data["mc"] + solar_arc) % 360.0
    arc_des = (natal_house_data["des"] + solar_arc) % 360.0
    arc_ic = (natal_house_data["ic"] + solar_arc) % 360.0

    progressed_planets = {}
    for pname, pdata in natal_planets.items():
        prog_lon = (pdata["ecliptic_longitude"] + solar_arc) % 360.0
        prog_zodiac = longitude_to_zodiac(prog_lon)
        house_number = determine_planet_house(prog_lon, arc_house_cusps)
        progressed_planets[pname] = {
            "name": pname,
            "ecliptic_longitude": round(prog_lon, 4),
            "ecliptic_latitude": pdata.get("ecliptic_latitude", 0.0),
            "zodiac": prog_zodiac,
            "house_number": house_number,
            "is_retrograde": pdata.get("is_retrograde", False),
            "speed": pdata.get("speed", 0.0),
            "natal_longitude": pdata["ecliptic_longitude"],
            "arc_added": round(solar_arc, 4),
        }

    planet_lons = {}
    for pname, pdata in progressed_planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = arc_asc
    planet_lons["Midheaven"] = arc_mc

    aspects = calc_aspects(planet_lons)

    return {
        "progression_type": "solar_arc",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "solar_arc_degrees": round(solar_arc, 4),
        "years_progressed": round(diff_years, 2),
        "description": f"太阳弧推进：弧度{solar_arc:.2f}° = {diff_years:.1f}年推进",
        "planets": progressed_planets,
        "houses": {
            "house_cusps": [round(c, 4) for c in arc_house_cusps],
            "asc": round(arc_asc, 4),
            "mc": round(arc_mc, 4),
            "des": round(arc_des, 4),
            "ic": round(arc_ic, 4),
            "house_system": natal_house_data["house_system"],
        },
        "aspects": aspects,
    }


def calculate_solar_return(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_year: int, tz: float = 8.0, house_system: str = "P",
    use_birth_location: bool = True,
    return_lat: Optional[float] = None,
    return_lon: Optional[float] = None,
) -> Dict[str, Any]:
    natal_jd = datetime_to_jd(birth_dt, tz)

    natal_sun_ecl = real_swe.calc_ut(natal_jd, 0)
    natal_sun_lon = float(natal_sun_ecl[0][0]) % 360.0

    # Select the return occurring in the requested calendar year. A broad
    # two-year window can otherwise return the prior year's anniversary first.
    search_start = datetime(target_year, 1, 1)
    search_end = datetime(target_year + 1, 1, 1)
    jd_start = datetime_to_jd(search_start, tz)
    jd_end = datetime_to_jd(search_end, tz)

    sr_jd = _find_sun_return_time(jd_start, jd_end, natal_sun_lon)

    if sr_jd is None:
        return {
            "status": "error",
            "error": f"无法找到{target_year}年的太阳返照时刻",
        }

    if use_birth_location:
        sr_lat, sr_lon = birth_lat, birth_lon
    else:
        if return_lat is None or return_lon is None:
            raise ValueError("return_lat and return_lon are required when use_birth_location=False")
        sr_lat, sr_lon = float(return_lat), float(return_lon)

    house_data = calculate_house_cusps(sr_jd, sr_lat, sr_lon, house_system)
    house_cusps = house_data["house_cusps"]

    planets = calc_planet_positions(sr_jd, house_cusps)

    planet_lons = {}
    for pname, pdata in planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    aspects = calc_aspects(planet_lons)

    sr_dt = _jd_to_datetime(sr_jd)

    return {
        "progression_type": "solar_return",
        "birth_datetime": birth_dt.isoformat(),
        "target_year": target_year,
        "return_location": {
            "latitude": round(sr_lat, 6),
            "longitude": round(sr_lon, 6),
            "used_birth_location": bool(use_birth_location),
        },
        "solar_return_datetime": sr_dt.isoformat(),
        "solar_return_jd": round(sr_jd, 6),
        "description": f"太阳返照：{target_year}年太阳回到本命位置",
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
    }


def calculate_lunar_return(
    birth_dt: datetime, birth_lat: float, birth_lon: float,
    target_dt: datetime, tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    natal_jd = datetime_to_jd(birth_dt, tz)

    natal_moon_ecl = real_swe.calc_ut(natal_jd, 1)
    natal_moon_lon = float(natal_moon_ecl[0][0]) % 360.0

    search_start_jd = datetime_to_jd(target_dt - timedelta(days=35), tz)
    search_end_jd = datetime_to_jd(target_dt + timedelta(days=35), tz)

    lr_jd = _find_moon_return_time(search_start_jd, search_end_jd, natal_moon_lon)

    if lr_jd is None:
        return {
            "status": "error",
            "error": "无法找到目标日期附近的月亮返照时刻",
        }

    house_data = calculate_house_cusps(lr_jd, birth_lat, birth_lon, house_system)
    house_cusps = house_data["house_cusps"]

    planets = calc_planet_positions(lr_jd, house_cusps)

    planet_lons = {}
    for pname, pdata in planets.items():
        planet_lons[pname] = pdata["ecliptic_longitude"]
    planet_lons["Ascendant"] = house_data["asc"]
    planet_lons["Midheaven"] = house_data["mc"]

    aspects = calc_aspects(planet_lons)

    lr_dt = _jd_to_datetime(lr_jd)

    return {
        "progression_type": "lunar_return",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "lunar_return_datetime": lr_dt.isoformat(),
        "lunar_return_jd": round(lr_jd, 6),
        "description": "月亮返照：月亮回到本命位置",
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
    }


def _find_sun_return_time(jd_start: float, jd_end: float, target_lon: float, precision: float = 1e-6) -> Optional[float]:
    step = 1.0
    jd = jd_start
    while jd < jd_end:
        sun_ecl = real_swe.calc_ut(jd, 0)
        sun_lon = float(sun_ecl[0][0]) % 360.0

        next_jd = jd + step
        if next_jd > jd_end:
            break
        next_sun_ecl = real_swe.calc_ut(next_jd, 0)
        next_sun_lon = float(next_sun_ecl[0][0]) % 360.0

        crossed = False
        if sun_lon < next_sun_lon:
            if sun_lon < target_lon <= next_sun_lon:
                crossed = True
        else:
            if target_lon > sun_lon or target_lon <= next_sun_lon:
                crossed = True

        if crossed:
            lo, hi = jd, next_jd
            while (hi - lo) > precision:
                mid = (lo + hi) / 2
                mid_ecl = real_swe.calc_ut(mid, 0)
                mid_lon = float(mid_ecl[0][0]) % 360.0
                if sun_lon < next_sun_lon:
                    if mid_lon < target_lon:
                        lo = mid
                    else:
                        hi = mid
                else:
                    if mid_lon < target_lon or mid_lon >= sun_lon:
                        lo = mid
                    else:
                        hi = mid
            return (lo + hi) / 2

        jd = next_jd
    return None


def _find_moon_return_time(jd_start: float, jd_end: float, target_lon: float, precision: float = 1e-6) -> Optional[float]:
    step = 1.0
    jd = jd_start
    while jd < jd_end:
        moon_ecl = real_swe.calc_ut(jd, 1)
        moon_lon = float(moon_ecl[0][0]) % 360.0

        next_jd = jd + step
        if next_jd > jd_end:
            break
        next_moon_ecl = real_swe.calc_ut(next_jd, 1)
        next_moon_lon = float(next_moon_ecl[0][0]) % 360.0

        crossed = False
        if moon_lon < next_moon_lon:
            if moon_lon < target_lon <= next_moon_lon:
                crossed = True
        else:
            if target_lon > moon_lon or target_lon <= next_moon_lon:
                crossed = True

        if crossed:
            lo, hi = jd, next_jd
            while (hi - lo) > precision:
                mid = (lo + hi) / 2
                mid_ecl = real_swe.calc_ut(mid, 1)
                mid_lon = float(mid_ecl[0][0]) % 360.0
                if moon_lon < next_moon_lon:
                    if mid_lon < target_lon:
                        lo = mid
                    else:
                        hi = mid
                else:
                    if mid_lon < target_lon or mid_lon >= moon_lon:
                        lo = mid
                    else:
                        hi = mid
            return (lo + hi) / 2

        jd = next_jd
    return None
