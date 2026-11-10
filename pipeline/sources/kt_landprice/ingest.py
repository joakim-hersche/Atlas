"""Residential building land prices per Gemeinde, compiled from cantonal statistics (`*`, D5).

- ZH  Statistisches Amt ZH, Gemeindeporträt: 199 Baulandpreis (gewichteter Median der Handänderungen)
      [Fr./m²], 477 Baulandpreis Modell (Median) [Fr./m²], 402 Verkäufe von unbebautem Land [Anz.];
      1974–2024 (sales 2007–2024). ZH back-casts some merged municipalities (see kthelp.zh_current).
      199 is not published for fewer than 4 relevant transactions: shown as `suppressed` where
      ZH reports at least one sale of unbuilt land that year, `no_data` where it reports none.
      Unbuilt land in residential and mixed zones (unbebautes Land in Wohn-/Mischzonen).
- BL  Amt für Daten und Statistik BL, dataset 10200: average price of residential building land
      (Wohnbauland) [CHF/m²] and number of transactions, 1979–2025 (Bezirk Laufen from 1994).
      '( )' = data protection (fewer than 3 transactions) -> `suppressed`; empty = no transaction
      that year -> price `no_data`, count 0.
TG (tax-valuation base prices, not transactions) and GE (dwelling prices) are not included.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.sources.kt_finance.kthelp import complete, ods_csv, to_ref, zh_current

SOURCE = "kt_landprice"
PRICE, MODEL, NTX = "land_price_m2", "land_price_model_m2", "land_transactions"
MAP = {"price": PRICE, "model": MODEL, "ntx": NTX}
RULES = {"price": "not_aggregatable", "model": "not_aggregatable", "ntx": "sum"}
NOT_COVERED = {"TG": "Thurgau publishes only tax-valuation base prices per zone, not transaction prices",
               "GE": "Geneva publishes dwelling prices (houses, flats), not building-land prices"}
DEFAULT_NC = "this canton publishes no building-land prices per municipality"


def zh() -> pd.DataFrame:
    p, _ = zh_current(199, SOURCE)
    m, _ = zh_current(477, SOURCE)
    n, _ = zh_current(402, SOURCE)
    w = (p[["bfs_nr", "year", "value"]].rename(columns={"value": "price"})
         .merge(m[["bfs_nr", "year", "value"]].rename(columns={"value": "model"}), on=["bfs_nr", "year"], how="outer")
         .merge(n[["bfs_nr", "year", "value"]].rename(columns={"value": "ntx"}), on=["bfs_nr", "year"], how="left"))
    w["price__sup"] = w["price"].isna() & (w["ntx"] > 0)
    return w.rename(columns={"year": "period"})


def bl() -> pd.DataFrame:
    d = ods_csv("data.bl.ch", "10200", SOURCE)
    for c in ("falle", "quadratmeterpreis_chf"):
        d[c] = d[c].astype("string")
    sup = d["quadratmeterpreis_chf"].eq("( )").fillna(False)
    none = d["falle"].isna()
    w = pd.DataFrame({"bfs_nr": d["bfs_nummer"].astype(int), "period": d["jahr"].astype(int),
                      "price": pd.to_numeric(d["quadratmeterpreis_chf"], errors="coerce"),
                      "ntx": pd.to_numeric(d["falle"], errors="coerce")})
    w.loc[none, "ntx"] = 0.0
    w["price__sup"] = sup.to_numpy()
    w["ntx__sup"] = sup.to_numpy()
    return w


def observations() -> pd.DataFrame:
    parts, cov = [], {}
    for kt, fn in (("ZH", zh), ("BL", bl)):
        w = fn()
        w["period"] = w["period"].astype(int).astype(str)
        cols = [c for c in MAP if c in w]
        o = to_ref(w, {c: MAP[c] for c in cols}, SOURCE, kt, rules=RULES)
        if kt == "ZH":
            nd = o["metric_id"].eq(PRICE) & o["status"].eq("no_data")
            o.loc[nd, "note"] = "no sale of unbuilt land reported by ZH this year"
            o.loc[o["status"].eq("suppressed"), "note"] = ("not published by ZH (fewer than 4 relevant "
                                                            "transactions)")
        else:
            o.loc[o["status"].eq("suppressed"), "note"] = "not published by BL (data protection: fewer than 3 transactions)"
            nd = o["metric_id"].eq(PRICE) & o["status"].eq("no_data")
            o.loc[nd, "note"] = "no transaction of residential building land this year (BL)"
        parts.append(o)
        for c in cols:
            cov[(MAP[c], kt)] = set(w["period"])
    obs = pd.concat(parts, ignore_index=True)
    covered = {}
    for m, kt in cov:
        covered.setdefault(m, set()).add(kt)
    return complete(obs, SOURCE, covered, NOT_COVERED, DEFAULT_NC, covered_periods=cov)
