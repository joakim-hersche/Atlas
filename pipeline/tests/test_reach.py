"""Reach hubs (D39), main stations (expert audit MUST 2), multi-day station times, nearest-hub metrics.
Data checks skip when the inputs are not built."""
import numpy as np
import pandas as pd
import pytest

from pipeline.common import interim_path
from pipeline.reach import hubs as H

TT = interim_path("reach", "travel_times.parquet")
OBS = interim_path("observation", "reach_metrics.parquet")
STATPOP = interim_path("observation", "bfs_statpop.parquet")

# (hub, bfs_nr, label, (lo, hi)) station time towards the hub, minutes. Usual journey-planner times
# with a margin; Genève -> Zürich arrives 07:30-08:30 on early-morning trains (04:46 departure with a
# change, 190 min in the 2026 feed on every weekday checked; daytime direct trains 173 min).
KNOWN = [("zuerich", 230, "Winterthur", (18, 26)), ("zuerich", 2701, "Basel", (50, 60)),
         ("basel", 2829, "Liestal", (9, 16)), ("zuerich", 1711, "Zug", (21, 30)),
         ("zuerich", 6621, "Genève", (155, 195)), ("zuerich", 5192, "Lugano", (100, 125)),
         ("luzern", 1402, "Engelberg", (40, 50)), ("chur", 3921, "Arosa", (55, 68)),
         ("zuerich", 4021, "Baden", (12, 20))]


def test_hub_list():
    assert len(H.HUBS) == 21 and len(set(H.SLUGS)) == 21
    assert ("baden", "Baden", 8503504) in H.HUBS
    assert set(H.NEAREST_HUBS_EXPECTED) <= set(H.SLUGS)
    assert len(H.NEAREST_HUBS_EXPECTED) == 15
    assert set(H.AGGLO_HUB.values()) == set(H.NEAREST_HUBS_EXPECTED)
    # the picker keeps the other approved stations (D39)
    assert {"bellinzona", "chur", "fribourg", "sion", "schaffhausen", "thun"} <= set(H.SLUGS) - set(H.NEAREST_HUBS_EXPECTED)


@pytest.mark.skipif(not STATPOP.exists(), reason="STATPOP observations not built")
def test_nearest_hub_set_matches_rule():
    slugs, q = H.nearest_hubs()          # raises when the derived set differs from the approved 15
    assert slugs == H.NEAREST_HUBS_EXPECTED
    a = H.agglomeration_population()
    assert (q["pop"] >= H.MIN_AGGLO_POP).all()
    assert set(a.loc[a["pop"] >= H.MIN_AGGLO_POP, "agglomeration"]) == set(q.agglomeration)
    assert (a.loc[~a.agglomeration.isin(q.agglomeration), "pop"] < H.MIN_AGGLO_POP).all()
    # each agglomeration's hub station lies in its core municipality (agglomeration code = core BFS number)
    tt = pd.read_parquet(TT) if TT.exists() else None
    if tt is not None:
        ms = tt[(tt.method == "gtfs_rcsa_mainstation") & (tt.minutes == 0)]
        core = dict(zip(ms.hub, ms.bfs_nr))
        for code, slug in H.AGGLO_HUB.items():
            assert core.get(slug) == code, (slug, code, core.get(slug))


@pytest.mark.skipif(not OBS.exists() or not STATPOP.exists(), reason="reach metrics not built")
def test_nearest_metric_uses_only_rule_hubs():
    o = pd.read_parquet(OBS)
    names = {H.NAMES[s] for s in H.NEAREST_HUBS_EXPECTED}
    for mode in ("ptst", "pt", "car"):
        n = o[o.metric_id == f"reach_{mode}_nearest_hub"]
        assert len(n) == 2110
        ok = n[n.status == "ok"]
        used = ok.note.str.extract(r"^nearest hub: ([^;]+)")[0]
        assert used.notna().all()
        assert set(used) <= names, set(used) - names
        # the value is the minimum over the 15 hubs, never over the others
        w = o[o.metric_id.isin([f"reach_{mode}_{s}" for s in H.NEAREST_HUBS_EXPECTED]) & (o.status == "ok")]
        mn = w.groupby("unit_id").value.min()
        assert np.allclose(ok.set_index("unit_id").value, mn.reindex(ok.unit_id).values)


