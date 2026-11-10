"""GWR building table (one row per building) from the cached public extract, as a small parquet.

Columns kept: EGID, GDEKT, GGDENR (municipality number as registered, current state of the extract),
GKODE/GKODN (building coordinates, LV95), GSTAT (status), GKAT (building category), GKLAS (class),
GBAUJ (construction year), GANZWHG (number of dwellings).
"""
from __future__ import annotations

import zipfile

import pandas as pd

from pipeline.common import interim_path
from pipeline.sources.bfs_gwr.fetch import gwr_zip

COLS = ["EGID", "GDEKT", "GGDENR", "GKODE", "GKODN", "GSTAT", "GKAT", "GKLAS", "GBAUJ", "GANZWHG"]
CSV = "gebaeude_batiment_edificio.csv"


def load(refresh: bool = False) -> pd.DataFrame:
    out = interim_path("gwr", "buildings.parquet")
    if out.exists() and not refresh:
        return pd.read_parquet(out)
    with zipfile.ZipFile(gwr_zip()) as z, z.open(CSV) as f:
        df = pd.read_csv(f, sep="\t", usecols=COLS, dtype=str, encoding="utf-8")
    for c in ("EGID", "GGDENR", "GSTAT", "GKAT", "GKLAS", "GBAUJ", "GANZWHG"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("GKODE", "GKODN"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return df
