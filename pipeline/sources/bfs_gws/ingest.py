"""Buildings and dwellings statistics (GWS) per municipality, 2010–latest (31 December).

BFS SDMX flows (CH1.GWS, 1.1.0), geo codes on the SNAP_2025 state (history re-mapped by BFS):
  DF_GWS_REG1  buildings with residential use by building category x construction period
  DF_GWS_REG3  ... by heating energy source (2021+)
  DF_GWS_REG5  dwellings by number of rooms x construction period
  DF_GWS_REG7  dwellings by floor-area class (2012+)
Only the margins needed are requested (other dimensions at '_T'), so downloads stay small.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_sdmx.fetch import data, data_chunked
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_gws"
AG, VER = "CH1.GWS", "1.1.0"
GEO = "GEMEINDENAME"
YEARS = list(range(2010, 2026))

PERIODS = {  # construction-period classes -> GBAUPS codes
    "gws_bld_pre1919": ["8011"],
    "gws_bld_1919_1945": ["8012"],
    "gws_bld_1946_1980": ["8013", "8014", "8015"],
    "gws_bld_1981_2000": ["8016", "8017", "8018", "8019"],
    "gws_bld_2001_2010": ["8020", "8021"],
    "gws_bld_2011plus": ["8022", "8023", "8024"],
}
CATEGORIES = {"gws_bld_sfh": "1021", "gws_bld_mfh": "1025", "gws_bld_res_mixed": "1030",
              "gws_bld_partly_res": "1040"}
HEATING = {"gws_heat_heatpump": "1", "gws_heat_gas": "2", "gws_heat_oil": "3", "gws_heat_wood": "4",
           "gws_heat_electric": "5", "gws_heat_district": "6", "gws_heat_other": ["7", "8"],
           "gws_heat_none": "9"}
ROOMS = {"gws_dw_rooms_1_2": ["1", "2"], "gws_dw_rooms_3": "3", "gws_dw_rooms_4": "4",
         "gws_dw_rooms_5plus": ["5", "6"]}
AREAS = {"gws_dw_area_lt60": "1", "gws_dw_area_60_79": "2", "gws_dw_area_80_99": "3",
         "gws_dw_area_100_119": "4", "gws_dw_area_120_159": "5", "gws_dw_area_160plus": "6"}


def dwellings_by_rooms() -> pd.DataFrame:
    """Long frame of DF_GWS_REG5 by rooms (all construction periods, all categories)."""
    return data(AG, "DF_GWS_REG5", VER, {"FREQ": "A", "GBAUPS": "_T", "GKATS": "_T"})


def wide() -> pd.DataFrame:
    parts = []
    b_per = data_chunked(AG, "DF_GWS_REG1", VER, {"FREQ": "A", "GKATS": "_T"}, YEARS)
    parts.append(pivot(b_per, GEO, {"gws_buildings": {"GBAUPS": "_T"},
                                    **{k: {"GBAUPS": v} for k, v in PERIODS.items()}}))
    b_cat = data(AG, "DF_GWS_REG1", VER, {"FREQ": "A", "GBAUPS": "_T"})
    parts.append(pivot(b_cat, GEO, {k: {"GKATS": v} for k, v in CATEGORIES.items()}))
    heat = data(AG, "DF_GWS_REG3", VER, {"FREQ": "A", "GBAUPS": "_T", "GKATS": "_T"})
    parts.append(pivot(heat, GEO, {k: {"GWAERZH": v} for k, v in HEATING.items()}))
    rooms = dwellings_by_rooms()
    parts.append(pivot(rooms, GEO, {"gws_dwellings": {"WAZIMS": "_T"},
                                    **{k: {"WAZIMS": v} for k, v in ROOMS.items()}}))
    dper = data(AG, "DF_GWS_REG5", VER, {"FREQ": "A", "GBAUPS": ["_T", "8020", "8021", "8022", "8023", "8024"],
                                         "GKATS": "_T", "WAZIMS": "_T"})
    parts.append(pivot(dper, GEO, {"gws_dw_2001plus": {"GBAUPS": ["8020", "8021", "8022", "8023", "8024"]},
                                   "gws_dw_2011plus": {"GBAUPS": ["8022", "8023", "8024"]}}))
    area = data(AG, "DF_GWS_REG7", VER, {"FREQ": "A", "GBAUPS": "_T", "GKATS": "_T"})
    parts.append(pivot(area, GEO, {k: {"FLAECHKL": v} for k, v in AREAS.items()}))
    out = parts[0]
    for p in parts[1:]:
        out = out.merge(p, on=[GEO, "TIME_PERIOD"], how="left")
    return out


def observations() -> pd.DataFrame:
    w = wide()
    cols = [c for c in w.columns if c.startswith("gws_") and not c.endswith("__status")]
    obs, _ = to_observations(w, GEO, "TIME_PERIOD", {c: c for c in cols}, SOURCE)
    # series that start later (heating 2021+, floor area 2012+) have no rows before
    return obs[~((obs["status"] == "no_data") & obs["note"].isna())].reset_index(drop=True)
