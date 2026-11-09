"""Federal population census 1970–2000 by municipality (BFS PxWeb cubes px-x-40010000…).

All four census years are published on the municipality state of 2000 (2896 Gemeinden).
Geography codes are running indexes; the BFS number is in the label ('......0261 Zürich').
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.pxweb import GEO
from pipeline.sources.bfs_pxweb.fetch import metadata, parse_geo_label, query_codes

CUBES = {
    "language": ("px-x-4001000000_123", "Hauptsprache", {"Staatsangehörigkeit (Kategorie)": ["0"]}),
    "religion": ("px-x-4001000000_122", "Religion", {}),
    "hh_type": ("px-x-4001000000_102", "Haushaltstyp", {}),
    "hh_size": ("px-x-4001000000_101", "Haushaltsgrösse", {}),
}


def geo_table(dbid: str) -> pd.DataFrame:
    """Geo index code -> level, unit (BFS number / canton number / 'CH'), label."""
    v = next(x for x in metadata(dbid)["variables"] if x["code"] == GEO)
    rows, canton_no = [], 0
    for code, text in zip(v["values"], v["valueTexts"]):
        level, bfs, name = parse_geo_label(text)
        if level == "kanton":
            canton_no += 1  # cantons are listed in BFS order (1 ZH … 26 JU)
            rows.append((code, "kanton", canton_no, name))
        elif level == "gemeinde":
            rows.append((code, "gemeinde", bfs, name))
        elif level == "bezirk":
            rows.append((code, "bezirk", None, name))
        elif text.strip() == "Schweiz":
            rows.append((code, "schweiz", None, name))
    return pd.DataFrame(rows, columns=["geo", "level", "unit", "name"])


def years(dbid: str) -> dict[str, str]:
    v = next(x for x in metadata(dbid)["variables"] if x["code"] == "Jahr")
    return dict(zip(v["values"], v["valueTexts"]))


def cube(kind: str) -> pd.DataFrame:
    """Long frame: geo, year (e.g. '1970'), category code, value."""
    dbid, var, fixed = CUBES[kind]
    df = query_codes(dbid, {"Jahr": "*", GEO: "*", var: "*", **fixed})
    df["year"] = df["Jahr"].map(years(dbid))
    return df.rename(columns={GEO: "geo", var: "cat"})[["geo", "year", "cat", "value"]]
