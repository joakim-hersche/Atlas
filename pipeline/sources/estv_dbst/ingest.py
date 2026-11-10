"""ESTV direct federal tax statistics, natural persons, by municipality (tax years 2003-2023).

Population: all taxpayers (tax units; a married couple is one taxpayer), with and without a federal
tax, normal and special cases together - the only definition available for every year:
  2003-2019 'auswertung' workbooks: taxpayers with federal tax, normal + special cases (counts:
            sheets 211 + 212, because the count Total of 241 is '*' wherever a class is
            suppressed; amounts: Total column of 242-244) + taxpayers without federal tax, normal +
            special cases (sheet 3 counts 2003-2007; sheets 311 + 312 with incomes from 2008).
  2020-2023 one file per case: all taxpayers normal cases (2023: file 500; 2020-22 '-normalfall')
            + special cases (600 / '-sonderfall'); without tax: 300 + 400 / '-ohne-belastung-*'.
            Publisher error: the 2020 '-normalfall' file repeats the special-case figures, so 2020
            normal cases are built from '-mit-belastung-normalfall' + '-ohne-belastung-normalfall'.
Net and taxable income are complete (incl. taxpayers without tax) only from 2008; 2003-2007 give
taxpayer counts and federal tax yield. 2001-2002 are left out: several cantons were still on
two-year assessment (taxpayer total 3.5 M vs 4.3 M in 2003); 1999/2000 and earlier likewise (PDF
before 1999).
Income classes (10 classes of taxable income, incl. CHF 100,001+) exist only in the 2020+ files;
they are taken from the normal cases (file 500) with their own denominator
(tax_np_taxpayers_normal), so the share above CHF 100k is a share of normal-case taxpayers.
Each year is on the municipality state of its tax year: inferred per year, reprojected to the
reference state (counts and amounts summed). '-' / '*' = suppressed (tax secrecy) -> status
suppressed; municipalities missing from a sheet (2006 sheet 212 lacks 379 rows) -> no_data.
"""
from __future__ import annotations

import re
import warnings

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, fetch
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.estv_dbst.fetch import SOURCE, links, year_file
from pipeline.sources.estv_dbst.refhelp import SUP, per_period_to_reference

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
YEARS = range(2003, 2024)
INCOME_FROM = 2008
NEW_FROM = 2020
CLASSES = ["0", "1-30k", "30-40k", "40-50k", "50-75k", "75-100k", "100-200k", "200-500k", "500k-1m", "1m+"]
CLASS_IDS = ["0", "1_30k", "30_40k", "40_50k", "50_75k", "75_100k", "100_200k", "200_500k", "500k_1m", "1m_plus"]
VINTAGE_LOG: dict = {}
NATIONAL: dict = {}


