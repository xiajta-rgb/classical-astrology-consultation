---
name: classical-astrology-consultation
description: Evidence-first classical astrology consultation for natal-chart interpretation. Use when a user provides a natal chart, birth-chart placements, chart screenshots/PDFs, or asks about personality, abilities, wealth, career, property, children, marriage, shared finances, timing, or the limits of what a chart can establish.
---

# Classical Astrology Consultation

## Mission

Turn a supplied natal chart into a traceable consultation:

`chart validation → chart facts → topic mapping → competing hypotheses → lordship/state analysis → cross-validation and falsification → graded conclusion → consulting translation → quality gate`

Prioritize astrological evidence over fluent prose. Do not replace chart structure with personality labels, generic encouragement, or invented certainty.

## Operating rules

1. Default to classical astrology. Use this order unless the user explicitly requests another tradition:
   `houses → house rulers → essential dignity → placement → aspects → reception/mutual reception → sect → angularity/cadency → Lot of Fortune → annual profections → transits`.
2. Treat houses 1, 2, 4, 5, 6, 7, 8, 10 and 11, their rulers, ruler placement and dignity, angularity, benefic/malefic condition, and aspects as primary evidence. Reception, mutual reception, Lot of Fortune, profection lord and dispositorship chains are secondary. Uranus, Neptune and Pluto are auxiliary only; never let modern outers overrule the classical structure.
3. Validate the chart before judging it. Record zodiac, house system, birth-time precision, location, degrees, Ascendant boundary risk, and day/night sect. Determine sect from the Sun’s position relative to the horizon, not from a sign or an assumed clock time. If the Ascendant is at 0°/29°–30° or the house system is unclear, branch the analysis or downgrade confidence; do not silently treat a cusp-sensitive chart as exact.
4. Separate fact extraction from interpretation. Build a `Chart Facts` inventory before explaining anything. Do not write personality or life conclusions while facts are still being extracted.
5. Route each question through a house-responsibility matrix. Do not make a strong claim without calling the houses that actually govern the question. See [references/house-matrix.md](references/house-matrix.md).
6. Do not collapse a house into one modern keyword. List the relevant traditional significations first, generate at least two competing hypotheses, then use additional rulers, occupants, aspects, dignity, Lot of Fortune, and timing to select a leading interpretation. Preserve unresolved alternatives as B/C-level possibilities.
7. Analyze every relevant planet in two separate dimensions: (a) what house(s) it rules and where it is placed; (b) how capable it is of delivering those matters. Check essential dignity, sect, angularity, speed, visibility, combustion, retrogradation, reception, applying aspects, and malefic/benefic condition when data permits. Apply sect as a weight modifier: in a day chart Jupiter is the in-sect benefic and Saturn the in-sect malefic; in a night chart Venus is the in-sect benefic and Mars the in-sect malefic. Do not erase other testimonies or turn sect into a binary good/bad switch. “Dignified” is not synonymous with “good”, and “debilitated” is not synonymous with “failure”.
8. Treat reception as typed data, not as a generic positive bond. Record domicile/exaltation/triplicity/term/face reception, direction, and whether an applying aspect actually connects the planets. Do not call a one-way reception “mutual reception”.
9. Keep classical and modern layers separate. The seven visible planets establish rulership, essential dignity, sect, primary house judgments, and core evidence scores. Uranus, Neptune, Pluto, Chiron, asteroids, nodes, and modern-only aspects may be mentioned only after the classical judgment, labeled auxiliary, and never used to overturn or independently upgrade a classical conclusion.
10. For every material conclusion, show `fact → rule → intermediate inference → conclusion`. A single placement cannot carry an entire-life conclusion.
11. Grade conclusions with the S/A/B/C/N/A scale in [references/evidence-and-language.md](references/evidence-and-language.md).
12. Always record both supporting and limiting testimonies. Actively search for at least one counter-testimony before finalizing a claim. Do not count the same underlying fact repeatedly as independent evidence.
13. Run anti-generalization and value checks before finalizing each important sentence:
   - **Swap-chart test**: would this still be true for many other charts? If yes, delete it or make it chart-specific.
   - **Uniqueness test**: why does this wording follow from this chart’s particular house-ruler chain?
