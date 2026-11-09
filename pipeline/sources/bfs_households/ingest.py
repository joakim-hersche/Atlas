"""Private households by size and persons in private households, per municipality, 2012–latest.

BFS SDMX: CH1.STATPOP DF_STATPOP_PHH 1.1.0 (households by size; '_M' = mean size, not used: the
mean is recomputed as persons / households) and DF_STATPOP_PERSPHH 1.1.0 (persons in private
households, totals over sex and age). Geo codes on the SNAP_2025 state (history re-mapped by BFS).
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_households"
AG = "CH1.STATPOP"
SIZES = {"hh_size1": "1", "hh_size2": "2", "hh_size3": "3", "hh_size4": "4", "hh_size5": "5", "hh_size6plus": "60"}


def wide() -> pd.DataFrame:
    hh = data(AG, "DF_STATPOP_PHH", "1.1.0", {"FREQ": "A"})
    w = pivot(hh, "GEO_UNIT", {"hh_total": {"HH_SIZE": "_T"}, **{k: {"HH_SIZE": v} for k, v in SIZES.items()}})
    ps = data(AG, "DF_STATPOP_PERSPHH", "1.1.0", {"SEX": "_T", "AGE_GROUP": "_T", "HH_SIZE": "_T", "FREQ": "A"})
    w2 = pivot(ps, "GEO_UNIT", {"hh_persons": {"HH_SIZE": "_T"}})
    return w.merge(w2, on=["GEO_UNIT", "TIME_PERIOD"], how="outer")


def observations() -> pd.DataFrame:
    w = wide()
    cols = ["hh_total", *SIZES, "hh_persons"]
    for c in cols:
        w[f"{c}__status"] = w[f"{c}__status"].fillna("no_data")
    obs, _ = to_observations(w, "GEO_UNIT", "TIME_PERIOD", {c: c for c in cols}, SOURCE)
    return obs
