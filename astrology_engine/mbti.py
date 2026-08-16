"""MBTI personality insight adapter.

The scoring implementation in :mod:`astrology_engine.mbti_modules` is the
algorithm migrated from ephh.  This module is the public, framework-free
entrypoint for the current project: it accepts the local natal envelope (or a
small chart payload) and returns the detailed, auditable result.

MBTI here is an auxiliary symbolic insight layer.  It is not a psychological
diagnosis, a validated personality assessment, or a replacement for the
classical chart judgment.
"""
from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping

from .mbti_modules.calculator import MBTICalculator
from .mbti_modules.constants import ASPECT_TYPE_MAP, CORE_BODIES, MBTI_FUNCTION_ORDER
from .mbti_modules.rules_store import get_merged_rules


_SIGNS = (
    "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
    "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座",
)
_SIGN_ALIASES = {
    **{sign: sign for sign in _SIGNS},
    **{sign[:-1]: sign for sign in _SIGNS},
    **{name.lower(): _SIGNS[index] for index, name in enumerate((
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ))},
}
_CLASSICAL_RULERS = {
    "白羊座": "Mars", "金牛座": "Venus", "双子座": "Mercury", "巨蟹座": "Moon",
    "狮子座": "Sun", "处女座": "Mercury", "天秤座": "Venus", "天蝎座": "Mars",
    "射手座": "Jupiter", "摩羯座": "Saturn", "水瓶座": "Saturn", "双鱼座": "Jupiter",
}
_DIGNITIES = {
    "Sun": {"狮子座": "domicile", "白羊座": "exaltation", "水瓶座": "detriment", "天秤座": "fall"},
    "Moon": {"巨蟹座": "domicile", "金牛座": "exaltation", "摩羯座": "detriment", "天蝎座": "fall"},
    "Mercury": {"双子座": "domicile", "处女座": "domicile_exaltation", "射手座": "detriment", "双鱼座": "fall"},
    "Venus": {"金牛座": "domicile", "天秤座": "domicile", "双鱼座": "exaltation", "白羊座": "detriment", "天蝎座": "detriment", "处女座": "fall"},
    "Mars": {"白羊座": "domicile", "天蝎座": "domicile", "摩羯座": "exaltation", "天秤座": "detriment", "金牛座": "detriment", "巨蟹座": "fall"},
    "Jupiter": {"射手座": "domicile", "双鱼座": "domicile", "巨蟹座": "exaltation", "双子座": "detriment", "处女座": "detriment", "摩羯座": "fall"},
    "Saturn": {"摩羯座": "domicile", "水瓶座": "domicile", "天秤座": "exaltation", "巨蟹座": "detriment", "狮子座": "detriment", "白羊座": "fall"},
}
_TRADITIONAL = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
_PLANET_ALIASES = {
    "太阳": "Sun", "月亮": "Moon", "水星": "Mercury", "金星": "Venus", "火星": "Mars",
    "木星": "Jupiter", "土星": "Saturn", "天王星": "Uranus", "海王星": "Neptune", "冥王星": "Pluto",
    "北交点": "North Node", "南交点": "South Node",
}


def _canonical_planet_name(value: Any) -> str:
    raw = str(value).strip()
    return _PLANET_ALIASES.get(raw, raw)


def _validated_house(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"MBTI行星宫位必须是1到12的整数，收到: {value!r}")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"MBTI行星宫位必须是1到12的整数，收到: {value!r}") from exc
    if not math.isfinite(numeric) or numeric != int(numeric) or not 1 <= int(numeric) <= 12:
        raise ValueError(f"MBTI行星宫位必须是1到12的整数，收到: {value!r}")
    return int(numeric)


def _validated_longitude(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label}必须是0到360之间的黄经，收到: {value!r}")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}必须是0到360之间的黄经，收到: {value!r}") from exc
    if not math.isfinite(numeric) or not 0 <= numeric < 360:
        raise ValueError(f"{label}必须是0到360之间的黄经，收到: {value!r}")
    return numeric


