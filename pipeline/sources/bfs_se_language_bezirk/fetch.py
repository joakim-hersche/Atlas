"""Structural Survey (SE): main languages by district, 3-year pooled (BFS table su-d-40.02.01.08.09-<year>).

One xlsx per edition on the BFS DAM (OPEN-BY). Editions are listed through the DAM search API.
"""
from __future__ import annotations

import json
import re

import pandas as pd

from pipeline.common import fetch

SOURCE = "bfs_se_language_bezirk"
DAM = "https://dam-api.bfs.admin.ch/hub/api/dam/assets"


def editions() -> pd.DataFrame:
    """One row per edition: dam_id, order_nr, period ('2022-2024')."""
    p = fetch(DAM, SOURCE, "dam_search.json",
              params={"language": "de", "limit": 100, "extendedSearch": "Hauptsprachen nach Bezirk%"})
    rows = []
    for a in json.loads(p.read_text(encoding="utf-8"))["data"]:
        order = (a.get("shop") or {}).get("orderNr") or ""
        if not order.startswith("su-d-40.02.01.08.09-"):
            continue
        m = re.search(r"(\d{4})-(\d{4}) kumuliert", a["description"]["titles"]["main"])
        rows.append({"dam_id": a["ids"]["damId"], "order_nr": order, "period": f"{m.group(1)}-{m.group(2)}"})
    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)


def edition_file(dam_id: int, period: str):
    return fetch(f"{DAM}/{dam_id}/master", SOURCE, f"hauptsprachen_bezirk_{period}.xlsx")
