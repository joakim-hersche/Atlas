"""Fetch the BFS historized municipality register and its REST API outputs.

Source: BFS – Applikation der Schweizer Gemeinden (https://www.agvchapp.bfs.admin.ch).
API documentation: /documents/rest_api_de.pdf.
"""
from __future__ import annotations

import datetime as dt

from pipeline.common import REFERENCE_DATE, ddmmyyyy, fetch

SOURCE = "bfs_agvch"
BASE = "https://www.agvchapp.bfs.admin.ch"
FIRST_DATE = dt.date(1848, 9, 12)


def fetch_all(reference_date: dt.date = REFERENCE_DATE) -> dict[str, object]:
    today = dt.date.today()
    end = max(today, reference_date)
    files = {
        # eCH-0071 v1.2.0 register (TXT, Latin-1): all municipality versions since 1848
        "register_zip": fetch(f"{BASE}/file/txt/dz-b-00.04-hgv-01.zip", SOURCE, "register_txt.zip"),
        # every mutation since 1848, including pure territory exchanges
        "mutations": fetch(f"{BASE}/api/communes/mutations", SOURCE, "mutations_1848_all.csv", params={
            "includeTerritoryExchange": "true",
            "startPeriod": ddmmyyyy(FIRST_DATE),
            "endPeriod": ddmmyyyy(end),
        }),
        # snapshot of cantons/districts/municipalities valid on the reference date
        "snapshot": fetch(f"{BASE}/api/communes/snapshot", SOURCE,
                          f"snapshot_{reference_date.isoformat()}.csv",
                          params={"date": ddmmyyyy(reference_date)}),
        # spatial levels / typologies valid on the reference date
        "levels": fetch(f"{BASE}/api/communes/levels", SOURCE,
                        f"levels_{reference_date.isoformat()}.csv",
                        params={"date": ddmmyyyy(reference_date), "labelLanguages": "de,fr,it,en"}),
        # official correspondence 1960 -> reference date (used to validate our crosswalk)
        "correspondences_1960": fetch(f"{BASE}/api/communes/correspondances", SOURCE,
                                      f"correspondences_1960-01-01_{reference_date.isoformat()}.csv",
                                      params={
                                          "includeUnmodified": "true",
                                          "includeTerritoryExchange": "true",
                                          "startPeriod": "01-01-1960",
                                          "endPeriod": ddmmyyyy(reference_date),
                                      }),
    }
    # historical typology editions (MS regions, Gemeindetypologie 2012, ...) via older dates
    files["levels_historic"] = [
        fetch(f"{BASE}/api/communes/levels", SOURCE, f"levels_{d}.csv",
              params={"date": ddmmyyyy(dt.date.fromisoformat(d)), "labelLanguages": "de"})
        for d in ("1990-01-01", "2010-01-01", "2016-01-01", "2022-01-01")
    ]
    return files


if __name__ == "__main__":
    for k, v in fetch_all().items():
        print(k, v)
