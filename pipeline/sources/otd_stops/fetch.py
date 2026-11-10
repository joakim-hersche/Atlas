"""Fetch public transport stops and rail station ridership from opentransportdata.swiss.

service-point-v2 (atlas): actual-date-swiss-service-point.csv, all service points valid on the
download day (semicolon CSV; fsoNumber = BFS municipality number, meansOfTransport, stopPoint).
einundaus: t01x-freq-bhf-gare-staz-stn-2025.xlsx, boardings + alightings per rail station,
2018 and 2022–2025 (SBB Angebotsplanung; state March 2026).
Resource URLs from the dataset pages (the CKAN API is not served on this host).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "otd_stops"
SP = ("https://data.opentransportdata.swiss/dataset/39e5f264-257a-4f3f-bccc-5322c37058c5/resource/"
      "d85ec42a-636d-486e-8b2b-eb4db0fbcaed/download/actual-date-swiss-service-point.csv")
RIDERSHIP = ("https://data.opentransportdata.swiss/dataset/02569ba8-b029-4d75-ad59-a6ffd4b6b569/resource/"
             "2254e1d8-c367-4b4d-bdc3-77327d933320/download/t01x-freq-bhf-gare-staz-stn-2025.xlsx")


def service_points():
    return fetch(SP, SOURCE, "actual-date-swiss-service-point.csv")


def ridership():
    return fetch(RIDERSHIP, SOURCE, "t01x-freq-bhf-gare-staz-stn-2025.xlsx")


if __name__ == "__main__":
    print(service_points())
    print(ridership())
