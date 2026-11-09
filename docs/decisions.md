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
