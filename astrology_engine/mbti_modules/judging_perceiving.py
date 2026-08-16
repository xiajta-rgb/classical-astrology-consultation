# J/P 判断/知觉计算模块 - 矫正版
# 核心原则：
# 1. 力量与倾向分离：庙旺弱仅影响权重，不改变J/P倾向
# 2. 修正项互斥：星座修正基于模式（基本/固定/变动），不重复计算
# 3. 对称性约束：所有修正项J+P=0
# 4. 关键修正：变动宫（双子、处女、射手、双鱼）= P，非J
# 5. 全局修正由calculator.py统一处理（乘法×1.05/×1.03）
from typing import Dict, Any, List, Optional
from .constants import (
    PLANET_JP_BASE, ZODIAC_JP_CORRECTION, HOUSE_JP_CORRECTION,
    ASC_RULERS, CORE_BODIES, TRANSPERSONAL_PLANETS
)
from .energy_distribution import (
    get_planet_house, get_planet_dignity_status,
    get_weight_coefficient, get_weight_breakdown,
    get_dominant_function_multiplier, determine_dominant_functions,
    check_transpersonal_activation
)


def _get_jp_rules(rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取J/P规则（默认或自定义）"""
    if rules:
        return {
            'planet_jp_base': rules.get('planet_jp_base', PLANET_JP_BASE),
            'zodiac_jp_correction': rules.get('zodiac_jp_correction', ZODIAC_JP_CORRECTION),
            'house_jp_correction': rules.get('house_jp_correction', HOUSE_JP_CORRECTION),
            'asc_rulers': rules.get('asc_rulers', ASC_RULERS),
        }
    return {
        'planet_jp_base': PLANET_JP_BASE,
        'zodiac_jp_correction': ZODIAC_JP_CORRECTION,
        'house_jp_correction': HOUSE_JP_CORRECTION,
        'asc_rulers': ASC_RULERS,
    }


def calculate_judging_perceiving(
    planets: List[Dict[str, Any]],
    ascendant: str,
    scores: Dict[str, float],
    calculation_process: Dict[str, List],
    rules: Optional[Dict[str, Any]] = None,
    aspects: Optional[List[Dict[str, Any]]] = None
) -> None:
    """计算J/P判断/知觉分布 - 荣格合规性重构版
    核心改动：
    1. 删除庙旺弱偏移（力量与倾向分离）
    2. J/P=外倾主导功能类型：J=外倾主导功能为T/F，P=外倾主导功能为S/N
    3. 主导功能层级统治：上升3倍权重（J/P核心影响者）
    4. 命主星加权J/P维度
    5. 宫位力量系数统一1.0
    6. 世代行星相位激活：三王星仅与个人行星紧密相位时纳入
    """
    process = []
    skipped_transpersonal = []

    total_j = 0.0
    total_p = 0.0

    aspects = aspects or []

    r = _get_jp_rules(rules)
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

        base = r['planet_jp_base'].get(body, {'J': 5, 'P': 5, 'weight': 1.0})
        base_j = base['J']
        base_p = base['P']

        dignity = get_planet_dignity_status(body, zodiac, rules)
        wb = get_weight_breakdown(body, is_ruler, sun_house, rules, dimension='JP')
        weight_coeff = wb['weight']

        zodiac_corr = r['zodiac_jp_correction'].get(zodiac, {'J': 0, 'P': 0})

        if body == 'Ascendant':
            house_corr = {'J': 0, 'P': 0}
        else:
            # 尝试整数键查找，再尝试字符串键查找
            house_data = r['house_jp_correction'].get(house)
            if house_data is None:
                house_data = r['house_jp_correction'].get(str(house))
            house_corr = house_data if house_data is not None else {'J': 0, 'P': 0}

        raw_j = base_j + zodiac_corr['J'] + house_corr['J']
        raw_p = base_p + zodiac_corr['P'] + house_corr['P']

        body_j = max(0, raw_j * weight_coeff * tp_aspect_weight)
        body_p = max(0, raw_p * weight_coeff * tp_aspect_weight)

        total_j += body_j
        total_p += body_p

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
                f'J: {base_j}+({zodiac_corr["J"]:+.1f})+({house_corr["J"]:+.1f}) = {raw_j:.1f} '
                f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(body_j, 2)} | '
                f'P: {base_p}+({zodiac_corr["P"]:+.1f})+({house_corr["P"]:+.1f}) = {raw_p:.1f} '
                f'× {weight_desc}={round(weight_coeff, 2)}(权重){tp_desc} = {round(body_p, 2)}'
            ),
            'final_j': round(body_j, 2),
            'final_p': round(body_p, 2)
        })

    total = total_j + total_p
    if total > 0:
        scores['J'] = round(total_j, 2)
        scores['P'] = round(total_p, 2)
        normalized_j = round((total_j / total) * 100, 2)
        normalized_p = round((total_p / total) * 100, 2)
    else:
        scores['J'] = 50
        scores['P'] = 50
        normalized_j = 50
        normalized_p = 50

    calculation_process['judging_perceiving_distribution'] = [{
        'step': 'J/P基础计算（荣格合规性重构版）',
        'description': (
            '荣格合规性重构算法：'
            '1.基础分值(原型中性J5/P5) '
            '2.星座修正(外倾主导功能类型：T/F→J, S/N→P) '
            '3.宫位修正(表达领域) '
            '4.权重系数(维度差异化+命主星加权J/P) '
            '5.主导功能层级统治(太阳/上升3倍绝对权重) '
            '6.宫位力量系数统一1.0 '
            '7.世代行星相位激活(三王星仅与个人行星紧密相位时纳入) '
            '8.全局修正由calculator统一乘法处理'
        ),
        'dominant_function_analysis': dominant_info,
        'skipped_transpersonal': skipped_transpersonal,
        'body_details': process,
        'total_j': round(total_j, 2),
        'total_p': round(total_p, 2),
        'normalized': {'J': normalized_j, 'P': normalized_p},
        'raw_scores': {'J': scores['J'], 'P': scores['P']}
    }]
