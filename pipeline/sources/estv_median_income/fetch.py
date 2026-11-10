"""Fetch for estv_median_income: the ESTV workbooks are the same files as estv_dbst (shared cache).

Per tax year 2020-2023 the income-class counts of the normal cases:
  2023       statistik-dbst-np-gemeinden-2023-500.xlsx  (sheet 521)
  2021-2022  statistik-dbst-np-gden-<y>-normalfall[-de].xlsx
  2020       the '-normalfall' file repeats the special cases (publisher error, see estv_dbst) -> built from
             '-mit-belastung-normalfall' + '-ohne-belastung-normalfall'
Files are downloaded by pipeline.sources.estv_dbst.fetch (cached in data/raw/estv_dbst/<date>/).
"""
from __future__ import annotations

from pipeline.sources.estv_dbst.fetch import links  # noqa: F401  (re-exported)
from pipeline.sources.estv_dbst.ingest import _new_file  # the same file lookup

SOURCE = "estv_median_income"
YEARS = (2020, 2021, 2022, 2023)


def class_workbooks(year: int) -> list:
    """Workbooks whose sheet '521' (all normal cases) or '121' + '321' (2020) hold the class counts."""
    if year == 2020:
        return [_new_file(year, "with_normal"), _new_file(year, "none_normal")]
    return [_new_file(year, "all_normal")]
