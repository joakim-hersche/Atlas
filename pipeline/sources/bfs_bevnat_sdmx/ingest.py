"""Marriages, divorces and live births per municipality, 1969–latest (BFS BEVNAT via SDMX).

Flows (CH1.BEVNAT, version 1.0.0): DF_BEVNAT_MARIAGES_2, DF_BEVNAT_DIVORCES_3,
DF_BEVNAT_NAISSANCES_1; totals only (all other dimensions '_T'). Geo codes on the SNAP_2025 state
(BFS re-maps the history back to 1969 onto that state). Counts 1–3 are suppressed by BFS
(OBS_STATUS Q) and delivered with status 'suppressed'.

Births from 1981 (audit round 2, M6): where BEVNAT suppresses a municipality's births (1–3 events),
the count is taken from the BFS demographic balance (connector bfs_bevnat_bilanz, cube
px-x-0102020000_201), which publishes every municipality from 1981 and is identical wherever both
publish (84,308 municipality-years compared; differences only in 1981/82 territory and reprojected
splits). The note names the source of each filled value.
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


BILANZ_NOTE = "from the BFS demographic balance (px-x-0102020000_201); BEVNAT suppresses 1 to 3 births"


def _bilanz_births() -> pd.DataFrame:
    """Municipal births of the demographic balance (its connector's output, or the connector itself)."""
    from pipeline.common import interim_path
    p = interim_path("observation", "bfs_bevnat_bilanz.parquet")
    if p.exists():
        b = pd.read_parquet(p)
    else:
        from pipeline.sources.bfs_bevnat_bilanz.ingest import observations as bil
        b = bil()
    return b[(b["metric_id"] == "bil_births") & (b["level"] == "gemeinde") & (b["status"] == "ok")]


def fill_births(obs: pd.DataFrame, bil: pd.DataFrame) -> pd.DataFrame:
    """Suppressed BEVNAT births (1981+) filled from the demographic balance."""
    m = (obs["metric_id"] == "bevnat_births") & (obs["level"] == "gemeinde") & (obs["status"] == "suppressed")
    b = bil.set_index(["unit_id", "period"])
    key = pd.MultiIndex.from_arrays([obs.loc[m, "unit_id"].astype(str), obs.loc[m, "period"].astype(str)])
    hit = key.isin(b.index)
    idx = obs.index[m][hit]
    src = b.loc[key[hit]]
    obs.loc[idx, "value"] = src["value"].values
    obs.loc[idx, "status"] = "ok"
    obs.loc[idx, "precision"] = src["precision"].values
    obs.loc[idx, "provenance"] = src["provenance"].values
    obs.loc[idx, "note"] = BILANZ_NOTE
    return obs


def observations() -> pd.DataFrame:
    obs, _ = to_observations(wide(), "GEO", "TIME_PERIOD", {c: c for c in FLOWS}, SOURCE)
    obs.loc[obs["status"] == "suppressed", "note"] = SUPPRESSED_NOTE
    return fill_births(obs, _bilanz_births())