def _num(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    """numeric values and suppression flags ('-' or '*')."""
    st = s.astype(str).str.strip()
    sup = st.isin(["-", "*"]) | st.str.fullmatch(r"\*+")
    return pd.to_numeric(st.where(~sup), errors="coerce"), sup


# ---------- new format (2020+) ----------------------------------------------------------------
FILE_NO = {"all_normal": 500, "all_special": 600, "with_normal": 100, "with_special": 200,
           "none_normal": 300, "none_special": 400}
FILE_KIND = {"all_normal": "normalfall", "all_special": "sonderfall",
             "with_normal": "mit-belastung-normalfall", "with_special": "mit-belastung-sonderfall",
             "none_normal": "ohne-belastung-normalfall", "none_special": "ohne-belastung-sonderfall"}
# Publisher error: the 2020 file '...-2020-normalfall-de.xlsx' repeats the special-case numbers
# (CH 572,569 = '...-2020-sonderfall-de.xlsx'); all normal cases 2020 are therefore built as
# taxpayers with tax + without tax (normal cases). Checked: all = with + without in 2021-2023.
BUILD_ALL_NORMAL = {2020}


def _new_file(year: int, case: str):
    ls = links()
    if year >= 2023:
        name = f"statistik-dbst-np-gemeinden-{year}-{FILE_NO[case]}.xlsx"
    else:
        cands = [k for k in ls if re.fullmatch(rf"statistik-dbst-np-gden-{year}-{FILE_KIND[case]}(-de)?\.xlsx", k)]
        if not cands:
            raise FileNotFoundError(f"{year} {case}")
        name = cands[0]
    return fetch(ls[name], SOURCE, name)


def _class_id(label: str) -> str:
    lab = label.replace("'", "").replace(" ", "")
    m = {"0": "0", "1-30000": "1_30k", "30001-40000": "30_40k", "40001-50000": "40_50k",
         "50001-75000": "50_75k", "75001-100000": "75_100k", "100001-200000": "100_200k",
         "200001-500000": "200_500k", "500001-1000000": "500k_1m"}
    if lab.startswith("1000001"):
        return "1m_plus"
    if lab.startswith("Total"):
        return "total"
    if lab not in m:
        raise ValueError(f"unknown income class label {label!r}")
    return m[lab]


def _new_table(path, suffix: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """(values, suppressed flags, national row) by class id (+ 'total') for one sheet."""
    x = pd.ExcelFile(path)
    sheet = [s for s in x.sheet_names if s.strip().endswith(suffix) and s.strip()[:1].isdigit()][0]
    d = pd.read_excel(x, sheet, header=None, dtype=str)
    hdr = d.index[d[2].astype(str).str.strip() == "Gemeinde ID"][0]
    cols = {c: _class_id(str(d.iloc[hdr, c]).strip()) for c in range(4, d.shape[1])}
    body = d.iloc[hdr + 1:]
    gde = pd.to_numeric(body[2], errors="coerce")
    m = body[(gde > 0) & (gde < 9000)]
    idx = gde[(gde > 0) & (gde < 9000)].astype(int).values
    vals, sups = {}, {}
    for c, cid in cols.items():
        v, s_ = _num(m[c])
        vals[cid], sups[cid] = v.values, s_.values.astype(bool)
    nat = body[body[1].astype(str).str.startswith("Schweiz")]
    natrow = pd.Series({cid: pd.to_numeric(nat[c], errors="coerce").iloc[0] for c, cid in cols.items()})
    return pd.DataFrame(vals, index=idx), pd.DataFrame(sups, index=idx), natrow


def _case(year: int, case: str, suffix: str):
    if case == "all_normal" and year in BUILD_ALL_NORMAL:
        # tax yield: taxpayers without federal tax contribute nothing (their tax sheet is all '-')
        parts = ("with_normal",) if suffix == "24" else ("with_normal", "none_normal")
        tabs = [_case(year, c, suffix) for c in parts]
        if len(tabs) == 1:
            return tabs[0]
        idx = tabs[0][0].index.union(tabs[1][0].index)
        cols = sorted(set(tabs[0][0].columns) | set(tabs[1][0].columns))
        v = sum(t[0].reindex(index=idx, columns=cols).fillna(0) for t in tabs)
        s_ = np.logical_or.reduce([t[1].reindex(index=idx, columns=cols).fillna(False).astype(bool) for t in tabs])
        s_ = pd.DataFrame(s_, index=idx, columns=cols)
        v = v.mask(s_)
        nat = sum(t[2].reindex(cols).fillna(0) for t in tabs)
        return v, s_, nat
    p = _new_file(year, case)
    prefix = str(FILE_NO[case])[0]
    return _new_table(p, prefix + suffix)


def _new_year(year: int) -> tuple[pd.DataFrame, dict]:
    """Municipality rows (wide) and national totals for one 2020+ year."""
    tabs = {(c, k): _case(year, c, suf)
            for c in ("all_normal", "all_special") for k, suf in
            (("n", "21"), ("net", "22"), ("taxable", "23"), ("tax", "24"))}
    for c in ("none_normal", "none_special"):
        tabs[(c, "n")] = _case(year, c, "21")
    idx = sorted(set().union(*[set(t[0].index) for t in tabs.values()]))
    w = pd.DataFrame(index=idx)

    def put(col, parts, cls="total"):
        v = sum(tabs[p][0][cls].reindex(idx) for p in parts)
        s_ = np.logical_or.reduce([tabs[p][1][cls].reindex(idx).fillna(False).astype(bool) for p in parts])
        w[col], w[col + SUP] = v, s_

    put("taxpayers", [("all_normal", "n"), ("all_special", "n")])
    put("no_tax", [("none_normal", "n"), ("none_special", "n")])
    put("net", [("all_normal", "net"), ("all_special", "net")])
    put("taxable", [("all_normal", "taxable"), ("all_special", "taxable")])
    put("tax", [("all_normal", "tax"), ("all_special", "tax")])
    put("taxpayers_normal", [("all_normal", "n")])
    for cid in CLASS_IDS:
        put(f"cls_{cid}", [("all_normal", "n")], cls=cid)
    # taxable income > CHF 100,000 (normal cases): sum of the four upper classes, or total minus
    # the six lower classes where an upper class is suppressed
    # (2020: the all-normal file is wrong, see BUILD_ALL_NORMAL; taxpayers with taxable income above
    # CHF 100k all pay federal tax, so the 'with tax' normal-case file is used for this count)
    src = _case(year, "with_normal", "21") if year in BUILD_ALL_NORMAL else tabs[("all_normal", "n")]
    v, s_ = src[0].reindex(idx), src[1].reindex(idx).fillna(True)
    for c in CLASS_IDS:
        if c not in v:
            v[c], s_[c] = 0.0, False
    up, low = CLASS_IDS[6:], CLASS_IDS[:6]
    hi = np.where(~s_[up].any(axis=1), v[up].sum(axis=1),
                  np.where(~s_[low].any(axis=1) & ~s_["total"], v["total"] - v[low].sum(axis=1), np.nan))
    present = pd.Index(idx).isin(src[0].index)
    w["tp_100k"], w["tp_100k" + SUP] = hi, np.isnan(hi) & present
    nat = {k: tabs[k][2]["total"] for k in tabs}
    n = {"taxpayers": nat[("all_normal", "n")] + nat[("all_special", "n")],
         "no_tax": nat[("none_normal", "n")] + nat[("none_special", "n")],
         "net": nat[("all_normal", "net")] + nat[("all_special", "net")],
         "taxable": nat[("all_normal", "taxable")] + nat[("all_special", "taxable")],
         "tax": nat[("all_normal", "tax")] + nat[("all_special", "tax")],
         "taxpayers_normal": nat[("all_normal", "n")],
         "tp_100k": float(src[2].reindex(up).sum())}
    return w.rename_axis("bfs_nr").reset_index(), n


# ---------- old format (2001-2019) ------------------------------------------------------------
def _old_sheet(x: pd.ExcelFile, name: str) -> pd.DataFrame:
    sheet = [s for s in x.sheet_names if s.strip() == name][0]
    d = pd.read_excel(x, sheet, header=None, dtype=str)
    d["gde"] = pd.to_numeric(d[1], errors="coerce")
    d["name"] = d[2].astype(str).str.strip()
    return d


def _old_total(d: pd.DataFrame, col: int) -> tuple[pd.DataFrame, float]:
    m = d[(d["gde"] > 0) & (d["gde"] < 9000)]
    v, s = _num(m[col])
    nat = d[d["name"].str.upper().str.startswith("SCHWEIZ")]
    natv = float(pd.to_numeric(nat[col], errors="coerce").iloc[0]) if len(nat) else np.nan
    return pd.DataFrame({"v": v.values, "s": s.values}, index=m["gde"].astype(int).values), natv


def _old_year(year: int) -> tuple[pd.DataFrame, dict]:
    x = pd.ExcelFile(year_file(year))
    parts, nat = {}, {}
    hdr241 = _old_sheet(x, "241")
    tot_col = max(c for c in hdr241.columns if isinstance(c, int) and
                  hdr241[c].astype(str).str.strip().eq("Total").any())
    # amounts: Total column of 242-244 (complete). The count Total of 241 is '*' wherever a class
    # is suppressed, so the count of taxpayers with tax is taken from 211 + 212 (by occupation).
    for key, sh, scale in (("net_tax", "242", 1000), ("taxable_tax", "243", 1000), ("tax", "244", 1)):
        d = _old_sheet(x, sh)
        t, nv = _old_total(d, tot_col)
        t["v"] *= scale
        parts[key], nat[key] = t, nv * scale
    groups = [("n_tax", ("211", "212"), 5, 1)]
    if year >= INCOME_FROM:
        groups += [("n_none", ("311", "312"), 5, 1), ("net_none", ("311", "312"), 13, 1000),
                   ("taxable_none", ("311", "312"), 14, 1000)]
    if True:
        for key, sheets, col, scale in groups:
            acc_v, acc_s, acc_n = None, None, 0.0
            for sh in sheets:
                d = _old_sheet(x, sh)
                hdr = re.sub(r"-\s+", "", " ".join(map(str, d.iloc[:16, col].tolist())))
                exp = {5: "Steuerpflichtige", 13: "Reines", 14: "Steuerbares"}[col]
                if exp not in hdr:
                    raise ValueError(f"{year} {sh}: column {col} is not '{exp}'")
                t, nv = _old_total(d, col)
                acc_v = t["v"] if acc_v is None else acc_v.add(t["v"], fill_value=np.nan)
                acc_s = t["s"] if acc_s is None else (acc_s | t["s"].reindex(acc_s.index, fill_value=True))
                acc_n += nv
            parts[key] = pd.DataFrame({"v": acc_v * scale, "s": acc_s})
            nat[key] = acc_n * scale
    if year < INCOME_FROM:
        d = _old_sheet(x, "3")
        tcol = max(c for c in d.columns if isinstance(c, int) and d[c].astype(str).str.strip().eq("Total").any())
        parts["n_none"], nat["n_none"] = _old_total(d, tcol)
    idx = sorted(set().union(*[set(df.index) for df in parts.values()]))
    w = pd.DataFrame(index=idx)

    def put(col, keys):
        v = sum(parts[k]["v"].reindex(idx) for k in keys)
        s = np.any([parts[k]["s"].reindex(idx).fillna(False).astype(bool) for k in keys], axis=0)
        w[col], w[col + SUP] = v, s

    put("taxpayers", ["n_tax", "n_none"])
    put("no_tax", ["n_none"])
    put("tax", ["tax"])
    n = {"taxpayers": nat["n_tax"] + nat["n_none"], "no_tax": nat["n_none"], "tax": nat["tax"]}
    if year >= INCOME_FROM:
        put("net", ["net_tax", "net_none"])
        put("taxable", ["taxable_tax", "taxable_none"])
        n["net"] = nat["net_tax"] + nat["net_none"]
        n["taxable"] = nat["taxable_tax"] + nat["taxable_none"]
    return w.rename_axis("bfs_nr").reset_index(), n


METRICS = {"taxpayers": "tax_np_taxpayers", "no_tax": "tax_np_taxpayers_no_federal_tax",
           "net": "tax_np_net_income_chf", "taxable": "tax_np_taxable_income_chf",
           "tax": "tax_np_federal_tax_chf", "taxpayers_normal": "tax_np_taxpayers_normal",
           "tp_100k": "tax_np_normal_taxable_100k_plus",
           **{f"cls_{c}": f"tax_np_normal_taxable_class_{c}" for c in CLASS_IDS}}


def load_wide() -> pd.DataFrame:
    parts = []
    for y in YEARS:
        w, n = (_new_year(y) if y >= NEW_FROM else _old_year(y))
        w["period"] = str(y)
        NATIONAL[str(y)] = n
        parts.append(w)
    return pd.concat(parts, ignore_index=True)


def observations() -> pd.DataFrame:
    w = load_wide()
    cols = [c for c in METRICS if c in w.columns]
    obs = per_period_to_reference(w, {c: METRICS[c] for c in cols}, SOURCE, log=VINTAGE_LOG)
    # metrics that do not exist for a year (income before 2008, classes before 2020) -> drop rows
    has = obs.groupby(["metric_id", "period"])["status"].transform(lambda st: (st != "no_data").any())
    obs = obs[has]
    # national totals as published (native)
    nat = pd.DataFrame([{"unit_id": "CH", "period": p, **v} for p, v in NATIONAL.items()])
    native = emit(nat, {c: METRICS[c] for c in METRICS if c in nat}, "period", SOURCE, level="schweiz",
                  unit_col="unit_id", vintage=REFERENCE_DATE, provenance="native")
    native = native[native["value"].notna()]
    return pd.concat([obs, native], ignore_index=True)[OBS_COLUMNS]
