# E/I 能量分布计算模块 - 荣格合规性重构版
# 核心原则：
# 1. 力量与倾向分离：庙旺弱仅影响权重，不改变E/I倾向
# 2. 修正项互斥：同一属性修正仅计算1次（星座修正已含阴阳，不再重复）
# 3. 全局修正由calculator.py统一处理（乘法×1.05）
# 4. 对称性约束：所有修正项E+I=0
# 5. 权重层级统治：三巨头(Sun/Moon/Asc)通过权重配置体现统治力，无额外乘法倍率
# 6. 得时行星规则：日生人(太阳7-12宫)日月木土得时加权，夜生人(太阳1-6宫)月金火得时加权
from typing import Dict, Any, List, Tuple, Optional
from .constants import (
    PLANET_EI_BASE, ZODIAC_EI_CORRECTION, HOUSE_EI_CORRECTION,
    PLANET_EXALTATION, PLANET_DETRIMENT, PLANET_RULERSHIP, PLANET_FALL,
    PLANET_STRENGTH_WEIGHT, PLANET_WEIGHT_CONFIG, RULER_WEIGHT_OVERRIDE,
    ASC_RULERS, CORE_BODIES, RETROGRADE_FACTOR, PERSONAL_PLANETS,
    HOUSE_STRENGTH_WEIGHT, ZODIAC_DOMINANT_FUNCTION,
    TRANSPERSONAL_PLANETS, TRANSPERSONAL_ACTIVATION_ASPECTS,
    TRANSPERSONAL_ACTIVATION_ORB, TRANSPERSONAL_ASPECT_WEIGHT,
    TRANSPERSONAL_ACTIVATION_PLANETS, ASPECT_TYPE_MAP,
    FAVORABLE_PLANETS_DAY, FAVORABLE_PLANETS_NIGHT, FAVORABLE_WEIGHT
)


def _normalize_aspect_type(aspect_type: str) -> str:
    return ASPECT_TYPE_MAP.get(aspect_type, aspect_type)


