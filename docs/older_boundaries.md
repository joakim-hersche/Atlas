# Older boundaries — scope note

Backlog item (geographer): *view data on older boundaries (e.g. 2000) as well as harmonised.*
Everything in ATLAS is shown on the latest municipality state (D8, 2026-01-01, 2,110 municipalities).
This note says which older states can be offered, with which data, and how; the first version
described at the end is built by `pipeline/build/vintages.py`.

## 1. Geometry: which vintages are feasible

| Source | States | Licence | Use |
|---|---|---|---|
| BFS generalised historized boundaries G1 (`bfs_hist_boundaries`, already cached and used for the current map, D19) | every municipality state 1850–today; each polygon carries `GDEHISTID` = register histId and `VALID_FROM`/`VALID_TO` | OPEN-BY (BFS termsOfUse, DAM 36390147): free use with source | **yes** |
| BFS K4 (same collection) | same states, coarser | OPEN-BY | not needed (G1 at 40 % is already small) |
| swissBOUNDARIES3D | current and recent releases only | swisstopo OGD | no (area figures only, D19) |

So **any** state can be drawn, keyed by histId, i.e. exactly the versions the backbone crosswalk
uses. Polygons valid on the chosen dates (Swiss municipalities, `GARTE` 11; lakes `GARTE` 13):

| Vintage | Date | Municipalities | Why this date |
|---|---|---|---|
| 2000 | 2000-12-31 | 2,896 | the state BFS uses for all four censuses 1970–2000 (inferred from the cube's BFS numbers, Jaccard 1.0) |
| 2010 | 2010-12-31 | 2,584 | the state of the STATPOP 2010 municipality file (`GDEHISTID` matches one-to-one) |
| *2026 (reference)* | 2026-01-01 | 2,110 | harmonised view, unchanged |

Canton outlines of an older state are not a separate file: the browser derives them from the
municipality topology (TopoJSON mesh between municipalities of different cantons), so they are always
consistent with the municipalities (e.g. Vellerat in JU since 1996, Clavaleyres still in BE in
2000/2010, Moutier in BE).

## 2. Which metrics can be shown on an older vintage

A value may be shown on an older state only if it is **published on that state** or on an **even
older** state (then carried forward with the crosswalk). Nothing is projected *backwards* from a
newer state: a merged municipality cannot be split into its former parts without modelling.

| Route | Rule | Precision tag | First version |
|---|---|---|---|
| **Native** — the source publishes on that state | values as published | as published (`exact`) | census 1970/1980/1990/2000 on the 2000 state; STATPOP 2010 on 31.12.2010 |
| **Forward** — source on an older state, reprojected with `to_vintage(df, source, target)` | counts: mergers summed (weight 1), splits and transfers split by the population weights of the backbone; shares recomputed from the reprojected counts | `exact` where all weights are 1, else `boundary_estimate` | census 1970–2000 on the 2010 state |
| **Backward** — source on a newer state, split back to older units | would need disaggregation weights, e.g. the share of a merged municipality's residents living in each former part, from the STATPOP hectare grid placed in the old polygons | `modelled` | **not done** (see 5) |

Consequences for the current catalog:
- Most series (STATPOP, BEVNAT, STATENT, GWS, votes, Arealstatistik, …) are published by BFS on a
  recent state only (D14). They have **no** values on the 2000 or 2010 boundaries in this version
  and are labelled as such in the app, with a link back to the harmonised map.
- Census 1970–2000 (language, religion, households: 47 metrics, 30 counts and 17 shares) is native
  on 2000 and carried forward to 2010.
- STATPOP 2010 municipality file: residents, Swiss, foreigners, men, women and the two shares.
  Checked against the PxWeb STATPOP series that ATLAS ships: identical for every municipality whose
  version is unchanged to 2026 and for the national totals (7,870,134 residents). The file's
  age classes and its separate foreigners column are *not* used: they differ from the published
  series by a few persons (foreigners column in 0.6 % of municipalities, age classes in 4–45 %).
- Areas, densities, elevation, reach and other geometry-based metrics are computed on the reference
  polygons only; not offered on older states.
- Ratios use the same `ratio:` definitions as the harmonised catalog, computed from the counts on
  the older state (never averaged).

## 3. Payload (mobile)

Loaded only when an older vintage is opened; nothing is added to the first load of the app.

| File | Content | 2000 (gzip) | 2010 (gzip) |
|---|---|---|---|
| `geo/vintage_<id>.topojson` | municipalities + lakes of that state, 40 % of vertices kept as on the current map | 315 KB | 293 KB |
| `web/vintage/<id>/units.json` | names, canton, district, label point, successors on the 2026 state | 76 KB | 69 KB |
| `web/vintage/<id>/core.json` | headline shares, all periods | 95 KB | 96 KB |
| `web/vintage/<id>/<theme>.json` | the other metrics of one theme file, all periods (on first use) | 300–336 KB | 16–310 KB |
| `web/vintages.json` | index (vintages, metrics, periods, provenance, sources) | 2 KB | |

Opening a vintage with a headline metric costs about 0.5 MB (geometry, units, core); the current
first load (≈ 1 MB) is unchanged. Count metrics of all four census years are the largest part; if
needed they can be split per period later.

## 4. UI

- A **Boundaries** switch (2026 harmonised · 2010 · 2000) on the map, next to the level switch.
  It is view state like everything else: `#v=vintage&vin=2000&m=vz_lang_fr_share&y=1970&sel=6621`.
- Choosing an older vintage opens the municipality map of that state. The shade metric is kept when
  it exists there; otherwise the map says so in one line (“not available on the 2000 boundaries:
  published on a later municipality state only”), offers the harmonised map, and the picker lists
  only the metrics that exist on that state, with their periods (year slider over the census years).
- Every value carries its provenance: “BFS, 2000 boundaries” or “carried forward to the 2010
  boundaries by ATLAS (boundary estimate where municipalities were split)”.
- The card of an old municipality names the municipality or municipalities it is part of today
  (with the weight where it was split) and links to their profiles. Going back to 2026 keeps the
  metric and selects the main successor.
- Districts and cantons of the older state, filters, reach and ranking stay on the harmonised map in
  this version.

## 5. Not in this version (possible next steps)

1. **Backward projection** of current-state series to older units with hectare weights
   (`modelled`), e.g. STATPOP 2011–2025 on 2010 boundaries. The weights exist (STATPOP hectares
   1990, 2000, 2010–2025), but the value is a model, not a publication; owner decision needed.
2. More native sources per tax or release year: ESTV direct federal tax 2003–2019 (each year on
   its own state), ARE second homes, building statistics 1995–2012, federal votes on the state of
   the vote date (only a sample of votes is cached).
3. Districts and cantons of the older state (aggregate the same rules up the old hierarchy).
4. A swipe or side-by-side comparison of an old and the harmonised map.
