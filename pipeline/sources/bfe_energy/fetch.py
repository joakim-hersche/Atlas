"""Fetch BFE / EnergieSchweiz energy-transition data per municipality.

- Energie Reporter (geoimpact AG for EnergieSchweiz): monthly historized slices since 2021-03,
  one CSV per level in a zip (opendata.geoimpact.ch; the site root redirects, direct paths work).
- Solarenergiepotenziale der Schweizer Gemeinden (BFE, uvek-gis OGD 52): JSON, one record per
  municipality (roofs only / roofs + facades scenarios).
- Energiestädte (BFE via data.geo.admin.ch): label holders with label level and points.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfe_energy"


def energyreporter_historized():
    return fetch("https://opendata.geoimpact.ch/energiereporter/energyreporter_historized.zip", SOURCE,
                 "energyreporter_historized.zip")


def solar_potential():
    return fetch("https://www.uvek-gis.admin.ch/BFE/ogd/52/Solarenergiepotenziale_Gemeinden_Daecher_und_Fassaden.json",
                 SOURCE, "Solarenergiepotenziale_Gemeinden_Daecher_und_Fassaden.json")


def energiestaedte():
    return fetch("https://data.geo.admin.ch/ch.bfe.energiestaedte/energiestaedte/energiestaedte_2056.gpkg",
                 SOURCE, "energiestaedte_2056.gpkg")


if __name__ == "__main__":
    print(energyreporter_historized(), solar_potential(), energiestaedte())