def _behavioral_translation(result: Mapping[str, Any], chart_data: Mapping[str, Any], audit: Mapping[str, Any]) -> dict[str, Any]:
    """Translate the dimension score into an observable, falsifiable behavior.

    This is deliberately kept separate from the four-letter label.  A strong
    I score is useful only when it explains a repeatable pattern (for example,
    sustained independent work), and the counter-test prevents the chart
    symbolism from being treated as a deterministic psychological diagnosis.
    """
    scores = result.get("scores", {})
    introversion = int(scores.get("I", 0))
    extraversion = int(scores.get("E", 0))
    gap = introversion - extraversion
    if gap >= 20:
        status = "strong"
        observable = "I倾向明显：可以连续较长时间独立处理自己的事情，持续社交不是维持工作状态的必要条件。"
    elif gap >= 10:
        status = "moderate"
        observable = "I倾向偏高：通常需要独处或低干扰时段来恢复注意力，再按任务需要进行社交。"
    else:
        status = "weak_or_mixed"
        observable = "I/E差距不足以单独支持稳定的独处偏好，需要更多现实行为样本校准。"

    planets = {item.get("name"): item for item in chart_data.get("planets", [])}
    evidence: list[str] = [f"I/E评分为{introversion}/{extraversion}，差距{gap}分。"]
    chart_ruler = audit.get("chart_ruler")
    chart_ruler_house = audit.get("chart_ruler_house")
    if chart_ruler and chart_ruler_house:
        evidence.append(f"命主星{chart_ruler}落第{chart_ruler_house}宫，提示主体能量的主要承载场域。")
    axis_by_house = {item.get("house"): item for item in audit.get("axis_audit", [])}
    for house in (3, 12):
        item = axis_by_house.get(house)
        if item and item.get("ruler_house"):
            evidence.append(f"第{house}宫宫主{item.get('ruler')}落第{item.get('ruler_house')}宫，沟通/退隐议题回流至私域。")
    private_cluster = [name for name, item in planets.items() if item.get("house") == 4 and name in _TRADITIONAL]
    if len(private_cluster) >= 2:
        evidence.append(f"第4宫有{', '.join(private_cluster)}等传统星体聚集，独处、内在整理与私人根基的权重较高。")

    return {
        "status": status,
        "observable_pattern": observable,
        "mechanism": "独处时更容易维持注意力、整理内部信息并完成连续性工作；社交更像按任务需要调用，而非持续驱动。",
        "evidence": evidence,
        "counter_test": "若现实中必须高频互动仍能长期保持精力与产出，或独处后并不恢复反而明显耗竭，则应降低I标签的解释权重。",
        "grade": "B",
        "notice": "行为翻译是候选机制，不是心理测验结论；应以重复的现实观察优先校准。",
    }


