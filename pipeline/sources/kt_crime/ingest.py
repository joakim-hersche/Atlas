"""Criminal Code (StGB) offences per municipality, compiled from cantonal police statistics
(`*` metric, decision D6). All cantonal PKS figures follow the BFS PKS counting rules.

- ZH  Kantonspolizei Zürich OGD KTZH_00001202_00003600: Straftaten nach Gemeinde, only
      municipalities with more than 10,000 inhabitants (34), 2009–2025. StGB total = sum of the five
      StGB main titles; Zürich and Winterthur = sum over their Stadtkreise (incl. offences without
      a known Kreis). Other ZH municipalities: `not_published`.
- BS  Statistisches Amt Basel-Stadt dataset 100508 (StGB offences by Gemeinde, 2009–2025): rows
      'Total StGB', 'Total Gegen das Vermögen', 'Total Gegen Leib und Leben' for Basel, Riehen,
      Bettingen. A missing title row in a year with a 'Total StGB' row is 0 (sparse table).
      'Gemeinde unbekannt' is only in the canton total (native kanton row); kept as level 'pseudo'
      (unit_id 'BS:unbekannt') so the canton total can be reconciled.
- ZH  burglaries: Kantonspolizei Zürich OGD KTZH_00001202_00006848 'Anzahl Einbrüche nach
      Gemeinden' (all municipalities, 2009–2025; 'Einbrüche insgesamt' = Einbruchdiebstahl +
      Einschleichdiebstahl). Zürich = sum over its Stadtkreise incl. 'unbekannt'. The ZH OGD
      files moved to daten.statistik.zh.ch (2026).
- AR, AI, BL  cantonal PKS annual report 2025 (BFS template, PDF), table 'Strafgesetzbuch:
      Straftaten nach Gemeinde' (2019–2025, StGB total only; see pks_pdf.py). The table lists at
      most 40 municipalities (BL: the 40 with most offences in 2025; the other 46 are lumped as
      'Übrige Gemeinden' -> `not_published`, kept as a pseudo unit). 'Unbekannt <KT>' (no known
      municipality) is a pseudo unit. Municipality rows + pseudo rows = 'Total Kanton' exactly
      (checked 2019–2025). The template back-casts earlier years on the 2025 state.
Other cantons with PDF reports only (LU, SO, FR, GR, SZ, GE, BE, VD, ...) are not parsed here.
Period = year the offence was registered (Ausgangsjahr).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit
import re

from pipeline.common import REFERENCE_DATE
from pipeline.sources.kt_crime.pks_pdf import stgb_by_gemeinde
from pipeline.sources.kt_finance.kthelp import complete, fetch_retry, match_names, ods_csv, ref_units, to_ref

SOURCE = "kt_crime"
ZH_URL = "https://daten.statistik.zh.ch/ogd/daten/ressourcen/KTZH_00001202_00003600.csv"
ZH_BURGLARY_URL = "https://daten.statistik.zh.ch/ogd/daten/ressourcen/KTZH_00001202_00006848.csv"
PKS_PDF = {
    "AR": "https://ar.ch/fileadmin/user_upload/Departement_Inneres_Sicherheit/Kapo/Kriminalpolizei/Statistiken/Kriminalstatistik_2025.pdf",
    "BL": ("https://bl-api.webcloud7.ch/politik-und-behorden/direktionen/sicherheitsdirektion/polizei/"
           "statistik/downloads-statistiken/kriminalstatistik-2025.pdf"),
}
AI_LIST = "https://www.ai.ch/themen/sicherheit/kantonspolizei/statistik/kriminalstatistiken"
PKS_YEAR = 2025
MAP = {"stgb": "crime_stgb_offences", "prop": "crime_stgb_property", "viol": "crime_stgb_violent"}
BURG = "crime_burglaries"
ZH_TITLES = {"Total gegen das Vermögen": "prop", "Total gegen Leib und Leben": "viol"}
BS_ROWS = {"Total StGB": "stgb", "Total Gegen das Vermögen": "prop", "Total Gegen Leib und Leben": "viol"}
PDF = "this canton publishes offences per municipality only in its PDF police statistics report (not parsed)"
NOT_COVERED = {k: PDF for k in ("LU", "SO", "FR", "GR", "SZ", "GE", "BE", "VD")}
NOT_COVERED["GL"] = "the police statistics report of Glarus is on a host not available to the pipeline"
DEFAULT_NC = "this canton publishes no offences per municipality"


def zh() -> pd.DataFrame:
    z = pd.read_csv(fetch_retry(ZH_URL, SOURCE, "KTZH_00001202_00003600.csv"))
    z = z[z["Gesetz_Abk"] == "StGB"]
    key = ["Gemeinde_BFS_Nr", "Ausgangsjahr"]
    w = z.groupby(key)["Straftaten_total"].sum().rename("stgb").to_frame()
    for title, col in ZH_TITLES.items():
        w[col] = z[z["Haupttitel"] == title].groupby(key)["Straftaten_total"].sum()
    w = w.fillna({"prop": 0, "viol": 0}).reset_index()
    return w.rename(columns={"Gemeinde_BFS_Nr": "bfs_nr", "Ausgangsjahr": "period"})


def bs() -> tuple[pd.DataFrame, pd.DataFrame]:
    b = ods_csv("data.bs.ch", "100508", SOURCE)
    b = b[b["straftaten"].isin(BS_ROWS)].assign(col=lambda x: x["straftaten"].map(BS_ROWS))
    w = b.pivot_table(index=["gemeinde", "jahr"], columns="col", values="anzahl_total", aggfunc="sum").reset_index()
    has_total = w["stgb"].notna()
    for c in ("prop", "viol"):
        w.loc[has_total & w[c].isna(), c] = 0.0
    kt = w[w["gemeinde"] == "Kanton Basel-Stadt"].assign(unit="BS").rename(columns={"jahr": "period"})
    unk = w[w["gemeinde"] == "Gemeinde unbekannt"].assign(unit="BS:unbekannt").rename(columns={"jahr": "period"})
    ids = ref_units().query("canton == 'BS'").set_index("name")["bfs_nr"].to_dict()
    w = w[w["gemeinde"].isin(ids)].assign(bfs_nr=lambda x: x["gemeinde"].map(ids))
    kt = pd.concat([kt, unk], ignore_index=True)
    return w.rename(columns={"jahr": "period"}).drop(columns="gemeinde"), kt.drop(columns="gemeinde")


def zh_burglaries() -> pd.DataFrame:
    z = pd.read_csv(fetch_retry(ZH_BURGLARY_URL, SOURCE, "KTZH_00001202_00006848.csv"))
    z = z[z["Tatbestand"] == "Einbrüche insgesamt"]
    w = z.groupby(["Gemeinde_BFS_Nr", "Ausgangsjahr"])["Straftaten_total"].sum().rename("n").reset_index()
    return w.rename(columns={"Gemeinde_BFS_Nr": "bfs_nr", "Ausgangsjahr": "period"})


def _pks_pdf(kt: str):
    if kt != "AI":
        return fetch_retry(PKS_PDF[kt], SOURCE, f"pks_{kt.lower()}_{PKS_YEAR}.pdf")
    # Appenzell Innerrhoden serves its files through a download proxy with a changing token
    html = fetch_retry(AI_LIST, SOURCE, "ai_kriminalstatistiken.html").read_text(encoding="utf-8")
    m = re.search(rf'href="(/api/download\?url=[^"]*kriminalstatistik-{PKS_YEAR}-kapo-ai\.pdf[^"]*)"', html)
    if not m:
        raise ValueError(f"AI: no link to the {PKS_YEAR} police statistics report on {AI_LIST}")
    return fetch_retry("https://www.ai.ch" + m.group(1).replace("&amp;", "&"), SOURCE, f"pks_ai_{PKS_YEAR}.pdf")


def pks(kt: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Municipality rows (bfs_nr, period, stgb) and canton/pseudo rows (unit, period, stgb)."""
    d = stgb_by_gemeinde(_pks_pdf(kt))
    d["period"] = d["period"].astype(int)
    special = d["label"].eq("Total Kanton") | d["label"].str.startswith(("Unbekannt", "Übrige Gemeinden"))
    g = d[~special]
    m = match_names(g["label"].unique(), kt)
    miss = set(g["label"]) - set(m)
    if miss:
        raise ValueError(f"{kt} PKS municipality names not matched: {sorted(miss)}")
    w = g.assign(bfs_nr=g["label"].map(m)).rename(columns={"n": "stgb"})[["bfs_nr", "period", "stgb"]]
    k = d[special].copy()
    k["unit"] = k["label"].map(lambda x: kt if x == "Total Kanton" else
                               f"{kt}:unbekannt" if x.startswith("Unbekannt") else f"{kt}:uebrige")
    tot = k[k["unit"] == kt].set_index("period")["n"]
    rest = pd.concat([w.groupby("period")["stgb"].sum(), k[k["unit"] != kt].groupby("period")["n"].sum()],
                     axis=1).fillna(0).sum(axis=1)
    if not (tot - rest.reindex(tot.index)).abs().max() < 0.5:
        raise ValueError(f"{kt} PKS: municipalities + pseudo rows do not add up to the canton total")
    return w, k.rename(columns={"n": "stgb"})[["unit", "period", "stgb"]]


