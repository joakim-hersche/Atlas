"""School and university buildings per municipality from the public GWR extract.

Count of existing buildings (GSTAT 1004, 'Gebäude bestehend') of GWR building class 1263, 'Schul- und
Hochschulgebäude, Forschungseinrichtungen', per municipality (GGDENR of the extract), with 0 for municipalities that
have none. This counts buildings, not schools: one school site often has several buildings, kindergartens and
daycare centres usually sit in buildings of other classes (residential, office), and class 1263 also holds
universities and research institutes. The register is a live snapshot (the extract is dated in its file
EXPDAT, 2026-11-10); period 2026.
Resident base for the per-1,000 ratio: STATPOP permanent residents of 31 Dec 2025 (BFS municipality table on the
municipality state of 2025), reprojected to the reference state (sums).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.sources.bfs_gwr.buildings import load
from pipeline.sources.bfs_statpop_geodata.fetch import municipalities
from pipeline.sources.estv_dbst.refhelp import per_period_to_reference

SOURCE = "bfs_gwr"
SCHOOL_CLASS = 1263
EXISTING = 1004
PERIOD = "2026"
POP_YEAR = 2025


def school_counts() -> pd.DataFrame:
    b = load()
    b = b[(b["GSTAT"] == EXISTING) & b["GGDENR"].notna()]
    n = b.groupby(b["GGDENR"].astype(int)).agg(buildings=("EGID", "size"),
                                                schools=("GKLAS", lambda s: int((s == SCHOOL_CLASS).sum())))
    return n.rename_axis("bfs_nr").reset_index().assign(period=PERIOD)


def residents() -> pd.DataFrame:
    d = pd.read_parquet(municipalities(POP_YEAR), columns=["GDENR", "BBTOT"])
    return d.rename(columns={"GDENR": "bfs_nr", "BBTOT": "residents"}).assign(period=PERIOD)


def observations() -> pd.DataFrame:
    s = per_period_to_reference(school_counts(), {"schools": "gwr_school_buildings"}, SOURCE)
    s["note"] = "existing GWR buildings of class 1263 (school and university buildings, research institutions)"
    r = per_period_to_reference(residents(), {"residents": "gwr_resident_base"}, SOURCE)
    r["note"] = f"STATPOP permanent residents 31 Dec {POP_YEAR}, base for the per-1,000 ratio"
    return pd.concat([s, r], ignore_index=True)
