"""Residents by public transport quality class (ARE ÖV-Güteklassen A–D) per municipality, 2012–2026.

Each year's class polygons (non-overlapping; A best ... D lowest; outside = no class) are
rasterized on the 100 m STATPOP hectare lattice (cell centre inside the polygon) of
pipeline/sources/meteoswiss_climate/zonal.py and combined with the STATPOP hectare residents
(BBTOT) of the same year, or the nearest available year (STATPOP hectares end 2025: the 2026
classes use 2025 residents). Hectares are assigned to the reference-state municipalities (centre
in polygon, else nearest within 500 m).

ARE items are dated in spring of the year (e.g. 2026-03-18) and describe the timetable in force at
that time (timetable year starting in December of the previous year).
Counts per municipality: gk_pop_a .. gk_pop_d, gk_pop_none, and the denominator gk_population;
classes absent from a municipality are explicit zeros (the counts partition the residents).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyogrio
from rasterio.features import rasterize

from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.are_gueteklassen.fetch import YEARS, gpkg_zip
from pipeline.sources.bfs_statpop_geodata.fetch import LAST_YEAR
from pipeline.sources.meteoswiss_climate import zonal

SOURCE = "are_gueteklassen"
CODES = {"A": 1, "B": 2, "C": 3, "D": 4}
COLS = {1: "gk_pop_a", 2: "gk_pop_b", 3: "gk_pop_c", 4: "gk_pop_d", 0: "gk_pop_none"}
LOG: dict = {}


def class_lattice(year: int) -> np.ndarray:
    p = gpkg_zip(year)
    g = pyogrio.read_dataframe(f"/vsizip/{p}/OeV_Gueteklassen_ARE.gpkg", layer="OeV_Gueteklassen_ARE")
    col = [c for c in g.columns if c.lower() == "klasse"][0]
    bad = set(g[col]) - set(CODES)
    if bad:
        raise ValueError(f"Güteklassen {year}: unknown classes {bad}")
    g = g.assign(code=g[col].map(CODES)).sort_values("code", ascending=False)  # A drawn last
    return rasterize(((geom, int(c)) for geom, c in zip(g.geometry, g["code"])),
                     out_shape=(zonal.HEIGHT, zonal.WIDTH), transform=zonal.TRANSFORM, fill=0, dtype="int16")


def observations() -> pd.DataFrame:
    parts = []
    for year in YEARS:
        pop_year = min(year, LAST_YEAR)
        cls = class_lattice(year)
        pop, ids, info = zonal.population(pop_year)
        ok = (ids > 0) & (pop > 0)
        n = int(ids.max()) + 1
        idx = ids[ok]
        w = pop[ok]
        c = cls[ok]
        tot = np.bincount(idx, weights=w, minlength=n)
        units = np.nonzero(tot > 0)[0]
        wide = pd.DataFrame({"bfs_nr": units, "gk_population": tot[units]})
        for code, name in COLS.items():
            wide[name] = np.bincount(idx, weights=w * (c == code), minlength=n)[units]
        wide["period"] = str(year)
        LOG[year] = {"pop_year": pop_year, **{k: float(wide[k].sum()) for k in ["gk_population", *COLS.values()]},
                     "pop_unassigned": info["pop_unassigned"]}
        print(f"gueteklassen {year}:", LOG[year])
        note = f"ARE ÖV-Güteklassen {year}, STATPOP {pop_year} hectares"
        for name in ["gk_population", *COLS.values()]:
            o = emit(wide, {name: name}, "period", SOURCE, precision="exact" if name == "gk_population" else "modelled",
                     provenance="source_current_state")
            o["note"] = note
            parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
