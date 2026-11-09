# Gemeindebank — Project Brief for Claude Code

> A personal web app to explore and compare every Swiss municipality (Gemeinde), district, canton and region on one map, with as much open data as can be found, on consistent boundaries over time. It should answer "what is this place like and how does it compare?" without having to search the web.

This file is the standing brief for the project. Read it at the start of every session. The **Working agreement** section is binding.

> Repository note: the GitHub repository is `joakim-hersche/atlas`; the project name is Gemeindebank. Phase status and owner decisions live in `docs/decisions.md`.

---

## 1. Working agreement (read first)

1. **The project runs in phases with hard stops.** At each `🛑 CHECKPOINT` stop, present the results to the owner and wait for decisions. Do not continue into the next phase without explicit approval.
2. **Phase 1 (data discovery) comes first.** Do not write app code, choose a frontend framework or build pipelines before the data catalog has been reviewed with the owner.
3. **Never invent data.** No placeholder figures in the shipped site. Every value must trace back to a downloaded source file. If a source cannot be reached, say so and record it in the catalog; do not substitute numbers from memory.
4. **Verify, don't recall.** Source names, URLs, formats, licenses and time coverage listed in this brief are leads from memory. Confirm each one against the live source before relying on it.
5. **Track licensing and attribution** for every dataset from the start. Anything with unclear or restrictive terms is flagged, not used.
6. **Reproducible pipeline.** Raw downloads are cached and never edited by hand. Every derived file can be regenerated from raw with one command.
7. **Owner context:** intermediate data/SQL skills, uses the site on an iPhone and on desktop, works from Claude Code on mobile at times. Keep explanations short and decisions explicit. Ask with a small number of clear options when a choice is genuinely the owner's.
8. Use a task list for each phase and commit at the end of each completed step with a clear message.

---

## 2. Product vision

### Core idea
Every geographic unit in Switzerland is a row, and every fact about it is a column, **on consistent boundaries across years**. The app lets you:

- **Encode** any metric on the map: shade (choropleth or symbol color) and circle size, each driven by a different metric.
- **Filter** by stacking any number of conditions (min/max ranges per metric, categorical filters such as language region or municipality type), combined with AND.
- **Reach:** choose a hub (major station or city) and a mode (train or car), drag a time slider, and watch the reachable network grow outward along real lines. Reach can also be used as a filter ("within 30 min of Bern by train").
- **Profile:** open any municipality, district, canton or region and get a full fact sheet with all available metrics, rank within Switzerland and within its canton, time series, boundary history, and links to official sources.
- **Compare:** put 2–4 places side by side.
- **Move through time:** a year slider for metrics with time series, always on harmonized boundaries.
- **Switch level:** Gemeinde ↔ Bezirk ↔ Kanton ↔ other official spatial levels (see 4.3), with values aggregated correctly.

### What a session looks like
"Show tax burden as shade and population as size, keep municipalities with falling tax since 2015, vacancy above 1%, and within 40 min of Zürich HB by train. Rank them. Open the third one."

### Prototype reference
A clickable draft with invented data exists as a design reference (shade by metric, size by metric, stacked range filters, hub plus train/car reach lines that grow with a time slider, municipality detail with rank and source tags). Treat it as UX direction only, not as code to reuse.

### Non-goals (for v1)
- No user accounts, no backend server, no sync.
- No paid data sources unless the owner explicitly approves one.
- No natural-language query layer in v1 (possible later).

---

## 3. Phase 1 — Data discovery (do this first)

