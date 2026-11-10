"""Median taxable income per taxpayer (normal cases), estimated from the ESTV income classes, 2020-2023.

Municipalities: class counts of the tax year's municipality state are reprojected to the reference state by
summing (estv_dbst.refhelp, same suppression rules), then the median is estimated per municipality (estimate.py).
Cantons and Switzerland: the same estimate from the published canton / national class totals (provenance native).
The result is a model, precision "modelled": the interpolation inside the income class that contains the median is
an assumption, and the classes are wide (CHF 50,001-75,000 holds the median in most municipalities).
Population: all taxpayers of the normal cases (tax units: a married couple counts once), with and without federal
tax; taxable income as assessed for the direct federal tax (not the cantonal base).

2020: the workbook of all normal cases is wrong (publisher error), so the class counts are the sum of the
taxpayers with federal tax (sheet 121) and without (sheet 321). In the 'without' sheet the classes above CHF
75,000 are almost always '-' (cell below 4); such a cell counts as 0 when the 'with' sheet has a value for it
(an error of at most 3 taxpayers in a class that holds dozens).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.estv_dbst.refhelp import SUP, per_period_to_reference
from pipeline.sources.estv_median_income.estimate import median_from_classes
from pipeline.sources.estv_median_income.fetch import SOURCE, YEARS, class_workbooks

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
CLASSES = ["0", "1_30k", "30_40k", "40_50k", "50_75k", "75_100k", "100_200k", "200_500k", "500k_1m", "1m_plus"]
CLASS_COLS = [f"cls_{c}" for c in CLASSES]
LABELS = {"0": "0", "1-30000": "1_30k", "30001-40000": "30_40k", "40001-50000": "40_50k", "50001-75000": "50_75k",
          "75001-100000": "75_100k", "100001-200000": "100_200k", "200001-500000": "200_500k",
          "500001-1000000": "500k_1m"}
CANTONS = ["ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR",
           "AG", "TG", "TI", "VD", "VS", "NE", "GE", "JU"]
METRIC = "tax_np_median_taxable_income"
VINTAGE_LOG: dict = {}


def _class_id(label: str) -> str:
    lab = str(label).replace("'", "").replace(" ", "")
    if lab.startswith("1000001"):
        return "1m_plus"
    if lab.startswith("Total"):
        return "total"
    if lab not in LABELS:
        raise ValueError(f"unknown income class label {label!r}")
    return LABELS[lab]


def _num(s: pd.Series) -> pd.Series:
    st = s.astype(str).str.strip()
    return pd.to_numeric(st.where(~(st.isin(["-", "*"]) | st.str.fullmatch(r"\*+"))), errors="coerce")


def read_class_sheet(path, suffix: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(municipalities by BFS number, 27 totals: cantons 1-26 in order, Switzerland = 27), columns = class ids and
    'total'. Suppressed cells ('-', '*') are NaN."""
    x = pd.ExcelFile(path)
    sheet = [s for s in x.sheet_names if s.strip() == suffix][0]
    d = pd.read_excel(x, sheet, header=None, dtype=str)
    hdr = d.index[d[2].astype(str).str.strip() == "Gemeinde ID"][0]
    cols = {c: _class_id(d.iloc[hdr, c]) for c in range(4, d.shape[1])}
    body = d.iloc[hdr + 1:]
    gde = pd.to_numeric(body[2], errors="coerce")
    m = body[(gde > 0) & (gde < 9000)]
    muni = pd.DataFrame({cid: _num(m[c]).to_numpy() for c, cid in cols.items()},
                        index=gde[(gde > 0) & (gde < 9000)].astype(int).to_numpy())
    t = body[gde == 10000]
    assert len(t) == 27, "expected 26 canton totals and the national total"
    # some workbooks leave the canton number blank: the rows are in canton order (1-26), then Switzerland (27)
    tot = pd.DataFrame({cid: _num(t[c]).to_numpy() for c, cid in cols.items()}, index=range(1, 28))
    return muni, tot


def class_tables(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Municipal and canton/national class counts of all normal cases of the tax year, columns CLASSES + 'total'."""
    parts = [read_class_sheet(p, s) for p, s in class_workbooks(year)]
    cols = [*CLASSES, "total"]
    if len(parts) == 1:
        muni, tot = parts[0]
        return muni.reindex(columns=cols), tot.reindex(columns=cols)
    (mw, tw), (mn, tn) = parts  # with federal tax, without

    def comb(w: pd.DataFrame, n: pd.DataFrame) -> pd.DataFrame:
        idx = w.index.union(n.index)
        w, n = w.reindex(idx), n.reindex(idx)
        out = pd.DataFrame(index=idx)
        for c in cols:
            wc = w[c] if c in w else pd.Series(0.0, index=idx)  # class 0: no taxpayer with federal tax
            nc = n[c] if c in n else pd.Series(0.0, index=idx)
            # a suppressed 'with' cell stays suppressed (NaN); a suppressed 'without' cell counts as 0
            out[c] = wc + nc.fillna(0)
        return out

    return comb(mw, mn), comb(tw, tn)


def municipal_wide() -> pd.DataFrame:
    parts = []
    for y in YEARS:
        muni, _ = class_tables(y)
        w = muni.rename(columns={c: f"cls_{c}" for c in CLASSES}).rename(columns={"total": "taxpayers_normal"})
        for c in [*CLASS_COLS, "taxpayers_normal"]:
            w[c + SUP] = w[c].isna()
        w = w.rename_axis("bfs_nr").reset_index()
        w["period"] = str(y)
        parts.append(w)
    return pd.concat(parts, ignore_index=True)


def estimates(wide: pd.DataFrame) -> pd.DataFrame:
    """Reproject the class counts to the reference state and estimate the median per municipality and year."""
    cols = [*CLASS_COLS, "taxpayers_normal"]
    obs = per_period_to_reference(wide, {c: c for c in cols}, SOURCE, log=VINTAGE_LOG)
    v = obs.pivot_table(index=["unit_id", "period"], columns="metric_id", values="value", aggfunc="first",
                        dropna=False)
    prov = obs.groupby(["unit_id", "period"])["provenance"].agg(
        lambda s: "reprojected_weighted" if (s == "reprojected_weighted").any() else s.iloc[0])
    arr, tot = v[CLASS_COLS].to_numpy(), v["taxpayers_normal"].to_numpy()
    res = pd.DataFrame({"bfs_nr": [i[0] for i in v.index], "period": [i[1] for i in v.index],
                        "median": [median_from_classes(list(a), t) for a, t in zip(arr, tot)]})
    res["provenance"] = prov.reindex(v.index).to_numpy()
    res["precision"] = "modelled"
    return res


def observations() -> pd.DataFrame:
    res = estimates(municipal_wide())
    o = emit(res, {"median": METRIC}, "period", SOURCE)
    sup = o["value"].isna()
    o.loc[sup, "status"] = "suppressed"
    o.loc[sup, "note"] = "median class not determinable: small cells suppressed by tax secrecy"
    nat = []
    for y in YEARS:
        _, tot = class_tables(y)
        for i, r in tot.iterrows():
            nat.append({"unit": "CH" if i == 27 else CANTONS[i - 1], "level": "schweiz" if i == 27 else "kanton",
                        "period": str(y), "median": median_from_classes([r[c] for c in CLASSES], r["total"])})
    nat = pd.DataFrame(nat)
    parts = [o] + [emit(d, {"median": METRIC}, "period", SOURCE, level=lvl, unit_col="unit", vintage=REFERENCE_DATE,
                        precision="modelled", provenance="native") for lvl, d in nat.groupby("level")]
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
