"""Fetch the public GWR extract (Federal Register of Buildings and Dwellings, authorisation level A).

https://public.madd.bfs.admin.ch/ch.zip  (about 950 MB; one CSV per entity inside: gebaeude_batiment_edificio.csv,
eingang_entree_entrata.csv, wohnung_logement_abitazione.csv, ...). Licence: "Freie Nutzung. Quellenangabe ist Pflicht"
(license.txt of the GWR publication, https://data.geo.admin.ch/ch.bfs.gebaeude_wohnungs_register/license.txt).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_gwr"
URL = "https://public.madd.bfs.admin.ch/ch.zip"
LICENSE_URL = "https://data.geo.admin.ch/ch.bfs.gebaeude_wohnungs_register/license.txt"


def gwr_zip():
    return fetch(URL, SOURCE, "gwr_ch.zip")


def licence_txt():
    return fetch(LICENSE_URL, SOURCE, "gwr_license.txt")


if __name__ == "__main__":
    print(licence_txt())
    print(gwr_zip())
