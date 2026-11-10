# Gemeindebank build entry points.
#   make data      fetch (cached) + build everything the web app needs
#   make backbone  register, mutations, split weights, crosswalk
#   make geometry  web geometry and label points
#   make validate  backbone validation report (docs/backbone_report.md)
#   make observations / metrics / quality   ingest all sources, build all levels, plausibility sweep
#   make vintages  older boundary states (2000, 2010): geometry and the values published on them
#   make profile   search (names, postal codes), identity, boundary history, neighbours for the web app
#   make web-data  copy the data files the web app reads into web/public/data/
#   make web-app   install pinned npm deps and build the static site (web/dist/)
#   make deploy    publish web/dist to the gh-pages branch (GitHub Pages)
#   make release   package the open data release into data/out/release/ (after make data)
#   make test      unit tests (the data-dependent ones skip when data/ is not built)
# Set GB_REFRESH=1 to re-download sources; GB_REFERENCE_DATE=YYYY-MM-DD to change the target state.

PY := uv run python

.PHONY: data backbone geometry validate observations metrics quality web profile reach vintages web-data web-app release test clean-interim

data: backbone geometry validate observations metrics quality web profile reach vintages

backbone:
	$(PY) -m pipeline.backbone.build

geometry: backbone
	$(PY) -m pipeline.build.geometry

validate: backbone
	$(PY) -m pipeline.backbone.validate

observations: backbone
	$(PY) -m pipeline.harmonize.run

metrics: observations
	$(PY) -m pipeline.build.metrics

quality: metrics
	$(PY) -m pipeline.build.quality

web: metrics geometry
	$(PY) -m pipeline.build.web

# needs units.json (web) and the reference-state polygons (geometry)
profile: web geometry
	$(PY) -m pipeline.build.profile

reach: geometry
	$(PY) -m pipeline.reach.run

# older boundary states (docs/older_boundaries.md); needs metrics.json (web) and the backbone
vintages: web
	$(PY) -m pipeline.build.vintages

# Web app (web/): copy the built data files into web/public/data/, then build the static site to web/dist/
web-data:
	cd web && node scripts/copy-data.mjs

web-app:
	cd web && npm ci && npm run build

deploy:
	./scripts/deploy_pages.sh

# needs a finished `make data`; writes only data/out/release/ (licence-gated)
release:
	$(PY) -m pipeline.release

test:
	uv run pytest -q pipeline/tests

clean-interim:
	rm -rf data/interim/*
