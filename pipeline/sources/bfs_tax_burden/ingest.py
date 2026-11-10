"""ESTV tax burden as republished by BFS under OPEN-BY (the ESTV calculator export itself is held back).

1) Cities (Statistik der Schweizer Städte, 180 cities, tax years 2023 and 2024): burden in % of gross
   income for four household cases at selected incomes, and the wealth-tax burden of a married
   couple in % of net wealth. Level 'gemeinde', partial coverage; the SSV municipality state
   (REGION_STATE) is mapped 1:1 to the reference state (not_aggregatable).
   The flows do not say which taxes are included. Checked against the ESTV calculator (tax year
   2024, married, one income, 2 children, CHF 100,000): the city values equal the calculator's total
   (federal + cantonal + municipal + church + personal tax) to within 0.006 percentage points in
   about half the cities; elsewhere they differ by up to 0.5 points by canton (GE, NE, JU, FR most),
   which points to a different church-tax assumption. Without the federal tax the match is worse.
2) Labour market areas 2018 (Indikatoren regionaler Disparitäten, 2010-2025): estimated average
   burden 'durch Bundes-, Kantons-, Gemeinde- und Kirchensteuern', weighted by the permanent resident
   population of each municipality. Level 'arbeitsmarktgebiet' (unit = BAE2018 code without the
   leading zero, as in the backbone membership), provenance 'native'. CI cells are empty in the
   source and not delivered.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from pipeline.harmonize.helpers import emit, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_tax_burden.fetch import SOURCE, SSV_FLOWS, SSV_VERSIONS, amr_tax, ssv_flow

# flow -> metric prefix; income levels (kCHF) delivered per flow
CASES = {"DF_SSV_TAX_BRDN_REV_SIN": "taxb_city_single",
         "DF_SSV_TAX_BRDN_REV_MAR_NC": "taxb_city_married",
         "DF_SSV_TAX_BRDN_REV_MAR_2C": "taxb_city_married2c",
         "DF_SSV_TAX_BRDN_REV_RENT": "taxb_city_pensioners",
         "DF_SSV_TAX_BRDN_FOR_MAR_NC": "taxb_city_wealth_married"}
INCOMES = ["50", "80", "100", "150", "200", "500"]
WEALTH = ["500", "1000"]
AMR = {"EC6004I": "taxb_amr_single_40k", "EC6003I": "taxb_amr_single_80k", "EC6005I": "taxb_amr_single_150k",
       "EC6001I": "taxb_amr_married2c2i_60k", "EC6000I": "taxb_amr_married2c2i_125k",
       "EC6002I": "taxb_amr_married2c2i_250k"}
SUP_NOTE = "suppressed by the source (OBS_STATUS Q)"
VINTAGE_LOG: dict = {}


def _metric(flow: str, level: str) -> str:
    return f"{CASES[flow]}_{level}k"


def _ssv_edition(version: str) -> pd.DataFrame:
    parts, state, period = [], None, None
    for flow in SSV_FLOWS:
        d = pd.read_csv(ssv_flow(flow, version), dtype=str)
        d = d.rename(columns={c: c[5:] for c in d.columns if c.startswith("DIFF_")})
        # the income/wealth dimension is named after the flow in 2025.2, SSV_TAX_BURDEN in 2026.1.0
        if list(d.columns[:3]) != ["DATAFLOW", "SSV_SWISS_CITY", "SSV_CLASS_CITY"]:
            raise ValueError(f"{SOURCE} {flow} {version}: unexpected columns {list(d.columns)}")
        d = d.rename(columns={d.columns[3]: "SSV_TAX_BURDEN"})
        d["SSV_TAX_BURDEN"] = d["SSV_TAX_BURDEN"].str.rsplit("_", n=1).str[-1]  # 'rev_cel_80' (2025.2) -> '80'
        d = d[d["SSV_SWISS_CITY"] != "_ST"]
        if set(d["REGION_REF"]) != {"POLG"} or d["REGION_STATE"].nunique() != 1 or d["PERIOD"].nunique() != 1:
            raise ValueError(f"{SOURCE} {flow} {version}: unexpected REGION_REF/REGION_STATE/PERIOD")
        s = dt.datetime.strptime(d["REGION_STATE"].iloc[0], "%d.%m.%Y").date()
        p = str(d["PERIOD"].iloc[0])[-4:]
        if state not in (None, s) or period not in (None, p):
            raise ValueError(f"{SOURCE} {version}: flows disagree on state/period")
        state, period = s, p
        levels = WEALTH if flow.startswith("DF_SSV_TAX_BRDN_FOR") else INCOMES
        d = d[d["SSV_TAX_BURDEN"].isin(levels)]
        if d["SSV_TAX_BURDEN"].nunique() != len(levels):
            raise ValueError(f"{SOURCE} {flow} {version}: income/wealth levels missing")
        parts.append(d.assign(metric=[_metric(flow, x) for x in d["SSV_TAX_BURDEN"]]))
    d = pd.concat(parts, ignore_index=True)
    d["value"] = pd.to_numeric(d["OBS_VALUE"], errors="coerce")
    d.loc[d["OBS_STATUS"].eq("Q"), "value"] = np.nan
    wide = d.pivot_table(index="SSV_SWISS_CITY", columns="metric", values="value", aggfunc="first", dropna=False)
    wide = wide.reset_index().rename(columns={"SSV_SWISS_CITY": "bfs_nr"})
    wide["bfs_nr"] = wide["bfs_nr"].astype(int)
    wide["period"] = period
    cols = [c for c in wide.columns if c.startswith("taxb_city")]
    ref, unm = to_reference(wide, state, cols, ["period"], rule="not_aggregatable")
    VINTAGE_LOG[period] = {"version": version, "region_state": state.isoformat(), "cities": int(len(wide)),
                           "unmapped": int(len(unm)), "mapped": int(ref[cols].notna().any(axis=1).sum())}
    obs = emit(ref, {c: c for c in cols}, "period", SOURCE, precision="modelled")
    q = d[d["OBS_STATUS"].eq("Q")][["SSV_SWISS_CITY", "metric"]].rename(
        columns={"SSV_SWISS_CITY": "unit_id", "metric": "metric_id"}).assign(q=True)
    obs = obs.merge(q, on=["unit_id", "metric_id"], how="left")
    obs.loc[obs["q"].eq(True), ["status", "note"]] = ["suppressed", SUP_NOTE]
    obs.loc[obs["value"].isna() & obs["status"].eq("no_data"), "note"] = \
        "not 1:1 with a reference municipality, or no value in the source"
    return obs[OBS_COLUMNS]


def _amr() -> pd.DataFrame:
    d = pd.read_csv(amr_tax(), dtype=str)
    d = d[(d["STATISTICAL_OPERATION"] == "OBS") & d["ID_INDIC_DISPR"].isin(AMR)]
    if d["ID_RAUM"].nunique() != 101:
        raise ValueError(f"{SOURCE} RDISP: expected 101 labour market areas, got {d['ID_RAUM'].nunique()}")
    out = pd.DataFrame({
        "unit_id": d["ID_RAUM"].astype(int).astype(str),
        "level": "arbeitsmarktgebiet",
        "vintage": d["TIME_PERIOD"].astype(str) + "-12-31",
        "metric_id": d["ID_INDIC_DISPR"].map(AMR),
        "period": d["TIME_PERIOD"].astype(str),
        "value": pd.to_numeric(d["OBS_VALUE"], errors="coerce").astype(float),
        "precision": "modelled", "provenance": "native", "source_id": SOURCE,
    })
    out["status"] = np.where(out["value"].notna(), "ok", "no_data")
    out["note"] = None
    return out[OBS_COLUMNS]


def observations() -> pd.DataFrame:
    parts = [_ssv_edition(v) for v in SSV_VERSIONS] + [_amr()]
    return pd.concat(parts, ignore_index=True)
