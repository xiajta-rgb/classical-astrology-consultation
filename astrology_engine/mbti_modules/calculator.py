# MBTI 主计算器模块 - 矫正版
# 核心原则：
# 1. 力量与倾向分离：庙旺弱仅影响权重，不改变倾向
# 2. 修正项互斥：删除重复修正
# 3. 全局修正严格按文档：维度专属乘法修正（×1.05/×1.03）
# 4. 元素主导阈值≥4颗，模式主导阈值≥4颗
from typing import Dict, Any, List, Optional
from .constants import (
    ZODIAC_ELEMENTS, ZODIAC_MODALITY, PLANET_JUNGIAN_FUNCTIONS,
    PLANET_EXALTATION, PLANET_DETRIMENT, ASC_RULERS,
    HOUSE_JUNGIAN_ASSOCIATIONS, ELEMENT_JUNGIAN_ASSOCIATIONS, ASPECT_ANGLE_WEIGHT,
    PLANET_RULERSHIP, NODE_JUNGIAN_FUNCTIONS, NODE_HOUSE_INFLUENCE, ASPECT_TYPE_MAP,
    HARMONIOUS_ASPECT_TYPES, TENSE_ASPECT_TYPES, MALEFIC_PLANETS, TRANSPERSONAL_PLANETS
)
from .energy_distribution import calculate_energy_distribution, check_transpersonal_activation, get_planet_house
from .sensing_intuition import calculate_sensing_intuition
from .thinking_feeling import calculate_thinking_feeling
from .judging_perceiving import calculate_judging_perceiving
from .rules_store import get_merged_rules


