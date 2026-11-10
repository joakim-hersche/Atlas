"""Fetch the BFS accessibility hectare grid (Erreichbarkeit von Dienstleistungen) from
data.geo.admin.ch (STAC collection ch.bfs.erreichbarkeit, one item 'erreichbarkeit').

erreichbarkeit_2056.csv: one row per inhabited hectare and year (2011, 2015, 2018, 2021), LV95,
semicolon-separated, distances in metres. erreichbarkeit.zip: the data description.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_accessibility"
BASE = "https://data.geo.admin.ch/ch.bfs.erreichbarkeit/erreichbarkeit"


def grid_csv():
    return fetch(f"{BASE}/erreichbarkeit_2056.csv", SOURCE, "erreichbarkeit_2056.csv")


def description_zip():
    return fetch(f"{BASE}/erreichbarkeit.zip", SOURCE, "erreichbarkeit.zip")


if __name__ == "__main__":
    print(grid_csv())
    print(description_zip())
