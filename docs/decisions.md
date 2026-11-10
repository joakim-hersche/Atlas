# Decisions log

Owner decisions, newest last. The `recommendation` column in `data_catalog.csv` reflects these decisions.

## Checkpoint 1 — data review (2026-11-09, closed)

### D1. Strong themes approved as proposed
Approved without changes: Geography & identity, Population & demography, Migration & nationality, Households & family, Economy & jobs, Income & tax, Housing & buildings, Land use & built environment, Mobility & accessibility, Politics. The include/maybe/exclude values in `data_catalog.csv` for these themes now stand as decisions.

### D2. Filling national gaps from local sources, marked with *
Where no national municipality-level source exists, a metric may be **compiled from local sources** (cantonal statistical offices, cities) and shown with an asterisk (`*`).
- `*` means: compiled by Gemeindebank from several local publishers. Coverage may be incomplete, and definitions may differ between publishers. The tooltip and the sources page list which cantons/cities are covered and the source for each.
- Applies to the gap themes (e.g. public finances, property prices, crime, unemployment), decided theme by theme.
- Consequences for later phases: one connector per local publisher, a coverage map per `*` metric, and the cantonal hosts must be allowed in the environment.

### D3. Language & religion: option B
- Municipality level: census values (language 1860–2000, religion 1850–2000), shown for 2000 with change since 1970, labeled "census 2000".
- Each profile also shows its **district's** current language shares from the Structural Survey (3-year pooled, with confidence intervals), labeled "district, survey".
- City-level survey values (~170 cities) are not used, to avoid mixing levels on one map.
- Catalog: `bfs_se_language_bezirk` → include, `bfs_se_language_cities` → exclude.

### D4. Public finances: option B
- National: city finances from BFS SDMX (~180 cities, 2023), labeled as cities (`bfs_ssv_city_finances` → include).
- Plus a `*` compilation of about five standard HRM2 ratios per municipality from cantonal sources (`kt_gemeindefinanzen_compiled`, placeholder row until verified).
- Prerequisite: a **cantonal sweep** before Phase 3 to establish which cantons publish municipal finances, in what format and license. Needs cantonal hosts allowed. If coverage turns out thin, fall back to cities only.

### D5. Real estate prices: option B
- Regional values attached to each municipality, labeled "region": rent per m² by labour-market region and canton (Structural Survey), and the BFS property price index trend for the municipality's type.
- Census rent classes 1970–2000 as history.
- `*` compilation of cantonal municipal property/land prices (ZH known, others via the cantonal sweep), one metric per price type.

### D6. Standing rule: apply the D4/D5 pattern wherever the choice is similar
Owner instruction: where a theme has a national or regional fallback and a possible `*` compilation from local sources, take **option B** (fallback + `*` compilation) without asking again. Applied so far:
- **Safety:** district crime rates (BFS, national) and the ~27-city table included; `*` municipal crime statistics from cantonal police/statistics (`kt_crime_gemeinde_compiled`).
- **Environment & hazards:** cantonal hazard maps (Gefahrenkarten) as a `*` compilation (`cantonal_gefahrenkarten` → include; the cantonal geodata hub geodienste.ch is the lead).
- **Education:** `*` pupils and schools per municipality from cantonal education statistics (`kt_pupils_schools_compiled`); canton values as fallback.
- **Economy & jobs (extension of D1):** `*` registered unemployment per municipality from cantonal labour-market offices (`kt_unemployment_gemeinde_compiled`); cities and cantons as fallback.
All `*` rows are placeholders (`verified = no`) until the cantonal sweep.

### D7. Energy & climate, Environment & hazards, Health & social, Education: approved as proposed
- Energy: include Energie Reporter, solar potential, PV capacity, Energiestadt, climate normals 1991–2020 (settlement-weighted); maybe charging points, Minergie, district heating, biomass.
- Environment: include population-weighted air quality and protected-area share; maybe noise (effort L), radon, earthquake zone, national hazard overviews.
- Health & social: include social assistance rate, health-sector jobs, distance to services, health insurance premiums (once hosts allowed); maybe canton-only supply figures.
- Education: include attainment and completion rates; maybe higher-education presence, district Matura rate.
The catalog already carried these values; no row changes.

### D8. Reference vintage: latest state
All data is shown on the **latest municipality state** (currently 2026-01-01, 2,110 municipalities). History is reprojected onto it. The reference moves forward each January after mergers; the pipeline rebuilds the crosswalk accordingly.

### D9. Reach hubs: the proposed 20
Zürich HB, Bern, Basel SBB, Genève, Lausanne, Luzern, St. Gallen, Winterthur, Lugano, Bellinzona, Chur, Biel/Bienne, Fribourg, Sion, Zug, Aarau, Olten, Schaffhausen, Neuchâtel, Thun.

