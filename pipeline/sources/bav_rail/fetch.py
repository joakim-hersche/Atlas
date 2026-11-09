"""Fetch the BAV rail network (Schienennetz) GeoPackage from the geo.admin.ch STAC.

Layers: Netzsegment (lines), Netzknoten (nodes, Betriebspunkt_Nummer = didok number),
KmLinie, Fehlerprofil. LV95 (EPSG:2056).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bav_rail"
URL = "https://data.geo.admin.ch/ch.bav.schienennetz/schienennetz/schienennetz_2056_de.gpkg"


def schienennetz():
    return fetch(URL, SOURCE, "schienennetz_2056_de.gpkg")


if __name__ == "__main__":
    print(schienennetz())
