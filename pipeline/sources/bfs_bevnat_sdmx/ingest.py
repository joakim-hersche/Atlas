"""Marriages, divorces and live births per municipality, 1969–latest (BFS BEVNAT via SDMX).

Flows (CH1.BEVNAT, version 1.0.0): DF_BEVNAT_MARIAGES_2, DF_BEVNAT_DIVORCES_3,
DF_BEVNAT_NAISSANCES_1; totals only (all other dimensions '_T'). Geo codes on the SNAP_2025 state
(BFS re-maps the history back to 1969 onto that state). Counts 1–3 are suppressed by BFS
(OBS_STATUS Q) and delivered with status 'suppressed'.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_bevnat_sdmx"
AG, VER = "CH1.BEVNAT", "1.0.0"
FLOWS = {
    "bevnat_marriages": ("DF_BEVNAT_MARIAGES_2", {"GENDER_CONST": "_T", "P1_NAT_CAT": "_T", "P2_NAT_CAT": "_T", "FREQ": "A"}),
    "bevnat_divorces": ("DF_BEVNAT_DIVORCES_3", {"MAR_DUR": "_T", "P1_NAT_CAT": "_T", "P2_NAT_CAT": "_T", "FREQ": "A"}),
    "bevnat_births": ("DF_BEVNAT_NAISSANCES_1", {"SEX": "_T", "NAT_CAT": "_T", "P1_AGE_GRP": "_T", "FREQ": "A"}),
}
SUPPRESSED_NOTE = "suppressed by BFS (1 to 3 events)"


def wide() -> pd.DataFrame:
    out = None
    for col, (flow, sel) in FLOWS.items():
        d = data(AG, flow, VER, sel)
        w = pivot(d, "GEO", {col: {}})
        out = w if out is None else out.merge(w, on=["GEO", "TIME_PERIOD"], how="outer")
    for col in FLOWS:
        out[f"{col}__status"] = out[f"{col}__status"].fillna("no_data")
    return out


def observations() -> pd.DataFrame:
    obs, _ = to_observations(wide(), "GEO", "TIME_PERIOD", {c: c for c in FLOWS}, SOURCE)
    obs.loc[obs["status"] == "suppressed", "note"] = SUPPRESSED_NOTE
    return obs
