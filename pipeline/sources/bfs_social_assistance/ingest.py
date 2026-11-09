"""BFS social assistance (SHS) per municipality, 2007-latest, from the Map Explorer JSON.

The value arrays (GC_coldata) are flat. Their order was established before ingesting
(checked again on every run, see _check_order):
  territory-major, years ascending: value[i * n_years + t] = territory codgeo[i] (GC_refdata
  order, string-sorted BFS numbers) in year 2007 + t.
Evidence (2026-11-09): (1) the 2019 rates match the independent Regionalporträts 2021 file
(Sozialhilfequote 2019) for 95 % of 1647 municipalities (rest = rounding of .x5 halves and merged
municipalities), while every other layout/year matches < 10 %; (2) summing municipal recipients per
canton reproduces the separate canton array year by year (municipal sum 1-2.5 % above the canton
value, as documented: movers are counted in each municipality), and any year shift, reversed years
or a year-major layout fits much worse.

Recipients are cumulative over the year; summing municipalities overstates canton totals by
~1-2.5 % (documented double counting). The rate is BFS's own (denominator: STATPOP of the previous
year; from 2025 cumulative population of the year), so it is delivered as published and
not_aggregatable. -9999 = not available (small numbers or data not delivered, e.g. Genève 2025):
status no_data. 2024-2025 use BFS weighting during the modernisation of the statistic (time-series
break in 2025): precision modelled.
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_social_assistance.fetch import (SOURCE, coldata, indic_meta, refdata,
                                                          regionalportraets_2021)
from pipeline.sources.estv_dbst.refhelp import SUP, per_period_to_reference

NIVGEO, VIEW, VIEW_KT, NIVGEO_KT = "polg2025_04_06", "map226", "map164", "kant2022_01_01"
INDICS = {"sozialhilfeempf": "sh_recipients", "sozialhilfequot": "sh_rate"}
FIRST_YEAR = 2007
VINTAGE_LOG: dict = {}
CHECKS: dict = {}


def _years(view: str) -> list[int]:
    m = json.loads(indic_meta("sozialhilfequot", view).read_text(encoding="utf-8"))["content"]
    ys = sorted(int(y) for y in m["options"]["axisAvailableMods"]["annee"])
    if ys != list(range(FIRST_YEAR, ys[-1] + 1)):
        raise ValueError(f"unexpected year axis {ys}")
    return ys


def _matrix(indic: str, view: str, nivgeo: str) -> pd.DataFrame:
    codes = json.loads(refdata(nivgeo).read_text(encoding="utf-8"))["content"]["territories"]["codgeo"]
    d = json.loads(coldata(indic, view).read_text(encoding="utf-8"))
    vals = np.array(d["content"][indic], dtype=float)
    years = _years(view)
    if len(vals) != len(codes) * len(years):
        raise ValueError(f"{indic}/{view}: {len(vals)} values for {len(codes)} units × {len(years)} years")
    m = vals.reshape(len(codes), len(years))  # territory-major, years ascending (see module doc)
    return pd.DataFrame(m, index=[int(c) for c in codes], columns=years)


def _check_order(rate: pd.DataFrame, recip: pd.DataFrame) -> None:
    """Re-run the two order checks; refuse to ingest if they fail."""
    rp = pd.read_excel(regionalportraets_2021(), header=None, skiprows=9)
    rp = rp[pd.to_numeric(rp[0], errors="coerce").notna()]
    ref = pd.Series(pd.to_numeric(rp[32], errors="coerce").values, index=rp[0].astype(int))
    common = [c for c in rate.index if c in ref.index and pd.notna(ref[c]) and rate.loc[c, 2019] != -9999]
    match = (np.abs(rate.loc[common, 2019].values - ref[common].values) <= 0.0501).mean()
    CHECKS["regionalportraets_2019_match"] = round(float(match), 4)
    CHECKS["regionalportraets_2019_n"] = len(common)
    # canton consistency
    kt = _matrix("sozialhilfeempf", VIEW_KT, NIVGEO_KT).replace(-9999, np.nan)
    from pipeline.backbone.crosswalk import load_backbone, versions_at
    mv, _ = load_backbone()
    v = versions_at(mv, dt.date(2025, 4, 6))
    cp = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    ab2id = dict(zip(cp["canton"], cp["canton_id"].astype(int)))
    cid = dict(zip(v["bfs_nr"].astype(int), v["canton"].map(ab2id)))
    s = recip.replace(-9999, np.nan).groupby(recip.index.map(cid)).sum(min_count=1).loc[kt.index]
    rel = (s / kt - 1).abs()
    CHECKS["canton_sum_median_abs_rel_diff"] = round(float(np.nanmedian(rel.values)), 4)
    if match < 0.9 or CHECKS["canton_sum_median_abs_rel_diff"] > 0.05:
        raise ValueError(f"Map Explorer value order check failed: {CHECKS}")


def observations() -> pd.DataFrame:
    recip = _matrix("sozialhilfeempf", VIEW, NIVGEO)
    rate = _matrix("sozialhilfequot", VIEW, NIVGEO)
    _check_order(rate, recip)
    long = []
    for name, m in (("recip", recip), ("rate", rate)):
        s = m.stack().rename(name)
        s.index.names = ["bfs_nr", "period"]
        long.append(s)
    w = pd.concat(long, axis=1).reset_index()
    w["period"] = w["period"].astype(str)
    for c in ("recip", "rate"):
        w[c + SUP] = w[c] == -9999
        w.loc[w[c + SUP], c] = np.nan
    obs = per_period_to_reference(w, {"recip": "sh_recipients", "rate": "sh_rate"}, SOURCE,
                                  rules={"rate": "not_aggregatable"}, vintage=dt.date(2025, 4, 6),
                                  log=VINTAGE_LOG)
    na = obs["status"] == "suppressed"
    obs.loc[na, "status"] = "no_data"
    obs.loc[na, "note"] = "not available in source (-9999: small numbers or data not delivered)"
    late = obs["period"].isin(["2024", "2025"]) & (obs["precision"] == "exact")
    obs.loc[late, "precision"] = "modelled"
    obs.loc[late & obs["note"].isna(), "note"] = "BFS weighting during the SHS modernisation (break in series 2025)"
    # canton values as published (native)
    cp = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    id2ab = dict(zip(cp["canton_id"].astype(int), cp["canton"]))
    native = []
    for indic, metric in INDICS.items():
        k = _matrix(indic, VIEW_KT, NIVGEO_KT).replace(-9999, np.nan).stack().rename("v").reset_index()
        k.columns = ["kt", "period", "v"]
        k["unit_id"] = k["kt"].map(id2ab)
        k["period"] = k["period"].astype(str)
        o = emit(k, {"v": metric}, "period", SOURCE, level="kanton", unit_col="unit_id",
                 vintage=REFERENCE_DATE, precision="exact", provenance="native")
        o.loc[o["period"].isin(["2024", "2025"]), "precision"] = "modelled"
        native.append(o)
    return pd.concat([obs, *native], ignore_index=True)[OBS_COLUMNS]
