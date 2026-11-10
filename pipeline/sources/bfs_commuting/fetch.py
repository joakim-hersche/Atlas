"""Fetch the BFS commuter matrix 'Erwerbstätige nach Wohn- und Arbeitsgemeinde, 2014, 2018 und 2020'
(Gemeindestand 2020) from the BFS DAM API.

asset 27885394 (ts-x-11.04.04.05): CSV, columns PERSPECTIVE, REF_YEAR, GEO_CANT_RESID,
GEO_COMM_RESID, GEO_CANT_WORK, GEO_COMM_WORK, VALUE; appendix = variable description (ODS).
asset 27885387 (je-d-11.04.04.05): the same data as XLSX, with notes.
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "bfs_commuting"
DAM = "https://dam-api.bfs.admin.ch/hub/api/dam/assets"


def matrix_csv():
    return fetch(f"{DAM}/27885394/master", SOURCE, "ts-x-11.04.04.05.csv")


def appendix_ods():
    return fetch(f"{DAM}/27885394/appendix", SOURCE, "ts-x-11.04.04.05_appendix.ods")


def matrix_xlsx():
    return fetch(f"{DAM}/27885387/master", SOURCE, "je-d-11.04.04.05.xlsx")


if __name__ == "__main__":
    print(matrix_csv())
    print(appendix_ods())
    print(matrix_xlsx())