14. Describe mechanisms and observable behavior, not moralized personality judgments. Prefer “个人判断更容易通过项目产出进入职业领域” over “你很有洞察力”; prefer “组织授权与资源统筹需要后天建立” over “你不够自信”.
15. Keep certainty calibrated. Never turn “可能” into “一定”, one symbol into an “人生主线”, or an astrology inference into a practical fact.
16. Distinguish **natal judgment** (what the chart signifies) from **consulting advice** (what the person may choose to do). Advice must be derived from earlier testimonies, not pasted-in life coaching.
17. Respect technical boundaries. Natal charts can describe structural tendencies; age-specific claims require profections; year/month/event claims require appropriate timing techniques; a specific house purchase or investment outcome cannot be confirmed from natal placements alone.

## Required workflow

### 1. Establish data quality and scope

Identify the chart source, zodiac, house system, exact birth time quality, location, and whether degrees are available. Mark missing or uncertain data before interpreting. If the user asks a timing question but supplies only a natal chart, state the limitation and offer the minimum additional technique/data needed.

Default to the [NATAL-1.0 natal-first architecture](references/natal-first-architecture.md): complete the natal Chart Facts, house responsibility chains, planetary-state audit, competing hypotheses and full-picture synthesis before activating any timing extension. Profections, transits, progressions, primary directions, zodiacal releasing and solar returns are inactive until the user explicitly asks a future-time question and the required data are available.

### 2. Build the Chart Facts inventory

Record, in neutral language:

- Ascendant, MC, sect (day/night), and chart ruler.
- All house cusps and each house ruler.
- Each planet’s sign, degree if known, house, essential dignity, sect condition, speed/visibility/combustion/retrogradation when available.
- Major applying/separating aspects, receptions and mutual receptions.
- Dispositor chains, angular/succedent/cadent status, benefic/malefic condition.
- Lot of Fortune and any supplied profection/annual-lord information.

Do not write “therefore you are…” in this section.

### 3. Map the user’s theme to houses

Select the relevant responsibility matrix, then scan the full chain rather than the most striking planet. For major themes, use the following minimum scans:

- **Money**: 2 → 8 → 11 → 5 → 10 → 4 → Lot of Fortune.
- **Property/home**: 4 → ruler of 4 → 2 → 8 → 10.
- **Children/creative output**: 5 → ruler of 5 → 1 → 4 → 8.
- **Career**: 10 → ruler of 10 → 1 → 6 → 7 → 11.
- **Marriage/shared finances**: 7 → ruler of 7 → 8 → 2 → 4.

See [references/house-matrix.md](references/house-matrix.md) for expanded mappings and boundary notes.

### 4. Generate and rank competing hypotheses

For each ambiguous testimony, write at least two traditional explanations before selecting one. Example: “2nd-ruler in 4th” can indicate family resources, household/property, fixed assets, family obligations, or end-of-life foundations. Then test each hypothesis against the 4th ruler, occupants, 2nd/8th/10th/11th houses, Lot of Fortune, receptions and timing. Do not output the most vivid hypothesis merely because it is vivid; state the leader, runner-up, and unconfirmed options.

### 5. Analyze lordship and planetary state

For each topic ruler, separate:

- **Responsibility**: which houses it rules and what those houses signify.
- **Placement**: where the ruler is located and which house receives the matter.
- **Capability**: dignity, sect, angularity, speed/visibility, combustion/retrogradation, reception, applying aspects, and benefic/malefic condition.
- **Delivery path**: dispositors and whether the planet can actually complete the matter.

Do not turn one dignity label into a final judgment. Explain how the planet’s condition modifies its ability to deliver its responsibilities.

### 6. Construct evidence chains

For every core claim, write an internal chain with four fields:

`Evidence:` exact placements/aspects/rulers.

`Rule:` the classical significations being applied.

`Inference:` the narrow structural consequence.

`Conclusion:` the user-facing statement with A/B/C certainty.

Example: “Mercury rules 1 and 4, is in the 5th in Scorpio, and trines Jupiter ruling 10 and placed in its domicile in the 10th. The 1st signifies the person’s agency, the 5th projects creative work, and the 10th signifies vocation. Therefore personal judgment is more likely to become career value through projects or creative output. **A-level career linkage** if the testimonies are applying/otherwise confirmed.”

