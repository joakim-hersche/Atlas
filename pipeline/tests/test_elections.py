"""National Council rules of decision D37 on the built data (skip when not built).

- canton and Swiss party strength vs BFS cube 104 within 0.01 pp (2019, 2023; Moutier counted with the
  canton it voted in, so JU/BE are compared on election-time boundaries);
- party shares add up to 100 ± 0.05 for every unit at every level and election, in metrics_all and in
  the shipped latest files;
- every party metric at a level defaults to one election (the newest one it stood in);
- no no_data where a party did not stand;
- the majority-election flag is on every row of single-seat canton-years (latest and series files).
"""
import json

import pandas as pd
import pytest

from pipeline.common import OUT, interim_path

METRICS_ALL = interim_path("metrics_all.parquet")
OBS = interim_path("observation", "bfs_nrw.parquet")
WEB = OUT / "web"
need = pytest.mark.skipif(not METRICS_ALL.exists() or not OBS.exists(), reason="metrics not built")
need_web = pytest.mark.skipif(not (WEB / "metrics.json").exists(), reason="web data not built")


def _sql(q: str) -> pd.DataFrame:
    import duckdb
    return duckdb.sql(q.replace("{M}", f"read_parquet('{METRICS_ALL}')").replace("{O}", f"read_parquet('{OBS}')")).df()


def _parties() -> list[str]:
    from pipeline.sources.bfs_nrw.ingest import PARTY_SLUG
    return list(PARTY_SLUG.values())


def _cube104() -> pd.DataFrame:
    from pipeline.sources.bfs_nrw.fetch import canton_parties
    from pipeline.sources.bfs_nrw.ingest import PARTY_SLUG
    k = canton_parties()
    k = k[k["Ergebnisse"] == "3"].assign(party=lambda x: x["Partei"].map(PARTY_SLUG))
    return k.rename(columns={"Kanton": "unit", "Jahr": "period"})[["unit", "period", "party", "value"]]


def canton_at_election(year: int) -> pd.Series:
    """Reference-state bfs_nr -> canton its territory voted in at the election (largest weight)."""
    import datetime as dt
    from pipeline.backbone.crosswalk import load_backbone, versions_at
    from pipeline.backbone.vintage import crosswalk
    from pipeline.common import REFERENCE_DATE
    mv, _ = load_backbone()
    at = versions_at(mv, dt.date(year, 10, 1))[["hist_id", "canton"]].astype({"hist_id": "int64"})
    m = at.merge(crosswalk(REFERENCE_DATE)[["from_hist_id", "to_bfs_nr", "weight"]], left_on="hist_id", right_on="from_hist_id")
    m = m.groupby(["to_bfs_nr", "canton"])["weight"].sum().reset_index().sort_values("weight")
    m = m.drop_duplicates("to_bfs_nr", keep="last")
    return m.set_index(m["to_bfs_nr"].astype(int))["canton"]


