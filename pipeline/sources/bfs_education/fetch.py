"""Fetch BFS education data per municipality.

1. Bildungsstand – Geodaten (STAC ch.bfs.bildungsstand): highest completed education of the
   permanent resident population aged 25-64, per municipality, years 1990, 2000, 2017-latest.
2. LABB – Sekundarstufe II by municipality of residence at age 15 (DAM asset 36811719, zip).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_education"
BASE = "https://data.geo.admin.ch/ch.bfs.bildungsstand"
YEARS = [1990, 2000, *range(2017, 2024)]
LABB_URL = "https://dam-api.bfs.admin.ch/hub/api/dam/assets/36811719/master"


def attainment(year: int):
    f = f"bildungsstand_{year}_gmde_2056.csv"
    return fetch(f"{BASE}/bildungsstand_{year}/{f}", SOURCE, f)


def attainment_all():
    f = "bildungsstand_gmde_2056.csv"
    return fetch(f"{BASE}/bildungsstand/{f}", SOURCE, f)


def labb():
    return fetch(LABB_URL, SOURCE, "labb_sek2_36811719.zip")
