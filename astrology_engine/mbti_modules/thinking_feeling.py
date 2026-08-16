# F/T 情感/思考计算模块 - 矫正版
# 核心原则：
# 1. 力量与倾向分离：庙旺弱仅影响权重，不改变F/T倾向
# 2. 修正项互斥：星座修正已含元素属性，不重复计算
# 3. 对称性约束：所有修正项F+T=0
# 4. 天蝎座修正统一到星座修正表中，不再单独处理
# 5. 全局修正由calculator.py统一处理（乘法×1.05）
from typing import Dict, Any, List, Optional
from .constants import (
    PLANET_FT_BASE, ZODIAC_FT_CORRECTION, HOUSE_FT_CORRECTION,
    ASC_RULERS, CORE_BODIES, TRANSPERSONAL_PLANETS
)
from .energy_distribution import (
    get_planet_house, get_planet_dignity_status,
    get_weight_coefficient, get_weight_breakdown,
    get_dominant_function_multiplier, determine_dominant_functions,
    check_transpersonal_activation
)


def _get_ft_rules(rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取F/T规则（默认或自定义）"""
    if rules:
        return {
            'planet_ft_base': rules.get('planet_ft_base', PLANET_FT_BASE),
            'zodiac_ft_correction': rules.get('zodiac_ft_correction', ZODIAC_FT_CORRECTION),
            'house_ft_correction': rules.get('house_ft_correction', HOUSE_FT_CORRECTION),
            'asc_rulers': rules.get('asc_rulers', ASC_RULERS),
        }
    return {
        'planet_ft_base': PLANET_FT_BASE,
        'zodiac_ft_correction': ZODIAC_FT_CORRECTION,
        'house_ft_correction': HOUSE_FT_CORRECTION,
        'asc_rulers': ASC_RULERS,
    }


def calculate_thinking_feeling(
    planets: List[Dict[str, Any]],
    ascendant: str,
    scores: Dict[str, float],
    calculation_process: Dict[str, List],
    rules: Optional[Dict[str, Any]] = None,
    aspects: Optional[List[Dict[str, Any]]] = None
) -> None:
    """计算F/T情感/思考分布 - 荣格合规性重构版
    核心改动：
    1. 删除庙旺弱偏移（力量与倾向分离）
    2. 删除天蝎座特殊动态处理（已统一到ZODIAC_FT_CORRECTION）
    3. 权重系数与力量系数完全分离
    4. 主导功能层级统治：月亮3倍权重（F/T核心影响者）
    5. 命主星不加权F/T维度
    6. 宫位力量系数统一1.0
    7. 世代行星相位激活：三王星仅与个人行星紧密相位时纳入
    """
    process = []
    skipped_transpersonal = []

    total_f = 0.0
    total_t = 0.0

    aspects = aspects or []

    r = _get_ft_rules(rules)
    chart_ruler = r['asc_rulers'].get(ascendant, 'Sun')
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

        base = r['planet_ft_base'].get(body, {'F': 5, 'T': 5, 'weight': 1.0})
        base_f = base['F']
        base_t = base['T']
        dim_base_weight = base.get('weight', 1.0)

        dignity = get_planet_dignity_status(body, zodiac, rules)
        wb = get_weight_breakdown(body, is_ruler, sun_house, rules, dimension='FT', dimension_base_weight=dim_base_weight)
        weight_coeff = wb['weight']

        zodiac_corr = r['zodiac_ft_correction'].get(zodiac, {'F': 0, 'T': 0})

        if body == 'Ascendant':
            house_corr = {'F': 0, 'T': 0}
        else:
            # 尝试整数键查找，再尝试字符串键查找
            house_data = r['house_ft_correction'].get(house)
            if house_data is None:
                house_data = r['house_ft_correction'].get(str(house))
            house_corr = house_data if house_data is not None else {'F': 0, 'T': 0}

        raw_f = base_f + zodiac_corr['F'] + house_corr['F']
        raw_t = base_t + zodiac_corr['T'] + house_corr['T']

        body_f = max(0, raw_f * weight_coeff * tp_aspect_weight)
        body_t = max(0, raw_t * weight_coeff * tp_aspect_weight)

        total_f += body_f
        total_t += body_t

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
                f'F: {base_f}+({zodiac_corr["F"]:+.1f})+({house_corr["F"]:+.1f}) = {raw_f:.1f} '
                f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(body_f, 2)} | '
                f'T: {base_t}+({zodiac_corr["T"]:+.1f})+({house_corr["T"]:+.1f}) = {raw_t:.1f} '
                f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(body_t, 2)}'
            ),
            'final_f': round(body_f, 2),
            'final_t': round(body_t, 2)
        })

    total = total_f + total_t
    if total > 0:
        scores['F'] = round(total_f, 2)
        scores['T'] = round(total_t, 2)
        normalized_f = round((total_f / total) * 100, 2)
        normalized_t = round((total_t / total) * 100, 2)
    else:
        scores['F'] = 50
        scores['T'] = 50
        normalized_f = 50
        normalized_t = 50

    calculation_process['thinking_feeling_distribution'] = [{
        'step': 'F/T基础计算（荣格合规性重构版）',
        'description': (
            '荣格合规性重构算法：'
            '1.基础分值(原型中性F5/T5) '
            '2.星座修正(判断功能原型：价值vs逻辑) '
            '3.宫位修正(表达领域) '
            '4.权重系数(维度差异化+命主星加权) '
            '5.主导功能层级统治(太阳/月亮3倍绝对权重) '
            '6.宫位力量系数统一1.0 '
            '7.世代行星相位激活(三王星仅与个人行星紧密相位时纳入) '
            '8.全局修正由calculator统一乘法处理'
        ),
        'dominant_function_analysis': dominant_info,
        'skipped_transpersonal': skipped_transpersonal,
        'body_details': process,
        'total_f': round(total_f, 2),
        'total_t': round(total_t, 2),
        'normalized': {'F': normalized_f, 'T': normalized_t},
        'raw_scores': {'F': scores['F'], 'T': scores['T']}
    }]
