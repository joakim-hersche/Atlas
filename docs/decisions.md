# Decisions log

Owner decisions, newest last. The `recommendation` column in `data_catalog.csv` reflects these decisions.

## Checkpoint 1 — data review (2026-11-09, in progress)

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

### Pending
Energy & climate · Environment & hazards (non-* items) · Health & social · Education (non-* items) · reference vintage · hubs and reach parameters · blocked hosts.
