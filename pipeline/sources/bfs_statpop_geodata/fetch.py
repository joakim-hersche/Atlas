"""Fetch BFS STATPOP geodata: per-municipality tables and the population hectare grid.

STAC collection ch.bfs.statistik-bevoelkerung_haushalte on data.geo.admin.ch.
  1990, 2000: hectare CSV in LV03 (EPSG:21781)
  2010–latest: hectare and municipality files in LV95 (EPSG:2056), municipality files with GDEHISTID
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_statpop_geodata"
BASE = "https://data.geo.admin.ch/ch.bfs.statistik-bevoelkerung_haushalte"
HA_YEARS_LV03 = (1990, 2000)
FIRST_LV95_YEAR, LAST_YEAR = 2010, 2025


def _name(year: int, kind: str, crs: int, ext: str) -> str:
    return f"statistik-bevoelkerung_haushalte_{year}_{kind}_{crs}.{ext}"


def hectare(year: int):
    if year in HA_YEARS_LV03:
        f = _name(year, "ha", 21781, "csv")
    else:
        f = _name(year, "ha", 2056, "parquet")
    return fetch(f"{BASE}/statistik-bevoelkerung_haushalte_{year}/{f}", SOURCE, f)


def municipalities(year: int):
    f = _name(year, "gmde", 2056, "parquet")
    return fetch(f"{BASE}/statistik-bevoelkerung_haushalte_{year}/{f}", SOURCE, f)


def hectare_years() -> list[int]:
    return [*HA_YEARS_LV03, *range(FIRST_LV95_YEAR, LAST_YEAR + 1)]


if __name__ == "__main__":
    for y in hectare_years():
        print(y, hectare(y))
    for y in range(FIRST_LV95_YEAR, LAST_YEAR + 1):
        print(y, municipalities(y))
