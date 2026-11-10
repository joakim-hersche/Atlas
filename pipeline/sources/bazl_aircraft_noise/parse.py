"""Population exposure to civil aircraft noise per municipality (FOCA/BAZL noise cadastre of civil aerodromes).

Method (documented in metrics.yaml and meta.yaml)
- Inputs: the closed noise exposure curves (isolines, LV95) of the cadastre, the public GWR building register
  (building coordinates, dwellings, construction year) and the STATPOP 2021 hectare population; the residents are
  assigned to buildings exactly as in bafu_noise (hectare residents spread over residential buildings by dwellings;
  hectares without such a building at the hectare centre).
- Curves used: "OverallTrafficDay_Lr" (small and large aircraft, 06-22 h, Lr) at 60 dB(A), and "FirstNightHour_Lr"
  (22-23 h) at 55 dB(A): the immission limit values (IGW) of sensitivity level II (residential zones) of Annex 5
  LSV (SR 814.41), as stated by the canton of Zürich for the Zürich airport area limit line ("mehr als 60 Dezibel
  am Tag oder 55 Dezibel in der Nacht (oder beides)"). Second and last night hour are not used (limit value not
  confirmed from a primary text).
- A resident counts as exposed when the building coordinate lies inside a closed curve of the given level of any
  aerodrome. Curves of different aerodromes have different dates and calculation bases (cadastre per aerodrome).
- Aerodromes in the cadastre: Zürich, Genève, Basel-Mulhouse, Bern, Lugano-Agno, Saanen, Samedan, St. Gallen-
  Altenrhein (+ one military curve set, Locarno). Aerodromes without a cadastre entry are not covered, and the
  cadastre is an inventory (no direct legal effect, FOCA), not the official count of people above the limit.
Everything is a model: precision "modelled".
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.helpers import emit
from pipeline.sources.bafu_noise.parse import levels
from pipeline.sources.bazl_aircraft_noise.fetch import gpkg
from pipeline.sources.meteoswiss_climate import zonal

SOURCE = "bazl_aircraft_noise"
POP_YEAR = 2021
# Cantons with an aerodrome of the cadastre (Zürich, Genève, Bern + Saanen, Lugano-Agno, Samedan, St. Gallen-
# Altenrhein, Basel-Mulhouse: the airport lies in France, its curves reach BS/BL only marginally if at all).
# Values are emitted for the municipalities of these cantons only: elsewhere the cadastre says nothing about
# aerodromes it does not contain (e.g. Grenchen, Lausanne, Sion, military airfields).
COVERED_CANTONS = ("ZH", "GE", "BE", "TI", "GR", "SG", "BS")
LAYERS = {"day": ("OverallTrafficDay_Lr", 60.0), "night1": ("FirstNightHour_Lr", 55.0)}


def curves(layer: str, level: float) -> gpd.GeoDataFrame:
    """Closed curves of exactly `level` dB(A) in one layer, one polygon per ring, with the aerodrome name."""
    g = gpd.read_file(gpkg(), layer=layer)
    g["lvl"] = pd.to_numeric(g["LEVEL_DB"], errors="coerce")
    g = g[(g["lvl"] == level) & g.geometry.apply(lambda x: x is not None and x.geom_type == "LineString" and x.is_closed)]
    g = g[g.geometry.apply(lambda x: len(x.coords) >= 4)]
    return gpd.GeoDataFrame({"aerodrome": g["REG_NAME"].to_numpy()},
                            geometry=[Polygon(x.coords) for x in g.geometry], crs=g.crs)


def inside(e: np.ndarray, n: np.ndarray, polys: gpd.GeoDataFrame) -> np.ndarray:
    """Boolean per point: inside the union of the polygons."""
    u = unary_union(list(polys.geometry))
    return shapely.contains_xy(u, e, n)


def residents_points() -> pd.DataFrame:
    """One row per residential building / fallback hectare centre with coordinates and residents."""
    pop, ids, info = zonal.population(POP_YEAR)
    b, h = levels()
    ok = (b["row"] >= 0) & (b["row"] < zonal.HEIGHT) & (b["col"] >= 0) & (b["col"] < zonal.WIDTH)
    b = b[ok].copy()
    key = b["row"] * zonal.WIDTH + b["col"]
    b["residents"] = pop[b["row"], b["col"]] * b["GANZWHG"] / b.groupby(key)["GANZWHG"].transform("sum")
    b = b[b["residents"] > 0]
    h = h.copy()
    h["residents"] = pop[h["row"], h["col"]]
    cols = ["row", "col", "GKODE", "GKODN", "residents"]
    t = pd.concat([b[cols], h[cols]], ignore_index=True)
    t["bfs_nr"] = ids[t["row"], t["col"]]
    return t[t["bfs_nr"] > 0].reset_index(drop=True)


def exposure(t: pd.DataFrame, flags: dict[str, np.ndarray]) -> pd.DataFrame:
    """Per municipality: residents, and residents flagged by day / night1 / either."""
    d = pd.DataFrame({"bfs_nr": t["bfs_nr"].to_numpy(), "residents": t["residents"].to_numpy()})
    d["day"] = d["residents"] * flags["day"]
    d["night1"] = d["residents"] * flags["night1"]
    d["any"] = d["residents"] * (flags["day"] | flags["night1"])
    return d.groupby("bfs_nr", as_index=False).sum()


METRICS = {"residents": "aircraft_noise_residents", "day": "aircraft_day_60_residents",
           "night1": "aircraft_night_55_residents", "any": "aircraft_igw2_residents"}


def covered_municipalities() -> set[int]:
    g = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde")
    return set(g.loc[g["canton"].isin(COVERED_CANTONS), "id"].astype(int))


def observations() -> pd.DataFrame:
    t = residents_points()
    e, n = t["GKODE"].to_numpy(), t["GKODN"].to_numpy()
    flags = {k: inside(e, n, curves(*v)) for k, v in LAYERS.items()}
    x = exposure(t, flags)
    x = x[x["bfs_nr"].isin(covered_municipalities())]
    x["period"] = "2021"
    o = emit(x, METRICS, "period", SOURCE, precision="modelled", provenance="source_current_state")
    o["note"] = "BAZL noise cadastre curves (2025), GWR buildings, STATPOP 2021 hectares; modelled (see description)"
    o.loc[o["metric_id"] == "aircraft_noise_residents", "precision"] = "exact"
    o.loc[o["metric_id"] == "aircraft_noise_residents", "note"] = "STATPOP 2021 hectare residents assigned to the municipality"
    return o
