"""Fetch cantonal municipal tax multipliers (Steuerfuss) from cantonal open-data portals.

Cleared: canton Zürich, Statistisches Amt / Amt für Statistik und Daten, dataset 711 'Steuerfüsse der Zürcher Gemeinden für
natürliche und juristische Personen' (distribution licence NonCommercialAllowed-CommercialAllowed-ReferenceRequired).
Held back (licence statement not confirmed, see pipeline/licence_review.yaml): BL data.bl.ch 10580, ZG data.zg.ch resource 849.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "kt_tax_multipliers"
ZH = "https://www.web.statistik.zh.ch/ogd/data/steuerfuesse/kanton_zuerich_stf_{}.csv"


def zh(kind: str):
    """kind: 'timeseries' (2012-2026, one row per municipality and year) or 'aktuell' (current survey)."""
    return fetch(ZH.format(kind), SOURCE, f"zh_stf_{kind}.csv")


if __name__ == "__main__":
    print(zh("timeseries"), zh("aktuell"))
