"""Foreign cross-border commuters by municipality of work (Grenzgängerstatistik, GGS), 1996–latest.

BFS SDMX: CH1.GGS DF_GGS_2 1.1.0 (dims FREQ=Q, SEX, GDE_WORK; quarterly, end of quarter). Values
are BFS estimates (non-integer: register data with imputed/allocated place of work), hence precision
'modelled'. Annual value = mean of the four quarters (complete years only); the latest quarters are
flagged provisional (OBS_STATUS P) by BFS. Geo codes on the SNAP_2026 state.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import to_observations

SOURCE = "bfs_crossborder"
GEO = "GDE_WORK"


def annual() -> pd.DataFrame:
    d = data("CH1.GGS", "DF_GGS_2", "1.1.0", {"FREQ": "Q", "SEX": "_T"})
    d["year"] = d["TIME_PERIOD"].str[:4]
    g = d.groupby([GEO, "year"])
    out = pd.DataFrame({"xb_commuters": g["value"].mean(), "_n": g["value"].count(),
                        "_prov": g["OBS_STATUS"].agg(lambda s: (s == "P").any())}).reset_index()
    # complete years only (4 quarters published for Switzerland)
    full = out.loc[(out[GEO] == "8100") & (out["_n"] == 4), "year"]
    out = out[out["year"].isin(full)].copy()
    out.loc[out["_n"] < 4, "xb_commuters"] = np.nan
    return out.rename(columns={"year": "TIME_PERIOD"})


def observations() -> pd.DataFrame:
    w = annual()
    obs, _ = to_observations(w, GEO, "TIME_PERIOD", {"xb_commuters": "xb_commuters"}, SOURCE,
                             precision="modelled")
    prov_years = set(w.loc[w["_prov"], "TIME_PERIOD"])
    m = obs["period"].isin(prov_years) & (obs["status"] == "ok")
    obs.loc[m, "note"] = "includes quarters flagged provisional by BFS"
    return obs
