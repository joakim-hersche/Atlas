# Gemeindebank — Data catalog (Phase 1)

Status: **reviewed at Checkpoint 1** (2026-11-09). The `recommendation` column now holds the owner's decisions; see `decisions.md` (D1–D12). Theme sections below show the original proposals.
Machine-readable catalog: [`data_catalog.csv`](data_catalog.csv) — 218 datasets (214 found in the sweep + 4 placeholder rows for `*` compilations added at Checkpoint 1), one row per dataset, including rejected ones.

**Totals:** 81 proposed *include*, 92 *maybe*, 41 *exclude*. Verification: 107 rows checked against a live data sample, 99 against live metadata or the source page only, 8 not reachable. The `include` rows alone yield about 420 candidate metrics.

## How to read the CSV

- Columns follow the brief (section 3.3), plus two extra ones: `candidate_metrics` (what the owner would see as metrics) and `verified` (`yes` = structure seen in a live sample, `partial` = source/API reached but no data sample, `no` = not reachable).
- Any field marked `UNVERIFIED:` comes from documentation or memory, not from the live source.
- `access = scrape` marks undocumented internal endpoints of official web apps (ESTV tax calculator, BFS Statatlas). The data is official and openly licensed, but the route can break without notice, so raw responses must be cached.

---

## Key facts (brief 3.1)

| Question | Answer (verified) |
|---|---|
| Municipality key | BFS number (`bfs_nr`). Almost all federal sources use it. Exceptions: Structural Survey district/city tables (names only), PKS city table (names only), BFE power plants (coordinates/EGID), swissNAMES3D (coordinates). |
| Historized register | BFS register, eCH-0071 v1.2.0. TXT/XML download, every state since 12.09.1848 (6,335 records). A REST API returns the municipalities on any date, the mutation list (3,738 mutations since 1960) and an old→new correspondence table. **2,110 municipalities on 2026-01-01.** |
| Geometry per year | BFS historized generalized boundaries G1/K4: every state 1850–2026 (`VALID_FROM`/`VALID_TO`, same history id as the register), 6.5 MB, **including mean/median/min/max elevation per municipality**. swissBOUNDARIES3D full-resolution for 2016–2026. Current swissBOUNDARIES3D matches the register 1:1. |
| PLZ | Official swisstopo locality directory: PLZ → BFS number with the share of addresses in each municipality, monthly. Swiss Post is not needed. |
| Vintages | Three patterns: (a) **re-projected to the latest state** by BFS (STATPOP PxWeb cubes, federal votes since 1960, SDMX flows, social assistance, agriculture); (b) **each year's own state** with history id (ESTV, STATENT/GWS/STATPOP geodata CSVs, census 1850–2020 CSV); (c) **a fixed older state** (census cubes 1970–2000: 2000 state; National Council elections: 2023 state; ARE travel-time model: ~2015/2023 states). The boundary engine has to handle all three. |

**Useful side effect:** several sources come in both forms (BFS re-projected vs. per-year with history id). That gives a ready-made test for our own crosswalk: reprojecting the per-year version should reproduce BFS's re-projected numbers.

## Access routes (what actually works)

