"""Fetch the average net rent per m2 by labour market area from the BFS regional disparities indicators.

SDMX flow CH1.RDISP DF_RDISP_2 1.0.0 (Regionale Disparitäten: Ausgewählte Variablen nach Arbeitsmarktregionen 2018,
BFS asset 36681060, OPEN-BY), indicators SA1048V (monthly net rent per m2, CHF) and SA1001V (dwellings, total; not used).
Measures OBS (value) and CI (confidence interval +/-); the flow is NonProductionDataflow, so the version is pinned.
Same figures as the Swiss Stats Map Explorer map of asset 36679710 (dataset ch_21_03, indicator sa1048v).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_amr_rents"
BASE = "https://disseminate.stats.swiss/rest/data"
CSV = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0;labels=both"}
FLOW = "CH1.RDISP,DF_RDISP_2,1.0.0"


def rent_csv():
    return fetch(f"{BASE}/{FLOW}/.SA1048V..", SOURCE, "DF_RDISP_2_SA1048V.csv", headers=CSV)


def dam_asset():
    """Asset metadata of the flow (terms of use)."""
    return fetch("https://dam-api.bfs.admin.ch/hub/api/dam/assets/36681060", SOURCE, "dam_asset_36681060.json")


def dam_map_asset():
    return fetch("https://dam-api.bfs.admin.ch/hub/api/dam/assets/36679710", SOURCE, "dam_asset_36679710.json")


if __name__ == "__main__":
    print(rent_csv(), dam_asset(), dam_map_asset())
