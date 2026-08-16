"""Project-local astrology calculation engine."""

from .natal import calculate_natal
from .significations import calculate_responsibilities
from .predictive import calculate_bundle, calculate_predictive
from .predictive_events import scan_progressive_window, scan_timing_window, refine_aspect_contacts
from .identity import chart_id


def calculate_mbti(*args, **kwargs):
    """Lazy auxiliary import; core natal calculations do not load MBTI rules."""
    from .mbti import calculate_mbti as _calculate_mbti
    return _calculate_mbti(*args, **kwargs)


def calculate_mbti_insight(*args, **kwargs):
    from .mbti import calculate_mbti_insight as _calculate_mbti_insight
    return _calculate_mbti_insight(*args, **kwargs)


def calculate_personality_insight(*args, **kwargs):
    from .mbti import calculate_personality_insight as _calculate_personality_insight
    return _calculate_personality_insight(*args, **kwargs)


def calculate_tpes(*args, **kwargs):
    """Lazy auxiliary import; career insight is opt-in, not natal-core plumbing."""
    from .tpes import calculate_tpes as _calculate_tpes
    return _calculate_tpes(*args, **kwargs)


def calculate_career_insight(*args, **kwargs):
    from .tpes import calculate_career_insight as _calculate_career_insight
    return _calculate_career_insight(*args, **kwargs)

__all__ = [
    "calculate_natal", "calculate_responsibilities", "calculate_predictive", "calculate_bundle",
    "scan_progressive_window", "scan_timing_window", "refine_aspect_contacts", "chart_id",
    "calculate_mbti", "calculate_mbti_insight", "calculate_personality_insight",
    "calculate_tpes", "calculate_career_insight",
]