### Goal
Find out **everything that is realistically available** at Gemeinde level (and at higher levels where Gemeinde level doesn't exist), and produce a reviewed catalog. Breadth matters: the owner wants as much data as possible.

### Method
1. **Systematically sweep the publishers** listed in 3.2. For each, list the datasets that have a geographic breakdown at Gemeinde, Bezirk, Kanton or another official spatial level.
2. For each candidate dataset, **open the actual source**, check the access method, and if possible download a small sample to confirm the structure (column names, geographic key, years present).
3. Record everything in the catalog (3.3), including datasets you rejected and why.
4. Group the catalog into **themes** (3.4) for the review.
5. Estimate effort per dataset (S/M/L) and flag the hard ones (no BFS number, only PDFs, only cantonal coverage, survey-based, license issues).

### 3.1 Key facts to establish early
- The **municipality key**: BFS number (Gemeindenummer) and how each source references municipalities (BFS number, name, postal code, coordinates).
- The **historized municipality register** (all mergers, splits, renames, canton changes since 1960, with mutation dates). This is the backbone of the project; confirm its format and access route first.
- **Boundary geometries** per year (or at least current plus the ability to map old municipalities to current ones).
- **Which data comes with which boundary vintage.**

### 3.2 Publishers and leads to sweep (verify each)

Federal statistics and registers
- **BFS (Federal Statistical Office):** historized municipality register; STAT-TAB / PxWeb cubes; municipality portraits (Regionalporträts / Gemeindeporträts, a compiled indicator set that's a good starting point); STATPOP (population structure), BEVNAT (births, deaths), migration; STATENT (businesses and jobs by sector); building and dwelling statistics (GWS), the vacancy count (Leerwohnungszählung); Structural Survey (language, religion, education, commuting, household; note survey precision and pooling); land use statistics (Arealstatistik); social assistance rate; spatial typologies (municipality types, urban/rural, agglomerations, labor market regions, MS regions, language regions); federal votes and National Council elections by municipality; turnout.
- **opendata.swiss** (CKAN API): search systematically for datasets tagged at municipality level, across all federal and cantonal publishers.
- **Federal Register of Buildings and Dwellings (GWR):** building age, heating type, energy source, dwelling sizes; check public access and aggregation options.

Tax and income
- **ESTV / AFC (Federal Tax Administration):** tax burden by municipality for standard household types; direct federal tax statistics (taxable income distribution by municipality); municipal tax multipliers.

Space, mobility and environment
- **swisstopo / geo.admin.ch:** swissBOUNDARIES3D (municipality, district and canton boundaries), swissNAMES3D, elevation model (municipality mean or median elevation), geo.admin API layers.
- **ARE (Federal Office for Spatial Development):** accessibility indicators, travel-time data from the national passenger transport model, building zone statistics, mobility microcensus outputs.
- **opentransportdata.swiss:** national GTFS timetable (for train and public transport reach), station list with usage counts if available.
- **OpenStreetMap** (Geofabrik Switzerland extract): road network for car reach; POIs (supermarkets, schools, doctors, pharmacies) as a fallback for amenity counts.
- **MeteoSwiss open data:** climate normals (temperature, sunshine, precipitation, fog days if available) that can be aggregated to municipalities from grids or stations.
- **BAFU / FOEN:** road and rail noise exposure, natural hazards, air quality.
- **BFE / SFOE:** rooftop solar potential (sonnendach), heating systems, EV chargers, renewable installations.

Society and services
- **Police crime statistics (PKS):** municipality coverage limits apply (mostly larger municipalities).
- **SECO / amstat:** unemployment by municipality, if published at that level.
- **BAG / FOPH:** hospitals, health insurance premium regions (premiums by region and canton).
- **Education:** schools and universities; cantonal sources may be needed.
- **Swiss Post:** postal code ↔ municipality mapping (needed for joining many sources).

Cantonal and other
- **Cantonal statistical offices** (e.g. Zürich, Bern, Vaud, Geneva, Basel-Stadt): often richer municipal data such as property transaction prices, local finances, school data. Note per-canton coverage; partial-coverage metrics must be labeled as such.
- **Wikidata:** names in all languages, Wikipedia links, coat of arms (check image licenses), founding/merger events (as a cross-check only).
- **Real-estate prices:** check what is genuinely open (cantonal transaction statistics, any federal price index by region). Commercial providers are out of scope unless approved.

Also search beyond this list. If you find a good municipality-level source that is not here, add it.

### 3.3 Catalog format
Write two files:

- `docs/data_catalog.csv`, one row per dataset, with columns:
  `id, theme, dataset, publisher, url, access (api|download|pdf|scrape), format, geo_level (gemeinde|bezirk|kanton|other), geo_key (bfs_nr|name|plz|coords|grid), boundary_vintage, years_available, frequency, latest_year, precision (exact|survey|modelled), coverage (national|partial:<cantons>), license, attribution_text, size_estimate, effort (S|M|L), recommendation (include|maybe|exclude), notes`
- `docs/data_catalog.md`: a readable summary by theme: what exists, highlights, gaps, the hard cases, and proposed v1 scope.

Also list the **candidate metrics** each dataset would yield (e.g. "median taxable income, share of taxpayers above CHF 100k"), since the owner thinks in metrics, not datasets.

### 3.4 Themes for the review
Population & demography · Migration & nationality · Language & religion · Households & family · Economy & jobs · Income & tax · Public finances · Housing & buildings · Real estate prices · Land use & built environment · Mobility & accessibility · Energy & climate · Environment & hazards · Health & social · Education · Safety · Politics (votes, elections) · Geography & identity (elevation, area, typologies, names, coat of arms).

### 🛑 CHECKPOINT 1 — Data review with the owner
Go through the catalog **with the owner, one theme at a time**:
1. For each theme give a short summary: what exists, at what level, how far back, how reliable, and the effort.
2. Propose include / maybe / exclude for each dataset.
3. Ask the owner to decide, using a small number of clear options.
4. Record the decisions in `docs/data_catalog.csv` (`recommendation` column) and a short `docs/decisions.md`.

Also agree on:
- **v1 metric list**, aiming for breadth; partial-coverage and survey metrics are fine if labeled.
- **Default reference vintage** (proposal: current boundaries, reprojecting history onto them).
- **Hub list for reach** (proposal: Zürich HB, Bern, Basel SBB, Genève, Lausanne, Luzern, St. Gallen, Winterthur, Lugano, Bellinzona, Chur, Biel/Bienne, Fribourg, Sion, Zug, Aarau, Olten, Schaffhausen, Neuchâtel, Thun).
- **Reach parameters:** departure time (e.g. weekday 08:00), whether train means rail only or all public transport, and the car assumptions (free-flow vs. typical).

Only continue after the owner approves the scope.

---

## 4. Phase 2 — Backbone: geography and boundary history

### 4.1 Municipality history engine
- Import the historized municipality register into tables:
  - `municipality_version(bfs_nr, name, canton, district, valid_from, valid_to, mutation_id)`
  - `mutation(mutation_id, date, type (merger|split|rename|transfer|...), from_bfs[], to_bfs[])`
- Build a **crosswalk** from any (bfs_nr, date) to the current municipality, with weights:
  - Mergers: weight 1, values combined.
  - Splits and partial transfers: population weights (or area weights where population is unavailable), with the weight source recorded.
- Expose a function `to_vintage(df, source_vintage, target_vintage, rule)` that reprojects a dataset.

### 4.2 Aggregation rules (indicator catalog)
Every metric gets metadata: `id, label_de, label_en, unit, decimals, direction (higher_better|lower_better|neutral), aggregation (sum|weighted_mean:<weight>|ratio:<num>/<den>|not_aggregatable), precision, source_id, license, coverage, years`.
- Counts are summed.
- Rates and shares are recomputed from summed numerators and denominators wherever possible, otherwise weighted means are used.
- Medians and indices that can't be re-aggregated are flagged and shown only at their native level.

### 4.3 Spatial levels
At minimum: Gemeinde, Bezirk, Kanton. Then the official BFS levels: Grossregion, language region, agglomeration, MS region, labor market region, urban/rural typology. Aggregate up using the same rules.

### 4.4 Geometry
- Current boundaries from swissBOUNDARIES3D, simplified at several zoom levels and converted to TopoJSON or vector tiles (PMTiles), small enough for mobile.
- Centroids or label points per unit (for symbols and labels).

### Validation (must pass)
- Reprojected municipality totals equal published canton and national totals within a small tolerance (population, votes, jobs).
- Every current municipality has geometry, and every row in every dataset maps to a municipality or is logged.

### 🛑 CHECKPOINT 2
Show the merger history coverage, the crosswalk test results and any unmapped records. Agree on the handling of edge cases.

---

## 5. Phase 3 — Ingestion and harmonization

- One connector per source under `pipeline/sources/<source_id>/` with: `fetch` (download to `data/raw/<source_id>/<date>/`), `parse` (to tidy Parquet), `metadata` (license, attribution, vintage).
- Harmonized long table in DuckDB/Parquet: `observation(unit_id, level, vintage, metric_id, period, value, source_id, precision)`.
- Build the outputs the web app needs (see 6.3).
- Data quality report per run: row counts, missing municipalities per metric, outliers (e.g. > 5 SD year-on-year jumps), totals checks. Write it to `docs/quality_report.md`.
- A single command rebuilds everything: `make data` (or `just data`).

### 5.1 Reach (travel time) data
Goal: for each hub and mode, a network that can be drawn growing outward with time.

- **Train / public transport:** compute from the GTFS timetable for the agreed departure window (e.g. the median travel time over 07:30–08:30 on a typical weekday). Candidate tools: `r5py` or OpenTripPlanner. Result: travel time from each hub to each municipality (to its main station or population-weighted centroid).
- **Car:** compute on the OSM road network (candidate tools: OSRM or `r5py` car mode). Result: hub → municipality travel times.
- **Growing lines:** export the shortest-path tree per hub and mode as line segments with `t_start` and `t_end` (cumulative minutes at each end), using real rail lines (GTFS shapes or the swisstopo rail network) and real roads. The frontend draws each segment up to the slider time and interpolates partial segments.
- Compare against official travel-time data from ARE if available, as a sanity check.
- Keep file sizes mobile-friendly (simplify geometry, round coordinates, one file per hub and mode, loaded on demand).

### 🛑 CHECKPOINT 3
Present the quality report, the metric count per theme and level, and sample reach outputs for two hubs. Agree on any gaps before building the frontend.

---

## 6. Phase 4 — Web app

### 6.1 Requirements
Mobile-first, equally good on desktop. Light and dark mode. Fast on a phone over mobile data. Everything works without a server.

**Map**
- Choropleth (polygons) and proportional symbols, switchable. At Gemeinde level choropleth is the default and symbols are optional.
- "Shade by" and "Size by" selectors over all metrics, grouped by theme, with search.
- A sequential color scale (diverging for metrics with a meaningful midpoint, e.g. change over time); direction-aware legend ("darker = better" when the metric has a direction).
- Classification: quantiles by default, plus continuous and equal-interval options.
- Tap or hover a unit for a quick card; tap again to open the profile.

**Filters**
- Add any number of conditions: numeric min/max (dual slider plus typed input), categorical (canton, language region, municipality type, agglomeration).
- Live count of matches; non-matching units dimmed, not hidden.
- Optional reach filter ("within N min of <hub> by <mode>").

**Reach**
- Hub picker, train/car toggle, time slider, a Play button that animates the growth.
- Lines grow along the real network; reached units are highlighted, and the travel time shows in the quick card.

**Ranking table**
- Sortable list of matching units with the selected metrics as columns. Tapping a row selects it on the map.

**Profile page** (the "don't need Google" page)
- Header: name (all official languages), canton, district, type, population, area, elevation, coat of arms where licensed, links (official website, Wikipedia, BFS portrait).
- All metrics grouped by theme, each with value, unit, year, rank in Switzerland and in the canton, a percentile bar, a source tag, and a precision tag (exact / survey / modelled / partial coverage).
- Time-series sparklines where history exists.
- Boundary history (mergers, predecessors) with dates.
- Neighbors and "similar places" (nearest by a standardized vector of selected metrics).
- Reach summary: travel time to each hub by train and car.

**Compare**
- 2–4 units side by side with the same layout as the profile; differences highlighted.

**Time**
- Year slider for metrics with series; harmonized boundaries throughout; labeled when a metric has no value for the chosen year.

**Levels**
- Gemeinde / Bezirk / Kanton / other levels from 4.3, with values aggregated by the catalog rules; non-aggregatable metrics are disabled at higher levels with an explanation.

**State and sharing**
- All view state (level, metrics, filters, hub, year, selection) encoded in the URL so any view can be bookmarked or shared.

**Search**
- Find any municipality, district, canton or postal code instantly (accent- and language-insensitive: "Geneve", "Genf" and "Genève" all work).

**Sources page**
- Every dataset with publisher, license, attribution, vintage and last update.

### 6.2 Language
UI in English by default with German as an option; place names in their official form.

### 6.3 Data delivery to the browser (proposal, confirm at Checkpoint 3)
- `units.json`: id, level, names, canton, type, centroid (small).
- Geometry: TopoJSON per level or PMTiles.
- Metric values: one compact columnar file per level for the latest year (all metrics), loaded at start; time series per metric loaded on demand.
- Reach: one file per hub and mode, loaded on demand.
- Option to consider: DuckDB-WASM for in-browser querying if filtering on plain arrays turns out to be too limited. Start simple.

### 6.4 Tech proposal (confirm before building)
- Pipeline: Python (managed with `uv`), DuckDB, Parquet, GeoPandas/Shapely, `r5py` or OTP, OSRM.
- Frontend: TypeScript + Vite, MapLibre GL for the map, a small state layer, no heavy framework unless it clearly helps (Svelte is a reasonable choice if one is wanted).
- Hosting: static site on GitHub Pages or Cloudflare Pages, deployed by GitHub Actions.
- Data refresh: a scheduled GitHub Action (monthly) that re-runs fetch and build and opens a PR with the quality report.

### 🛑 CHECKPOINT 4
Before writing the full UI, show a clickable skeleton (map + one metric + one filter + one hub's reach) deployed to a preview URL that works on the owner's phone. Iterate on feel before building the rest.

---

## 7. Phase 5 — Polish and ship

- Performance budget: first view interactive in under 3 s on a mid-range phone on 4G; initial payload under ~3 MB gzipped.
- Accessibility: keyboard navigation, focus states, color scales that work for color-vision deficiency, reduced-motion support (Play jumps straight to the end).
- Installable as a PWA (home-screen icon, offline cache of the last-used data).
- README with how to rebuild data, add a source, and deploy.

---

## 8. Repository layout (proposal)

```
gemeindebank/
  CLAUDE.md                  # this brief
  docs/
    data_catalog.csv
    data_catalog.md
    decisions.md
    quality_report.md
  pipeline/
    sources/<source_id>/     # fetch.py, parse.py, meta.yaml
    backbone/                # municipality history, crosswalk, levels
    reach/                   # GTFS + road routing, segment export
    build/                   # outputs for the web app
    tests/
  data/
    raw/                     # cached downloads (gitignored, or LFS if small)
    interim/
    out/                     # files shipped to the site
  web/
    src/
    public/
  Makefile (or justfile)
  .github/workflows/
```

---

## 9. Definition of done for v1

- Every current municipality has a profile page with all agreed metrics, sources and boundary history.
- Shade, size, stacked filters, levels, the year slider, reach (all agreed hubs, train and car) and compare all work on iPhone Safari and desktop browsers.
- Every number on the site traces back to a cached source file, and the sources page lists licenses and attribution.
- `make data && make web` rebuilds everything from scratch.
- The quality report passes the totals checks.

---

## 10. First session: what to do now

1. Read this file.
2. Create the repo skeleton and a task list for Phase 1.
3. Start the data discovery sweep (Section 3). Begin with the backbone sources (historized municipality register, boundaries, BFS portraits), then go theme by theme.
4. Write `docs/data_catalog.csv` and `docs/data_catalog.md`.
5. Stop at **Checkpoint 1** and walk the owner through the catalog, one theme at a time.
