"""Tests of the bfs_amr_rents connector (average net rent per m2 by labour market area, BFS RDISP)."""
from __future__ import annotations

import pandas as pd
import pytest
import yaml

from pipeline.common import RAW
from pipeline.harmonize.schema import OBS_COLUMNS, SOURCES_DIR, validate_metrics, validate_observations

SRC = "bfs_amr_rents"


def _metrics() -> pd.DataFrame:
    return pd.DataFrame(yaml.safe_load((SOURCES_DIR / SRC / "metrics.yaml").read_text(encoding="utf-8")))


def test_metrics_valid():
    m = _metrics()
    m["source_id"] = SRC
    assert not validate_metrics(m)
    assert set(m["native_level"]) == {"arbeitsmarktgebiet"} and set(m["precision"]) == {"survey"}


def test_labels_registered():
    reg = yaml.safe_load((SOURCES_DIR.parent / "i18n" / "labels.yaml").read_text(encoding="utf-8"))
    for i in _metrics()["id"]:
        assert i in reg and reg[i].get("label_fr")


@pytest.mark.skipif(not list((RAW / SRC).glob("*/DF_RDISP_2_SA1048V.csv")), reason="rent flow not cached")
def test_real_data():
    from pipeline.sources.bfs_amr_rents.ingest import observations
    o = observations()
    assert list(o.columns) == OBS_COLUMNS
    assert not validate_observations(o, set(_metrics()["id"]))
    assert o["level"].eq("arbeitsmarktgebiet").all() and o["unit_id"].nunique() == 101
    assert sorted(o["period"].unique()) == [str(y) for y in range(2012, 2025)]
    v = o[o.metric_id == "rent_amr_chf_m2"].pivot_table(index="unit_id", columns="period", values="value")
    # same figures as the Statatlas map of the same indicator (Zürich area 12033: 23.8 in 2024, 20.0 in 2012)
    assert v.loc["12033", "2024"] == 23.8 and v.loc["12033", "2012"] == 20.0
    assert v["2024"].between(8, 30).all()
    # Zürich and Genève areas are dearer than the Swiss median area; Scuol (mountain) is cheaper
    assert v.loc["12033", "2024"] > v["2024"].median() and v.loc["16110", "2024"] < v["2024"].median()
    ci = o[o.metric_id == "rent_amr_chf_m2_ci"].pivot_table(index="unit_id", columns="period", values="value")
    assert (ci.fillna(0) >= 0).all().all() and ci["2024"].median() < 2
