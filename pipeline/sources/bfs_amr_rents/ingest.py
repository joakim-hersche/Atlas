"""Connector entry point (pipeline.harmonize.run): observations() of bfs_amr_rents.

Average monthly net rent per m2 of occupied rented dwellings by labour market area 2018 (101 areas), BFS regional
disparities indicators (Structural Survey / GWS), 2012-2024. Level 'arbeitsmarktgebiet' (unit = BAE2018 code without
the leading zero, as in the backbone membership), provenance 'native', precision 'survey'. The CI measure is delivered
as a separate metric. Status 'U' (low reliability) is kept with a note; missing values (status 'O', including the
values the source withholds above a coefficient of variation of 10 %) become no_data with a note.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_amr_rents.fetch import SOURCE, rent_csv

MEASURES = {"OBS": "rent_amr_chf_m2", "CI": "rent_amr_chf_m2_ci"}


def observations() -> pd.DataFrame:
    d = pd.read_csv(rent_csv(), dtype=str)
    d.columns = ["dataflow", "raum", "indic", "measure", "freq", "period", "value", "dfid", "conf", "status", "dec"]
    d["measure"] = d["measure"].str.split(":").str[0].str.strip()
    d["status_code"] = d["status"].str.split(":").str[0].str.strip()
    d["unit_id"] = d["raum"].str.split(":").str[0].astype(int).astype(str)
    if d["unit_id"].nunique() != 101:
        raise ValueError(f"{SOURCE}: expected 101 labour market areas, got {d['unit_id'].nunique()}")
    d = d[d["measure"].isin(MEASURES)]
    d["v"] = pd.to_numeric(d["value"], errors="coerce")
    out = pd.DataFrame({
        "unit_id": d["unit_id"], "level": "arbeitsmarktgebiet",
        "vintage": d["period"].astype(str) + "-12-31",
        "metric_id": d["measure"].map(MEASURES), "period": d["period"].astype(str), "value": d["v"].astype(float),
        "precision": "survey", "provenance": "native", "source_id": SOURCE,
    })
    out["status"] = np.where(out["value"].notna(), "ok", "no_data")
    note = pd.Series(None, index=out.index, dtype="object")
    note[d["status_code"].eq("U")] = "low reliability (BFS status U)"
    note[d["status_code"].eq("B")] = "time series break (BFS status B)"
    note[d["v"].isna()] = "no value in the source (not published, or coefficient of variation above 10 %)"
    out["note"] = note
    # the source lists 2025 as an empty column: drop periods without any value
    keep = out.groupby("period")["value"].transform(lambda s: s.notna().any())
    return out[keep][OBS_COLUMNS].reset_index(drop=True)