### D10. Public-transport reach
- Mode: **all public transport** (train, bus, tram, boat, cableway), labeled "public transport" in the UI.
- Time: **median travel time over departures 07:30–08:30 on a typical weekday** (exact reference date chosen from the GTFS feed in Phase 3; avoid holidays).
- Drawing: lines along real rail track (BAV rail network); bus legs drawn simplified.

### D11. Car reach: typical weekday
- Travel times from the official **ARE national passenger transport model (NPVM 2023) car matrix** (Zenodo, CC-BY 4.0, average weekday), hub zone → municipality zones, reprojected from the 2023 zone state.
- Lines drawn on swisstopo roads (swissTLMRegio), so OpenStreetMap is not required for v1.
- To verify in Phase 3: whether the NPVM car times reflect congested (peak) or daily-average conditions; state it on the sources page.

### D12. Hosts and cantonal sweep: option B
- Federal hosts added to the Atlas environment: `www.bag.admin.ch`, `www.priminfo.admin.ch`, `upload.wikimedia.org`, `www.efv.admin.ch`.
- Checkpoint 1 is closed; Phase 2 (backbone) starts now.
- The cantonal sweep for the `*` metrics (D4–D6) runs alongside or after Phase 2. Its cantonal hosts are requested in one batch before it starts. Results replace the placeholder rows in `data_catalog.csv`.

**Checkpoint 1 closed: 2026-11-09.**

## After Checkpoint 1

### D13. Data plausibility sweep (owner request, 2026-11-09)
A detailed plausibility sweep is scheduled at the end of Phase 3, before Checkpoint 3: municipalities must add up to districts, cantons and Switzerland as published by each source, plus range, time-series, cross-source, spatial and coverage checks. It then runs on every rebuild and in the monthly refresh. Plan: `validation_plan.md`.

## Checkpoint 2 — backbone review (2026-11-09, closed)

Owner instruction: "Use common sense on these. It needs to be transparent, but you have the data, so use the best way to show gaps." The recommended option was taken for each question in `checkpoint2.md`, with transparency rules added.

### D14. Prefer BFS's own re-projection where it exists
Series that BFS already publishes on the current state (STATPOP, federal votes) are taken from BFS. Our engine reprojects everything else. Every value carries a provenance tag: "BFS, current boundaries" or "reprojected by Gemeindebank (population-weighted)" when a weighted split was involved. Our version of BFS-reprojected series stays in the quality report as a cross-check.

### D15. Pre-1991 splits: 1990 population as proxy, labeled
Kept, with the weight method stored per crosswalk row. Values that depend on a proxy-weighted split show a "boundary estimate" marker with the method in the tooltip.

### D16. Current boundaries throughout, with explicit notes
History is shown on current boundaries at every level, including cantons (Moutier counted in JU, Clavaleyres in FR for all years). Canton pages note the difference from the officially published historical canton totals and give the size of the difference.

### D17. Vote pseudo-units
Swiss abroad and postal-vote districts (BFS codes 9xxx) are excluded from the municipality map but included in canton and national results, so these match the official results. The canton/national view states how many votes come from them.

### D18. MS regions dropped from v1
Not valid on the current state; BFS's labour market areas 2018 replace them.

### D19. Web geometry from BFS generalized boundaries (G1)
Kept. swissBOUNDARIES3D is used for area figures only.

### D20. Cantonal hosts allowed in one batch; cantonal sweep runs
Candidate hosts from `cantonal_sources.md` are requested in one batch; the sweep then replaces the `*` placeholder rows with verified sources.

### D21. How gaps are shown (transparency rule for the app)
- A missing value is never blank and never zero. It is shown as a hatched "no data" fill on the map, with the reason in the card: *not published at this level*, *suppressed (small numbers)*, *not covered by this canton* (for `*` metrics), *not applicable*, or *no data for this year*.
- `*` metrics show a coverage indicator (e.g. "14 of 26 cantons") and a coverage map; rankings say "rank among N municipalities with data".
- Regional values attached to municipalities (district survey, labour-market-region rents, district crime) are labeled with their level and drawn without municipal borders inside the region, so they don't look municipal.
- Every value carries its precision tag (exact / survey with confidence interval / modelled / boundary estimate) and its source and year.
- The quality report and the sources page list all known gaps per metric.

**Checkpoint 2 closed: 2026-11-09.** Phase 3 (ingestion and harmonization) starts.

## Phase 3 notes (no owner decision needed)

- **Car reach without OpenStreetMap:** OSM can't be downloaded from the build environment. PT reach uses our own connection-scan routing on the national GTFS; car times come from ARE NPVM 2023 (D11); drawings use swisstopo roads. Validation in `reach_method.md`.
- **Licence gate:** the web build ships only sources whose terms are cleared (`pipeline/licence_review.yaml`); 12 sources wait for verification (Checkpoint 3, question 1).

## Checkpoint 3 — data review (2026-11-10, closed)

Owner: "No emails. Go with your recommendation." Options from `checkpoint3.md`:

