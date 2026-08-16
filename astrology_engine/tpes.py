"""TPES 职业洞察 v3：以 2/6/10 宫为核心的可解释职业风格评分。

The calculator is migrated from ephh but deliberately has no web route,
authentication or database dependency.  ``calculate_tpes`` accepts the local
project natal envelope and returns the same fixed-budget, auditable result.
"""

from collections import defaultdict
import math
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator
from .tpes_modules.templates import ANIMAL_TYPES, PLANET_NAME_MAP, PLANET_TO_TPES, ELEMENT_TO_TPES, MODALITY_TO_TPES, normalize_aspect_type

ZODIAC_NAMES = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
ZODIAC_MAP = {**{name.lower(): name for name in ZODIAC_NAMES}, "白羊": "Aries", "白羊座": "Aries", "金牛": "Taurus", "金牛座": "Taurus", "双子": "Gemini", "双子座": "Gemini", "巨蟹": "Cancer", "巨蟹座": "Cancer", "狮子": "Leo", "狮子座": "Leo", "处女": "Virgo", "处女座": "Virgo", "天秤": "Libra", "天秤座": "Libra", "天蝎": "Scorpio", "天蝎座": "Scorpio", "射手": "Sagittarius", "射手座": "Sagittarius", "摩羯": "Capricorn", "摩羯座": "Capricorn", "水瓶": "Aquarius", "水瓶座": "Aquarius", "双鱼": "Pisces", "双鱼座": "Pisces"}
PLANET_NAME_MAP_REVERSE = {value: key for key, value in PLANET_NAME_MAP.items()}
CORE_PLANETS = set(PLANET_NAME_MAP)
TRADITIONAL = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
OUTER = {"Uranus", "Neptune", "Pluto"}
CAREER_HOUSES = {2: 10.0, 6: 15.0, 10: 20.0}
CORE_PERSONAL_PLANETS = ("Sun", "Moon", "Mercury", "Venus", "Mars")
RULERS = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"}
ELEMENTS = {"Aries": "火象", "Leo": "火象", "Sagittarius": "火象", "Taurus": "土象", "Virgo": "土象", "Capricorn": "土象", "Gemini": "风象", "Libra": "风象", "Aquarius": "风象", "Cancer": "水象", "Scorpio": "水象", "Pisces": "水象"}
MODALITIES = {"Aries": "基本宫", "Cancer": "基本宫", "Libra": "基本宫", "Capricorn": "基本宫", "Taurus": "固定宫", "Leo": "固定宫", "Scorpio": "固定宫", "Aquarius": "固定宫", "Gemini": "变动宫", "Virgo": "变动宫", "Sagittarius": "变动宫", "Pisces": "变动宫"}
DIGNITIES = {
    "Sun": {"Leo": ("庙", 1.20), "Aries": ("旺", 1.10), "Aquarius": ("弱", .90), "Libra": ("陷", .80)},
    "Moon": {"Cancer": ("庙", 1.20), "Taurus": ("旺", 1.10), "Capricorn": ("弱", .90), "Scorpio": ("陷", .80)},
    "Mercury": {"Gemini": ("庙", 1.20), "Virgo": ("庙/旺", 1.20), "Sagittarius": ("弱", .90), "Pisces": ("陷", .80)},
    "Venus": {"Taurus": ("庙", 1.20), "Libra": ("庙", 1.20), "Pisces": ("旺", 1.10), "Aries": ("弱", .90), "Scorpio": ("弱", .90), "Virgo": ("陷", .80)},
    "Mars": {"Aries": ("庙", 1.20), "Scorpio": ("庙", 1.20), "Capricorn": ("旺", 1.10), "Libra": ("弱", .90), "Taurus": ("弱", .90), "Cancer": ("陷", .80)},
    "Jupiter": {"Sagittarius": ("庙", 1.20), "Pisces": ("庙", 1.20), "Cancer": ("旺", 1.10), "Gemini": ("弱", .90), "Virgo": ("弱", .90), "Capricorn": ("陷", .80)},
    "Saturn": {"Capricorn": ("庙", 1.20), "Aquarius": ("庙", 1.20), "Libra": ("旺", 1.10), "Cancer": ("弱", .90), "Leo": ("弱", .90), "Aries": ("陷", .80)},
}

