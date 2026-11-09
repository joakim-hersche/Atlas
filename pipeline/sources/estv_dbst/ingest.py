"""ESTV direct federal tax statistics, natural persons, by municipality (tax years 2001-2023).

Population: all taxpayers (tax units; a married couple is one taxpayer), with and without a federal
tax, normal and special cases together. This is the only definition that is available for every
year with one meaning:
  2001-2019 'auswertung' workbooks: taxpayers with federal tax, normal + special cases (sheets
            241-244, Total column) + taxpayers without federal tax, normal + special cases
            (sheet 3 counts 2001-2007; sheets 311 + 312 with incomes from 2008).
  2020-2023 separate files per case: all taxpayers normal cases (2023: file 500, 2020-22:
            '...-normalfall') + special cases (600 / '...-sonderfall'); taxpayers without tax:
            300 + 400 / '...-ohne-belastung-normalfall' + '...-sonderfall'.
Income amounts are only complete (incl. taxpayers without tax) from 2008; for 2001-2007 only the
taxpayer counts and the federal tax yield are delivered.
Income-class distribution (10 classes of taxable income, incl. CHF 100,001+) exists only in the
2020+ format, and it is taken from the normal cases (file 500) with its own denominator, so the
share above CHF 100k is a share of normal-case taxpayers.
Each year is on the municipality state of its tax year: inferred per year, reprojected to the
reference state (counts and amounts summed). '-' / '*' = suppressed (tax secrecy) -> status
suppressed. 1999/2000 and earlier (two-year periods, PDF before 1999) are not ingested.
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
YEARS = range(2001, 2024)
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
def _new_file(year: int, case: str):
    """case: 'all_normal' | 'all_special' | 'none_normal' | 'none_special'."""
    ls = links()
    if year >= 2023:
        n = {"all_normal": 500, "all_special": 600, "none_normal": 300, "none_special": 400}[case]
        name = f"statistik-dbst-np-gemeinden-{year}-{n}.xlsx"
    else:
        kind = {"all_normal": "normalfall", "all_special": "sonderfall",
                "none_normal": "ohne-belastung-normalfall", "none_special": "ohne-belastung-sonderfall"}[case]
        cands = [k for k in ls if re.fullmatch(rf"statistik-dbst-np-gden-{year}-{kind}(-de)?\.xlsx", k)]
        if not cands:
            raise FileNotFoundError(f"{year} {case}")
        name = cands[0]
    return fetch(ls[name], SOURCE, name)


def _new_sheet(path, suffix: str) -> pd.DataFrame:
    x = pd.ExcelFile(path)
    sheet = [s for s in x.sheet_names if s.strip().endswith(suffix) and s.strip()[:1].isdigit()][0]
    d = pd.read_excel(x, sheet, header=None, dtype=str)
    hdr = d.index[d[2].astype(str).str.strip() == "Gemeinde ID"][0]
    labels = [str(v).strip() for v in d.iloc[hdr, 4:15]]
    if not (labels[0] == "0" and labels[1].startswith("1 -") and labels[-1].startswith("Total")):
        raise ValueError(f"{path.name} {sheet}: unexpected class header {labels}")
    body = d.iloc[hdr + 1:].copy()
    body["gde"] = pd.to_numeric(body[2], errors="coerce")
    body["kt"] = pd.to_numeric(body[0], errors="coerce")
    return body


def _new_year(year: int) -> tuple[pd.DataFrame, dict]:
    """Municipality rows (wide) and national totals for one 2020+ year."""
    out, nat = {}, {}
    for case in ("all_normal", "all_special", "none_normal", "none_special"):
        p = _new_file(year, case)
        sheets = {"n": "21", "net": "22", "taxable": "23", "tax": "24"} if case.startswith("all") else {"n": "21"}
        for k, suf in sheets.items():
            b = _new_sheet(p, suf)
            m = b[(b["gde"] > 0) & (b["gde"] < 9000)]
            v, s = _num(m[14])
            out[(case, k)] = pd.DataFrame({"v": v.values, "s": s.values}, index=m["gde"].astype(int).values)
            ch = b[(b["gde"] == 10000) & (b["kt"] == 27)]
            nat[(case, k)] = float(pd.to_numeric(ch[14], errors="coerce").iloc[0])
            if case == "all_normal" and k == "n":
                cl = {}
                for j, cid in enumerate(CLASS_IDS):
                    cv, cs = _num(m[4 + j])
                    cl[cid] = (cv.values, cs.values)
                # taxpayers with taxable income > CHF 100,000: sum of the four upper classes, or
                # total minus the six lower classes where an upper class is suppressed
                up = np.nansum([cl[c][0] for c in CLASS_IDS[6:]], axis=0)
                up_sup = np.any([cl[c][1] for c in CLASS_IDS[6:]], axis=0)
                low = np.nansum([cl[c][0] for c in CLASS_IDS[:6]], axis=0)
                low_sup = np.any([cl[c][1] for c in CLASS_IDS[:6]], axis=0)
                tot = v.values
                hi = np.where(~up_sup, up, np.where(~low_sup & ~s.values, tot - low, np.nan))
                out[("cls", "100k")] = pd.DataFrame({"v": hi, "s": np.isnan(hi)}, index=m["gde"].astype(int).values)
                for cid in CLASS_IDS:
                    out[("cls", cid)] = pd.DataFrame({"v": cl[cid][0], "s": cl[cid][1]},
                                                     index=m["gde"].astype(int).values)
    idx = sorted(set().union(*[set(df.index) for df in out.values()]))
    w = pd.DataFrame(index=idx)

    def put(col, parts):
        v = sum(out[p]["v"].reindex(idx) for p in parts)
        s = np.any([out[p]["s"].reindex(idx).fillna(True).astype(bool) for p in parts], axis=0)
        w[col], w[col + SUP] = v, s

    put("taxpayers", [("all_normal", "n"), ("all_special", "n")])
    put("no_tax", [("none_normal", "n"), ("none_special", "n")])
    put("net", [("all_normal", "net"), ("all_special", "net")])
    put("taxable", [("all_normal", "taxable"), ("all_special", "taxable")])
    put("tax", [("all_normal", "tax"), ("all_special", "tax")])
    put("taxpayers_normal", [("all_normal", "n")])
    put("tp_100k", [("cls", "100k")])
    for cid in CLASS_IDS:
        put(f"cls_{cid}", [("cls", cid)])
    n = {"taxpayers": nat[("all_normal", "n")] + nat[("all_special", "n")],
         "no_tax": nat[("none_normal", "n")] + nat[("none_special", "n")],
         "net": nat[("all_normal", "net")] + nat[("all_special", "net")],
         "taxable": nat[("all_normal", "taxable")] + nat[("all_special", "taxable")],
         "tax": nat[("all_normal", "tax")] + nat[("all_special", "tax")],
         "taxpayers_normal": nat[("all_normal", "n")]}
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
    for key, sh, scale in (("n_tax", "241", 1), ("net_tax", "242", 1000), ("taxable_tax", "243", 1000),
                           ("tax", "244", 1)):
        d = _old_sheet(x, sh)
        t, nv = _old_total(d, tot_col)
        t["v"] *= scale
        parts[key], nat[key] = t, nv * scale
    if year >= INCOME_FROM:
        for key, (col, scale) in {"n_none": (5, 1), "net_none": (13, 1000), "taxable_none": (14, 1000)}.items():
            acc_v, acc_s, acc_n = None, None, 0.0
            for sh in ("311", "312"):
                d = _old_sheet(x, sh)
                hdr = " ".join(map(str, d.iloc[:16, col].tolist()))
                exp = {5: "Steuerpflichtige", 13: "Reines", 14: "Steuerbares"}[col]
                if exp not in hdr:
                    raise ValueError(f"{year} {sh}: column {col} is not '{exp}'")
                t, nv = _old_total(d, col)
                acc_v = t["v"] if acc_v is None else acc_v.add(t["v"], fill_value=np.nan)
                acc_s = t["s"] if acc_s is None else (acc_s | t["s"].reindex(acc_s.index, fill_value=True))
                acc_n += nv
            parts[key] = pd.DataFrame({"v": acc_v * scale, "s": acc_s})
            nat[key] = acc_n * scale
    else:
        d = _old_sheet(x, "3")
        tcol = max(c for c in d.columns if isinstance(c, int) and d[c].astype(str).str.strip().eq("Total").any())
        parts["n_none"], nat["n_none"] = _old_total(d, tcol)
    idx = sorted(set().union(*[set(df.index) for df in parts.values()]))
    w = pd.DataFrame(index=idx)

    def put(col, keys):
        v = sum(parts[k]["v"].reindex(idx) for k in keys)
        s = np.any([parts[k]["s"].reindex(idx).fillna(True).astype(bool) for k in keys], axis=0)
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
    obs = obs[~((obs["status"] == "no_data") & obs["value"].isna())]
    # national totals as published (native)
    nat = pd.DataFrame([{"unit_id": "CH", "period": p, **v} for p, v in NATIONAL.items()])
    native = emit(nat, {c: METRICS[c] for c in METRICS if c in nat}, "period", SOURCE, level="schweiz",
                  unit_col="unit_id", vintage=REFERENCE_DATE, provenance="native")
    native = native[native["value"].notna()]
    return pd.concat([obs, native], ignore_index=True)[OBS_COLUMNS]
