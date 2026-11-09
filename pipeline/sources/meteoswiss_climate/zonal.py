"""Zonal statistics on a 100 m lattice (LV95): municipality means, area- or population-weighted.

Shared by the raster connectors meteoswiss_climate and bafu_air (both maintained together).

Lattice: 100 m cells aligned to the STATPOP hectare grid (corners at multiples of 100 m),
E 2'480'000–2'850'000, N 1'065'000–1'300'000.
- Municipality ids: the reference-state polygons (data/interim/geo/units_<ref>.gpkg, layer gemeinde)
  rasterized at the lattice (cell centre inside the polygon). Municipalities smaller than a cell
  centre spacing get the cells they touch (all_touched) as a fallback.
- Population: STATPOP hectare counts (BBTOT) placed in their hectare cell.
- Raster values: any LV95 grid sampled at the lattice cell centres (nearest source cell), or, for
  grids finer than 100 m, block-averaged to 100 m (block_mean_100m, read in row windows).
A hectare whose centre lies outside every polygon (lake shores, generalized G1 borders) is
assigned to the nearest municipality cell within 500 m; the rest is reported as unassigned.
"""
from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import Window

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.sources.bfs_statpop_geodata.fetch import hectare

RES = 100
E0, N1 = 2_480_000, 1_300_000
WIDTH, HEIGHT = 3_700, 2_350
TRANSFORM = from_origin(E0, N1, RES, RES)


def _centres():
    xs = E0 + RES * (np.arange(WIDTH) + 0.5)
    ys = N1 - RES * (np.arange(HEIGHT) + 0.5)
    return xs, ys


@lru_cache(maxsize=1)
def _polygons() -> gpd.GeoDataFrame:
    g = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde")
    return g[["id", "geometry"]].assign(id=lambda d: d["id"].astype(int))


@lru_cache(maxsize=1)
def municipality_ids() -> np.ndarray:
    g = _polygons()
    ids = rasterize(((geom, int(i)) for i, geom in zip(g["id"], g.geometry)), out_shape=(HEIGHT, WIDTH),
                    transform=TRANSFORM, fill=0, dtype="int32")
    missing = set(g["id"].astype(int)) - set(np.unique(ids))
    if missing:  # very small municipalities: cells they touch, where still unassigned
        sub = g[g["id"].astype(int).isin(missing)]
        touch = rasterize(((geom, int(i)) for i, geom in zip(sub["id"], sub.geometry)),
                          out_shape=(HEIGHT, WIDTH), transform=TRANSFORM, fill=0, dtype="int32",
                          all_touched=True)
        put = (touch > 0) & (ids == 0)
        ids[put] = touch[put]
        still = set(sub["id"].astype(int)) - set(np.unique(ids))
        for i in still:  # override one touched cell
            r, c = np.argwhere(touch == i)[0]
            ids[r, c] = i
    return ids


