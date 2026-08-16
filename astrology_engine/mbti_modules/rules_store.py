# MBTI 规则数据存储模块
# 架构说明：
# - constants.py 是唯一的默认规则数据源（Single Source of Truth）
# - mbti_rules_custom.json 仅用于用户自定义覆盖（可选）
# - 所有模块必须通过 get_merged_rules() 获取规则，禁止直接 import constants
# - 当自定义文件不存在时，自动使用 constants.py 中的默认值
# - 修改权重时只需更新 constants.py，自定义文件会自动 fallback
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .constants import (
    PLANET_EI_BASE, ZODIAC_EI_CORRECTION, HOUSE_EI_CORRECTION,
    PLANET_SN_BASE, ZODIAC_SN_CORRECTION, HOUSE_SN_CORRECTION,
    PLANET_FT_BASE, ZODIAC_FT_CORRECTION, HOUSE_FT_CORRECTION,
    PLANET_JP_BASE, ZODIAC_JP_CORRECTION, HOUSE_JP_CORRECTION,
    PLANET_WEIGHT_CONFIG, RULER_WEIGHT_OVERRIDE, RETROGRADE_FACTOR,
    PLANET_STRENGTH_WEIGHT, PLANET_EXALTATION, PLANET_DETRIMENT,
    PLANET_FALL, PLANET_RULERSHIP, ASC_RULERS,
    PLANET_JUNGIAN_FUNCTIONS, HOUSE_JUNGIAN_ASSOCIATIONS,
    ELEMENT_JUNGIAN_ASSOCIATIONS, PLANET_STRENGTH_OFFSET,
    NODE_EI_BASE, NODE_SN_BASE, NODE_FT_BASE, NODE_JP_BASE,
    NODE_JUNGIAN_FUNCTIONS, NODE_HOUSE_INFLUENCE,
    FUNCTION_LEVEL_WEIGHTS, ASPECT_ANGLE_WEIGHT,
    HARMONIOUS_ASPECT_TYPES, TENSE_ASPECT_TYPES, MALEFIC_PLANETS,
    HOUSE_STRENGTH_WEIGHT, FAVORABLE_PLANETS_DAY, FAVORABLE_PLANETS_NIGHT, FAVORABLE_WEIGHT,
    TRANSPERSONAL_ACTIVATION_ASPECTS, TRANSPERSONAL_ACTIVATION_ORB,
    TRANSPERSONAL_ASPECT_WEIGHT, TRANSPERSONAL_ACTIVATION_PLANETS,
)

# Keep custom rules inside this project. The ephh source resolved this path
# relative to its API package, which would escape the migrated engine here.
RULES_FILE = str(Path(__file__).resolve().parents[1] / 'data' / 'mbti_rules_custom.json')

# 默认规则映射表（所有值均来自 constants.py，禁止在此处硬编码任何数值）
DEFAULT_RULES = {
    'planet_ei_base': PLANET_EI_BASE,
    'zodiac_ei_correction': ZODIAC_EI_CORRECTION,
    'house_ei_correction': HOUSE_EI_CORRECTION,
    'planet_sn_base': PLANET_SN_BASE,
    'zodiac_sn_correction': ZODIAC_SN_CORRECTION,
    'house_sn_correction': HOUSE_SN_CORRECTION,
    'planet_ft_base': PLANET_FT_BASE,
    'zodiac_ft_correction': ZODIAC_FT_CORRECTION,
    'house_ft_correction': HOUSE_FT_CORRECTION,
    'planet_jp_base': PLANET_JP_BASE,
    'zodiac_jp_correction': ZODIAC_JP_CORRECTION,
    'house_jp_correction': HOUSE_JP_CORRECTION,
    'planet_weight_config': PLANET_WEIGHT_CONFIG,
    'ruler_weight_override': RULER_WEIGHT_OVERRIDE,
    'retrograde_factor': RETROGRADE_FACTOR,
    'planet_strength_weight': PLANET_STRENGTH_WEIGHT,
    'planet_exaltation': PLANET_EXALTATION,
    'planet_detriment': PLANET_DETRIMENT,
    'planet_fall': PLANET_FALL,
    'planet_rulership': PLANET_RULERSHIP,
    'asc_rulers': ASC_RULERS,
    'planet_jungian_functions': PLANET_JUNGIAN_FUNCTIONS,
    'house_jungian_associations': HOUSE_JUNGIAN_ASSOCIATIONS,
    'element_jungian_associations': ELEMENT_JUNGIAN_ASSOCIATIONS,
    'node_ei_base': NODE_EI_BASE,
    'node_sn_base': NODE_SN_BASE,
    'node_ft_base': NODE_FT_BASE,
    'node_jp_base': NODE_JP_BASE,
    'node_jungian_functions': NODE_JUNGIAN_FUNCTIONS,
    'node_house_influence': NODE_HOUSE_INFLUENCE,
    'function_level_weights': FUNCTION_LEVEL_WEIGHTS,
    'aspect_angle_weight': ASPECT_ANGLE_WEIGHT,
    'harmonious_aspect_types': list(HARMONIOUS_ASPECT_TYPES),
    'tense_aspect_types': list(TENSE_ASPECT_TYPES),
    'malefic_planets': list(MALEFIC_PLANETS),
    'house_strength_weight': HOUSE_STRENGTH_WEIGHT,
    'favorable_planets_day': FAVORABLE_PLANETS_DAY,
    'favorable_planets_night': FAVORABLE_PLANETS_NIGHT,
    'favorable_weight': FAVORABLE_WEIGHT,
    'transpersonal_activation_aspects': list(TRANSPERSONAL_ACTIVATION_ASPECTS),
    'transpersonal_activation_orb': TRANSPERSONAL_ACTIVATION_ORB,
    'transpersonal_aspect_weight': TRANSPERSONAL_ASPECT_WEIGHT,
    'transpersonal_activation_planets': TRANSPERSONAL_ACTIVATION_PLANETS,
}


def load_custom_rules() -> Dict[str, Any]:
    """加载自定义规则覆盖（仅包含用户修改过的键）"""
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_custom_rules(rules: Dict[str, Any]) -> bool:
    """保存自定义规则覆盖"""
    try:
        os.makedirs(os.path.dirname(RULES_FILE), exist_ok=True)
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_merged_rules() -> Dict[str, Any]:
    """获取合并后的规则（constants.py 默认值 + 自定义覆盖）
    
    优先级：自定义规则 > constants.py 默认值
    当自定义文件中不存在某个键时，自动使用 constants.py 中的默认值
    """
    custom = load_custom_rules()
    merged = {}
    for key, default_val in DEFAULT_RULES.items():
        if key in custom:
            merged[key] = custom[key]
        else:
            merged[key] = default_val
    return merged


def get_rules_for_display() -> Dict[str, Any]:
    """获取用于前端展示的规则数据（含默认值和自定义值对比）"""
    custom = load_custom_rules()
    result = {}
    for key, default_val in DEFAULT_RULES.items():
        result[key] = {
            'default': default_val,
            'custom': custom.get(key),
            'is_custom': key in custom,
        }
    return result


def reset_to_defaults() -> bool:
    """重置为默认规则（删除自定义文件）"""
    try:
        if os.path.exists(RULES_FILE):
            os.remove(RULES_FILE)
        return True
    except Exception:
        return False