@need
@pytest.mark.parametrize("year", ["2019", "2023"])
def test_canton_and_ch_shares_match_cube_104(year):
    pub = _cube104()
    pub = pub[(pub["period"] == year) & pub["value"].notna()]
    # Switzerland: the shipped share (LPS counted under FDP, D37 rule 3)
    ch = _sql(f"SELECT metric_id, value FROM {{M}} WHERE level = 'schweiz' AND period = '{year}' "
              "AND metric_id LIKE 'nrw_share_%'").set_index("metric_id")["value"]
    for r in pub[pub["unit"] == "CH"].itertuples():
        mid = "nrw_share_mitte" if r.party in ("mitte",) else f"nrw_share_{r.party}"
        got = ch[mid] if r.party not in ("cvp", "bdp") else ch[f"nrw_share_{r.party}"]
        assert abs(got - r.value) <= 0.01, (r.party, got, r.value)
    # cantons at election-time boundaries: municipal fictitious voters + pseudo-units of the canton
    g = _sql(f"SELECT unit_id, metric_id, value FROM {{M}} WHERE level = 'gemeinde' AND period = '{year}' "
             "AND metric_id LIKE 'nrw_fw_%' AND value IS NOT NULL")
    kt = canton_at_election(int(year))
    g["kt"] = g["unit_id"].astype(int).map(kt)
    ps = _sql(f"SELECT unit_id, metric_id, value FROM {{O}} WHERE level = 'pseudo' AND period = '{year}' "
              "AND metric_id LIKE 'nrw_fw_%' AND status = 'ok'")
    from pipeline.build.metrics import pseudo_owner
    ct = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    by_nr = dict(zip(ct["canton_id"].astype(int), ct["canton"]))
    ps["kt"] = ps["unit_id"].map(lambda u: pseudo_owner(u, by_nr))
    s = pd.concat([g, ps]).groupby(["kt", "metric_id"])["value"].sum().unstack()
    share = s.div(s["nrw_fw_total"], axis=0) * 100
    n = 0
    for r in pub[pub["unit"] != "CH"].itertuples():
        got = share.loc[r.unit, f"nrw_fw_{r.party}"]
        assert abs(got - r.value) <= 0.01, (r.unit, r.party, got, r.value)
        n += 1
    assert n > 200
    # and the shipped canton values equal this computation outside JU/BE (Moutier, D16)
    k = _sql(f"SELECT unit_id, metric_id, value FROM {{M}} WHERE level = 'kanton' AND period = '{year}' "
             "AND metric_id LIKE 'nrw_share_%' AND value IS NOT NULL")
    for r in k[~k["unit_id"].isin(["JU", "BE"])].itertuples():
        p = r.metric_id[10:]
        if p in _parties() and p != "mitte":
            assert abs(share.loc[r.unit_id, f"nrw_fw_{p}"] - r.value) <= 0.01, (r.unit_id, p)


@need
def test_ch_fdp_includes_lps_and_svp_unchanged():
    ch = _sql("SELECT metric_id, period, value FROM {M} WHERE level = 'schweiz' AND metric_id IN "
              "('nrw_share_fdp', 'nrw_share_svp', 'nrw_share_lps')").pivot(index="period", columns="metric_id", values="value")
    assert abs(ch.loc["2023", "nrw_share_fdp"] - 14.25) <= 0.01
    assert abs(ch.loc["2019", "nrw_share_fdp"] - 15.11) <= 0.01
    assert abs(ch.loc["2023", "nrw_share_svp"] - 27.93) <= 0.01
    assert ch.loc[[p for p in ch.index if p >= "2011"], "nrw_share_lps"].isna().all()


def _sum_check(d: pd.DataFrame) -> pd.Series:
    """Σ party shares per unit (Mitte series counted without its CVP + BDP part)."""
    w = d.pivot_table(index=["level", "unit_id", "period"], columns="metric_id", values="value", aggfunc="first")
    has = w.notna().any(axis=1)
    w = w.fillna(0)
    tot = w.drop(columns=["nrw_share_mitte"]).sum(axis=1) + w["nrw_share_mitte"] - w["nrw_share_cvp"] - w["nrw_share_bdp"]
    return tot[has]


@need
def test_shares_sum_to_100_everywhere():
    ids = ", ".join(f"'nrw_share_{p}'" for p in _parties())
    d = _sql(f"SELECT level, unit_id, period, metric_id, value FROM {{M}} WHERE metric_id IN ({ids})")
    tot = _sum_check(d)
    bad = tot[(tot - 100).abs() > 0.05]
    assert bad.empty, bad.head(20)
    lv = set(tot.index.get_level_values("level"))
    assert {"gemeinde", "bezirk", "kanton", "grossregion", "sprachgebiet", "agglomeration", "schweiz"} <= lv
    per = set(tot.index.get_level_values("period"))
    assert {"1971", "1979", "2023"} <= per
    # the named units of the audit
    for lvl, u in (("grossregion", "2"), ("sprachgebiet", "1"), ("agglomeration", "351")):
        assert (lvl, u, "2023") in tot.index, (lvl, u)
    # blocs: left + centre + right + other = 100
    b = _sql("SELECT level, unit_id, period, SUM(value) AS s, COUNT(value) AS n FROM {M} WHERE metric_id IN "
             "('nrw_share_bloc_left', 'nrw_share_bloc_centre', 'nrw_share_bloc_right', 'nrw_share_bloc_other') GROUP BY ALL")
    full = b[b["n"] == 4]
    assert len(full) > 1000 and ((full["s"] - 100).abs() <= 0.05).all()


