import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_TYPE = "sqlite"

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "astro_app.db")

API_KEY_CONFIG = {
    "enabled": True,
    "keys": [
        os.getenv("API_ACCESS_KEY", "your_api_key_here"),
    ],
    "header_name": "X-API-Key",
    "query_param": "api_key"
}

ADDRESS_API_CONFIG = {
    "enable": False,
    "url": "https://cn.apihz.cn/api/other/jwjuhe.php",
    "id": os.getenv("ADDRESS_API_ID", "10010204"),
    "key": os.getenv("ADDRESS_API_KEY", ""),
    "timeout": 10,
    "cache_duration": 86400
}

PRESET_CITIES = [
    {"name": "上海", "latitude": 31.2304, "longitude": 121.4737, "timezone": "Asia/Shanghai"},
    {"name": "湖南株洲", "latitude": 27.8270, "longitude": 113.1241, "timezone": "Asia/Shanghai"},
    {"name": "福建宁德", "latitude": 26.6518, "longitude": 119.5355, "timezone": "Asia/Shanghai"},
    {"name": "北京", "latitude": 39.9042, "longitude": 116.4074, "timezone": "Asia/Shanghai"},
    {"name": "广州", "latitude": 23.1291, "longitude": 113.2644, "timezone": "Asia/Shanghai"},
    {"name": "深圳", "latitude": 22.5431, "longitude": 114.0579, "timezone": "Asia/Shanghai"},
    {"name": "杭州", "latitude": 30.2741, "longitude": 120.1551, "timezone": "Asia/Shanghai"},
    {"name": "成都", "latitude": 30.5728, "longitude": 104.0668, "timezone": "Asia/Shanghai"},
    {"name": "重庆", "latitude": 29.4316, "longitude": 106.9123, "timezone": "Asia/Shanghai"},
    {"name": "西安", "latitude": 34.3416, "longitude": 108.9398, "timezone": "Asia/Shanghai"},
    {"name": "武汉", "latitude": 30.5928, "longitude": 114.3055, "timezone": "Asia/Shanghai"},
    {"name": "南京", "latitude": 32.0603, "longitude": 118.7969, "timezone": "Asia/Shanghai"},
    {"name": "纽约", "latitude": 40.7128, "longitude": -74.0060, "timezone": "America/New_York"},
    {"name": "洛杉矶", "latitude": 34.0522, "longitude": -118.2437, "timezone": "America/Los_Angeles"},
    {"name": "伦敦", "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"},
    {"name": "巴黎", "latitude": 48.8566, "longitude": 2.3522, "timezone": "Europe/Paris"},
    {"name": "东京", "latitude": 35.6762, "longitude": 139.6503, "timezone": "Asia/Tokyo"},
    {"name": "悉尼", "latitude": -33.8688, "longitude": 151.2093, "timezone": "Australia/Sydney"},
    {"name": "新加坡", "latitude": 1.3521, "longitude": 103.8198, "timezone": "Asia/Singapore"},
    {"name": "曼谷", "latitude": 13.7563, "longitude": 100.5018, "timezone": "Asia/Bangkok"}
]
