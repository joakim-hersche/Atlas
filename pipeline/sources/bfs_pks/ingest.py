"""BFS Polizeiliche Kriminalstatistik (PKS): offences by district and canton, 2009-latest.

National coverage below the canton: the PKS is published by district (Bezirk) for all of
Switzerland in the Swiss Stats Map Explorer (dataset ch_19_03). There is no national municipal
PKS table (cities >= 30,000 residents: bfs_pks_staedte; a few cantons: kt_crime).

Delivered (native values, no reprojection):
  level bezirk   143 districts on the state of 1 Jan 2023 (vintage 2023-01-01), all years
                 back-cast by BFS on that state. Cantons without districts appear as one unit
                 (e.g. 1200 Basel-Stadt, 2500 Genève), matching the register's district numbers.
                 The only change to the reference state: Moutier moved from district 241 Jura
                 bernois (BE) to the new district 2604 (JU) on 1 Jan 2026 -> 241 keeps Moutier
                 (noted), 2604 has no PKS value (not_published).
  level kanton   26 cantons (nivgeo kant2022_01_01).
  level schweiz  sum of the 26 published canton values, except the Criminal Code total, which
                 is the published national total of STAT-TAB px-x-1903020100_101 (it includes
                 offences that are not assigned to a canton, e.g. 4,612 in 2009 and 48 in 2025).
Per offence group: the count of offences registered by the police (base, sum) and, shared by
all groups, the population the PKS divides by (pks_pop: permanent residents on 31 Dec of the
previous year). The rates per 1,000 (BFS Häufigkeitszahl) are derived ratios count/pks_pop*1000;
they reproduce the published Häufigkeitszahl.

District counts do not add up to the canton counts: offences the police could not assign to a
district are only in the canton value (e.g. Aargau 2009: 6,633 StGB offences; Genève 1,200-3,900
a year). Populations add up exactly.

Clearance (canton and Switzerland only): StGB offences recorded as cleared ('aufgeklärt') in
STAT-TAB px-x-1903020100_101; clearance rate = cleared / StGB offences * 100 (derived).

Value order of the Map Explorer arrays: territory-major, years ascending (as for
bfs_social_assistance). Checked on every run (_checks): canton populations = sums of district
populations for every year; canton StGB counts = STAT-TAB canton counts (labelled by year) within
2 offences; Swiss Häufigkeitszahl computed from STAT-TAB and the populations = the Map Explorer's
published national value (GC_indic) within 0.05 for every year.
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from pipeline.common import interim_path
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_pks.fetch import SOURCE, VIEWS, coldata, dam_asset, indic_meta, px_offences, refdata

# Map Explorer indicator -> (raw count variable, metric id)
INDICS = {
    "stgbprotausend": ("stgb", "pks_stgb"),
    "stgbgprotausend": ("stgbg", "pks_violent"),
    "stgb126protausend": ("stgb126", "pks_assault"),
    "stgb180protausend": ("stgb180", "pks_threat"),
    "stgb123protausend": ("stgb123", "pks_injury"),
    "stgb285protausend": ("stgb285", "pks_officials"),
    "stgb140protausend": ("stgb140", "pks_robbery"),
    "stgb139dprotausend": ("stgb139d", "pks_theft"),
    "stgb139eprotausend": ("stgb139e", "pks_burglary"),
    "stgb139frprotausend": ("stgb139fr", "pks_bicycle_theft"),
    "stgb139fzprotausend": ("stgb139fz", "pks_vehicle_theft"),
    "stg144protausend": ("stg144", "pks_damage"),
    "stgb146protausend": ("stgb146", "pks_fraud"),
    "stgb147protausend": ("stgb147", "pks_computer_fraud"),
    "betmgprotausend": ("betmg", "pks_betmg"),
    "aigprotausend": ("aig", "pks_aig"),
}
POP = "pks_pop"
CLEARED = "pks_kt_stgb_cleared"
BEZIRK_STATE = dt.date(2023, 1, 1)
KANTON_STATE = dt.date(2022, 1, 1)
MOUTIER_OLD, MOUTIER_NEW = "241", "2604"
NOTE_241 = ("district on the state of 1 Jan 2023 (PKS geography): includes Moutier, "
            "which moved to the canton of Jura on 1 Jan 2026")
NOTE_2604 = ("district created on 1 Jan 2026; the PKS districts are on the state of 1 Jan 2023 "
             "(Moutier is counted in Jura bernois)")
NOTE_CH_SUM = "sum of the 26 published canton values (offences not assigned to a canton are not included)"
NOTE_CH_PX = "published national total (STAT-TAB px-x-1903020100_101), incl. offences not assigned to a canton"
CHECKS: dict = {}


def _years(indic: str, view: str) -> list[int]:
    m = json.loads(indic_meta(indic, view).read_text(encoding="utf-8"))["content"]
    ys = sorted(int(y) for y in m["options"]["axisAvailableMods"]["annee"])
    if ys != list(range(ys[0], ys[-1] + 1)):
        raise ValueError(f"unexpected year axis {ys}")
    return ys


def _national_hz(indic: str, view: str) -> pd.Series:
    """Published Swiss Häufigkeitszahl per year (GC_indic zonref 'ch')."""
    m = json.loads(indic_meta(indic, view).read_text(encoding="utf-8"))["content"]
    ch = next(z for z in m["zonrefs"] if z["zonref"]["c_id_zonref"] == "ch")
    return pd.Series({int(v["annee"]): float(v[indic]) for v in ch["values"]})


def _matrix(indic: str, var: str, level: str) -> pd.DataFrame:
    view, nivgeo = VIEWS[level]
    m = json.loads(indic_meta(indic, view).read_text(encoding="utf-8"))["content"]["indic"]["frmType"]
    if m["type"] != "p1*var1/var2" or var not in (m["var1"], m["var2"]) or m["var2"] != "pop" or int(m["p1"]) != 1000:
        raise ValueError(f"{indic}: unexpected formula {m}")
    codes = json.loads(refdata(nivgeo).read_text(encoding="utf-8"))["content"]["territories"]["codgeo"]
    vals = np.array(json.loads(coldata(indic, var, view).read_text(encoding="utf-8"))["content"][var], dtype=float)
    years = _years(indic, view)
    if len(vals) != len(codes) * len(years):
        raise ValueError(f"{var}/{view}: {len(vals)} values for {len(codes)} units x {len(years)} years")
    # territory-major, years ascending (module doc; checked in _checks)
    return pd.DataFrame(vals.reshape(len(codes), len(years)), index=[str(c) for c in codes], columns=years)


def _px() -> pd.DataFrame:
    """STAT-TAB: StGB total (all / cleared) by canton code and year."""
    df = px_offences({"Straftat": ["311.00.T0"], "Kanton": "*", "Ausführungsgrad": ["0"],
                      "Aufklärungsgrad": ["0", "2"], "Jahr": "*"})
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.pivot_table(index=["Kanton", "Jahr"], columns="Aufklärungsgrad", values="value").rename(
        columns={"0": "all", "2": "cleared"}).reset_index()


def _px_ch(px: pd.DataFrame) -> pd.Series:
    """Published Swiss StGB total per year (int index)."""
    c = px[px["Kanton"] == "8100"]
    return pd.Series(c["all"].to_numpy(), index=c["Jahr"].astype(int).to_numpy())


def _checks(bez: dict, kt: dict, px: pd.DataFrame, id2ab: dict) -> None:
    pop_b, pop_k = bez[POP], kt[POP]
    kt_of = {c: c[:-2] for c in pop_b.index}   # district number = canton id + 2 digits
    s = pop_b.groupby(pop_b.index.map(kt_of)).sum().reindex(pop_k.index)
    CHECKS["canton_pop_max_abs_diff"] = float((s - pop_k).abs().max().max())
    over = {}
    for mid in bez:
        if mid == POP:
            continue
        d = bez[mid].groupby(bez[mid].index.map(kt_of)).sum().reindex(kt[mid].index) - kt[mid]
        over[mid] = float(d.max().max())   # district sum may be lower (unassigned), never higher
    CHECKS["district_sum_above_canton_max"] = max(over.values())
    p = px[px["Kanton"] != "8100"].copy()
    p["Jahr"] = p["Jahr"].astype(int)
    pk = p.pivot(index="Kanton", columns="Jahr", values="all").reindex(kt["pks_stgb"].index)
    CHECKS["canton_stgb_vs_stattab_max_abs_diff"] = float((pk - kt["pks_stgb"]).abs().max().max())
    ch = _px_ch(px)
    hz = (ch / pop_k.sum() * 1000).round(1)
    pub = _national_hz("stgbprotausend", VIEWS["bezirk"][0]).reindex(hz.index)
    CHECKS["national_hz_max_abs_diff"] = round(float((hz - pub).abs().max()), 3)
    if (CHECKS["canton_pop_max_abs_diff"] > 0 or CHECKS["district_sum_above_canton_max"] > 0
            or CHECKS["canton_stgb_vs_stattab_max_abs_diff"] > 2 or CHECKS["national_hz_max_abs_diff"] > 0.051):
        raise ValueError(f"PKS Map Explorer consistency checks failed: {CHECKS}")


def _long(mats: dict, unit_map=None) -> pd.DataFrame:
    parts = []
    for mid, m in mats.items():
        s = m.stack().rename("value").reset_index()
        s.columns = ["unit_id", "period", "value"]
        s["metric_id"] = mid
        parts.append(s)
    d = pd.concat(parts, ignore_index=True)
    if unit_map:
        d["unit_id"] = d["unit_id"].map(unit_map)
    d["period"] = d["period"].astype(str)
    return d


def _obs(d: pd.DataFrame, level: str, vintage: dt.date) -> pd.DataFrame:
    w = d.pivot_table(index=["unit_id", "period"], columns="metric_id", values="value").reset_index()
    mids = [c for c in w.columns if c not in ("unit_id", "period")]
    return emit(w, {m: m for m in mids}, "period", SOURCE, level=level, unit_col="unit_id",
                vintage=vintage, precision="exact", provenance="native")


def observations() -> pd.DataFrame:
    terms = json.loads(dam_asset().read_text(encoding="utf-8"))["description"]["categorization"]["termsOfUse"]
    if [t["code"] for t in terms] != ["OPEN-BY"]:
        raise ValueError(f"terms of use changed: {terms}")
    cp = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    id2ab = dict(zip(cp["canton_id"].astype(int).astype(str), cp["canton"]))
    bez, kt = {}, {}
    for indic, (var, mid) in INDICS.items():
        bez[mid] = _matrix(indic, var, "bezirk")
        kt[mid] = _matrix(indic, var, "kanton")
    bez[POP] = _matrix("stgbprotausend", "pop", "bezirk")
    kt[POP] = _matrix("stgbprotausend", "pop", "kanton")
    px = _px()
    _checks(bez, kt, px, id2ab)

    ob = _obs(_long(bez), "bezirk", BEZIRK_STATE)
    ob.loc[ob["unit_id"] == MOUTIER_OLD, "note"] = NOTE_241
    years = sorted(ob["period"].unique())
    gap = pd.DataFrame([{"unit_id": MOUTIER_NEW, "level": "bezirk", "vintage": BEZIRK_STATE.isoformat(),
                         "metric_id": m, "period": y, "value": np.nan, "status": "not_published",
                         "precision": "exact", "provenance": "native", "source_id": SOURCE, "note": NOTE_2604}
                        for m in [*bez] for y in years])

    ok = _obs(_long(kt, id2ab), "kanton", KANTON_STATE)
    # Switzerland: sum of cantons; StGB total from STAT-TAB (published, incl. unassigned offences)
    chs = {mid: m.sum().to_frame("CH").T for mid, m in kt.items()}
    chs["pks_stgb"] = _px_ch(px).to_frame("CH").T
    och = _obs(_long(chs), "schweiz", KANTON_STATE)
    och["note"] = np.where(och["metric_id"] == "pks_stgb", NOTE_CH_PX, NOTE_CH_SUM)
    och.loc[och["metric_id"] == POP, "note"] = "sum of the 26 published canton values"

    # clearance (STAT-TAB, canton + Switzerland)
    cl = px.copy()
    cl["unit_id"] = cl["Kanton"].map(lambda k: "CH" if k == "8100" else id2ab[k])
    cl["level"] = np.where(cl["Kanton"] == "8100", "schweiz", "kanton")
    ocl = pd.concat([emit(g, {"cleared": CLEARED}, "Jahr", SOURCE, level=lvl, unit_col="unit_id",
                          vintage=KANTON_STATE, precision="exact", provenance="native")
                     for lvl, g in cl.groupby("level")], ignore_index=True)
    out = pd.concat([ob, gap, ok, och, ocl], ignore_index=True)
    return out[OBS_COLUMNS]
