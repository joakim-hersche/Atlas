"""Fine boundaries for the zoomed-in map: municipalities, districts and cantons.

The generalized files (pipeline/build/geometry.py) come from the BFS G1 boundaries, which are drawn at
web scale: about 490 m between vertices, too coarse at street level. The finer outlines come from
swissBOUNDARIES3D (swisstopo, release 2026-01), the source of the municipal areas (geo_identity): the
cadastral boundaries, accuracy +-0.5 m, 1:1 on the BFS number for the reference state's 2,110 municipalities.
Licence: swisstopo OGD, free use with source attribution (pipeline/licence_review.yaml, geo_identity).

Consistency with the generalized files, so that the map data joins unchanged:
  * ids: the BFS number (municipalities), the district number as text (districts), the canton code
    (cantons), exactly as in <level>.topojson. District and canton membership is taken from the
    generalized units (data/interim/geo/units_<ref>.gpkg), not recomputed.
  * lakes: swissBOUNDARIES3D municipalities include their lake share, the G1 ones do not (lakes are a
    separate layer in the app). The G1 lake polygons are cut out of the fine municipalities, so the two
    layers cover the same ground and the lakes layer stays valid.
  * topology: shared borders are simplified once (mapshaper, topology-preserving), and districts and
    cantons are dissolved from the same fine municipalities.

Output (data/out/geo/): gemeinde_fine.topojson, bezirk_fine.topojson, kanton_fine.topojson
(WGS84, only the `id` property). The generalized files are not touched.
Run: python -m pipeline.build.geometry_fine   (part of `make geometry`)
"""
from __future__ import annotations

import subprocess

import geopandas as gpd
import pandas as pd
import shapely

from pipeline.build.geometry import MAPSHAPER, current_units
from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.sources.geo_identity.fetch import swissboundaries

GPKG = "swissBOUNDARIES3D_1_5_LV95_LN02.gpkg"
LEVELS = ("gemeinde", "bezirk", "kanton")
# Douglas-Peucker tolerance in metres: 8 m keeps street-level shape (borders along streams and roads)
# at about a third of the vertices of the cadastral outline; 1:1 pixels at zoom 12 are about 20 m.
INTERVAL_M = 8
# 500,000 steps across Switzerland: about 1 m
QUANTIZATION = 500_000


def fine_municipalities() -> gpd.GeoDataFrame:
    """swissBOUNDARIES3D municipalities (LV95, 2D) without the lake areas, id = BFS number."""
    h = gpd.read_file(f"/vsizip/{swissboundaries()}/{GPKG}", layer="tlm_hoheitsgebiet")
    m = h[(h["icc"] == "CH") & (h["objektart"] == "Gemeindegebiet")][["bfs_nummer", "geometry"]].copy()
    m["geometry"] = shapely.force_2d(m.geometry.values)
    g = current_units()
    lakes = g[g["GARTE"] == 13].geometry.union_all()
    m["geometry"] = m.geometry.difference(lakes)
    m = m.rename(columns={"bfs_nummer": "id"}).astype({"id": int})
    return m.reset_index(drop=True)


def _write(gdf: gpd.GeoDataFrame, level: str) -> str:
    src = interim_path("geo", f"{level}_fine.geojson")
    gdf.to_crs(4326).to_file(src, driver="GeoJSON")
    dst = out_path("geo", f"{level}_fine.topojson")
    # no -clean after -simplify: it rebuilds the arcs from the unsimplified input
    cmd = [*MAPSHAPER, str(src), "-simplify", "dp", f"interval={INTERVAL_M}", "keep-shapes",
           "-rename-layers", level,   # the TopoJSON object keeps the level's name, as in <level>.topojson
           "-o", str(dst), "format=topojson", f"quantization={QUANTIZATION}", "force"]
    subprocess.run(cmd, check=True, capture_output=True)
    return str(dst)


def run() -> dict[str, str]:
    ref = REFERENCE_DATE.isoformat()
    mun = fine_municipalities()
    coarse = gpd.read_file(interim_path("geo", f"units_{ref}.gpkg"), layer="gemeinde")[["id", "canton", "district"]]
    coarse["id"] = coarse["id"].astype(int)
    if set(coarse["id"]) != set(mun["id"]):
        missing = sorted(set(coarse["id"]) ^ set(mun["id"]))
        raise RuntimeError(f"swissBOUNDARIES3D and the generalized units differ in ids: {missing[:10]}")
    mun = mun.merge(coarse, on="id", how="left")

    out = {"gemeinde": _write(mun[["id", "geometry"]], "gemeinde")}
    for level, col in (("bezirk", "district"), ("kanton", "canton")):
        d = mun[[col, "geometry"]].dissolve(by=col, as_index=False).rename(columns={col: "id"})
        d["id"] = d["id"].astype(int).astype(str) if level == "bezirk" else d["id"].astype(str)
        out[level] = _write(d, level)
    return out


if __name__ == "__main__":
    import gzip
    import os
    for k, v in run().items():
        raw = os.path.getsize(v)
        with open(v, "rb") as fh:
            gz = len(gzip.compress(fh.read(), 9))
        print(f"{k:10s} {raw/1024:8.0f} KB raw {gz/1024:8.0f} KB gzip  {v}")
