"""Downloads used only by the reach drawing that have no connector of their own.

swissTLMRegio (swisstopo) road network, STAC collection ch.swisstopo.swisstlmregio.
"""
from __future__ import annotations

from pipeline.common import fetch

TLMREGIO_SOURCE = "swisstopo_tlmregio"
TLMREGIO_YEAR = 2026


def tlmregio(year: int = TLMREGIO_YEAR):
    f = f"swisstlmregio_{year}_2056.gpkg.zip"
    return fetch(f"https://data.geo.admin.ch/ch.swisstopo.swisstlmregio/swisstlmregio_{year}/{f}",
                 TLMREGIO_SOURCE, f, timeout=3600)
