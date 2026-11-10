"""Vacant dwellings (Leerwohnungszählung, 1 June) per municipality, 1995–latest.

BFS SDMX: CH1.LWZ DF_LWZ_1 1.1.0 (dims GR_KT_GDE, WOHN_ANZAHL rooms, LEERWOHN_TYP type,
MEASURE_DIMENSION OBS = count / RATE = published vacancy rate, FREQ). Geo codes on the SNAP_2026
state. The flow has no dwelling stock; BFS's denominator is the GWS dwelling stock at 31 December of
the previous year (checked: CH 2026 45 493 / GWS 2025 4 883 159 = 0.93 % = published RATE), so the
stock is taken from DF_GWS_REG5 (total dwellings, year Y-1) and delivered as vac_dwelling_stock for
period Y (2011+). The published rate (1997+) is also delivered (vac_rate_bfs, not re-aggregatable).
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_gws.ingest import dwellings_by_rooms
from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_vacancy"
AG, FLOW, VER = "CH1.LWZ", "DF_LWZ_1", "1.1.0"
GEO = "GR_KT_GDE"
ROOMS = {"vac_rooms_1_2": ["1", "2"], "vac_rooms_3": "3", "vac_rooms_4": "4", "vac_rooms_5plus": ["5", "6"]}
TYPES = {"vac_sfh": "1", "vac_for_sale": "3", "vac_for_rent": "4", "vac_new": "5"}


def wide() -> pd.DataFrame:
    tot = data(AG, FLOW, VER, {"WOHN_ANZAHL": "_T", "LEERWOHN_TYP": "_T", "FREQ": "A"})
    w = pivot(tot, GEO, {"vac_dwellings": {"MEASURE_DIMENSION": "OBS"},
                         "vac_rate_bfs": {"MEASURE_DIMENSION": "RATE"}})
    rooms = data(AG, FLOW, VER, {"LEERWOHN_TYP": "_T", "MEASURE_DIMENSION": "OBS", "FREQ": "A"})
    w = w.merge(pivot(rooms, GEO, {k: {"WOHN_ANZAHL": v} for k, v in ROOMS.items()}), on=[GEO, "TIME_PERIOD"], how="left")
    types = data(AG, FLOW, VER, {"WOHN_ANZAHL": "_T", "MEASURE_DIMENSION": "OBS", "FREQ": "A"})
    w = w.merge(pivot(types, GEO, {k: {"LEERWOHN_TYP": v} for k, v in TYPES.items()}), on=[GEO, "TIME_PERIOD"], how="left")
    return w


def stock() -> pd.DataFrame:
    """GWS dwellings at 31 Dec of Y-1, labelled with the vacancy-count year Y."""
    s = pivot(dwellings_by_rooms(), "GEMEINDENAME", {"vac_dwelling_stock": {"WAZIMS": "_T"}})
    s["TIME_PERIOD"] = (s["TIME_PERIOD"].astype(int) + 1).astype(str)
    return s


def observations() -> pd.DataFrame:
    w = wide()
    cols = ["vac_dwellings", *ROOMS, *TYPES]
    o1, _ = to_observations(w, GEO, "TIME_PERIOD", {c: c for c in cols}, SOURCE)
    o2, _ = to_observations(w, GEO, "TIME_PERIOD", {"vac_rate_bfs": "vac_rate_bfs"}, SOURCE,
                            rule_by_col={"vac_rate_bfs": "not_aggregatable"})
    o2 = o2[o2["period"].astype(int) >= 1997]
    o2.loc[o2["status"] != "ok", "note"] = o2.loc[o2["status"] != "ok", "note"].fillna(
        "published rate not available (municipality merged since the count, or not published)")
    o3, _ = to_observations(stock(), "GEMEINDENAME", "TIME_PERIOD", {"vac_dwelling_stock": "vac_dwelling_stock"},
                            SOURCE, notes={"vac_dwelling_stock": "GWS dwellings at 31 Dec of the previous year"})
    return pd.concat([o1, o2, o3], ignore_index=True)
