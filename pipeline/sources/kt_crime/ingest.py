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
Cantons with PDF reports only (LU, SO, FR, GR, SZ, GE, BE, VD, ...) are out of scope here.
Period = year the offence was registered (Ausgangsjahr).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.sources.kt_finance.kthelp import complete, fetch_retry, ods_csv, ref_units, to_ref

SOURCE = "kt_crime"
ZH_URL = "https://www.web.statistik.zh.ch/ogd/daten/ressourcen/KTZH_00001202_00003600.csv"
MAP = {"stgb": "crime_stgb_offences", "prop": "crime_stgb_property", "viol": "crime_stgb_violent"}
ZH_TITLES = {"Total gegen das Vermögen": "prop", "Total gegen Leib und Leben": "viol"}
BS_ROWS = {"Total StGB": "stgb", "Total Gegen das Vermögen": "prop", "Total Gegen Leib und Leben": "viol"}
PDF = "this canton publishes offences per municipality only in its PDF police statistics report (not parsed)"
NOT_COVERED = {k: PDF for k in ("LU", "SO", "FR", "GR", "SZ", "GE", "BE", "VD")}
NOT_COVERED.update({k: "the police statistics report of this canton is on a host not available to the pipeline"
                    for k in ("AR", "AI", "BL", "GL")})
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


def observations() -> pd.DataFrame:
    parts, cov = [], {}
    zw = zh()
    bw, bkt = bs()
    for kt, w in (("ZH", zw), ("BS", bw)):
        w["period"] = w["period"].astype(int).astype(str)
        parts.append(to_ref(w, MAP, SOURCE, kt, min_jaccard=0.0 if kt == "ZH" else 0.97))
        for m in MAP.values():
            cov[(m, kt)] = set(w["period"])
    obs = pd.concat(parts, ignore_index=True)
    # ZH: municipalities up to 10,000 inhabitants are not published
    zh_units = set(ref_units().query("canton == 'ZH'")["bfs_nr"].astype(str))
    have = set(zip(obs["unit_id"], obs["metric_id"], obs["period"]))
    rows = [(u, m, p) for m in MAP.values() for p in sorted(cov[(m, "ZH")]) for u in zh_units
            if (u, m, p) not in have]
    add = pd.DataFrame(rows, columns=["unit_id", "metric_id", "period"]).assign(
        level="gemeinde", vintage=obs["vintage"].iloc[0], value=float("nan"), status="not_published",
        precision="exact", provenance="native", source_id=SOURCE,
        note="ZH publishes offences only for municipalities with more than 10,000 inhabitants")
    obs = pd.concat([obs, add[obs.columns]], ignore_index=True)
    covered = {m: {"ZH", "BS"} for m in MAP.values()}
    obs = complete(obs, SOURCE, covered, NOT_COVERED, DEFAULT_NC, covered_periods=cov)
    bkt["period"] = bkt["period"].astype(int).astype(str)
    nat = emit(bkt[bkt["unit"] == "BS"], MAP, "period", SOURCE, level="kanton", unit_col="unit", provenance="native")
    # 'Gemeinde unbekannt' (offences without a known municipality): in the canton total only.
    # Checked 2009–2025: canton = Basel + Riehen + Bettingen + unbekannt exactly.
    ps = emit(bkt[bkt["unit"] != "BS"], MAP, "period", SOURCE, level="pseudo", unit_col="unit", provenance="native")
    ps["note"] = "BS police statistics 'Gemeinde unbekannt': offences without a known municipality"
    return pd.concat([obs, nat[nat["status"] == "ok"], ps[ps["status"] == "ok"]], ignore_index=True)
