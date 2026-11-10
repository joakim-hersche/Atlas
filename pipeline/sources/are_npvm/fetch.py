"""Fetch ARE NPVM 2023 (national passenger transport model) files from Zenodo.

Record doi:10.5281/zenodo.23009199 (CC-BY-4.0, published 2026-09-28 by VM-UVEK).
Matrices are $O-format text inside zip files, for the average weekday (DWV).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "are_npvm"
RECORD = "https://zenodo.org/api/records/23009199/files"
FILES = {
    "doc_de": "00_NPVM_2023_Datenbezug.pdf",
    "doc_fr": "00_MNTP_2023_Description_données.pdf",
    "zones": "1_Verkehrszonen_Schweiz_NPVM_2023.zip",
    "zone_centroids": "1_Verkehrszonen_Schweiz_Zentroide_NPVM_2023.gpkg",
    "car_time": "4_TTC_PW_NPVM_2023.zip",          # Reisezeit PW (car travel time)
    "pt_time": "4_RITA_ACT_EGT_NPVM_2023.zip",     # Reisezeit OeV = RITA + ACT + EGT
    "pt_trips": "3_Wegematrix_OEV_NPVM_2023.zip",
}


def get(kind: str):
    name = FILES[kind]
    safe = name.encode("ascii", "ignore").decode() if kind == "doc_fr" else name
    from urllib.parse import quote
    return fetch(f"{RECORD}/{quote(name)}/content", SOURCE, safe, timeout=3600)


if __name__ == "__main__":
    import sys
    for k in (sys.argv[1:] or FILES):
        print(k, get(k))
