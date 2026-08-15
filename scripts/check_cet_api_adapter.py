"""Regression tests for the read-only CET response adapter."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cet_api_client as adapter  # noqa: E402
from cet_api_client import normalize  # noqa: E402


def main() -> int:
    complete = {
        "status": "success",
        "input": {"house_system": "Placidus"},
        "ephemeris": {
            "Sun": {"ecliptic_longitude": 280.4, "house_number": 10},
            "Fortune": {"ecliptic_longitude": 110.0, "house_number": 4},
        },
        "axes": {"asc": {"ecl_lon": 11.8}},
        "house_cusps_detail": [{"house_number": 1}],
        "aspects": [{"planet1": "Sun", "planet2": "Moon", "orb": 1.0}],
        "mutual_receptions": [{"planet1": "Mars", "planet2": "Jupiter"}],
    }
    result = normalize(complete)
    assert set(result) == {
        "input",
        "planets",
        "axes",
        "houses",
        "aspects",
        "fortune",
        "site_mutual_receptions",
        "raw_response",
    }
    assert result["planets"]["Sun"]["house_number"] == 10
    assert result["fortune"]["house_number"] == 4
    assert len(result["houses"]) == 1
    assert len(result["aspects"]) == 1
    assert len(result["site_mutual_receptions"]) == 1

    sparse = {"status": "success", "ephemeris": {}, "aspects": []}
    degraded = normalize(sparse)
    assert degraded["planets"] == {}
    assert degraded["houses"] == []
    assert degraded["axes"] == {}
    assert degraded["fortune"] is None
    assert degraded["site_mutual_receptions"] == []

    for bad in (
        [],
        {"status": "success", "ephemeris": []},
        {"status": "success", "house_cusps_detail": {}},
        {"status": "success", "aspects": {}},
        {"status": "success", "mutual_receptions": {}},
    ):
        try:
            normalize(bad)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"malformed CET payload was accepted: {bad!r}")

    class _FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    original_get = adapter.requests.get
    try:
        adapter.requests.get = lambda *args, **kwargs: _FakeResponse({"status": "error", "message": "bad input"})
        try:
            adapter.fetch_chart({"year": 1990})
        except RuntimeError as exc:
            assert "non-success status" in str(exc)
        else:
            raise AssertionError("non-success CET status was accepted")

        adapter.requests.get = lambda *args, **kwargs: _FakeResponse(["not", "an", "object"])
        try:
            adapter.fetch_chart({"year": 1990})
        except RuntimeError as exc:
            assert "non-object JSON" in str(exc)
        else:
            raise AssertionError("non-object CET JSON was accepted")
    finally:
        adapter.requests.get = original_get

    print("PASS CET adapter self-test: complete, sparse, malformed and API-failure branches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
