import logging
import swisseph as real_swe
from typing import Dict, Any, List
logger = logging.getLogger(__name__)


PLANETS = [
    ("Sun", 0),
    ("Moon", 1),
    ("Mercury", 2),
    ("Venus", 3),
    ("Mars", 4),
    ("Jupiter", 5),
    ("Saturn", 6),
    ("Uranus", 7),
    ("Neptune", 8),
    ("Pluto", 9),
    ("North Node", real_swe.TRUE_NODE),
    ("Chiron", real_swe.CHIRON),
    ("Juno", real_swe.JUNO),
    ("Fortune", -1),
]

PLANETS_EXTENDED = [
    ("Sun", 0),
    ("Moon", 1),
    ("Mercury", 2),
    ("Venus", 3),
    ("Mars", 4),
    ("Jupiter", 5),
    ("Saturn", 6),
    ("Uranus", 7),
    ("Neptune", 8),
    ("Pluto", 9),
    ("North Node", real_swe.TRUE_NODE),
    ("Chiron", real_swe.CHIRON),
    ("Juno", real_swe.JUNO),
    ("Ceres", real_swe.CERES),
    ("Pallas", real_swe.PALLAS),
    ("Vesta", real_swe.VESTA),
    ("Fortune", -1),
    ("Lilith", -2),
]

PLANET_MAG = {
    "Sun": -26.74,
    "Moon": -12.74,
    "Mercury": -0.6,
    "Venus": -4.0,
    "Mars": -1.5,
    "Jupiter": -2.2,
    "Saturn": 0.9,
    "Uranus": 5.7,
    "Neptune": 7.8,
    "Pluto": 14.0,
    "North Node": 6.0,
    "South Node": 6.0,
    "Chiron": 6.0,
    "Juno": 6.0,
    "Ceres": 6.0,
    "Pallas": 6.0,
    "Vesta": 6.0,
    "Fortune": 6.0,
    "Lilith": 6.0,
}

PLANET_COLOR = {
    "Sun": "#FFCC33",
    "Moon": "#DDDDFF",
    "Mercury": "#BFBFBF",
    "Venus": "#FFD1DC",
    "Mars": "#FF6B6B",
    "Jupiter": "#F5C27A",
    "Saturn": "#E0C588",
    "Uranus": "#8FD3FF",
    "Neptune": "#6EA8FF",
    "Pluto": "#C0A0C8",
    "North Node": "#99FF99",
    "South Node": "#FF9999",
    "Chiron": "#B0E0E6",
    "Juno": "#DDA0DD",
    "Ceres": "#98FB98",
    "Pallas": "#87CEEB",
    "Vesta": "#FFA07A",
    "Lilith": "#9370DB",
}

PLANET_NAMES_CN = {
    "Sun": "太阳",
    "Moon": "月亮",
    "Mercury": "水星",
    "Venus": "金星",
    "Mars": "火星",
    "Jupiter": "木星",
    "Saturn": "土星",
    "Uranus": "天王星",
    "Neptune": "海王星",
    "Pluto": "冥王星",
    "North Node": "北交点",
    "South Node": "南交点",
    "Chiron": "凯龙星",
    "Juno": "婚神星",
    "Ceres": "谷神星",
    "Pallas": "智神星",
    "Vesta": "灶神星",
    "Fortune": "福点",
    "Lilith": "莉莉丝",
    "Ascendant": "上升点",
    "Midheaven": "中天",
    "Descendant": "下降点",
    "Imum Coeli": "天底",
}

SIGN_RULERS_TRADITIONAL = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}

SIGN_RULERS_MODERN = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Pluto",
    8: "Jupiter",
    9: "Saturn",
    10: "Uranus",
    11: "Neptune",
}

EXALTATION_RULERS = {
    0: "Sun",
    1: "Moon",
    2: None,
    3: "Jupiter",
    4: None,
    5: "Mercury",
    6: "Saturn",
    7: None,
    8: None,
    9: "Mars",
    10: None,
    11: "Venus",
}

DETRIMENT_RULERS_TRADITIONAL = {
    0: "Venus",
    1: "Mars",
    2: "Jupiter",
    3: "Saturn",
    4: "Saturn",
    5: "Jupiter",
    6: "Mars",
    7: "Venus",
    8: "Mercury",
    9: "Moon",
    10: "Sun",
    11: "Mercury",
}

FALL_RULERS = {
    0: "Saturn",
    1: None,
    2: None,
    3: "Mars",
    4: None,
    5: "Jupiter",
    6: None,
    7: None,
    8: None,
    9: "Jupiter",
    10: None,
    11: None,
}

