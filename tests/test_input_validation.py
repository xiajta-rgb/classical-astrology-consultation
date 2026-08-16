import pytest

from astrology_engine import calculate_natal
from astrology_engine.predictive import calculate_predictive


@pytest.mark.parametrize(
    "lat,lon",
    [(91, 0), (-91, 0), (0, 181), (0, -181), (0, 400)],
)
def test_public_calculators_reject_out_of_range_coordinates(lat, lon):
    with pytest.raises(ValueError, match="纬度|经度"):
        calculate_natal("1996-11-11T22:25:00", lat=lat, lon=lon, tz=8)


@pytest.mark.parametrize("tz", [-15, 15, float("nan"), float("inf")])
def test_public_calculators_reject_invalid_fixed_timezone(tz):
    with pytest.raises((ValueError, OverflowError), match="时区|finite|有限|cannot"):
        calculate_natal("1996-11-11T22:25:00", lat=27, lon=113, tz=tz)


def test_predictive_entrypoint_uses_the_same_coordinate_contract():
    with pytest.raises(ValueError, match="经度"):
        calculate_predictive("essential_dignities", "1996-11-11T22:25:00", lat=27, lon=400, tz=8)


@pytest.mark.parametrize("technique", ["transit", "solar_return"])
def test_predictive_target_coordinates_use_the_same_coordinate_contract(technique):
    kwargs = {
        "target_lat": 91,
        "target_lon": 113,
    }
    if technique == "transit":
        kwargs["target_datetime"] = "2026-01-01T00:00:00"
    else:
        kwargs["target_year"] = 2026
        kwargs["use_birth_location"] = False
    with pytest.raises(ValueError, match="纬度"):
        calculate_predictive(
            technique,
            "1996-11-11T22:25:00",
            lat=27,
            lon=113,
            tz=8,
            **kwargs,
        )


def test_public_chart_contract_rejects_embedded_timezone_offsets():
    with pytest.raises(ValueError, match="不带时区"):
        calculate_natal("1996-11-11T22:25:00+08:00", lat=27, lon=113, tz=8)


def test_house_system_normalization_keeps_chart_identity_consistent():
    lower = calculate_natal("1996-11-11T22:25:00", lat=27, lon=113, tz=8, house_system="p")
    empty = calculate_natal("1996-11-11T22:25:00", lat=27, lon=113, tz=8, house_system="")
    assert lower["chart_id"] == empty["chart_id"]
    assert lower["house_system"] == empty["house_system"] == "Placidus"


def test_predictive_envelope_uses_the_same_house_system_display_name():
    result = calculate_predictive(
        "essential_dignities",
        "1996-11-11T22:25:00",
        lat=27,
        lon=113,
        tz=8,
        house_system="p",
    )
    assert result["house_system"] == "Placidus"
