"""Median taxable income per taxpayer (normal cases), estimated from the ESTV income classes, 2020-2023.

Municipalities: class counts of the tax year's municipality state are reprojected to the reference state by
summing (estv_dbst helpers, same suppression rules), then the median is estimated per municipality
(estimate.py). Cantons and Switzerland: the same estimate from the published canton / national class totals
(level kanton / schweiz, provenance native). The result is a model, precision "modelled": the interpolation inside
the income class that contains the median is an assumption, and the classes are wide (CHF 50,001-75,000 is the
median class in most municipalities).
Population: all taxpayers of the normal cases (tax units: a married couple counts once), with and without
federal tax; taxable income as assessed for the direct federal tax (not the cantonal base).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.estv_dbst import ingest as dbst
from pipeline.sources.estv_dbst.refhelp import SUP, per_period_to_reference
from pipeline.sources.estv_median_income.estimate import median_from_classes
from pipeline.sources.estv_median_income.fetch import SOURCE, YEARS, class_workbooks

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
CLASSES = dbst.CLASS_IDS
CLASS_COLS = [f"cls_{c}" for c in CLASSES]
MUNI_METRIC = "tax_np_median_taxable_income"
VINTAGE_LOG: dict = {}


def _unit_rows(path, suffix: str = "21") -> pd.DataFrame:
    """Canton rows (Gemeinde ID 10000 = canton total; 'Schweiz' = national) of the class sheet, by class id."""
    x = pd.ExcelFile(path)
    sheet = [s for s in x.sheet_names if s.strip().endswith(suffix) and s.strip()[:1].isdigit()][0]
    d = pd.read_excel(x, sheet, header=None, dtype=str)
    hdr = d.index[d[2].astype(str).str.strip() == "Gemeinde ID"][0]
    cols = {c: dbst._class_id(str(d.iloc[hdr, c]).strip()) for c in range(4, d.shape[1])}
    body = d.iloc[hdr + 1:]
    body = body[pd.to_numeric(body[2], errors="coerce") == 10000]
    rows = []
    assert len(body) == 27, "expected 26 canton totals and the national total"
    # some workbooks leave the canton number blank: the rows are in canton order (1-26), then Switzerland (27)
    for i, (_, r) in enumerate(body.iterrows(), start=1):
        kid = str(i)
        if i == 27:
            unit, level = "CH", "schweiz"
        else:
            unit, level = None, "kanton"
        rows.append({"canton_id": kid, "unit": unit, "level": level,
                     **{cid: pd.to_numeric(r[c], errors="coerce") for c, cid in cols.items()}})
    return pd.DataFrame(rows)


def _canton_abbrev(df: pd.DataFrame) -> pd.DataFrame:
    """Canton number (1-26, BFS order) -> abbreviation."""
    ab = ["ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR",
          "AG", "TG", "TI", "VD", "VS", "NE", "GE", "JU"]
    df = df.copy()
    k = df["level"] == "kanton"
    df.loc[k, "unit"] = df.loc[k, "canton_id"].astype(int).map(lambda i: ab[i - 1])
    return df


def native_classes(year: int) -> pd.DataFrame:
    parts = [_canton_abbrev(_unit_rows(p)) for p in class_workbooks(year)]
    if len(parts) == 1:
        return parts[0]
    a, b = parts
    # a taxpayer without federal tax has no tax in class 'with tax' files: classes absent from one workbook are 0
    ai, bi = a.set_index("unit"), b.set_index("unit")
    m = pd.DataFrame({c: ai.get(c, 0).add(bi.get(c, 0), fill_value=0) for c in CLASSES})
    return m.rename_axis("unit").reset_index().merge(a[["unit", "level"]], on="unit")


def municipal_wide() -> pd.DataFrame:
    parts = []
    for y in YEARS:
        w, _ = dbst._new_year(y)
        w = w[["bfs_nr", *CLASS_COLS, *[c + SUP for c in CLASS_COLS], "taxpayers_normal", "taxpayers_normal" + SUP]]
        w["period"] = str(y)
        parts.append(w)
    return pd.concat(parts, ignore_index=True)


def observations() -> pd.DataFrame:
    wide = municipal_wide()
    cols = [*CLASS_COLS, "taxpayers_normal"]
    obs = per_period_to_reference(wide, {c: c for c in cols}, SOURCE, log=VINTAGE_LOG)
    v = obs.pivot_table(index=["unit_id", "period"], columns="metric_id", values="value", aggfunc="first")
    prov = obs.groupby(["unit_id", "period"])["provenance"].agg(lambda s: "reprojected_weighted"
                                                                 if (s == "reprojected_weighted").any()
                                                                 else s.iloc[0])
    arr = v[CLASS_COLS].to_numpy()
    tot = v["taxpayers_normal"].to_numpy()
    med = [median_from_classes(list(a), t) for a, t in zip(arr, tot)]
    res = pd.DataFrame({"bfs_nr": [i[0] for i in v.index], "period": [i[1] for i in v.index], "median": med})
    res["provenance"] = prov.reindex(v.index).to_numpy()
    res["precision"] = "modelled"
    o = emit(res, {"median": MUNI_METRIC}, "period", SOURCE)
    o.loc[o["value"].isna(), "status"] = "suppressed"
    o.loc[o["status"] == "suppressed", "note"] = ("median class not determinable: small cells suppressed by tax "
                                                  "secrecy, or no data for the unit")
    # canton and national class totals (published, complete): same estimator
    nat = []
    for y in YEARS:
        n = native_classes(y)
        for _, r in n.iterrows():
            nat.append({"unit": r["unit"], "level": r["level"], "period": str(y),
                        "median": median_from_classes([r[c] for c in CLASSES])})
    nat = pd.DataFrame(nat)
    parts = [o]
    for lvl, d in nat.groupby("level"):
        parts.append(emit(d, {"median": MUNI_METRIC}, "period", SOURCE, level=lvl, unit_col="unit",
                          vintage=REFERENCE_DATE, precision="modelled", provenance="native"))
    out = pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
    return out
