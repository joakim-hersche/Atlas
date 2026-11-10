"""Pupils in compulsory school by residence municipality, compiled from cantonal statistics
(`*` metric, decision D6). Count per school year; per 1000 residents as a derived ratio.

- ZH  Bildungsstatistik via Gemeindeporträt: 143 Kindergarten + 149 Primarschule + 147 Oberstufe
      [Anz.], counted at the pupil's political municipality of residence (small municipalities
      without an upper-secondary school have Oberstufe pupils), ZH back-casts some merged municipalities
      (see kthelp.zh_current). Volksschule; whether private schools are included is UNVERIFIED.
      Kindergarten 1990–2023, Oberstufe from 2001: the total starts in 2001.
- BL  dataset 10420 (BFS Statistik der Lernenden, residence BL): Obligatorische Schule = public
      kindergarten, primary, lower secondary, special-needs schooling and private schools, 2014–2024.
- FR  15_02_eleves_lieu_domicile (OFS SDL): Scolarité obligatoire = primary 1-2, 3-8, lower
      secondary and special-needs schooling (enseignement séparatif), 2010–2024.
Period = first calendar year of the school year (2024 = school year 2024/25).
TG and SG count pupils by school district (Schulgemeinde / Schulträger), several of which span
more than one political municipality: not included (no 1:1 mapping).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.sources.kt_finance.kthelp import complete, ods_csv, to_ref, zh_current

SOURCE = "kt_pupils"
M = "pup_compulsory"
NOT_COVERED = {
    "TG": "Thurgau counts pupils by school municipality (Schulgemeinde), which does not map 1:1 to political municipalities",
    "SG": "St.Gallen counts pupils by school board (Schulträger), which does not map 1:1 to political municipalities",
    "LU": "Lucerne publishes pupils per municipality only in PDF profiles",
}
DEFAULT_NC = "this canton publishes no machine-readable pupil counts by municipality of residence"


def zh() -> tuple[pd.DataFrame, pd.DataFrame]:
    gs, ks = [], []
    for ind in (143, 149, 147):
        g, k = zh_current(ind, SOURCE)
        gs.append(g.set_index(["bfs_nr", "year"])["value"].rename(ind))
        ks.append(k.set_index("year")["value"].rename(ind))
    g = pd.concat(gs, axis=1)
    k = pd.concat(ks, axis=1)
    w = g.sum(axis=1, min_count=3).rename("n").reset_index().rename(columns={"year": "period"})
    kt = k.sum(axis=1, min_count=3).rename("n").reset_index().rename(columns={"year": "period"}).assign(unit="ZH")
    return w.dropna(subset=["n"]), kt.dropna(subset=["n"])


def bl() -> pd.DataFrame:
    d = ods_csv("data.bl.ch", "10420", SOURCE)
    d = d[d["schulstufe_grob_code"] == 1]
    w = d.groupby(["bfs_nummer", "jahr"])["wert"].sum().rename("n").reset_index()
    return w.rename(columns={"bfs_nummer": "bfs_nr", "jahr": "period"})


def fr() -> pd.DataFrame:
    d = ods_csv("opendata.fr.ch", "15_02_eleves_lieu_domicile", SOURCE)
    d = d[(d["classification_ch1"] == "Scolarité obligatoire") & d["canton_id_domicile"].eq(10)]
    w = d.groupby(["commune_id_domicile", "annee"])["eleves"].sum().rename("n").reset_index()
    return w.rename(columns={"commune_id_domicile": "bfs_nr", "annee": "period"})


def observations() -> pd.DataFrame:
    parts, natives, cov = [], [], {}
    for kt, fn in (("ZH", zh), ("BL", bl), ("FR", fr)):
        res = fn()
        w, k = res if isinstance(res, tuple) else (res, None)
        w["period"] = w["period"].astype(int).astype(str)
        parts.append(to_ref(w, {"n": M}, SOURCE, kt))
        cov[(M, kt)] = set(w["period"])
        if k is not None:
            k["period"] = k["period"].astype(int).astype(str)
            natives.append(emit(k, {"n": M}, "period", SOURCE, level="kanton", unit_col="unit",
                                provenance="native"))
    obs = pd.concat(parts, ignore_index=True)
    obs = complete(obs, SOURCE, {M: {"ZH", "BL", "FR"}}, NOT_COVERED, DEFAULT_NC, covered_periods=cov)
    return pd.concat([obs, *natives], ignore_index=True)
