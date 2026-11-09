"""Federal popular votes by municipality since 1960 (BFS PxWeb px-x-1703030000_101) and
vote titles from the voteinfo OGD JSON (ogd-static.voteinfo-app.ch, 1981+).

The cube is published by BFS on the current municipality state (all votes re-aggregated).
"""
from __future__ import annotations

import json

import pandas as pd

from pipeline.common import fetch
from pipeline.harmonize.pxweb import GEO
from pipeline.sources.bfs_pxweb.fetch import metadata, query_codes

SOURCE = "bfs_votes_gemeinde"
CUBE = "px-x-1703030000_101"
VORLAGE = "Datum und Vorlage"
RESULTS = {"1": "eligible", "2": "ballots", "4": "valid", "5": "yes", "6": "no"}
VOTEINFO = "https://ogd-static.voteinfo-app.ch/v1/ogd/sd-t-17-02-{d}-eidgAbstimmung.json"


def results() -> pd.DataFrame:
    """Long frame: geo code, vorlagen id, result code, value (counts only; % are recomputed)."""
    return query_codes(CUBE, {GEO: "*", VORLAGE: "*", "Ergebnis": list(RESULTS)})


def vorlagen_labels() -> pd.DataFrame:
    m = metadata(CUBE)
    v = next(x for x in m["variables"] if x["code"] == VORLAGE)
    df = pd.DataFrame({"vorlagen_id": v["values"], "label": v["valueTexts"]})
    df["date"] = df["label"].str[:10]
    df["title_px"] = df["label"].str[11:].str.strip()
    return df


def voteinfo(date: str) -> dict | None:
    """voteinfo JSON for a vote date 'YYYY-MM-DD' (None if not published, e.g. before 1981)."""
    try:
        p = fetch(VOTEINFO.format(d=date.replace("-", "")), SOURCE, f"voteinfo_{date}.json", retries=2)
    except RuntimeError:
        return None
    return json.loads(p.read_text(encoding="utf-8"))
