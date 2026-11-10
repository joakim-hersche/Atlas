"""STATENT – workplaces, jobs and FTE per municipality, 2011–latest.

Main series: BFS PxWeb px-x-0602010000_102 (municipality × sector × unit), all years published by
BFS on one municipality state (2131 municipalities). Geo codes are plain BFS numbers ('1', '261');
'99999' = Switzerland.

Branch detail: STATENT geodata (STAC ch.bfs.betriebszaehlungen, connector bfs_statent_geodata),
one file per year on that year's state with GDEHISTID -> mapped by hist_id. Data protection in
these files: every value below 4 is set to 4 (zeros stay zero); kept as delivered (rule 5).
The PxWeb cube instead suppresses small cells ('X' -> status 'suppressed').

Published canton totals (audit round 2, M1): px-x-0602010000_101 (canton × NOGA division × unit), as
level 'kanton' rows (provenance native) for the totals and the three sectors (sector 1 = divisions
01–03, 2 = 05–43, 3 = 45–96). They are the published fallback where one small municipality is
suppressed in the municipal cube (e.g. 2024: 5315 blanks TI) and feed the plausibility sweep.
The Swiss total comes from the municipal cube (geo code 99999).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit, to_reference
from pipeline.sources.bfs_bevnat_bilanz.pxgeo import SUPPRESSED_SYMBOLS, query_status, query_status_split, to_obs
from pipeline.sources.bfs_pxweb.fetch import metadata
from pipeline.sources.bfs_statent_geodata.fetch import FIRST_YEAR, LAST_YEAR, municipalities

SOURCE = "bfs_statent"
DB = "px-x-0602010000_102"
SECTOR, UNIT = "Wirtschaftssektor", "Beobachtungseinheit"
UNITS = {"1": "workplaces", "2": "jobs", "3": "jobs_women", "5": "fte"}
SECTORS = {"999": "", "1": "_s1", "2": "_s2", "3": "_s3"}
KEEP = {"ent_workplaces", "ent_jobs", "ent_jobs_women", "ent_fte", "ent_workplaces_s1", "ent_workplaces_s2",
        "ent_workplaces_s3", "ent_jobs_s1", "ent_jobs_s2", "ent_jobs_s3", "ent_fte_s1", "ent_fte_s2", "ent_fte_s3"}

# NOGA 2008 divisions (geodata columns B08<div>EMP = jobs)
NOGA = {
    "ent_jobs_retail": ["47"],
    "ent_jobs_accommodation": ["55"],
    "ent_jobs_food_service": ["56"],
    "ent_jobs_ict": ["62", "63"],
    "ent_jobs_finance": ["64", "65", "66"],
    "ent_jobs_education": ["85"],
    "ent_jobs_health": ["86"],
    "ent_jobs_care_social": ["87", "88"],
}


DB_CANTON = "px-x-0602010000_101"
SECTOR_DIVS = {"_s1": range(1, 4), "_s2": range(5, 44), "_s3": range(45, 100)}


def _cantons() -> pd.DataFrame:
    """Published canton totals and sector sums (cube 101); a sector is suppressed if any division is."""
    from pipeline.common import interim_path
    kt = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    abbr = dict(zip(kt["canton_id"].astype(int).astype(str), kt["canton"]))
    df = query_status_split(DB_CANTON, {"Jahr": "*", "Kanton": sorted(abbr, key=int), "Wirtschaftsabteilung": "*",
                                        UNIT: list(UNITS)})
    df["sup"] = df["status"].isin(SUPPRESSED_SYMBOLS) & df["value"].isna()
    div = df["Wirtschaftsabteilung"].astype(int)
    parts = [df[div == 999].assign(sfx="")]
    for sfx, rng in SECTOR_DIVS.items():
        parts.append(df[div.isin(list(rng))].assign(sfx=sfx))
    x = pd.concat(parts, ignore_index=True)
    g = x.groupby(["Kanton", "Jahr", UNIT, "sfx"]).agg(value=("value", lambda v: v.sum(min_count=1)),
                                                     sup=("sup", "any"), n_nan=("value", lambda v: int(v.isna().sum())))
    g = g.reset_index()
    g.loc[g["sup"] | (g["n_nan"] > 0), "value"] = float("nan")
    g["metric"] = "ent_" + g[UNIT].map(UNITS) + g["sfx"]
    g = g[g["metric"].isin(KEEP)]
    g["unit"] = g["Kanton"].map(abbr)
    w = g.pivot_table(index=["unit", "Jahr"], columns="metric", values="value", aggfunc="first", dropna=False).reset_index()
    out = emit(w, {c: c for c in sorted(KEEP) if c in w}, "Jahr", SOURCE, level="kanton", unit_col="unit",
               precision="exact", provenance="native")
    sup = g.set_index(["unit", "Jahr", "metric"])["sup"]
    key = list(zip(out["unit_id"], out["period"], out["metric_id"]))
    is_sup = pd.Series([bool(sup.get(k, False)) for k in key], index=out.index)
    out.loc[is_sup, "status"] = "suppressed"
    out["note"] = "published canton total (BFS STATENT, px-x-0602010000_101)"
    return out[out["status"] == "ok"]


def _geo(code: str) -> str:
    return "8100" if code == "99999" else f"{int(code):04d}"


def _sectors(report: dict | None) -> pd.DataFrame:
    years = next(v for v in metadata(DB)["variables"] if v["code"] == "Jahr")["values"]
    df = pd.concat([query_status(DB, {"Jahr": years[i:i + 2], "Gemeinde": "*", SECTOR: "*", UNIT: list(UNITS)})
                    for i in range(0, len(years), 2)], ignore_index=True)
    df["metric"] = "ent_" + df[UNIT].map(UNITS) + df[SECTOR].map(SECTORS)
    df = df[df["metric"].isin(KEEP)]
    df["sup"] = df["status"].isin(SUPPRESSED_SYMBOLS) & df["value"].isna()
    df["geo"] = df["Gemeinde"].map(_geo)
    w = df.pivot_table(index=["geo", "Jahr"], columns="metric", values="value", aggfunc="first", dropna=False)
    s = df.pivot_table(index=["geo", "Jahr"], columns="metric", values="sup", aggfunc="first", dropna=False)
    cols = sorted(KEEP)
    w, s = w[cols].reset_index(), s[cols].astype(bool).reset_index()
    return to_obs(w, "geo", "Jahr", {c: c for c in cols}, SOURCE, suppressed=s, report=report)


def _noga() -> pd.DataFrame:
    parts = []
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        d = pd.read_parquet(municipalities(y))
        hid = "GDEHISTID" if "GDEHISTID" in d else "GDE_HISTID"
        row = pd.DataFrame({"hist_id": d[hid].astype("int64"), "Jahr": str(y)})
        for m, divs in NOGA.items():
            row[m] = d[[f"B08{x}EMP" for x in divs]].sum(axis=1, min_count=len(divs))
        parts.append(row)
    df = pd.concat(parts, ignore_index=True)
    cols = list(NOGA)
    ref, _ = to_reference(df, None, cols, ["Jahr"], rule="sum")
    return emit(ref, {c: c for c in cols}, "Jahr", SOURCE)


def observations(report: dict | None = None) -> pd.DataFrame:
    return pd.concat([_sectors(report), _noga(), _cantons()], ignore_index=True)
