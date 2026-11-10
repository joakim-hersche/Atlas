"""Older boundary vintages (pipeline/build/vintages.py, docs/older_boundaries.md).

Unit tests of the derivation rules run on synthetic data; the checks on the built files are skipped
when `python -m pipeline.build.vintages` has not been run.
"""
import json

import numpy as np
import pandas as pd
import pytest

from pipeline.build.vintages import derive, national
from pipeline.common import OUT

CATALOG = {
    "a": {"aggregation": "sum"}, "b": {"aggregation": "sum"}, "c": {"aggregation": "sum"},
    "share_a": {"aggregation": "ratio:a/b*100"},
    "share_ac": {"aggregation": "ratio:a+c/b*100"},
    "share_x": {"aggregation": "ratio:x/b*100"},          # input missing on this state: not derived
}


def _base(rows):
    return pd.DataFrame(rows, columns=["hist_id", "period", "metric_id", "value", "precision"]).assign(
        provenance="native", kind="native", source_id="s", note="n")


def test_derive_ratios_and_precision():
    base = _base([
        (1, "2000", "a", 10.0, "exact"), (1, "2000", "b", 40.0, "exact"), (1, "2000", "c", 2.0, "exact"),
        (2, "2000", "a", 5.0, "boundary_estimate"), (2, "2000", "b", 0.0, "exact"), (2, "2000", "c", 1.0, "exact"),
        (3, "2000", "a", 3.0, "exact"), (3, "2000", "b", 6.0, "boundary_estimate"), (3, "2000", "c", np.nan, "exact"),
    ])
    d = derive(base, CATALOG).set_index(["metric_id", "hist_id"])
    assert set(d.index.get_level_values(0)) == {"share_a", "share_ac"}
    assert d.loc[("share_a", 1), "value"] == pytest.approx(25.0)
    assert np.isnan(d.loc[("share_a", 2), "value"])                     # zero denominator -> gap
    assert d.loc[("share_a", 3), "precision"] == "boundary_estimate"    # worst input precision
    assert d.loc[("share_ac", 1), "value"] == pytest.approx(30.0)
    assert np.isnan(d.loc[("share_ac", 3), "value"])                    # a missing input -> gap


def test_derive_keeps_only_periods_with_inputs():
    # a second source with another period must not create empty periods for the census shares
    base = _base([(1, "2000", "a", 1.0, "exact"), (1, "2000", "b", 2.0, "exact"), (1, "2010", "c", 5.0, "exact")])
    d = derive(base, CATALOG)
    assert set(d.loc[d["metric_id"] == "share_a", "period"]) == {"2000"}


def test_national_ratio_of_sums():
    base = _base([(1, "2000", "a", 10.0, "exact"), (1, "2000", "b", 40.0, "exact"),
                  (2, "2000", "a", 30.0, "exact"), (2, "2000", "b", 60.0, "exact")])
    ch = national(base, CATALOG)
    assert ch[("a", "2000")] == 40 and ch[("b", "2000")] == 100
    assert ch[("share_a", "2000")] == pytest.approx(40.0)   # not the mean of 25 % and 50 %


# ---------------------------------------------------------------- built files
WEB = OUT / "web"
built = pytest.mark.skipif(not (WEB / "vintages.json").exists(), reason="vintages not built (python -m pipeline.build.vintages)")


