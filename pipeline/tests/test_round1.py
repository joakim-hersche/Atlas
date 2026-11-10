"""Review round 1 rules (docs/web_data_contract.md): zero_when real-value rule, vote national ratio,
default-period rule, reverse CSA and reach station-time sanity. Data checks skip when not built."""
import glob
import json

import numpy as np
import pandas as pd
import pytest

from pipeline.common import OUT, RAW, interim_path

METRICS_ALL = interim_path("metrics_all.parquet")
TT = interim_path("reach", "travel_times.parquet")
WEB = OUT / "web"


def _rows(sql: str) -> pd.DataFrame:
    import duckdb
    return duckdb.sql(sql.replace("{M}", f"read_parquet('{METRICS_ALL}')")).df()


# ---------------------------------------------------------------- rules (no data needed)

def test_default_period_rule():
    from pipeline.build.web import default_period
    # Arealstatistik-like: newest round half done -> the last complete round is the default
    assert default_period([("2004/09", 2110), ("2013/18", 2110), ("2020/25", 1007)]) == "2013/18"
    # a few suppressed municipalities in the newest year do not move the default back
    assert default_period([("2024", 2110), ("2025", 2100)]) == "2025"
    assert default_period([("2026-03-08#6850", 2105), ("2026-06-14#6870", 10)], per_vote=True) == "2026-06-14#6870"


def test_reverse_csa_toy_network():
    """A -> B -> C on one trip, C is the target: latest departures and in-trip/boarding rules."""
    from pipeline.reach.csa import INF, Network
    con = pd.DataFrame({"dep": [100, 200, 150], "arr": [190, 290, 180], "from_idx": [0, 1, 0],
                        "to_idx": [1, 2, 1], "trip": [0, 0, 1], "seq": [1, 2, 1]})
    net = Network(dep=con.dep.to_numpy(np.int32), arr=con.arr.to_numpy(np.int32), frm=con.from_idx.to_numpy(np.int32),
                  to=con.to_idx.to_numpy(np.int32), trip=con.trip.to_numpy(np.int32),
                  board=np.ones(3, np.bool_), alight=np.ones(3, np.bool_), chain=np.full(3, -1, np.int32),
                  mct=np.array([0, 60, 0], np.int32), fp_start=np.zeros(4, np.int64), fp_to=np.zeros(0, np.int32),
                  fp_w=np.zeros(0, np.int32), n_trips=2, stations=None, connections=con, trips=None)
    ld = net.run_reverse([2], 300)
    assert ld[2] == 300 and ld[1] == 200
    # from A: trip 0 at 100 stays seated to C; trip 1 (A 150 -> B 180) misses the 60 s change at B (180+60 > 200)
    assert ld[0] == 100
    net.mct[1] = 10
    assert net.run_reverse([2], 300)[0] == 150      # now the change works: leave A at 150
    assert net.run_reverse([2], 250)[0] <= -INF      # nothing arrives at C by 250


# ---------------------------------------------------------------- built data

need_metrics = pytest.mark.skipif(not METRICS_ALL.exists(), reason="metrics_all.parquet not built")


@need_metrics
def test_zero_when_needs_a_real_value():
    """Party did not stand -> gap (not 0 %) in majority cantons; BE pooled communes still complete."""
    d = _rows("""SELECT level, unit_id, metric_id, value, status FROM {M} WHERE period = '2023'
                 AND metric_id IN ('nrw_share_left_bloc', 'nrw_share_svp')
                 AND ((level = 'gemeinde' AND unit_id = '3034') OR (level = 'kanton' AND unit_id IN ('AR', 'BE')))""")
    k = d.set_index(["level", "unit_id", "metric_id"])
    assert k.loc[("gemeinde", "3034", "nrw_share_left_bloc"), "status"] == "not_applicable"   # Rehetobel
    assert k.loc[("kanton", "AR", "nrw_share_left_bloc"), "status"] == "not_applicable"
    assert k.loc[("kanton", "AR", "nrw_share_svp"), "status"] == "ok"
    assert 30.8 <= k.loc[("kanton", "BE", "nrw_share_svp"), "value"] <= 31.0


@need_metrics
def test_vote_national_is_ratio_incl_swiss_abroad():
    """National yes share = yes/(yes+no) over municipalities + pseudo-units = the official result."""
    files = sorted(glob.glob(str(RAW / "bfs_votes_gemeinde" / "*" / "voteinfo_2026-06-14.json")))
    if not files:
        pytest.skip("voteinfo file not cached")
    official = {f"2026-06-14#{v['vorlagenId']}": v["resultat"]["jaStimmenInProzent"]
                for v in json.load(open(files[-1], encoding="utf-8"))["schweiz"]["vorlagen"]}
    d = _rows("""SELECT period, value FROM {M} WHERE level = 'schweiz' AND metric_id = 'vote_yes_share'
                 AND period LIKE '2026-06-14#%'""").set_index("period")["value"]
    for per, pct in official.items():
        assert abs(d[per] - pct) < 0.005, per
    be = _rows("""SELECT status FROM {M} WHERE level = 'kanton' AND unit_id = 'BE' AND metric_id = 'vote_yes_share'
                  AND period = '2026-06-14#6870'""")
    assert be["status"].tolist() == ["ok"]


@pytest.mark.skipif(not (WEB / "votes" / "index.json").exists(), reason="votes index not built")
def test_votes_index_staendemehr_matches_voteinfo():
    idx = {v["period"]: v for v in json.loads((WEB / "votes" / "index.json").read_text(encoding="utf-8"))["votes"]}
    checked = 0
    for f in sorted(glob.glob(str(RAW / "bfs_votes_gemeinde" / "*" / "voteinfo_*.json"))):
        js = json.load(open(f, encoding="utf-8"))
        date = f"{js['abstimmtag'][:4]}-{js['abstimmtag'][4:6]}-{js['abstimmtag'][6:]}"
        for v in js["schweiz"]["vorlagen"]:
            st, per = v.get("staende") or {}, f"{date}#{v['vorlagenId']}"
            if per not in idx or st.get("jaStaendeGanz") is None:
                continue
            yes = st["jaStaendeGanz"] + st["jaStaendeHalb"] / 2
            assert idx[per]["cantons_yes"] == yes, per
            checked += 1
    assert checked > 50


@pytest.mark.skipif(not TT.exists(), reason="reach not built")
def test_reach_station_times_sane():
    t = pd.read_parquet(TT)
    st = t[t.method == "gtfs_rcsa_mainstation"].set_index(["hub", "bfs_nr"])["minutes"]
    assert 18 <= st[("zuerich", 230)] <= 26     # Winterthur
    assert 50 <= st[("zuerich", 2701)] <= 60    # Basel
    assert 9 <= st[("basel", 2829)] <= 16       # Liestal
    assert 21 <= st[("zuerich", 1711)] <= 30    # Zug
    assert st[("zuerich", 261)] == 0            # hub municipality: hub station
    dd = t[t.method == "gtfs_rcsa_popweighted"].set_index(["hub", "bfs_nr"])["minutes"]
    assert dd[("zuerich", 93)] < 60             # Oberweningen (was 419 before the best-stop fix)
    assert t.groupby(["method", "hub"]).bfs_nr.nunique().min() == 2110
