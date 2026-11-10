"""Fetch the FOCA/BAZL noise pollution register for civil aerodromes (Lärmbelastungskataster der
Zivilflugplätze) from data.geo.admin.ch: GeoPackage with the noise exposure curves (isolines, LV95).

STAC collection ch.bazl.laermbelastungskataster-zivilflugplaetze (item date 2025-04-28, updated 2025-12-11).
Licence link of the collection: https://opendata.swiss/en/terms-of-use/#terms_by (open use, source must be provided).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bazl_aircraft_noise"
BASE = "https://data.geo.admin.ch"
COLL = "ch.bazl.laermbelastungskataster-zivilflugplaetze"
NAME = "laermbelastungskataster-zivilflugplaetze"


def gpkg():
    return fetch(f"{BASE}/{COLL}/{NAME}/{NAME}_2056.gpkg", SOURCE, f"{NAME}_2056.gpkg")


def stac():
    return fetch(f"{BASE}/api/stac/v1/collections/{COLL}", SOURCE, f"stac_{NAME}.json")


if __name__ == "__main__":
    print(stac(), gpkg())
