# Data audit, round 2 (2026-11-10)

Owner: "have those agents check every data not just the election data". The same four reviewers who audited the National Council data audited every theme. All work was read-only. The reviewers were:
- an elections expert (Mobility, Energy & climate, Environment & hazards)
- a statistician (Population, Migration, Households, Language & religion, Health & social, Education, Safety)
- a mathematician (Economy, Income & tax, Public finances, Housing, Real estate, and the shared machinery)
- a data journalist (Geography, Land use, and presentation of all themes)

Their scripts, CSVs and screenshots were kept in the session scratchpad. This file is the consolidated, prioritised fix list. The election-specific rules are in D37, the "maps must tell a story" rule in D38, and the hub rule in D39.

## What is correct (verified against the live publishers)
- STATPOP, demographic balance, migration and naturalisation: 1,702 cells checked against BFS PxWeb (CH, 26 cantons and 14 municipalities, 2025 and 2015). They match exactly, apart from Moutier and later mergers, which differ by design.
- STATENT jobs (CH and municipalities, 2014 and 2024), vehicles (BFS SDMX 2025), and the city tax burden (the live file is byte-identical to ours) match exactly. Vacancy rate is within 0.007 pp. BLN share CH is 19.1 % (BAFU: 19 %).
- National Council party strengths: municipalities match exactly. Cantons and CH are within 0.005 pp, apart from the FDP/LPS and Moutier items in D37.
- Parts add up to totals for sectors, building and dwelling types, income classes, age, sex, nationality and household sizes. Ratios are recomputed from sums, and medians are not re-aggregated.

## Must fix

| # | Defect | Evidence | Fix |
|---|---|---|---|
| M1 | One suppressed municipality blanks every total above it | 18 jobs in 5315 blank total jobs for TI, VD and VS. Tertiary education is blank in 12 cantons and CH. Commuting is blank for BE, GR, VS, TI, FR and CH. | Aggregate when the suppressed share of the base is ≤ 1 %, flagged as an estimate (the error is bounded). Ingest the published canton/CH tables (STATENT, UDEMO, federal tax). |
| M2 | Published fallback taken on a different boundary vintage | BE/JU household sizes and births mix Moutier in BE with Moutier in JU | Use a fallback only when its vintage matches the current boundaries; otherwise leave a gap with its reason |
| M3 | Amounts not attributable to a municipality are left out of CH and canton totals | Construction spending CH 59.0 bn vs 67.5 bn (−12.5 %). CH emigration −2.0 %, net migration +3.8 %. Vehicles −0.38 %. | Add the unallocated rows to canton and CH sums (`include_pseudo`), or prefer the published value. Label sub-canton totals. |
| M4 | Default year differs between levels of the same metric | 54 metrics: commuting 2018 vs 2020, social assistance 2024 vs 2025, UDEMO 2016–2022, STATENT sectors 2022/23 vs 2024 | One default period per metric across all levels (generic fix in the election build) |
| M5 | Per-resident climate and energy metrics only at municipality level | The weighted mean looks for a population weight of the same period ("1991-2020", "2026-10") | Use the nearest population year as weight, or define as a ratio to population |
| M6 | Births from a gapped source | 281 municipalities suppressed although the demographic-balance cube has all 2,110 | Births from the demographic balance from 1981 onwards |
| M7 | Duplicates that disagree | Two EV shares (5.5 % vs 5.16 %), two vacancy rates, `bil_naturalisations` = `nat_total`, `bil_pop_dec` = `pop_total`, `com_leave_unit` = `com_out_commuters` at municipality level | Keep one on maps (BFS); move or hide the others |
| M8 | Hazards look national but cover 19 of 26 cantons | Missing: GR, SG, VD, UR, NW, OW, BS | Municipality level only, with coverage note and "rank among covered" |
| M9 | Tiny or special municipalities top rankings | Income #1 Vaux-sur-Morges (185 residents). Cars per 1000: Appenzell 2,793 (fleets). Social assistance max: Schelten (37). | Small-number flag on every ratio (denominator rules). Flagged units out of top-N lists and class breaks by default. |

## Should fix
- **Definitions**:
  - Naturalisation rate: 1 Jan denominator, as BFS uses (1.651 vs our 1.609).
  - Birth rate: mean population (8.60 vs our 8.56).
  - `share_married`: exclude children from the denominator.
  - Census vs Structural Survey languages: say why they differ.
  - Do not chain census households into register households.
- **Years and vintages**:
  - Census 2000 headlines get the year in their titles and their own "Census 2000" group.
  - Structural Survey language values for cantons: derive from the district sums.
  - Unemployment: put the VD monthly snapshots in a separate metric.
  - Social assistance 2025: mark the series break.
  - Moutier: note it on pre-2026 JU values.
- **Energie Reporter**: label as modelled and show the data date. Drop broken months (electricity −11 %/+14 %, charging-point dips, solar +21 %).
- **Regional values** (canton rents, tax burden by labour-market area): rank at their native level. The regression clusters at the coarsest native level of any regressor.
- **Labels**:
  - Fix the "agglomertation" typo.
  - Fix the German "zum/zur" template.
  - Directions: residents within reach is not higher-is-better, and electricity per capita should not penalise industry.
  - `com_out_share` label above municipality level.
  - Show definitions everywhere; 368 metrics have no description yet.
- **Precision**: make precision consistent between card and statistics (social assistance). Rank on unrounded values. Spearman with weights.
- **To verify**:
  - Lowest point below lake level (Lausanne 368 m, Lugano 269 m).
  - Mean elevation including lake surfaces.
  - Geneva hazard coding (2.5 % red zones).
  - Matran vacancy rate of 10 %.

## Curation (D38)
The four reviewers wrote a verdict for every metric × level: SHOW, SHOW-WITH-NOTE, HIDE-AT-LEVEL or HIDE-FROM-MAPS, each with a reason. The proposed generic rule (mathematician):
- **SHOW**: ≥ 80 % of units and of population have a value.
- **SHOW-WITH-NOTE**: ≥ 25 % of units, 50 % of population and ≥ 20 units.
- **Levels with fewer than 20 units** (urban/rural, municipality type, language region, major region): shown only if every unit has a value.
- **Regional values**: always with a note.
- **Never a map**: confidence intervals and technical denominators.

The rule runs after M1, so maps are not hidden because of a fixable aggregation gap. Applied to the current data it hides about 634 of 5,024 metric × level maps, and 64 metrics would have no map at all, including:
- land price (30 municipalities)
- cantonal unemployment and public finances
- crime until the national data lands
- tertiary education at urban/rural level

City-only data (tax burden and rents for 179–180 cities) becomes a separate cities layer.

**Featured story maps** (journalist):
- population density
- 10-year population change
- share 65+
- foreign share
- cross-border commuters
- mean taxable income
- tax burden by labour-market area
- tertiary education
- vacancy rate (districts)
- second homes vs the 20 % limit
- PT time to the nearest hub
- heat pumps
- latest vote as difference from the national result
- SVP 2023 with single-seat cantons marked
- French share (Structural Survey, districts)

## Order of work
1. Elections (D37) and the generic default-period fix (M4): in progress.
2. Travel times (D39 hubs, station choice, several weekdays): in progress.
3. National crime data (BFS PKS by district, canton and city): in progress.
4. Data machinery batch: M1–M3 and M5–M9 plus the should-fix items.
5. Curation file and enforcement (D38), featured maps.