### 7. Reconcile support, limits and conflicts

Make a compact table or prose pair for each major theme:

`supporting testimonies` + `limiting/contrary testimonies` → `balanced structural judgment`.

Name the actual tension (for example, expansion versus obligation, individual production versus organizational scaling, or resource leverage versus debt/risk). Do not hide conflicts behind positive language.

### 8. Produce the consultation

Use this fixed order unless the user asks for a shorter answer:

1. **核心判断** — 3–5 chart-specific claims only.
2. **证据结构** — evidence chain and A/B/C level for each claim.
3. **结构性优势** — concrete supported capacities, not praise.
4. **结构性矛盾** — named house/planet tensions and their mechanisms.
5. **用户所问主题** — the relevant financial, career, family, relationship, or property synthesis.
6. **风险边界** — where overextension, debt, conflict, or misjudgment is structurally more likely.
7. **咨询建议** — practical options derived from the chart, clearly labeled as advice.
8. **不可判断项** — what the natal chart cannot establish and which additional technique/data is required.

Use concrete wording such as “明确表现为”, “明显倾向于”, “可能涉及”, or “本命盘无法确认” according to evidence strength.

主题正文必须先经过[本命征象显著性筛选协议](references/interpretation-priority.md)：优先输出能改变主题责任链的 `critical/high` 征象；`supporting/context` 征象默认延后到审计层，不得用数量堆叠制造重要性。

### 9. Network research and system iteration

When new online astrology material is requested, use [references/research-ledger.md](references/research-ledger.md) as the intake register and execute the full [LOOP-1.0 research iteration](references/research-loop.md):

1. Identify the work, author, period, translator/editor, host, and chapter/page before extracting a rule.
2. Classify the item as primary historical text, later traditional synthesis, modern empirical research, or commentary. Do not merge the layers.
3. Record the historical claim in neutral language, then record scope conditions, independent support, counter-testimony, and modern status.
4. For death, disease, mental health, sexuality, reproduction, crime, violence, servitude, curses, or stigma, run [references/sensitive-significations.md](references/sensitive-significations.md) before any user-facing wording.
5. Convert useful passages into [references/quote-insight-cards.md](references/quote-insight-cards.md): preserve only short, versioned quotations; use paraphrase for longer material; attach tags, locator, conditions, counter-test and output guardrail.
6. Add rules only as versioned, reversible hypotheses. A new source can strengthen, qualify, downgrade, or remove a rule; “more material” is not automatically “more evidence”.
7. Run the source, rule, counter-test, anti-generalization, directness, sensitive-topic and full-picture gates. The lightweight checker is [scripts/check_research_loop.py](scripts/check_research_loop.py).
8. After each update, re-run representative chart judgments and check that the new rule does not create double counting, deterministic event claims, or modern outer-planet override.

The system may maintain this ledger across future user-requested research turns, but it must not imply autonomous background browsing or unverified continuous learning between turns.

## Quality gate

Before emitting a core conclusion, require all of the following:

1. It names why this chart, not a generic chart.
2. It can point to at least two genuinely independent testimonies for an S/A claim.
3. It includes a counter-testimony or explicitly says none was available.
4. It does not count the same planet, house, or aspect twice under different labels.
5. It passes the hypothesis-competition test: leading interpretation, runner-up, and unresolved limit are recorded where ambiguity exists.
6. It passes the consultation-value test: it adds structural information beyond a zodiac personality description.
7. It separates astrology fact, structural inference, observable translation, and advice in that order.

## Generic-advice blocklist

Do not use these as standalone conclusions: “你需要不断成长”, “找到平衡”, “发挥优势”, “提高认知”, “保持稳定”, “抓住机会”, “适合长期主义”, “不要过度焦虑”, “人生会经历变化”, “相信自己”, “突破舒适区”. If a practical recommendation is genuinely warranted, tie it to a named testimony and label it as advice. A lightweight checker is available at [scripts/check_consultation.py](scripts/check_consultation.py).

## Boundary and safety language

Astrology is an interpretive framework, not a guarantee of events or a substitute for medical, legal, financial, or safety-critical professional advice. For investments, property selection, medical outcomes, legal disputes, or other high-stakes decisions, present the astrological structure as one reflective input and explicitly recommend appropriate real-world due diligence.

## Reference files