PSEUDO_NOTE = {"unbekannt": "police statistics 'Unbekannt': offences without a known municipality (in the canton total only)",
               "uebrige": "police statistics 'Übrige Gemeinden': municipalities not listed individually (in the canton total only)"}


def observations() -> pd.DataFrame:
    parts, cov = [], {}
    zw = zh()
    bw, bkt = bs()
    for kt, w in (("ZH", zw), ("BS", bw)):
        w["period"] = w["period"].astype(int).astype(str)
        parts.append(to_ref(w, MAP, SOURCE, kt, min_jaccard=0.0 if kt == "ZH" else 0.97))
        for m in MAP.values():
            cov[(m, kt)] = set(w["period"])
    zb = zh_burglaries()
    zb["period"] = zb["period"].astype(int).astype(str)
    parts.append(to_ref(zb, {"n": BURG}, SOURCE, "ZH"))
    cov[(BURG, "ZH")] = set(zb["period"])
    pks_kt, pks_listed = [], {}
    for kt in ("AR", "AI", "BL"):
        w, k = pks(kt)
        w["period"] = w["period"].astype(str)
        k["period"] = k["period"].astype(str)
        parts.append(to_ref(w, {"stgb": MAP["stgb"]}, SOURCE, kt, vintage=REFERENCE_DATE))
        cov[(MAP["stgb"], kt)] = set(w["period"])
        pks_kt.append(k)
        pks_listed[kt] = set(w["bfs_nr"].astype(str))
    obs = pd.concat(parts, ignore_index=True)
    have = set(zip(obs["unit_id"], obs["metric_id"], obs["period"]))
    # ZH: municipalities up to 10,000 inhabitants are not published
    zh_units = set(ref_units().query("canton == 'ZH'")["bfs_nr"].astype(str))
    rows = [(u, m, p) for m in MAP.values() for p in sorted(cov[(m, "ZH")]) for u in zh_units
            if (u, m, p) not in have]
    add = pd.DataFrame(rows, columns=["unit_id", "metric_id", "period"]).assign(
        note="ZH publishes offences only for municipalities with more than 10,000 inhabitants")
    # PKS reports: at most 40 municipalities listed (BL), the others are 'Übrige Gemeinden'
    rows = []
    for kt in pks_listed:
        units = set(ref_units().query("canton == @kt")["bfs_nr"].astype(str))
        rows += [(u, MAP["stgb"], p) for p in sorted(cov[(MAP["stgb"], kt)]) for u in units - pks_listed[kt]
                 if (u, MAP["stgb"], p) not in have]
    add2 = pd.DataFrame(rows, columns=["unit_id", "metric_id", "period"]).assign(
        note="the cantonal police statistics report lists only the 40 municipalities with most offences; "
             "this municipality is in 'Übrige Gemeinden'")
    add = pd.concat([add, add2], ignore_index=True).assign(
        level="gemeinde", vintage=REFERENCE_DATE.isoformat(), value=float("nan"), status="not_published",
        precision="exact", provenance="native", source_id=SOURCE)
    obs = pd.concat([obs, add[obs.columns]], ignore_index=True)
    covered = {m: {"ZH", "BS"} for m in MAP.values()}
    covered[MAP["stgb"]] |= {"AR", "AI", "BL"}
    covered[BURG] = {"ZH"}
    obs = complete(obs, SOURCE, covered, NOT_COVERED, DEFAULT_NC, covered_periods=cov)
    bkt["period"] = bkt["period"].astype(int).astype(str)
    nat = emit(bkt[bkt["unit"] == "BS"], MAP, "period", SOURCE, level="kanton", unit_col="unit", provenance="native")
    # 'Gemeinde unbekannt' (offences without a known municipality): in the canton total only.
    # Checked 2009–2025: canton = Basel + Riehen + Bettingen + unbekannt exactly.
    ps = emit(bkt[bkt["unit"] != "BS"], MAP, "period", SOURCE, level="pseudo", unit_col="unit", provenance="native")
    ps["note"] = "BS police statistics 'Gemeinde unbekannt': offences without a known municipality"
    pk = pd.concat(pks_kt, ignore_index=True)
    pnat = emit(pk[~pk["unit"].str.contains(":")], {"stgb": MAP["stgb"]}, "period", SOURCE, level="kanton",
                unit_col="unit", provenance="native")
    pps = emit(pk[pk["unit"].str.contains(":")], {"stgb": MAP["stgb"]}, "period", SOURCE, level="pseudo",
               unit_col="unit", provenance="native")
    pps["note"] = pps["unit_id"].str.split(":").str[1].map(PSEUDO_NOTE)
    out = [obs] + [x[x["status"] == "ok"] for x in (nat, ps, pnat, pps)]
    return pd.concat(out, ignore_index=True)