@lru_cache(maxsize=8)
def population(year: int) -> tuple[np.ndarray, np.ndarray, dict]:
    """Population per lattice cell (STATPOP hectare BBTOT), the municipality id per cell for that
    population (populated cells outside every polygon snapped to the nearest one within 500 m), and
    assignment diagnostics."""
    df = pd.read_parquet(hectare(year), columns=["E_KOORD", "N_KOORD", "BBTOT"])
    df = df[df["BBTOT"] > 0]
    col = ((df["E_KOORD"] - E0) // RES).astype(int).to_numpy()
    row = ((N1 - df["N_KOORD"]) // RES - 1).astype(int).to_numpy()  # E/N are lower-left corners
    ok = (col >= 0) & (col < WIDTH) & (row >= 0) & (row < HEIGHT)
    pop = np.zeros((HEIGHT, WIDTH), dtype="float64")
    np.add.at(pop, (row[ok], col[ok]), df["BBTOT"].to_numpy()[ok])
    ids = municipality_ids().copy()
    rr, cc = np.nonzero((ids == 0) & (pop > 0))
    xs, ys = _centres()
    pts = gpd.GeoDataFrame({"r": rr, "c": cc}, geometry=gpd.points_from_xy(xs[cc], ys[rr]), crs=2056)
    j = gpd.sjoin_nearest(pts, _polygons(), how="inner", max_distance=500)
    j = j[~j.index.duplicated()]
    ids[j["r"].to_numpy(), j["c"].to_numpy()] = j["id"].to_numpy()
    snapped = float(pop[j["r"].to_numpy(), j["c"].to_numpy()].sum())
    info = {"year": year, "pop_total": float(pop.sum()), "pop_snapped": snapped,
            "pop_unassigned": float(pop[(ids == 0) & (pop > 0)].sum())}
    return pop, ids, info


def sample(path, band: int = 1) -> np.ndarray:
    """Values of an LV95 grid at the lattice cell centres (nearest cell; NaN outside/nodata)."""
    with rasterio.open(path) as r:
        a = r.read(band).astype("float64")
        if r.nodata is not None:
            a[a == r.nodata] = np.nan
        t = r.transform
    xs, ys = _centres()
    c = np.floor((xs - t.c) / t.a).astype(int)
    rr = np.floor((ys - t.f) / t.e).astype(int)
    cv, rv = (c >= 0) & (c < a.shape[1]), (rr >= 0) & (rr < a.shape[0])
    out = np.full((HEIGHT, WIDTH), np.nan)
    sub = a[np.clip(rr, 0, a.shape[0] - 1)][:, np.clip(c, 0, a.shape[1] - 1)]
    out[np.ix_(rv, cv)] = sub[np.ix_(rv, cv)]
    return out


def block_mean_100m(path, rows_per_window: int = 500) -> np.ndarray:
    """Average a fine grid (cell size dividing 100 m, origin on the 100 m lattice) to the lattice."""
    with rasterio.open(path) as r:
        t = r.transform
        f = int(round(RES / t.a))
        assert abs(t.a * f - RES) < 1e-6 and abs(-t.e * f - RES) < 1e-6, "cell size must divide 100 m"
        c0 = (t.c - E0) / RES
        r0 = (N1 - t.f) / RES
        assert c0 == int(c0) and r0 == int(r0), "grid origin not on the 100 m lattice"
        c0, r0 = int(c0), int(r0)
        out = np.full((HEIGHT, WIDTH), np.nan)
        step = rows_per_window - rows_per_window % f
        ncols = (r.width // f) * f
        for top in range(0, (r.height // f) * f, step):
            h = min(step, (r.height // f) * f - top)
            a = r.read(1, window=Window(0, top, ncols, h)).astype("float32")
            if r.nodata is not None:
                a[a == r.nodata] = np.nan
            with np.errstate(invalid="ignore"):
                m = np.nanmean(a.reshape(h // f, f, ncols // f, f), axis=(1, 3))
            rr = r0 + top // f
            cc = c0
            rs, cs = slice(max(rr, 0), min(rr + m.shape[0], HEIGHT)), slice(max(cc, 0), min(cc + m.shape[1], WIDTH))
            out[rs, cs] = m[rs.start - rr:rs.stop - rr, cs.start - cc:cs.stop - cc]
    return out


def zonal_mean(values: np.ndarray, ids: np.ndarray, weights: np.ndarray | None = None) -> pd.DataFrame:
    """Weighted mean of values per municipality id (weights=None: area mean over valid cells)."""
    w = np.ones_like(values) if weights is None else weights
    ok = (ids > 0) & np.isfinite(values) & (w > 0)
    idx = ids[ok]
    n = int(ids.max()) + 1
    sw = np.bincount(idx, weights=w[ok], minlength=n)
    swv = np.bincount(idx, weights=(w * np.nan_to_num(values))[ok], minlength=n)
    cnt = np.bincount(idx, minlength=n)
    present = np.nonzero(sw > 0)[0]
    return pd.DataFrame({"bfs_nr": present, "value": swv[present] / sw[present], "weight": sw[present],
                         "cells": cnt[present]})


def share_above(values: np.ndarray, ids: np.ndarray, weights: np.ndarray, limit: float) -> pd.DataFrame:
    """Weight (population) in cells with value > limit, and total weight with a value, per id."""
    ok = (ids > 0) & np.isfinite(values) & (weights > 0)
    idx = ids[ok]
    n = int(ids.max()) + 1
    tot = np.bincount(idx, weights=weights[ok], minlength=n)
    above = np.bincount(idx, weights=(weights * (np.nan_to_num(values) > limit))[ok], minlength=n)
    present = np.nonzero(tot > 0)[0]
    return pd.DataFrame({"bfs_nr": present, "above": above[present], "total": tot[present]})
