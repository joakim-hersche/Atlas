"""Fetch BFS republications of the ESTV tax burden (BFS OPEN-BY), from the SDMX platform.

Cities: Statistik der Schweizer Städte (BFS/Städteverband), flows DF_SSV_TAX_BRDN_* (180 cities),
  editions 2025.2 (tax year 2023) and 2026.1.0 (tax year 2024); asset 36503269 (2026 edition).
Labour market areas 2018: Indikatoren regionaler Disparitäten, flow CH1.RDISP DF_RDISP_2 1.0.0
  (asset 36681060), indicators EC6000I-EC6005I, 2010-2025.
Both flows carry NonProductionDataflow=true, so versions are pinned.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_tax_burden"
BASE = "https://disseminate.stats.swiss/rest/data"
CSV = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}
SSV_FLOWS = ["DF_SSV_TAX_BRDN_REV_SIN", "DF_SSV_TAX_BRDN_REV_MAR_NC", "DF_SSV_TAX_BRDN_REV_MAR_2C",
             "DF_SSV_TAX_BRDN_REV_RENT", "DF_SSV_TAX_BRDN_FOR_MAR_NC"]
SSV_VERSIONS = ["2025.2", "2026.1.0"]
AMR_INDICATORS = ["EC6000I", "EC6001I", "EC6002I", "EC6003I", "EC6004I", "EC6005I"]


def ssv_flow(flow: str, version: str):
    return fetch(f"{BASE}/CH1.SSV,{flow},{version}/all", SOURCE, f"{flow}_{version}.csv", headers=CSV)


def amr_tax():
    key = "." + "+".join(AMR_INDICATORS) + ".."
    return fetch(f"{BASE}/CH1.RDISP,DF_RDISP_2,1.0.0/{key}", SOURCE, "DF_RDISP_2_tax.csv", headers=CSV)
