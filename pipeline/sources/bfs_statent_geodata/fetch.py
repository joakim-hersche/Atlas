"""Fetch BFS STATENT geodata per municipality (workplaces, jobs, FTE by NOGA division).

STAC collection ch.bfs.betriebszaehlungen; one file per year 2011–latest, each on the municipality
state of its year (GDENR + GDEHISTID / GDE_HISTID). Data protection: all values < 4 are set to 4.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_statent_geodata"
BASE = "https://data.geo.admin.ch/ch.bfs.betriebszaehlungen"
FIRST_YEAR, LAST_YEAR = 2011, 2024


def municipalities(year: int):
    f = f"betriebszaehlungen_{year}_gmde_2056.parquet"
    return fetch(f"{BASE}/betriebszaehlungen_{year}/{f}", SOURCE, f)
