"""Population exposure to road and rail traffic noise per municipality (BAFU sonBASE 2021 grids).

Method (documented in metrics.yaml and meta.yaml)
- Inputs: four 10 m grids of the modelled noise level Lr in dB(A) (road day / night, rail day / night; sonBASE,
  state 2021), the public GWR building register (building coordinates, dwellings, construction year) and the
  STATPOP 2021 hectare population.
- Residents: each populated STATPOP hectare distributes its residents over the residential buildings (GKAT 1020,
  1030, 1040; existing, built up to 2021) whose coordinate lies in the hectare, in proportion to their dwellings.
  Hectares without such a building put their residents at the hectare centre. Residents therefore add up to the
  STATPOP hectare total.
- Level at a building: the maximum of the grid over the 3 x 3 cells (30 m) around the building coordinate, which
  approximates the most exposed facade. A building without a mapped value is counted as not exposed (the grids
  carry no value outside the modelled noise corridor).
- Exposure indicators: residents in buildings at or above 60 dB(A) by day or 50 dB(A) by night (the immission limit
  values, IGW, of the Noise Abatement Ordinance LSV, SR 814.41, for sensitivity level II, residential zones), and
  at or above 65 / 55 dB(A) (IGW of sensitivity level III, mixed zones). The cantonal zoning (which limit applies
  where) is not used, so these are indicators, not the official count of people above the IGW.
Everything is a model: precision "modelled". sonBASE is for statistics at national and regional level
(BAFU disclaimer); values for a single municipality are indicative.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.common import interim_path
from pipeline.harmonize.helpers import emit
from pipeline.sources.bafu_noise.fetch import KINDS, grid
from pipeline.sources.bafu_noise.sample import sample_points
from pipeline.sources.bfs_gwr.buildings import load as load_buildings
from pipeline.sources.meteoswiss_climate import zonal

SOURCE = "bafu_noise"
POP_YEAR = 2021
NEIGHBOURHOOD = 1  # 3 x 3 cells = +-10 m around the building coordinate
LIMITS = {"road_day": 60.0, "road_night": 50.0, "rail_day": 60.0, "rail_night": 50.0}  # IGW, sensitivity level II
HIGH = {"road_day": 65.0, "road_night": 55.0, "rail_day": 65.0, "rail_night": 55.0}  # IGW, sensitivity level III
RES_CATEGORIES = (1020, 1030, 1040)


def _cell(e, n):
    col = np.floor((e - zonal.E0) / zonal.RES).astype("int64")
    row = ((zonal.N1 - np.floor(n / zonal.RES) * zonal.RES) // zonal.RES - 1).astype("int64")
    return row, col


def residential_points() -> pd.DataFrame:
    """Residential buildings with hectare cell; noise levels cached per building."""
    b = load_buildings()
    b = b[(b["GSTAT"] == 1004) & b["GKAT"].isin(RES_CATEGORIES) & (b["GANZWHG"] > 0) & b["GKODE"].notna()
          & ~(b["GBAUJ"] > POP_YEAR)].copy()
    b["row"], b["col"] = _cell(b["GKODE"].to_numpy(), b["GKODN"].to_numpy())
    return b[["EGID", "GKODE", "GKODN", "GANZWHG", "row", "col"]].reset_index(drop=True)


def levels() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(buildings, fallback hectare centres) with one column per grid kind; cached in data/interim/noise."""
    f1, f2 = interim_path("noise", "building_levels.parquet"), interim_path("noise", "hectare_levels.parquet")
    if f1.exists() and f2.exists():
        return pd.read_parquet(f1), pd.read_parquet(f2)
    pop, ids, info = zonal.population(POP_YEAR)
    b = residential_points()
    has_b = np.zeros(pop.shape, dtype=bool)
    ok = (b["row"] >= 0) & (b["row"] < zonal.HEIGHT) & (b["col"] >= 0) & (b["col"] < zonal.WIDTH)
    has_b[b.loc[ok, "row"], b.loc[ok, "col"]] = True
    rr, cc = np.nonzero((pop > 0) & ~has_b)
    xs, ys = zonal._centres()
    h = pd.DataFrame({"row": rr, "col": cc, "GKODE": xs[cc], "GKODN": ys[rr]})
    for kind in KINDS:
        p = grid(kind)
        b[kind] = sample_points(p, b["GKODE"].to_numpy(), b["GKODN"].to_numpy(), NEIGHBOURHOOD)
        h[kind] = sample_points(p, h["GKODE"].to_numpy(), h["GKODN"].to_numpy(), NEIGHBOURHOOD)
        print("noise", kind, "buildings with value", float(b[kind].notna().mean()),
              "fallback hectares", len(h), "with value", float(h[kind].notna().mean()), flush=True)
    f1.parent.mkdir(parents=True, exist_ok=True)
    b.to_parquet(f1, index=False)
    h.to_parquet(f2, index=False)
    return b, h


def residents_table() -> pd.DataFrame:
    """One row per residential building / fallback hectare with its residents and the four levels."""
    pop, ids, info = zonal.population(POP_YEAR)
    b, h = levels()
    ok = (b["row"] >= 0) & (b["row"] < zonal.HEIGHT) & (b["col"] >= 0) & (b["col"] < zonal.WIDTH)
    b = b[ok].copy()
    key = b["row"] * zonal.WIDTH + b["col"]
    b["residents"] = pop[b["row"], b["col"]] * b["GANZWHG"] / b.groupby(key)["GANZWHG"].transform("sum")
    b = b[b["residents"] > 0]
    h = h.copy()
    h["residents"] = pop[h["row"], h["col"]]
    cols = ["row", "col", "residents", *KINDS]
    t = pd.concat([b[cols], h[cols]], ignore_index=True)
    t["bfs_nr"] = ids[t["row"], t["col"]]
    return t


def exposure(t: pd.DataFrame) -> pd.DataFrame:
    """Per municipality: residents and residents at or above the limits (see METRICS)."""
    t = t[t["bfs_nr"] > 0]
    d = pd.DataFrame({"bfs_nr": t["bfs_nr"].to_numpy(), "residents": t["residents"].to_numpy()})
    for k, lim in LIMITS.items():
        d[k] = d["residents"] * (t[k] >= lim).to_numpy()
    hi = np.logical_or.reduce([(t[k] >= lim).to_numpy() for k, lim in HIGH.items()])
    lo = np.logical_or.reduce([(t[k] >= lim).to_numpy() for k, lim in LIMITS.items()])
    d["any_60_50"] = d["residents"] * lo
    d["any_65_55"] = d["residents"] * hi
    return d.groupby("bfs_nr", as_index=False).sum()


METRICS = {"residents": "noise_residents", "road_day": "noise_road_day_60_residents",
           "road_night": "noise_road_night_50_residents", "rail_day": "noise_rail_day_60_residents",
           "rail_night": "noise_rail_night_50_residents", "any_60_50": "noise_any_60_50_residents",
           "any_65_55": "noise_any_65_55_residents"}


def observations() -> pd.DataFrame:
    e = exposure(residents_table())
    e["period"] = "2021"
    o = emit(e, METRICS, "period", SOURCE, precision="modelled", provenance="source_current_state")
    o["note"] = "sonBASE 2021 grids, GWR buildings, STATPOP 2021 hectares; modelled (see description)"
    o.loc[o["metric_id"] == "noise_residents", "precision"] = "exact"
    o.loc[o["metric_id"] == "noise_residents", "note"] = "STATPOP 2021 hectare residents assigned to the municipality"
    return o
