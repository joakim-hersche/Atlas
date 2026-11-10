# Backlog

Feature requests from persona review round 1 (`docs/review_round1.md`) that are not in the current build (D32: defects, export, vote picker, small-number flags, French UI). Owner asked to keep them as a todo list, 2026-11-10. Not yet prioritised.

- [x] **Commute filters** (done: `f=m:...`, see web/src/lib/commute.svelte.ts)
  - Combined commute to two hubs, as a sum or a maximum (family).
  - "Within N min of any hub" or of the nearest hub (mathematician).
  - Public transport minus car time (mathematician).
- [ ] **Travel-time detail:** spread over the morning (P10/median/P90) and both directions (mathematician).
- [ ] **Custom similarity:** choose metrics and weights, and show what drives each match. Consider Mahalanobis or PCA (mathematician).
- [ ] **Year comparisons**
  - Change between two years as a metric (economist).
  - Fixed class breaks across years and series-break markers (statistician).
  - Small multiples of several years (statistician).
- [ ] **Reliability:** confidence intervals or a low-reliability badge for survey and modelled values, including rank intervals (statistician, mathematician).
- [ ] **More data**
  - Median income, e.g. estimated from the ESTV income classes (economist, mathematician).
  - Noise exposure, childcare places, school locations (family).
  - Recent language data: pooled Structural Survey, municipal or MS region (journalist, geographer).
- [ ] **Map:** reference layer with lake and city labels, more detailed boundaries on zoom, symbols by default for count metrics (geographer).
- [ ] **Spatial statistics:** Moran's I, LISA cluster map, bivariate choropleth (geographer).
- [ ] **Older boundaries:** view data on older boundaries (e.g. 2000) as well as harmonised (geographer).
- [x] **Filtered aggregate** (done: `ag=`, web/src/lib/aggregate.ts): weighted result for the filtered set, e.g. "French-speaking CH: X % yes" (journalist).
- [ ] **Embedding:** embeddable view (iframe) of any saved URL state (journalist).
- [ ] **Casual users:** plain-language "In short" summary per place; "places like X near Y" (casual user).
- [x] **Ranking table** (done: `xc=`, `rmin=`, `rmf=`): add any metric as a column; minimum-size filter or flag for small municipalities (analyst, economist).
- [ ] **Open data and repo**
  - Data release: observation Parquet, metrics CSV with licence columns, GeoPackage.
  - Sample data so `npm run dev` works after cloning; CI workflow.
  - Unit tests for search, hash, classify.
  - (coder, geographer, analyst)
