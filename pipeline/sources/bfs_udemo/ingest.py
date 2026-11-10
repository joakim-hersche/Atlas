"""UDEMO business demography per municipality, 2013–latest (BFS PxWeb px-x-0602030000_205).

Active enterprises, new enterprises (births), closures and their jobs, for the secondary and
tertiary sector (the primary sector is not covered). All years on one municipality state.
Small cells are shown as 'X' (JSON-stat status) -> status 'suppressed'. Sector totals are only
formed where both sectors are published; otherwise the total is 'suppressed' as well.

Published canton and Swiss values (audit round 2, M1; most small municipalities are suppressed, so
municipal sums are almost never complete): px-x-0602030000_204 (canton × sector × size class) and
px-x-0602030000_202 (Switzerland, NOGA division × size class), summed over the size classes (and
divisions), as level 'kanton' / 'schweiz' rows with provenance native. A sum with a suppressed
cell is left out.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import SUPPRESSED_SYMBOLS, query_status, to_obs
from pipeline.sources.bfs_pxweb.fetch import metadata

SOURCE = "bfs_udemo"
DB = "px-x-0602030000_205"
UNIT, SECTOR = "Beobachtungseinheit", "Wirtschaftssektor"
UNITS = {"1": "active", "2": "births", "3": "closures", "4": "jobs_active", "5": "jobs_births",
         "6": "jobs_closures"}
SECTORS = {"2": "_s2", "3": "_s3"}
DB_CANTON, DB_CH = "px-x-0602030000_204", "px-x-0602030000_202"


def _published() -> pd.DataFrame:
    """Canton (cube 204) and Swiss (cube 202) values, summed over size classes / divisions."""
    from pipeline.common import interim_path
    from pipeline.harmonize.helpers import emit
    from pipeline.sources.bfs_bevnat_bilanz.pxgeo import query_status_split
    kt = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    abbr = {f"{int(i):02d}": k for i, k in zip(kt["canton_id"], kt["canton"])}
    c = query_status_split(DB_CANTON, {UNIT: "*", "Kanton": "*", SECTOR: "*", "Grössenklasse": "*", "Jahr": "*"})
    c["unit"], c["level"] = c["Kanton"].map(abbr), "kanton"
    n = query_status_split(DB_CH, {UNIT: "*", "Wirtschaftsabteilung": "*", "Grössenklasse": "*", "Jahr": "*"})
    div = n["Wirtschaftsabteilung"].astype(int)
    n[SECTOR] = (div >= 45).map({True: "3", False: "2"})
    n["unit"], n["level"] = "CH", "schweiz"
    x = pd.concat([c, n], ignore_index=True)
    x["bad"] = x["value"].isna()
    g = x.groupby(["level", "unit", "Jahr", UNIT, SECTOR]).agg(value=("value", "sum"), bad=("bad", "any")).reset_index()
    g.loc[g["bad"], "value"] = float("nan")
    t = g.groupby(["level", "unit", "Jahr", UNIT]).agg(value=("value", lambda v: v.sum(min_count=2)),
                                                       bad=("bad", "any")).reset_index()
    t.loc[t["bad"], "value"] = float("nan")
    g["metric"] = "udemo_" + g[UNIT].map(UNITS) + g[SECTOR].map(SECTORS)
    t["metric"] = "udemo_" + t[UNIT].map(UNITS)
    keep = {f"udemo_{v}" for v in UNITS.values()} | {"udemo_active_s2", "udemo_active_s3", "udemo_births_s2", "udemo_births_s3"}
    a = pd.concat([g, t], ignore_index=True)
    a = a[a["metric"].isin(keep)]
    outs = []
    for lvl, gl in a.groupby("level"):
        w = gl.pivot_table(index=["unit", "Jahr"], columns="metric", values="value", aggfunc="first", dropna=False).reset_index()
        outs.append(emit(w, {m: m for m in sorted(keep) if m in w}, "Jahr", SOURCE, level=lvl, unit_col="unit",
                         precision="exact", provenance="native"))
    out = pd.concat(outs, ignore_index=True)
    out["note"] = "published value (BFS UDEMO, px-x-0602030000_204 / _202, summed over size classes)"
    out = out[out["status"] == "ok"]
    # Switzerland where cube 202 has a suppressed cell: the sum of the 26 published canton values
    kt_ok = out[out["level"] == "kanton"].groupby(["metric_id", "period"]).agg(n=("value", "size"), v=("value", "sum")).reset_index()
    kt_ok = kt_ok[kt_ok["n"] == len(abbr)]
    have = set(zip(out.loc[out["level"] == "schweiz", "metric_id"], out.loc[out["level"] == "schweiz", "period"]))
    add = kt_ok[[(m, p) not in have for m, p in zip(kt_ok["metric_id"], kt_ok["period"])]]
    if len(add):
        ch = out[out["level"] == "kanton"].head(len(add)).copy().reset_index(drop=True)
        ch["unit_id"], ch["level"] = "CH", "schweiz"
        ch["metric_id"], ch["period"], ch["value"] = add["metric_id"].values, add["period"].values, add["v"].values
        ch["note"] = "sum of the 26 published canton values (BFS UDEMO, px-x-0602030000_204)"
        out = pd.concat([out, ch], ignore_index=True)
    return out


def _fetch() -> pd.DataFrame:
    years = next(v for v in metadata(DB)["variables"] if v["code"] == "Jahr")["values"]
    parts = [query_status(DB, {UNIT: "*", "Gemeinde": "*", SECTOR: "*", "Jahr": years[i:i + 3]})
             for i in range(0, len(years), 3)]
    return pd.concat(parts, ignore_index=True)


def observations(report: dict | None = None) -> pd.DataFrame:
    df = _fetch()
    df["sup"] = df["status"].isin(SUPPRESSED_SYMBOLS) & df["value"].isna()
    df["geo"] = df["Gemeinde"].map(lambda c: f"{int(c):04d}")
    idx = ["geo", "Jahr"]
    val = df.pivot_table(index=idx, columns=[UNIT, SECTOR], values="value", aggfunc="first", dropna=False)
    sup = df.pivot_table(index=idx, columns=[UNIT, SECTOR], values="sup", aggfunc="first", dropna=False)
    v, s = pd.DataFrame(index=val.index), pd.DataFrame(index=val.index)
    for u, name in UNITS.items():
        for sc, suf in SECTORS.items():
            v[f"udemo_{name}{suf}"] = val[(u, sc)]
            s[f"udemo_{name}{suf}"] = sup[(u, sc)].astype(bool)
        v[f"udemo_{name}"] = val[(u, "2")] + val[(u, "3")]
        s[f"udemo_{name}"] = s[f"udemo_{name}_s2"] | s[f"udemo_{name}_s3"]
    keep = [f"udemo_{n}" for n in UNITS.values()] + ["udemo_active_s2", "udemo_active_s3",
                                                    "udemo_births_s2", "udemo_births_s3"]
    v, s = v[keep].reset_index(), s[keep].reset_index()
    obs = to_obs(v, "geo", "Jahr", {c: c for c in keep}, SOURCE, suppressed=s, report=report)
    pub = _published()
    # the municipal cube's own higher-level rows (if any) give way to the published tables
    obs = obs[~(obs["level"].isin(["kanton", "schweiz"]) & obs["provenance"].eq("native"))]
    return pd.concat([obs, pub], ignore_index=True)
