"""Downloads for kt_finance (municipal finance key ratios, cantonal publishers). All cached in
data/raw/kt_finance/<date>/ via pipeline.common.fetch (or the session/ODS helpers in kthelp)."""
from __future__ import annotations

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
