"""Fetch BFS historized generalized administrative boundaries (G1 and K4), all states 1850–today.

STAC collections on data.geo.admin.ch:
  ch.bfs.historisierte-administrative_grenzen_g1  (web-scale generalization)
  ch.bfs.historisierte-administrative_grenzen_k4  (small-scale generalization)
Each version carries GDEHISTID (= register histId), VALID_FROM/VALID_TO and elevation statistics.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_hist_boundaries"
BASE = "https://data.geo.admin.ch"


def fetch_all() -> dict[str, object]:
    out = {}
    for level in ("g1", "k4"):
        coll = f"ch.bfs.historisierte-administrative_grenzen_{level}"
        name = f"historisierte-administrative_grenzen_{level}"
        out[level] = fetch(f"{BASE}/{coll}/{name}/{name}_2056.gpkg", SOURCE, f"{name}_2056.gpkg")
    return out


if __name__ == "__main__":
    for k, v in fetch_all().items():
        print(k, v)
