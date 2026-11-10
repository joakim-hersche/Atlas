"""Downloads for kt_finance (municipal finance key ratios, cantonal publishers). All cached in
data/raw/kt_finance/<date>/ via pipeline.common.fetch (or the session/ODS helpers in kthelp)."""
from __future__ import annotations

import pandas as pd

from pipeline.sources.kt_finance.kthelp import fetch_retry, fetch_session, ods_csv, zh_current

SOURCE = "kt_finance"

URLS = {
    "lu": "https://www.data.lustat.ch/gefis-lu-jr.csv",
    "ge": "https://statistique.ge.ch/tel/domaines/18/18_02/T_18_02_2_04.xlsx",
    "vd": ("https://www.vd.ch/fileadmin/user_upload/themes/territoire/communes/finances_communales/"
           "fichiers_xls/Indicateurs_par_commune_2017-2025--2026.xlsx"),
    "ag": ("https://www.ag.ch/media/kanton-aargau/dfr/dokumente/statistik/statistische-daten/"
           "oeffentliche-statistik/18-oeffentliche-verwaltung-und-finanzen/gemeindefinanzen/"
           "gemeindefinanzen-2025-edossier.xlsx"),
}
SO_RATIOS = {"KZ07": "net debt I per resident", "KZ02": "self-financing ratio"}


def zh(ind: int):
    return zh_current(ind, SOURCE)


def lu():
    return fetch_retry(URLS["lu"], SOURCE, "gefis-lu-jr.csv")


def bl():
    return ods_csv("data.bl.ch", "10640", SOURCE)


def fr():
    return ods_csv("opendata.fr.ch", "18_02_indicateurs", SOURCE)


def gr():
    return ods_csv("data.gr.ch", "dfg_afg_econ_20260326", SOURCE)


def tg():
    return ods_csv("data.tg.ch", "sk-stat-4", SOURCE)


def so(ratio: str):
    return fetch_session(["https://gefin.so.ch/home", f"https://gefin.so.ch/ratio.do?mi={ratio}"],
                         f"https://gefin.so.ch/ratiocsv.do?mi={ratio}", SOURCE, f"so_gefin_{ratio}.csv")


def ge():
    return fetch_retry(URLS["ge"], SOURCE, "T_18_02_2_04.xlsx")


def vd():
    return fetch_retry(URLS["vd"], SOURCE, "vd_indicateurs_2017-2025.xlsx")


def ag():
    return fetch_retry(URLS["ag"], SOURCE, "ag_edossier_2025.xlsx")


BL_CSV = "https://fkd-sta-files.bl.ch/ogd/gemeindefinanzen/gemeindefinanzen_2014-2025.csv"


def bl_file():
    """Full HRM2 accounts 2014–2025 (the file linked from data.bl.ch dataset 10640)."""
    return fetch_retry(BL_CSV, SOURCE, "bl_gemeindefinanzen_2014-2025.csv")


# --- ZG: data.zg.ch (EntryScape), dataset 'Gemeindefinanzen' (store/1/resource/840) ---------------
ZG_RESOURCES = {"net": 841, "sfg": 2151}  # Nettoschuld pro Einwohner; Selbstfinanzierungsgrad (CSV)


def zg(res: int):
    return fetch_retry(f"https://data.zg.ch/store/1/resource/{res}", SOURCE, f"zg_resource_{res}.csv")


# --- SG: STADA2 statistics database (Fachstelle für Statistik SG), CSV export (zip) --------------
STADA2 = "https://stada2.sg.ch/webapp/gpsg/GPSG"
STADA2_GEMEINDEN = "https://stada2.sg.ch/pages/export/auswahlGemeinden.php"
SG_INDICATORS = {2008: "net", 2000: "sfg", 2043: "tax"}  # Nettoschuld I RMSG, SFG RMSG, 40 Fiskalertrag


def stada2_gemeinden(source_id: str = SOURCE) -> list[int]:
    """Area ids of the 'Pol.Gemeinden SG' selection list (equal to the BFS numbers)."""
    import json
    import re
    t = fetch_retry(STADA2_GEMEINDEN, source_id, "stada2_auswahlGemeinden.html").read_text(encoding="utf-8")
    j = json.loads(re.search(r"loadGebietTreetable\(\"[^\"]+\", (\{.*?\})\)", t, re.S).group(1))
    return sorted(int(r["RAUMEINHEIT_ID"]) for r in j["RAUMEINHEITEN"])


def stada2_export(indicators, years, source_id: str, filename: str, *, canton: bool = True) -> pd.DataFrame:
    """One STADA2 CSV export (zip with data + metainfo) for all SG political municipalities
    (+ canton, area id 17). Returns the data table as delivered (values as strings)."""
    import io
    import zipfile
    raum = ([17] if canton else []) + stada2_gemeinden(source_id)
    params = {"type": "EXPORT", "raum": ",".join(map(str, raum)),
              "indikatoren": ",".join(map(str, indicators)), "jahr": ",".join(map(str, years)),
              "export": "CSV"}
    p = fetch_retry(STADA2, source_id, filename, params=params)
    with zipfile.ZipFile(p) as z:
        name = next(n for n in z.namelist() if n.startswith("stada2_data"))
        raw = z.read(name).decode("utf-8")
    return pd.read_csv(io.StringIO(raw), sep=";", index_col=False, dtype=str)


def sg() -> pd.DataFrame:
    return stada2_export(SG_INDICATORS, range(2017, 2027), SOURCE, "sg_stada2_finance.zip")


# --- TI: Sezione degli enti locali, Statistica finanziaria dei comuni, allegato statistico ------
TI_PAGE = "https://www4.ti.ch/di/sel/comuni/dati-finanziari/statistica-finanziaria"
TI_BASE = "https://www4.ti.ch"


def ti() -> dict[int, "Path"]:
    """Per accounting year: the 'allegato statistico: dati per comune' workbook (2000–)."""
    import re
    html = fetch_retry(TI_PAGE, SOURCE, "ti_statistica_finanziaria.html").read_text(encoding="utf-8")
    out = {}
    for href in sorted(set(re.findall(r'href="([^"]*StatisticaFinanziaria/(20\d\d)-_?allegato[^"]*\.xlsx?)"', html))):
        url, year = href
        out[int(year)] = fetch_retry(TI_BASE + url, SOURCE, "ti_" + url.rsplit("/", 1)[1])
    return out
