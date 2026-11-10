"""Fetch the BAFU sonBASE noise exposure grids (GeoTIFF, LV95) from data.geo.admin.ch.

Collections ch.bafu.laerm-strassenlaerm_tag|nacht and ch.bafu.laerm-bahnlaerm_tag|nacht (state 2021 traffic data,
published 2025/2026). Licence link of the STAC collections: https://opendata.swiss/en/terms-of-use/#terms_by
(open use, source must be provided).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bafu_noise"
BASE = "https://data.geo.admin.ch"
KINDS = {"road_day": "strassenlaerm_tag", "road_night": "strassenlaerm_nacht",
         "rail_day": "bahnlaerm_tag", "rail_night": "bahnlaerm_nacht"}


def grid(kind: str):
    c = f"laerm-{KINDS[kind]}"
    return fetch(f"{BASE}/ch.bafu.{c}/{c}/{c}_2056.tif", SOURCE, f"{c}_2056.tif")


def docs(kind: str):
    c = f"laerm-{KINDS[kind]}"
    return fetch(f"{BASE}/ch.bafu.{c}/{c}/{c}.zip", SOURCE, f"{c}.zip")


def stac(kind: str):
    c = f"laerm-{KINDS[kind]}"
    return fetch(f"{BASE}/api/stac/v1/collections/ch.bafu.{c}", SOURCE, f"stac_{c}.json")


if __name__ == "__main__":
    for k in KINDS:
        print(stac(k), docs(k), grid(k))
