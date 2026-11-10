"""Area of each municipality in federal landscape inventories, parks and biotope inventories
(BAFU, current state), by polygon overlay with the reference-state boundaries.

Municipality polygons: swissBOUNDARIES3D 2026-01 (layer tlm_hoheitsgebiet, objektart
Gemeindegebiet, = the 2110 reference municipalities; lake parts inside a municipality included),
via pipeline/sources/geo_identity/fetch.py. Areas are planimetric (2D) in LV95; the denominator
pa_municipal_area_ha is the 2D area of the same polygon, so shares are consistent.

  pa_bln_ha       BLN (Federal Inventory of Landscapes and Natural Monuments), state 2022-11-15
  pa_parks_ha     Swiss National Park and parks of national importance (park perimeters: regional
                  nature parks, nature discovery parks, national park), state 2025-04-30
  pa_biotopes_ha  union of the five federal biotope inventories (NHG Art. 18a): raised bogs, fens,
                  floodplains, amphibian spawning sites (area objects), dry grasslands; states
                  2022–2026. Annex objects not in force (floodplain annex 2) and point objects
                  (amphibian migration sites) are not included.
Each category is dissolved first, so overlapping objects are counted once. Municipalities without
an object get 0 (the inventories are complete national lists).
"""
from __future__ import annotations

import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely

from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bafu_protected_areas.fetch import BIOTOPES, BLN, PARKS, shp_zip
from pipeline.sources.geo_identity.fetch import swissboundaries

SOURCE = "bafu_protected_areas"
PERIOD = "2026"
GPKG = "swissBOUNDARIES3D_1_5_LV95_LN02.gpkg"
LOG: dict = {}


def municipalities() -> gpd.GeoDataFrame:
    g = pyogrio.read_dataframe(f"/vsizip/{swissboundaries()}/{GPKG}", layer="tlm_hoheitsgebiet",
                               columns=["bfs_nummer", "icc", "objektart"])
    g = g[(g["icc"] == "CH") & (g["objektart"] == "Gemeindegebiet")]
    g = g.assign(bfs_nr=g["bfs_nummer"].astype(int), geometry=shapely.force_2d(g.geometry.values))
    return gpd.GeoDataFrame(g[["bfs_nr"]], geometry=g.geometry, crs=2056).dissolve("bfs_nr").reset_index()


def _layers(name: str, exclude=("Anhang", "Wanderobjekt")) -> list[gpd.GeoDataFrame]:
    p = shp_zip(name)
    out = []
    for s in zipfile.ZipFile(p).namelist():
        if s.endswith(".shp") and not any(x in s for x in exclude):
            g = pyogrio.read_dataframe(f"/vsizip/{p}/{s}")
            if "ParkPerimeter" not in s and name == PARKS:
                continue  # zones layer duplicates the perimeters
            LOG[s] = len(g)
            out.append(g)
    return out


def _union(names: list[str]):
    geoms = [shapely.force_2d(shapely.make_valid(g.geometry.values)) for n in names for g in _layers(n)]
    return shapely.union_all(np.concatenate(geoms))


def _overlay_ha(mun: gpd.GeoDataFrame, geom) -> np.ndarray:
    parts = shapely.get_parts(geom)
    tree = shapely.STRtree(parts)
    out = np.zeros(len(mun))
    for i, mg in enumerate(mun.geometry.values):
        idx = tree.query(mg, predicate="intersects")
        if len(idx):
            out[i] = shapely.area(shapely.intersection(mg, parts[idx])).sum() / 1e4
    return out


def observations() -> pd.DataFrame:
    mun = municipalities()
    if len(mun) != 2110:
        raise ValueError(f"expected 2110 municipalities, got {len(mun)}")
    wide = pd.DataFrame({"bfs_nr": mun["bfs_nr"], "pa_municipal_area_ha": mun.area / 1e4})
    for col, names in (("pa_bln_ha", [BLN]), ("pa_parks_ha", [PARKS]), ("pa_biotopes_ha", BIOTOPES)):
        u = _union(names)
        wide[col] = np.minimum(_overlay_ha(mun, u), wide["pa_municipal_area_ha"])
        LOG[col] = {"union_ha": u.area / 1e4, "sum_ha": float(wide[col].sum())}
        print(col, LOG[col])
    wide["period"] = PERIOD
    parts = []
    for col in ["pa_municipal_area_ha", "pa_bln_ha", "pa_parks_ha", "pa_biotopes_ha"]:
        o = emit(wide, {col: col}, "period", SOURCE, precision="exact" if col == "pa_municipal_area_ha" else "modelled",
                 provenance="source_current_state")
        o["note"] = "swissBOUNDARIES3D 2026-01 polygon (2D)" if col == "pa_municipal_area_ha" else "BAFU inventory overlay, current state"
        parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
