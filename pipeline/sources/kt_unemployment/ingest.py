"""Registered unemployed per municipality of residence, compiled from cantonal sources (`*`, D6).
All are SECO AVAM/PLASTA extracts (same definition: registered unemployed at the RAV).

- ZH  Gemeindeporträt 107 Arbeitslose [Anz.], annual mean, 1991–2024 (ZH back-casts some merged
      municipalities, see kthelp.zh_current). Missing values for small municipalities are
      treated as suppressed (smallest published value 6).
- GE  OCSTAT T 03.03.4.01 chômeurs inscrits par commune de résidence, moyennes annuelles,
      1990–2025 (45 communes; 'Non spécifié' only in the canton total). Breaks noted by OCSTAT:
      2011 (LACI revision), 2012 (LIASI), 2018 (SECO reclassification of job seekers).
- VD  Statistique Vaud DE_Chomeurs_Taux_com.xlsx: monthly snapshot (latest month, previous month,
      same month a year earlier), only communes with more than 1000 economically active
      residents and values of at least 6; other communes -> suppressed. Periods 'YYYY-MM'.
Derived: per 100 residents aged 20–64 (STATPOP pop_age_20_64). The 20–64 group is used because
STATPOP delivers it for every municipality; ZH's own rate uses the 15–64 population and SECO's
rate the labour force (Structural Survey), so values are not the official unemployment rate.
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.sources.kt_finance.kthelp import complete, fetch_retry, match_names, ref_units, to_ref, zh_current

SOURCE = "kt_unemployment"
M = "unemp_registered"
GE_URL = "https://statistique.ge.ch/tel/domaines/03/03_03/T_03_03_4_01.xlsx"
VD_URL = "https://www.vd.ch/fileadmin/user_upload/organisation/dfin/statvd/Dom_03/Tableaux/DE_Chomeurs_Taux_com.xlsx"
MONTHS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
          "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}
VD_NAMES = {"Bussigny-près-Lausanne": 5624, "Arzier": 5702}  # older names used by Statistique Vaud
NOT_COVERED = {
    "SG": "St.Gallen's STADA2 database host (stada2.sg.ch) is not reachable from the pipeline",
    "AG": "Aargau publishes municipal unemployment only as monthly PDFs",
    "LU": "Lucerne publishes municipal unemployment only in PDF profiles",
    "BS": "Basel-Stadt publishes only a rate for Riehen and Bettingen (no counts)",
}
DEFAULT_NC = "this canton publishes no registered unemployed per municipality"


def zh() -> tuple[pd.DataFrame, pd.DataFrame]:
    g, k = zh_current(107, SOURCE)
    w = g[["bfs_nr", "year", "value"]].rename(columns={"year": "period", "value": "n"})
    w["n__sup"] = w["n"].isna()
    kt = k[["year", "value"]].rename(columns={"year": "period", "value": "n"}).assign(unit="ZH")
    return w, kt


def ge() -> tuple[pd.DataFrame, pd.DataFrame]:
    path = fetch_retry(GE_URL, SOURCE, "T_03_03_4_01.xlsx")
    rows = []
    for sh in pd.ExcelFile(path).sheet_names:
        s = pd.read_excel(path, sheet_name=sh, header=None)
        hdr = next(i for i in range(len(s)) if s.iloc[i, 1:].astype(str).str[:4].str.isdigit().sum() >= 5)
        years = {c: int(str(v)[:4]) for c, v in s.iloc[hdr].items() if str(v)[:4].isdigit()}
        for _, r in s.iloc[hdr + 1:].iterrows():
            name = str(r[0]).strip() if pd.notna(r[0]) else ""
            if not name or name.startswith("(") or name.startswith("Source"):
                continue
            for c, y in years.items():
                v = r[c]
                rows.append((name, y, 0.0 if str(v).strip() == "-" else pd.to_numeric(v, errors="coerce")))
            if name == "Canton":  # footnotes follow
                break
    d = pd.DataFrame(rows, columns=["name", "period", "n"]).drop_duplicates(["name", "period"])
    kt = d[d["name"].eq("Canton")].assign(unit="GE").drop(columns="name")
    d = d[~d["name"].isin(["Canton", "Non spécifié"])]
    m = match_names(d["name"].unique(), "GE")
    miss = set(d["name"]) - set(m)
    if miss:
        raise ValueError(f"GE names not matched: {miss}")
    return d.assign(bfs_nr=d["name"].map(m)).drop(columns="name"), kt


def vd() -> pd.DataFrame:
    path = fetch_retry(VD_URL, SOURCE, "DE_Chomeurs_Taux_com.xlsx")
    s = pd.read_excel(path, sheet_name="effectifs", header=None)
    hdr = next(i for i in range(len(s)) if str(s.iloc[i, 0]).startswith("Communes"))
    chom = [c for c in range(1, s.shape[1]) if "dont" in str(s.iloc[hdr, c])]  # 'dont chômeurs'
    per = {}
    for c in range(1, s.shape[1]):
        lab = s.iloc[hdr - 1, c]
        if pd.notna(lab):  # month label of a 3-column block: attach it to the nearest 'dont chômeurs'
            mon, yr = str(lab).strip().lower().split()
            per[min(chom, key=lambda j: abs(j - c))] = f"{int(yr)}-{MONTHS[mon]:02d}"
    assert len(per) == len(chom), (per, chom)
    body = s.iloc[hdr + 1:]
    body = body[body[0].notna() & ~body[0].astype(str).str.startswith(("Remarques", "1)", "2)", "-", "Sources"))]
    m = match_names(body[0].astype(str).str.strip().unique(), "VD", extra=VD_NAMES)
    miss = set(body[0].astype(str).str.strip()) - set(m)
    if miss:
        raise ValueError(f"VD names not matched: {miss}")
    rows = []
    for _, r in body.iterrows():
        for c, p in per.items():
            v = r[c]
            sup = pd.isna(v) or str(v).strip() in ("-", "")
            rows.append((m[str(r[0]).strip()], p, pd.to_numeric(v, errors="coerce"), sup))
    w = pd.DataFrame(rows, columns=["bfs_nr", "period", "n", "n__sup"])
    # communes not listed (fewer than 1000 economically active residents): suppressed
    vd_all = ref_units().query("canton == 'VD'")["bfs_nr"]
    extra = [(b, p, float("nan"), True) for p in per.values() for b in vd_all if b not in set(w["bfs_nr"])]
    return pd.concat([w, pd.DataFrame(extra, columns=w.columns)], ignore_index=True)


def observations() -> pd.DataFrame:
    parts, natives, cov = [], [], {}
    for kt, fn in (("ZH", zh), ("GE", ge), ("VD", vd)):
        res = fn()
        w, k = res if isinstance(res, tuple) else (res, None)
        w["period"] = w["period"].astype(str)
        o = to_ref(w, {"n": M}, SOURCE, kt)
        sup = o["status"].eq("suppressed")
        o.loc[sup, "note"] = {"ZH": "not published by ZH (small numbers)",
                              "GE": "not published",
                              "VD": "not published by VD (fewer than 1000 economically active residents or fewer than 6 unemployed)"}[kt]
        if kt == "VD":
            o.loc[~sup, "note"] = "monthly count (VD publishes only the latest months)"
        parts.append(o)
        cov[(M, kt)] = set(w["period"])
        if k is not None:
            k["period"] = k["period"].astype(int).astype(str)
            natives.append(emit(k, {"n": M}, "period", SOURCE, level="kanton", unit_col="unit", provenance="native"))
    obs = pd.concat(parts, ignore_index=True)
    obs = complete(obs, SOURCE, {M: {"ZH", "GE", "VD"}}, NOT_COVERED, DEFAULT_NC, covered_periods=cov)
    nat = pd.concat(natives, ignore_index=True)
    return pd.concat([obs, nat[nat["status"] == "ok"]], ignore_index=True)
