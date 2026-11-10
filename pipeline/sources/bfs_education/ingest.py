"""BFS education per municipality.

1. Bildungsstand – Geodaten (highest completed education, residents aged 25-64), 1990, 2000,
   2017-2023. All years are published on one municipality state with GDEHISTID (mapped by hist_id).
   Shares are published as integer percentages of persons with known attainment; the level counts
   delivered here are share × persons with known attainment / 100 (so the derived shares reproduce
   the published ones at municipality level, re-aggregation error ≤ 0.5 % of each municipality's
   population). 1990/2000: census (persons with unknown attainment in BBTOT25_64_MISS); 2017+:
   register/survey imputation model (precision modelled). Shares are blank for small municipalities
   (< 100 persons) -> status suppressed.
2. LABB – first upper-secondary qualification / Matura by age 25 (cohorts aged 15 in 2010-2014,
   observed 10 years), by municipality of residence at 15, state 2024-06-28. Rates only (rounded to
   the nearest even number), so not_aggregatable; canton and national rows kept as native.
"""
from __future__ import annotations

import datetime as dt
import io
import zipfile

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_education.fetch import SOURCE, YEARS, attainment, labb
from pipeline.sources.estv_dbst.refhelp import SUP, per_period_to_reference

VINTAGE_LOG: dict = {}
LEVELS = {"COMPULSORY": "n_comp", "SECONDARYII": "n_sec2", "TERTIARY": "n_tert"}


def _attainment_wide() -> pd.DataFrame:
    parts = []
    for y in YEARS:
        d = pd.read_csv(attainment(y), sep=";")
        if (d["ERHJAHR"] != y).any():
            raise ValueError(f"Bildungsstand {y}: unexpected ERHJAHR")
        miss = d["BBTOT25_64_MISS"] if "BBTOT25_64_MISS" in d else 0
        known = d["BBTOT25_64"] - miss
        w = pd.DataFrame({"hist_id": d["GDEHISTID"].astype(int), "period": str(y),
                          "pop": d["BBTOT25_64"].astype(float), "known": known.astype(float),
                          "imputation": pd.to_numeric(d["IMPUTATION"], errors="coerce") if y >= 2017 else np.nan})
        shares = d[list(LEVELS)].apply(pd.to_numeric, errors="coerce")
        sup = shares.isna().any(axis=1)
        for src, col in LEVELS.items():
            w[col] = shares[src] * known / 100
            w[col + SUP] = sup.to_numpy()
        w["known" + SUP] = sup.to_numpy()
        w["imputation" + SUP] = (y >= 2017) & w["imputation"].isna()
        parts.append(w)
    return pd.concat(parts, ignore_index=True)


def _labb() -> pd.DataFrame:
    z = zipfile.ZipFile(labb())
    g = pd.read_csv(io.BytesIO(z.read("dat-b-00.03-labb-01-gmde.csv")), encoding="utf-8-sig", dtype=str)
    k = pd.read_csv(io.BytesIO(z.read("dat-b-00.03-labb-01-kt.csv")), encoding="utf-8-sig", dtype=str)
    if set(g["STATE_NOMEN"]) != {"2024-06-28"} or set(g["COHORTS"]) != {"2010-2014"}:
        raise ValueError("LABB: unexpected state or cohorts")
    cols = {"UPSEC2_P": "edu_labb_upsec2_rate", "MAT_P": "edu_labb_matura_rate",
            "UPSEC2_AFT_25_P": "edu_labb_upsec2_after25_rate"}
    w = pd.DataFrame({"bfs_nr": g["GDE_ID"].astype(int), "period": "2010-2014"})
    for c in cols:
        w[c] = pd.to_numeric(g[c], errors="coerce")
        w[c + SUP] = w[c].isna()
    obs = per_period_to_reference(w, cols, SOURCE, rules={c: "not_aggregatable" for c in cols},
                                  vintage=dt.date(2024, 6, 28), log=VINTAGE_LOG)
    obs.loc[obs["status"] == "suppressed", "note"] = "not published (small cohort)"
    # canton and national rows as published (native)
    abbr = dict(zip(pd.read_parquet(interim_path("backbone", "canton.parquet"))["canton_id"].astype(int),
                    pd.read_parquet(interim_path("backbone", "canton.parquet"))["canton"].astype(str)))
    nat = k["KT_NAME"].str.startswith("Total")
    k["level"] = np.where(nat, "schweiz", "kanton")
    k["unit_id"] = ["CH" if n else abbr[int(x)] for n, x in zip(nat, k["KT_ID"])]
    k["period"] = "2010-2014"
    for c in cols:
        k[c] = pd.to_numeric(k[c], errors="coerce")
    native = [emit(part, cols, "period", SOURCE, level=lvl, unit_col="unit_id", vintage=REFERENCE_DATE,
                   precision="exact", provenance="native") for lvl, part in k.groupby("level")]
    return pd.concat([obs, *native], ignore_index=True)


def observations() -> pd.DataFrame:
    w = _attainment_wide()
    old = w["period"].isin(["1990", "2000"])
    m_cnt = {"n_comp": "edu_compulsory_25_64", "n_sec2": "edu_upper_secondary_25_64",
             "n_tert": "edu_tertiary_25_64", "known": "edu_known_25_64"}
    parts = [
        per_period_to_reference(w, {"pop": "edu_pop_25_64"}, SOURCE, key="hist_id", log=VINTAGE_LOG),
        per_period_to_reference(w[old], m_cnt, SOURCE, key="hist_id"),
        per_period_to_reference(w[~old], m_cnt, SOURCE, key="hist_id", precision="modelled"),
        per_period_to_reference(w[~old], {"imputation": "edu_imputation_share"}, SOURCE, key="hist_id",
                                rules={"imputation": "weighted_mean:pop"}, precision="modelled"),
        _labb(),
    ]
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
