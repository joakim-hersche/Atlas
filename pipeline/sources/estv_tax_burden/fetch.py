"""Fetch ESTV tax burden (Steuerbelastung) of all municipalities for standard household cases.

Undocumented export of the public ESTV tax calculator (swisstaxcalculator.estv.admin.ch), request
body reverse-engineered from the web app's JavaScript:
POST /delegate/ost-integration/v1/export/income-tax-values/XLSX/DE
  {massExportModelId: <household model>, belastungsVergleich: 2 (LOCAL_COMPARISON), taxGroup: 99
   (all municipalities), confession: 1 (reformed), incomes: [<gross income>], fortunes: [0],
   klasse: 1 (INCOME), simKey: null, years: [<year>], output: 2 (TOTAL_TAX_IN_PERCENTAGE),
   considerMaximumExposureLimit: false}
One request per case and year (multi-year requests return HTTP 500 for some models; multi-income
requests interleave rows, so they are avoided).
"""
from __future__ import annotations

from pipeline.sources.estv_dbst.refhelp import fetch_post

SOURCE = "estv_tax_burden"
URL = "https://swisstaxcalculator.estv.admin.ch/delegate/ost-integration/v1/export/income-tax-values/XLSX/DE"
YEARS = range(2010, 2027)
# case id -> (massExportModelId, gross income CHF, label in the export's header)
CASES = {
    "single_80k": (1, 80_000, "Ledig, ohne Kinder"),
    "single_150k": (1, 150_000, "Ledig, ohne Kinder"),
    "married2c_100k": (7, 100_000, "Verheiratet, ein Einkommen, mit 2 Kindern"),
    "married2c_200k": (7, 200_000, "Verheiratet, ein Einkommen, mit 2 Kindern"),
    "pensioners_60k": (18, 60_000, "Verheiratet, eine Rente"),
}


def burden(case: str, year: int):
    model, income, _ = CASES[case]
    body = {"massExportModelId": model, "belastungsVergleich": 2, "taxGroup": 99, "confession": 1,
            "incomes": [income], "fortunes": [0], "klasse": 1, "simKey": None, "years": [year],
            "output": 2, "considerMaximumExposureLimit": False}
    return fetch_post(URL, SOURCE, f"burden_{case}_{year}.xlsx", body)
