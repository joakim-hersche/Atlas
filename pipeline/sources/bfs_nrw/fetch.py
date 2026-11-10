"""National Council elections 1971–2023 by municipality (BFS PxWeb, Statistik der Nationalratswahlen).

  px-x-1702020000_105  party votes (Parteistimmen) and party strength by district and municipality
  px-x-1702020000_104  party votes, fictitious voters (fiktive Wählende) and strength: CH and cantons
  px-x-1702020000_101  eligible voters, voters and ballot types: CH, cantons, districts, municipalities
Municipal cubes are on the 2023-01-01 municipality state (BFS retro-aggregated older elections).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.pxweb import GEO
from pipeline.sources.bfs_pxweb.fetch import metadata, query_codes

GEO105 = "Bezirk (>>) / Gemeinde (......)"
TURNOUT = {"1": "eligible", "2": "voters", "4": "ballots_blank", "5": "ballots_invalid",
           "6": "ballots_valid", "7": "ballots_unchanged", "8": "ballots_changed"}


def party_votes() -> pd.DataFrame:
    """Parteistimmen (1) and Parteistärke % (2) by district/municipality × year × party."""
    return query_codes("px-x-1702020000_105", {GEO105: "*", "Jahr": "*", "Partei": "*", "Ergebnisse": ["1", "2"]})


def canton_parties() -> pd.DataFrame:
    """Parteistimmen (1), fiktive Wählende (2), Parteistärke % (3) for CH and cantons."""
    return query_codes("px-x-1702020000_104", {"Kanton": "*", "Jahr": "*", "Partei": "*", "Ergebnisse": "*"})


def turnout() -> pd.DataFrame:
    return query_codes("px-x-1702020000_101", {GEO: "*", "Jahr": "*", "Ergebnisse": list(TURNOUT)})


def parties() -> dict[str, str]:
    v = next(x for x in metadata("px-x-1702020000_105")["variables"] if x["code"] == "Partei")
    return dict(zip(v["values"], v["valueTexts"]))


def seats() -> pd.Series:
    """Seats (elected, all parties, both sexes) per canton and election year, px-x-1702020000_103
    (Nationalratswahlen: Anzahl Kandidaturen und Gewählte seit 1971). Index (Kanton, Jahr)."""
    d = query_codes("px-x-1702020000_103", {"Kanton": "*", "Jahr": "*", "Partei": ["0"], "Geschlecht": ["Z"],
                                           "Ergebnisse": ["2"]})
    return d.set_index(["Kanton", "Jahr"])["value"]


def majority_cantons() -> dict[str, list[str]]:
    """Election year -> cantons with a single seat. With one seat the election is by majority
    (Majorzwahl, Art. 47 BPR), so party strength is not comparable with proportional cantons."""
    s = seats()
    s = s[s.index.get_level_values("Kanton") != "CH"]
    one = s[s == 1].reset_index()
    return {str(y): sorted(g["Kanton"]) for y, g in one.groupby("Jahr")}
