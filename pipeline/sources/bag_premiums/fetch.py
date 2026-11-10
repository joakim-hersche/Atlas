"""Fetch BAG health insurance premium overviews and premium-region lists.

priminfo.admin.ch (BAG):
  /downloads/gesamtbericht_ch-<year>.pdf  premium overview of the current premium year (all
                                          insurers, cantons, regions, models, franchises)
  /downloads/praemien_<year>.pdf          the same overview for earlier years (archive)
  /downloads/praemienregionen-<year>.xlsx municipality -> premium region list of the current year,
                                          incl. sheet D_PRIM (BAG mean monthly premium per region)
bag.admin.ch: machine-readable annex of the EDI ordinance on premium regions (SR 832.106.1),
  state 1 January 2026 (multi-region cantons only).
The machine-readable premium tables are on opendata.swiss, which is not reachable (403);
region lists of years before 2026 are not offered as files on the allowed hosts.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bag_premiums"
PRIMINFO = "https://www.priminfo.admin.ch/downloads"
CURRENT_YEAR = 2027
ANNEX_2026 = ("https://www.bag.admin.ch/dam/de/sd-web/IvHRHXKH3eYG/"
              "Anhang%20EDI%20Ver.%20%C3%BCber%20die%20PrReg_Mut_2026.xlsx")


def overview(year: int):
    f = f"gesamtbericht_ch-{year}.pdf" if year == CURRENT_YEAR else f"praemien_{year}.pdf"
    return fetch(f"{PRIMINFO}/{f}", SOURCE, f)


def regions(year: int = CURRENT_YEAR):
    f = f"praemienregionen-{year}.xlsx"
    return fetch(f"{PRIMINFO}/{f}", SOURCE, f)


def annex_2026():
    return fetch(ANNEX_2026, SOURCE, "Anhang_EDI_Ver_PrReg_Mut_2026.xlsx")


if __name__ == "__main__":
    print(overview(CURRENT_YEAR), regions(), annex_2026(), overview(2026))
