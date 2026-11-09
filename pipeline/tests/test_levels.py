"""Unit tests for level aggregation rules (synthetic membership, no network)."""
import numpy as np
import pandas as pd
import pytest

from pipeline.backbone import levels


@pytest.fixture(autouse=True)
def fake_membership(monkeypatch):
    m = pd.DataFrame({"bfs_nr": [1, 2, 3, 4], "kanton": ["A", "A", "B", "B"],
                      "agglomeration": ["10", pd.NA, "10", "20"]})
    monkeypatch.setattr(levels, "membership", lambda: m)


def test_sum_and_missing():
    df = pd.DataFrame({"bfs_nr": [1, 2, 3, 4], "value": [1.0, 2.0, 3.0, np.nan]})
    out = levels.aggregate(df, "kanton", "sum").set_index("unit_id")
    assert out.loc["A", "value"] == 3 and pd.isna(out.loc["B", "value"]) and out.loc["B", "n_missing"] == 1


def test_ratio_recomputed_from_parts():
    df = pd.DataFrame({"bfs_nr": [1, 2], "value": [0, 0], "vacant": [1.0, 9.0], "dwellings": [100.0, 100.0]})
    out = levels.aggregate(df, "kanton", "ratio:vacant/dwellings").set_index("unit_id")
    assert out.loc["A", "value"] == pytest.approx(0.05)


def test_weighted_mean_and_units_without_level():
    df = pd.DataFrame({"bfs_nr": [1, 2, 3, 4], "value": [10.0, 20.0, 30.0, 40.0], "pop": [1.0, 1.0, 3.0, 1.0]})
    out = levels.aggregate(df, "agglomeration", "weighted_mean:pop").set_index("unit_id")
    assert out.loc["10", "value"] == pytest.approx((10 + 90) / 4)   # municipality 2 has no agglomeration
    assert set(out.index) == {"10", "20"}


def test_not_aggregatable():
    df = pd.DataFrame({"bfs_nr": [1, 2, 3, 4], "value": [1.0, 2.0, 3.0, 4.0]})
    out = levels.aggregate(df, "agglomeration", "not_aggregatable").set_index("unit_id")
    assert pd.isna(out.loc["10", "value"]) and out.loc["20", "value"] == 4
