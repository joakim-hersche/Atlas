"""Fetch ARE Wohnungsinventar / Zweitwohnungsanteil releases (STAC ch.are.wohnungsinventar-zweitwohnungsanteil).

One zipped XLSX per release (2017, 2018, then March/October since 2019), each on the municipality
state of its release.
"""
from __future__ import annotations

import json

import requests

from pipeline.common import USER_AGENT, fetch

SOURCE = "are_zweitwohnungen"
STAC = "https://data.geo.admin.ch/api/stac/v1/collections/ch.are.wohnungsinventar-zweitwohnungsanteil/items"


def items() -> list[tuple[str, str, str]]:
    """(release 'YYYY' or 'YYYY-MM', data date, xlsx.zip url) for every STAC item (items list cached)."""
    p = fetch(STAC + "?limit=100", SOURCE, "stac_items.json")
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for f in d["features"]:
        rel = f["id"].rsplit("_", 1)[1]
        for name, a in f["assets"].items():
            if name.endswith(".xlsx.zip"):
                out.append((rel, f["properties"]["datetime"][:10], a["href"]))
    return sorted(out)


def release(href: str):
    return fetch(href, SOURCE, href.rsplit("/", 1)[1])
