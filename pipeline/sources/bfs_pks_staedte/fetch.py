"""Fetch BFS table je-d-19.02.01.01.04 'Strafgesetzbuch: Auswahl von Straftaten, nach Städten ab
30'000 Einwohner' (Häufigkeitszahlen 2009-latest), xlsx on the BFS DAM (OPEN-BY)."""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_pks_staedte"
DAM = "https://dam-api.bfs.admin.ch/hub/api/dam/assets/36455965"


def asset_meta():
    """Asset metadata incl. termsOfUse (licence evidence)."""
    return fetch(DAM, SOURCE, "dam_asset_36455965.json")


def table():
    return fetch(f"{DAM}/master", SOURCE, "je-d-19.02.01.01.04.xlsx")
