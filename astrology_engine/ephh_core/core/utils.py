import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional
from .cache import cached, LONG_TTL
from datetime import datetime
from .config import ADDRESS_API_CONFIG, PRESET_CITIES

logger = logging.getLogger(__name__)

def log_audit(action: str, username: str, detail: str = "", extra: Optional[Dict[str, Any]] = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[AUDIT] {timestamp} | user={username} | action={action} | detail={detail}"
    if extra:
        log_entry += f" | extra={json.dumps(extra, ensure_ascii=False, default=str)}"
    logger.info(log_entry)

def normalize_timezone(timezone_str: str) -> str:
    if not timezone_str:
        return "Asia/Shanghai"
    tz = str(timezone_str).strip()
    if '/' in tz:
        return tz
    try:
        if tz.upper().startswith('UTC'):
            offset_str = tz.upper().replace('UTC', '').replace('+', '')
            if not offset_str:
                offset = 0.0
            else:
                offset = float(offset_str)
        else:
            offset = float(tz)
        if offset == 8.0:
            return "Asia/Shanghai"
        if offset == 9.0:
            return "Asia/Tokyo"
        if offset == 0.0:
            return "Europe/London"
        if offset == -5.0:
            return "America/New_York"
        if offset == -8.0:
            return "America/Los_Angeles"
        for iana, off in TIMEZONE_OFFSET_MAP.items():
            if off == offset:
                return iana
        return f"UTC{'+' if offset >= 0 else ''}{offset:g}"
    except (ValueError, TypeError):
        return "Asia/Shanghai"

ZODIAC_NAMES = ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]

def get_data_cities_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, "data", "cities")

def get_provinces_list() -> List[str]:
    index_path = os.path.join(get_data_cities_path(), "index.json")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return []