| Route | What it serves | Notes |
|---|---|---|
| **BFS SDMX API** (`disseminate.stats.swiss/rest`) | The new home of many BFS statistics: vacancies since 1995, building and dwelling statistics (GWS), land use, vehicles, households, marriages/divorces/births since 1969, cross-border commuters | 246 dataflows, about 22 at municipality level. Uniform CSV, BFS numbers, OPEN-BY. **Probably the richest single source.** |
| **BFS PxWeb API** (`pxweb.bfs.admin.ch`) | STATPOP, migration, STATENT, agriculture, votes since 1960, NR elections since 1971, census 1970–2000 | 633 databases. Rate limit ~1 request/s. Some older cubes now return "Bad Request" (moved to SDMX). |
| **geo.admin STAC** (`data.geo.admin.ch`) | BFS geodata as plain per-municipality CSV/Parquet (STATPOP, GWS, STATENT, education, accessibility), boundaries, BAFU/BFE/ARE/MeteoSwiss layers | 514 collections. Per-year files carry the history id. |
| **BFS DAM API** (`dam-api.bfs.admin.ch`) | All BFS tables/files, with license per asset | `termsOfUse` = OPEN-BY on everything checked. |
| BFS register app API | Register, mutations, typologies for any date | Backbone. |
| ESTV (Excel + tax calculator) | Income tax statistics, tax burden, tax multipliers | Tax calculator export is undocumented (`scrape`). |
| opentransportdata.swiss | GTFS (current and archive 2016–2026), stations, ridership | Must cite source; state the feed version. |
| BFS Statatlas internal JSON | Indicators found nowhere else (e.g. social assistance rate by municipality) | Undocumented (`scrape`); use only as a last resort. |

## Licensing

- **BFS:** every asset checked (including the SDMX flows) carries *OPEN-BY — open use, source must be cited*.
- **swisstopo / other federal geodata:** STAC lists most collections as "proprietary". These are federal open geodata (free use with attribution), but the exact terms link differs by collection. **To confirm per dataset before Phase 3.**
- **CC-BY 4.0:** MeteoSwiss, Energie Reporter, NPVM travel-time matrices (Zenodo). **CC0:** Wikidata.
- **ODbL:** OpenStreetMap. Travel-time results are fine with attribution; redistributing road geometry derived from OSM keeps it ODbL.
- **Coats of arms:** 100 of 100 sampled Commons files are public domain (Swiss municipal arms). Show them as identification only, with source.
- **Flagged:** ESTV tax-calculator export (no explicit license on the app; the ESTV statistics colophon allows reproduction with source), the BFS accessibility grid (OPEN-BY in DAM vs. "on request" on geo.admin), the voteinfo JSON (license page unreachable; the same data on DAM is OPEN-BY).

---

## Themes

Each theme lists what exists, how far back, how reliable, effort, and the proposed v1 scope. Dataset ids refer to the CSV.

### 1. Geography & identity — strong
- **Exists:** register + mutations, typologies (language region, municipality type 9/25, urban/rural, agglomeration, labour market area, mountain area, Grossregion, MS region via older dates), boundaries 1850–2026, elevation, area, PLZ, Wikidata names in all languages plus Wikipedia/website links, coats of arms (public domain), swissNAMES3D peaks/localities.
- **Gaps:** none material. swissNAMES3D needs a spatial join (no BFS number).
- **v1 proposal:** include `bfs_agvch_register`, `bfs_agvch_api`, `bfs_agvch_levels`, `bfs_agvchapp_levels_historic`, `bfs_hist_boundaries_g1`, `bfs_themakart_set`, `swisstopo_swissboundaries3d`, `swisstopo_plz_directory`, `wikidata_municipalities`, `wikimedia_commons_coa`. Maybe: swissNAMES3D (highest peak), Regionalporträts 2021 (cross-check only), Statatlas internal API.

### 2. Population & demography — strong
- **Exists:** STATPOP by age, sex, nationality, marital status per municipality 2010–2025 (re-projected to the current state); births, deaths and migration balance per municipality **since 1981**; births by mother's age since 1969 (SDMX); census population per municipality **1850–2020**; hectare grid 2010–2025.
- **Gaps:** population projections are canton-only (2025–2055).
- **v1 proposal:** include the STATPOP cubes, the balance since 1981, census 1850–2020 (long-run growth), projections as a canton-level metric. Small municipalities: use 5-year sums for births/deaths.

### 3. Migration & nationality — good
- **Exists per municipality 2011–2025:** foreign share and top nationalities, immigration/emigration, inter- and intra-cantonal moves, naturalisations, residence one year earlier.
- **Canton only:** permit types, origin/destination countries, migration background.
- **v1 proposal:** include migration flows, naturalisations, nationality shares. The rest at canton level is "maybe".

