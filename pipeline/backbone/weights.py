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
    g = g[["GDEHISTID", "GDENR", "GDENAME", "VALID_FROM", "VALID_TO", "geometry"]].copy()
    # A register version (histId) can have several geometry states in G1 (boundary corrections
    # without a register mutation), each with its own VALID_FROM/VALID_TO. Select by date.
    g["VALID_FROM"] = pd.to_datetime(g["VALID_FROM"])
    g["VALID_TO"] = pd.to_datetime(g["VALID_TO"])
    return g


def geom_at(g1: gpd.GeoDataFrame, hist_id: int, date: pd.Timestamp):
    """Geometry of a version valid on date; nearest state in time if none covers the date."""
    rows = g1[g1["GDEHISTID"] == hist_id]
    if rows.empty:
        return None
    cover = rows[(rows["VALID_FROM"] <= date) & (rows["VALID_TO"].isna() | (rows["VALID_TO"] >= date))]
    if cover.empty:
        dist = (rows["VALID_FROM"] - date).abs()
        cover = rows.loc[[dist.idxmin()]]
    return cover.geometry.union_all()


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


def _descend_to_geometry(t: int, date: pd.Timestamp, g1: gpd.GeoDataFrame, succ: dict,
                         depth: int = 0) -> list[tuple[int, pd.Timestamp]]:
    """Versions with geometry reached from t (t itself if it has geometry on/after date).

    Short-lived transitional versions (e.g. one-day versions of the Thurgau reform 1994–1998) have
    no geometry in G1; their successors do.
    """
    if geom_at(g1, t, date) is not None or depth > 20:
        return [(t, date)]
    out = []
    for nxt, ndate in succ.get(t, []):
        out += _descend_to_geometry(nxt, ndate, g1, succ, depth + 1)
    return out


def _predecessor_geometry(h: int, g1: gpd.GeoDataFrame, pred: dict, depth: int = 0):
    """Union of the predecessors' geometries just before they became version h.

    Only valid when h was created entirely from its predecessors (merger/rename result), which is
    the case for the transitional versions this is used for.
    """
    if depth > 10 or h not in pred:
        return None
    parts = []
    for p, d in pred[h]:
        geom = geom_at(g1, p, d - pd.Timedelta(days=1))
        if geom is None:
            geom = _predecessor_geometry(p, g1, pred, depth + 1)
        if geom is None:
            return None
        parts.append(geom)
    return gpd.GeoSeries(parts, crs=2056).union_all()


def compute_split_weights(pair: pd.DataFrame) -> pd.DataFrame:
    """Weights per (mutation, source version, successor).

    Where a successor has no geometry (transitional version), the weights are computed directly
    onto the first descendants that have geometry ('look-through'); build_crosswalk then uses those
    descendants as the successors of the source version for that mutation.
    """
    succ: dict[int, list[tuple[int, pd.Timestamp]]] = {}
    pred: dict[int, list[tuple[int, pd.Timestamp]]] = {}
    for r in pair.sort_values("date").itertuples():
        if r.to_hist_id != r.from_hist_id:
            succ.setdefault(r.from_hist_id, []).append((r.to_hist_id, r.date))
            pred.setdefault(r.to_hist_id, []).append((r.from_hist_id, r.date))
    sp = split_pairs(pair)
    if sp.empty:
        return pd.DataFrame(columns=["mutation_id", "from_hist_id", "to_hist_id", "weight",
                                     "weight_source", "pop_year", "pop_total"])
    g1 = load_g1()
    years = hectare_years()
    groups = list(sp.groupby(["mutation_id", "from_hist_id"]))
    needed = {pop_year_for(g["date"].iloc[0], years)[0] for _, g in groups}
    points = {y: load_hectare_points(y) for y in sorted(needed)}
    rows = []
    for (mid, fh), g in groups:
        date = g["date"].iloc[0]
        tos = sorted(set(g["to_hist_id"]))
        year, label = pop_year_for(date, years)
        src = geom_at(g1, fh, date - pd.Timedelta(days=1))   # state just before the mutation
        if src is None:
            # transitional source (e.g. Verzasca 2020-10-17, a one-day merger result): its territory
            # is the union of its predecessors just before they were merged into it
            src = _predecessor_geometry(fh, g1, pred)
        if src is None:
            # source itself is a transitional version without geometry; no data is keyed on it in
            # practice, and earlier versions look through it. Equal shares, flagged.
            for t in tos:
                rows.append((mid, fh, t, 1 / len(tos), "equal_no_geometry", None, None))
            continue
        suffix = ""
        if any(geom_at(g1, t, date) is None for t in tos):
            reached = []
            for t in tos:
                reached += _descend_to_geometry(t, date, g1, succ)
            seen, uniq = set(), []
            for h, d in reached:
                if h not in seen:
                    seen.add(h)
                    uniq.append((h, d))
            tos = [h for h, _ in uniq]
            tgeoms = [geom_at(g1, h, d) for h, d in uniq]
            suffix = "_lookthrough"
        else:
            tgeoms = [geom_at(g1, t, date) for t in tos]      # states on the mutation date
        tgt = gpd.GeoDataFrame({"to": tos}, geometry=tgeoms, crs=2056)
        pts = points[year]
        inside = pts[pts.within(src)]
        if inside["pop"].sum() > 0:
            j = gpd.sjoin_nearest(inside, tgt, how="left")
            j = j[~j.index.duplicated()]  # a point on a shared edge counts once
            share = j.groupby("to")["pop"].sum().reindex(tos, fill_value=0.0)
            total = share.sum()
            w = share / total
            src_label = f"{label}_{year}{suffix}"
        else:
            area = np.array([src.intersection(geom).area for geom in tgt.geometry])
            total = None
            w = pd.Series(area / area.sum() if area.sum() > 0 else 1 / len(tos), index=tos)
            src_label = f"area_g1{suffix}"
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
