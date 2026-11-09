"""STATPOP – resident population by municipality, 2010–latest (BFS PxWeb, current state).

Cubes: px-x-0102010000_101 (type, nationality, sex, single-year age)
       px-x-0102010000_103 (type, sex, marital status, 5-year age class)
BFS publishes these on the latest municipality state (decision D14: prefer BFS's re-projection);
the remaining step to the reference state is merger-only.
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.pxweb import GEO, to_observations, wide_by_geo
from pipeline.sources.bfs_pxweb.fetch import query_codes

SOURCE = "bfs_statpop"
T = "-99999"  # PxWeb code for "Total"


def _population() -> pd.DataFrame:
    df = query_codes("px-x-0102010000_101", {"Jahr": "*", GEO: "*", "Bevölkerungstyp": "*",
                                             "Staatsangehörigkeit (Kategorie)": "*", "Geschlecht": "*"})
    perm = {"Bevölkerungstyp": "1", "Alter": T}
    return wide_by_geo(df, GEO, "Jahr", {
        "pop_total": {**perm, "Staatsangehörigkeit (Kategorie)": T, "Geschlecht": T},
        "pop_male": {**perm, "Staatsangehörigkeit (Kategorie)": T, "Geschlecht": "1"},
        "pop_female": {**perm, "Staatsangehörigkeit (Kategorie)": T, "Geschlecht": "2"},
        "pop_swiss": {**perm, "Staatsangehörigkeit (Kategorie)": "1", "Geschlecht": T},
        "pop_foreign": {**perm, "Staatsangehörigkeit (Kategorie)": "2", "Geschlecht": T},
        "pop_nonpermanent": {"Bevölkerungstyp": "2", "Alter": T, "Staatsangehörigkeit (Kategorie)": T,
                             "Geschlecht": T},
    })


AGE_GROUPS = {  # metric column -> 5-year class lower bounds in cube _103 (codes are lower bounds)
    "pop_age_0_19": ["0", "5", "10", "15"],
    "pop_age_20_64": [str(a) for a in range(20, 65, 5)],
    "pop_age_65_79": ["65", "70", "75"],
    "pop_age_80plus": ["80", "85", "90", "95", "100"],
}
CIVIL = {"pop_single": "1", "pop_married": "2", "pop_widowed": "3", "pop_divorced": "4"}


def _age_civil() -> pd.DataFrame:
    meta_ages = [a for codes in AGE_GROUPS.values() for a in codes]
    ages = query_codes("px-x-0102010000_103", {"Jahr": "*", GEO: "*", "Bevölkerungstyp": ["1"],
                                               "Geschlecht": [T], "Zivilstand": [T], "Altersklasse": meta_ages})
    out = None
    for col, codes in AGE_GROUPS.items():
        s = (ages[ages["Altersklasse"].isin(codes)].groupby([GEO, "Jahr"])["value"].sum(min_count=len(codes))
             .rename(col).reset_index())
        out = s if out is None else out.merge(s, on=[GEO, "Jahr"], how="outer")
    civ = query_codes("px-x-0102010000_103", {"Jahr": "*", GEO: "*", "Bevölkerungstyp": ["1"],
                                              "Geschlecht": [T], "Zivilstand": list(CIVIL.values()),
                                              "Altersklasse": [T]})
    w = wide_by_geo(civ, GEO, "Jahr", {k: {"Zivilstand": v} for k, v in CIVIL.items()})
    return out.merge(w, on=[GEO, "Jahr"], how="outer")


def observations() -> pd.DataFrame:
    wide = _population().merge(_age_civil(), on=[GEO, "Jahr"], how="outer")
    metric_map = {c: c for c in wide.columns if c not in (GEO, "Jahr")}
    return to_observations(wide, GEO, "Jahr", metric_map, SOURCE)
