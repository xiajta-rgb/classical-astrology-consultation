#!/usr/bin/env python3
"""Event-based birth-time validation for the local classical astrology engine.

The script ranks candidate birth times from dated observations. It never edits
the natal chart from an event and never treats a single aspect as proof.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from astrology_engine import calculate_natal  # noqa: E402
from astrology_engine.predictive import calculate_predictive  # noqa: E402
from astrology_engine.predictive_events import scan_progressive_window  # noqa: E402


SIGN_RULERS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
EVENT_TARGETS: dict[str, dict[str, set[str]]] = {
    "relationship_intimacy": {
        "houses": {1, 5, 7, 8},
        "points": {"Venus", "Mars", "Moon", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Moon", "Venus", "Saturn", "Mars"},
    },
    "academic_result": {
        "houses": {3, 6, 9, 10},
        "points": {"Mercury", "Jupiter", "Sun", "Mars", "Ascendant", "Midheaven"},
        "preferred_lords": {"Jupiter", "Mercury", "Moon"},
    },
    "health": {
        "houses": {1, 6, 8, 12},
        "points": {"Moon", "Mars", "Jupiter", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Jupiter", "Mars", "Saturn", "Moon"},
    },
    "employment_exit": {
        "houses": {2, 6, 7, 10, 12},
        "points": {"Sun", "Moon", "Mars", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Mars", "Saturn", "Sun", "Mercury"},
    },
    "employment_entry": {
        "houses": {2, 6, 10, 11},
        "points": {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Mars", "Sun", "Venus", "Jupiter"},
    },
    "family_asset_transfer": {
        "houses": {2, 4, 8, 11},
        "points": {"Sun", "Moon", "Venus", "Mars", "Jupiter", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Sun", "Venus", "Mercury", "Jupiter", "Saturn"},
    },
    "institutional_transition": {
        "houses": {6, 9, 10, 12},
        "points": {"Sun", "Moon", "Mars", "Jupiter", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Mars", "Saturn", "Jupiter", "Sun"},
    },
    "family_loss": {
        "houses": {4, 8, 10, 12},
        "points": {"Moon", "Venus", "Mars", "Saturn", "Ascendant", "Midheaven"},
        "preferred_lords": {"Moon", "Venus", "Saturn", "Mars"},
    },
}


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _sign_index(longitude: float) -> int:
    return int(float(longitude) % 360 // 30)


def _ruler_houses(natal: dict[str, Any]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    cusps = natal["houses"]["house_cusps"]
    for house, cusp in enumerate(cusps, start=1):
        result.setdefault(SIGN_RULERS[_sign_index(cusp)], []).append(house)
    return result


def _active_firdaria(result: dict[str, Any]) -> list[str]:
    age = float(result["target_age"])
    active: list[str] = []
    for major in result.get("periods", []):
        if major["start_age"] <= age < major["end_age"]:
            active.append(major["planet"])
            for sub in major.get("sub_periods", []):
                if sub["start_age"] <= age < sub["end_age"]:
                    active.append(sub["planet"])
            break
    return active


def _event_date(event: dict[str, Any]) -> datetime:
    raw = event.get("date") or event.get("datetime")
    if not raw:
        raise ValueError(f"event {event.get('id', '<unknown>')} has no date")
    return _parse_dt(str(raw) + ("T12:00:00" if len(str(raw)) == 10 else ""))


def _candidate_times(center: datetime, radius: int, step: int) -> list[datetime]:
    if step <= 0:
        raise ValueError("candidate step must be positive")
    return [center + timedelta(minutes=minute) for minute in range(-radius, radius + 1, step)]


def _cluster_event_rows(event_rows: list[dict[str, Any]], tolerance_days: int) -> list[dict[str, Any]]:
    """Group nearby manifestations so one timing contact is not counted twice."""
    ordered = sorted(event_rows, key=lambda row: row["event_date"])
    clusters: list[dict[str, Any]] = []
    for row in ordered:
        event_date = datetime.fromisoformat(row["event_date"])
        if not clusters:
            clusters.append({"event_ids": [row["event_id"]], "rows": [row], "last_date": event_date})
            continue
        current = clusters[-1]
        if (event_date - current["last_date"]).days <= tolerance_days:
            current["event_ids"].append(row["event_id"])
            current["rows"].append(row)
            current["last_date"] = event_date
        else:
            clusters.append({"event_ids": [row["event_id"]], "rows": [row], "last_date": event_date})
    normalized: list[dict[str, Any]] = []
    for index, cluster in enumerate(clusters, start=1):
        rows = cluster["rows"]
        union_groups = sorted({group for row in rows for group in row["independent_groups"]})
        normalized.append({
            "cluster_id": f"C{index}",
            "event_ids": cluster["event_ids"],
            "date_span": [rows[0]["event_date"], rows[-1]["event_date"]],
            "independent_groups": union_groups,
            "group_score": len(union_groups),
            "lord_fit_score": round(max(row.get("fit_score", 0.0) for row in rows), 2),
        })
        for row in rows:
            row["event_cluster"] = f"C{index}"
            row["cluster_note"] = "same_time_cluster" if len(rows) > 1 else "independent_event"
    return normalized


def _scan_contacts(
    technique: str,
    birth: datetime,
    event_dt: datetime,
    *,
    tolerance_days: int,
    targets: dict[str, set[str]],
    base: dict[str, Any],
    moving_bodies: set[str] | None = None,
) -> list[dict[str, Any]]:
    rows = scan_progressive_window(
        technique,
        birth,
        start_datetime=event_dt - timedelta(days=tolerance_days),
        end_datetime=event_dt + timedelta(days=tolerance_days),
        step_days=1,
        applying_orb=3,
        separating_orb=1,
        **base,
    )
    allowed_aspects = {"conjunction", "square", "opposition"}
    moving_bodies = moving_bodies or {"Moon"}
    return [
        row for row in rows
        if row.get("moving_body") in moving_bodies
        and row.get("natal_point") in targets["points"]
        and row.get("aspect") in allowed_aspects
    ]


def _score_event(
    birth: datetime,
    natal: dict[str, Any],
    event: dict[str, Any],
    *,
    tolerance_days: int,
    base: dict[str, Any],
) -> dict[str, Any]:
    domain = str(event["domain"])
    targets = EVENT_TARGETS.get(domain)
    if targets is None:
        raise ValueError(f"unsupported event domain: {domain}")
    event_tolerance_days = int(event.get("tolerance_days", tolerance_days))
    event_dt = _event_date(event)
    ruler_houses = _ruler_houses(natal)
    evidence: list[dict[str, Any]] = []
    groups: set[str] = set()
    fit_score = 0.0

    firdaria = calculate_predictive("firdaria", birth, target_datetime=event_dt, **base)["result"]
    profection = calculate_predictive("profection", birth, target_datetime=event_dt, **base)["result"]
    active = _active_firdaria(firdaria)
    relevant_lords = [
        planet for planet in active + [profection.get("year_ruler", "")]
        if set(ruler_houses.get(planet, [])) & targets["houses"]
        or natal.get("placements", {}).get(planet, {}).get("house_number") in targets["houses"]
    ]
    if relevant_lords:
        groups.add("time_lord")
        fit_score += 0.75 * len(set(relevant_lords) & targets.get("preferred_lords", set()))
        fit_score += 0.25 if profection.get("year_ruler") in targets.get("preferred_lords", set()) else 0.0
        evidence.append({
            "group": "time_lord",
            "active_firdaria": active,
            "profection_house": profection.get("profection_house"),
            "year_ruler": profection.get("year_ruler"),
            "relevant_planets": sorted(set(relevant_lords)),
        })

    for technique, group in (("secondary", "secondary_moon"), ("tertiary", "tertiary_moon")):
        contacts = _scan_contacts(technique, birth, event_dt, tolerance_days=event_tolerance_days, targets=targets, base=base)
        if contacts:
            groups.add(group)
            best = min(contacts, key=lambda row: float(row.get("orb", 99)))
            evidence.append({
                "group": group,
                "count": len(contacts),
                "best_contact": {
                    "date": best.get("datetime"),
                    "natal_point": best.get("natal_point"),
                    "aspect": best.get("aspect"),
                    "orb": best.get("orb"),
                    "direction": best.get("direction"),
                    "profile": best.get("calculation_profile"),
                    "natal_house": natal.get("placements", {}).get(best.get("natal_point"), {}).get("house_number"),
                },
            })

    solar_arc = _scan_contacts(
        "solar_arc", birth, event_dt, tolerance_days=tolerance_days, targets=targets, base=base,
        moving_bodies={"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"},
    )
    if solar_arc:
        groups.add("solar_arc")
        best = min(solar_arc, key=lambda row: float(row.get("orb", 99)))
        evidence.append({"group": "solar_arc", "count": len(solar_arc), "best_contact": {
            "date": best.get("datetime"), "moving_body": best.get("moving_body"),
            "natal_point": best.get("natal_point"), "aspect": best.get("aspect"),
            "orb": best.get("orb"), "direction": best.get("direction"),
        }})

    transit = _scan_contacts("transit", birth, event_dt, tolerance_days=tolerance_days, targets=targets, base=base)
    if transit:
        groups.add("transit")
        best = min(transit, key=lambda row: float(row.get("orb", 99)))
        evidence.append({"group": "transit", "count": len(transit), "best_contact": {
            "date": best.get("datetime"), "natal_point": best.get("natal_point"),
            "aspect": best.get("aspect"), "orb": best.get("orb"), "direction": best.get("direction"),
        }})

    birth_anniversary = birth.replace(year=event_dt.year)
    return_year = event_dt.year if event_dt >= birth_anniversary else event_dt.year - 1
    for technique, group, kwargs in (
        ("solar_return", "solar_return", {"target_year": return_year}),
        ("lunar_return", "lunar_return", {"target_datetime": event_dt}),
    ):
        package = calculate_predictive(technique, birth, **kwargs, **base)
        return_result = package["result"]
        relevant = []
        for planet, row in return_result.get("planets", {}).items():
            if planet in targets["points"] and row.get("house_number") in targets["houses"]:
                relevant.append({"planet": planet, "house": row.get("house_number")})
        if relevant:
            groups.add(group)
            evidence.append({"group": group, "return_year": return_year, "relevant_planets": relevant})

    return {
        "event_id": event.get("id"),
        "domain": domain,
        "event_date": event_dt.date().isoformat(),
        "tolerance_days": event_tolerance_days,
        "independent_groups": sorted(groups),
        "score": len(groups),
        "fit_score": round(fit_score, 2),
        "evidence": evidence,
    }


def validate(
    *,
    birth_date: str,
    center_time: str,
    events: list[dict[str, Any]],
    lat: float,
    lon: float,
    tz: float,
    house_system: str = "P",
    radius_minutes: int = 30,
    step_minutes: int = 5,
    tolerance_days: int = 10,
) -> dict[str, Any]:
    center = _parse_dt(f"{birth_date}T{center_time}:00")
    base = {"lat": lat, "lon": lon, "tz": tz, "house_system": house_system}
    candidates: list[dict[str, Any]] = []
    for birth in _candidate_times(center, radius_minutes, step_minutes):
        natal = calculate_natal(birth, **base)
        event_rows = [_score_event(birth, natal, event, tolerance_days=tolerance_days, base=base) for event in events]
        event_clusters = _cluster_event_rows(event_rows, tolerance_days)
        group_score = sum(cluster["group_score"] for cluster in event_clusters)
        lord_fit_score = round(sum(cluster["lord_fit_score"] for cluster in event_clusters), 2)
        total = round(group_score + lord_fit_score, 2)
        candidates.append({
            "birth_time": birth.strftime("%H:%M"),
            "birth_datetime": birth.isoformat(),
            "ascendant": natal["houses"]["asc"],
            "mc": natal["houses"]["mc"],
            "chart_id": natal["chart_id"],
            "total_score": total,
            "group_score": group_score,
            "lord_fit_score": lord_fit_score,
            "event_count": len(event_rows),
            "event_rows": event_rows,
            "event_clusters": event_clusters,
        })
    candidates.sort(key=lambda row: (-row["total_score"], row["birth_datetime"]))
    return {
        "schema_version": "BIRTH-TIME-VALIDATION-1.0",
        "status": "ready",
        "method": "natal_first_event_window_cross_validation",
        "birth_date": birth_date,
        "center_time": center_time,
        "candidate_range_minutes": radius_minutes,
        "candidate_step_minutes": step_minutes,
        "event_tolerance_days": tolerance_days,
        "events": events,
        "candidates": candidates,
        "limitations": [
            "This is a calibration aid, not proof of a birth time.",
            "Primary directions and zodiacal releasing are not silently substituted because they are not production implementations.",
            "Sensitive health and family-loss events are scored as domain/timing corroboration, not diagnosis or mortality prediction.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--birth-date", required=True)
    parser.add_argument("--center-time", required=True, help="HH:MM")
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--tz", type=float, default=8.0)
    parser.add_argument("--house-system", default="P")
    parser.add_argument("--radius-minutes", type=int, default=30)
    parser.add_argument("--step-minutes", type=int, default=5)
    parser.add_argument("--tolerance-days", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.events.read_text(encoding="utf-8"))
    events = payload if isinstance(payload, list) else payload.get("birth_time_validation", {}).get("events", [])
    if not events:
        raise SystemExit("events file must contain a list or birth_time_validation.events")
    result = validate(
        birth_date=args.birth_date,
        center_time=args.center_time,
        events=events,
        lat=args.lat,
        lon=args.lon,
        tz=args.tz,
        house_system=args.house_system,
        radius_minutes=args.radius_minutes,
        step_minutes=args.step_minutes,
        tolerance_days=args.tolerance_days,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