# Traditional Egyptian terms.  The table is kept explicit because term
# systems differ; the production engine must never silently switch between
# Egyptian and Ptolemaic bounds.
TERMS_EGYPTIAN = {
    0: [(6, "Jupiter"), (12, "Venus"), (20, "Mercury"), (25, "Mars"), (30, "Saturn")],
    1: [(8, "Venus"), (14, "Mercury"), (22, "Jupiter"), (27, "Saturn"), (30, "Mars")],
    2: [(6, "Mercury"), (12, "Jupiter"), (17, "Venus"), (24, "Mars"), (30, "Saturn")],
    3: [(7, "Mars"), (13, "Venus"), (19, "Mercury"), (26, "Jupiter"), (30, "Saturn")],
    4: [(6, "Jupiter"), (11, "Venus"), (18, "Saturn"), (24, "Mercury"), (30, "Mars")],
    5: [(7, "Mercury"), (17, "Venus"), (21, "Jupiter"), (28, "Mars"), (30, "Saturn")],
    6: [(6, "Mercury"), (14, "Saturn"), (21, "Jupiter"), (28, "Venus"), (30, "Mars")],
    7: [(6, "Saturn"), (11, "Mercury"), (20, "Jupiter"), (24, "Venus"), (30, "Mars")],
    8: [(6, "Mars"), (14, "Venus"), (19, "Mercury"), (25, "Jupiter"), (30, "Saturn")],
    9: [(6, "Mercury"), (12, "Jupiter"), (19, "Venus"), (25, "Saturn"), (30, "Mars")],
    10: [(6, "Mercury"), (12, "Venus"), (20, "Jupiter"), (25, "Mars"), (30, "Saturn")],
    11: [(8, "Venus"), (14, "Jupiter"), (20, "Mercury"), (25, "Mars"), (30, "Saturn")],
}

# Triplicity rulers in the order day, night, participating.  This is the
# Dorothean scheme used by the project's classical layer.
TRIPLICITY_RULERS_DOROTHEAN = {
    "fire": ("Sun", "Jupiter", "Saturn"),
    "earth": ("Venus", "Moon", "Mars"),
    "air": ("Saturn", "Mercury", "Jupiter"),
    "water": ("Venus", "Mars", "Moon"),
}
SIGN_TRIPLICITY = {
    0: "fire", 1: "earth", 2: "air", 3: "water",
    4: "fire", 5: "earth", 6: "air", 7: "water",
    8: "fire", 9: "earth", 10: "air", 11: "water",
}

# Faces/decans, beginning with Mars at 0° Aries and proceeding in Chaldean
# order.  Each tuple is the end degree and ruler of that face.
FACES_CHALDEAN = {
    sign: [(10, order[(sign * 3 + 0) % 7]), (20, order[(sign * 3 + 1) % 7]), (30, order[(sign * 3 + 2) % 7])]
    for sign, order in [(i, ["Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter"]) for i in range(12)]
}

FIRDARIA_ORDER_DAY = [
    ("Sun", 10), ("Venus", 8), ("Mercury", 13), ("Moon", 9),
    ("Saturn", 11), ("Jupiter", 12), ("Mars", 7), ("North Node", 3),
]

FIRDARIA_ORDER_NIGHT = [
    ("Moon", 9), ("Saturn", 11), ("Jupiter", 12), ("Mars", 7),
    ("North Node", 3), ("Sun", 10), ("Venus", 8), ("Mercury", 13),
]

ASPECT_DEFS = {
    "conjunction": {"angle": 0, "orb": 8.0},
    "opposition": {"angle": 180, "orb": 8.0},
    "trine": {"angle": 120, "orb": 8.0},
    "square": {"angle": 90, "orb": 7.0},
    "sextile": {"angle": 60, "orb": 6.0},
    "quincunx": {"angle": 150, "orb": 5.0},
    "semisquare": {"angle": 45, "orb": 3.0},
    "sesquisquare": {"angle": 135, "orb": 3.0},
}

ASPECT_NAMES_CN = {
    "conjunction": "合相",
    "opposition": "对冲",
    "trine": "三分相",
    "square": "四分相",
    "sextile": "六分相",
    "quincunx": "梅花相",
    "semisquare": "半四分相",
    "sesquisquare": "倍半四分相",
}

ZODIAC_NAMES = ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
                "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]

HOUSE_MEANINGS = {
    1: "自我、外貌、性格",
    2: "财运、价值观、物质资源",
    3: "沟通、学习、兄弟姐妹",
    4: "家庭、房产、父母、根基",
    5: "恋爱、子女、创造力、娱乐",
    6: "工作、健康、服务、日常",
    7: "婚姻、合伙、他人、合作",
    8: "投资、偏财、转化、深层",
    9: "教育、旅行、哲学、信仰",
    10: "事业、名声、地位、成就",
    11: "社交、人脉、理想、群体",
    12: "玄学、潜意识、隐秘、灵性",
}


def check_ephemeris():
    try:
        real_swe.calc_ut(2459000, 0)
        logger.info("[INFO] swisseph库已成功加载，无需星历表文件")
    except Exception as e:
        logger.error(f"[WARN] swisseph库加载失败：{str(e)}")
