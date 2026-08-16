import pytest

from astrology_engine import calculate_natal
from astrology_engine.mbti import calculate_mbti
from astrology_engine.tpes import calculate_tpes


def _chart():
    planets = {
        "Sun": {"zodiac": {"name": "白羊座"}, "house_number": 10, "ecliptic_longitude": 15},
        "Moon": {"zodiac": {"name": "巨蟹座"}, "house_number": 6, "ecliptic_longitude": 105},
        "Mercury": {"zodiac": {"name": "双鱼座"}, "house_number": 2, "ecliptic_longitude": 350},
        "Venus": {"zodiac": {"name": "金牛座"}, "house_number": 2, "ecliptic_longitude": 45},
        "Mars": {"zodiac": {"name": "狮子座"}, "house_number": 5, "ecliptic_longitude": 135},
    }
    return {
        "placements": planets,
        "houses": {"asc": 90, "mc": 15, "house_cusps": [i * 30 for i in range(12)]},
        "is_day_chart": True,
        "aspects": [{"planet1": "Sun", "planet2": "Mars", "type": "trine", "orb": 1}],
    }


def test_mbti_insight_is_available_from_local_chart_facts():
    result = calculate_mbti(_chart())
    assert len(result["personality_type"]) == 4
    assert set(result["scores"]) == {"E", "I", "S", "N", "T", "F", "J", "P"}
    assert result["algorithm_version"] == "mbti-ephh-migrated"
    assert "不是心理诊断" in result["interpretation_limits"]
    assert result["astrology_audit"]["status"] == "auxiliary_context_only"


def test_mbti_rejects_invalid_house_and_sign_instead_of_silent_neutral_scoring():
    invalid_house = {"placements": {"Sun": {"zodiac": {"name": "白羊座"}, "house_number": 0}}}
    invalid_sign = {"placements": {"Sun": {"zodiac": {"name": "不存在的星座"}, "house_number": 1}}}
    with pytest.raises(ValueError, match="宫位"):
        calculate_mbti(invalid_house)
    with pytest.raises(ValueError, match="合法星座"):
        calculate_mbti(invalid_sign)


def test_mbti_marks_incomplete_high_weight_inputs_as_low_confidence():
    result = calculate_mbti({"placements": {"Moon": {"zodiac": {"name": "白羊座"}, "house_number": 1}}})
    assert result["classification_stability"]["status"] == "insufficient_input"
    assert set(result["input_summary"]["input_quality"]["missing_high_weight_bodies"]) == {"Sun", "Ascendant"}


def test_mbti_custom_rules_reach_jungian_and_aspect_layers():
    result = calculate_mbti(
        _chart(),
        rules={
            "planet_jungian_functions": {"Sun": [["Fi", 1.0]]},
            "harmonious_aspect_types": [],
        },
    )
    fi_steps = [step for step in result["calculation_process"]["jungian_functions"] if step["step"] == "2. Fi功能贡献明细"]
    assert fi_steps and any(item["body"] == "Sun" for item in fi_steps[0]["contributions"])
    jp_step = next(step for step in result["calculation_process"]["global_corrections"] if step["step"] == "J/P相位修正")
    assert jp_step["harmonious_count"] == 0


def test_tpes_insight_keeps_fixed_budget_and_career_profile():
    result = calculate_tpes(_chart())
    assert sum(result["scores"].values()) == pytest.approx(100, abs=1e-6)
    assert result["final_type"] in result["scores"]
    assert result["algorithm_version"] == "tpes-career-v3.2"
    assert result["career_profile"]["primary_axis"].startswith("第")
    assert result["career_profile"]["primary_axis"].startswith("第10宫")
    assert result["career_profile"]["classical_axis_audit"][0]["house"] == 10
    assert "职业胜任力" in result["interpretation_limits"]["auxiliary_layer"]


def test_tpes_keeps_outer_planets_out_of_classical_core_budget():
    chart = _chart()
    chart["placements"]["Neptune"] = {"zodiac": {"name": "摩羯座"}, "house_number": 6, "ecliptic_longitude": 295}
    chart["aspects"].append({"planet1": "Mercury", "planet2": "Neptune", "type": "sextile", "orb": 1})
    result = calculate_tpes(chart)
    assert "Neptune" in result["career_profile"]["classical_axis_audit"][2]["auxiliary_occupants"]
    assert all("Neptune" not in item["label"] for item in result["score_breakdown"]["aspects"]["contributions"])


def test_mbti_unactivated_outer_planets_do_not_enter_jungian_scores():
    chart = _chart()
    chart["placements"]["Neptune"] = {"zodiac": {"name": "摩羯座"}, "house_number": 6, "ecliptic_longitude": 295}
    result = calculate_mbti(chart)
    assert all(
        item.get("body") != "Neptune"
        for step in result["calculation_process"]["jungian_functions"]
        for item in step.get("contributions", [])
    )


def test_real_chart_keeps_classical_audit_primary_over_modern_labels():
    chart = calculate_natal(
        "1996-11-11T22:25:00", lat=27.8065115, lon=113.2582282, tz=8, house_system="P"
    )
    mbti = calculate_mbti(chart)
    tpes = calculate_tpes(chart)
    assert mbti["personality_type"] == "INFJ"
    assert mbti["classification_stability"]["status"] == "borderline"
    assert mbti["astrology_audit"]["chart_ruler"] == "Moon"
    assert mbti["behavioral_translation"]["status"] == "strong"
    assert "连续较长时间独立" in mbti["behavioral_translation"]["observable_pattern"]
    assert tpes["final_type"] == "狼型"
    assert tpes["career_profile"]["primary_axis"].startswith("第10宫")
    assert tpes["interpretation_limits"]["type_distinction"]["level"] == "区分接近"


def test_1997_08_03_zhou_ning_matches_reported_enfj_feedback():
    # Coordinates are the resolved administrative centroid for 周宁县, 福建省;
    # keep the regression deterministic and expose the centroid caveat in the
    # user-facing chart envelope rather than geocoding during tests.
    chart = calculate_natal(
        "1997-08-03T05:05:00", lat=27.0872517, lon=119.2950426, tz=8, house_system="P"
    )
    mbti = calculate_mbti(chart)
    assert mbti["personality_type"] == "ENFJ"
    assert mbti["scores"]["E"] > mbti["scores"]["I"]
    assert mbti["scores"]["F"] > mbti["scores"]["T"]
    assert set(mbti["classification_stability"]["borderline_dimensions"]) == {"SN", "JP"}
    assert mbti["astrology_audit"]["chart_ruler"] == "Sun"
