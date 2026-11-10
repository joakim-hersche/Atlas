"""UDEMO business demography per municipality, 2013–latest (BFS PxWeb px-x-0602030000_205).

Active enterprises, new enterprises (births), closures and their jobs, for the secondary and
tertiary sector (the primary sector is not covered). All years on one municipality state.
Small cells are shown as 'X' (JSON-stat status) -> status 'suppressed'. Sector totals are only
formed where both sectors are published; otherwise the total is 'suppressed' as well.
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
    return to_obs(v, "geo", "Jahr", {c: c for c in keep}, SOURCE, suppressed=s, report=report)
