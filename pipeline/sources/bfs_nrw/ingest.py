"""National Council elections 1971–2023 by municipality (BFS PxWeb cubes 105, 104, 101).

Party strength cannot be summed or averaged across municipalities of different cantons: party
votes (Parteistimmen) are list votes, and each voter has as many as the canton has seats. BFS
makes party results additive with 'fiktive Wählende' (fictitious voters = party votes scaled by a
canton-and-election constant). Cube 104 publishes them for CH and cantons only; per canton and
election the ratio fiktive Wählende / Parteistimmen is the same for every party (checked: spread
< 0.6 %, i.e. rounding). We therefore deliver per municipality

    nrw_fw_<party> = Parteistimmen(municipality, party) × ΣFW(canton) / ΣPS(canton)

using the canton the municipality belonged to AT THE ELECTION (Jura municipalities voted in Bern
until 1975, Laufental in Bern until 1991, ...), and party share as the derived ratio
nrw_fw_<party> / nrw_fw_total. Within a municipality the share equals BFS's published party
strength (checked: max deviation 0.2 pp, all from rounding of 1971 published percentages).

Parties are kept as published (25 BFS party codes). CVP and BDP merged into Die Mitte in 2021:
up to 2019 they are nrw_fw_cvp / nrw_fw_bdp, from 2023 nrw_fw_mitte. LPS merged into FDP in 2009.
A party code without a value ('...') means the party did not stand: status not_applicable.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.backbone.vintage import crosswalk
from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.pxweb import GEO, to_observations
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_nrw.fetch import GEO105, TURNOUT, canton_parties, party_votes, turnout

SOURCE = "bfs_nrw"
CUBE_STATE = dt.date(2023, 1, 1)  # municipality state of cubes 101 and 105
PARTY_SLUG = {"1": "fdp", "34": "mitte", "3": "sp", "4": "svp", "5": "lps", "7": "evp", "8": "csp",
              "31": "glp", "9": "pda", "27": "sol", "12": "fga", "13": "gruene", "15": "sd",
              "16": "edu", "18": "lega", "33": "mcr", "2": "cvp", "32": "bdp", "6": "ldu",
              "11": "poch", "14": "rep", "10": "psa", "17": "fps", "26": "sep", "35": "other"}
PSEUDO = r"9\d{3}"
PSEUDO_NOTE = "pseudo-unit (Swiss abroad / postal voting / other), not a municipality"


def _canton_codes() -> dict[int, str]:
    ct = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    return dict(zip(ct["canton_id"].astype(int), ct["canton"]))


def canton_at_election(year: int) -> pd.Series:
    """bfs_nr on the cube state (2023-01-01) -> canton its territory belonged to at the election."""
    mv, _ = load_backbone()
    at = versions_at(mv, dt.date(year, 10, 1))[["hist_id", "canton"]].astype({"hist_id": "int64"})
    cw = crosswalk(CUBE_STATE)[["from_hist_id", "to_bfs_nr", "weight"]]
    m = at.merge(cw, left_on="hist_id", right_on="from_hist_id")
    m = m.groupby(["to_bfs_nr", "canton"])["weight"].sum().reset_index()
    m = m.sort_values("weight").drop_duplicates("to_bfs_nr", keep="last")
    return m.set_index(m["to_bfs_nr"].astype(int))["canton"]


def fw_factor() -> pd.Series:
    """(canton, year) -> fiktive Wählende per party vote, from cube 104."""
    k = canton_parties()
    w = k.pivot_table(index=["Kanton", "Jahr", "Partei"], columns="Ergebnisse", values="value").reset_index()
    w = w[w["1"].notna() & w["2"].notna() & (w["1"] > 0)]
    t = w.groupby(["Kanton", "Jahr"])[["1", "2"]].sum()
    return (t["2"] / t["1"]).rename("factor")


def _party_wide() -> pd.DataFrame:
    d = party_votes()
    d = d[d["Ergebnisse"] == "1"]
    d = d[d[GEO105].str.fullmatch(r"\d{4}")]  # municipalities and pseudo-units; districts dropped
    cid = _canton_codes()
    parts = []
    for year, g in d.groupby("Jahr"):
        cant = canton_at_election(int(year))
        code = g[GEO105].astype(int)
        g = g.assign(kt=np.where(code >= 9000, code.map(lambda c: cid.get(c // 10 % 100)), code.map(cant)))
        parts.append(g)
    d = pd.concat(parts)
    if d["kt"].isna().any():
        raise ValueError(f"no canton at election for {d.loc[d['kt'].isna(), GEO105].unique()[:10]}")
    # strict sums when reprojecting (to_vintage): where a party stood in the canton and the
    # municipality has results, a missing party value means zero votes (15 cells, 1971-1979)
    mun = d[GEO105].astype(int) < 9000
    stood = d.groupby(["kt", "Jahr", "Partei"])["value"].transform(lambda x: x.notna().any())
    has_res = d.groupby([GEO105, "Jahr"])["value"].transform(lambda x: x.notna().any())
    fill = mun & stood & has_res & d["value"].isna()
    d.loc[fill, "value"] = 0.0
    f = fw_factor()
    d = d.merge(f.reset_index().rename(columns={"Kanton": "kt"}), on=["kt", "Jahr"], how="left")
    d["fw"] = d["value"] * d["factor"]
    d["col"] = "nrw_fw_" + d["Partei"].map(PARTY_SLUG)
    w = d.pivot_table(index=[GEO105, "Jahr"], columns="col", values="fw", aggfunc="first", dropna=False)
    w = w.reindex(columns=sorted(set(d["col"])))
    w["nrw_fw_total"] = w.sum(axis=1, min_count=1)
    w.columns.name = None
    return w.reset_index().rename(columns={GEO105: GEO})


def _status_party(obs: pd.DataFrame) -> pd.DataFrame:
    """Party value missing while the unit has election results -> the party did not stand."""
    tot = obs[(obs["metric_id"] == "nrw_fw_total") & (obs["status"] == "ok")]
    has = set(zip(tot["level"], tot["unit_id"], tot["period"]))
    party = obs["metric_id"].str.startswith("nrw_fw_") & (obs["status"] == "no_data")
    key = pd.Series(list(zip(obs["level"], obs["unit_id"], obs["period"])), index=obs.index)
    na = party & key.isin(has)
    obs.loc[na, "status"] = "not_applicable"
    obs.loc[na, "note"] = "party did not stand (BFS '...')"
    return obs


NO_RESULT = ("no result published for this municipality and election (counted with another "
             "municipality, tacit election, or canton did not exist)")


def _pseudo(wide: pd.DataFrame, metric_map: dict[str, str]) -> pd.DataFrame:
    p = wide[wide[GEO].str.fullmatch(PSEUDO)]
    rows = emit(p, metric_map, "Jahr", SOURCE, level="pseudo", unit_col=GEO, vintage=REFERENCE_DATE,
                precision="exact", provenance="native")
    rows = rows[rows["status"] == "ok"].copy()
    rows["note"] = PSEUDO_NOTE
    return rows


def _national(wide: pd.DataFrame, metric_map: dict[str, str]) -> pd.DataFrame:
    ch = wide[wide[GEO] == "CH"].assign(unit="CH")  # cube codes Switzerland 'CH', not 8100
    return emit(ch, metric_map, "Jahr", SOURCE, level="schweiz", unit_col="unit", precision="exact",
                provenance="native", vintage=CUBE_STATE)


def _parties() -> pd.DataFrame:
    wide = _party_wide()
    cols = [c for c in wide.columns if c.startswith("nrw_fw_")]
    mm = {c: c for c in cols}
    mun = wide[~wide[GEO].str.fullmatch(PSEUDO)]
    obs = to_observations(mun, GEO, "Jahr", mm, SOURCE, published_on_current_state=False)
    # published canton and national fiktive Wählende (cube 104)
    k = canton_parties()
    k = k[k["Ergebnisse"] == "2"].assign(col=lambda x: "nrw_fw_" + x["Partei"].map(PARTY_SLUG))
    kw = k.pivot_table(index=["Kanton", "Jahr"], columns="col", values="value", dropna=False)
    kw["nrw_fw_total"] = kw.sum(axis=1, min_count=1)
    kw.columns.name = None
    kw = kw.reset_index()
    nat = []
    for level, sub in (("schweiz", kw[kw["Kanton"] == "CH"]), ("kanton", kw[kw["Kanton"] != "CH"])):
        nat.append(emit(sub.assign(unit=sub["Kanton"]), {c: c for c in cols if c in sub}, "Jahr", SOURCE,
                        level=level, unit_col="unit", precision="exact", provenance="native",
                        vintage=CUBE_STATE))
    obs = pd.concat([obs, *nat, _pseudo(wide, mm)], ignore_index=True)
    return _status_party(obs)


def _turnout() -> pd.DataFrame:
    t = turnout()
    t["col"] = "nrw_" + t["Ergebnisse"].map(TURNOUT)
    w = t.pivot_table(index=[GEO, "Jahr"], columns="col", values="value", dropna=False)
    w.columns.name = None
    w = w.reset_index()
    mm = {c: c for c in w.columns if c.startswith("nrw_")}
    mun = w[~w[GEO].str.fullmatch(PSEUDO) & (w[GEO] != "CH")]
    obs = to_observations(mun, GEO, "Jahr", mm, SOURCE, published_on_current_state=False)
    return pd.concat([obs, _national(w, mm), _pseudo(w, mm)], ignore_index=True)


POOLED = ("counted with another municipality in the BFS results (its votes are included there); "
          "no separate result")


def _pooled(obs: pd.DataFrame) -> pd.DataFrame:
    """Municipalities without a result although others in the same canton have one for that election.

    BFS counts some very small municipalities together with a neighbour (e.g. Meienried, Hellsau BE in
    2023), so their votes are inside the neighbour's figures. They get status not_published (and
    metrics.yaml `zero_when`), so sums and party shares of districts and cantons stay complete. A
    canton with no municipal results at all (tacit election, canton did not exist) stays no_data.
    """
    gem = (obs["level"] == "gemeinde")
    cand = gem & (obs["status"] == "no_data")
    if not cand.any():
        return obs
    years = sorted(obs.loc[cand, "period"].unique())
    kt = pd.concat([canton_at_election(int(y)).rename("kt").to_frame().assign(period=y) for y in years])
    kt.index = kt.index.astype(str)
    kt = kt.rename_axis("unit_id").reset_index()
    g = obs.loc[gem, ["unit_id", "metric_id", "period", "status"]].merge(kt, on=["unit_id", "period"], how="left")
    has = g[g["status"] == "ok"].groupby(["kt", "metric_id", "period"]).size().rename("n_ok").reset_index()
    c = obs.loc[cand, ["unit_id", "metric_id", "period"]].reset_index().merge(kt, on=["unit_id", "period"], how="left")
    c = c.merge(has, on=["kt", "metric_id", "period"], how="left")
    idx = c.loc[c["n_ok"].fillna(0) > 0, "index"]
    obs.loc[idx, "status"] = "not_published"
    obs.loc[idx, "note"] = POOLED
    return obs


def observations() -> pd.DataFrame:
    obs = pd.concat([_parties(), _turnout()], ignore_index=True)
    obs = _pooled(obs)
    obs.loc[(obs["status"] == "no_data") & obs["note"].isna(), "note"] = NO_RESULT
    return obs[OBS_COLUMNS]
