# Project-local astrology engine

This folder contains the calculation subset copied from the ephh project at
`C:/Users/xiajt/Documents/trae_projects/ephh`. It is intentionally separate
from the knowledge modules and contains no web server, database, client store,
or API credentials.

The public entry points are `natal.py`, `significations.py`, `predictive.py` and
`predictive_events.py`. `identity.py` supplies the shared chart identity used
by natal and predictive envelopes. They expose one common envelope for
the following techniques:

- secondary progression (day-for-a-year)
- tertiary progression (day-for-a-month)
- solar-arc progression
- solar return and lunar return
- transit chart and transit-to-natal contact scanning
- Firdaria and annual profection
- essential dignities (including Egyptian terms, triplicity, face and basic accidental condition) and mutual reception

All calculations use tropical positions and Placidus (`P`) by default. Whole Sign (`W`) is supported as an explicit comparison mode. Inputs
accept a place name or explicit latitude/longitude, plus timezone and local
birth time. Use `timezone_name` with an IANA zone when historical/DST-aware
calculation is required; otherwise `tz` is treated as a declared fixed offset.
Place-name resolution is explicit, recorded, and marked as a
centroid warning; it never silently claims an exact birth address. Unsupported
house systems fail closed. Swiss
Ephemeris data is bundled under `ephh_core/ephe` and is
configured automatically before each calculation.

The copied source revision and file hashes are recorded in `MANIFEST.json`.
The algorithms remain candidate computational infrastructure; they do not by
themselves determine an event or replace the project's evidence and timing
guardrails.

Timing snapshots and window scans are separate outputs: a snapshot never
counts as a timed event until an explicit scan/refinement call supplies a
window, step and contact direction. `technique_registry.json` is the activation contract. It records required
inputs, time resolution, provenance and fallback policy. Horosa-derived
methods that are not yet locally equivalent remain `candidate_external_parity`;
Vedic calculation rules are not part of the production classical layer.

## Optional insight layers migrated from ephh

The engine also exposes two explicit-topic, auxiliary layers:

- `astrology_engine.mbti.calculate_mbti(chart)` runs the migrated MBTI
  dimension and Jungian-function scoring, including the calculation trace.
- `astrology_engine.tpes.calculate_tpes(chart)` runs the migrated TPES career
  style model, with fixed 2/6/10 career-axis budgets and a full score
  breakdown.

Both accept the natal envelope returned by `calculate_natal` (and compatible
legacy `placements`/`planets` payloads). They are available through the
`personality`/`mbti` and `career`/`work` consultation topics respectively and
are returned under `run_natal_pipeline(...)["insights"]`. They are symbolic
interpretation aids, not psychological diagnoses, validated personality
inventories, occupational aptitude tests, success probabilities, or a
substitute for the classical house/ruler judgment.

The boundary and regression rationale is recorded in
`references/insight-layer-audit.md`.

The insight outputs also expose an `astrology_audit` (MBTI) or
`career_profile.classical_axis_audit` (TPES). These fields preserve the
classical 1/2/6/10/11-house responsibility chain, ruler placement, sect and
auxiliary-planet boundary. TPES core budgets use only the seven visible
planets; outer planets and modern aspects remain auxiliary. Tied career-axis
evidence is ordered 10th → 2nd → 6th, and duplicate occupant/ruler testimony
is not counted twice. MBTI aspect contributions are limited to the functions
of the two planets actually forming the aspect, rather than assigning every
harmonious/tense aspect to a blanket function group.
