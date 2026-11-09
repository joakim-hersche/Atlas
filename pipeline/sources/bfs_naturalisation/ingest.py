"""Acquisitions of Swiss citizenship per municipality, 2011–latest
(BFS PxWeb px-x-0103030100_102, STATPOP), total and by former nationality group.

Geo value codes are running indices; BFS numbers come from the labels (pxgeo.geo_codes).
Published by BFS on the latest municipality state.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import geo_codes, to_obs
from pipeline.sources.bfs_pxweb.fetch import query_codes

SOURCE = "bfs_naturalisation"
DB = "px-x-0103030100_102"
G = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"
NAT, SEX = "Staatsangehörigkeit ehemalig (Auswahl)", "Geschlecht"
GROUPS = {"nat_total": ["0"], "nat_eu_efta": ["1", "2"], "nat_other_europe": ["3"],
          "nat_outside_europe": ["4", "5", "6", "7", "8"]}


def observations(report: dict | None = None) -> pd.DataFrame:
    codes, _, _ = geo_codes(DB, G)
    df = query_codes(DB, {"Jahr": "*", G: "*", NAT: sorted({c for v in GROUPS.values() for c in v}, key=int),
                          SEX: ["0", "2"]})
    tot = df[df[SEX] == "0"]
    out = None
    for name, cc in GROUPS.items():
        s = (tot[tot[NAT].isin(cc)].groupby([G, "Jahr"])["value"].sum(min_count=len(cc)).rename(name))
        out = s.to_frame() if out is None else out.join(s, how="outer")
    out["nat_women"] = df[(df[SEX] == "2") & (df[NAT] == "0")].set_index([G, "Jahr"])["value"]
    out = out.reset_index()
    out["geo"] = out[G].map(codes)
    cols = [c for c in out.columns if c.startswith("nat_")]
    return to_obs(out, "geo", "Jahr", {c: c for c in cols}, SOURCE, report=report)
