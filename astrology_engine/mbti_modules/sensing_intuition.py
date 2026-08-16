# S/N 感觉/直觉计算模块 - 矫正版
# 核心原则：
# 1. 力量与倾向分离：庙旺弱仅影响权重，不改变S/N倾向
# 2. 修正项互斥：星座修正已含元素属性，不重复计算
# 3. 对称性约束：所有修正项S+N=0
# 4. 全局修正由calculator.py统一处理（乘法×1.05）
from typing import Dict, Any, List, Optional
from .constants import (
    PLANET_SN_BASE, ZODIAC_SN_CORRECTION, HOUSE_SN_CORRECTION,
    ASC_RULERS, CORE_BODIES, TRANSPERSONAL_PLANETS
)
from .energy_distribution import (
    get_planet_house, get_planet_dignity_status,
    get_weight_coefficient, get_weight_breakdown,
    get_dominant_function_multiplier, determine_dominant_functions,
    check_transpersonal_activation
)


def _get_sn_rules(rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取S/N规则（默认或自定义）"""
    if rules:
        return {
            'planet_sn_base': rules.get('planet_sn_base', PLANET_SN_BASE),
            'zodiac_sn_correction': rules.get('zodiac_sn_correction', ZODIAC_SN_CORRECTION),
            'house_sn_correction': rules.get('house_sn_correction', HOUSE_SN_CORRECTION),
            'asc_rulers': rules.get('asc_rulers', ASC_RULERS),
        }
    return {
        'planet_sn_base': PLANET_SN_BASE,
        'zodiac_sn_correction': ZODIAC_SN_CORRECTION,
        'house_sn_correction': HOUSE_SN_CORRECTION,
        'asc_rulers': ASC_RULERS,
    }


def get_chart_ruler(ascendant: str, planets: List[Dict[str, Any]], rules: Optional[Dict[str, Any]] = None) -> str:
    r = _get_sn_rules(rules)
    return r['asc_rulers'].get(ascendant, 'Moon')


def get_zodiac_sn_correction(zodiac: str, rules: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    r = _get_sn_rules(rules)
    return r['zodiac_sn_correction'].get(zodiac, {'S': 0, 'N': 0})


def get_house_sn_correction(house: int, rules: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    r = _get_sn_rules(rules)
    # 尝试整数键查找，再尝试字符串键查找
    house_data = r['house_sn_correction'].get(house)
    if house_data is None:
        house_data = r['house_sn_correction'].get(str(house))
    return house_data if house_data is not None else {'S': 0, 'N': 0}


def calculate_sensing_intuition(
    planets: List[Dict[str, Any]],
    ascendant: str,
    scores: Dict[str, float],
    calculation_process: Dict[str, List],
    rules: Optional[Dict[str, Any]] = None,
    aspects: Optional[List[Dict[str, Any]]] = None
) -> None:
    """计算S/N感觉/直觉分布 - 荣格合规性重构版
    核心改动：
    1. 删除庙旺弱偏移（力量与倾向分离）
    2. 权重系数与力量系数完全分离
    3. 星座修正基于知觉功能原型（非判断功能混淆）
    4. 主导功能层级统治：月亮3倍权重（S/N核心影响者）
    5. 命主星不加权S/N维度
    6. 宫位力量系数统一1.0
    7. 世代行星相位激活：三王星仅与个人行星紧密相位时纳入
    """
    process = []
    skipped_transpersonal = []

    total_s = 0.0
    total_n = 0.0

    aspects = aspects or []

    chart_ruler = get_chart_ruler(ascendant, planets, rules)
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
            is_ruler = True
        else:
            planet = next((p for p in planets if p['name'] == body), None)
            is_ruler = (body == chart_ruler)

        if not planet:
            continue

        zodiac = planet.get('zodiac', {}).get('name', '') if body != 'Ascendant' else ascendant
        house = planet.get('house', 1) if body != 'Ascendant' else 1
        is_retrograde = planet.get('is_retrograde', False) if body != 'Ascendant' else False

        tp_check = check_transpersonal_activation(body, aspects, rules)

        if not tp_check['activated']:
            skipped_transpersonal.append({
                'body': body,
                'reason': '未与个人行星形成紧密相位(合/刑冲/拱/六合≤3°)，不纳入计算'
            })
            continue

        tp_aspect_weight = tp_check['aspect_weight']

        r = _get_sn_rules(rules)
        base = r['planet_sn_base'].get(body, {'S': 5, 'N': 5, 'weight': 1.0})
        base_s = base['S']
        base_n = base['N']
        dim_base_weight = base.get('weight', 1.0)

        dignity = get_planet_dignity_status(body, zodiac, rules)
        wb = get_weight_breakdown(body, is_ruler, sun_house, rules, dimension='SN', dimension_base_weight=dim_base_weight)
        weight_coeff = wb['weight']

        zodiac_corr = get_zodiac_sn_correction(zodiac, rules)

        if body == 'Ascendant':
            house_corr = {'S': 0, 'N': 0}
        else:
            house_corr = get_house_sn_correction(house, rules)

        raw_s = base_s + zodiac_corr['S'] + house_corr['S']
        raw_n = base_n + zodiac_corr['N'] + house_corr['N']

        body_s = max(0, raw_s * weight_coeff * tp_aspect_weight)
        body_n = max(0, raw_n * weight_coeff * tp_aspect_weight)

        total_s += body_s
        total_n += body_n

        tp_desc = f' × {tp_aspect_weight}(世代相位)' if tp_aspect_weight < 1.0 else ''

        weight_parts = [f'{wb["base_weight"]:.1f}']
        if wb['ruler_bonus'] > 0:
            weight_parts.append(f'+{wb["ruler_bonus"]:.1f}(命主星)')
        if wb['is_favorable']:
            fav_label = '日生得时' if wb['favorable_type'] == 'day' else '夜生得时'
            weight_parts.append(f'×{wb["favorable_multiplier"]:.1f}({fav_label})')
        weight_desc = ''.join(weight_parts)

        process.append({
            'body': body,
            'zodiac': zodiac,
            'house': house,
            'is_ruler': is_ruler,
            'dignity': dignity,
            'base': base,
            'zodiac_corr': zodiac_corr,
            'house_corr': house_corr,
            'is_retrograde': is_retrograde,
            'weight_coeff': round(weight_coeff, 4),
            'weight_breakdown': wb,
            'transpersonal_aspect_weight': tp_aspect_weight,
            'calculation_process': (
                f'S: {base_s}+({zodiac_corr["S"]:+.1f})+({house_corr["S"]:+.1f}) = {raw_s:.1f} '
                f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(body_s, 2)} | '
                f'N: {base_n}+({zodiac_corr["N"]:+.1f})+({house_corr["N"]:+.1f}) = {raw_n:.1f} '
                f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(body_n, 2)}'
            ),
            'final_s': round(body_s, 2),
            'final_n': round(body_n, 2)
        })

    total = total_s + total_n
    if total > 0:
        scores['S'] = round(total_s, 2)
        scores['N'] = round(total_n, 2)
        normalized_s = round((total_s / total) * 100, 2)
        normalized_n = round((total_n / total) * 100, 2)
    else:
        scores['S'] = 50
        scores['N'] = 50
        normalized_s = 50
        normalized_n = 50

    calculation_process['sensing_intuition_distribution'] = [{
        'step': 'S/N基础计算（荣格合规性重构版）',
        'description': (
            '荣格合规性重构算法：'
            '1.基础分值(原型中性S5/N5) '
            '2.星座修正(知觉功能原型：五感vs潜意识) '
            '3.宫位修正(表达领域) '
            '4.权重系数(维度差异化+命主星加权) '
            '5.主导功能层级统治(太阳/月亮3倍绝对权重) '
            '6.宫位力量系数统一1.0 '
            '7.世代行星相位激活(三王星仅与个人行星紧密相位时纳入) '
            '8.全局修正由calculator统一乘法处理'
        ),
        'dominant_function_analysis': dominant_info,
        'chart_ruler': chart_ruler,
        'body_details': process,
        'total_s': round(total_s, 2),
        'total_n': round(total_n, 2),
        'normalized': {'S': normalized_s, 'N': normalized_n},
        'raw_scores': {'S': scores['S'], 'N': scores['N']}
    }]
