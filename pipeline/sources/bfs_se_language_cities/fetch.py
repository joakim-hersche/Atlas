"""Structural Survey (SE): main languages by statistical city, 5-year pooled (BFS table su-d-40.02.01.08.31-<year>).

One xlsx per edition on the BFS DAM (OPEN-BY), listed through the DAM search API (same route as
bfs_se_language_bezirk). Editions 2010-2014 ... latest.
"""
from __future__ import annotations

import json
import re

import pandas as pd

from pipeline.common import fetch

SOURCE = "bfs_se_language_cities"
DAM = "https://dam-api.bfs.admin.ch/hub/api/dam/assets"
ORDER = "su-d-40.02.01.08.31-"


def editions() -> pd.DataFrame:
    """One row per edition: dam_id, order_nr, period ('2020-2024')."""
    p = fetch(DAM, SOURCE, "dam_search.json",
              params={"language": "de", "limit": 100, "extendedSearch": "Hauptsprachen nach Städten%"})
    rows = []
    for a in json.loads(p.read_text(encoding="utf-8"))["data"]:
        order = (a.get("shop") or {}).get("orderNr") or ""
        if not order.startswith(ORDER):
            continue
        m = re.search(r"(\d{4})-(\d{4}) kumuliert", a["description"]["titles"]["main"])
        rows.append({"dam_id": a["ids"]["damId"], "order_nr": order, "period": f"{m.group(1)}-{m.group(2)}"})
    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)


def edition_file(dam_id: int, period: str):
    return fetch(f"{DAM}/{dam_id}/master", SOURCE, f"hauptsprachen_staedte_{period}.xlsx")


if __name__ == "__main__":
    e = editions()
    print(e)
    for r in e.itertuples():
        print(edition_file(r.dam_id, r.period))
