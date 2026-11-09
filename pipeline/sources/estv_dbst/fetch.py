"""Fetch ESTV 'Statistik direkte Bundessteuer, natürliche Personen, Gemeinden' (one workbook per
tax year). Links are taken from the ESTV statistics page (cached) because the DAM paths carry
random ids.

Per year the file with all taxpayers (with and without federal tax), normal cases:
  2023+      statistik-dbst-np-gemeinden-<y>-500.xlsx
  2020-2022  statistik-dbst-np-gden-<y>-normalfall[-de].xlsx
  2001-2019  statistik-dbst-np-gemeinde-<y>-auswertung-de.xls(x)
Earlier years (1999/2000 two-year periods, PDFs before) are not ingested.
"""
from __future__ import annotations

import re

from pipeline.common import fetch

SOURCE = "estv_dbst"
PAGE = "https://www.estv.admin.ch/de/statistiken-natuerliche-personen-gemeinden-1983-bis-heute"


def links() -> dict[str, str]:
    html = fetch(PAGE, SOURCE, "page_np_gemeinden.html").read_text(encoding="utf-8", errors="replace")
    urls = sorted(set(re.findall(r'href="(https://www\.estv\.admin\.ch/dam/[^"]+\.(?:xlsx|xls))"', html)))
    return {u.rsplit("/", 1)[1]: u for u in urls}


def year_file(year: int):
    ls = links()
    pats = [rf"statistik-dbst-np-gemeinden-{year}-500\.xlsx",
            rf"statistik-dbst-np-gden-{year}-normalfall(-de)?\.xlsx",
            rf"statistik-dbst-np-gemeinde-{year}-auswertung-de\.xlsx?"]
    for p in pats:
        hit = [n for n in ls if re.fullmatch(p, n)]
        if hit:
            return fetch(ls[hit[0]], SOURCE, hit[0])
    raise FileNotFoundError(f"no ESTV municipality file for {year}")