def get_cities_by_province(province: str) -> Dict[str, Any]:
    province_file = os.path.join(get_data_cities_path(), f"{province}.json")
    try:
        with open(province_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {}

TIMEZONE_OFFSET_MAP = {
    "Asia/Shanghai": 8.0,
    "Asia/Taipei": 8.0,
    "Asia/Tokyo": 9.0,
    "Asia/Seoul": 9.0,
    "Asia/Singapore": 8.0,
    "Asia/Bangkok": 7.0,
    "Asia/Hong_Kong": 8.0,
    "Asia/Macau": 8.0,
    "Asia/Chongqing": 8.0,
    "Asia/Harbin": 8.0,
    "Asia/Urumqi": 6.0,
    "Asia/Kashgar": 6.0,
    "Europe/London": 0.0,
    "Europe/Paris": 1.0,
    "Europe/Berlin": 1.0,
    "Europe/Rome": 1.0,
    "Europe/Madrid": 1.0,
    "Europe/Amsterdam": 1.0,
    "Europe/Brussels": 1.0,
    "Europe/Vienna": 1.0,
    "Europe/Zurich": 1.0,
    "Europe/Stockholm": 1.0,
    "Europe/Oslo": 1.0,
    "Europe/Copenhagen": 1.0,
    "Europe/Helsinki": 2.0,
    "Europe/Moscow": 3.0,
    "Europe/Istanbul": 3.0,
    "Europe/Athens": 2.0,
    "America/New_York": -5.0,
    "America/Los_Angeles": -8.0,
    "America/Chicago": -6.0,
    "America/Denver": -7.0,
    "America/Phoenix": -7.0,
    "America/Toronto": -5.0,
    "America/Vancouver": -8.0,
    "America/Mexico_City": -6.0,
    "America/Sao_Paulo": -3.0,
    "America/Buenos_Aires": -3.0,
    "America/Lima": -5.0,
    "Australia/Sydney": 10.0,
    "Australia/Melbourne": 10.0,
    "Australia/Brisbane": 10.0,
    "Australia/Perth": 8.0,
    "Australia/Adelaide": 9.5,
    "Australia/Darwin": 9.5,
    "Pacific/Auckland": 12.0,
    "Asia/Dubai": 4.0,
    "Asia/Riyadh": 3.0,
    "Asia/Tehran": 3.5,
    "Asia/Karachi": 5.0,
    "Asia/Mumbai": 5.5,
    "Asia/Dhaka": 6.0,
    "Asia/Jakarta": 7.0,
    "Asia/Manila": 8.0,
    "Asia/Ho_Chi_Minh": 7.0,
    "Africa/Cairo": 2.0,
    "Africa/Johannesburg": 2.0,
    "Africa/Lagos": 1.0,
    "Africa/Nairobi": 3.0
}

def convert_timezone_to_offset(timezone_str: str) -> float:
    return TIMEZONE_OFFSET_MAP.get(timezone_str, 8.0)

def get_lnglat_by_city(city: str) -> Dict[str, Any]:
    try:
        city_stripped = city.strip().replace(' ', '')

        provinces = get_provinces_list()
        for province in provinces:
            cities_data = get_cities_by_province(province)
            for prov_name, cities_dict in cities_data.items():
                prov_stripped = prov_name.replace(' ', '')
                for city_name, district_info in cities_dict.items():
                    city_stripped_inner = city_name.replace(' ', '')
                    if city_stripped == f"{prov_stripped}{city_stripped_inner}":
                        if isinstance(district_info, dict):
                            if "lat" in district_info and "lon" in district_info:
                                return {
                                    "lat": float(district_info["lat"]),
                                    "lon": float(district_info["lon"]),
                                    "timezone": district_info.get("timezone", "Asia/Shanghai")
                                }
                            for district_name, location in district_info.items():
                                if isinstance(location, dict) and "lat" in location and "lon" in location:
                                    return {
                                        "lat": float(location["lat"]),
                                        "lon": float(location["lon"]),
                                        "timezone": location.get("timezone", "Asia/Shanghai")
                                    }
                    if isinstance(district_info, dict):
                        for district_name, location in district_info.items():
                            district_stripped = district_name.replace(' ', '')
                            if city_stripped == f"{prov_stripped}{city_stripped_inner}{district_stripped}":
                                if isinstance(location, dict) and "lat" in location and "lon" in location:
                                    return {
                                        "lat": float(location["lat"]),
                                        "lon": float(location["lon"]),
                                        "timezone": location.get("timezone", "Asia/Shanghai")
                                    }
                            if district_stripped == city_stripped or city_stripped == district_name:
                                if isinstance(location, dict) and "lat" in location and "lon" in location:
                                    return {
                                        "lat": float(location["lat"]),
                                        "lon": float(location["lon"]),
                                        "timezone": location.get("timezone", "Asia/Shanghai")
                                    }

                    if city_stripped == city_stripped_inner or city_stripped == city_name:
                        if isinstance(district_info, dict):
                            if "lat" in district_info and "lon" in district_info:
                                return {
                                    "lat": float(district_info["lat"]),
                                    "lon": float(district_info["lon"]),
                                    "timezone": district_info.get("timezone", "Asia/Shanghai")
                                }
                            for district_name, location in district_info.items():
                                if isinstance(location, dict) and "lat" in location and "lon" in location:
                                    return {
                                        "lat": float(location["lat"]),
                                        "lon": float(location["lon"]),
                                        "timezone": location.get("timezone", "Asia/Shanghai")
                                    }

                    if city_stripped == prov_stripped:
                        if isinstance(district_info, dict):
                            for district_name, location in district_info.items():
                                if isinstance(location, dict) and "lat" in location and "lon" in location:
                                    return {
                                        "lat": float(location["lat"]),
                                        "lon": float(location["lon"]),
                                        "timezone": location.get("timezone", "Asia/Shanghai")
                                    }

        for preset_city in PRESET_CITIES:
            if preset_city["name"].replace(' ', '') == city_stripped or preset_city["name"] == city:
                return {
                    "lat": float(preset_city["latitude"]),
                    "lon": float(preset_city["longitude"]),
                    "timezone": preset_city.get("timezone", "Asia/Shanghai")
                }

        if ADDRESS_API_CONFIG.get("enable", False):
            params = {
                "id": ADDRESS_API_CONFIG["id"],
                "key": ADDRESS_API_CONFIG["key"],
                "address": city
            }
            try:
                response = requests.post(
                    ADDRESS_API_CONFIG["url"],
                    data=params,
                    timeout=ADDRESS_API_CONFIG.get("timeout", 10),
                    verify=False
                )
                result = response.json()

                if result.get("code") == 200 and (result.get("score") or 0) >= 70:
                    return {
                        "lat": float(result["lat"]),
                        "lon": float(result["lng"]),
                        "timezone": "Asia/Shanghai"
                    }
                else:
                    error_msg = result.get("msg", "城市地址解析失败")
                    return {"error": f"地址解析失败：{error_msg}"}
            except requests.exceptions.RequestException:
                pass

        return {"error": f"城市'{city}'在数据库中未找到"}

    except Exception as e:
        return {"error": f"未知错误：{str(e)}"}

def validate_params(year: int, month: int, day: int, hour: int, minute: int, second: int, lat: Optional[float], lon: Optional[float], tz: float) -> List[str]:
    errs = []
    if year < 1900 or year > 2100:
        errs.append("year must be 1900-2100")
    if month < 1 or month > 12:
        errs.append("month must be 1-12")
    if day < 1 or day > 31:
        errs.append("day must be 1-31")
    if hour < 0 or hour > 23:
        errs.append("hour must be 0-23")
    if minute < 0 or minute > 59:
        errs.append("minute must be 0-59")
    if second < 0 or second > 59:
        errs.append("second must be 0-59")
    if lat is not None and (lat < -90 or lat > 90):
        errs.append("lat must be -90..90")
    if lon is not None and (lon < -180 or lon > 180):
        errs.append("lon must be -180..180")
    if tz < -12 or tz > 14:
        errs.append("tz seems out of range (-12..14)")
    return errs

def longitude_to_zodiac(lon_deg: float) -> Dict[str, Any]:
    lon = lon_deg % 360.0
    idx = int(lon // 30)
    name = ZODIAC_NAMES[idx]
    degree_in_zodiac = round(lon % 30, 2)
    degree = int(degree_in_zodiac)
    minute = round((degree_in_zodiac - degree) * 60)
    return {
        "index": idx,
        "name": name,
        "degree": degree_in_zodiac,
        "degree_str": f"{degree}°{minute}'",
        "full_str": f"{name} {degree}°{minute}'"
    }

def mag_to_size(mag: float, min_size: float = 3.0, max_size: float = 15.0) -> float:
    mag_min = -27.0
    mag_max = 15.0
    m = max(min(mag, mag_max), mag_min)
    frac = (mag_max - m) / (mag_max - mag_min)
    size = min_size + frac * (max_size - min_size)
    return round(size, 2)