def check_transpersonal_activation(
    body: str,
    aspects: List[Dict[str, Any]],
    rules: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """检查世代行星是否被个人行星相位激活（荣格合规性：集体无意识需个体意识桥梁）
    
    激活标准：三王星仅与个人行星(Sun/Moon/Mercury/Venus/Mars)形成紧密相位时纳入计算
    激活相位类型：合相、刑冲(四分/对分)、拱相(三分)、六合，容许度≤3°
    相位权重：合相×1.0，刑冲/拱相/六合×0.8
    
    Returns:
        Dict with keys:
        - 'activated': bool - 是否被激活
        - 'aspect_weight': float - 相位权重(0.8或1.0)，未激活时为0
        - 'activating_aspects': List - 激活相位详情
    """
    if body not in TRANSPERSONAL_PLANETS:
        return {'activated': True, 'aspect_weight': 1.0, 'activating_aspects': []}

    activation_aspects = rules.get('transpersonal_activation_aspects', TRANSPERSONAL_ACTIVATION_ASPECTS) if rules else TRANSPERSONAL_ACTIVATION_ASPECTS
    activation_orb = rules.get('transpersonal_activation_orb', TRANSPERSONAL_ACTIVATION_ORB) if rules else TRANSPERSONAL_ACTIVATION_ORB
    aspect_weights = rules.get('transpersonal_aspect_weight', TRANSPERSONAL_ASPECT_WEIGHT) if rules else TRANSPERSONAL_ASPECT_WEIGHT
    activation_planets = rules.get('transpersonal_activation_planets', TRANSPERSONAL_ACTIVATION_PLANETS) if rules else TRANSPERSONAL_ACTIVATION_PLANETS

    activating_aspects = []
    best_weight = 0.0

    for aspect in aspects:
        p1 = aspect.get('planet1', '')
        p2 = aspect.get('planet2', '')
        aspect_type_raw = aspect.get('type', '')
        orb = abs(aspect.get('orb', 0))

        cn_type = _normalize_aspect_type(aspect_type_raw)

        other_planet = None
        if p1 == body and p2 in activation_planets:
            other_planet = p2
        elif p2 == body and p1 in activation_planets:
            other_planet = p1

        if other_planet is None:
            continue

        if cn_type not in activation_aspects:
            continue

        if orb > activation_orb:
            continue

        weight = aspect_weights.get(cn_type, 0.8)
        activating_aspects.append({
            'transpersonal': body,
            'personal': other_planet,
            'aspect_type': cn_type,
            'orb': orb,
            'aspect_weight': weight
        })

        if weight > best_weight:
            best_weight = weight

    activated = len(activating_aspects) > 0

    return {
        'activated': activated,
        'aspect_weight': best_weight if activated else 0.0,
        'activating_aspects': activating_aspects
    }


def _get_ei_rules(rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取E/I规则（默认或自定义）"""
    if rules:
        return {
            'planet_ei_base': rules.get('planet_ei_base', PLANET_EI_BASE),
            'zodiac_ei_correction': rules.get('zodiac_ei_correction', ZODIAC_EI_CORRECTION),
            'house_ei_correction': rules.get('house_ei_correction', HOUSE_EI_CORRECTION),
            'planet_weight_config': rules.get('planet_weight_config', PLANET_WEIGHT_CONFIG),
            'ruler_weight_override': rules.get('ruler_weight_override', RULER_WEIGHT_OVERRIDE),
            'planet_exaltation': rules.get('planet_exaltation', PLANET_EXALTATION),
            'planet_detriment': rules.get('planet_detriment', PLANET_DETRIMENT),
            'planet_fall': rules.get('planet_fall', PLANET_FALL),
            'planet_rulership': rules.get('planet_rulership', PLANET_RULERSHIP),
            'asc_rulers': rules.get('asc_rulers', ASC_RULERS),
            'retrograde_factor': rules.get('retrograde_factor', RETROGRADE_FACTOR),
            'planet_strength_weight': rules.get('planet_strength_weight', PLANET_STRENGTH_WEIGHT),
            'house_strength_weight': rules.get('house_strength_weight', HOUSE_STRENGTH_WEIGHT),
        }
    return {
        'planet_ei_base': PLANET_EI_BASE,
        'zodiac_ei_correction': ZODIAC_EI_CORRECTION,
        'house_ei_correction': HOUSE_EI_CORRECTION,
        'planet_weight_config': PLANET_WEIGHT_CONFIG,
        'ruler_weight_override': RULER_WEIGHT_OVERRIDE,
        'planet_exaltation': PLANET_EXALTATION,
        'planet_detriment': PLANET_DETRIMENT,
        'planet_fall': PLANET_FALL,
        'planet_rulership': PLANET_RULERSHIP,
        'asc_rulers': ASC_RULERS,
        'retrograde_factor': RETROGRADE_FACTOR,
        'planet_strength_weight': PLANET_STRENGTH_WEIGHT,
        'house_strength_weight': HOUSE_STRENGTH_WEIGHT,
    }


def get_zodiac_ei_correction(zodiac: str, rules: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    r = _get_ei_rules(rules)
    return r['zodiac_ei_correction'].get(zodiac, {'E': 0, 'I': 0})


def get_house_ei_correction(house: int, rules: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    r = _get_ei_rules(rules)
    # 尝试整数键查找，再尝试字符串键查找
    house_data = r['house_ei_correction'].get(house)
    if house_data is None:
        house_data = r['house_ei_correction'].get(str(house))
    return house_data if house_data is not None else {'E': 0, 'I': 0}


def get_planet_dignity_status(body: str, zodiac: str, rules: Optional[Dict[str, Any]] = None) -> str:
    """判断行星在星座中的力量状态（入庙/旺相/失势/落陷/普通）"""
    r = _get_ei_rules(rules)
    if body == 'Ascendant':
        return 'normal'

    if body in r['planet_rulership']:
        if zodiac in r['planet_rulership'][body]:
            return 'exaltation'

    exaltation = r['planet_exaltation'].get(body, '')
    if zodiac == exaltation:
        return 'exalted'

    detriment = r['planet_detriment'].get(body, '')
    if isinstance(detriment, list):
        if zodiac in detriment:
            return 'detriment'
    elif zodiac == detriment:
        return 'detriment'

    fall = r['planet_fall'].get(body, '')
    if zodiac == fall:
        return 'fall'

    return 'normal'


def get_strength_coefficient(dignity: str, body: str, is_retrograde: bool, rules: Optional[Dict[str, Any]] = None, house: int = 1) -> float:
    """力量系数已废弃，始终返回1.0
    
    历史：曾经计算庙旺弱×逆行系数，但根据荣格合规性重构原则，
    力量系数不再影响MBTI计算，倾向完全由落座+落宫+相位决定
    """
    return 1.0


def get_weight_coefficient(body: str, is_ruler: bool, sun_house: int, rules: Optional[Dict[str, Any]] = None, dimension: str = 'EI', dimension_base_weight: Optional[float] = None) -> float:
    """计算行星权重系数（荣格合规性重构 - 严格权重叠加顺序 + 得时行星规则）
    
    权重叠加顺序（严格按用户规则优先级）：
    步骤1：基础权重 + 命主星加成（加法，仅E/I和J/P维度，上限3.3，不突破太阳基础权重3.0）
    步骤2：维度差异化权重（各维度PLANET_*_BASE.weight已含差异化，直接作为基础权重使用）
    步骤3：得时行星规则（日生人日月木土×1.1，夜生人月金火×1.1）
    
    优先级规则：得时行星规则 > 维度差异化权重 > 基础权重 > 星座修正值 > 命主星加成
    
    命主星规则边界：
    - 守护体系：古典占星七星守护体系，不纳入三王星
    - 加成规则：仅对E/I、J/P维度生效，在基础权重上+0.3
    - 加成后权重上限固定为3.3，不得突破太阳的基础权重
    
    得时行星规则（古典占星日夜盘体系）：
    - 日生人（太阳在7-12宫）：太阳、月亮、木星、土星为得时行星，权重×1.1
    - 夜生人（太阳在1-6宫）：月亮、金星、火星为得时行星，权重×1.1
    - 原理：古典占星认为行星在日夜盘中的力量不同，得时行星在对应时段力量更强
    
    dimension: 'EI'|'SN'|'FT'|'JP'，默认'EI'
    dimension_base_weight: 维度差异化基础权重，如未提供则使用PLANET_WEIGHT_CONFIG
    """
    r = _get_ei_rules(rules)

    if body == 'Ascendant':
        config = r['planet_weight_config'].get('Ascendant', {'base': 2.6, 'max': 2.9})
        weight = config['base']
        return min(weight, config['max'])

    SUN_BASE_WEIGHT = 3.0
    RULER_ABSOLUTE_MAX = 3.3

    if dimension_base_weight is not None:
        weight = dimension_base_weight
    else:
        config = r['planet_weight_config'].get(body, {'base': 1.0, 'max': 1.3})
        weight = config['base']

    if is_ruler and dimension in ('EI', 'JP'):
        ruler_config = r['ruler_weight_override']
        ruler_bonus = ruler_config.get('ruler_bonus', 0.3)
        ruler_max = ruler_config.get('max', RULER_ABSOLUTE_MAX)
        weight = min(weight + ruler_bonus, ruler_max, SUN_BASE_WEIGHT)

    is_day_chart = sun_house in [7, 8, 9, 10, 11, 12]

    favorable_day = rules.get('favorable_planets_day', FAVORABLE_PLANETS_DAY) if rules else FAVORABLE_PLANETS_DAY
    favorable_night = rules.get('favorable_planets_night', FAVORABLE_PLANETS_NIGHT) if rules else FAVORABLE_PLANETS_NIGHT
    favorable_weight = rules.get('favorable_weight', FAVORABLE_WEIGHT) if rules else FAVORABLE_WEIGHT

    if is_day_chart and body in favorable_day:
        weight *= favorable_weight
    elif not is_day_chart and body in favorable_night:
        weight *= favorable_weight

    config = r['planet_weight_config'].get(body, {})
    planet_max = config.get('max', RULER_ABSOLUTE_MAX)
    return min(weight, planet_max)


def get_weight_breakdown(body: str, is_ruler: bool, sun_house: int, rules: Optional[Dict[str, Any]] = None, dimension: str = 'EI', dimension_base_weight: Optional[float] = None) -> Dict[str, Any]:
    """计算行星权重系数并返回分解信息（用于计算过程展示）
    
    Returns:
        Dict containing:
        - weight: 最终权重系数
        - base_weight: 基础权重
        - ruler_bonus: 命主星加成（0或0.3）
        - is_favorable: 是否得时行星
        - favorable_type: 'day'/'night'/None
        - favorable_multiplier: 得时乘数（1.0或1.1）
    """
    r = _get_ei_rules(rules)

    if body == 'Ascendant':
        config = r['planet_weight_config'].get('Ascendant', {'base': 2.6, 'max': 2.9})
        return {
            'weight': min(config['base'], config['max']),
            'base_weight': config['base'],
            'ruler_bonus': 0,
            'is_favorable': False,
            'favorable_type': None,
            'favorable_multiplier': 1.0,
        }

    SUN_BASE_WEIGHT = 3.0
    RULER_ABSOLUTE_MAX = 3.3

    if dimension_base_weight is not None:
        base_weight = dimension_base_weight
    else:
        config = r['planet_weight_config'].get(body, {'base': 1.0, 'max': 1.3})
        base_weight = config['base']

    ruler_bonus = 0.0
    weight = base_weight

    if is_ruler and dimension in ('EI', 'JP'):
        ruler_config = r['ruler_weight_override']
        ruler_bonus = ruler_config.get('ruler_bonus', 0.3)
        ruler_max = ruler_config.get('max', RULER_ABSOLUTE_MAX)
        weight = min(weight + ruler_bonus, ruler_max, SUN_BASE_WEIGHT)

    is_day_chart = sun_house in [7, 8, 9, 10, 11, 12]

    favorable_day = rules.get('favorable_planets_day', FAVORABLE_PLANETS_DAY) if rules else FAVORABLE_PLANETS_DAY
    favorable_night = rules.get('favorable_planets_night', FAVORABLE_PLANETS_NIGHT) if rules else FAVORABLE_PLANETS_NIGHT
    favorable_weight = rules.get('favorable_weight', FAVORABLE_WEIGHT) if rules else FAVORABLE_WEIGHT

    is_favorable = False
    favorable_type = None
    favorable_multiplier = 1.0

    if is_day_chart and body in favorable_day:
        is_favorable = True
        favorable_type = 'day'
        favorable_multiplier = favorable_weight
        weight *= favorable_weight
    elif not is_day_chart and body in favorable_night:
        is_favorable = True
        favorable_type = 'night'
        favorable_multiplier = favorable_weight
        weight *= favorable_weight

    config = r['planet_weight_config'].get(body, {})
    planet_max = config.get('max', RULER_ABSOLUTE_MAX)
    final_weight = min(weight, planet_max)

    return {
        'weight': final_weight,
        'base_weight': base_weight,
        'ruler_bonus': ruler_bonus,
        'is_favorable': is_favorable,
        'favorable_type': favorable_type,
        'favorable_multiplier': favorable_multiplier,
    }


def get_planet_house(planets: List[Dict[str, Any]], planet_name: str) -> int:
    planet = next((p for p in planets if p['name'] == planet_name), None)
    return planet.get('house', 1) if planet else 1


def get_dominant_function_multiplier(body: str, zodiac: str, dimension: str, rules: Optional[Dict[str, Any]] = None) -> float:
    """获取主导功能权重倍率（已废弃，始终返回1.0）
    
    历史：曾经根据太阳/月亮/上升落座给予3倍权重
    新版：三巨头通过权重配置直接体现统治力（太阳×3.0 > 月亮×2.8 > 上升×2.6）
    不再使用额外乘法倍率，避免重复加权
    """
    return 1.0


def determine_dominant_functions(sun_zodiac: str, moon_zodiac: str, ascendant: str, rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """判定星盘的主导功能层级（荣格合规性核心架构）
    
    基于太阳/月亮/上升的落座，确定主导功能方向：
    - 太阳落座 → 意识核心功能定向
    - 月亮落座 → 潜意识支撑功能定向
    - 上升落座 → 外倾表达方式定向
    
    Returns:
        Dict containing dominant function analysis for each dimension
    """
    zodiac_func = rules.get('zodiac_dominant_function', ZODIAC_DOMINANT_FUNCTION) if rules else ZODIAC_DOMINANT_FUNCTION
    
    sun_func = zodiac_func.get(sun_zodiac, {'perception': 'S', 'judgment': 'T', 'attitude': 'e'})
    moon_func = zodiac_func.get(moon_zodiac, {'perception': 'S', 'judgment': 'F', 'attitude': 'i'})
    asc_func = zodiac_func.get(ascendant, {'perception': 'S', 'judgment': 'F', 'attitude': 'e'})
    
    return {
        'sun_zodiac': sun_zodiac,
        'moon_zodiac': moon_zodiac,
        'ascendant': ascendant,
        'sun_function': sun_func,
        'moon_function': moon_func,
        'asc_function': asc_func,
        'ei_dominant': 'E' if sun_func['attitude'] == 'e' else 'I',
        'sn_dominant': sun_func['perception'],
        'ft_dominant': sun_func['judgment'],
        'jp_dominant': 'J' if sun_func['judgment'] in ('T', 'F') else 'P',
    }


def calculate_body_ei_score(
    body: str,
    planet: Dict[str, Any],
    ascendant: str,
    is_retrograde: bool,
    sun_house: int,
    rules: Optional[Dict[str, Any]] = None,
    transpersonal_aspect_weight: float = 1.0
) -> Dict[str, Any]:
    """计算单个天体的E/I得分（荣格合规性重构版）
    计算过程：
    1. 基础分值：从PLANET_EI_BASE获取（E+I=10）
    2. 星座修正：从ZODIAC_EI_CORRECTION获取（已含阴阳，不重复）
    3. 宫位修正：从HOUSE_EI_CORRECTION获取（降低影响）
    4. 权重系数：base×ruler×day/night（与力量分离，受max约束）
    5. 世代行星相位权重：激活后按相位类型加权(合相1.0/其他0.8)
    6. 日夜修正：日间盘(太阳7-12宫)E×1.05，夜间盘(太阳1-6宫)I×1.05
    7. 最终得分 = (基础分值 + 星座修正 + 宫位修正) × 权重系数 × 世代行星相位权重 × 日夜修正
    """
    r = _get_ei_rules(rules)
    zodiac = planet.get('zodiac', {}).get('name', '') if body != 'Ascendant' else ascendant
    house = planet.get('house', 1) if body != 'Ascendant' else 1

    base = r['planet_ei_base'].get(body, {'E': 5, 'I': 5, 'weight': 1.0})
    base_e = base['E']
    base_i = base['I']
    dim_base_weight = base.get('weight', 1.0)

    chart_ruler = r['asc_rulers'].get(ascendant, 'Sun')
    is_ruler = (body == chart_ruler)

    wb = get_weight_breakdown(body, is_ruler, sun_house, rules, dimension='EI', dimension_base_weight=dim_base_weight)
    weight_coeff = wb['weight']

    zodiac_corr = get_zodiac_ei_correction(zodiac, rules)

    if body == 'Ascendant':
        house_corr = {'E': 0, 'I': 0}
    else:
        house_corr = get_house_ei_correction(house, rules)

    raw_e = base_e + zodiac_corr['E'] + house_corr['E']
    raw_i = base_i + zodiac_corr['I'] + house_corr['I']

    is_day_chart = sun_house in [7, 8, 9, 10, 11, 12]
    day_corr_e = 1.05 if is_day_chart else 1.0
    day_corr_i = 1.05 if not is_day_chart else 1.0

    total_e = max(0, raw_e * weight_coeff * transpersonal_aspect_weight * day_corr_e)
    total_i = max(0, raw_i * weight_coeff * transpersonal_aspect_weight * day_corr_i)

    weight_parts = [f'{wb["base_weight"]:.1f}']
    if wb['ruler_bonus'] > 0:
        weight_parts.append(f'+{wb["ruler_bonus"]:.1f}(命主星)')
    if wb['is_favorable']:
        fav_label = '日生得时' if wb['favorable_type'] == 'day' else '夜生得时'
        weight_parts.append(f'×{wb["favorable_multiplier"]:.1f}({fav_label})')
    weight_desc = ''.join(weight_parts)

    day_desc = f' × {day_corr_e}(日夜)' if day_corr_e > 1.0 else ''
    tp_desc = f' × {transpersonal_aspect_weight}(世代相位)' if transpersonal_aspect_weight < 1.0 else ''

    return {
        'body': body,
        'zodiac': zodiac,
        'house': house,
        'is_ruler': is_ruler,
        'base': base,
        'zodiac_corr': zodiac_corr,
        'house_corr': house_corr,
        'weight_coeff': round(weight_coeff, 4),
        'weight_breakdown': wb,
        'day_night_corr': {'E': day_corr_e, 'I': day_corr_i},
        'transpersonal_aspect_weight': transpersonal_aspect_weight,
        'calculation_process': (
            f'E: {base_e}+({zodiac_corr["E"]:+.1f})+({house_corr["E"]:+.1f}) = {raw_e:.1f} '
            f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc}{day_desc} = {round(total_e, 2)} | '
            f'I: {base_i}+({zodiac_corr["I"]:+.1f})+({house_corr["I"]:+.1f}) = {raw_i:.1f} '
            f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(total_i, 2)}'
        ),
        'final_e': round(total_e, 2),
        'final_i': round(total_i, 2)
    }


def calculate_energy_distribution(
    planets: List[Dict[str, Any]],
    ascendant: str,
    scores: Dict[str, float],
    calculation_process: Dict[str, List],
    rules: Optional[Dict[str, Any]] = None,
    aspects: Optional[List[Dict[str, Any]]] = None
) -> None:
    """计算E/I能量分布 - 荣格合规性重构版
    核心改动：
    1. 删除阴阳重复修正（星座修正已含阴阳）
    2. 权重系数与力量系数完全分离
    3. 去除庙旺弱偏移和逆行修正
    4. 降低宫位修正影响
    5. 权重层级统治：三巨头通过权重配置体现统治力，无额外乘法倍率
    6. 世代行星相位激活：三王星仅与个人行星紧密相位时纳入
    7. 全局修正由calculator.py统一乘法处理
    8. 得时行星规则：日生人日月木土得时加权，夜生人月金火得时加权
    """
    process = []
    skipped_transpersonal = []

    total_e = 0.0
    total_i = 0.0

    aspects = aspects or []

    sun_house = get_planet_house(planets, 'Sun')
    sun_zodiac = ''
    moon_zodiac = ''
    for p in planets:
        if p['name'] == 'Sun':
            sun_zodiac = p.get('zodiac', {}).get('name', '')
        elif p['name'] == 'Moon':
            moon_zodiac = p.get('zodiac', {}).get('name', '')

    dominant_info = determine_dominant_functions(sun_zodiac, moon_zodiac, ascendant, rules)

    for body in CORE_BODIES:
        if body == 'Ascendant':
            planet = {'name': 'Ascendant', 'zodiac': {'name': ascendant}, 'house': 1}
        else:
            planet = next((p for p in planets if p['name'] == body), None)

        if not planet:
            continue

        is_retrograde = planet.get('is_retrograde', False) if body != 'Ascendant' else False
        zodiac = planet.get('zodiac', {}).get('name', '') if body != 'Ascendant' else ascendant

        tp_check = check_transpersonal_activation(body, aspects, rules)

        if not tp_check['activated']:
            skipped_transpersonal.append({
                'body': body,
                'reason': '未与个人行星形成紧密相位(合/刑冲/拱/六合≤3°)，不纳入计算'
            })
            continue

        tp_aspect_weight = tp_check['aspect_weight']

        result = calculate_body_ei_score(
            body, planet, ascendant, is_retrograde, sun_house, rules,
            transpersonal_aspect_weight=tp_aspect_weight
        )

        if tp_check['activating_aspects']:
            result['transpersonal_activation'] = tp_check['activating_aspects']

        process.append(result)
        total_e += result['final_e']
        total_i += result['final_i']

    total_e = max(0, total_e)
    total_i = max(0, total_i)

    total = total_e + total_i
    if total > 0:
        scores['E'] = round(total_e, 2)
        scores['I'] = round(total_i, 2)
        normalized_e = round((total_e / total) * 100, 2)
        normalized_i = round((total_i / total) * 100, 2)
    else:
        scores['E'] = 50
        scores['I'] = 50
        normalized_e = 50
        normalized_i = 50

    calculation_process['energy_distribution'] = [{
        'step': 'E/I基础计算（荣格合规性重构版）',
        'description': (
            '荣格合规性重构算法：'
            '1.基础分值(原型中性E5/I5) '
            '2.星座修正(能量流向，非行为刻板印象) '
            '3.宫位修正(表达领域) '
            '4.权重系数(维度差异化+命主星仅E/I/J/P+得时行星) '
            '5.权重层级统治(三巨头通过权重配置体现统治力) '
            '6.宫位力量系数统一1.0(宫位=表达领域非力量) '
            '7.世代行星相位激活(三王星仅与个人行星紧密相位时纳入) '
            '8.全局修正由calculator统一乘法处理'
        ),
        'dominant_function_analysis': dominant_info,
        'sun_house': sun_house,
        'is_day_chart': sun_house in [7, 8, 9, 10, 11, 12],
        'skipped_transpersonal': skipped_transpersonal,
        'body_details': process,
        'total_e': round(total_e, 2),
        'total_i': round(total_i, 2),
        'normalized': {'E': normalized_e, 'I': normalized_i},
        'raw_scores': {'E': scores['E'], 'I': scores['I']}
    }]
