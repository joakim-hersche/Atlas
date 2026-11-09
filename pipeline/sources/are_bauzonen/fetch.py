"""Fetch ARE Bauzonenstatistik Schweiz (editions 2012, 2017, 2022), results per municipality.

Page: https://www.are.admin.ch/de/bauzonenstatistik-schweiz
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "are_bauzonen"
DAM = "https://www.are.admin.ch/dam/de/sd-web"
FILES = {
    2012: f"{DAM}/3lK47686QIeu/Bauzonenstatistik_Schweiz_2012.zip",
    2017: f"{DAM}/iLHkdaGp7qi3/Bauzonenstatistik_Schweiz_2017.zip",
    2022: f"{DAM}/7cEPibyb2l-3/bauzonenstatistik_schweiz_2022_gemeinden.xlsx",
}
RESULTS_2022 = f"{DAM}/uPugMgFnGj0m/bauzonenstatistik_schweiz_2022_resultate.xlsx"
REPORT_2022 = f"{DAM}/AS4q88PlZYXF/bzs_2022.pdf"


def edition(year: int):
    url = FILES[year]
    return fetch(url, SOURCE, url.rsplit("/", 1)[1])


def results_2022():
    return fetch(RESULTS_2022, SOURCE, RESULTS_2022.rsplit("/", 1)[1])


def report_2022():
    return fetch(REPORT_2022, SOURCE, REPORT_2022.rsplit("/", 1)[1])
