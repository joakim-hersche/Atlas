"""Fetch MeteoSwiss spatial climate normals (yearly grids, 1 km, LV95 GeoTIFF).

STAC collection ch.meteoschweiz.ogd-climate-normals-grid, item 'ch' on data.geo.admin.ch.
Variables: tnorm (mean air temperature °C), rnorm (precipitation mm), snorm (sunshine duration h);
normal periods 1991–2020 ('9120') and 1961–1990 ('6190').
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "meteoswiss_climate"
BASE = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-climate-normals-grid/ch"
PERIODS = {"9120": ("1991-2020", "19910101000000"), "6190": ("1961-1990", "19610101000000")}
VARIABLES = ("tnorm", "rnorm", "snorm")


def grid(var: str, period: str):
    stamp = PERIODS[period][1]
    f = f"ogd-climate-normals-grid.{var}y{period}_ch01r.swiss.lv95_{stamp}_{stamp}.tif"
    return fetch(f"{BASE}/{f}", SOURCE, f)


if __name__ == "__main__":
    for v in VARIABLES:
        for p in PERIODS:
            print(grid(v, p))
