# Writing a source connector

One directory per source: `pipeline/sources/<source_id>/`

| File | Purpose |
|---|---|
| `fetch.py` (optional) | download functions using `pipeline.common.fetch()` (cached in `data/raw/<source_id>/<date>/`, manifest written) |
| `ingest.py` | `observations() -> pd.DataFrame` in the schema `pipeline.harmonize.schema.OBS_COLUMNS` |
| `metrics.yaml` | metadata of every metric the connector delivers (`kind: base`) and of derived metrics (`kind: derived`) |
| `meta.yaml` | source_id, title, publisher, url, license, attribution, vintage, years, catalog_ids |

Run and validate one connector: `uv run python -m pipeline.harmonize.run <source_id>` (writes `data/interim/observation/<source_id>.parquet`; prints row count and schema problems — there must be none).

Reference implementation: `pipeline/sources/bfs_statpop/`.

## Rules

1. **Never invent data.** Every value comes from a downloaded file. Unknown → `status` other than `ok` and `value` NaN, with the reason in `note`.
2. **Municipality rows are on the reference state** (`pipeline.common.REFERENCE_DATE`). Use:
   - `pipeline.harmonize.pxweb.to_observations()` for PxWeb cubes on BFS institutional geography;
   - `pipeline.harmonize.helpers.infer_vintage()` to find a source's municipality state from its BFS numbers, then `to_reference()` and `emit()`;
   - per-year files carrying `GDEHISTID`: pass `hist_id` instead of `bfs_nr` (no state needed).
   Use `rule="sum"` for counts. Deliver **counts** (numerators and denominators) as base metrics and define shares/rates as `kind: derived` with `aggregation: ratio:<num>/<den>[*100]` — the build computes them at every level. Use `weighted_mean:<metric>` only for values that are not counts (e.g. modelled mean distances), and `not_aggregatable` for medians/indices (those are kept only where the municipality mapping is 1:1).
3. **Published higher levels** (canton, district, Switzerland) are kept as `level` rows with `provenance: native` — they feed the plausibility sweep (docs/validation_plan.md).
4. **Precision**: `exact` (full count), `survey` (sample, add CI metrics if published), `modelled` (estimates, model outputs, zonal statistics), `boundary_estimate` (set automatically by `to_reference()` when weighted splits are involved).
5. **Gaps** (decision D21): `suppressed` (small-number protection), `not_published` (not at this level), `not_covered` (partial/`*` sources), `not_applicable`, `no_data`. Never write 0 for unknown. STATENT's "values < 4 set to 4" is kept as delivered but noted in metrics.yaml `source_note`.
6. **Periods** as strings: `2025`, `2020/25` (survey period), `2022-2024` (pooled years), `2026-10` (month).
7. **Metric ids**: snake_case, unique across all sources (prefix with a short topic if needed). `theme` must be one of the 18 catalog themes. `label_en` and `label_de` are required.
8. Do not edit shared modules (`pipeline/common.py`, `pipeline/harmonize/*`, `pipeline/backbone/*`, other sources). If you need a generic helper, put it in your source directory and report it.
9. Large raster/vector inputs: zonal statistics per municipality on the reference-state geometry (`data/interim/geo/units_<ref>.gpkg`, layer `gemeinde`, LV95), population-weighted where the metric is about exposure (STATPOP hectare grid via `pipeline.sources.bfs_statpop_geodata.fetch.hectare(year)`).
10. Be gentle with servers: PxWeb ≤ 1 request/s (the helper paces itself); cache everything through `fetch()`.
