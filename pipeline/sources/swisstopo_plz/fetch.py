"""Download the official directory of localities with postal codes (Amtliches Ortschaftenverzeichnis).

    python -m pipeline.sources.swisstopo_plz.fetch

Asset of the STAC collection ch.swisstopo-vd.ortschaftenverzeichnis_plz (data.geo.admin.ch), CSV in
LV95 (semicolon separated, UTF-8 with BOM). Cached through pipeline.common.fetch in
data/raw/swisstopo_plz/<date>/ with a manifest entry; GB_REFRESH=1 downloads the current release.
"""
from __future__ import annotations

from pathlib import Path

from pipeline.common import fetch

SOURCE = "swisstopo_plz"
STAC = "https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo-vd.ortschaftenverzeichnis_plz"
URL = ("https://data.geo.admin.ch/ch.swisstopo-vd.ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz/"
       "ortschaftenverzeichnis_plz_2056.csv.zip")
FILE = "ortschaftenverzeichnis_plz_2056.csv.zip"
MEMBER = "AMTOVZ_CSV_LV95/AMTOVZ_CSV_LV95.csv"


def directory_zip() -> Path:
    return fetch(URL, SOURCE, FILE)


if __name__ == "__main__":
    print(directory_zip())
