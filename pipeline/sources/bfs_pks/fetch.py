"""Fetch BFS Polizeiliche Kriminalstatistik (PKS) by district and canton from the Swiss Stats Map
Explorer (Statistischer Atlas der Schweiz), plus the STAT-TAB cube of offences by canton.

Map Explorer (mapexplorer.bfs.admin.ch, Géoclip; undocumented internal JSON endpoints, raw
responses cached): dataset ch_19_03 'Polizeiliche Kriminalstatistik', years 2009-latest.
  view map33  = districts, nivgeo bezk2023_01_01 (143 districts, state 1 Jan 2023)
  view map164 = cantons,   nivgeo kant2022_01_01 (26 cantons)
Each indicator is a formula p1*var1/var2 (offences / population * 1000, GC_indic 'frmType');
GC_coldata returns the raw variables: the offence count (var1) and the population (var2 'pop').
GC_refdata gives the territory codes the value arrays refer to. DAM asset 36495988 (one of the
Statatlas map assets of this dataset) carries the terms of use (OPEN-BY).

STAT-TAB px-x-1903020100_101 (offences by offence, canton, completion, clearance, year) is
queried through the generic bfs_pxweb helper (cached under data/raw/bfs_pxweb).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_pks"
BASE = "https://mapexplorer.bfs.admin.ch"
DATASET = "ch_19_03"
VIEWS = {"bezirk": ("map33", "bezk2023_01_01"), "kanton": ("map164", "kant2022_01_01")}
DAM_ASSET = "https://dam-api.bfs.admin.ch/hub/api/dam/assets/36495988"
PX_TABLE = "px-x-1903020100_101"


def coldata(indic: str, var: str, view: str):
    return fetch(f"{BASE}/GC_coldata.php", SOURCE, f"coldata_{view}_{var}.json",
                 params={"view": view, "dataset": DATASET, "indic": indic, "vars": var})


def indic_meta(indic: str, view: str, lang: str = "de"):
    return fetch(f"{BASE}/GC_indic.php", SOURCE, f"indic_{view}_{indic}_{lang}.json",
                 params={"lang": lang, "view": view, "dataset": DATASET, "indic": indic})


def refdata(nivgeo: str):
    return fetch(f"{BASE}/GC_refdata.php", SOURCE, f"refdata_{nivgeo}.json",
                 params={"nivgeo": nivgeo, "extent": "ch", "lang": "de"})


def dam_asset():
    """Asset metadata incl. termsOfUse (licence evidence)."""
    return fetch(DAM_ASSET, SOURCE, "dam_asset_36495988.json")


def px_offences(select: dict):
    from pipeline.sources.bfs_pxweb.fetch import query_codes
    return query_codes(PX_TABLE, select)