@pytest.mark.skipif(not OBS.exists(), reason="reach metrics not built")
def test_no_arrival_is_not_applicable():
    o = pd.read_parquet(OBS)
    pt = o[o.metric_id.str.startswith(("reach_ptst_", "reach_pt_"))]
    late = pt[pt.note.str.contains("no arrival at the hub by 10:30", na=False)]
    assert len(late) and (late.status == "not_applicable").all()
    assert not ((pt.status == "no_data") & pt.note.str.contains("no arrival", na=False)).any()


@pytest.mark.skipif(not TT.exists(), reason="reach not built")
def test_known_pairs():
    t = pd.read_parquet(TT)
    st = t[t.method == "gtfs_rcsa_mainstation"].set_index(["hub", "bfs_nr"])["minutes"]
    for hub, bfs, label, (lo, hi) in KNOWN:
        assert lo <= st[(hub, bfs)] <= hi, (label, hub, st[(hub, bfs)])
    assert st[("baden", 4021)] == 0
    assert t.groupby(["method", "hub"]).bfs_nr.nunique().min() == 2110
    assert t.hub.nunique() == 21


@pytest.mark.skipif(not TT.exists(), reason="reach not built")
def test_main_station_by_population_served():
    t = pd.read_parquet(TT)
    ms = t[t.method == "gtfs_rcsa_mainstation"].drop_duplicates("bfs_nr").set_index("bfs_nr")
    assert ms.loc[1402, "main_station"] == "Engelberg"      # was Grafenort
    assert ms.loc[3921, "main_station"] == "Arosa"          # was St. Peter-Molinis
    assert ms.loc[3561, "main_station"] == "Poschiavo"      # was Alp Grüm
    assert ms.loc[5113, "main_station"] != "Riazzino"       # Locarno: a central station
    assert ms.loc[1069, "main_mode"] != "rail"              # Weggis: no rail station, labelled bus/boat
    assert ms.loc[261, "main_station"] == "Zürich HB"
    assert set(ms.main_mode.dropna()) <= {"rail", "bus", "boat", "tram", "metro", "cableway", "funicular"}


@pytest.mark.skipif(not TT.exists(), reason="reach not built")
def test_car_towards_hub():
    t = pd.read_parquet(TT)
    car = t[t["mode"] == "car"].set_index(["hub", "bfs_nr"])["minutes"]
    assert car[("zuerich", 261)] < 25
    assert 60 <= car[("zuerich", 351)] <= 130     # model incl. congestion; free flow is about 75 min


# ---------------------------------------------------------------- spread over the morning (P10 / median / P90)
from pipeline.reach import pt  # noqa: E402

SPREAD_METHODS = ("gtfs_rcsa_mainstation", "gtfs_rcsa_popweighted", "gtfs_fcsa_mainstation", "gtfs_fcsa_popweighted")


def test_pct_inf_and_forward_summary():
    x = np.array([[60.0, 60.0], [120.0, 60.0], [180.0, np.inf], [240.0, np.inf]])
    assert pt._pct_inf(x, 10)[0] == pytest.approx(np.percentile(x[:, 0], 10))
    p = pt._pct_inf(x, 90)
    assert p[0] == pytest.approx(np.percentile(x[:, 0], 90)) and np.isinf(p[1])     # depends on unreached rows
    j = np.array([[60.0], [120.0], [180.0]])
    med, medw, p10, p90, late, w10, w90 = pt.forward_summary(j, j + 30)
    assert (med[0], medw[0]) == (120.0, 150.0) and p10[0] < med[0] < p90[0] and w10[0] < medw[0] < w90[0]
    assert np.isnan(late[0])