def _j(*parts):
    return json.loads(OUT.joinpath(*parts).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def index():
    return _j("web", "vintages.json")


def _values(v):
    out = {}
    for f in v["files"].values():
        out.update(_j(*f["path"].split("/"))["metrics"])
    return out


def _series_ch(metric, period):
    p = WEB / "series" / f"{metric}.json"
    if not p.exists():
        return None
    s = json.loads(p.read_text(encoding="utf-8"))
    return s["levels"]["schweiz"]["CH"][s["periods"].index(period)] if period in s["periods"] else None


@built
def test_units_geometry_and_values_align(index):
    for v in index["vintages"]:
        units = _j(*v["units"]["path"].split("/"))["units"]
        ids = [u["id"] for u in units]
        assert len(ids) == len(set(ids)) == v["n_units"]
        topo = _j(*v["geometry"]["path"].split("/"))
        geo_ids = {str(g["properties"]["id"]) for g in topo["objects"]["gemeinde"]["geometries"]}
        assert geo_ids == set(ids), f"{v['id']}: every unit has exactly one polygon"
        assert "lakes" in topo["objects"]
        for f in v["files"].values():
            assert _j(*f["path"].split("/"))["units"] == ids
        # successors on the reference state: shares of the old unit's residents add up to 1
        for u in units:
            assert u["to"], f"{v['id']} {u['id']} has no successor"
            assert sum(w for *_, w in u["to"]) == pytest.approx(1, abs=0.002)


@built
def test_expected_states(index):
    n = {v["id"]: v["n_units"] for v in index["vintages"]}
    assert n == {"2000": 2896, "2010": 2584}   # census 2000 state; STATPOP 2010 municipality file


@built
def test_census_totals_match_published_national_values(index):
    """Counts summed over the old municipalities equal the national census totals (2000: native;
    2010: carried forward, so the sum is preserved)."""
    checked = 0
    for v in index["vintages"]:
        vals = _values(v)
        for mid in ("vz_lang_total", "vz_rel_total", "vz_hh_private", "vz_lang_fr", "vz_rel_catholic"):
            for col in vals[mid]:
                pub = _series_ch(mid, col["period"])
                if pub is None:
                    continue
                assert sum(x for x in col["v"] if x is not None) == pytest.approx(pub, abs=1), (v["id"], mid, col["period"])
                assert col["ch"] == pytest.approx(pub, abs=1)
                checked += 1
    if not checked:
        pytest.skip("harmonised series files not built")


@built
def test_statpop_2010_matches_published_series(index):
    v = next(x for x in index["vintages"] if x["id"] == "2010")
    vals = _values(v)
    for mid in ("pop_total", "pop_swiss", "pop_foreign", "pop_male", "pop_female"):
        pub = _series_ch(mid, "2010")
        if pub is None:
            pytest.skip("harmonised series files not built")
        assert vals[mid][0]["ch"] == pub, mid
    assert v["metrics"]["pop_total"]["provenance"] == "native"


@built
def test_shares_recomputed_from_counts(index):
    v = next(x for x in index["vintages"] if x["id"] == "2000")
    vals = _values(v)
    for share, num, den in (("vz_lang_fr_share", "vz_lang_fr", "vz_lang_total"),
                            ("vz_rel_catholic_share", "vz_rel_catholic", "vz_rel_total")):
        for cs, cn, cd in zip(vals[share], vals[num], vals[den]):
            assert cs["period"] == cn["period"] == cd["period"]
            for s, n, d in zip(cs["v"], cn["v"], cd["v"]):
                if d:
                    assert s == pytest.approx(100 * n / d, abs=0.051)


@built
def test_forward_unchanged_units_keep_their_values(index):
    """A municipality with the same histId on both states has identical census counts."""
    by = {v["id"]: v for v in index["vintages"]}
    u0 = {u["hist_id"]: k for k, u in enumerate(_j("web", "vintage", "2000", "units.json")["units"])}
    u1 = {u["hist_id"]: k for k, u in enumerate(_j("web", "vintage", "2010", "units.json")["units"])}
    same = [(u0[h], u1[h]) for h in set(u0) & set(u1)]
    assert len(same) > 1000   # histIds also change on district reforms (single successor)
    c0 = _values(by["2000"])["vz_lang_total"]
    c1 = _values(by["2010"])["vz_lang_total"]
    for a, b in zip(c0, c1):
        assert all(a["v"][i] == b["v"][j] for i, j in same)
    m = by["2010"]["metrics"]["vz_lang_total"]
    assert m["provenance"] == "forward" and by["2000"]["metrics"]["vz_lang_total"]["provenance"] == "native"


@built
def test_only_cleared_sources_and_catalog_metrics(index):
    catalog = {m["id"] for m in _j("web", "metrics.json")}
    for v in index["vintages"]:
        assert set(v["metrics"]) <= catalog
        for m in v["metrics"].values():
            assert m["source"] in index["sources"]
    assert "bfs_hist_boundaries" in index["sources"]
