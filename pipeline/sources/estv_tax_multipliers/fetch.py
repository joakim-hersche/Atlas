"""Fetch ESTV tax multipliers (Steuerfüsse) of all municipalities per tax year.

Undocumented export of the public ESTV tax calculator (swisstaxcalculator.estv.admin.ch), reverse-
engineered from the web app: POST /delegate/ost-integration/v1/export/income-tax-rates/DE with
{"taxGroup": 99 (= all of Switzerland), "simKey": null, "year": <year>} -> XLSX. Years 2010-2026
(2009 and earlier answer HTTP 502). Responses are cached like any other download.
"""
from __future__ import annotations

from pipeline.sources.estv_dbst.refhelp import fetch_post

SOURCE = "estv_tax_multipliers"
URL = "https://swisstaxcalculator.estv.admin.ch/delegate/ost-integration/v1/export/income-tax-rates/DE"
YEARS = range(2010, 2027)


def rates(year: int):
    return fetch_post(URL, SOURCE, f"estv_income_rates_{year}.xlsx",
                      {"taxGroup": 99, "simKey": None, "year": year})