WORLD_MODEL_MODULES = {
    "Moon": {"module": "认知表征与记忆", "english": "Representation & Memory", "question": "如何形成并保留可调用的内部经验？", "capabilities": ["经验归纳", "模式记忆", "情境感知"]},
    "Mercury": {"module": "信息压缩", "english": "Information Compression", "question": "如何从复杂信息中提取可用信号？", "capabilities": ["抽象表达", "信息筛选", "指标与模型沟通"]},
    "Sun": {"module": "状态空间", "english": "State Space", "question": "问题系统的关键变量与目标是什么？", "capabilities": ["问题定义", "目标聚焦", "系统建模"]},
    "Saturn": {"module": "本体结构", "english": "Ontology", "question": "实体、边界、关系与规则如何被组织？", "capabilities": ["结构化", "规则设计", "质量与风险约束"]},
    "Mars": {"module": "因果推理", "english": "Causality", "question": "什么因素驱动结果，哪些行动能形成干预？", "capabilities": ["假设检验", "行动推进", "实验与复盘"]},
    "Jupiter": {"module": "动态演化", "english": "Dynamics", "question": "系统如何随时间变化并形成趋势？", "capabilities": ["趋势判断", "长期推演", "机会扩展"]},
    "Neptune": {"module": "涌现规律", "english": "Emergence", "question": "微观互动如何形成群体与文化层面的结果？", "capabilities": ["整体感知", "文化洞察", "复杂关系识别"]},
    "Venus": {"module": "价值与策略", "english": "Value & Policy", "question": "什么值得优化，以及如何在约束中取舍？", "capabilities": ["价值判断", "利益相关者协调", "资源取舍"]},
    "Uranus": {"module": "反馈控制", "english": "Feedback Control", "question": "如何根据反馈修正策略与系统？", "capabilities": ["迭代优化", "系统创新", "反馈闭环"]},
    "Pluto": {"module": "元进化", "english": "Meta Evolution", "question": "如何重构原有框架并提升学习能力？", "capabilities": ["深度研究", "范式重构", "持续学习"]},
}


def normalize_zodiac(value: Union[str, int, None]) -> Optional[str]:
    if isinstance(value, int) and 1 <= value <= 12:
        return ZODIAC_NAMES[value - 1]
    if isinstance(value, str):
        return ZODIAC_MAP.get(value.strip().lower()) or ZODIAC_MAP.get(value.strip())
    return None


def normalize_planet_name(name: str) -> Optional[str]:
    return name.strip() if name.strip() in CORE_PLANETS else PLANET_NAME_MAP_REVERSE.get(name.strip())


class ZodiacInfo(BaseModel):
    name: Optional[str] = None
    sign: Optional[int] = None
    degree: Optional[float] = None


class PlanetInput(BaseModel):
    name: str
    sign: Optional[str] = None
    house: Optional[int] = Field(None, ge=1, le=12)
    degree: Optional[float] = None
    ecl_lon: Optional[float] = Field(None, ge=0, lt=360)
    zodiac: Optional[Union[ZodiacInfo, str]] = None
    house_number: Optional[int] = Field(None, ge=1, le=12)
    is_retrograde: bool = False

    @model_validator(mode="after")
    def normalize(self):
        self.name = normalize_planet_name(self.name) or ""
        if not self.name:
            raise ValueError("未知核心行星")
        value: Union[str, int, None] = self.sign
        if value is None and self.zodiac is not None:
            value = self.zodiac.name if isinstance(self.zodiac, ZodiacInfo) else self.zodiac
        if value is None and isinstance(self.zodiac, ZodiacInfo):
            value = self.zodiac.sign
        self.sign = normalize_zodiac(value)
        if not self.sign:
            raise ValueError("必须提供合法星座（Aries...Pisces 或中文星座）")
        if self.house is not None and self.house_number is not None and self.house != self.house_number:
            raise ValueError("house 与 house_number 不可冲突")
        self.house = self.house_number if self.house_number is not None else self.house
        if self.house is None:
            raise ValueError("必须提供宫位 house 或 house_number")
        self.house_number = self.house
        return self


class AspectInput(BaseModel):
    planet1: Optional[str] = None
    planet2: Optional[str] = None
    type: str
    orb: float = Field(0.0, ge=0)

    @model_validator(mode="after")
    def validate_finite_orb(self):
        if not math.isfinite(self.orb):
            raise ValueError("相位容许度必须是有限的非负数")
        return self


class AxisInput(BaseModel):
    ecl_lon: float = Field(..., ge=0, lt=360)


class ChartContext(BaseModel):
    axes: Optional[Dict[str, Union[AxisInput, float]]] = None
    house_cusps: Optional[List[float]] = None
    house_system: Optional[str] = None
    is_day_chart: Optional[bool] = None

    @model_validator(mode="after")
    def validate_context(self):
        if self.axes:
            invalid = set(self.axes) - {"asc", "mc"}
            if invalid:
                raise ValueError("axes 仅支持 asc、mc")
            for axis in self.axes.values():
                lon = axis.ecl_lon if isinstance(axis, AxisInput) else axis
                if not 0 <= lon < 360:
                    raise ValueError("axes 黄经必须在 0 到 360 之间")
        if self.house_cusps is not None:
            if len(self.house_cusps) != 12 or any(not 0 <= lon < 360 for lon in self.house_cusps):
                raise ValueError("house_cusps 必须为 12 个 0 到 360 的黄经")
            if len(set(self.house_cusps)) != 12:
                raise ValueError("house_cusps 必须对应12个不同的宫头")
        return self

    def axis_lon(self, name: str) -> Optional[float]:
        if not self.axes or name not in self.axes:
            return None
        axis = self.axes[name]
        return axis.ecl_lon if isinstance(axis, AxisInput) else axis