class MBTICalculator:
    def __init__(self, chart_data: Dict[str, Any], custom_rules: Optional[Dict[str, Any]] = None):
        self.chart_data = chart_data
        self.custom_rules = custom_rules or get_merged_rules()
        self.scores = {
            'E': 0, 'I': 0, 'S': 0, 'N': 0,
            'T': 0, 'F': 0, 'J': 0, 'P': 0
        }
        self.jungian_scores = {
            'Se': 0, 'Si': 0, 'Ne': 0, 'Ni': 0,
            'Te': 0, 'Ti': 0, 'Fe': 0, 'Fi': 0
        }
        self.calculation_process = {
            'energy_distribution': [],
            'sensing_intuition_distribution': [],
            'thinking_feeling_distribution': [],
            'judging_perceiving_distribution': [],
            'global_corrections': [],
            'jungian_functions': []
        }
        self.planets = chart_data.get('planets', [])
        self.house_cusps = chart_data.get('house_cusps', [])
        self.ascendant = chart_data.get('ascendant', '')
        self.moon_sign = chart_data.get('moon_sign', '')
        self.sun_sign = chart_data.get('sun_sign', '')
        self.aspects = chart_data.get('aspects', [])

    def _rule(self, name: str, default: Any) -> Any:
        """Read a merged rule so custom configuration affects every layer."""
        return self.custom_rules.get(name, default)

    def calculate_scores(self) -> Dict[str, Any]:
        """计算MBTI各项得分 - 矫正版
        流程：
        1. 四维度基础计算由各模块完成（含权重/力量/逆行）
        2. 应用维度专属全局修正（乘法×1.05/×1.03）
        3. 计算荣格八维
        4. 归一化
        """
        calculate_energy_distribution(
            self.planets, self.ascendant, self.scores, self.calculation_process, self.custom_rules,
            aspects=self.aspects
        )

        calculate_sensing_intuition(
            self.planets, self.ascendant, self.scores, self.calculation_process, self.custom_rules,
            aspects=self.aspects
        )

        calculate_thinking_feeling(
            self.planets, self.ascendant, self.scores, self.calculation_process, self.custom_rules,
            aspects=self.aspects
        )

        calculate_judging_perceiving(
            self.planets, self.ascendant, self.scores, self.calculation_process, self.custom_rules,
            aspects=self.aspects
        )

        self.apply_global_corrections()

        self.calculate_jungian_functions()
        self.apply_shadow_function_correction()
        self.normalize_basic_dimensions()

        personality_type = self.determine_personality_type()

        return {
            'scores': self.scores,
            'jungian_scores': self.jungian_scores,
            'personality_type': personality_type,
            'calculation_process': self.calculation_process
        }

    def apply_global_corrections(self) -> None:
        """应用维度专属全局修正（严格按矫正文档，乘法×1.05/×1.03）
        E/I: 日夜盘修正×1.05
        S/N: 元素主导修正×1.05（土/水→S, 火/风→N）
        T/F: 元素主导修正×1.05（风/土→T, 水→F）
        J/P: 模式主导修正×1.05（基本宫→J, 变动宫→P）, 相位修正×1.03
        """
        corrections = []

        self._apply_ei_global_corrections(corrections)
        self._apply_sn_element_correction(corrections)
        self._apply_tf_element_correction(corrections)
        self._apply_jp_modality_correction(corrections)
        self._apply_jp_aspect_correction(corrections)

        self.calculation_process['global_corrections'] = corrections

    def _apply_ei_global_corrections(self, corrections: List) -> None:
        """E/I全局修正：日夜盘修正×1.05
        文档规则：
        - 日间盘(太阳7-12宫) → E×1.05
        - 夜间盘(太阳1-6宫) → I×1.05
        """
        sun_house = get_planet_house(self.planets, 'Sun')
        is_day_chart = sun_house in [7, 8, 9, 10, 11, 12]

        ei_corrections = {}

        if is_day_chart:
            self.scores['E'] *= 1.05
            ei_corrections['day_night'] = '日间盘(太阳7-12宫) → E×1.05'
        else:
            self.scores['I'] *= 1.05
            ei_corrections['day_night'] = '夜间盘(太阳1-6宫) → I×1.05'

        corrections.append({
            'step': 'E/I全局修正',
            'dimension': 'E/I',
            'corrections': ei_corrections,
            'is_day_chart': is_day_chart,
            'scores_after': {'E': round(self.scores['E'], 2), 'I': round(self.scores['I'], 2)}
        })

    def _apply_sn_element_correction(self, corrections: List) -> None:
        """S/N元素主导修正×1.05
        荣格元素-功能对应规则：
        - 土元素行星≥4颗 → S×1.05（土元素=具象现实经验=实感S）
        - 火/风元素行星≥4颗 → N×1.05（火=抽象信念/风=概念逻辑=直觉N）
        水元素核心是判断功能F，与知觉功能S/N无关
        """
        element_counts = {'火': 0, '土': 0, '风': 0, '水': 0}
        for planet in self.planets:
            element = ZODIAC_ELEMENTS.get(planet.get('zodiac', {}).get('name', ''), '')
            if element in element_counts:
                element_counts[element] += 1

        earth = element_counts['土']
        fire_air = element_counts['火'] + element_counts['风']

        sn_corrections = {}

        if earth >= 4:
            self.scores['S'] *= 1.05
            sn_corrections['earth'] = f'土元素{earth}颗≥4 → S×1.05'
        else:
            sn_corrections['earth'] = f'土元素{earth}颗<4，无修正'

        if fire_air >= 4:
            self.scores['N'] *= 1.05
            sn_corrections['fire_air'] = f'火/风元素{fire_air}颗≥4 → N×1.05'
        else:
            sn_corrections['fire_air'] = f'火/风元素{fire_air}颗<4，无修正'

        corrections.append({
            'step': 'S/N元素主导修正',
            'dimension': 'S/N',
            'element_counts': element_counts,
            'earth_count': earth,
            'fire_air_count': fire_air,
            'corrections': sn_corrections,
            'scores_after': {'S': round(self.scores['S'], 2), 'N': round(self.scores['N'], 2)}
        })

    def _apply_tf_element_correction(self, corrections: List) -> None:
        """T/F元素主导修正×1.05
        文档规则：某元素行星数量≥4颗
        - 风/土元素主导 → T×1.05
        - 水元素主导 → F×1.05
        """
        element_counts = {'火': 0, '土': 0, '风': 0, '水': 0}
        for planet in self.planets:
            element = ZODIAC_ELEMENTS.get(planet.get('zodiac', {}).get('name', ''), '')
            if element in element_counts:
                element_counts[element] += 1

        air_earth = element_counts['风'] + element_counts['土']
        water = element_counts['水']

        tf_corrections = {}

        if air_earth >= 4:
            self.scores['T'] *= 1.05
            tf_corrections['air_earth'] = f'风/土元素{air_earth}颗≥4 → T×1.05'
        else:
            tf_corrections['air_earth'] = f'风/土元素{air_earth}颗<4，无修正'

        if water >= 4:
            self.scores['F'] *= 1.05
            tf_corrections['water'] = f'水元素{water}颗≥4 → F×1.05'
        else:
            tf_corrections['water'] = f'水元素{water}颗<4，无修正'

        corrections.append({
            'step': 'T/F元素主导修正',
            'dimension': 'T/F',
            'element_counts': element_counts,
            'air_earth_count': air_earth,
            'water_count': water,
            'corrections': tf_corrections,
            'scores_after': {'T': round(self.scores['T'], 2), 'F': round(self.scores['F'], 2)}
        })

    def _apply_jp_modality_correction(self, corrections: List) -> None:
        """J/P模式主导修正×1.05
        文档规则：某模式行星数量≥4颗
        - 基本宫主导 → J×1.05
        - 变动宫主导 → P×1.05
        """
        modality_counts = {'基本': 0, '固定': 0, '变动': 0}
        for planet in self.planets:
            modality = ZODIAC_MODALITY.get(planet.get('zodiac', {}).get('name', ''), '')
            if modality in modality_counts:
                modality_counts[modality] += 1

        jp_corrections = {}

        if modality_counts['基本'] >= 4:
            self.scores['J'] *= 1.05
            jp_corrections['cardinal'] = f'基本宫{modality_counts["基本"]}颗≥4 → J×1.05'
        else:
            jp_corrections['cardinal'] = f'基本宫{modality_counts["基本"]}颗<4，无修正'

        if modality_counts['变动'] >= 4:
            self.scores['P'] *= 1.05
            jp_corrections['mutable'] = f'变动宫{modality_counts["变动"]}颗≥4 → P×1.05'
        else:
            jp_corrections['mutable'] = f'变动宫{modality_counts["变动"]}颗<4，无修正'

        corrections.append({
            'step': 'J/P模式主导修正',
            'dimension': 'J/P',
            'modality_counts': modality_counts,
            'corrections': jp_corrections,
            'scores_after': {'J': round(self.scores['J'], 2), 'P': round(self.scores['P'], 2)}
        })

    def _apply_jp_aspect_correction(self, corrections: List) -> None:
        """J/P相位修正×1.03
        文档规则：
        - 紧张相位(刑/冲)数量＞和谐相位(三合/六合) → J×1.03
        - 和谐相位数量＞紧张相位 → P×1.03
        """
        harmonious_count = 0
        tense_count = 0

        for aspect in self.aspects:
            aspect_type = self._normalize_aspect_type(aspect.get('type', ''))
            harmonious_types = set(self._rule('harmonious_aspect_types', HARMONIOUS_ASPECT_TYPES))
            tense_types = set(self._rule('tense_aspect_types', TENSE_ASPECT_TYPES))
            if aspect_type in harmonious_types:
                harmonious_count += 1
            elif aspect_type in tense_types:
                tense_count += 1

        jp_aspect_corrections = {}

        if tense_count > harmonious_count:
            self.scores['J'] *= 1.03
            jp_aspect_corrections['aspect'] = f'紧张相位{tense_count}＞和谐相位{harmonious_count} → J×1.03'
        elif harmonious_count > tense_count:
            self.scores['P'] *= 1.03
            jp_aspect_corrections['aspect'] = f'和谐相位{harmonious_count}＞紧张相位{tense_count} → P×1.03'
        else:
            jp_aspect_corrections['aspect'] = f'紧张{tense_count}=和谐{harmonious_count}，无修正'

        corrections.append({
            'step': 'J/P相位修正',
            'dimension': 'J/P',
            'harmonious_count': harmonious_count,
            'tense_count': tense_count,
            'corrections': jp_aspect_corrections,
            'scores_after': {'J': round(self.scores['J'], 2), 'P': round(self.scores['P'], 2)}
        })

    def _normalize_aspect_type(self, aspect_type: str) -> str:
        return ASPECT_TYPE_MAP.get(aspect_type, aspect_type)

    def calculate_jungian_functions(self) -> None:
        """计算荣格八维主导功能"""
        process = []
        function_contributions = {func: [] for func in self.jungian_scores.keys()}
        planet_functions = self._rule('planet_jungian_functions', PLANET_JUNGIAN_FUNCTIONS)
        house_associations_map = self._rule('house_jungian_associations', HOUSE_JUNGIAN_ASSOCIATIONS)
        element_associations_map = self._rule('element_jungian_associations', ELEMENT_JUNGIAN_ASSOCIATIONS)

        for planet in self.planets:
            planet_name = planet.get('name', '')
            if planet_name in TRANSPERSONAL_PLANETS:
                activation = check_transpersonal_activation(planet_name, self.aspects, self.custom_rules)
                if not activation['activated']:
                    continue
            zodiac_name = planet.get('zodiac', {}).get('name', '')
            house_number = planet.get('house', 1)
            strength = self._calculate_planet_strength(planet_name)

            functions = planet_functions.get(planet_name, [])
            for func, weight in functions[:2]:
                if func in self.jungian_scores:
                    contrib = strength * 2 * weight
                    self.jungian_scores[func] += contrib
                    function_contributions[func].append({
                        'body': planet_name,
                        'zodiac': zodiac_name,
                        'house': house_number,
                        'type': 'base',
                        'value': contrib,
                        'formula': f'{strength}(强度)×2×{weight}(权重)={contrib:.1f}'
                    })

            house_associations = house_associations_map.get(house_number, house_associations_map.get(str(house_number), {}))
            for func, weight in house_associations.items():
                if func in self.jungian_scores:
                    contrib = strength * 0.5 * weight
                    self.jungian_scores[func] += contrib
                    function_contributions[func].append({
                        'body': planet_name,
                        'zodiac': zodiac_name,
                        'house': house_number,
                        'type': 'house',
                        'value': contrib,
                        'formula': f'{strength}(强度)×0.5×{weight}(权重)={contrib:.1f}'
                    })

            element = ZODIAC_ELEMENTS.get(zodiac_name, '')
            if element:
                element_associations = element_associations_map.get(element, {})
                for func, weight in element_associations.items():
                    if func in self.jungian_scores:
                        contrib = strength * 0.3 * weight
                        self.jungian_scores[func] += contrib
                        function_contributions[func].append({
                            'body': planet_name,
                            'zodiac': zodiac_name,
                            'house': house_number,
                            'type': 'element',
                            'value': contrib,
                            'formula': f'{strength}(强度)×0.3×{weight}(权重)={contrib:.1f}'
                        })

        self._calculate_aspect_influence_on_functions(function_contributions)
        self._calculate_nodes_contribution(function_contributions)

        sorted_functions = sorted(self.jungian_scores.items(), key=lambda x: x[1], reverse=True)

        process.append({
            'step': '1. 八维功能基础分计算',
            'description': f'共计算{len(self.planets)}颗行星的八维贡献',
            'function_scores': {func: round(score, 1) for func, score in self.jungian_scores.items()},
            'top_functions': [f'{func}({score:.1f})' for func, score in sorted_functions[:4]],
            'current_scores': {k: v for k, v in self.scores.items()}
        })

        for func, contribs in function_contributions.items():
            if contribs:
                total = sum(c['value'] for c in contribs)
                process.append({
                    'step': f'2. {func}功能贡献明细',
                    'description': f'总贡献: {total:.1f}',
                    'contributions': [{
                        'body': c['body'],
                        'zodiac': c['zodiac'],
                        'house': f'{c["house"]}宫',
                        'type': {'base': '基础', 'house': '宫位', 'element': '元素', 'aspect': '相位', 'node': '交点'}[c['type']],
                        'value': round(c['value'], 1),
                        'formula': c.get('formula', '')
                    } for c in contribs[:5]],
                    'current_jungian_scores': {func: round(self.jungian_scores.get(func, 0), 1)}
                })

        self.calculation_process['jungian_functions'] = process

    def _calculate_nodes_contribution(self, function_contributions: Dict) -> Dict:
        """计算南北交点对荣格八维的特殊贡献"""
        node_contrib = {'North Node': {}, 'South Node': {}}
        node_functions_map = self._rule('node_jungian_functions', NODE_JUNGIAN_FUNCTIONS)
        node_house_influence_map = self._rule('node_house_influence', NODE_HOUSE_INFLUENCE)

        for node_name in ['North Node', 'South Node']:
            node = next((p for p in self.planets if p['name'] == node_name), None)
            if not node:
                continue

            zodiac_name = node.get('zodiac', {}).get('name', '')
            house_number = node.get('house', 1)
            strength = self._calculate_planet_strength(node_name)

            node_functions = node_functions_map.get(node_name, [])
            for func, weight in node_functions:
                if func in self.jungian_scores:
                    contrib = strength * 1.5 * weight
                    self.jungian_scores[func] += contrib
                    if func not in node_contrib[node_name]:
                        node_contrib[node_name][func] = 0
                    node_contrib[node_name][func] += contrib
                    function_contributions[func].append({
                        'body': node_name,
                        'zodiac': zodiac_name,
                        'house': house_number,
                        'type': 'node',
                        'value': contrib,
                        'formula': f'{strength}(强度)×1.5(交点权重)×{weight}(功能权重)={contrib:.1f}'
                    })

            house_influence = node_house_influence_map.get(node_name, {}).get(house_number, node_house_influence_map.get(node_name, {}).get(str(house_number), {}))
            for dim, weight in house_influence.items():
                if dim in self.scores:
                    self.scores[dim] += weight * 0.5

        return node_contrib

    def _calculate_aspect_influence_on_functions(self, function_contributions: Dict) -> Dict:
        """计算相位对荣格八维功能的影响。

        The old ephh implementation assigned every harmonious aspect to all
        extraverted functions and every tense aspect to all introverted
        functions. That made an unrelated aspect change the type in a
        chart-independent way.  An aspect now contributes only to the
        Jungian functions associated with its two actual planets; the aspect
        character changes the size of the contribution, not its target.
        """
        aspect_contrib = {}

        for aspect in self.aspects:
            planet1 = aspect.get('planet1', '')
            planet2 = aspect.get('planet2', '')
            aspect_type = aspect.get('type')
            orb = aspect.get('orb', 0)

            if not planet1 or not planet2:
                continue

            angle_weight = 1.0
            angle_weights = self._rule('aspect_angle_weight', ASPECT_ANGLE_WEIGHT)
            if orb <= 1:
                angle_weight = angle_weights['exact']
            elif orb <= 3:
                angle_weight = angle_weights['close']
            elif orb <= 6:
                angle_weight = angle_weights['wide']
            elif orb <= 8:
                angle_weight = angle_weights['orb']

            cn_aspect_type = self._normalize_aspect_type(aspect_type)

            harmonious_types = set(self._rule('harmonious_aspect_types', HARMONIOUS_ASPECT_TYPES))
            tense_types = set(self._rule('tense_aspect_types', TENSE_ASPECT_TYPES))
            if cn_aspect_type not in harmonious_types and cn_aspect_type not in tense_types:
                continue
            aspect_character = 'resource' if cn_aspect_type in harmonious_types else 'development_tension'
            base = 4.0 if aspect_character == 'resource' else 3.0
            for body in (planet1, planet2):
                functions = self._rule('planet_jungian_functions', PLANET_JUNGIAN_FUNCTIONS).get(body, [])
                for func, function_weight in functions:
                    if func not in self.jungian_scores:
                        continue
                    contrib = base * angle_weight * function_weight
                    self.jungian_scores[func] += contrib
                    function_contributions[func].append({
                        'body': f'{planet1}-{planet2}',
                        'zodiac': aspect_type,
                        'house': 0,
                        'type': 'aspect',
                        'value': contrib,
                        'effect': aspect_character,
                        'formula': f'{base:.1f}(相位性质)×{angle_weight}(容许度权重)×{function_weight}(行星功能权重)={contrib:.1f}'
                    })

        return aspect_contrib

    def apply_shadow_function_correction(self) -> None:
        """阴影功能补充修正"""
        shadow_functions = {
            'Se': 'Ni', 'Ni': 'Se',
            'Si': 'Ne', 'Ne': 'Si',
            'Te': 'Fi', 'Fi': 'Te',
            'Ti': 'Fe', 'Fe': 'Ti'
        }

        shadow_scores = {}
        for func, score in self.jungian_scores.items():
            shadow_func = shadow_functions.get(func)
            if shadow_func:
                shadow_score = max(0, 100 - score) * 0.3
                shadow_scores[shadow_func] = shadow_scores.get(shadow_func, 0) + shadow_score

        for func, score in shadow_scores.items():
            if func in self.jungian_scores:
                self.jungian_scores[func] += score

    def normalize_basic_dimensions(self) -> None:
        """将基本MBTI维度归一化"""
        original_scores = {k: v for k, v in self.scores.items()}

        dimension_pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]

        for dim1, dim2 in dimension_pairs:
            score1 = original_scores[dim1]
            score2 = original_scores[dim2]

            total_pair_score = score1 + score2

            if total_pair_score == 0:
                normalized1 = 50
                normalized2 = 50
            else:
                normalized1 = int((score1 / total_pair_score) * 100)
                normalized2 = 100 - normalized1

            self.scores[dim1] = normalized1
            self.scores[dim2] = normalized2

        self.normalize_jungian_scores()

    def normalize_jungian_scores(self) -> None:
        """将荣格八维功能评分归一化到0-100范围"""
        max_score = max(self.jungian_scores.values()) if self.jungian_scores else 1
        if max_score <= 0:
            max_score = 1
        for func in self.jungian_scores:
            self.jungian_scores[func] = round((self.jungian_scores[func] / max_score) * 100, 1)

    def determine_personality_type(self) -> str:
        """确定最终人格类型"""
        e_i = 'E' if self.scores['E'] >= self.scores['I'] else 'I'
        s_n = 'S' if self.scores['S'] >= self.scores['N'] else 'N'
        t_f = 'T' if self.scores['T'] >= self.scores['F'] else 'F'
        j_p = 'J' if self.scores['J'] >= self.scores['P'] else 'P'

        return f"{e_i}{s_n}{t_f}{j_p}"

    def _calculate_planet_strength(self, planet_name: str) -> int:
        """计算行星强度"""
        planet = next((p for p in self.planets if p['name'] == planet_name), None)
        if not planet:
            return 0

        house = planet.get('house', 1)
        aspects_count = self._get_planet_aspects_count(planet_name)

        house_strength = 10 - abs(house - 10)

        zodiac_name = planet.get('zodiac', {}).get('name', '')
        is_exalted = zodiac_name == self._rule('planet_exaltation', PLANET_EXALTATION).get(planet_name, '')
        detriment_map = self._rule('planet_detriment', PLANET_DETRIMENT)
        detriment_value = detriment_map.get(planet_name, '')
        is_detriment = zodiac_name in detriment_value if isinstance(detriment_value, list) else zodiac_name == detriment_value

        modifier = 0
        if is_exalted:
            modifier = 2
        elif is_detriment:
            modifier = -2

        return house_strength + aspects_count + modifier

    def _get_planet_aspects_count(self, planet_name: str) -> int:
        return len(self._get_planet_aspects(planet_name))

    def _get_planet_aspects(self, planet_name: str) -> List[Dict[str, Any]]:
        aspects = []
        for aspect in self.aspects:
            if aspect.get('planet1') == planet_name or aspect.get('planet2') == planet_name:
                aspects.append(aspect)
        return aspects
