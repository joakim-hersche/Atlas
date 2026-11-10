"""Federal popular votes by municipality: BFS DAM JSON files (voteinfo schema).

For each vote date BFS publishes two JSON files:
  'date'    municipality state at the vote date (spatial_reference voge = that state)
  'current' re-aggregated by BFS to the latest municipality state
Both are OPEN-BY. Used here as raw input and to validate our reprojection against BFS's.
"""
from __future__ import annotations

import json
import re

import pandas as pd
import requests

from pipeline.common import USER_AGENT, fetch

SOURCE = "bfs_votes"
DAM = "https://dam-api.bfs.admin.ch/hub/api/dam/assets"


def list_vote_assets() -> pd.DataFrame:
    """One row per vote date with the DAM ids of both variants."""
    r = requests.get(DAM, params={"language": "de", "limit": 350, "extendedSearch": "Volksabstimmung vom%"},
                     headers={"User-Agent": USER_AGENT}, timeout=120)
    r.raise_for_status()
    pairs: dict[str, dict] = {}
    for a in r.json()["data"]:
        t = a["description"]["titles"]
        sub = t.get("sub") or ""
        m = re.search(r"(\d\d)\.(\d\d)\.(\d{4})", t.get("main", ""))
        if not m or "JSON" not in sub:
            continue
        kind = "date" if "Datum der Abstimmung" in sub else "current" if "aktuellsten" in sub else None
        if kind:
            d = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            pairs.setdefault(d, {"vote_date": d})[kind] = a["ids"]["damId"]
    df = pd.DataFrame(pairs.values()).sort_values("vote_date")
    return df.dropna(subset=["date", "current"]).astype({"date": int, "current": int})


def fetch_vote(dam_id: int, vote_date: str, kind: str):
    return fetch(f"{DAM}/{dam_id}/master", SOURCE, f"vote_{vote_date}_{kind}.json")


def parse_vote(path) -> tuple[pd.DataFrame, str]:
    """Long table: one row per (vorlage, municipality). Returns (df, voge spatial date)."""
    d = json.loads(open(path, encoding="utf-8").read())
    voge = next(s["spatial_date"] for s in d["spatial_reference"] if s["spatial_unit"] == "voge")
    rows = []
    for v in d["schweiz"]["vorlagen"]:
        for k in v["kantone"]:
            for g in k["gemeinden"]:
                r = g["resultat"]
                rows.append({
                    "vote_date": d["abstimmtag"], "vorlagen_id": v["vorlagenId"],
                    "canton": k.get("geoLevelname"), "bfs_nr": int(g["geoLevelnummer"]),
                    "name": g["geoLevelname"], "eligible": r.get("anzahlStimmberechtigte"),
                    "ballots": r.get("eingelegteStimmzettel"), "valid": r.get("gueltigeStimmen"),
                    "yes": r.get("jaStimmenAbsolut"), "no": r.get("neinStimmenAbsolut"),
                })
    return pd.DataFrame(rows), voge
