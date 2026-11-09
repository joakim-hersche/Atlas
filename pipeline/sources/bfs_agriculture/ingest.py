"""Agricultural structure survey per municipality (BFS PxWeb px-x-0702000000_104, STRU):
farms, agricultural workers, utilised agricultural area and livestock, 1975, 1980, 1985, 1990 and
1996–latest. Farms are counted at the municipality of the farm seat (land may lie elsewhere).
All years are published by BFS on the latest municipality state. Geo value codes are running
indices (BFS numbers parsed from the labels); 'Jahr' codes are indices too (0 = latest year).
Livestock is given in head counts (no livestock units in this cube).
Cell symbols: '( )' = suppressed (data protection) -> status 'suppressed'; '...' = not available.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import SUPPRESSED_SYMBOLS, geo_codes, query_status_split, to_obs
from pipeline.sources.bfs_pxweb.fetch import metadata

SOURCE = "bfs_agriculture"
DB = "px-x-0702000000_104"
G = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"
UNIT, SYS = "Beobachtungseinheit", "Betriebssystem"
TOTAL_UNITS = {
    "0": "agr_farms",
    "1": "agr_workers",
    "2": "agr_workers_fulltime",
    "6": "agr_workers_women",
    "9": "agr_workers_family",
    "10": "agr_area_ha",
    "11": "agr_area_arable_ha",
    "12": "agr_area_grassland_ha",
    "13": "agr_area_permanent_crops_ha",
    "15": "agr_cattle",
    "16": "agr_horses",
    "17": "agr_sheep",
    "18": "agr_goats",
    "19": "agr_pigs",
    "20": "agr_poultry",
}
ORGANIC_UNITS = {"0": "agr_farms_organic", "10": "agr_area_organic_ha"}


def observations(report: dict | None = None) -> pd.DataFrame:
    codes, _, _ = geo_codes(DB, G)
    jv = next(v for v in metadata(DB)["variables"] if v["code"] == "Jahr")
    year = dict(zip(jv["values"], jv["valueTexts"]))
    a = query_status_split(DB, {UNIT: list(TOTAL_UNITS), G: "*", SYS: ["0"], "Jahr": "*"})
    a["metric"] = a[UNIT].map(TOTAL_UNITS)
    b = query_status_split(DB, {UNIT: list(ORGANIC_UNITS), G: "*", SYS: ["1"], "Jahr": "*"})
    b["metric"] = b[UNIT].map(ORGANIC_UNITS)
    df = pd.concat([a, b], ignore_index=True)
    df["year"] = df["Jahr"].map(year)
    df["geo"] = df[G].map(codes)
    df["sup"] = df["status"].isin(SUPPRESSED_SYMBOLS) & df["value"].isna()
    cols = [*TOTAL_UNITS.values(), *ORGANIC_UNITS.values()]
    w = df.pivot_table(index=["geo", "year"], columns="metric", values="value", aggfunc="first", dropna=False)
    s = df.pivot_table(index=["geo", "year"], columns="metric", values="sup", aggfunc="first", dropna=False)
    w, s = w[cols].reset_index(), s[cols].astype(bool).reset_index()
    return to_obs(w, "geo", "year", {c: c for c in cols}, SOURCE, suppressed=s, report=report)