- [references/house-matrix.md](references/house-matrix.md): theme-to-house responsibility matrix and technical boundaries.
- [references/evidence-and-language.md](references/evidence-and-language.md): evidence scoring, anti-generalization tests, certainty vocabulary, and output template.
- [references/judgment-algorithm.md](references/judgment-algorithm.md): hypothesis competition, planetary-state audit, counter-evidence, and duplicate-testimony controls.
- [references/sect-and-planetary-layers.md](references/sect-and-planetary-layers.md): day/night sect weighting and classical-versus-modern evidence hierarchy.
- [references/research-ledger.md](references/research-ledger.md): traceable online source intake, versioning, conflicts, and iterative updates.
- [references/research-campaign-20260814.md](references/research-campaign-20260814.md): current broad-source research lanes, quality filters, and distilled priorities.
- [references/sensitive-significations.md](references/sensitive-significations.md): sensitive-topic levels, prohibited deterministic outputs, and historical-language handling.
- [references/sensitive-dictionary.json](references/sensitive-dictionary.json): versioned multilingual/implicit sensitive markers used by the observation privacy gate.
- [references/quote-insight-cards.md](references/quote-insight-cards.md): short quotations, structured paraphrases, tags, conditions, counter-tests and output guardrails.
- [references/research-loop.md](references/research-loop.md): multi-round research, adversarial testing, directness protocol, full-picture snapshot, and rollback rules.
- [references/natal-first-architecture.md](references/natal-first-architecture.md): natal Chart Facts, topic chains, hypothesis cards, full-picture synthesis, and timing-extension boundary.
- [references/cet-api-integration.md](references/cet-api-integration.md): CET public ephemeris endpoint, field mapping, derived fly-in/reception rules, and verification limits.
- [references/ephh-integration.md](references/ephh-integration.md): local ephh/Swiss Ephemeris input contract, coordinate uncertainty, aspect generation and CET comparison limits.
- [references/interpretation-modules/registry.json](references/interpretation-modules/registry.json): decoupled natal interpretation modules for timing baseline, identity, wealth, career, relationships and family.
- [references/interpretation-priority.md](references/interpretation-priority.md): salience levels, primary-rule caps, deferred evidence and chart-specific prioritization.
- [references/loop-runs/LOOP-20260814.md](references/loop-runs/LOOP-20260814.md): current research/test rounds and next-round handoff.
- [references/loop-runs/ROUND93-STATUS.md](references/loop-runs/ROUND93-STATUS.md): current end-to-end research status, user-chart boundaries, and shortest HOLD-release path.
- [references/loop-runs/ROUND100-ARTIFACT-MANIFEST.json](references/loop-runs/ROUND100-ARTIFACT-MANIFEST.json): durable facts/audit/manifest/report SHA-256 snapshot.
- [scripts/check_research_loop.py](scripts/check_research_loop.py): fail-closed QA for traceability, specificity, coverage, sensitive-topic boundaries, and generic-language leakage.
- [scripts/check_natal_first.py](scripts/check_natal_first.py): prevents timing language from leaking into a natal-only draft without explicit activation.
- [scripts/cet_api_client.py](scripts/cet_api_client.py): read-only CET API fetcher and UTF-8 normalizer; preserves raw response for audit.
- [scripts/check_cet_api_adapter.py](scripts/check_cet_api_adapter.py): regression for complete CET field mapping and sparse/unknown response branches.
- [scripts/ephh_chart_client.py](scripts/ephh_chart_client.py): invokes the local ephh calculator through an isolated compatible interpreter and normalizes exact natal facts.
- [scripts/ephh_worker.py](scripts/ephh_worker.py): initializes ephh Swiss Ephemeris and adds the explicitly-labelled Chiron extra point.
- [scripts/check_ephh_chart_client.py](scripts/check_ephh_chart_client.py): offline regression for ephh normalization, sign cleanup and aspect candidate generation.
- [scripts/build_modular_interpretation.py](scripts/build_modular_interpretation.py): matches module rules to Chart Facts and renders evidence-linked topic reports without activating timing.
- [scripts/check_modular_interpretation.py](scripts/check_modular_interpretation.py): regression for module count, timing hold and topic evidence anchors.
- [scripts/validate_chart_facts.py](scripts/validate_chart_facts.py): validates traditional ruler fly-ins, deduplicates receptions, and classifies degree-dependent aspect geometry without inventing missing degrees.
- [scripts/rulership_candidates.py](scripts/rulership_candidates.py): enumerates dignity-based house/topic candidate claims without collapsing domicile, exaltation, triplicity, terms, and face into a score.
- [scripts/planetary_state.py](scripts/planetary_state.py): versioned sect, essential dignity, triplicity, terms, faces, and angularity state layer; missing degrees remain unresolved.
- [scripts/check_planetary_state.py](scripts/check_planetary_state.py): regression for declared-versus-unknown speed, retrograde, and visibility evidence.
- [scripts/build_natal_facts.py](scripts/build_natal_facts.py): combines Chart Facts, geometry/reception checks, planetary state, topic coverage and a fail-closed natal release gate.
- [scripts/render_natal_report.py](scripts/render_natal_report.py): renders an evidence-first natal audit, paragraph/source upgrade labels, and can recompute score output from raw cards plus registry before publication.
- [scripts/build_hypothesis_cards.py](scripts/build_hypothesis_cards.py): creates bounded H1/H2 natal hypothesis cards only after the release gate passes.
- [scripts/check_hypothesis_cards.py](scripts/check_hypothesis_cards.py): detects duplicated evidence, generic hypotheses, missing chart anchors, and forbidden auto-upgrades.
- [scripts/score_hypothesis_cards.py](scripts/score_hypothesis_cards.py): applies transparent 1.0/0.5 unique-versus-shared evidence weighting, source limits, version gates, counter-test classification, and publication reasons without automatic S/A upgrades.
- [scripts/compare_score_outputs.py](scripts/compare_score_outputs.py): compares before/after score outputs and proves that observation withdrawal or supersession changes only the intended topic set.
- [scripts/build_release_manifest.py](scripts/build_release_manifest.py): combines chart gate, score, source, dictionary and score-diff states into a fail-closed machine-readable release manifest.
- [scripts/check_source_registry.py](scripts/check_source_registry.py): validates evidence provenance IDs, source status, and conflict-cluster references.
- [scripts/build_artifact_fingerprint.py](scripts/build_artifact_fingerprint.py): creates deterministic SHA-256 snapshots for facts, audits, manifests and rendered reports.
- [scripts/check_release_bundle.py](scripts/check_release_bundle.py): recomputes the release manifest and verifies all artifact hashes in one pre-publication gate.
- [scripts/check_release_gates.py](scripts/check_release_gates.py): adversarial regression for locked-rule/missing-metadata combinations, source HOLD propagation, paragraph BLOCKED labels, and scorer grade caps.
- [scripts/validate_observations.py](scripts/validate_observations.py): validates versioned real-world observations, active/withdrawn tombstones, sensitive privacy gates, and chart-fact separation.
- [scripts/check_sensitive_dictionary.py](scripts/check_sensitive_dictionary.py): compares sensitive-dictionary versions against regression samples and reports added/removed markers and changed classifications.
- [scripts/check_research_assets.py](scripts/check_research_assets.py): cross-checks quote-insight-card IDs, statuses, pending cards, and source IDs against the source registry without upgrading draft material.
- [scripts/check_user_chart_input.py](scripts/check_user_chart_input.py): regression-checks the complete user-supplied natal summary and keeps missing birth metadata fail-closed.
- [scripts/check_reception_connections.py](scripts/check_reception_connections.py): adversarial regression for direction-only, sector-only, degree-confirmed, and unsupported reception branches.
- [references/source-registry.json](references/source-registry.json): machine-readable source layers, versions, limits, and unresolved conflict clusters.
- [references/research-asset-audit.json](references/research-asset-audit.json): latest quote-card/source/capability cross-audit; warnings remain visible and do not upgrade evidence.
- Pending research cards carry P0/P1/P2 priorities; priority is workflow order only and never an evidence upgrade.
- [references/fixtures/user-chart-1996-supplied.json](references/fixtures/user-chart-1996-supplied.json): supplied chart fixture with missing metadata retained as an intentional hold-case.
- [references/fixtures/sensitive-observation-cases.json](references/fixtures/sensitive-observation-cases.json): regression samples for sensitive-marker recall and benign false-positive control.
