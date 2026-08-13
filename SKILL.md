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
3. Validate the chart before judging it. Record zodiac, house system, birth-time precision, location, degrees, Ascendant boundary risk, and day/night sect. If the Ascendant is at 0°/29°–30° or the house system is unclear, branch the analysis or downgrade confidence; do not silently treat a cusp-sensitive chart as exact.
4. Separate fact extraction from interpretation. Build a `Chart Facts` inventory before explaining anything. Do not write personality or life conclusions while facts are still being extracted.
5. Route each question through a house-responsibility matrix. Do not make a strong claim without calling the houses that actually govern the question. See [references/house-matrix.md](references/house-matrix.md).
6. Do not collapse a house into one modern keyword. List the relevant traditional significations first, generate at least two competing hypotheses, then use additional rulers, occupants, aspects, dignity, Lot of Fortune, and timing to select a leading interpretation. Preserve unresolved alternatives as B/C-level possibilities.
7. Analyze every relevant planet in two separate dimensions: (a) what house(s) it rules and where it is placed; (b) how capable it is of delivering those matters. Check essential dignity, sect, angularity, speed, visibility, combustion, retrogradation, reception, applying aspects, and malefic/benefic condition when data permits. “Dignified” is not synonymous with “good”, and “debilitated” is not synonymous with “failure”.
8. Treat reception as typed data, not as a generic positive bond. Record domicile/exaltation/triplicity/term/face reception, direction, and whether an applying aspect actually connects the planets. Do not call a one-way reception “mutual reception”.
9. For every material conclusion, show `fact → rule → intermediate inference → conclusion`. A single placement cannot carry an entire-life conclusion.
10. Grade conclusions with the S/A/B/C/N/A scale in [references/evidence-and-language.md](references/evidence-and-language.md).
11. Always record both supporting and limiting testimonies. Actively search for at least one counter-testimony before finalizing a claim. Do not count the same underlying fact repeatedly as independent evidence.
12. Run anti-generalization and value checks before finalizing each important sentence:
   - **Swap-chart test**: would this still be true for many other charts? If yes, delete it or make it chart-specific.
   - **Uniqueness test**: why does this wording follow from this chart’s particular house-ruler chain?
13. Describe mechanisms and observable behavior, not moralized personality judgments. Prefer “个人判断更容易通过项目产出进入职业领域” over “你很有洞察力”; prefer “组织授权与资源统筹需要后天建立” over “你不够自信”.
14. Keep certainty calibrated. Never turn “可能” into “一定”, one symbol into an “人生主线”, or an astrology inference into a practical fact.
15. Distinguish **natal judgment** (what the chart signifies) from **consulting advice** (what the person may choose to do). Advice must be derived from earlier testimonies, not pasted-in life coaching.
16. Respect technical boundaries. Natal charts can describe structural tendencies; age-specific claims require profections; year/month/event claims require appropriate timing techniques; a specific house purchase or investment outcome cannot be confirmed from natal placements alone.

## Required workflow

### 1. Establish data quality and scope

Identify the chart source, zodiac, house system, exact birth time quality, location, and whether degrees are available. Mark missing or uncertain data before interpreting. If the user asks a timing question but supplies only a natal chart, state the limitation and offer the minimum additional technique/data needed.

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