### 4. Language & religion — weakest of the demographic themes
- **Full-count municipality data ends with the 2000 census** (language 1860–2000, religion 1850–2000).
- After 2010 only the Structural Survey: districts (3-year pooled, with confidence intervals, names instead of numbers) and ~170 cities (5-year pooled). Religion after 2000: nothing machine-readable below canton or city.
- **v1 proposal:** include census 2000 values and 1970→2000 change at municipality level, clearly labeled "2000". Maybe: a district-level survey layer for recent language shares. **Owner decision needed** (see question list).

### 5. Households & family — good
- **Exists:** household size per municipality 2010–2025; marriages/divorces per municipality **since 1969** (SDMX); marital status 2010–2025; household type (couples, single parents) only in the 1970–2000 census.
- **v1 proposal:** include household size, marriage/divorce rates (5-year averages), census household types labeled "2000".

### 6. Economy & jobs — strong
- **Exists:** STATENT jobs/FTE/workplaces by sector 2011–2024 and by 85 industry divisions; new firms and closures 2013–2023; agriculture (farms, area, livestock, organic share) **since 1975**; cross-border commuters per work municipality since 1996 (quarterly); hotel stays (186 municipalities only).
- **Gaps:** **unemployment by municipality is not available** nationally (SECO's amstat has no export; only 181 cities via SDMX, 2025 only). Wages only for 7 Grossregionen. STATENT replaces values below 4 by 4 (small municipalities).
- **v1 proposal:** include STATENT (sector + selected divisions), UDEMO, agriculture, cross-border commuters (maybe). Unemployment: cities only, or leave out.

### 7. Income & tax — strong (the strongest new find)
- **Exists:** direct federal tax statistics per municipality **every year 1983–2023** (taxpayers, net and taxable income, income classes); corporate version 1999–2023; **tax burden for any household type and income, every municipality, 2010–2026**; municipal tax multipliers 2010–2026.
- **Caveats:** the burden and multiplier exports are undocumented (`scrape`). Multipliers are only comparable within a canton. Pre-2009 burden is PDF only.
- **v1 proposal:** include all three ESTV sources. **Owner decision needed:** which household types and incomes to show as standard tax-burden metrics.

### 8. Public finances — gap
- **No national municipality-level finance data found.** Only ~180 cities (SDMX, 2023). EFV aggregates municipalities per canton (host blocked, unverified). Full coverage would need 26 cantonal sources.
- **v1 proposal:** leave out of v1, or include cities only, labeled partial.

### 9. Housing & buildings — strong
- **Exists:** vacancy rate per municipality **1995–2026** (SDMX); building and dwelling statistics 2010–2025 (type, age, rooms, floor area, heating energy source since 2021); public GWR extract per building (for medians such as construction year); new dwellings 1995–2024; construction investment 1994–2024; second-home share 2017–2026 (ARE); census housing 1970–2000.
- **Gaps:** no current owner-occupancy or rent per municipality.
- **v1 proposal:** include vacancy, GWS, new dwellings, construction investment, second homes; GWR extract for selected derived metrics (effort L, 949 MB).

### 10. Real estate prices — gap
- **No open federal property prices per municipality.** The BFS price index has only 5 municipality types. Rents: canton and labour-market region (Structural Survey), cities; per municipality only census rent classes 1970–2000. Canton Zurich publishes land prices per municipality (host blocked, unverified); GE/VD/BS not checked.
- **v1 proposal:** maybe: rent per m² by labour-market region attached to each municipality (labeled as regional), the price index type label. **Owner decision needed** on whether to pursue cantonal sources (partial coverage).

### 11. Land use & built environment — strong
- **Exists:** land use statistics per municipality for 5 survey periods (1979/85 → 2020/25, latest period still in progress), via SDMX or the hectare grid; building zones per municipality 2012/2017/2022 (ARE), incl. unbuilt reserves; settlement area 1919–2025 (ARE).
- **v1 proposal:** include land use (settlement, agriculture, forest, unproductive shares and change since 1985), building zones, sealed area.

### 12. Mobility & accessibility — strong, and covers the reach feature
- **Reach inputs:** GTFS 2026 (290 MB, no line shapes) and archive 2016–2026; federal rail network geometry keyed by station number (to draw lines along real track); station list with BFS number; ARE NPVM 2023 car and PT travel-time matrices (Zenodo, CC-BY, ~500 MB each) as the official sanity check; also an ETH 100 m multi-modal accessibility dataset (Zenodo, CC-BY, 6.9 GB) worth considering.
- **Metrics:** car ownership and electric-car share per municipality 2010–2025; commuter matrix municipality→municipality (2014/2018/2020); station ridership (1,177 stations); PT quality classes 2012–2026; distance to supermarket, pharmacy, doctor, school, PT stop (hectare grid, 2011–2021); road accidents 2011–2025.
- **Blocker:** **OpenStreetMap (Geofabrik) does not download in this environment** (the proxy tunnel drops). Needed for car reach. Fallbacks: NPVM car matrices (zone level, official) or swissTLMRegio roads.
- **v1 proposal:** include all of the above except the microcensus (region types only).

### 13. Energy & climate — good
- **Exists:** Energie Reporter per municipality (CC-BY, monthly since 2021: e-car share, solar used vs potential, renewable heating, electricity use); rooftop solar potential per municipality; all 339k electricity production plants (join via building id/coordinates); Energiestadt labels; EV charging points; climate normals 1961–1990 and 1991–2020 on a 1 km grid (MeteoSwiss, CC-BY).
- **Caveat:** climate needs zonal statistics, weighted to settled area for mountain municipalities.
- **v1 proposal:** include Energie Reporter, solar potential, PV capacity, Energiestadt, climate normals (temperature, precipitation, sunshine).

### 14. Environment & hazards — medium, mostly raster work
- **Exists:** NO2 (1990–2025), PM10, PM2.5 annual grids; road and rail noise 2021 (large 10 m rasters); radon probability grid; protected areas; earthquake zones; national hazard overview layers (surface runoff, SilvaProtect).
- **Gaps:** detailed hazard maps are cantonal (not on geo.admin); no light-pollution dataset.
- **v1 proposal:** include air quality (population-weighted), protected-area share. Maybe: noise (effort L), radon, earthquake zone, hazard overviews.

### 15. Health & social — mixed
- **Exists per municipality:** social assistance rate 2007–2025 (Statatlas internal API — needs a value-order check), health-sector jobs (STATENT), distance to pharmacy/doctor/dentist (hectare grid, see Mobility).
- **Canton only:** doctors, hospitals, nursing homes, supplementary benefits.
- **Not verified (hosts blocked):** health insurance premiums and the premium-region → municipality mapping (BAG, priminfo).
- **v1 proposal:** include social assistance rate, health-sector jobs, distance to services; premiums once the hosts are allowed.

### 16. Education — medium
- **Exists:** educational attainment of 25–64-year-olds per municipality 1990, 2000, 2017–2023 (modelled); upper-secondary and Matura completion by municipality (one pooled edition, cohorts 2010–2014); Matura rate by district.
- **Canton only:** pupils, teachers, schools.
- **v1 proposal:** include attainment and completion rates; university/college presence as a "maybe".

### 17. Safety — gap at municipality level
- Police crime statistics: canton (2009–2025), district via Statatlas, ~27 cities over 30,000 inhabitants.
- **v1 proposal:** district-level crime rates as a district metric shown on municipality profiles (clearly labeled), plus the city table. Road accidents are under Mobility.

### 18. Politics — very strong
- **Exists:** every federal vote **since 1960 per municipality, already on current boundaries** (511 votes); vote titles in all languages via voteinfo; National Council party strengths and turnout **1971–2023** per municipality (2023 state); ticket-splitting statistics 2019/2023.
- **Gaps:** cantonal elections only at canton level.
- **v1 proposal:** include votes and NR elections. Derived metrics (left/right bloc, "progressive index" from curated votes) need a short method note.

---

## Hard cases

1. **Undocumented endpoints** (ESTV tax calculator, Statatlas): official data, but cache everything and add a contract test.
2. **Survey data** (Structural Survey): district/city only, pooled years, confidence intervals, names instead of numbers.
3. **Small numbers and suppression:** STATENT (<4 → 4), UDEMO `X`, ESTV `-`, hotel stays `x`, social assistance −9999. Show "suppressed", never zero.
4. **Raster-only layers** (air, noise, radon, climate, hazards): zonal statistics with population or settlement weights. Noise rasters are 165–553 MB.
5. **Breaks in series:** census (to 2000) vs. STATPOP (from 2010); GWS heating from 2021; party mergers (CVP+BDP → Mitte).
6. **OSM blocked** in this environment.

## Hosts still blocked (would add value)

| Host | For |
|---|---|
| `opendata.swiss` | Server refuses this machine (HTTP 403). Blocks the brief's systematic CKAN sweep and some license checks. **Cannot be fixed by allowlisting.** |
| `download.geofabrik.de` | Allowlisted, but the proxy tunnel drops every connection. Needed for car reach. |
| `www.bag.admin.ch`, `www.priminfo.admin.ch` | Health insurance premiums and premium regions |
| `upload.wikimedia.org` | Coat-of-arms image files |
| `www.efv.admin.ch` | Public finances (probably canton-aggregated) |
| Cantonal: `www.zh.ch`, `www.web.statistik.zh.ch`, `statistique.ge.ch`, `www.vd.ch`, `www.statistik.bs.ch`, `data.bs.ch` | Property prices and other partial-coverage metrics |

## Proposed v1 scope (summary)

- **National, municipality-level, verified:** ~80 datasets, ~400 candidate metrics across 16 themes. That's breadth well beyond the Regionalporträts' 41 indicators.
- **Labeled partial or regional:** language/religion (2000 census + district survey), crime (district), rents (labour-market region), unemployment and finances (cities only), canton-only health metrics.
- **Out of v1 unless the owner wants them:** cantonal property prices, cantonal hazard maps, municipal finances beyond cities, light pollution.

## Owner decisions needed at Checkpoint 1

1. Include / maybe / exclude per theme (walk-through).
2. Language & religion: show 2000 census values at municipality level, district survey values, or both?
3. Tax burden: which standard household types and incomes (e.g. single CHF 80k, married with 2 children CHF 150k, pensioner)?
4. Partial-coverage metrics (cities only, ZH only): show with a "partial" label, or leave out?
5. Default reference vintage (proposal: current boundaries, history reprojected).
6. Hub list and reach parameters (departure window, rail only vs. all PT, car free-flow vs. typical).
7. Hosts: allow BAG/priminfo and upload.wikimedia.org? Pursue cantonal hosts?
8. Car reach fallback while OSM is blocked: NPVM car matrices, swissTLMRegio roads, or try OSM from another environment?

## Addendum 2026-11-10: backlog item "More data"

Built: `estv_median_income` (modelled median taxable income from the ESTV classes, 2020–2023), `bafu_noise` (sonBASE 2021 exposure of residents, modelled), `bfs_gwr` (school and university buildings, GWR class 1263), `bfs_se_language_cities` (SE main languages, 5-year pools, statistical cities, partial coverage). Rejected and recorded in the CSV: childcare places (no open source beyond one canton's PDF and Stadt Zürich quartiers), Structural Survey languages for MS regions or all municipalities (not published), cantonal school-site lists (four cantons or cities, licences unverifiable).
