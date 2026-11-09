"""Population weights for splits and territory exchanges.

For every (mutation, source version) with more than one successor, the weight of each successor is
the share of the source version's population living on the territory that goes to that successor.

Method
  1. Geometry of the source version and of each successor version from the BFS historized
     boundaries G1 (keyed by register histId).
  2. Population points from the BFS STATPOP hectare grid (hectare centres). Year: the last year
     before the mutation that is available (2010–2025), else 2000, else 1990 (proxy for older
     mutations; labeled as such).
  3. Each populated hectare inside the source polygon is assigned to the successor polygon that
     contains it (nearest successor if generalization leaves it in none).
  4. If the source territory has no population in the grid, area shares of the polygon overlap are
     used instead. If geometry is missing, successors get equal shares (flagged).

Result columns: mutation_id, from_hist_id, to_hist_id, weight, weight_source, pop_year, pop_total.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import split_pairs
from pipeline.common import interim_path
from pipeline.sources.bfs_hist_boundaries.fetch import fetch_all as fetch_boundaries
from pipeline.sources.bfs_statpop_geodata.fetch import HA_YEARS_LV03, hectare, hectare_years

LV03_TO_LV95 = (2_000_000, 1_000_000)  # hectare corners; sub-metre accuracy is irrelevant here


def load_g1() -> gpd.GeoDataFrame:
    path = fetch_boundaries()["g1"]
    g = gpd.read_file(path)
    g = g[g["GARTE"] == 11]  # political municipalities only
    return g[["GDEHISTID", "GDENR", "GDENAME", "VALID_FROM", "VALID_TO", "geometry"]]


def load_hectare_points(year: int) -> gpd.GeoDataFrame:
    path = hectare(year)
    if year in HA_YEARS_LV03:
        df = pd.read_csv(path, sep=";")
        ecol, ncol = ("KX", "KY") if "KX" in df.columns else ("X", "Y")
        pop = next(c for c in df.columns if c.endswith("BTOT"))
        e = df[ecol] + LV03_TO_LV95[0] + 50
        n = df[ncol] + LV03_TO_LV95[1] + 50
    else:
        df = pd.read_parquet(path)
        ecol = next(c for c in df.columns if c.upper() in ("E_KOORD", "E", "KX", "X"))
        ncol = next(c for c in df.columns if c.upper() in ("N_KOORD", "N", "KY", "Y"))
        pop = "BBTOT"
        e, n = df[ecol] + 50, df[ncol] + 50
    pts = gpd.GeoDataFrame({"pop": df[pop].astype(float)}, geometry=gpd.points_from_xy(e, n), crs=2056)
    return pts[pts["pop"] > 0]


def pop_year_for(date: pd.Timestamp, available: list[int]) -> tuple[int, str]:
    before = [y for y in available if y < date.year]
    lv95 = [y for y in before if y >= 2010]
    if lv95:
        return max(lv95), "pop_ha"
    if 2000 in before:
        return 2000, "pop_ha"
    if 1990 in before:
        return 1990, "pop_ha"
    return min(available), "pop_ha_proxy"  # mutation before 1991: nearest later grid as proxy


def compute_split_weights(pair: pd.DataFrame) -> pd.DataFrame:
    sp = split_pairs(pair)
    if sp.empty:
        return pd.DataFrame(columns=["mutation_id", "from_hist_id", "to_hist_id", "weight",
                                     "weight_source", "pop_year", "pop_total"])
    g1 = load_g1().set_index("GDEHISTID")
    years = hectare_years()
    groups = list(sp.groupby(["mutation_id", "from_hist_id"]))
    needed = {pop_year_for(g["date"].iloc[0], years)[0] for _, g in groups}
    points = {y: load_hectare_points(y) for y in sorted(needed)}
    rows = []
    for (mid, fh), g in groups:
        date = g["date"].iloc[0]
        tos = sorted(set(g["to_hist_id"]))
        year, label = pop_year_for(date, years)
        have_geom = fh in g1.index and all(t in g1.index for t in tos)
        if not have_geom:
            for t in tos:
                rows.append((mid, fh, t, 1 / len(tos), "equal_no_geometry", None, None))
            continue
        src = g1.loc[[fh], "geometry"].union_all()
        tgt = gpd.GeoDataFrame({"to": tos}, geometry=[g1.loc[t, "geometry"] for t in tos], crs=2056)
        pts = points[year]
        inside = pts[pts.within(src)]
        if inside["pop"].sum() > 0:
            j = gpd.sjoin_nearest(inside, tgt, how="left")
            j = j[~j.index.duplicated()]  # a point on a shared edge counts once
            share = j.groupby("to")["pop"].sum().reindex(tos, fill_value=0.0)
            total = share.sum()
            w = share / total
            src_label = f"{label}_{year}"
        else:
            area = np.array([src.intersection(geom).area for geom in tgt.geometry])
            total = None
            w = pd.Series(area / area.sum() if area.sum() > 0 else 1 / len(tos), index=tos)
            src_label = "area_g1"
        for t in tos:
            rows.append((mid, fh, t, float(w[t]), src_label, year if total else None, total))
    out = pd.DataFrame(rows, columns=["mutation_id", "from_hist_id", "to_hist_id", "weight",
                                      "weight_source", "pop_year", "pop_total"])
    return out


def run() -> str:
    pair = pd.read_parquet(interim_path("backbone", "mutation_pair.parquet"))
    w = compute_split_weights(pair)
    p = interim_path("backbone", "split_weights.parquet")
    w.to_parquet(p, index=False)
    return str(p)


if __name__ == "__main__":
    print(run())
