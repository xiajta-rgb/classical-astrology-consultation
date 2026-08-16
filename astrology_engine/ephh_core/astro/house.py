import logging
import swisseph as real_swe
from typing import Dict, Any
logger = logging.getLogger(__name__)

# 宫位制代码映射
HOUSE_SYSTEM_MAP = {
    "P": b"P",  # Placidus 普拉西度宫位制
    "E": b"E",  # Equal 等分宫位制
    "W": b"W",  # Whole Sign 整宫制
    "K": b"K",  # Koch 科赫宫位制
    "R": b"R",  # Regiomontanus 雷吉蒙塔努斯宫位制
    "C": b"C",  # Campanus 坎帕纳斯宫位制
}


def calculate_house_cusps(jd_ut: float, lat: float, lon: float, house_system: str = "P") -> Dict[str, Any]:
    try:
        requested = str(house_system or "P").upper()
        if requested not in HOUSE_SYSTEM_MAP:
            raise ValueError(
                f"unsupported house system {house_system!r}; choose from {sorted(HOUSE_SYSTEM_MAP)}"
            )
        house_code = HOUSE_SYSTEM_MAP[requested]
        
        houses_result = real_swe.houses(jd_ut, lat, lon, house_code)
        
        house_cusps = [round(cusp % 360, 4) for cusp in houses_result[0]]
        ascmc = houses_result[1]
        
        asc_ecl_lon = round(ascmc[0] % 360, 4)
        mc_ecl_lon = round(ascmc[1] % 360, 4)
        des_ecl_lon = round(ascmc[2] % 360, 4)
        ic_ecl_lon = round(ascmc[3] % 360, 4)
        
        # Swiss Ephemeris returns the Ascendant as the first cusp for most
        # quadrant systems.  Whole Sign is different: its first cusp is the
        # beginning of the Ascendant's sign, not the degree of the Ascendant.
        if requested == "W":
            first_cusp = (int(asc_ecl_lon // 30.0) * 30.0) % 360.0
            house_cusps = [round((first_cusp + i * 30.0) % 360.0, 4) for i in range(12)]
        else:
            house_cusps[0] = asc_ecl_lon
        
        # 限制为12个
        if len(house_cusps) > 12:
            house_cusps = house_cusps[:12]
        
        house_system_name = {"P": "Placidus", "E": "Equal", "W": "Whole Sign", "K": "Koch", "R": "Regiomontanus", "C": "Campanus"}[requested]
        
        logger.info(f"✅ {house_system_name}宫位计算结果：ASC={asc_ecl_lon}°, MC={mc_ecl_lon}°")
        return {
            "house_cusps": house_cusps,
            "asc": asc_ecl_lon,
            "mc": mc_ecl_lon,
            "des": des_ecl_lon,
            "ic": ic_ecl_lon,
            "house_system": house_system_name
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"宫位计算失败：{str(e)}")

def determine_planet_house(planet_lon: float, house_cusps: list) -> int:
    for i in range(12):
        current_cusp = house_cusps[i]
        next_cusp = house_cusps[(i+1)%12]
        if current_cusp is None or next_cusp is None:
            continue
        if current_cusp < next_cusp:
            if current_cusp <= planet_lon < next_cusp:
                return i + 1
        else:
            if planet_lon >= current_cusp or planet_lon < next_cusp:
                return i + 1
    return 1