- **D22 Licences:** allow the official terms pages (geo.admin.ch, swisstopo, ESTV and the federal offices) for one verification pass; then clear or block each held-back source with evidence in `pipeline/licence_review.yaml`.
- **D23 Initial payload:** the latest values are split into a small core file (headline metrics) plus one file per theme, loaded on first use.
- **D24 Metric curation:** about 60 headline metrics are shown first per theme; all others stay available under "all metrics" and in search. The headline list is proposed in `headline_metrics.md` for owner review.
- **D25 No national data requests:** no emails to BFS/SECO. Crime, pupils and unemployment stay as partial `*` cantonal coverage.
- **D26 Additional cantonal hosts:** allowed (data.zg.ch, stada2.sg.ch, daten.statistik.zh.ch, www.ebericht.be.ch and the others found by the sweep).
- **D27 Phase 4 stack:** TypeScript + Vite + MapLibre GL + Svelte; static hosting on GitHub Pages. The data is built in a working environment and published as a build artifact; a monthly job checks the sources rather than running the full rebuild.
- **D28 Births:** BEVNAT (1969+) is the births, marriages and divorces series. The demographic balance keeps migration and natural change; its births metric is hidden from the picker.

**Checkpoint 3 closed: 2026-11-10.** Phase 4 (web app) starts with the Checkpoint 4 skeleton.

## Phase 4 — Checkpoint 4 (2026-11-10, closed)

Skeleton built in `web/` (TypeScript, Vite, Svelte, MapLibre GL, D27) and published as a private preview: https://claude.ai/artifact/QWE95eJd2pbcCzUieHosCY
- Map of all 2,110 municipalities shaded by any of the headline metrics (quantiles, colour-vision-safe scale, gaps hatched with their reason per D21).
- Population filter (dual slider + typed min/max, live count, non-matching dimmed).
- Reach from Zürich HB, public transport and car: time slider, Play animation (reduced motion jumps to the end), reached municipalities highlighted.
- Quick card on tap: value, year, rank, precision and source tags, travel time.
- First load ≈ 0.95 MB gzipped (JS 300 KB incl. MapLibre, data 630 KB); first render about 1 s in testing.
GitHub Pages deployment follows once the feel is agreed (needs a workflow on the default branch).

Owner feedback round 1 (2026-11-10): "cleaner, more professional, as statisticians or economists would use it; split screen to compare." v2 added the analyst layout (histogram legend, distribution table) and a Compare mode: two synced maps, a scatter with Pearson r, Spearman ρ, population-weighted r and OLS line, and four example pairs.

### D29. White Swiss style, light only (owner, 2026-11-10)
Owner: "Contrast is still an issue. I want a white background Swiss style website." The app drops dark mode (overrides the brief's "light and dark mode" in 6.1): white ground, black type in Inter (a Helvetica stand-in on Google Fonts), black hairline and heavy rules, square corners, no shadows. Selected controls are black with white text. Swiss red (#d52b1e) is the single accent, for the brand mark, the A/B tags, the map selection and the percentile marker. Secondary text is #3d3d3d (11:1 on white) and footnotes #595959 (7:1); nothing in the UI falls below WCAG AA. The data colour scales stay as validated (blue sequential, orange–blue diverging), so red keeps no data meaning.

### D30. Checkpoint 4 closed: design approved (owner, 2026-11-10)
Owner: "I am happy with the design so far." The skeleton's look (D29), the Compare mode and the phone bottom sheet (chevron handle) are the base for the full UI (brief 6.1). Build order: map features first (all hubs, size by, stacked filters, reach filter, levels, year slider, ranking table), then pages (profile, compare places, search with postal codes, sources page, German UI). The preview stays a private artifact until the owner decides on public hosting.

## Phase 4 — persona review round 1 (2026-11-10)

Nine persona reviewers explored the app freely; synthesis in `docs/review_round1.md`.

### D31. Public-transport time shown: station time towards the hub, plus door-to-door (owner, 2026-11-10)
Reviewers did not trust the PT times because they did not match the SBB app. The headline figure becomes the timetable journey time from the municipality's main station **towards** the hub, for morning arrivals at the hub (median over an arrival window). The second line is door-to-door, also towards the hub: from inhabited hectares, walking to the best stop within 1.5 km. The method is stated in one line in the app. The growing-lines animation can stay hub-outward.

### D32. Next build after the defect fixes (owner, 2026-11-10)
Export (CSV of ranking/filtered table, PNG of maps/charts with a source line), a vote picker (all federal votes with titles, national and cantonal results, scale centred on 50 %), small-number flags (unstable rates marked, pooled multi-year rates for births, migration and social assistance), and a French UI. All defects in `docs/review_round1.md` are fixed first, without further owner decisions.

### D33. Hosting: separate public site repository (owner, 2026-11-10)
The Atlas repository stays private. The built site is pushed to a separate public repository created by the owner and served by GitHub Pages. Work is merged into `main` via pull request first (PR #2). The initial commit was rewritten to the owner's GitHub no-reply address at the owner's request; `main` and the work branch were force-pushed.
