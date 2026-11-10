"""Fetch BAFU modelled annual mean air pollutant maps (GeoTIFF, LV95) from data.geo.admin.ch.

Collections ch.bafu.luftreinhaltung-stickstoffdioxid (NO2, since 1990), -feinstaub_pm10 (since 1998),
-feinstaub_pm2_5 (since 2015); one item per year. Grid size varies by year (200 m in older years,
finer in recent years), read from each file.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bafu_air"
BASE = "https://data.geo.admin.ch"
COLLECTIONS = {"no2": "luftreinhaltung-stickstoffdioxid", "pm10": "luftreinhaltung-feinstaub_pm10",
               "pm25": "luftreinhaltung-feinstaub_pm2_5"}
YEARS = {"no2": [2010, 2015, 2020, 2025], "pm10": [2010, 2015, 2020, 2025], "pm25": [2015, 2020, 2025]}


def grid(pollutant: str, year: int):
    c = COLLECTIONS[pollutant]
    f = f"{c}_{year}_2056.tif"
    return fetch(f"{BASE}/ch.bafu.{c}/{c}_{year}/{f}", SOURCE, f)


if __name__ == "__main__":
    for p, ys in YEARS.items():
        for y in ys:
            print(grid(p, y))
