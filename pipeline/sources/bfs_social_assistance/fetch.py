"""Fetch BFS social assistance (SHS) per municipality from the Swiss Stats Map Explorer.

Undocumented internal JSON endpoints of mapexplorer.bfs.admin.ch (Géoclip): dataset ch_13_05a,
indicators sozialhilfeempf (recipients) and sozialhilfequot (rate), all years 2007-latest on one
municipality state (nivgeo polg2025_04_06, view map226). GC_refdata gives the territory codes the
value arrays refer to. Canton-level arrays (kant2022_01_01) are fetched for the order check.
Validation file: Regionalporträts 2021 (DAM 15864450), social assistance rate 2019 per municipality.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_social_assistance"
BASE = "https://mapexplorer.bfs.admin.ch"
DATASET = "ch_13_05a"
VIEWS = {"polg2025_04_06": "map226"}
REGIONALPORTRAETS_2021 = "https://dam-api.bfs.admin.ch/hub/api/dam/assets/15864450/master"


def coldata(indic: str, view: str):
    return fetch(f"{BASE}/GC_coldata.php", SOURCE, f"coldata_{view}_{indic}.json",
                 params={"view": view, "dataset": DATASET, "indic": indic, "vars": indic})


def indic_meta(indic: str, view: str):
    return fetch(f"{BASE}/GC_indic.php", SOURCE, f"indic_{view}_{indic}.json",
                 params={"lang": "de", "view": view, "dataset": DATASET, "indic": indic})


def refdata(nivgeo: str):
    return fetch(f"{BASE}/GC_refdata.php", SOURCE, f"refdata_{nivgeo}.json",
                 params={"nivgeo": nivgeo, "extent": "ch", "lang": "de"})


def regionalportraets_2021():
    return fetch(REGIONALPORTRAETS_2021, SOURCE, "regionalportraets_2021_gemeinden.xlsx")
