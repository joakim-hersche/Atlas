"""Unit tests for the crosswalk and to_vintage on a synthetic mutation history (no network)."""
import datetime as dt

import pandas as pd
import pytest

from pipeline.backbone import vintage
from pipeline.backbone.crosswalk import build_crosswalk

D = pd.Timestamp


def _mv(rows):
    df = pd.DataFrame(rows, columns=["hist_id", "bfs_nr", "name", "canton", "valid_from", "valid_to"])
    df["entry_mode"] = "11"
    df["valid_from"] = pd.to_datetime(df["valid_from"])
    df["valid_to"] = pd.to_datetime(df["valid_to"])
    return df


def _pairs(rows):
    return pd.DataFrame(rows, columns=["mutation_id", "date", "from_hist_id", "to_hist_id"]).assign(
        date=lambda d: pd.to_datetime(d["date"]))


@pytest.fixture
def history():
    # 1: A(1) + B(2) merge into C(3) on 2000-01-01
    # 2: D(4) split into E(5) and F(6) on 2005-01-01, weights 0.7 / 0.3
    # 3: E(5) renamed to E'(7) on 2010-01-01
    # 4: G(8) unchanged
    mv = _mv([
        (1, 101, "A", "ZH", "1960-01-01", "1999-12-31"),
        (2, 102, "B", "ZH", "1960-01-01", "1999-12-31"),
        (3, 103, "C", "ZH", "2000-01-01", None),
        (4, 104, "D", "BE", "1960-01-01", "2004-12-31"),
        (5, 105, "E", "BE", "2005-01-01", "2009-12-31"),
        (6, 106, "F", "BE", "2005-01-01", None),
        (7, 105, "E-new", "BE", "2010-01-01", None),
        (8, 108, "G", "BE", "1960-01-01", None),
    ])
    pair = _pairs([
        (1, "2000-01-01", 1, 3), (1, "2000-01-01", 2, 3),
        (2, "2005-01-01", 4, 5), (2, "2005-01-01", 4, 6),
        (3, "2010-01-01", 5, 7),
    ])
    sw = pd.DataFrame([(2, 4, 5, 0.7, "pop_ha_2004"), (2, 4, 6, 0.3, "pop_ha_2004")],
                      columns=["mutation_id", "from_hist_id", "to_hist_id", "weight", "weight_source"])
    return mv, pair, sw


def test_crosswalk_topology_and_weights(history):
    mv, pair, sw = history
    cw = build_crosswalk(mv, pair, sw, dt.date(2026, 1, 1))
    m = {(r.from_hist_id, r.to_hist_id): r.weight for r in cw.itertuples()}
    assert m[(1, 3)] == 1 and m[(2, 3)] == 1            # merger
    assert m[(4, 7)] == pytest.approx(0.7)              # split then rename
    assert m[(4, 6)] == pytest.approx(0.3)
    assert m[(5, 7)] == 1 and m[(8, 8)] == 1            # rename, unchanged
    assert cw.groupby("from_hist_id")["weight"].sum().round(9).eq(1).all()
    assert set(cw["to_hist_id"]) == {3, 6, 7, 8}


def test_crosswalk_to_intermediate_date(history):
    mv, pair, sw = history
    cw = build_crosswalk(mv, pair, sw, dt.date(2006, 6, 1))
    assert set(cw.loc[cw.from_hist_id == 4, "to_hist_id"]) == {5, 6}
    assert set(cw.loc[cw.from_hist_id == 7, "to_hist_id"]) == set()  # not yet existing: no mapping


def test_to_vintage_rules(history, monkeypatch):
    mv, pair, sw = history
    cw = build_crosswalk(mv, pair, sw, dt.date(2026, 1, 1))
    monkeypatch.setattr(vintage, "crosswalk", lambda target=None: cw)
    monkeypatch.setattr(vintage, "load_backbone", lambda: (mv, pair))
    df = pd.DataFrame({"bfs_nr": [101, 102, 104, 108], "value": [10.0, 20.0, 100.0, 5.0],
                       "pop": [10.0, 20.0, 100.0, 5.0]})
    s = vintage.to_vintage(df, source_vintage=dt.date(1990, 1, 1), rule="sum").set_index("bfs_nr")["value"]
    assert s[103] == 30 and s[105] == pytest.approx(70) and s[106] == pytest.approx(30) and s[108] == 5
    assert s.sum() == pytest.approx(df["value"].sum())

    rates = pd.DataFrame({"bfs_nr": [101, 102], "value": [0.1, 0.4], "pop": [10.0, 30.0]})
    r = vintage.to_vintage(rates, source_vintage=dt.date(1990, 1, 1), rule="weighted_mean:pop")
    assert r.set_index("bfs_nr").loc[103, "value"] == pytest.approx((0.1 * 10 + 0.4 * 30) / 40)

    med = pd.DataFrame({"bfs_nr": [101, 102, 104, 108], "value": [1.0, 2.0, 3.0, 4.0]})
    n = vintage.to_vintage(med, source_vintage=dt.date(1990, 1, 1), rule="not_aggregatable").set_index("bfs_nr")["value"]
    assert pd.isna(n[103]) and pd.isna(n[105]) and pd.isna(n[106]) and n[108] == 4


def test_unmapped_rows_are_reported(history, monkeypatch):
    mv, pair, sw = history
    cw = build_crosswalk(mv, pair, sw, dt.date(2026, 1, 1))
    monkeypatch.setattr(vintage, "crosswalk", lambda target=None: cw)
    monkeypatch.setattr(vintage, "load_backbone", lambda: (mv, pair))
    df = pd.DataFrame({"bfs_nr": [101, 999], "value": [1.0, 2.0]})
    out, unmapped = vintage.to_vintage(df, source_vintage=dt.date(1990, 1, 1), rule="sum",
                                       return_unmapped=True)
    assert list(unmapped["bfs_nr"]) == [999]
    assert list(out["bfs_nr"]) == [103]
