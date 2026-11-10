"""Population exposure to NO2, PM10 and PM2.5 per municipality (BAFU modelled annual mean maps).

For each pollutant and year (NO2, PM10: 2010, 2015, 2020, 2025; PM2.5: 2015, 2020, 2025):
- the grid is brought to the 100 m STATPOP hectare lattice (pipeline/sources/meteoswiss_climate/
  zonal.py): finer grids (20 m NO2 from 2020, 100 m) are block-averaged, 200 m grids (before 2020)
  are sampled at the hectare centre;
- population-weighted mean over the populated hectares of the municipality, with the STATPOP
  hectare population of the same year;
- residents living in hectares above the annual limit of the Ordinance on Air Pollution Control
  (LRV; values stated in the BAFU collection descriptions on data.geo.admin.ch): NO2 30 µg/m³,
  PM10 20 µg/m³, PM2.5 10 µg/m³ (strictly greater than the limit).
The hectare residents are delivered as the denominator (air_hectare_residents), so the share above
the limit and the higher-level means are exact re-aggregations.
Grid resolution changes (200 m -> 20/100 m in 2020) make the series not strictly comparable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import rasterio

from pipeline.harmonize.helpers import emit
from pipeline.sources.bafu_air.fetch import YEARS, grid
from pipeline.sources.meteoswiss_climate import zonal

SOURCE = "bafu_air"
LIMITS = {"no2": 30.0, "pm10": 20.0, "pm25": 10.0}


def _lattice(path) -> tuple[np.ndarray, float]:
    with rasterio.open(path) as r:
        res = r.transform.a
    if res <= zonal.RES and (zonal.RES / res).is_integer():
        return zonal.block_mean_100m(path), res
    return zonal.sample(path), res


def observations() -> pd.DataFrame:
    parts = []
    denom_done = set()
    for pol, years in YEARS.items():
        for year in years:
            vals, res = _lattice(grid(pol, year))
            pop, ids, info = zonal.population(year)
            lost = float(pop[(ids > 0) & ~np.isfinite(vals)].sum())
            print(f"air {pol} {year}: grid {res:g} m, residents without value {lost:.0f}", info)
            note = f"BAFU {res:g} m grid, STATPOP {year} hectares"
            z = zonal.zonal_mean(vals, ids, pop).assign(period=str(year))
            a = zonal.share_above(vals, ids, pop, LIMITS[pol]).assign(period=str(year))
            o1 = emit(z, {"value": f"air_{pol}_pop"}, "period", SOURCE, precision="modelled",
                      provenance="source_current_state")
            o2 = emit(a, {"above": f"air_{pol}_above_limit_residents"}, "period", SOURCE,
                      precision="modelled", provenance="source_current_state")
            o1["note"] = o2["note"] = note
            parts += [o1, o2]
            if year not in denom_done:
                tot = zonal.zonal_mean(np.zeros_like(pop), ids, pop)  # weight = residents per id
                tot = tot.assign(period=str(year))
                o3 = emit(tot, {"weight": "air_hectare_residents"}, "period", SOURCE, precision="exact",
                          provenance="source_current_state")
                o3["note"] = f"STATPOP {year} hectare residents assigned to the municipality"
                parts.append(o3)
                denom_done.add(year)
    return pd.concat(parts, ignore_index=True)
