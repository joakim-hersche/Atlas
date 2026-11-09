"""Arealstatistik (land use statistics) per municipality and survey period, 1979/85 – 2020/25.

BFS SDMX (CH1.AREA): DF_AREA_NOAS 1.1.0 (standard nomenclature NOAS04, hectares; dims NOAS,
PERIOD A1..A5, REGION) and DF_AREA_IMPV 1.0.0 (soil sealing). Geo codes on the 2026 state
(codelist CL_AREA_HIER_REGION_2026_DIFF; the hectare points are re-assigned by BFS, so the series
are on constant boundaries). The 2020/25 survey (A5) is still running: only the municipalities
already surveyed have values; the rest get status 'not_covered'. Codes 9xxx (lake areas outside
municipalities) and the condominium areas 2391, 5391, 5394 are only in canton/national totals.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_arealstatistik"
AG = "CH1.AREA"
GEO = "REGION"
PERIODS = {"A1": "1979/85", "A2": "1992/97", "A3": "2004/09", "A4": "2013/18", "A5": "2020/25"}
LATEST = "2020/25"
NOAS = {
    "area_settlement_ha": "1", "area_agriculture_ha": "2", "area_wooded_ha": "3", "area_unproductive_ha": "4",
    "area_industrial_ha": "101", "area_building_ha": "102", "area_transport_ha": "103",
    "area_water_ha": ["413", "414"], "area_glacier_ha": "417",
}
NOT_COVERED = "2020/25 survey not yet completed for this municipality (BFS publishes it canton by canton)"


def wide() -> pd.DataFrame:
    d = data(AG, "DF_AREA_NOAS", "1.1.0", {"NOAS": ["1", "2", "3", "4", "101", "102", "103", "413", "414", "417"]})
    w = pivot(d, GEO, {**{k: {"NOAS": v} for k, v in NOAS.items()},
                       "area_total_ha": {"NOAS": ["1", "2", "3", "4"]}}, period_col="PERIOD")
    s = data(AG, "DF_AREA_IMPV", "1.0.0", {"NOLC": ["1", "2"]})
    w = w.merge(pivot(s, GEO, {"area_sealed_ha": {"NOLC": "1"}}, period_col="PERIOD"), on=[GEO, "PERIOD"], how="left")
    # settlement area of the first survey, attached to every period as the base of the change index
    base = w.loc[w["PERIOD"] == "A1", [GEO, "area_settlement_ha"]].rename(columns={"area_settlement_ha": "area_settlement_base_ha"})
    w = w.merge(base, on=GEO, how="left")
    w["area_settlement_base_ha__status"] = np.where(w["area_settlement_base_ha"].notna(), "ok", "no_data")
    w["PERIOD"] = w["PERIOD"].map(PERIODS)
    return w


def observations() -> pd.DataFrame:
    w = wide()
    cols = [*NOAS, "area_total_ha", "area_sealed_ha", "area_settlement_base_ha"]
    obs, _ = to_observations(w, GEO, "PERIOD", {c: c for c in cols}, SOURCE)
    obs = obs[~((obs["metric_id"] == "area_settlement_base_ha") & (obs["period"] == "1979/85"))]
    # municipalities without a 2020/25 value yet -> explicit 'not_covered' rows
    gem = obs[obs["level"] == "gemeinde"]
    units = sorted(set(gem["unit_id"]))
    have = set(zip(gem.loc[gem["period"] == LATEST, "unit_id"], gem.loc[gem["period"] == LATEST, "metric_id"]))
    extra = [(u, m) for m in cols for u in units if (u, m) not in have]
    add = pd.DataFrame(extra, columns=["unit_id", "metric_id"]).assign(
        level="gemeinde", vintage=REFERENCE_DATE.isoformat(), period=LATEST, value=np.nan,
        status="not_covered", precision="exact", provenance="source_current_state", source_id=SOURCE,
        note=NOT_COVERED)
    return pd.concat([obs, add[OBS_COLUMNS]], ignore_index=True)
