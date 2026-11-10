# Gemeindebank

Personal web app to explore and compare every Swiss municipality, district, canton and region on one map, on consistent boundaries over time.

Status: **Checkpoint 3 — data ready for the frontend, awaiting owner review** (`docs/checkpoint3.md`).

## Try it without the data

The repository ships a small sample dataset (`web/sample-data/`, 3.6 MB: eight open metrics, all 2,110 municipalities, plus districts and cantons). No pipeline run is needed:

```sh
cd web
npm ci
npm run dev      # uses web/sample-data when data/out/web has not been built
```

`ATLAS_SAMPLE=1 npm run build` forces the sample even if a full build exists. The sample is regenerated from a full build with `uv run python scripts/make_sample_data.py`; it only takes metrics whose source is fully open for redistribution.

## Rebuild

Requirements: [uv](https://docs.astral.sh/uv/) (Python 3.13) and Node.js 22 (the geometry step runs `npx mapshaper`, pinned in `pipeline/build/geometry.py`).

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

## Add a source

1. Create `pipeline/sources/<source_id>/` with `meta.yaml` (title, publisher, url, **license**, **attribution**, vintage, years), `metrics.yaml` (one entry per metric) and `ingest.py` (`observations()` returns the harmonized rows). Downloads go through `pipeline.common.fetch()` so they are cached and logged. Rules and a reference implementation are in `docs/connector_guide.md`.
2. Run it alone: `uv run python -m pipeline.harmonize.run <source_id>` (it must print no schema problems).
3. Settle the licence before the data can be published. A source whose `meta.yaml` licence does not state open terms is held back by the build. Record the reviewed terms in `pipeline/licence_review.yaml` (`cleared` needs evidence, `blocked` keeps it out, `metrics:` and `cantons:` limit a clearance). Terms that allow only non-commercial use go in `pipeline/release_flags.yaml`.
4. `make data` rebuilds everything the site needs. The source then shows up on the Sources page and in the release.

## Tests

```sh
make test                                # pipeline: uv run pytest -q pipeline/tests
cd web && npm test                       # frontend unit tests (vitest): search, URL hash, classification
cd web && npx svelte-check --threshold error
```

Pipeline tests that need built data (`data/interim`, `data/out/web`, raw downloads) skip themselves when it is missing, so they run on a fresh clone. GitHub Actions (`.github/workflows/ci.yml`) runs pytest, svelte-check, the vitest tests and the frontend build (with the sample data) on every pull request and push to `main`. It does not deploy and uses no secrets.

## Data release

```sh
make release     # after `make data`: builds data/out/release/ from the built tables
```

Writes `data/out/release/` and nothing else: `observations.parquet`, `metrics.csv` (with licence and attribution columns), `sources.csv`, `boundaries.gpkg`, `excluded.csv` and a `README.md` with the licences and the attribution to quote. It applies the same licence gate as the site, plus `pipeline/release_flags.yaml` (sources flagged non-commercial, cantons left out). The release is not committed; attach it to a GitHub release or share it as a download.

## Deploy

The site is a static build served by GitHub Pages from the `gh-pages` branch:

```sh
make data web-data web-app   # data, copy into web/public/data, build web/dist
make deploy                  # scripts/deploy_pages.sh: replaces the branch with the build
```

Deployment is manual; CI never deploys.

## Licences and attribution

Every dataset is tracked with its licence and attribution in its `meta.yaml`. The Sources page of the site and `sources.csv` of the release list them. Data keep the terms of their publishers (mostly "free use, cite the source"); anything with unclear or restrictive terms is not published (`docs/licences.md`).