class TPESChartData(BaseModel):
    planets: List[PlanetInput] = Field(..., min_length=1)
    aspects: List[AspectInput] = Field(default_factory=list)
    ascendant: Optional[str] = None
    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    chart_context: Optional[ChartContext] = None

    @model_validator(mode="after")
    def validate_chart(self):
        names = [planet.name for planet in self.planets]
        if len(names) != len(set(names)):
            raise ValueError("行星名称不可重复")
        known = set(names)
        aspect_keys = set()
        for aspect in self.aspects:
            aspect.planet1, aspect.planet2 = normalize_planet_name(aspect.planet1 or ""), normalize_planet_name(aspect.planet2 or "")
            if not aspect.planet1 or not aspect.planet2 or aspect.planet1 not in known or aspect.planet2 not in known:
                raise ValueError("相位端点必须存在于 planets 中且为合法行星")
            if aspect.planet1 == aspect.planet2:
                raise ValueError("相位端点必须为两颗不同的行星")
            aspect.type = normalize_aspect_type(aspect.type.strip())
            key = (*sorted((aspect.planet1, aspect.planet2)), aspect.type)
            if key in aspect_keys:
                raise ValueError("同一对行星的同类相位不可重复")
            aspect_keys.add(key)
        self.aspects.sort(key=lambda item: (item.planet1 or "", item.planet2 or "", item.type, item.orb))
        return self


