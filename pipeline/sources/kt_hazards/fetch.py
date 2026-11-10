"""Downloads for kt_hazards: geodienste.ch Gefahrenkarten (MGDM 166.1 v1.3) as GeoPackage per
canton, plus the geodienste service list (publication status, terms, update date per canton)."""
from __future__ import annotations

import json

from pipeline.sources.kt_finance.kthelp import fetch_retry

SOURCE = "kt_hazards"
# 'Frei erhältlich' on geodienste.ch (services.json). NW, OW, UR, VD need approval
# ('Freigabe erforderlich', HTTP 401); BS is 'Im Aufbau' (not published).
CANTONS = ["AG", "AI", "AR", "BE", "BL", "FR", "GE", "GL", "GR", "JU", "LU", "NE", "SG", "SH", "SO",
           "SZ", "TG", "TI", "VS", "ZG", "ZH"]
URL = "https://geodienste.ch/downloads/geopackage/gefahrenkarten/{kt}/deu/gefahrenkarten_v1_3_{kt}_gpkg_lv95.zip"
SERVICES = "https://geodienste.ch/info/services.json"


def gpkg_zip(kt: str):
    return fetch_retry(URL.format(kt=kt), SOURCE, f"gefahrenkarten_v1_3_{kt}_gpkg_lv95.zip", timeout=1800)


def services() -> list[dict]:
    p = fetch_retry(SERVICES, SOURCE, "services_gefahrenkarten.json",
                    params={"base_topics": "gefahrenkarten", "language": "de"})
    return json.loads(p.read_text(encoding="utf-8"))["services"]


if __name__ == "__main__":
    for k in CANTONS:
        print(k, gpkg_zip(k))
