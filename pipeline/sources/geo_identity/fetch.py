"""Fetch swissBOUNDARIES3D (swisstopo) for municipality area figures (decision D19: area only).

STAC collection ch.swisstopo.swissboundaries3d on data.geo.admin.ch; one item per release.
The GeoPackage is read directly from the cached zip (/vsizip/), nothing is extracted.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "geo_identity"
RELEASE = "2026-01"
BASE = "https://data.geo.admin.ch/ch.swisstopo.swissboundaries3d"


def swissboundaries(release: str = RELEASE):
    f = f"swissboundaries3d_{release}_2056_5728.gpkg.zip"
    return fetch(f"{BASE}/swissboundaries3d_{release}/{f}", SOURCE, f)


if __name__ == "__main__":
    print(swissboundaries())
