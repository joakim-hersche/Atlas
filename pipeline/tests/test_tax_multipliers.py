"""Tests of the kt_tax_multipliers connector (canton Zürich municipal tax multipliers)."""
from __future__ import annotations

import pandas as pd
import pytest
import yaml

from pipeline.common import RAW
from pipeline.harmonize.schema import OBS_COLUMNS, SOURCES_DIR, validate_metrics, validate_observations

SRC = "kt_tax_multipliers"


def _metrics() -> pd.DataFrame:
    return pd.DataFrame(yaml.safe_load((SOURCES_DIR / SRC / "metrics.yaml").read_text(encoding="utf-8")))


def test_metrics_valid():
    m = _metrics()
    m["source_id"] = SRC
    assert not validate_metrics(m)
    assert set(m["coverage"]) == {"partial:ZH"} and set(m["aggregation"]) == {"not_aggregatable"}


def test_labels_registered():
    reg = yaml.safe_load((SOURCES_DIR.parent / "i18n" / "labels.yaml").read_text(encoding="utf-8"))
    for i in _metrics()["id"]:
        assert i in reg and reg[i].get("label_fr")


@pytest.mark.skipif(not list((RAW / SRC).glob("*/zh_stf_timeseries.csv")), reason="ZH file not cached")
def test_real_data():
    from pipeline.sources.kt_tax_multipliers.ingest import observations
    o = observations()
    assert list(o.columns) == OBS_COLUMNS
    assert not validate_observations(o, set(_metrics()["id"]))
    v = o[(o.status == "ok")].pivot_table(index="unit_id", columns="period", values="value")
    # Zürich city: 119 % (2026); Winterthur 125 % (raw file kanton_zuerich_stf_aktuell.csv); both published by the canton
    assert v.loc["261", "2026"] == 119.0 and v.loc["230", "2026"] == 125.0
    assert len(v["2026"].dropna()) >= 155 and v["2026"].between(60, 140).all()
    # other cantons are not covered, never a number
    nc = o[o.status == "not_covered"]
    assert len(nc) > 0 and nc["value"].isna().all() and "261" not in set(nc["unit_id"])
