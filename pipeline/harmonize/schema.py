"""Harmonized observation schema and metric metadata (brief 4.2 and 5).

observation (one row per unit × metric × period):
  unit_id     BFS number (gemeinde), district number (bezirk), canton abbreviation (kanton),
              or the level's code for other levels
  level       gemeinde | bezirk | kanton | schweiz | <analysis level id>
  vintage     ISO date of the municipality state the row refers to (reference state for gemeinde)
  metric_id   id from a source's metrics.yaml
  period      '2025', '2020/25' (survey period), '2022-2024' (pooled), '2026-11' (month)
  value       float; NaN when status is not 'ok'
  status      ok | suppressed | not_published | not_covered | not_applicable | no_data
  precision   exact | survey | modelled | boundary_estimate
  provenance  source_current_state (BFS published on the current state)
              | aggregated_mergers (only mergers between source state and reference: exact)
              | reprojected_weighted (splits/territory exchanges involved: estimate)
              | native (published at this level by the source, e.g. canton totals)
  source_id   connector id (pipeline/sources/<source_id>)
  note        free text (e.g. reason for a gap)

Metric metadata (pipeline/sources/<source_id>/metrics.yaml), list of:
  id, theme, label_en, label_de, unit, decimals, direction (higher_better|lower_better|neutral),
  aggregation  sum | ratio:<num>/<den>[*<factor>] | weighted_mean:<metric> | not_aggregatable
               | change:<metric>:<years> | pooled:<num>/<den>[*<factor>]:<years>[:<den lag>] (derived)
  optional     zero_when, include_pseudo (pipeline.build.metrics), credit_source (source shown in the app)
  kind         base (delivered by the connector) | derived (computed by the build from base metrics)
  precision, coverage (national | partial:<cantons>), native_level, description, source_note
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

OBS_COLUMNS = ["unit_id", "level", "vintage", "metric_id", "period", "value", "status",
               "precision", "provenance", "source_id", "note"]
STATUS = {"ok", "suppressed", "not_published", "not_covered", "not_applicable", "no_data"}
PRECISION = {"exact", "survey", "modelled", "boundary_estimate"}
PROVENANCE = {"source_current_state", "aggregated_mergers", "reprojected_weighted", "native"}
THEMES = ["Geography & identity", "Population & demography", "Migration & nationality",
          "Language & religion", "Households & family", "Economy & jobs", "Income & tax",
          "Public finances", "Housing & buildings", "Real estate prices",
          "Land use & built environment", "Mobility & accessibility", "Energy & climate",
          "Environment & hazards", "Health & social", "Education", "Safety", "Politics"]
METRIC_KEYS = {"id", "theme", "label_en", "label_de", "unit", "decimals", "direction",
               "aggregation", "kind", "precision", "coverage", "native_level"}

# optional keys; anything else is a typo or an unquoted comma in a YAML flow mapping
OPTIONAL_METRIC_KEYS = {"description", "source_note", "volatile", "zero_when", "plausibility_note",
                        "additivity_note", "additivity_rounding", "additivity_tolerance", "bounded_0_100",
                        "allow_negative", "source_id", "include_pseudo", "credit_source", "unavailable_note"}

SOURCES_DIR = Path(__file__).resolve().parents[1] / "sources"


def load_metrics(source_id: str | None = None) -> pd.DataFrame:
    """Metric metadata of one source or of all sources."""
    files = [SOURCES_DIR / source_id / "metrics.yaml"] if source_id else sorted(SOURCES_DIR.glob("*/metrics.yaml"))
    rows = []
    for f in files:
        if not f.exists():
            continue
        for m in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
            m["source_id"] = f.parent.name
            rows.append(m)
    return pd.DataFrame(rows)


def validate_metrics(df: pd.DataFrame) -> list[str]:
    errors = []
    for m in df.to_dict("records"):
        unknown = {str(k) for k, v in m.items() if v is not None and v == v} - METRIC_KEYS - OPTIONAL_METRIC_KEYS
        if unknown:
            errors.append(f"{m.get('id')}: unknown keys {sorted(unknown)} (quote values containing commas)")
        missing = METRIC_KEYS - {k for k, v in m.items() if v is not None and v == v}
        if missing:
            errors.append(f"{m.get('id')}: missing {sorted(missing)}")
        if m.get("theme") not in THEMES:
            errors.append(f"{m.get('id')}: unknown theme {m.get('theme')!r}")
        if m.get("direction") not in ("higher_better", "lower_better", "neutral"):
            errors.append(f"{m.get('id')}: bad direction")
        agg = str(m.get("aggregation", ""))
        if not (agg in ("sum", "not_aggregatable") or agg.startswith(("ratio:", "weighted_mean:", "change:", "pooled:"))):
            errors.append(f"{m.get('id')}: bad aggregation {agg!r}")
    dup = df["id"][df["id"].duplicated()].tolist() if "id" in df else []
    if dup:
        errors.append(f"duplicate metric ids: {dup}")
    return errors


def validate_observations(obs: pd.DataFrame, metric_ids: set[str]) -> list[str]:
    errors = []
    missing = [c for c in OBS_COLUMNS if c not in obs.columns]
    if missing:
        return [f"missing columns {missing}"]
    unknown = set(obs["metric_id"]) - metric_ids
    if unknown:
        errors.append(f"metric ids not in metrics.yaml: {sorted(unknown)[:10]}")
    for col, allowed in (("status", STATUS), ("precision", PRECISION), ("provenance", PROVENANCE)):
        bad = set(obs[col].dropna()) - allowed
        if bad:
            errors.append(f"bad {col}: {bad}")
    ok_nan = obs[(obs["status"] == "ok") & obs["value"].isna()]
    if len(ok_nan):
        errors.append(f"{len(ok_nan)} rows with status ok but no value")
    dup = obs.duplicated(["unit_id", "level", "metric_id", "period"]).sum()
    if dup:
        errors.append(f"{dup} duplicate unit×metric×period rows")
    return errors
