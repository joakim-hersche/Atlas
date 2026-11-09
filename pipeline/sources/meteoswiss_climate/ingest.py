"""Climate normals per municipality from the MeteoSwiss 1 km grids (zonal statistics).

Grids: yearly normals of mean temperature (°C), precipitation (mm) and relative sunshine duration
(% of the maximum possible; NetCDF long_name 'mean yearly sunshine duration ... relative to max
possible'), normal periods 1991–2020 and 1961–1990 (period strings '1991-2020', '1961-1990').
Two variants per variable (see zonal.py for the 100 m lattice):
  *_pop   mean over the STATPOP 2025 population hectares, weighted by residents: the climate where
          people live (mountain municipalities are not dominated by uninhabited peaks).
          Aggregation weighted_mean:pop_total.
  *_area  plain area mean over the municipal territory (100 m cells, incl. lakes covered by the
          grid). Higher levels: weighted by total area.
Each 100 m cell takes the value of the 1 km grid cell containing its centre.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.sources.meteoswiss_climate import zonal
from pipeline.sources.meteoswiss_climate.fetch import PERIODS, grid

SOURCE = "meteoswiss_climate"
POP_YEAR = 2025
VARS = {"tnorm": "clim_temp", "rnorm": "clim_precip", "snorm": "clim_sunshine"}


def observations() -> pd.DataFrame:
    ids = zonal.municipality_ids()
    pop, pop_ids, info = zonal.population(POP_YEAR)
    print("climate: population assignment", info)
    parts = []
    for var, mid in VARS.items():
        for code, (label, _) in PERIODS.items():
            vals = zonal.sample(grid(var, code))
            for suffix, (cells, w) in {"pop": (pop_ids, pop), "area": (ids, None)}.items():
                z = zonal.zonal_mean(vals, cells, w)
                z["period"] = label
                o = emit(z, {"value": f"{mid}_{suffix}"}, "period", SOURCE, precision="modelled",
                         provenance="source_current_state")
                o["note"] = (f"weighted by STATPOP {POP_YEAR} residents per hectare" if suffix == "pop"
                             else "area mean over 100 m cells")
                parts.append(o)
    out = pd.concat(parts, ignore_index=True)
    # every municipality must have a value; report if not
    n = out.groupby("metric_id")["unit_id"].nunique()
    if (n < 2110).any():
        print("climate: municipalities without value", n[n < 2110].to_dict())
    return out
