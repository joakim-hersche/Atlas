# Gemeindebank

Personal web app to explore and compare every Swiss municipality, district, canton and region on one map, on consistent boundaries over time.

Status: **Checkpoint 3 — data ready for the frontend, awaiting owner review** (`docs/checkpoint3.md`).

## Rebuild

Requirements: [uv](https://docs.astral.sh/uv/) (Python 3.13) and Node.js (for `npx mapshaper`).

```sh
uv sync          # install the pipeline's Python dependencies
make data        # fetch (cached) + build backbone, geometry and the validation report
make test        # unit tests
```

- Downloads are cached in `data/raw/<source>/<date>/` with a `manifest.jsonl` (URL, hash, time) and are never edited. Rebuilds reuse the cache; `GB_REFRESH=1 make data` downloads again.
- The target municipality state defaults to 2026-01-01 (decision D8: latest state). Override with `GB_REFERENCE_DATE=YYYY-MM-DD`.
- Outputs: `data/interim/` (tables, gitignored) and `data/out/` (files for the web app).

## Layout

```
pipeline/
  common.py                 paths, cached downloads, date helpers
  sources/<source_id>/      fetch.py, parse.py, meta.yaml (license, attribution, vintage)
  backbone/                 register tables, split weights, crosswalk, to_vintage, validation
  build/                    outputs for the web app (geometry, ...)
  tests/
docs/                       catalog, decisions, validation reports
```

## Reprojecting data onto the reference state

```python
from pipeline.backbone.vintage import to_vintage
# df: one row per municipality, columns bfs_nr (valid on 2015-01-01) and value
out = to_vintage(df, source_vintage=date(2015, 1, 1), rule="sum")              # counts
out = to_vintage(df, source_vintage=date(2015, 1, 1), rule="weighted_mean:pop") # rates
out = to_vintage(df, source_vintage=date(2015, 1, 1), rule="not_aggregatable")  # medians
```

Pass `return_unmapped=True` to also get the source rows that couldn't be mapped: `out, unmapped = to_vintage(...)`.