def test_journey_times_cap():
    # one station, arrival constant over every scan: the vehicle leaves after the last scan, journey unknown
    ea = np.full((pt.N_SCAN, 1), 12 * 3600, np.int64)
    j_old, w = pt.journey_times(ea)
    j_cap, w2 = pt.journey_times(ea, cap_unreached=True)
    assert np.isfinite(j_old).all() and np.isinf(j_cap).all()
    assert np.array_equal(w, w2)                               # waiting incl. is unaffected
    ea2 = ea.copy()
    ea2[:, 0] = pt.T_FIRST + 60 * np.minimum(np.arange(pt.N_SCAN) // 10 * 10 + 10, pt.N_SCAN - 1) + 600   # changes every 10 minutes
    assert np.isfinite(pt.journey_times(ea2, cap_unreached=True)[0][:10]).all()


def test_combine_days_keeps_all_summary_fields():
    mk = lambda v: tuple(np.array([v + k]) for k in range(7))   # noqa: E731
    out = pt.combine_days([mk(300.0), mk(100.0), mk(200.0)])
    assert len(out) == 7 and out[0][0] == 200.0 and out[6][0] == 206.0      # the middle day, every field from it


def test_access_index_matches_popweighted_rows():
    # two municipalities; hectares with one or two stops in reach, one hectare without a stop
    acc = pd.DataFrame({
        "RELI": [1, 1, 2, 3, 4, 5, 5], "bfs_nr": [10, 10, 10, 10, 20, 20, 20], "BBTOT": [5, 5, 3, 2, 4, 6, 6],
        "idx": [0, 1, 1, 2, np.nan, 0, 2], "walk_s": [100, 400, 60, 30, np.nan, 500, 50]})
    st = np.array([600.0, 1200.0, np.inf])
    ai = pt.AccessIndex(acc)
    new = ai.municipality(st, np.array([10, 20, 30])).set_index("bfs_nr")
    old = {r[2]: r for r in pt.popweighted_rows("h", st, st, acc, np.array([10, 20, 30]))}
    for b in (10, 20, 30):
        assert (new.loc[b, "minutes"] == old[b][3]) or (np.isnan(new.loc[b, "minutes"]) and np.isnan(old[b][3]))
    assert new.loc[20, "status"] == "ok" and new.loc[30, "status"] == "no populated hectare"
    # P10 <= median <= P90 carries over to the door-to-door values
    s10, s90 = st * 0.9, st * 1.3
    lo, hi = ai.municipality(s10, np.array([10]))["minutes"][0], ai.municipality(s90, np.array([10]))["minutes"][0]
    assert lo <= new.loc[10, "minutes"] <= hi


@pytest.mark.skipif(not TT.exists(), reason="reach not built")
def test_spread_columns_ordered():
    t = pd.read_parquet(TT)
    if "minutes_wait_p10" not in t:
        pytest.skip("travel_times.parquet built before the spread")
    assert t.hub.nunique() == 21
    for m in SPREAD_METHODS:
        d = t[(t.method == m) & (t.status == "ok")].dropna(subset=["minutes_p10", "minutes_p90"])
        assert len(d) > 1500, m
        assert (d.minutes_p10 <= d.minutes + 1e-6).all() and (d.minutes <= d.minutes_p90 + 1e-6).all(), m
        w = t[(t.method == m) & (t.status == "ok")].dropna(subset=["minutes_wait_p10", "minutes_wait_p90", "minutes_incl_wait"])
        assert (w.minutes_wait_p10 <= w.minutes_incl_wait + 1e-6).all() and (w.minutes_incl_wait <= w.minutes_wait_p90 + 1e-6).all(), m
        # waiting is added to the journey, never subtracted (except a handful of far outward pairs where departures
        # with an unknown journey count as unreached in the journey median but not in the waiting median)
        assert (w.minutes_incl_wait < w.minutes - 1e-6).sum() <= 5, m
    # existing columns of the old methods are still there
    assert {"gtfs_csa_station", "gtfs_csa_popweighted", "gtfs_rcsa_mainstation"} <= set(t.method)


@pytest.mark.skipif(not TT.exists(), reason="reach not built")
def test_spread_sanity_pairs():
    t = pd.read_parquet(TT)
    if "minutes_wait_p10" not in t:
        pytest.skip("travel_times.parquet built before the spread")
    st = t[t.method == "gtfs_rcsa_mainstation"].set_index(["hub", "bfs_nr"])
    wint, ober = st.loc[("zuerich", 230)], st.loc[("zuerich", 93)]
    # Winterthur -> Zürich: frequent service, narrow range; both the journey and with waiting
    assert wint.minutes_p90 - wint.minutes_p10 <= 12
    assert wint.minutes_wait_p90 - wint.minutes_wait_p10 <= 12
    # a rural stop with an hourly bus: same journey time, but the waiting makes the range much wider
    assert ober.minutes_wait_p90 - ober.minutes_wait_p10 >= 2 * (wint.minutes_wait_p90 - wint.minutes_wait_p10)
    fo = t[t.method == "gtfs_fcsa_mainstation"].set_index(["hub", "bfs_nr"])
    assert 15 <= fo.loc[("zuerich", 230)].minutes <= 30 and fo.loc[("zuerich", 230)].minutes_p90 - fo.loc[("zuerich", 230)].minutes_p10 <= 12
    assert fo.loc[("zuerich", 261)].minutes == 0           # the hub itself


SPREAD_DIR = interim_path("reach").parent.parent / "out" / "reach"


@pytest.mark.skipif(not (SPREAD_DIR / "spread.json").exists() or not TT.exists(), reason="spread files not built")
def test_spread_files():
    import json
    idx = json.loads((SPREAD_DIR / "spread.json").read_text())
    units = idx["units"]
    assert len(units) == 2110 and units == sorted(units, key=int)
    rt = SPREAD_DIR.parent / "web" / "reach_times.json"
    if rt.exists():
        assert json.loads(rt.read_text())["units"] == units      # same order as reach_times.json
    f = json.loads((SPREAD_DIR / "zuerich_spread.json").read_text())
    blk = f["to"]["pt_station"]["journey"]
    assert set(blk) == {"p10", "p50", "p90"} and all(len(v) == len(units) for v in blk.values())
    i = units.index("230")
    assert blk["p10"][i] <= blk["p50"][i] <= blk["p90"][i]
    assert set(f["from"]) == {"pt_station", "pt"} and f["from"]["pt_station"]["with_wait"]["p50"][units.index("261")] == 0
    assert len(list(SPREAD_DIR.glob("*_spread.json"))) == 21


@pytest.mark.skipif(not OBS.exists(), reason="reach metrics not built")
def test_spread_metrics():
    o = pd.read_parquet(OBS)
    ids = sorted(m for m in o.metric_id.unique() if m.startswith("reach_spread_"))
    if not ids:
        pytest.skip("observations built before the spread metrics")
    assert len(ids) == 10 and all(m.endswith("_nearest_hub") for m in ids)
    for m in ids:
        d = o[o.metric_id == m]
        assert len(d) == 2110
        assert d[d.status == "ok"].note.str.startswith("nearest hub: ").all()
    # P10 <= median <= P90 per unit where all exist (towards the hub: median = reach_ptst_nearest_hub)
    v = lambda m: o[(o.metric_id == m) & (o.status == "ok")].set_index("unit_id").value   # noqa: E731
    lo, md, hi = (v("reach_spread_to_ptst_p10_nearest_hub"), v("reach_ptst_nearest_hub"),
                  v("reach_spread_to_ptst_p90_nearest_hub"))
    j = lo.index.intersection(md.index).intersection(hi.index)
    assert len(j) > 1500 and (lo[j] <= md[j] + 1e-6).all() and (md[j] <= hi[j] + 1e-6).all()
    # existing metric ids are unchanged
    assert {"reach_ptst_zuerich", "reach_pt_zuerich", "reach_car_zuerich", "reach_pt_nearest_hub"} <= set(o.metric_id)
