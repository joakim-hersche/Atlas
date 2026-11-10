"""Municipal finance key ratios per Gemeinde, compiled from cantonal publishers (`*` metric, D2/D4).

Metrics (HRM2 definitions, FDK/KKAG Fachempfehlung 18):
- fin_net_debt_per_capita   Nettoschuld I per resident, CHF = (Fremdkapital − Finanzvermögen) /
                            residents. Positive = net debt, negative = net assets.
- fin_self_financing_ratio  Selbstfinanzierungsgrad, % = Selbstfinanzierung / Nettoinvestitionen.
- fin_tax_revenue_chf       Fiskalertrag (HRM2 Kontenart 40), CHF; per resident as a derived ratio.

Per canton (period = accounting year):
- ZH  Gemeindeporträt OGD 431 Nettovermögen [Fr./Einw.] (sign flipped), 434 SFG, 297 Steuerertrag
      politische + Schulgemeinde [Mio. Fr.]. 1990–2024; HRM1 until 2018, HRM2 from 2019. ZH
      back-casts some merged municipalities (see kthelp.zh_current). Political municipality only: the
      separate school municipalities (Schulgemeinden) are not included in 431/434.
- LU  LUSTAT gefis-lu-jr.csv (full HRM2 accounts, 2019–2025): ratios computed here (formula
      below); residents = STATPOP 31 Dec of the year (municipality file of that year).
- BL  ADS BL Gemeindefinanzen 2014–2025 (full HRM2 accounts, HRM2 since 2014): computed as LU.
- FR  SCom 18_02_indicateurs (MCH2 since 2021/22): Nettoschuld je Einwohner, SFG, 2022–2024.
- SO  GEFIN KZ07 Nettoschuld I / Einwohner and KZ02 SFG, 2021–2025 (HRM2 since 2016).
- AG  eDossier 2025 T12 (one edition online): Nettoschuld I pro Einwohner, SFG ('...' = not
      computable -> not_applicable).
- GR  data.gr.ch Finanzkennzahlen 2019–2024 (HRM2 since 2018 per canton law).
- TG  sk-stat-4 politische Gemeinden 2019–2024 (school municipalities separate, not included).
- GE  OCSTAT T 18.02.2.04 dette nette par habitant 2000–2024 (MCH2 from 2018; earlier MCH1).
- VD  Indicateurs par commune 2017–2025: degré d'autofinancement (fraction ×100). VD communes
      mix MCH1 and MCH2. Rows with 100% and no investments (proportion des investissements 0)
      are a convention for 'no net investment' -> not_applicable.
- ZG  data.zg.ch dataset 'Gemeindefinanzen' (store/1/resource/840): Nettoschuld pro Einwohner
      (resource 841) and Selbstfinanzierungsgrad (2151), 2014–2025, 11 Einwohnergemeinden.
- SG  STADA2 (Fachstelle für Statistik SG) CSV export, 'Gemeindefinanzen RMSG' 2017–2025:
      2008 Nettoschuld pro Einwohner I RMSG (Fremdkapital − passivierte Anschlussbeiträge −
      Finanzvermögen), 2000 Selbstfinanzierungsgrad RMSG (annual), 2043 '40 Fiskalertrag [Fr.]'.
      '***' = not computable: SFG alone -> not_applicable; all ratios '***' (accounts not
      available in RMSG form, mostly 2017/18) -> no_data. STADA2 lists current municipalities.
- TI  SEL Statistica finanziaria dei comuni, allegato statistico per comune (one workbook per
      year, 2000–2024): 'Debito pubblico pro capite' / 'Debito pubblico netto I procapite',
      'Grado di autofinanziamento' (fraction ×100; 'nd'/'non calcolato' -> not_applicable) and
      revenue type 40 (imposte / ricavi fiscali, 1'000 fr.). MCA2 (HRM2) indicators from 2022;
      up to 2021 MCA1 definitions (debito pubblico = capitale di terzi + finanziamenti speciali −
      beni patrimoniali, per the report's 'Calcolo debito pubblico'), noted as HRM1. Communes are
      named only: matched to the BFS numbers valid in that year. Rows labelled with an earlier
      year ('Tegna (2004)': last accounts available) are skipped.
Computed formula (LU, BL):
  Nettoschuld I = Σ accounts 20 (Fremdkapital) − Σ accounts 10 (Finanzvermögen), balance 31 Dec
  Selbstfinanzierung = Ertrag − Aufwand (ER without closing accounts 9) + 33 + 35 − 45 + 364 + 365
      + 366 + 383 + 387 + 389 − 4490 − 466 − 487 − 489
  Nettoinvestitionen = Σ 5 (without 59) − Σ 6 (without 69); SFG not computable if ≤ 0.
Checked against LUSTAT's Gemeindeprofil Luzern 2024 (Nettoschuld −5,249 Fr./Einw.; SFG 5 years
171.7%) and BL 10650 (Steuerertrag 2025 Aesch 31,214 kCHF).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit
from pipeline.sources.bfs_statpop_geodata.fetch import municipalities
from pipeline.sources.kt_finance import fetch as F
from pipeline.sources.kt_finance.kthelp import complete, match_names, match_names_at, to_ref

SOURCE = "kt_finance"
NET, SFG, TAX = "fin_net_debt_per_capita", "fin_self_financing_ratio", "fin_tax_revenue_chf"
RULES = {"net": "not_aggregatable", "sfg": "not_aggregatable", "tax": "sum"}
MAP = {"net": NET, "sfg": SFG, "tax": TAX}
NA_NOTES = {SFG: "self-financing ratio not computable (net investments ≤ 0 or negative self-financing; "
                 "source shows no value)"}
HRM1 = {"ZH": 2019, "GE": 2018, "TI": 2022}  # first HRM2 year where the published series also covers HRM1
NOT_COVERED = {
    "BE": ("Bern publishes municipal finances as PDF reports; its eBericht host (www.ebericht.be.ch) "
           "serves an incomplete TLS certificate chain, so downloads cannot be verified"),
    "AR": "Appenzell Ausserrhoden publishes municipal finance statistics only as PDF reports",
    "VS": "Valais publishes municipal finance reports only as PDF (no per-municipality export found)",
    "GL": "Glarus (3 municipalities) publishes only a PDF on a host not available to the pipeline",
    "NE": "Neuchâtel publishes the indicators only as PDF",
    "SH": "Schaffhausen publishes the indicators only as PDF",
    "JU": "Jura publishes no machine-readable municipal finance indicators",
    "BS": "Basel-Stadt (3 municipalities) publishes no municipal finance indicators; the city of Basel is covered by BFS city finances",
}
DEFAULT_NC = "this canton publishes no machine-readable municipal finance indicators"


def _pop(year: int) -> pd.Series:
    d = pd.read_parquet(municipalities(year), columns=["GDENR", "BBTOT"])
    return d.set_index("GDENR")["BBTOT"]


def _hrm2(acc: pd.DataFrame) -> pd.DataFrame:
    """acc: bfs_nr, period, teil (Bilanz|Erfolgsrechnung|Investitionsrechnung), art (str), amount
    (positive amounts per account class). Returns bfs_nr, period, net, sfg, tax + sfg__na."""
    a, s, t = acc["art"], acc["amount"], acc["teil"]
    B, E, I = t.eq("Bilanz"), t.eq("Erfolgsrechnung"), t.eq("Investitionsrechnung")
    key = [acc["bfs_nr"], acc["period"]]

    def tot(mask):
        return s.where(mask, 0.0).groupby(key).sum()

    def er(*prefixes):
        return tot(E & a.str.startswith(prefixes))

    out = pd.DataFrame({
        "fk": tot(B & a.str.startswith("20")), "fv": tot(B & a.str.startswith("10")),
        "ertrag": er("4"), "aufwand": er("3"),
        "plus": er("33", "35", "364", "365", "366", "383", "387", "389"),
        "minus": er("45", "4490", "466", "487", "489"),
        "ia": tot(I & a.str.startswith("5") & ~a.str.startswith("59")),
        "ie": tot(I & a.str.startswith("6") & ~a.str.startswith("69")),
        "tax": er("40"),
    })
    out.index.names = ["bfs_nr", "period"]
    out = out.reset_index()
    sf = out["ertrag"] - out["aufwand"] + out["plus"] - out["minus"]
    ni = out["ia"] - out["ie"]
    out["sfg"] = (sf / ni * 100).where(ni > 0)
    out["sfg__na"] = ~(ni > 0)
    pops = []
    for y, g in out.groupby("period"):
        p = _pop(int(y))
        pops.append(g["bfs_nr"].map(p))
    out["pop"] = pd.concat(pops)
    out["net"] = (out["fk"] - out["fv"]) / out["pop"]
    return out[["bfs_nr", "period", "net", "sfg", "sfg__na", "tax"]]


def lu() -> pd.DataFrame:
    d = pd.read_csv(F.lu(), sep=";", dtype={"art_nr": str, "gnr": int, "jahr": int})
    d = d[d["art_nr"].str.match(r"^\d")]
    acc = pd.DataFrame({"bfs_nr": d["gnr"], "period": d["jahr"], "teil": d["erhebungsteil"],
                        "art": d["art_nr"], "amount": pd.to_numeric(d["saldo"])})
    return _hrm2(acc)


def bl() -> pd.DataFrame:
    d = pd.read_csv(F.bl_file(), sep=";", encoding="latin-1", dtype=str)
    amt = pd.to_numeric(d["Betrag_CHF"].str.replace(r"[\s\xa0']", "", regex=True), errors="coerce").fillna(0)
    acc = pd.DataFrame({"bfs_nr": d["BFS_Nummer"].astype(int), "period": d["Jahr"].astype(int),
                        "teil": d["Rechnungsteil"], "art": d["Kontenart_Nr"].fillna(""), "amount": amt})
    acc = acc[acc["period"] >= 2014]
    return _hrm2(acc)


def zh() -> tuple[pd.DataFrame, pd.DataFrame]:
    parts, kts = [], []
    for ind, col, f in ((431, "net", -1.0), (434, "sfg", 1.0), (297, "tax", 1e6)):
        g, k = F.zh(ind)
        parts.append(g[["bfs_nr", "year", "value"]].assign(value=lambda x: x["value"] * f)
                     .rename(columns={"year": "period", "value": col}).set_index(["bfs_nr", "period"]))
        kts.append(k[["year", "value"]].assign(value=lambda x: x["value"] * f)
                   .rename(columns={"year": "period", "value": col}).set_index("period"))
    w = pd.concat(parts, axis=1).reset_index()
    kt = pd.concat(kts, axis=1).reset_index().assign(unit="ZH")
    return w, kt


def fr() -> pd.DataFrame:
    d = F.fr()
    sel = {"Nettoschuld je Einwohner (CHF)": "net", "Selbstfinanzierungsgrad (%)": "sfg"}
    d = d[d["indicateur_de"].isin(sel)].assign(col=lambda x: x["indicateur_de"].map(sel))
    w = d.pivot_table(index=["commune_id", "annee"], columns="col", values="valeur", aggfunc="first")
    return w.reset_index().rename(columns={"commune_id": "bfs_nr", "annee": "period"})


def gr() -> pd.DataFrame:
    d = F.gr()
    sel = {"Nettoschuld/-vermögen(-) je Einwohner in CHF": "net", "Selbstfinanzierungsgrad in %": "sfg"}
    d = d[d["typ"].isin(sel)].assign(col=lambda x: x["typ"].map(sel))
    w = d.pivot_table(index=["bfs_nummer", "jahr"], columns="col", values="betrag", aggfunc="first")
    return w.reset_index().rename(columns={"bfs_nummer": "bfs_nr", "jahr": "period"})


def tg() -> pd.DataFrame:
    d = F.tg()
    return pd.DataFrame({"bfs_nr": d["bfs_nr_gemeinde"], "period": d["jahr"],
                         "net": d["nettoschuld_nettovermogen_pro_einwohner_in_chf"],
                         "sfg": d["selbstfinanzierungsgrad_in"]})


def _so_one(ratio: str, col: str) -> pd.DataFrame:
    lines = F.so(ratio).read_bytes().decode("latin-1").splitlines()
    i = next(n for n, line in enumerate(lines) if line.startswith("BFS-Nr."))
    from io import StringIO
    body = [ln for ln in lines[i + 1:] if ln[:1].isdigit()]  # drops the 'Mittelwert' row (shifted)
    d = pd.read_csv(StringIO("\n".join([lines[i], *body])), sep=";", index_col=False,
                    dtype={"BFS-Nr.": int})
    ycols = [c for c in d.columns if c[:4].isdigit()]
    m = d.melt(id_vars=["BFS-Nr."], value_vars=ycols, var_name="period", value_name=col)
    m["period"] = m["period"].str[:4].astype(int)
    m[col] = pd.to_numeric(m[col], errors="coerce")
    return m.rename(columns={"BFS-Nr.": "bfs_nr"}).set_index(["bfs_nr", "period"])


def so() -> pd.DataFrame:
    return pd.concat([_so_one("KZ07", "net"), _so_one("KZ02", "sfg")], axis=1).reset_index()


def ag() -> tuple[pd.DataFrame, pd.DataFrame]:
    a = pd.read_excel(F.ag(), sheet_name="T12", header=None, skiprows=5)
    a = a[pd.to_numeric(a[1], errors="coerce").notna()]
    na = a[15].astype(str).str.strip().eq("...")
    w = pd.DataFrame({"bfs_nr": a[1].astype(int), "name": a[2].astype(str), "period": 2025,
                      "net": pd.to_numeric(a[10], errors="coerce"), "sfg": pd.to_numeric(a[15], errors="coerce"),
                      "sfg__na": na})
    kt = w[w["name"].str.startswith("Kanton")].assign(unit="AG")
    w = w[~w["name"].str.startswith(("Kanton", "Bezirk"))]
    return w.drop(columns="name"), kt.drop(columns=["name", "bfs_nr"])


def ge() -> tuple[pd.DataFrame, pd.DataFrame]:
    path = F.ge()
    rows = []
    for sh in pd.ExcelFile(path).sheet_names:
        g = pd.read_excel(path, sheet_name=sh, header=None)
        hdr = next(i for i in range(len(g)) if pd.to_numeric(g.iloc[i, 1:], errors="coerce").between(1990, 2100).sum() >= 2)
        years = pd.to_numeric(g.iloc[hdr], errors="coerce")
        cols = [c for c in g.columns if pd.notna(years[c])]
        per_cap = cols[len(cols) // 2:]  # second block: 'Dette nette par habitant, en franc'
        for _, r in g.iloc[hdr + 1:].iterrows():
            name = str(r[0]).strip() if pd.notna(r[0]) else ""
            if not name or name.startswith("(") or name.startswith("Source"):
                continue
            for c in per_cap:
                rows.append((name, int(years[c]), pd.to_numeric(r[c], errors="coerce")))
    d = pd.DataFrame(rows, columns=["name", "period", "net"]).dropna(subset=["net"])
    kt = d[d["name"].eq("Ensemble")].assign(unit="GE").drop(columns="name")
    d = d[~d["name"].eq("Ensemble")]
    m = match_names(d["name"].unique(), "GE")
    miss = set(d["name"]) - set(m)
    if miss:
        raise ValueError(f"GE names not matched: {miss}")
    d["bfs_nr"] = d["name"].map(m)
    return d.drop(columns="name").drop_duplicates(["bfs_nr", "period"]), kt


def vd() -> pd.DataFrame:
    v = pd.read_excel(F.vd())
    v.columns = ["period", "bfs_nr", "name", "tdn", "sfg", "dcc", "taf", "tdb", "pci", "psd", "pinv"]
    conv = v["sfg"].eq(1) & v["pinv"].eq(0)
    return pd.DataFrame({"bfs_nr": v["bfs_nr"].astype(int), "period": v["period"].astype(int),
                         "sfg": (v["sfg"] * 100).where(~conv), "sfg__na": conv})


def zg() -> pd.DataFrame:
    parts = []
    for col, res in F.ZG_RESOURCES.items():
        d = pd.read_csv(F.zg(res))
        val = next(c for c in d.columns if c not in ("jahr", "gemeinde", "bfscode"))
        parts.append(pd.DataFrame({"bfs_nr": d["bfscode"].astype(int), "period": d["jahr"].astype(int),
                                   col: pd.to_numeric(d[val], errors="coerce")}).set_index(["bfs_nr", "period"]))
    return pd.concat(parts, axis=1).reset_index()


def sg() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = F.sg()
    d["col"] = d["INDIKATOR_ID"].astype(int).map(F.SG_INDICATORS)
    d["bfs_nr"] = d["BFS_NR"].astype(int)
    d["period"] = d["INDIKATOR_JAHR"].astype(int)
    d["v"] = pd.to_numeric(d["INDIKATOR_VALUE"], errors="coerce")
    star = d["INDIKATOR_VALUE"].astype(str).str.strip().eq("***")
    w = d.pivot_table(index=["bfs_nr", "period"], columns="col", values="v", aggfunc="first")
    s = d.assign(star=star).pivot_table(index=["bfs_nr", "period"], columns="col", values="star", aggfunc="first")
    w = w.reindex(s.index)
    # '***' = not computable. SFG alone '***' (net debt published) = no net investments ->
    # not_applicable; all ratios '***' = accounts not available in RMSG form (2017/18, a few
    # later years) -> no_data.
    w["sfg__na"] = s["sfg"].fillna(False).astype(bool) & ~s["net"].fillna(False).astype(bool)
    w = w.reset_index()
    kt = w[w["bfs_nr"] == 17].drop(columns=["bfs_nr", "sfg__na"]).assign(unit="SG")
    return w[w["bfs_nr"] != 17], kt


TI_SKIP = re.compile(r"^(consuntivi|media|mediana|totale|\(|\[|\d|nb|mca|fonte|i dati|i valori|al beneficio|comuni |\*)", re.I)
TI_EXTRA = {"brione s/minusio": "Brione sopra Minusio"}


def _ti_name(raw: str, year: int) -> str | None:
    """Clean a commune label; None for footnotes and for rows that carry an older accounting year
    ('Tegna (2004)': last accounts available, not of this year)."""
    n = str(raw).strip()
    if not n or n == "nan" or TI_SKIP.match(n) or len(n) > 60:
        return None
    m = re.search(r"\((\d{4})\)\s*$", n)
    if m and int(m.group(1)) != year:
        return None
    n = re.sub(r"\((MCA2|\d)\)|\[\*+\]|\*|\(\d{4}\)", "", n).strip()
    return TI_EXTRA.get(n.lower(), n)


def _ti_sheet(path, pattern: str):
    for s in pd.ExcelFile(path).sheet_names:
        if re.match(pattern, str(pd.read_excel(path, sheet_name=s, header=None, nrows=1).iloc[0, 0])):
            return pd.read_excel(path, sheet_name=s, header=None)
    return None


def ti() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, totals = [], []
    for year, path in sorted(F.ti().items()):
        ind = _ti_sheet(path, rf"Tabella \d+ Indicatori finanziari, {year}")
        rev = _ti_sheet(path, r"Tabella \d+\w? Ricavi .*per genere.* a due cifre")
        hdr = [str(v).replace("\n", " ").replace("-", "").lower() for v in ind.iloc[1]]
        c_net = next(i for i, h in enumerate(hdr) if re.search(r"debito pubblico|dp netto", h) and re.search("pro ?capite|per abitante", h))
        c_sfg = next(i for i, h in enumerate(hdr) if "grado" in h and "autofin" in h)
        tax = {}
        if rev is not None:
            rh = [str(v).strip() for v in rev.iloc[1]]
            c40 = next(i for i, h in enumerate(rh) if re.match(r"40\b", h))
            for _, r in rev.iloc[2:].iterrows():
                if str(r[0]).strip().upper().startswith("TOTALE") and pd.notna(pd.to_numeric(r[c40], errors="coerce")):
                    totals.append((year, float(r[c40]) * 1000))
                n = _ti_name(r[0], year)
                v = pd.to_numeric(r[c40], errors="coerce")
                if n and pd.notna(v):
                    tax[n] = v * 1000  # 1'000 fr.
        for _, r in ind.iloc[2:].iterrows():
            n = _ti_name(r[0], year)
            if not n:
                continue
            sfg_raw = r[c_sfg]
            sfg = pd.to_numeric(sfg_raw, errors="coerce")
            rows.append((n, year, pd.to_numeric(r[c_net], errors="coerce"), sfg * 100,
                         pd.isna(sfg) and pd.notna(sfg_raw) and str(sfg_raw).strip() != "", tax.get(n, np.nan)))
    d = pd.DataFrame(rows, columns=["name", "period", "net", "sfg", "sfg__na", "tax"])
    # 2022: Maroggia, Melano and Rovio merged into Val Mara during the year; SEL reports the
    # merged accounts under the three names (footnote: computed for the new commune)
    d["name"] = d["name"].str.replace(r"^Maroggia\+Melano\+Rovio.*$", "Val Mara", regex=True)
    parts = []
    for y, g in d.groupby("period"):
        m = match_names_at(g["name"].unique(), "TI", int(y))
        miss = set(g["name"]) - set(m)
        if miss:
            raise ValueError(f"TI {y} names not matched: {sorted(miss)}")
        parts.append(g.assign(bfs_nr=g["name"].map(m)))
    out = pd.concat(parts, ignore_index=True).drop(columns="name")
    dup = out.duplicated(["bfs_nr", "period"], keep=False)
    if dup.any():
        raise ValueError(f"TI duplicate municipality rows: {out[dup].head()}")
    kt = pd.DataFrame(totals, columns=["period", "tax"]).assign(unit="TI")
    return out, kt


LOADERS = {"ZH": zh, "LU": lu, "BL": bl, "FR": fr, "SO": so, "AG": ag, "GR": gr, "TG": tg, "GE": ge, "VD": vd,
           "ZG": zg, "SG": sg, "TI": ti}


def observations() -> pd.DataFrame:
    parts, natives, covered_periods = [], [], {}
    log: dict = {}
    for kt, fn in LOADERS.items():
        res = fn()
        w, ktrows = res if isinstance(res, tuple) else (res, None)
        w = w.copy()
        w["period"] = w["period"].astype(int).astype(str)
        cols = [c for c in MAP if c in w]
        vint = REFERENCE_DATE if kt in ("VD", "SG") else None  # VD, SG back-cast on the current state; ZH rows carry src_vintage
        o = to_ref(w, {c: MAP[c] for c in cols}, SOURCE, kt, rules=RULES, vintage=vint, log=log,
                   na_notes=NA_NOTES)
        if kt in HRM1:
            old = o["period"].astype(int) < HRM1[kt]
            o.loc[old & o["note"].isna(), "note"] = (f"{kt}: HRM1 accounts (HRM2 from {HRM1[kt]}); "
                                                     "not comparable with later years")
        if kt in ("LU", "BL"):
            calc = o["metric_id"].isin([NET, SFG]) & o["status"].eq("ok")
            o.loc[calc, "note"] = "computed by Gemeindebank from the cantonal HRM2 accounts"
        parts.append(o)
        for c in cols:
            covered_periods[(MAP[c], kt)] = set(w.loc[w[c].notna() | w.get(f"{c}__na", False), "period"])
        if ktrows is not None:
            k = ktrows.copy()
            k["period"] = k["period"].astype(int).astype(str)
            natives.append(emit(k, {c: MAP[c] for c in cols if c in k}, "period", SOURCE, level="kanton",
                                unit_col="unit", provenance="native"))
    obs = pd.concat(parts, ignore_index=True)
    covered = {}
    for (m, kt) in covered_periods:
        covered.setdefault(m, set()).add(kt)
    obs = complete(obs, SOURCE, covered, NOT_COVERED, DEFAULT_NC, covered_periods=covered_periods)
    if natives:
        nat = pd.concat(natives, ignore_index=True)
        obs = pd.concat([obs, nat[nat["status"] == "ok"]], ignore_index=True)
    return obs