@need
def test_no_no_data_where_party_did_not_stand():
    """Gaps of party fictitious voters at municipality level are not_applicable / not_published only."""
    d = _sql("SELECT status, COUNT(*) AS n FROM {O} WHERE level = 'gemeinde' AND metric_id LIKE 'nrw_fw_%' "
             "AND metric_id <> 'nrw_fw_total' AND status = 'no_data' GROUP BY 1")
    assert d.empty, d
    # and no aggregate of a party share is a no_data gap
    a = _sql("SELECT level, COUNT(*) AS n FROM {M} WHERE metric_id LIKE 'nrw_share_%' AND status = 'no_data' "
             "AND level NOT IN ('gemeinde', 'kanton') GROUP BY 1")
    assert a.empty, a


def _majority():
    from pipeline.sources.bfs_nrw.fetch import majority_cantons
    return majority_cantons()


@need
def test_majority_status_in_single_seat_cantons():
    maj = _majority()
    assert maj["2023"] == ["AI", "AR", "GL", "NW", "OW", "UR"] and "AR" not in maj["1999"]
    d = _sql("SELECT unit_id, period, status FROM {M} WHERE level = 'kanton' AND metric_id = 'nrw_share_svp'")
    for r in d.itertuples():
        if r.unit_id in maj.get(r.period, []):
            assert r.status in ("majority_election", "not_applicable"), r
        else:
            assert r.status != "majority_election", r
    t = _sql("SELECT DISTINCT status FROM {M} WHERE metric_id = 'nrw_turnout'")
    assert "majority_election" not in set(t["status"])


@need_web
def test_shipped_latest_files():
    metrics = {m["id"]: m for m in json.loads((WEB / "metrics.json").read_text(encoding="utf-8"))}
    party = [f"nrw_share_{p}" for p in _parties()]
    maj = _majority()
    for lvl in ("gemeinde", "bezirk", "kanton", "grossregion", "sprachgebiet", "agglomeration", "schweiz"):
        cols, units = {}, None
        for f in (WEB / "latest" / lvl).glob("*.json"):
            j = json.loads(f.read_text(encoding="utf-8"))
            units = j["units"]
            cols.update({k: v for k, v in j["metrics"].items() if k.startswith("nrw_")})
        # one default election for all party metrics that stood in it
        stood = [m for m in party if m in cols and metrics[m].get("until") is None]
        assert {cols[m]["period"] for m in stood} == {"2023"}, (lvl, {m: cols[m]["period"] for m in stood})
        # Σ shares = 100 per unit (majority values from 'm')
        for i in range(len(units)):
            vals = {}
            for m in party:
                c = cols.get(m)
                if not c or c["period"] != "2023":
                    continue
                x = c["v"][i] if c["v"][i] is not None else c.get("m", {}).get(str(i))
                if x is not None:
                    vals[m] = x
            if vals:
                assert abs(sum(vals.values()) - 100) <= 0.05 + 0.0005 * len(vals), (lvl, units[i], sum(vals.values()))
        # majority flag on every single-seat canton row (gemeinde / bezirk / kanton)
        if lvl in ("gemeinde", "kanton"):
            from pipeline.backbone.levels import membership
            mem = membership()
            kt = dict(zip(mem["bfs_nr"].astype(str), mem["kanton"])) if lvl == "gemeinde" else {u: u for u in units}
            for m in stood:
                f = cols[m].get("f", {})
                for i, u in enumerate(units):
                    if kt.get(u) in maj["2023"]:
                        assert f.get(str(i), 0) & 4, (lvl, m, u)
                        assert cols[m]["v"][i] is None, (lvl, m, u)   # kept apart in 'm' (or did not stand)


@need_web
def test_series_carry_majority_flag():
    from pipeline.backbone.levels import membership
    mem = membership()
    kt = dict(zip(mem["bfs_nr"].astype(str), mem["kanton"]))
    maj = _majority()
    s = json.loads((WEB / "series" / "nrw_share_svp.json").read_text(encoding="utf-8"))
    for k, per in enumerate(s["periods"]):
        for lvl, kt_of in (("gemeinde", kt), ("kanton", None)):
            rows = s["levels"][lvl]
            for u in rows:
                c = u if kt_of is None else kt_of.get(u)
                if c in maj.get(per, []):
                    assert s["f"][lvl][u][str(k)] & 4, (lvl, u, per)
                    assert rows[u][k] is None
