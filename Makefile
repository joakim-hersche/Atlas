# Gemeindebank build entry points.
#   make data      fetch (cached) + build everything the web app needs
#   make backbone  register, mutations, split weights, crosswalk
#   make geometry  web geometry and label points
#   make validate  backbone validation report (docs/backbone_report.md)
#   make observations / metrics / quality   ingest all sources, build all levels, plausibility sweep
#   make test      unit tests
# Set GB_REFRESH=1 to re-download sources; GB_REFERENCE_DATE=YYYY-MM-DD to change the target state.

PY := uv run python

.PHONY: data backbone geometry validate observations metrics quality test clean-interim

data: backbone geometry validate observations metrics quality

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

test:
	uv run pytest -q pipeline/tests

clean-interim:
	rm -rf data/interim/*