class CareerTPESCalculator:
    """v3 单一生产算法；每个职业模块固定分配预算，合计恒为 100。"""
    budgets = {"career_axes": 45.0, "planet_functions": 20.0, "dignities": 10.0, "aspects": 15.0, "element_modality": 5.0, "sect": 5.0}
    # When evidence density ties, public role (10th) outranks income (2nd),
    # which outranks daily work/service (6th).  The old implementation used
    # numeric house order and therefore silently promoted the 2nd house.
    axis_priority = {10: 0, 2: 1, 6: 2}

    def _types(self, planet: str) -> List[str]:
        return list(self._type_weights(planet))

    def _type_weights(self, planet: str) -> Dict[str, float]:
        values = PLANET_TO_TPES.get(PLANET_NAME_MAP.get(planet, ""), [])
        return {str(values[index]): float(values[index + 1]) for index in range(0, len(values), 2)}

    def _combine_type_weights(self, *planets: str) -> Dict[str, float]:
        combined: Dict[str, float] = defaultdict(float)
        for planet in planets:
            for kind, weight in self._type_weights(planet).items():
                combined[kind] += weight
        return dict(combined)

    def _mapping_weight(self, planet: str) -> float:
        weights = self._type_weights(planet)
        return sum(weights.values()) / len(weights) if weights else 1.0

    def _credit_types(self, scores: Dict[str, float], item: Dict[str, Any]) -> None:
        weights = item.get("type_weights") or {kind: 1.0 for kind in item.get("tpes", ANIMAL_TYPES)}
        total = sum(weights.values()) or 1.0
        for kind, weight in weights.items():
            scores[kind] += item["score"] * weight / total

    def _aspect_type_weights(self, first: str, second: str, effect: str) -> Dict[str, float]:
        combined = self._combine_type_weights(first, second)
        if effect == "resource":
            return combined
        # 紧张相位表达为待整合的发展课题：90% 保持中性背景，仅 10% 投向相关原型。
        neutral = sum(combined.values()) / len(ANIMAL_TYPES)
        return {kind: neutral * .90 + combined.get(kind, 0.0) * .10 for kind in ANIMAL_TYPES}

    def _allocate(self, scores: Dict[str, float], raw: List[Dict[str, Any]], budget: float, fallback: str) -> List[Dict[str, Any]]:
        if not raw:
            raw = [{"label": fallback, "weight": 1.0, "tpes": list(ANIMAL_TYPES), "fallback": True}]
        total = sum(max(0.0, item["weight"]) for item in raw) or 1.0
        for item in raw:
            item["score"] = round(budget * max(0.0, item["weight"]) / total, 6)
        # Round each contribution for audit output, then put the rounding
        # residual back into the final contribution so this module still
        # consumes exactly its declared budget.
        residual = round(budget - sum(item["score"] for item in raw), 6)
        if residual:
            raw[-1]["score"] = round(raw[-1]["score"] + residual, 6)
        for item in raw:
            self._credit_types(scores, item)
        return raw

    def _career_carriers(self, planets: Dict[str, Dict[str, Any]], rulers: set) -> set:
        # A career score must be carried by the career houses or their
        # traditional rulers.  Treating every visible planet as a career
        # carrier diluted the actual responsibility chain.
        return {name for name, planet in planets.items() if planet["house"] in CAREER_HOUSES or name in rulers}

    def _allocate_axis_house(self, scores: Dict[str, float], house: int, base: float, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not entries:
            entries = [{"label": f"第{house}宫缺少行星与可用宫主证据，使用中性职业轴基线", "house": house, "weight": 1.0, "tpes": list(ANIMAL_TYPES), "fallback": True}]
        total_weight = sum(max(0.0, entry["weight"]) for entry in entries) or 1.0
        for entry in entries:
            entry["score"] = round(base * max(0.0, entry["weight"]) / total_weight, 6)
            entry["axis_budget"] = base
        residual = round(base - sum(entry["score"] for entry in entries), 6)
        if residual:
            entries[-1]["score"] = round(entries[-1]["score"] + residual, 6)
        for entry in entries:
            self._credit_types(scores, entry)
        return entries

    def _world_model_capabilities(self, planets: Dict[str, Dict[str, Any]], rulers: Dict[int, str], mc_lon: Optional[float]) -> List[Dict[str, Any]]:
        modules: List[Dict[str, Any]] = []
        ruler_names = set(rulers.values())
        for name, definition in WORLD_MODEL_MODULES.items():
            planet = planets.get(name)
            if not planet:
                continue
            strength = 1.0
            evidence = []
            if planet["house"] in CAREER_HOUSES:
                strength += 0.35
                evidence.append(f"落第{planet['house']}宫职业轴")
            if name in ruler_names:
                ruled_houses = [str(house) for house, ruler in rulers.items() if ruler == name]
                strength += 0.25
                evidence.append(f"为第{'／'.join(ruled_houses)}宫传统宫主")
            dignity, coefficient = DIGNITIES.get(name, {}).get(planet["sign"], ("普通", 1.0))
            strength *= coefficient
            if dignity != "普通":
                evidence.append(f"{planet['sign']}{dignity}")
            if mc_lon is not None and planet.get("ecl_lon") is not None:
                distance = abs((planet["ecl_lon"] - mc_lon + 180) % 360 - 180)
                if distance <= 6:
                    strength += 0.25 * (1 - distance / 6)
                    evidence.append(f"与 MC 相距 {distance:.1f}°")
            modules.append({
                "planet": name,
                "module": definition["module"],
                "english": definition["english"],
                "question": definition["question"],
                "capabilities": definition["capabilities"],
                "strength": round(strength, 4),
                "evidence": evidence or [f"{planet['sign']}第{planet['house']}宫：基础功能线索"],
                "evidence_layer": "auxiliary" if name in OUTER else "classical_seven",
            })
        return sorted(modules, key=lambda item: (-item["strength"], item["planet"]))

    def calculate_tpes_score(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        scores: Dict[str, float] = defaultdict(float)
        planets = {p["name"]: p for p in chart_data["planets"]}
        context = chart_data.get("chart_context") or {}
        cusps = context.get("house_cusps")
        mc = ((context.get("axes") or {}).get("mc"))
        mc_lon = mc.get("ecl_lon") if isinstance(mc, dict) else mc
        fallbacks: List[str] = []
        if not cusps:
            fallbacks.append("未提供 house_cusps：职业宫主星不可判定，仅使用输入 house 的 2/6/10 宫行星。")
        if mc_lon is None:
            fallbacks.append("未提供 MC：不生成 MC 相位贡献。")

        rulers: Dict[int, str] = {}
        axis_evidence: Dict[int, Dict[str, Any]] = {}
        axis_raw: List[Dict[str, Any]] = []
        for house, base in CAREER_HOUSES.items():
            house_entries: List[Dict[str, Any]] = []
            # Only the seven visible planets can establish the classical axis
            # budget. Modern outer planets remain an explicit auxiliary layer.
            occupants = [name for name, p in planets.items() if p["house"] == house and name in TRADITIONAL]
            auxiliary_occupants = [name for name, p in planets.items() if p["house"] == house and name in OUTER]
            evidence = []
            if occupants:
                evidence.append("有落宫行星")
            for name in occupants:
                house_entries.append({"label": f"{house}宫行星 {name}", "house": house, "planet": name, "role": "occupant", "weight": self._mapping_weight(name), "tpes": self._types(name), "type_weights": self._type_weights(name)})
            if cusps:
                sign = ZODIAC_NAMES[int(cusps[house - 1] // 30)]
                ruler = RULERS[sign]
                rulers[house] = ruler
                if ruler in planets:
                    evidence.append("有可用传统宫主星")
                    occupant_entry = next((entry for entry in house_entries if entry["planet"] == ruler), None)
                    if occupant_entry:
                        # Do not count the same planet/house fact twice just
                        # because it is both occupant and ruler.
                        occupant_entry["role"] = "occupant_and_ruler"
                        occupant_entry["label"] += "（兼本宫宫主）"
                    else:
                        house_entries.append({"label": f"{house}宫宫头 {sign} 的传统宫主 {ruler}", "house": house, "planet": ruler, "role": "ruler", "weight": self._mapping_weight(ruler) * .8, "tpes": self._types(ruler), "type_weights": self._type_weights(ruler)})
            if house == 10 and mc_lon is not None:
                evidence.append("职业关联 MC 信息可用")
            axis_evidence[house] = {
                "house": house,
                "evidence_density": len(evidence),
                "evidence": evidence or ["未发现落宫行星、可用宫主星或职业关联 MC 信息"],
                "classical_occupants": occupants,
                "classical_ruler": rulers.get(house),
                "auxiliary_occupants": auxiliary_occupants,
            }
            axis_raw.extend(self._allocate_axis_house(scores, house, base, house_entries))
        breakdown: Dict[str, Dict[str, Any]] = {}
        breakdown["career_axes"] = {"score": 45.0, "contributions": axis_raw}

        function_raw = []
        for name, planet in planets.items():
            if name in TRADITIONAL and (planet["house"] in CAREER_HOUSES or name in set(rulers.values())):
                multiplier = 1.35 if planet["house"] in CAREER_HOUSES else 1.0
                if name in set(rulers.values()): multiplier += .25
                function_raw.append({"label": f"{name} 的职业功能", "planet": name, "house": planet["house"], "weight": multiplier, "tpes": self._types(name), "type_weights": self._type_weights(name)})
            elif name in OUTER and (planet["house"] in CAREER_HOUSES or name in set(rulers.values())):
                function_raw.append({"label": f"{name} 的职业宫辅助功能", "planet": name, "house": planet["house"], "weight": .35, "tpes": self._types(name), "type_weights": self._type_weights(name), "auxiliary": True})
        breakdown["planet_functions"] = {"score": 20.0, "contributions": self._allocate(scores, function_raw, 20.0, "传统七曜信息不足，按可用行星工作风格基线分配")}

        dignity_raw = []
        related = self._career_carriers(planets, set(rulers.values()))
        for name in sorted(related & TRADITIONAL):
            planet = planets[name]
            state, coefficient = DIGNITIES.get(name, {}).get(planet["sign"], ("普通", 1.0))
            dignity_raw.append({"label": f"{name} 在 {planet['sign']}：{state}", "planet": name, "sign": planet["sign"], "dignity": state, "coefficient": coefficient, "weight": coefficient, "tpes": self._types(name), "type_weights": self._type_weights(name)})
        breakdown["dignities"] = {"score": 10.0, "contributions": self._allocate(scores, dignity_raw, 10.0, "无相关传统七曜，以中性尊贵基线分配")}

        carriers = self._career_carriers(planets, set(rulers.values()))
        aspect_raw = []
        major = {"合相": "resource", "三分相": "resource", "六分相": "resource", "四分相": "development_tension", "对分相": "development_tension"}
        for item in chart_data.get("aspects", []):
            kind = normalize_aspect_type(item["type"])
            p1, p2 = item["planet1"], item["planet2"]
            # Modern outer-planet aspects are retained nowhere in the core
            # budget; they can only be reported as auxiliary context.
            if kind not in major or p1 in OUTER or p2 in OUTER or (p1 not in carriers and p2 not in carriers):
                continue
            max_orb = 7.0 if {p1, p2} & {"Sun", "Moon"} else 5.0
            factor = max(0.0, 1 - item["orb"] / max_orb)
            if factor:
                effect = major[kind]
                aspect_raw.append({"label": f"{p1}-{p2} {kind}", "planets": [p1, p2], "orb": item["orb"], "max_orb": max_orb, "orb_factor": round(factor, 6), "effect": effect, "weight": factor, "tpes": sorted(set(self._types(p1) + self._types(p2))), "type_weights": self._aspect_type_weights(p1, p2, effect)})
        if mc_lon is not None:
            angles = {0: "合相", 60: "六分相", 90: "四分相", 120: "三分相", 180: "对分相"}
            for name, planet in planets.items():
                if name in OUTER or (name not in carriers) or planet.get("ecl_lon") is None:
                    continue
                distance = abs((planet["ecl_lon"] - mc_lon + 180) % 360 - 180)
                angle = min(angles, key=lambda value: abs(value - distance))
                orb = abs(distance - angle)
                max_orb = 6.0 if angle in (0, 180) else 4.0
                factor = max(0.0, 1 - orb / max_orb)
                if factor:
                    kind = angles[angle]
                    effect = major[kind]
                    aspect_raw.append({"label": f"{name}-MC {kind}", "planets": [name, "MC"], "orb": round(orb, 6), "max_orb": max_orb, "orb_factor": round(factor, 6), "effect": effect, "weight": factor, "tpes": self._types(name), "type_weights": self._type_weights(name) if effect == "resource" else self._aspect_type_weights(name, name, effect)})
        breakdown["aspects"] = {"score": 15.0, "contributions": self._allocate(scores, aspect_raw, 15.0, "无有效职业关联主要相位，按可用职业载体基线分配")}

        style_raw = []
        for name in sorted(carriers & TRADITIONAL):
            sign = planets[name]["sign"]
            element, modality = ELEMENTS[sign], MODALITIES[sign]
            types = sorted(set(ELEMENT_TO_TPES[element] + MODALITY_TO_TPES[modality]))
            style_raw.append({"label": f"{name} 的{element}/{modality}工作风格", "planet": name, "element": element, "modality": modality, "weight": 1.0, "tpes": types})
        breakdown["element_modality"] = {"score": 5.0, "contributions": self._allocate(scores, style_raw, 5.0, "无职业载体，按工作风格基线分配")}

        explicit_sect = context.get("is_day_chart")
        if explicit_sect is None:
            sun = planets.get("Sun")
            is_day = bool(sun and 7 <= sun["house"] <= 12)
            fallbacks.append("未提供 is_day_chart：按太阳位于 7-12 宫判定昼夜盘。")
        else:
            is_day = explicit_sect
        favored = {"Sun", "Jupiter", "Saturn"} if is_day else {"Moon", "Venus", "Mars"}
        sect_raw = [{"label": f"{'日间' if is_day else '夜间'}盘的 {name} 轻度支持", "planet": name, "is_day_chart": is_day, "weight": 1.0, "tpes": self._types(name)} for name in sorted(favored & set(planets))]
        breakdown["sect"] = {"score": 5.0, "contributions": self._allocate(scores, sect_raw, 5.0, "对应 sect 行星缺失，按中性工作风格基线分配")}

        rounded_scores = {kind: round(scores[kind], 4) for kind in ANIMAL_TYPES}
        # The public contract exposes four decimal places. Reconcile that
        # final display rounding as well, otherwise a valid 100-point budget
        # can appear as 99.9999/100.0001 to downstream consumers.
        display_residual = round(100.0 - sum(rounded_scores.values()), 4)
        if display_residual:
            display_target = max(ANIMAL_TYPES, key=lambda kind: (rounded_scores[kind], -ANIMAL_TYPES.index(kind)))
            rounded_scores[display_target] = round(rounded_scores[display_target] + display_residual, 4)
        ranked_types = sorted(ANIMAL_TYPES, key=lambda kind: (-rounded_scores[kind], ANIMAL_TYPES.index(kind)))
        final_type = ranked_types[0]
        type_gap = round(rounded_scores[ranked_types[0]] - rounded_scores[ranked_types[1]], 4)
        type_distinction_level = "区分明显" if type_gap >= 5 else "区分可见" if type_gap >= 2 else "区分接近"
        axis_order = sorted(CAREER_HOUSES, key=lambda house: (-axis_evidence[house]["evidence_density"], self.axis_priority[house]))
        valid_career_aspect_count = sum(1 for item in aspect_raw if not item.get("fallback"))
        present_core_planets = [name for name in CORE_PERSONAL_PLANETS if name in planets]
        coverage_points = len(present_core_planets) + int(bool(cusps)) + int(mc_lon is not None) + int(explicit_sect is not None) + int(valid_career_aspect_count > 0)
        coverage_ratio = round(coverage_points / (len(CORE_PERSONAL_PLANETS) + 4), 4)
        coverage_level = "输入完整" if coverage_ratio >= .85 else "输入较完整" if coverage_ratio >= .60 else "输入基础" if coverage_ratio >= .35 else "输入有限"
        world_model_capabilities = self._world_model_capabilities(planets, rulers, mc_lon)
        classical_capability_modules = [module for module in world_model_capabilities if module.get("evidence_layer") == "classical_seven"]
        top_capabilities = [capability for module in classical_capability_modules[:3] for capability in module["capabilities"][:1]] or [c["label"] for c in sorted(breakdown["planet_functions"]["contributions"], key=lambda c: c["score"], reverse=True)[:3]]
        classical_axis_audit = []
        for house in (10, 2, 6):
            ruler = rulers.get(house)
            ruler_data = planets.get(ruler) if ruler else None
            classical_axis_audit.append({
                "house": house,
                "role": {10: "public_role", 2: "income_and_resources", 6: "daily_work_and_service"}[house],
                "ruler": ruler,
                "ruler_sign": ruler_data.get("sign") if ruler_data else None,
                "ruler_house": ruler_data.get("house") if ruler_data else None,
                "ruler_dignity": DIGNITIES.get(ruler, {}).get(ruler_data.get("sign"), ("普通", 1.0))[0] if ruler_data else None,
                "ruler_retrograde": bool(ruler_data.get("is_retrograde", False)) if ruler_data else None,
                "dignity_source": "coarse_domicile_exaltation_detriment_fall_map",
                "occupants": axis_evidence[house]["classical_occupants"],
                "auxiliary_occupants": axis_evidence[house]["auxiliary_occupants"],
            })
        supporting_house_audit = []
        for house in (1, 7, 11):
            if not cusps:
                supporting_house_audit.append({"house": house, "ruler": None, "status": "deferred_without_house_cusps"})
                continue
            sign = ZODIAC_NAMES[int(cusps[house - 1] // 30)]
            ruler = RULERS[sign]
            ruler_data = planets.get(ruler)
            supporting_house_audit.append({
                "house": house,
                "cusp_sign": sign,
                "ruler": ruler,
                "ruler_sign": ruler_data.get("sign") if ruler_data else None,
                "ruler_house": ruler_data.get("house") if ruler_data else None,
                "ruler_dignity": DIGNITIES.get(ruler, {}).get(ruler_data.get("sign"), ("普通", 1.0))[0] if ruler_data else None,
                "dignity_source": "coarse_domicile_exaltation_detriment_fall_map",
                "purpose": {1: "agency_and_chart_ruler", 7: "clients_partners_and_opponents", 11: "allies_networks_and_gains"}[house],
            })
        classical_evidence_chain = []
        chain_inferences = {
            10: "事业/公共角色通过10宫主落点进入具体资源与交付领域",
            2: "收入与资源通过2宫主落点连接家庭、基础或固定投入领域",
            6: "日常工作与服务通过6宫主落点反映工作负荷、流程与可持续性",
        }
        for item in classical_axis_audit:
            if item.get("ruler") is None or item.get("ruler_house") is None:
                continue
            classical_evidence_chain.append({
                "fact": f"第{item['house']}宫宫主{item['ruler']}落第{item['ruler_house']}宫{item['ruler_sign']}",
                "rule": f"第{item['house']}宫负责{item['role']}; 宫主落宫决定责任的交付场景",
                "inference": chain_inferences[item["house"]],
                "grade": "B",
            })
        summary = f"{final_type}呈现为职业工作风格画像，侧重在岗位场景中可培养、可调整的偏好，而非固定天赋或职业断言。"
        process = ["# TPES 职业轴 v3.2 计算过程", "职业权重固定为：职业宫轴45、行星功能20、尊贵10、相位15、元素/模式5、sect5，总计100。", "古典审计优先顺序：10宫公共角色 → 2宫收入资源 → 6宫日常工作；现代外行星仅作辅助，不进入核心预算。"]
        for name, module in breakdown.items():
            process.append(f"## {name}: {module['score']}分")
            for contribution in module["contributions"]:
                process.append(f"- {contribution['label']}：{contribution['score']:.4f}分")
        input_coverage = {"core_personal_planets": {"present": present_core_planets, "count": len(present_core_planets), "total": len(CORE_PERSONAL_PLANETS)}, "has_house_cusps": bool(cusps), "has_mc": mc_lon is not None, "has_exact_sect": explicit_sect is not None, "valid_career_aspect_count": valid_career_aspect_count, "coverage_ratio": coverage_ratio, "coverage_level": coverage_level, "fallbacks": fallbacks}
        interpretation_limits = {"input_coverage": coverage_level, "type_distinction": {"top1": ranked_types[0], "top2": ranked_types[1], "gap": type_gap, "level": type_distinction_level}, "notice": "输入覆盖与类型区分度仅说明本次计算资料的完整度和类型分数差距，不是预测置信度，也不是职业胜任力、适配度或成功概率评估。", "classical_layer": "职业核心判断必须回到10宫、10宫主、2/6宫链、行星状态、sect、相位与接纳；TPES类型只作现代辅助标签。", "outer_planets": "天王、海王、冥王不进入职业核心预算，仅保留为辅助背景。"}
        return {"total_score": 100.0, "scores": rounded_scores, "final_type": final_type, "type_score": rounded_scores[final_type], "description": summary, "career_suggestions": ["将优势理解为可练习的工作方式，并在实际反馈中校准。", "优先选择能使用主要职业轴资源、同时容纳发展张力的任务环境。"], "calculation_process": "\n".join(process), "career_profile": {"summary": summary, "primary_axis": f"第{axis_order[0]}宫职业轴（证据密度最高；古典优先顺序）", "secondary_axis": f"第{axis_order[1]}宫职业轴（证据密度次高；古典优先顺序）", "axis_evidence": [axis_evidence[house] for house in axis_order], "classical_axis_audit": classical_axis_audit, "supporting_house_audit": supporting_house_audit, "classical_evidence_chain": classical_evidence_chain, "top_capabilities": top_capabilities, "development_focus": [c["label"] for c in breakdown["aspects"]["contributions"] if c.get("effect") == "development_tension"] or ["通过具体工作反馈持续校准职业风格。"]}, "world_model_capabilities": world_model_capabilities, "capability_model_notice": "行星隐喻用于组织可训练的认知与工作能力线索，不等同于已验证技能、学历资格或职业胜任力。", "score_breakdown": breakdown, "input_coverage": input_coverage, "interpretation_limits": interpretation_limits, "day_night": "日间盘" if is_day else "夜间盘", "planet_score": 20.0, "element_score": 5.0, "aspect_score": 15.0, "correction_score": 15.0}


TPESCalculator = CareerTPESCalculator


def _chart_to_tpes_payload(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Adapt the local natal envelope to TPES' explicit context contract."""
    source = chart.get("chart_facts") if isinstance(chart.get("chart_facts"), dict) else chart
    placements = source.get("placements") or source.get("planets") or {}
    if not isinstance(placements, dict):
        raise ValueError("TPES chart payload must contain placements/planets as a mapping")
    planets = []
    for name, raw in placements.items():
        if not isinstance(raw, dict):
            continue
        if normalize_planet_name(str(name)) is None:
            # The natal engine also exposes Chiron, Fortune and asteroids;
            # TPES is intentionally limited to its declared core planets.
            continue
        sign = raw.get("sign") or raw.get("zodiac")
        if isinstance(sign, dict):
            sign = sign.get("name") or sign.get("sign")
        raw_house = raw.get("house") if raw.get("house") is not None else raw.get("house_number")
        if raw.get("house") is not None and raw.get("house_number") is not None and raw.get("house") != raw.get("house_number"):
            raise ValueError(f"行星{name}的 house 与 house_number 不可冲突")
        house = raw_house
        longitude = raw.get("ecl_lon", raw.get("ecliptic_longitude"))
        if house is None or sign is None:
            continue
        planets.append({
            "name": normalize_planet_name(str(name)),
            "sign": sign,
            "house": house,
            "ecl_lon": longitude,
            "is_retrograde": bool(raw.get("is_retrograde", False)),
        })
    houses = source.get("houses") or {}
    context = {
        "house_cusps": houses.get("house_cusps") if isinstance(houses, dict) else None,
        "house_system": source.get("house_system"),
        "is_day_chart": source.get("is_day_chart"),
    }
    if isinstance(houses, dict):
        context["axes"] = {key: value for key, value in (("asc", houses.get("asc")), ("mc", houses.get("mc"))) if value is not None}
    aspects = []
    for raw in source.get("aspects", []) or []:
        if isinstance(raw, dict):
            p1 = normalize_planet_name(str(raw.get("planet1", "")))
            p2 = normalize_planet_name(str(raw.get("planet2", "")))
            if p1 and p2 and p1 != p2 and {p1, p2} <= {item["name"] for item in planets}:
                aspects.append({"planet1": p1, "planet2": p2, "type": raw.get("type", ""), "orb": raw.get("orb", 0)})
    return {"planets": planets, "aspects": aspects, "chart_context": context}


def calculate_tpes(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate the migrated TPES career insight for a natal chart."""
    payload = _chart_to_tpes_payload(chart)
    validated = TPESChartData.model_validate(payload).model_dump()
    result = CareerTPESCalculator().calculate_tpes_score(validated)
    result["algorithm_version"] = "tpes-career-v3.2"
    result["calculation_process_format"] = "markdown"
    result["interpretation_limits"]["auxiliary_layer"] = (
        "TPES 是基于星盘符号的职业工作风格洞察，不是职业胜任力、适配度、成功概率或就业预测。"
    )
    return result


calculate_career_insight = calculate_tpes
TPESCalculator = CareerTPESCalculator

__all__ = [
    "ANIMAL_TYPES", "CareerTPESCalculator", "TPESCalculator", "TPESChartData",
    "calculate_tpes", "calculate_career_insight", "normalize_zodiac", "normalize_planet_name",
]
