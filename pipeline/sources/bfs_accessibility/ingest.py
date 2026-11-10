"""Accessibility of services per municipality (BFS "Erreichbarkeit von Dienstleistungen", hectare
grid 2011, 2015, 2018, 2021).

Source: one row per inhabited hectare and reference year with POP_TOTAL (permanent residents at
31 Dec; 1–3 published as 3) and D_<service> = shortest road-network distance in metres from the
hectare centre to the nearest service location (swissTLM3D roads, Dijkstra; empty where the start
or target is more than 500 m from the network). Service locations: STATENT establishments geocoded
to the building (December of the reference year), MAS doctors' practices (2018, 2021 only), ARE
public transport stops by stop category (state 2012 for 2011, 2015, 2018, 2021).

Per municipality (reference-state polygons, pipeline/sources/meteoswiss_climate/zonal.py lattice;
a hectare whose centre falls outside every polygon is assigned to the nearest municipality within
500 m) and year:
  acc_population                 residents in the inhabited hectares (POP_TOTAL), the weight
  acc_dist_<service>             population-weighted mean distance (m) over hectares with a value
  acc_within500_<service>,       residents whose hectare is at most 500 m / 1 km from the service
  acc_within1000_<service>       (hectares without a distance count as not within)
Distance to a stop of category I or II = min(D_STOP_1, D_STOP_2).
"""
from __future__ import annotations

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_accessibility.fetch import grid_csv
from pipeline.sources.meteoswiss_climate import zonal

SOURCE = "bfs_accessibility"
# metric suffix -> source column(s) (several columns: minimum distance)
SERVICES = {
    "supermarket": ["D_SMARKET"], "grocery": ["D_GROCERY"], "pharmacy": ["D_PHARMA"],
    "doctor": ["D_MEDIC"], "gp": ["D_MEDIC_B"], "dentist": ["D_DENTIST"],
    "school_compulsory": ["D_SCHOOL_O"], "school_upper_secondary": ["D_SCHOOL_S"],
    "pt_stop": ["D_STOP_TOT"], "pt_stop_cat12": ["D_STOP_1", "D_STOP_2"],
    "bank": ["D_BANK"], "restaurant": ["D_RESTO"], "public_admin": ["D_ADMIN"],
    "nursing_home": ["D_RETIRE"], "forest": ["D_FOREST"],
}
WITHIN = {500: ["supermarket", "grocery", "pharmacy", "gp", "school_compulsory", "pt_stop"],
          1000: ["supermarket", "grocery", "pharmacy", "gp", "doctor", "school_compulsory", "pt_stop_cat12"]}
LOG: dict = {}


def _load() -> pd.DataFrame:
    cols = sorted({c for v in SERVICES.values() for c in v})
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    sel = ", ".join(["E_COORD", "N_COORD", "YEAR", "POP_TOTAL", *cols])
    d = con.execute(f"SELECT {sel} FROM read_csv('{grid_csv()}', delim=';', header=true)").df()
    con.close()
    return d


def _assign(e: np.ndarray, n: np.ndarray) -> np.ndarray:
    """Reference-state municipality id of each hectare (lower-left corner e, n)."""
    ids = zonal.municipality_ids()
    col = ((e - zonal.E0) // zonal.RES).astype(int)
    row = ((zonal.N1 - n) // zonal.RES - 1).astype(int)
    ok = (col >= 0) & (col < zonal.WIDTH) & (row >= 0) & (row < zonal.HEIGHT)
    out = np.zeros(len(e), dtype="int64")
    out[ok] = ids[row[ok], col[ok]]
    miss = np.nonzero(out == 0)[0]
    if len(miss):
        pts = gpd.GeoDataFrame({"i": miss}, geometry=gpd.points_from_xy(e[miss] + 50, n[miss] + 50), crs=2056)
        j = gpd.sjoin_nearest(pts, zonal._polygons(), how="inner", max_distance=500)
        j = j[~j.index.duplicated()]
        out[j["i"].to_numpy()] = j["id"].to_numpy()
    return out


def observations() -> pd.DataFrame:
    d = _load()
    d["bfs_nr"] = _assign(d["E_COORD"].to_numpy(), d["N_COORD"].to_numpy())
    parts = []
    for year, g in d.groupby("YEAR"):
        lost = g.loc[g["bfs_nr"] == 0, "POP_TOTAL"].sum()
        LOG[int(year)] = {"hectares": len(g), "residents": int(g["POP_TOTAL"].sum()), "unassigned_residents": int(lost)}
        print(f"accessibility {year}: {LOG[int(year)]}")
        g = g[g["bfs_nr"] > 0]
        pop = g["POP_TOTAL"].astype(float)
        wide = pd.DataFrame({"bfs_nr": sorted(g["bfs_nr"].unique())}).set_index("bfs_nr")
        wide["acc_population"] = pop.groupby(g["bfs_nr"]).sum()
        metric_cols = {"acc_population": "acc_population"}
        for svc, cols in SERVICES.items():
            dist = g[cols].astype(float).min(axis=1, skipna=False) if len(cols) > 1 else g[cols[0]].astype(float)
            if dist.notna().sum() == 0:
                continue  # service not computed by BFS for this year (doctors: 2018, 2021 only)
            has = dist.notna()
            sw = pop[has].groupby(g.loc[has, "bfs_nr"]).sum()
            swd = (pop[has] * dist[has]).groupby(g.loc[has, "bfs_nr"]).sum()
            c = f"acc_dist_{svc}"
            wide[c] = swd / sw.replace(0, np.nan)
            metric_cols[c] = c
            for lim, svcs in WITHIN.items():
                if svc in svcs:
                    c = f"acc_within{lim}_{svc}"
                    wide[c] = (pop * (dist <= lim)).groupby(g["bfs_nr"]).sum()
                    wide[c] = wide[c].fillna(0.0)
                    metric_cols[c] = c
        wide = wide.reset_index().assign(period=str(int(year)))
        for col, mid in metric_cols.items():
            o = emit(wide, {col: mid}, "period", SOURCE, precision="exact" if col == "acc_population" else "modelled",
                     provenance="source_current_state")
            o.loc[o["status"] == "ok", "note"] = f"BFS accessibility hectares {int(year)}"
            o.loc[o["status"] != "ok", "note"] = "no inhabited hectare with a road distance for this service"
            parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
