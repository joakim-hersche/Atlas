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
