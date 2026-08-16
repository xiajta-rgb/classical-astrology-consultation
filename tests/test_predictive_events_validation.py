import pytest

from astrology_engine.predictive_events import refine_aspect_contacts, scan_progressive_window


def _scan_kwargs() -> dict:
    return {
        "technique": "transit",
        "birth_datetime": "1996-11-11T22:25:00",
        "start_datetime": "2026-01-01T00:00:00",
        "end_datetime": "2026-01-01T01:00:00",
        "lat": 27,
        "lon": 113,
        "tz": 8,
    }


def test_timing_scan_rejects_aware_window_values_instead_of_stripping_offset():
    kwargs = _scan_kwargs()
    kwargs["start_datetime"] = "2026-01-01T00:00:00+08:00"
    with pytest.raises(ValueError, match="不带时区"):
        scan_progressive_window(**kwargs)


@pytest.mark.parametrize("field", ["step_days", "step_hours", "applying_orb", "separating_orb"])
def test_timing_scan_rejects_non_finite_or_negative_parameters(field):
    kwargs = _scan_kwargs()
    kwargs[field] = float("nan")
    with pytest.raises(ValueError, match="有限|positive"):
        scan_progressive_window(**kwargs)


def test_timing_refinement_rejects_negative_contact_limit():
    with pytest.raises(ValueError, match="max_contacts"):
        refine_aspect_contacts(**_scan_kwargs(), max_contacts=-1)

