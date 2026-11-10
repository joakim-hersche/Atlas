"""Fetch BAFU federal inventories and protected areas (shapefile zips, LV95) from data.geo.admin.ch.

One STAC item per collection (current state):
  bundesinventare-bln                       Federal Inventory of Landscapes and Natural Monuments
  schutzgebiete-paerke_nationaler_bedeutung Swiss National Park and parks of national importance
  bundesinventare-hochmoore, -flachmoore, -auen, -amphibien, -trockenwiesen_trockenweiden
                                            the five federal biotope inventories (NHG Art. 18a)
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bafu_protected_areas"
BASE = "https://data.geo.admin.ch"
BLN = "bundesinventare-bln"
PARKS = "schutzgebiete-paerke_nationaler_bedeutung"
BIOTOPES = ["bundesinventare-hochmoore", "bundesinventare-flachmoore", "bundesinventare-auen",
            "bundesinventare-amphibien", "bundesinventare-trockenwiesen_trockenweiden"]
ALL = [BLN, PARKS, *BIOTOPES]


def shp_zip(name: str):
    f = f"{name}_2056.shp.zip"
    return fetch(f"{BASE}/ch.bafu.{name}/{name}/{f}", SOURCE, f)


if __name__ == "__main__":
    for n in ALL:
        print(shp_zip(n))
