"""Fetch for estv_median_income: the ESTV workbooks of the direct federal tax statistics (shared cache with estv_dbst).

Per tax year 2020-2023 the income-class counts of the normal cases (sheet 'x21' = taxpayers by class of taxable
income, municipalities and canton totals):
  2023       statistik-dbst-np-gemeinden-2023-500.xlsx  (sheet 521)
  2021-2022  statistik-dbst-np-gden-<y>-normalfall[-de].xlsx
  2020       the '-normalfall' file repeats the special cases (publisher error, see estv_dbst) -> built from
             '-mit-belastung-normalfall' (sheet 121) + '-ohne-belastung-normalfall' (sheet 321)
The links come from the ESTV statistics page (pipeline.sources.estv_dbst.fetch.links, cached); files are cached in
data/raw/estv_dbst/<date>/ and shared with estv_dbst.
"""
from __future__ import annotations

import re

from pipeline.common import fetch
from pipeline.sources.estv_dbst.fetch import SOURCE as DBST_SOURCE
from pipeline.sources.estv_dbst.fetch import links

SOURCE = "estv_median_income"
YEARS = (2020, 2021, 2022, 2023)


def _file(year: int, kind: str):
    ls = links()
    if year >= 2023:
        name = f"statistik-dbst-np-gemeinden-{year}-500.xlsx"
    else:
        name = next((k for k in ls if re.fullmatch(rf"statistik-dbst-np-gden-{year}-{kind}(-de)?\.xlsx", k)), None)
        if name is None:
            raise FileNotFoundError(f"ESTV {year} {kind}")
    return fetch(ls[name], DBST_SOURCE, name)


def class_workbooks(year: int) -> list[tuple]:
    """[(path, sheet-number-suffix)] holding the class counts of all normal cases of the year."""
    if year == 2020:
        return [(_file(year, "mit-belastung-normalfall"), "121"), (_file(year, "ohne-belastung-normalfall"), "321")]
    return [(_file(year, "normalfall"), "521")]
