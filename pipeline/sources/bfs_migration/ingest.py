"""Migration of the permanent resident population per municipality, 2011–latest
(BFS PxWeb px-x-0103010200_121, STATPOP), split Swiss / non-Swiss.

Totals per migration type (also for 1981–2010) come from bfs_bevnat_bilanz; this connector adds
the split by nationality. 'Non-Swiss' = total minus Swiss (includes stateless and unknown).
Geo value codes are running indices; BFS numbers come from the labels (pxgeo.geo_codes).
Published by BFS on the latest municipality state. The 'Ohne Angabe' geo unit (in the Swiss total,
in no canton) is kept as level 'unallocated'.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import geo_codes, to_obs, unallocated_rows
from pipeline.sources.bfs_pxweb.fetch import query_codes

SOURCE = "bfs_migration"
DB = "px-x-0103010200_121"
G = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"
NAT, SEX, TYPE = "Staatsangehörigkeit (Auswahl)", "Geschlecht", "Migrationstyp"
TYPES = {"0": "immigration", "1": "emigration", "2": "intercant_in", "3": "intercant_out",
         "4": "intracant_in", "5": "intracant_out"}


def observations(report: dict | None = None) -> pd.DataFrame:
    codes, _, _ = geo_codes(DB, G)
    df = query_codes(DB, {"Jahr": "*", G: "*", NAT: ["0", "1"], SEX: ["0"], TYPE: "*"})
    w = df.pivot_table(index=[G, "Jahr"], columns=[TYPE, NAT], values="value", aggfunc="first")
    out = pd.DataFrame(index=w.index)
    for t, name in TYPES.items():
        out[f"mig_{name}_swiss"] = w[(t, "1")]
        out[f"mig_{name}_foreign"] = w[(t, "0")] - w[(t, "1")]
    for grp in ("swiss", "foreign"):
        out[f"mig_net_intl_{grp}"] = out[f"mig_immigration_{grp}"] - out[f"mig_emigration_{grp}"]
        out[f"mig_net_intercant_{grp}"] = out[f"mig_intercant_in_{grp}"] - out[f"mig_intercant_out_{grp}"]
    out = out.reset_index()
    out["geo"] = out[G].map(codes)
    cols = [c for c in out.columns if c.startswith("mig_")]
    obs = to_obs(out, "geo", "Jahr", {c: c for c in cols}, SOURCE, report=report)
    # 'Ohne Angabe' unit: in the Swiss total, in no canton -> level 'unallocated'
    return pd.concat([obs, unallocated_rows(out, G, "Jahr", cols, SOURCE, DB)], ignore_index=True)
