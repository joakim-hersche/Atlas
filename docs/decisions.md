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

### Pending
Public finances · Real estate prices · Energy & climate · Environment & hazards · Health & social · Education · Safety · reference vintage · hubs and reach parameters · blocked hosts.
