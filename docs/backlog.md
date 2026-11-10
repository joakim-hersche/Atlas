# Backlog

Feature requests from persona review round 1 (`docs/review_round1.md`) that are not in the current build (D32: defects, export, vote picker, small-number flags, French UI). Owner asked to keep them as a todo list, 2026-11-10. Not yet prioritised.

- [ ] **Commute filters**
  - Combined commute to two hubs, as a sum or a maximum (family).
  - "Within N min of any hub" or of the nearest hub (mathematician).
  - Public transport minus car time (mathematician).
- [ ] **Travel-time detail:** spread over the morning (P10/median/P90) and both directions (mathematician).
- [ ] **Custom similarity:** choose metrics and weights, and show what drives each match. Consider Mahalanobis or PCA (mathematician).
- [x] **Year comparisons** (done; URL keys `yc`, `ym`, `fx`, `sm`)
  - [x] Change between two years as a metric (economist): absolute and percent, diverging around 0.
  - [x] Fixed class breaks across years (statistician): `fx=1`, limits from all complete years pooled.
  - [ ] Series-break markers: shown for incomplete rounds (shipped). Real method breaks (census to STATPOP, GWS heating, party mergers) need a `series_breaks` field in `metrics.json`; the frontend reads it as soon as a build ships it.
  - [x] Small multiples of several years (statistician).
- [x] **Reliability** (done where the data allows): the Structural Survey and rents ship `<id>_ci` half-widths, which now give the interval on the card, a rank range and the count of units whose interval crosses a class. Every other survey or modelled value gets a badge. Intervals for Arealstatistik and modelled metrics need pipeline work (see the report of this change).
- [ ] **More data**
  - Median income, e.g. estimated from the ESTV income classes (economist, mathematician).
  - Noise exposure, childcare places, school locations (family).
  - Recent language data: pooled Structural Survey, municipal or MS region (journalist, geographer).
- [ ] **Map:** [x] reference layer with lake and city labels (canvas, from shipped data); [x] circles by default for count metrics; [ ] more detailed boundaries on zoom (needs a finer geometry file; only one generalised version ships) (geographer).
- [ ] **Spatial statistics:** Moran's I, LISA cluster map, bivariate choropleth (geographer).
- [ ] **Older boundaries:** view data on older boundaries (e.g. 2000) as well as harmonised (geographer).
- [ ] **Filtered aggregate:** weighted result for the filtered set, e.g. "French-speaking CH: X % yes" (journalist).
- [ ] **Embedding:** embeddable view (iframe) of any saved URL state (journalist).
- [ ] **Casual users:** plain-language "In short" summary per place; "places like X near Y" (casual user).
- [ ] **Ranking table:** add any metric as a column; minimum-size filter or flag for small municipalities (analyst, economist).
- [ ] **Open data and repo**
  - Data release: observation Parquet, metrics CSV with licence columns, GeoPackage.
  - Sample data so `npm run dev` works after cloning; CI workflow.
  - Unit tests for search, hash, classify.
  - (coder, geographer, analyst)
