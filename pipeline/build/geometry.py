"""Web geometry for the reference state: municipalities, districts, cantons and BFS analysis levels.

Input: BFS historized generalized boundaries G1 (versions valid on the reference date) and the
spatial levels from the register API. Output (data/out/geo/):
  <level>.topojson   WGS84, topology-preserving simplification (mapshaper), one file per level
  labels.json        label point per unit (pole of inaccessibility) and centroid, per level
and data/interim/geo/units_<ref>.gpkg with full-resolution G1 polygons and attributes.

Levels (brief 4.3): gemeinde, bezirk, kanton, grossregion (REGCH), sprachgebiet (SPRGEB2020),
agglomeration (AGGL2020), arbeitsmarktgebiet (BAE2018), stadt_land (STALAN2020).
"""
from __future__ import annotations

import json
import subprocess

import geopandas as gpd
import pandas as pd
from shapely.ops import polylabel

from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.sources.bfs_hist_boundaries.fetch import fetch_all as fetch_bounds

MAPSHAPER = ["npx", "--yes", "mapshaper@0.7.101"]
# level id -> (levels-table column, label column)
ANALYSIS_LEVELS = {
    "grossregion": ("REGCH", "REGCH_de"),
    "sprachgebiet": ("SPRGEB2020", "SPRGEB2020_de"),
    "agglomeration": ("AGGL2020", "AGGL2020_de"),
    "arbeitsmarktgebiet": ("BAE2018", "BAE2018_de"),
    "stadt_land": ("STALAN2020", "STALAN2020_de"),
}
# simplification: share of vertices kept, per output detail
DETAIL = {"gemeinde": "40%", "bezirk": "30%", "kanton": "20%"}
DEFAULT_DETAIL = "25%"


def current_units() -> gpd.GeoDataFrame:
    g = gpd.read_file(fetch_bounds()["g1"])
    ref = pd.Timestamp(REFERENCE_DATE)
    vf = pd.to_datetime(g["VALID_FROM"])
    vt = pd.to_datetime(g["VALID_TO"])
    g = g[(vf <= ref) & (vt.isna() | (vt >= ref))]
    return g


def _label_points(gdf: gpd.GeoDataFrame, id_col: str) -> list[dict]:
    pts = []
    wgs = gdf.to_crs(4326)
    for (_, row), geom_lv95 in zip(wgs.iterrows(), gdf.geometry):
        poly = max(geom_lv95.geoms, key=lambda p: p.area) if geom_lv95.geom_type == "MultiPolygon" else geom_lv95
        lab = gpd.GeoSeries([polylabel(poly, tolerance=25)], crs=2056).to_crs(4326).iloc[0]
        cen = row.geometry.centroid
        pts.append({"id": str(row[id_col]), "label": [round(lab.x, 5), round(lab.y, 5)],
                    "centroid": [round(cen.x, 5), round(cen.y, 5)]})
    return pts


def _to_topojson(gdf: gpd.GeoDataFrame, level: str, keep: str) -> str:
    src = interim_path("geo", f"{level}.geojson")
    gdf.to_crs(4326).to_file(src, driver="GeoJSON")
    dst = out_path("geo", f"{level}.topojson")
    cmd = [*MAPSHAPER, str(src), "-simplify", keep, "keep-shapes", "-clean",
           "-o", str(dst), "format=topojson", "quantization=100000", "force"]
    subprocess.run(cmd, check=True, capture_output=True)
    return str(dst)


def run() -> dict:
    g = current_units()
    ref = REFERENCE_DATE.isoformat()
    mun = g[g["GARTE"] == 11].copy()
    lakes = g[g["GARTE"] != 11].copy()
    levels = pd.read_parquet(interim_path("backbone", f"levels_{ref}.parquet"))
    mun = mun.merge(levels, left_on="GDENR", right_on="BfsCode", how="left")
    mun = mun.rename(columns={"GDENR": "id", "GDENAME": "name", "KTKZ": "canton", "BEZNR": "district"})
    keep_cols = ["id", "name", "canton", "KTNR", "district", "GDEHISTID", "Z_AVG", "Z_MED", "Z_MIN", "Z_MAX",
                 *[c for c, _ in ANALYSIS_LEVELS.values()], "geometry"]
    mun = mun[[c for c in keep_cols if c in mun.columns]]
    mun.to_file(interim_path("geo", f"units_{ref}.gpkg"), layer="gemeinde", driver="GPKG")

    out = {"gemeinde": _to_topojson(mun[["id", "name", "canton", "district", "geometry"]], "gemeinde", DETAIL["gemeinde"])}
    labels = {"gemeinde": _label_points(mun, "id")}

    dissolves = {"bezirk": ("district", None), "kanton": ("canton", None)}
    dissolves.update({k: v for k, v in ANALYSIS_LEVELS.items()})
    for level, (col, label_col) in dissolves.items():
        if col not in mun.columns:
            continue
        d = mun[[col, "geometry"]].dropna(subset=[col]).dissolve(by=col, as_index=False)
        d = d.rename(columns={col: "id"})
        d["id"] = d["id"].astype(str)
        if label_col and label_col in levels.columns:
            names = levels.drop_duplicates(col).set_index(levels.drop_duplicates(col)[col].astype(str))[label_col]
            d["name"] = d["id"].map(names)
        d.to_file(interim_path("geo", f"units_{ref}.gpkg"), layer=level, driver="GPKG")
        out[level] = _to_topojson(d, level, DETAIL.get(level, DEFAULT_DETAIL))
        labels[level] = _label_points(d, "id")
    if not lakes.empty:
        lk = lakes[["SEENAME", "geometry"]].rename(columns={"SEENAME": "name"})
        out["lakes"] = _to_topojson(lk, "lakes", "20%")
    lp = out_path("geo", "labels.json")
    lp.write_text(json.dumps(labels, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    out["labels"] = str(lp)
    return out


if __name__ == "__main__":
    import os
    for k, v in run().items():
        print(f"{k:20s} {os.path.getsize(v)/1024:8.0f} KB  {v}")
