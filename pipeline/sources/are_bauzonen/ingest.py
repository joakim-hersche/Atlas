"""ARE Bauzonenstatistik Schweiz – building-zone area per municipality (ha) by main use, unbuilt
reserves and public-transport quality class.

Editions and terms of use (sheet 'Inhalt' of each workbook):
- 2022 (state 1.1.2022): "Open Data: freie Nutzung, Quellenangabe ist Pflicht" -> all tables used.
- 2017 (state 1.1.2017): unbuilt-zone results "dürfen nicht für einzelne Gemeinden, sondern nur in
  aggregierter Form veröffentlicht werden" -> main uses and PT classes only, no unbuilt reserves.
- 2012: "Die Resultate nach Gemeinden sind nicht öffentlich verfügbar … Weitergabe an Dritte
  untersagt" -> not used (licence flag).
Blank cells in the workbooks are zero (sparse layout; the row totals confirm it).
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from pipeline.sources.are_bauzonen.fetch import SOURCE, edition
from pipeline.sources.estv_dbst.refhelp import per_period_to_reference

VINTAGE_LOG: dict = {}
HN = {f"HN_{i}": i for i in range(11, 20)}


def _book(year: int) -> pd.ExcelFile:
    p = edition(year)
    if str(p).endswith(".zip"):
        z = zipfile.ZipFile(p)
        return pd.ExcelFile(io.BytesIO(z.read(f"Bauzonenstatistik_Schweiz_{year}_Gemeinden.xlsx")))
    return pd.ExcelFile(p)


def _sheet(x: pd.ExcelFile, prefix: str) -> pd.DataFrame:
    name = [s for s in x.sheet_names if s.replace(" ", "_").startswith(prefix)][0]
    d = x.parse(name)
    key = "Gem_No" if "Gem_No" in d else "BFS_No"
    d = d[pd.to_numeric(d[key], errors="coerce").notna()].copy()
    d["bfs_nr"] = d[key].astype(int)
    return d.set_index("bfs_nr")


def _edition(year: int, with_unbuilt: bool) -> pd.DataFrame:
    x = _book(year)
    hn = _sheet(x, "Statistik_Hauptnutzung")
    cols = list(HN)
    hn[cols] = hn[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    tot = hn[cols].sum(axis=1)
    if "Total" in hn and (pd.to_numeric(hn["Total"], errors="coerce") - tot).abs().max() > 1e-6:
        raise ValueError(f"{year}: HN columns do not add up to Total")
    out = pd.DataFrame({
        "bz_total": tot, "bz_res": hn["HN_11"], "bz_work": hn["HN_12"], "bz_mixed": hn["HN_13"],
        "bz_centre": hn["HN_14"], "bz_public": hn["HN_15"],
        "bz_other": hn[["HN_16", "HN_17", "HN_18", "HN_19"]].sum(axis=1),
    })
    oev = _sheet(x, "Analyse_Erschliessung")
    oc = ["A", "B", "C", "D", "keine"]
    oev[oc] = oev[oc].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    for c in oc:
        out[f"bz_pt_{c.lower()}"] = oev[c]
    if with_unbuilt:
        for a in (1, 2):
            u = _sheet(x, f"Analyse_unüberbaut_Annahme_{a}")
            uc = [f"Unüb{a}_{i}" for i in range(11, 15)]
            u[uc] = u[uc].apply(pd.to_numeric, errors="coerce").fillna(0.0)
            out[f"bz_unbuilt_a{a}"] = u[uc].sum(axis=1)
    out["period"] = str(year)
    return out.reset_index()


METRICS = {
    "bz_total": "bz_area_total_ha", "bz_res": "bz_area_residential_ha", "bz_work": "bz_area_work_ha",
    "bz_mixed": "bz_area_mixed_ha", "bz_centre": "bz_area_centre_ha", "bz_public": "bz_area_public_ha",
    "bz_other": "bz_area_other_ha",
    "bz_pt_a": "bz_area_pt_a_ha", "bz_pt_b": "bz_area_pt_b_ha", "bz_pt_c": "bz_area_pt_c_ha",
    "bz_pt_d": "bz_area_pt_d_ha", "bz_pt_keine": "bz_area_pt_none_ha",
    "bz_unbuilt_a1": "bz_unbuilt_low_ha", "bz_unbuilt_a2": "bz_unbuilt_high_ha",
}


def observations() -> pd.DataFrame:
    w = pd.concat([_edition(2017, with_unbuilt=False), _edition(2022, with_unbuilt=True)], ignore_index=True)
    obs = per_period_to_reference(w, METRICS, SOURCE, log=VINTAGE_LOG)
    # 2017 unbuilt reserves: not publishable per municipality (terms of use) -> no rows
    obs = obs[~((obs["period"] == "2017") & obs["metric_id"].str.startswith("bz_unbuilt"))]
    return obs.reset_index(drop=True)
