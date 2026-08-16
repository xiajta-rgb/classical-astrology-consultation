import logging
import swisseph as real_swe
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .constants import (
    PLANETS, SIGN_RULERS_TRADITIONAL, SIGN_RULERS_MODERN,
    EXALTATION_RULERS, DETRIMENT_RULERS_TRADITIONAL, FALL_RULERS,
    FIRDARIA_ORDER_DAY, FIRDARIA_ORDER_NIGHT, ZODIAC_NAMES,
    HOUSE_MEANINGS, ASPECT_DEFS, TERMS_EGYPTIAN,
    TRIPLICITY_RULERS_DOROTHEAN, SIGN_TRIPLICITY, FACES_CHALDEAN,
)
from .house import calculate_house_cusps, determine_planet_house
from .utils import datetime_to_jd, calc_planet_positions, calc_natal_chart
from ..core.utils import longitude_to_zodiac

logger = logging.getLogger(__name__)


def _zodiac_name(idx: int) -> str:
    return ZODIAC_NAMES[idx] if 0 <= idx < len(ZODIAC_NAMES) else f"星座{idx}"


def calculate_essential_dignities(
    birth_dt: datetime, lat: float, lon: float,
    tz: float = 8.0, house_system: str = "P",
    use_modern_rulers: bool = False
) -> Dict[str, Any]:
    jd_ut = datetime_to_jd(birth_dt, tz)
    house_data = calculate_house_cusps(jd_ut, lat, lon, house_system)
    house_cusps = house_data["house_cusps"]

    rulers = SIGN_RULERS_MODERN if use_modern_rulers else SIGN_RULERS_TRADITIONAL

    natal_chart = calc_natal_chart(birth_dt, lat, lon, tz, house_system)
    is_day_chart = natal_chart["is_day_chart"]

    dignities = {}
    angular_houses = {1, 4, 7, 10}
    succedent_houses = {2, 5, 8, 11}

    def term_ruler(sign_index: int, degree: float) -> Optional[str]:
        for end_degree, ruler in TERMS_EGYPTIAN[sign_index]:
            if degree < end_degree:
                return ruler
        return None

    def face_ruler(sign_index: int, degree: float) -> Optional[str]:
        for end_degree, ruler in FACES_CHALDEAN[sign_index]:
            if degree < end_degree:
                return ruler
        return None

    def visibility(sun_lon: float, planet_lon: float) -> tuple[float, str]:
        separation = abs((planet_lon - sun_lon) % 360.0)
        separation = min(separation, 360.0 - separation)
        if separation <= (17.0 / 60.0):
            state = "cazimi"
        elif separation <= 8.5:
            state = "combust"
        elif separation <= 17.0:
            state = "under_beams"
        else:
            state = "visible_by_sun_distance"
        return round(separation, 4), state

    sun_lon = float(natal_chart["planets"].get("Sun", {}).get("ecliptic_longitude", 0.0))
    for pname, pconst in PLANETS:
        if pname in ("Fortune", "South Node"):
            continue
        try:
            if pname == "North Node":
                ecl = real_swe.calc_ut(jd_ut, real_swe.TRUE_NODE)
            elif pname == "Chiron":
                ecl = real_swe.calc_ut(jd_ut, real_swe.CHIRON)
            else:
                ecl = real_swe.calc_ut(jd_ut, pconst)
            if not (isinstance(ecl, tuple) and isinstance(ecl[0], (list, tuple)) and len(ecl[0]) >= 1):
                continue
            planet_lon = float(ecl[0][0]) % 360.0
        except Exception:
            continue

        sign_index = int(planet_lon // 30)
        sign_name = _zodiac_name(sign_index)

        degree_in_sign = planet_lon % 30.0
        status = "peregrine"
        status_score = -5

        if rulers.get(sign_index) == pname:
            status = "domicile"
            status_score = 5
        elif DETRIMENT_RULERS_TRADITIONAL.get(sign_index) == pname:
            status = "detriment"
            status_score = -5
        elif EXALTATION_RULERS.get(sign_index) == pname:
            status = "exaltation"
            status_score = 4
        elif FALL_RULERS.get(sign_index) == pname:
            status = "fall"
            status_score = -4

        triplicity = SIGN_TRIPLICITY[sign_index]
        triplicity_rulers = TRIPLICITY_RULERS_DOROTHEAN[triplicity]
        sect_triplicity_ruler = triplicity_rulers[0 if is_day_chart else 1]
        triplicity_score = 3 if pname == sect_triplicity_ruler else (1 if pname == triplicity_rulers[2] else 0)
        term = term_ruler(sign_index, degree_in_sign)
        face = face_ruler(sign_index, degree_in_sign)
        term_score = 2 if pname == term else 0
        face_score = 1 if pname == face else 0
        house_number = natal_chart["planets"].get(pname, {}).get("house_number")
        if house_number in angular_houses:
            accidental_condition = "angular"
        elif house_number in succedent_houses:
            accidental_condition = "succedent"
        else:
            accidental_condition = "cadent"
        speed = natal_chart["planets"].get(pname, {}).get("speed")
        retrograde = bool(natal_chart["planets"].get(pname, {}).get("is_retrograde", False))
        sun_distance, visibility_state = visibility(sun_lon, planet_lon)

        dignities[pname] = {
            "planet": pname,
            "sign": sign_name,
            "sign_index": sign_index,
            "longitude": round(planet_lon, 4),
            "status": status,
            "status_cn": _dignity_status_cn(status),
            "score": status_score + triplicity_score + term_score + face_score,
            "essential_score": {
                "domicile_or_detriment_or_exaltation_or_fall": status_score,
                "triplicity": triplicity_score,
                "term": term_score,
                "face": face_score,
            },
            "triplicity": triplicity,
            "triplicity_ruler_day": triplicity_rulers[0],
            "triplicity_ruler_night": triplicity_rulers[1],
            "triplicity_ruler_participating": triplicity_rulers[2],
            "sect_triplicity_ruler": sect_triplicity_ruler,
            "term_system": "egyptian",
            "term_ruler": term,
            "face_ruler": face,
            "house": house_number,
            "accidental_condition": accidental_condition,
            "speed": speed,
            "retrograde": retrograde,
            "sun_distance": sun_distance,
            "visibility_state": visibility_state,
        }

    strong = [d for d in dignities.values() if d["score"] > 0]
    weak = [d for d in dignities.values() if d["score"] < 0]
    peregrine = [d for d in dignities.values() if d["status"] == "peregrine" and d["essential_score"]["triplicity"] == 0 and d["essential_score"]["term"] == 0 and d["essential_score"]["face"] == 0]

    return {
        "chart_type": "essential_dignities",
        "birth_datetime": birth_dt.isoformat(),
        "is_day_chart": is_day_chart,
        "use_modern_rulers": use_modern_rulers,
        "dignities": dignities,
        "summary": {
            "strong_count": len(strong),
            "weak_count": len(weak),
            "peregrine_count": len(peregrine),
            "total_score": sum(d["score"] for d in dignities.values()),
            "strong_planets": [d["planet"] for d in strong],
            "weak_planets": [d["planet"] for d in weak],
        },
        "method": {
            "term_system": "egyptian",
            "triplicity_system": "dorothean",
            "accidental_condition_scope": "house_angularity_speed_retrograde_sun_distance",
        },
    }


def calculate_firdaria(
    birth_dt: datetime, lat: float, lon: float,
    target_dt: Optional[datetime] = None,
    tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    jd_ut = datetime_to_jd(birth_dt, tz)

    natal_chart = calc_natal_chart(birth_dt, lat, lon, tz, house_system)
    is_day_chart = natal_chart["is_day_chart"]

    order = FIRDARIA_ORDER_DAY if is_day_chart else FIRDARIA_ORDER_NIGHT

    firdaria_periods = []
    current_age = 0.0
    for i, (planet, years) in enumerate(order):
        start_age = current_age
        end_age = current_age + years
        sub_periods = []
        for j, (sub_planet, sub_years) in enumerate(order):
            sub_start = start_age + sum(o[1] for o in order[:j]) * years / sum(o[1] for o in order)
            sub_end = start_age + sum(o[1] for o in order[:j + 1]) * years / sum(o[1] for o in order)
            sub_periods.append({
                "planet": sub_planet,
                "start_age": round(sub_start, 2),
                "end_age": round(sub_end, 2),
            })

        firdaria_periods.append({
            "planet": planet,
            "years": years,
            "start_age": round(start_age, 2),
            "end_age": round(end_age, 2),
            "sub_periods": sub_periods,
        })
        current_age = end_age

    # Select the active period against the requested target date. Leaving this
    # at age 0 would incorrectly report the first period for every query.
    if target_dt is None:
        target_dt = birth_dt
    current_age_val = max(0.0, (target_dt - birth_dt).total_seconds() / (365.25 * 86400.0))
    current_period = None
    current_sub = None
    for period in firdaria_periods:
        if period["start_age"] <= current_age_val < period["end_age"]:
            current_period = period
            for sub in period["sub_periods"]:
                if sub["start_age"] <= current_age_val < sub["end_age"]:
                    current_sub = sub
                    break
            break

    return {
        "chart_type": "firdaria",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "target_age": round(current_age_val, 4),
        "is_day_chart": is_day_chart,
        "order_used": "day" if is_day_chart else "night",
        "periods": firdaria_periods,
        "current_period": current_period,
        "current_sub_period": current_sub,
    }


def calculate_profection(
    birth_dt: datetime, lat: float, lon: float,
    target_dt: Optional[datetime] = None,
    tz: float = 8.0, house_system: str = "P"
) -> Dict[str, Any]:
    jd_ut = datetime_to_jd(birth_dt, tz)
    house_data = calculate_house_cusps(jd_ut, lat, lon, house_system)
    house_cusps = house_data["house_cusps"]

    if target_dt is None:
        target_dt = datetime.now()

    age = max(0.0, (target_dt - birth_dt).total_seconds() / (365.25 * 86400.0))
    age_years = int(age)
    profection_house = (age_years % 12) + 1
    natal_asc_sign = int(house_data["asc"] // 30.0) % 12
    # Annual profection advances the natal Ascendant sign, not a raw cusp
    # index. Keep a sign-shifted Asc point for visualization and expose the
    # actual Placidus cusps separately.
    profection_sign = (natal_asc_sign + age_years) % 12
    profected_asc = (house_data["asc"] + age_years * 30.0) % 360.0

    natal_chart = calc_natal_chart(birth_dt, lat, lon, tz, house_system)
    is_day_chart = natal_chart["is_day_chart"]

    year_ruler = SIGN_RULERS_TRADITIONAL.get(profection_sign, "Unknown")

    ruler_data = None
    for pname, pdata in natal_chart["planets"].items():
        if pname == year_ruler:
            ruler_data = {
                "planet": pname,
                "longitude": pdata["ecliptic_longitude"],
                "zodiac": pdata.get("zodiac", ""),
                "house": pdata.get("house_number", 0),
            }
            break

    return {
        "chart_type": "profection",
        "birth_datetime": birth_dt.isoformat(),
        "target_datetime": target_dt.isoformat(),
        "age": round(age, 2),
        "profection_year": age_years,
        "profection_house": profection_house,
        "natal_ascendant": round(house_data["asc"], 4),
        "natal_ascendant_sign": natal_asc_sign,
        "profection_sign": profection_sign,
        "profection_sign_cn": _zodiac_name(profection_sign),
        "profected_ascendant": round(profected_asc, 4),
        "year_ruler": year_ruler,
        "year_ruler_data": ruler_data,
        "is_day_chart": is_day_chart,
        "house_cusps": house_cusps,
    }


def calculate_mutual_reception(
    birth_dt: datetime, lat: float, lon: float,
    tz: float = 8.0, house_system: str = "P",
    use_modern_rulers: bool = False
) -> Dict[str, Any]:
    jd_ut = datetime_to_jd(birth_dt, tz)

    rulers = SIGN_RULERS_MODERN if use_modern_rulers else SIGN_RULERS_TRADITIONAL

    planet_signs = {}
    for pname, pconst in PLANETS:
        if pname in ("Fortune", "South Node"):
            continue
        try:
            if pname == "North Node":
                ecl = real_swe.calc_ut(jd_ut, real_swe.TRUE_NODE)
            elif pname == "Chiron":
                ecl = real_swe.calc_ut(jd_ut, real_swe.CHIRON)
            else:
                ecl = real_swe.calc_ut(jd_ut, pconst)
            if not (isinstance(ecl, tuple) and isinstance(ecl[0], (list, tuple)) and len(ecl[0]) >= 1):
                continue
            planet_lon = float(ecl[0][0]) % 360.0
            sign_index = int(planet_lon // 30)
            planet_signs[pname] = sign_index
        except Exception:
            continue

    receptions = []
    planet_names = list(planet_signs.keys())

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]
            sign1 = planet_signs[p1]
            sign2 = planet_signs[p2]

            ruler1 = rulers.get(sign1)
            ruler2 = rulers.get(sign2)

            if ruler1 == p2 and ruler2 == p1:
                receptions.append({
                    "type": "mutual_reception_by_domicile",
                    "type_cn": "庙旺互容",
                    "planet1": p1,
                    "planet1_sign": _zodiac_name(sign1),
                    "planet2": p2,
                    "planet2_sign": _zodiac_name(sign2),
                    "description": f"{p1}在{_zodiac_name(sign1)}与{p2}在{_zodiac_name(sign2)}形成互容",
                })
            else:
                exalt1 = EXALTATION_RULERS.get(sign1)
                exalt2 = EXALTATION_RULERS.get(sign2)
                if (ruler1 == p2 and exalt2 == p1) or (exalt1 == p2 and ruler2 == p1):
                    receptions.append({
                        "type": "mutual_reception_mixed",
                        "type_cn": "混合互容",
                        "planet1": p1,
                        "planet1_sign": _zodiac_name(sign1),
                        "planet2": p2,
                        "planet2_sign": _zodiac_name(sign2),
                        "description": f"{p1}在{_zodiac_name(sign1)}与{p2}在{_zodiac_name(sign2)}形成混合互容",
                    })
                elif exalt1 == p2 and exalt2 == p1:
                    receptions.append({
                        "type": "mutual_reception_by_exaltation",
                        "type_cn": "旺相互容",
                        "planet1": p1,
                        "planet1_sign": _zodiac_name(sign1),
                        "planet2": p2,
                        "planet2_sign": _zodiac_name(sign2),
                        "description": f"{p1}在{_zodiac_name(sign1)}与{p2}在{_zodiac_name(sign2)}形成旺相互容",
                    })

    return {
        "chart_type": "mutual_reception",
        "birth_datetime": birth_dt.isoformat(),
        "use_modern_rulers": use_modern_rulers,
        "receptions": receptions,
        "reception_count": len(receptions),
        "has_reception": len(receptions) > 0,
    }


def _dignity_status_cn(status: str) -> str:
    mapping = {
        "domicile": "入庙",
        "detriment": "失势",
        "exaltation": "旺相",
        "fall": "落陷",
        "peregrine": "游走",
    }
    return mapping.get(status, status)
