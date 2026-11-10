"""Fetch the ARE public transport quality classes (ÖV-Güteklassen A–D), one GeoPackage per year.

STAC collection ch.are.gueteklassen_oev on data.geo.admin.ch; items gueteklassen_oev_<year>
(2012–2026, timetable state of the item's date in spring), asset gueteklassen_oev_<year>_2056.gpkg.zip.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "are_gueteklassen"
BASE = "https://data.geo.admin.ch/ch.are.gueteklassen_oev"
YEARS = list(range(2012, 2027))


def gpkg_zip(year: int):
    f = f"gueteklassen_oev_{year}_2056.gpkg.zip"
    return fetch(f"{BASE}/gueteklassen_oev_{year}/{f}", SOURCE, f)


if __name__ == "__main__":
    for y in YEARS:
        print(y, gpkg_zip(y))
