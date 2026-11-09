"""Road vehicles per municipality: passenger-car stock by fuel and holder (2010–latest, 30 Sept)
and first registrations of new passenger cars (2010–latest). BFS MFZ/IVS via SDMX.

Flows (CH1.MFZ_IVS, 1.0.0): DF_MFZ_0_COMMUNE (stock; dims geo, holder type, vehicle type, fuel)
and DF_IVS_0_COMMUNE (first registrations; adds registration type N = new vehicles, U = used).
Registration type '_T' (new + used imports) is published per municipality only for 2025, so the
series uses N (new vehicles), which exists for every year. Geo codes are on the 2025-04-05 state.
The flows are sparse: zero cells of the register are omitted (checked: fuel rows sum to the
total), so an absent fuel/holder row is a 0 when the municipality is in the flow.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_vehicles"
AG, VER = "CH1.MFZ_IVS", "1.0.0"
CAR = "001"  # passenger car
STOCK_FUELS = ["_T", "EL", "HP", "HD", "PH", "DH", "PC", "DC"]


def stock() -> pd.DataFrame:
    d = data(AG, "DF_MFZ_0_COMMUNE", VER, {"UV_RV_OWNER_TYPE": "_T", "UV_RV_VEHICLE_GROUP_AND_TYPE": CAR,
                                           "UV_RV_FUEL": STOCK_FUELS, "FREQ": "A"})
    w = pivot(d, "UV_KT_BEZ_GDE", {
        "mfz_cars": {"UV_RV_FUEL": "_T"},
        "mfz_cars_bev": {"UV_RV_FUEL": "EL"},
        "mfz_cars_phev": {"UV_RV_FUEL": ["HP", "HD"]},
        "mfz_cars_hev": {"UV_RV_FUEL": ["PH", "DH"]},
        "mfz_cars_petrol": {"UV_RV_FUEL": "PC"},
        "mfz_cars_diesel": {"UV_RV_FUEL": "DC"},
    }, absent_is_zero=True)
    p = data(AG, "DF_MFZ_0_COMMUNE", VER, {"UV_RV_OWNER_TYPE": "N", "UV_RV_VEHICLE_GROUP_AND_TYPE": CAR,
                                           "UV_RV_FUEL": "_T", "FREQ": "A"})
    w2 = pivot(p, "UV_KT_BEZ_GDE", {"mfz_cars_private": {}}, absent_is_zero=True)
    return w.merge(w2, on=["UV_KT_BEZ_GDE", "TIME_PERIOD"], how="left")


def new_registrations() -> pd.DataFrame:
    d = data(AG, "DF_IVS_0_COMMUNE", VER, {"UV_RV_OWNER_TYPE": "_T", "UV_RV_REGISTRATION_TYPE": "N",
                                           "UV_RV_VEHICLE_GROUP_AND_TYPE": CAR, "UV_RV_FUEL": ["_T", "EL"],
                                           "FREQ": "A"})
    return pivot(d, "UV_KT_BEZ_GDE", {"mfz_newreg_cars": {"UV_RV_FUEL": "_T"},
                                      "mfz_newreg_bev": {"UV_RV_FUEL": "EL"}}, absent_is_zero=True)


def observations() -> pd.DataFrame:
    s, n = stock(), new_registrations()
    cols_s = [c for c in s.columns if c.startswith("mfz_") and not c.endswith("__status")]
    cols_n = [c for c in n.columns if c.startswith("mfz_") and not c.endswith("__status")]
    o1, _ = to_observations(s, "UV_KT_BEZ_GDE", "TIME_PERIOD", {c: c for c in cols_s}, SOURCE)
    o2, _ = to_observations(n, "UV_KT_BEZ_GDE", "TIME_PERIOD", {c: c for c in cols_n}, SOURCE)
    return pd.concat([o1, o2], ignore_index=True)
