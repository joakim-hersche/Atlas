"""Fetch BFS rent tables (Structural Survey) by canton and the Swiss cities statistics (SSV).

Canton tables (BFS DAM, OPEN-BY, one sheet per survey year):
  36398431  T 09.03.03.01  average monthly net rent in CHF by number of rooms and canton
  36398447  average monthly net rent per m² in CHF by number of rooms and canton
Cities (Statistik der Schweizer Städte, SDMX on disseminate.stats.swiss, OPEN-BY assets
36503090 [2026 edition, data 2023] and 35367668 [2025 edition, data 2022]):
  DF_SSV_BUILD_HOUSING_OC  occupied dwellings by tenure and average monthly net rent (3 and 4 rooms)
Versions are pinned: SSV flows carry NonProductionDataflow=true.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_rents"
DAM = "https://dam-api.bfs.admin.ch/hub/api/dam/assets"
CANTON_TABLES = {"chf": 36398431, "m2": 36398447}
SSV_FLOW = "DF_SSV_BUILD_HOUSING_OC"
SSV_VERSIONS = ["2025.2", "2026.1.0"]  # editions 2025 (data 2022) and 2026 (data 2023)
CSV = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}


def canton_table(kind: str):
    dam = CANTON_TABLES[kind]
    return fetch(f"{DAM}/{dam}/master", SOURCE, f"rent_canton_{kind}_{dam}.xlsx")


def ssv_city_rents(version: str):
    url = f"https://disseminate.stats.swiss/rest/data/CH1.SSV,{SSV_FLOW},{version}/all"
    return fetch(url, SOURCE, f"ssv_housing_oc_{version}.csv", headers=CSV)
