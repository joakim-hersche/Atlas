"""Fetch ASTRA road traffic accidents with personal injury (point locations, 2011–latest).

STAC collection ch.astra.unfaelle-personenschaeden_alle on data.geo.admin.ch (CSV in zip, LV95).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "astra_accidents"
BASE = "https://data.geo.admin.ch/ch.astra.unfaelle-personenschaeden_alle/unfaelle-personenschaeden_alle"


def accidents():
    f = "unfaelle-personenschaeden_alle_2056.csv.zip"
    return fetch(f"{BASE}/{f}", SOURCE, f)


if __name__ == "__main__":
    print(accidents())
