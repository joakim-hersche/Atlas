"""STATENT – workplaces, jobs and FTE per municipality, 2011–latest.

Main series: BFS PxWeb px-x-0602010000_102 (municipality × sector × unit), all years published by
BFS on one municipality state (2131 municipalities). Geo codes are plain BFS numbers ('1', '261');
'99999' = Switzerland.

Branch detail: STATENT geodata (STAC ch.bfs.betriebszaehlungen, connector bfs_statent_geodata),
one file per year on that year's state with GDEHISTID -> mapped by hist_id. Data protection in
these files: every value below 4 is set to 4 (zeros stay zero); kept as delivered (rule 5).
The PxWeb cube instead suppresses small cells ('X' -> status 'suppressed').
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit, to_reference
from pipeline.sources.bfs_bevnat_bilanz.pxgeo import SUPPRESSED_SYMBOLS, query_status, to_obs
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
    return pd.concat([_sectors(report), _noga()], ignore_index=True)