def _sign(value: Any, longitude: Any = None) -> str:
    if isinstance(value, Mapping):
        value = value.get("name") or value.get("sign")
    if isinstance(value, str):
        normalized = _SIGN_ALIASES.get(value.strip()) or _SIGN_ALIASES.get(value.strip().lower())
        if normalized:
            return normalized
    if isinstance(value, int) and 0 <= value < 12:
        return _SIGNS[value]
    if isinstance(longitude, (int, float)):
        return _SIGNS[int(float(longitude) % 360 // 30)]
    return ""


def _placements(chart: Mapping[str, Any]) -> Mapping[str, Any]:
    """Locate placements in both current and legacy chart envelopes."""
    if isinstance(chart.get("placements"), Mapping):
        return chart["placements"]
    if isinstance(chart.get("planets"), Mapping):
        return chart["planets"]
    nested = chart.get("chart_facts")
    if isinstance(nested, Mapping):
        return _placements(nested)
    return {}


def normalize_chart_data(chart: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a local natal envelope to the migrated MBTI input contract."""
    source = chart.get("chart_facts") if isinstance(chart.get("chart_facts"), Mapping) else chart
    placements = _placements(source)
    planets: list[dict[str, Any]] = []
    for name, raw in placements.items():
        if not isinstance(raw, Mapping):
            continue
        canonical_name = _canonical_planet_name(name)
        if canonical_name not in set(CORE_BODIES) and canonical_name not in {"North Node", "South Node"}:
            continue
        row = dict(raw)
        longitude = _validated_longitude(row.get("ecl_lon", row.get("ecliptic_longitude")), f"MBTI行星{canonical_name}黄经")
        zodiac = _sign(row.get("zodiac", row.get("sign")), longitude)
        raw_house = row.get("house") if row.get("house") is not None else row.get("house_number")
        house = _validated_house(raw_house)
        if house is None:
            continue
        if not zodiac:
            raise ValueError(f"MBTI行星{canonical_name}缺少合法星座或黄经")
        planets.append({
            "name": _canonical_planet_name(row.get("name", canonical_name)),
            "ecl_lon": longitude,
            "zodiac": {"name": zodiac},
            "house": int(house),
            "house_number": int(house),
            "is_retrograde": bool(row.get("is_retrograde", False)),
        })
    if isinstance(chart.get("planets"), list):
        planets = []
        for raw in chart["planets"]:
            if not isinstance(raw, Mapping):
                continue
            canonical_name = _canonical_planet_name(raw.get("name", ""))
            if canonical_name not in set(CORE_BODIES) and canonical_name not in {"North Node", "South Node"}:
                continue
            longitude = _validated_longitude(raw.get("ecl_lon", raw.get("ecliptic_longitude")), f"MBTI行星{canonical_name}黄经")
            raw_house = raw.get("house") if raw.get("house") is not None else raw.get("house_number")
            house = _validated_house(raw_house)
            if house is None:
                continue
            zodiac = _sign(raw.get("zodiac", raw.get("sign")), longitude)
            if not zodiac:
                raise ValueError(f"MBTI行星{canonical_name}缺少合法星座或黄经")
            planets.append({
                **dict(raw),
                "name": canonical_name,
                "ecl_lon": longitude,
                "zodiac": {"name": zodiac},
                "house": int(house),
                "house_number": int(house),
            })
    names = [item["name"] for item in planets]
    if len(names) != len(set(names)):
        raise ValueError("MBTI行星名称不可重复")
    by_name = {item["name"]: item for item in planets}
    asc_lon = None
    houses = source.get("houses") if isinstance(source, Mapping) else None
    if isinstance(houses, Mapping):
        asc_lon = _validated_longitude(houses.get("asc"), "MBTI上升点黄经")
    raw_cusps = (houses or {}).get("house_cusps", []) if isinstance(houses, Mapping) else []
    if raw_cusps:
        if not isinstance(raw_cusps, (list, tuple)) or len(raw_cusps) != 12:
            raise ValueError("MBTI house_cusps必须包含12个黄经")
        house_cusps = [_validated_longitude(value, "MBTI宫头黄经") for value in raw_cusps]
        if len(set(house_cusps)) != 12:
            raise ValueError("MBTI house_cusps必须对应12个不同的宫头")
    else:
        house_cusps = []
    ascendant = source.get("ascendant") if isinstance(source, Mapping) else None
    ascendant = _sign(ascendant, asc_lon)
    aspects = []
    aspect_index: dict[tuple[tuple[str, str], str], int] = {}
    for raw in (source.get("aspects") or []) if isinstance(source, Mapping) else []:
        if not isinstance(raw, Mapping):
            continue
        p1 = _canonical_planet_name(raw.get("planet1") or raw.get("cel1") or "")
        p2 = _canonical_planet_name(raw.get("planet2") or raw.get("cel2") or "")
        supported_endpoints = set(by_name) | {"Ascendant"}
        if not p1 or not p2 or p1 not in supported_endpoints or p2 not in supported_endpoints:
            continue
        try:
            orb = float(raw.get("orb", 0) or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"MBTI相位容许度必须是非负数，收到: {raw.get('orb')!r}") from exc
        if not math.isfinite(orb) or orb < 0:
            raise ValueError(f"MBTI相位容许度必须是非负数，收到: {raw.get('orb')!r}")
        aspect_type = raw.get("type", "")
        if aspect_type is None:
            aspect_type = ""
        if not isinstance(aspect_type, str):
            raise ValueError(f"MBTI相位类型必须是文本，收到: {aspect_type!r}")
        aspect_type = aspect_type.strip()
        key = (tuple(sorted((p1, p2))), ASPECT_TYPE_MAP.get(aspect_type, aspect_type))
        normalized_aspect = {"planet1": p1, "planet2": p2, "type": aspect_type, "orb": orb}
        previous = aspect_index.get(key)
        if previous is None:
            aspect_index[key] = len(aspects)
            aspects.append(normalized_aspect)
        elif orb < aspects[previous]["orb"]:
            # A duplicated aspect record should not double-count its influence;
            # retain the tighter observation as the representative record.
            aspects[previous] = normalized_aspect
    return {
        "planets": list(by_name.values()),
        "aspects": aspects,
        "ascendant": ascendant,
        "sun_sign": by_name.get("Sun", {}).get("zodiac", {}).get("name", ""),
        "moon_sign": by_name.get("Moon", {}).get("zodiac", {}).get("name", ""),
        "house_cusps": house_cusps,
        "ascendant_longitude": asc_lon,
        "mc_longitude": (houses or {}).get("mc") if isinstance(houses, Mapping) else None,
    }


def _classical_audit(chart_data: Mapping[str, Any]) -> dict[str, Any]:
    """Build the classical evidence layer without changing the MBTI score.

    MBTI mappings are modern symbolic associations. This audit makes the
    traditional responsibility chain visible so a type label cannot silently
    replace the chart's actual rulers, condition, sect and angularity.
    """
    planets = {item["name"]: item for item in chart_data.get("planets", [])}
    asc = chart_data.get("ascendant") or ""
    chart_ruler = _CLASSICAL_RULERS.get(asc)
    sun_house = planets.get("Sun", {}).get("house", 0)
    is_day = sun_house in (7, 8, 9, 10, 11, 12)
    axis = []
    cusps = chart_data.get("house_cusps") or []
    for house in (1, 2, 3, 6, 10, 11, 12):
        ruler = None
        cusp_sign = None
        if len(cusps) == 12:
            cusp_lon = float(cusps[house - 1]) % 360
            cusp_sign = _SIGNS[int(cusp_lon // 30)]
            ruler = _CLASSICAL_RULERS.get(cusp_sign)
        ruler_data = planets.get(ruler) if ruler else None
        axis.append({
            "house": house,
            "cusp_sign": cusp_sign,
            "ruler": ruler,
            "ruler_sign": ruler_data.get("zodiac", {}).get("name") if ruler_data else None,
            "ruler_house": ruler_data.get("house") if ruler_data else None,
            "ruler_dignity": _DIGNITIES.get(ruler, {}).get(ruler_data.get("zodiac", {}).get("name"), "peregrine") if ruler_data else None,
            "occupants": [name for name, item in planets.items() if item.get("house") == house and name in _TRADITIONAL],
            "auxiliary_occupants": [name for name, item in planets.items() if item.get("house") == house and name not in _TRADITIONAL and name in {"Uranus", "Neptune", "Pluto"}],
        })
    evidence_chain = []
    for item in axis:
        if not item.get("ruler") or item.get("ruler_house") is None:
            continue
        house = item["house"]
        role = {1: "主体与行动", 2: "收入与资源", 3: "沟通与学习", 6: "日常工作与服务", 10: "公共角色与事业", 11: "盟友、网络与收益", 12: "退隐、隐性负荷与幕后事务"}[house]
        evidence_chain.append({
            "fact": f"第{house}宫宫头{item['cusp_sign']}，宫主{item['ruler']}落第{item['ruler_house']}宫{item['ruler_sign']}",
            "rule": f"第{house}宫负责{role}；宫主落宫表示该责任的交付领域",
            "inference": f"{role}需要沿{item['ruler']}的落宫领域观察，而不能由MBTI标签代替",
            "grade": "B",
        })
    return {
        "status": "auxiliary_context_only",
        "sect": "day" if is_day else "night",
        "chart_ruler": chart_ruler,
        "chart_ruler_house": planets.get(chart_ruler, {}).get("house") if chart_ruler else None,
        "axis_audit": axis,
        "evidence_chain": evidence_chain,
        "limiting_testimony": ["上升接近宫界、精确时间/地点误差会影响宫位", "人格类型没有心理测验或现实行为校准时只能作为候选标签"],
        "classical_priority": "人格/能力的古典判断须先看1宫、命主星、月亮、太阳、尊贵、sect、角性与相位；MBTI类型不能替代该判断。",
        "modern_layer": "MBTI维度与荣格功能仅是现代象征映射，不是由古典规则证明的心理类型。",
    }


def calculate_mbti(chart: Mapping[str, Any], *, rules: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Calculate the migrated MBTI insight for a natal chart."""
    chart_data = normalize_chart_data(deepcopy(dict(chart)))
    if not chart_data["planets"]:
        raise ValueError("MBTI calculation requires at least one planet with a house")
    result = MBTICalculator(chart_data, dict(rules) if rules is not None else get_merged_rules()).calculate_scores()
    result["algorithm_version"] = "mbti-ephh-migrated"
    sorted_functions = sorted(result["jungian_scores"].items(), key=lambda item: item[1], reverse=True)
    type_function_order = MBTI_FUNCTION_ORDER.get(result["personality_type"], [])
    level_names = ("dominant", "auxiliary", "tertiary", "inferior")
    # A type label has a theoretical stack.  Do not relabel the four highest
    # raw scores as that stack: an INFJ whose raw score happens to rank Ne
    # above Fe is precisely a low-alignment/borderline result, not a new MBTI
    # stack. Keep both views explicit for auditability.
    result["function_levels"] = {
        level: type_function_order[index] if len(type_function_order) > index else "N/A"
        for index, level in enumerate(level_names)
    }
    result["function_scores"] = {
        level: result["jungian_scores"].get(type_function_order[index], 0) if len(type_function_order) > index else 0
        for index, level in enumerate(level_names)
    }
    result["function_order"] = type_function_order
    result["function_score_rank"] = [name for name, _ in sorted_functions]
    result["function_stack_alignment"] = {
        "type_stack": type_function_order,
        "score_rank": [name for name, _ in sorted_functions[:4]],
        "status": "aligned" if type_function_order[:2] == [name for name, _ in sorted_functions[:2]] else "mixed",
        "notice": "类型功能顺序是理论栈；原始分数排名是星盘映射结果，二者不一致时不得把分数排名写成真实功能层级。",
    }
    result["dimension_offsets"] = {
        "ei": int((result["scores"]["E"] - result["scores"]["I"]) * 0.5),
        "sn": int((result["scores"]["S"] - result["scores"]["N"]) * 0.5),
        "tf": int((result["scores"]["T"] - result["scores"]["F"]) * 0.5),
        "jp": int((result["scores"]["J"] - result["scores"]["P"]) * 0.5),
    }
    present_names = {item["name"] for item in chart_data["planets"]}
    missing_core = [name for name in ("Sun", "Moon") if name not in present_names]
    if not chart_data["ascendant"]:
        missing_core.append("Ascendant")
    input_quality = {
        "present_core_bodies": sorted(present_names & {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}),
        "missing_high_weight_bodies": missing_core,
        "level": "完整" if not missing_core else "输入不足",
        "notice": "缺少太阳、月亮或上升时仍可计算符号分数，但不应将类型当作稳定人格结论。" if missing_core else "太阳、月亮与上升信息齐全，可进入常规候选型解释。",
    }
    result["input_summary"] = {
        "planet_count": len(chart_data["planets"]),
        "aspect_count": len(chart_data["aspects"]),
        "has_ascendant": bool(chart_data["ascendant"]),
        "input_quality": input_quality,
    }
    dimension_gaps = {
        pair: abs(result["scores"][first] - result["scores"][second])
        for pair, (first, second) in {"EI": ("E", "I"), "SN": ("S", "N"), "TF": ("T", "F"), "JP": ("J", "P")}.items()
    }
    borderline = [pair for pair, gap in dimension_gaps.items() if gap < 5]
    exact_ties = [pair for pair, gap in dimension_gaps.items() if gap == 0]
    result["classification_stability"] = {
        "dimension_gaps": dimension_gaps,
        "status": "insufficient_input" if missing_core else ("borderline" if borderline else "clear"),
        "borderline_dimensions": borderline,
        "exact_ties": exact_ties,
        "tie_policy": "四字母输出保留确定性格式，但精确平票不代表该轴有方向性证据。",
        "notice": (
            "输入缺少高权重太阳、月亮或上升，当前类型仅作低置信候选；"
            "补齐出生数据后再解释。" if missing_core else
            "边界维度不应被写成固定人格标签；需用现实行为和重复测量校准。"
        ),
    }
    result["astrology_audit"] = _classical_audit(chart_data)
    result["behavioral_translation"] = _behavioral_translation(
        result, chart_data, result["astrology_audit"]
    )
    result["interpretation_limits"] = (
        "这是基于星盘符号的辅助人格洞察，不是心理诊断、标准化人格测验或固定身份标签；"
        "请用现实行为与反馈校准。"
    )
    result["chart_data"] = chart_data
    return result


calculate_mbti_insight = calculate_mbti
calculate_personality_insight = calculate_mbti
MBTIInsightCalculator = MBTICalculator
MBTIPersonalityInsightCalculator = MBTICalculator

__all__ = [
    "MBTIInsightCalculator", "MBTIPersonalityInsightCalculator", "MBTICalculator",
    "calculate_mbti", "calculate_mbti_insight", "calculate_personality_insight",
    "normalize_chart_data",
]
