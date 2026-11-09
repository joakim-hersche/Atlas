"""Demographic balance per municipality, 1981–latest (BFS PxWeb px-x-0102020000_201).

Components of population change (ESPOP to 2010, STATPOP/BEVNAT from 2011), published by BFS on
the latest municipality state. Geo value codes are running indices; BFS numbers are parsed from
the labels (pxgeo.geo_codes).

Three Thurgau units of the 1990s municipal reform (cube codes 4505 Neukirch an der Thur,
4670 Illighausen, 4695 Scherzingen) could not be assigned to one current municipality by BFS.
The cube lists them with their values up to their abolition and zeros afterwards; their values are
needed for the TG and CH totals to add up. They are mapped to the register versions of the same
name (hist_id 12510, 11544, 13036) and reprojected with the crosswalk weights (successor rows
become 'boundary_estimate' for those years); the zero rows after abolition are dropped.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import geo_codes, to_obs
from pipeline.sources.bfs_pxweb.fetch import query_codes

SOURCE = "bfs_bevnat_bilanz"
DB = "px-x-0102020000_201"
G = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"
NAT, SEX, COMP = "Staatsangehörigkeit (Kategorie)", "Geschlecht", "Demografische Komponente"
LEGACY = {4505: 12510, 4670: 11544, 4695: 13036}

COMPONENTS = {  # component code -> metric id (nationality total)
    "0": "bil_pop_jan",
    "1": "bil_births",
    "2": "bil_deaths",
    "3": "bil_natural_balance",
    "4": "bil_immigration",
    "5": "bil_intercant_in",
    "6": "bil_intracant_in",
    "7": "bil_emigration",
    "8": "bil_intercant_out",
    "9": "bil_intracant_out",
    "10": "bil_net_migration",
    "16": "bil_pop_dec",
}


def wide() -> pd.DataFrame:
    codes, _, _ = geo_codes(DB, G)
    tot = query_codes(DB, {"Jahr": "*", G: "*", NAT: ["0"], SEX: ["0"], COMP: "*"})
    w = tot[tot[COMP].isin(COMPONENTS)].pivot_table(index=[G, "Jahr"], columns=COMP, values="value",
                                                     aggfunc="first")
    w = w.rename(columns=COMPONENTS)
    nat = query_codes(DB, {"Jahr": "*", G: "*", NAT: ["1", "2"], SEX: ["0"], COMP: ["0", "12"]})
    fj = nat[(nat[NAT] == "2") & (nat[COMP] == "0")].set_index([G, "Jahr"])["value"]
    nz = nat[(nat[NAT] == "1") & (nat[COMP] == "12")].set_index([G, "Jahr"])["value"]
    w["bil_pop_foreign_jan"] = fj
    w["bil_naturalisations"] = nz
    # net international / intercantonal migration as counts (sum-aggregatable)
    w["bil_net_international"] = w["bil_immigration"] - w["bil_emigration"]
    w["bil_net_intercant"] = w["bil_intercant_in"] - w["bil_intercant_out"]
    w = w.reset_index()
    w["geo"] = w[G].map(codes)
    return w


def observations(report: dict | None = None) -> pd.DataFrame:
    w = wide()
    cols = [c for c in w.columns if c.startswith("bil_")]
    return to_obs(w, "geo", "Jahr", {c: c for c in cols}, SOURCE, legacy_hist=LEGACY, report=report)
