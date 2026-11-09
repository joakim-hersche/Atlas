"""Energy transition per municipality: Energie Reporter (monthly), BFE solar potential, Energiestädte.

Energie Reporter (geoimpact / EnergieSchweiz, CC BY 4.0), historized monthly slices 2021-03..latest.
  Each slice is on the municipality state of its date (inferred from its BFS numbers) and is mapped
  to the reference state: counts with rule 'sum', shares (e-car share, solar potential usage) with
  'not_aggregatable' (kept where the mapping is 1:1). Period = slice month 'YYYY-MM'.
  Renewable heating share = renewable / (renewable + non-renewable) heating systems (checked against
  the published share: identical up to rounding), so the counts are delivered and the share derived.
  Per-capita values (PV kWp, electricity consumption, renewable production) are computed here from
  the reprojected totals and STATPOP pop_total (31 Dec of the previous year for Jan–Nov slices, same
  year for December slices, latest year 2025 at most), because the build can only form ratios of
  equal periods and STATPOP is annual. Reads data/interim/observation/bfs_statpop.parquet.
  Slices whose BFS-number set matches no single municipality state (2025-01, 2026-01: old and new
  numbers of merged municipalities side by side, indicators split between them) are skipped; the
  canton/national rows of those months are kept.
Solar potential (BFE OGD 52, release 2025-03, municipality state 2025-04-05): roofs only (scenario 1)
  and roofs + facades (scenario 3), GWh per year, summed to the reference state.
Energiestädte (BFE, data.geo.admin.ch): label holders with category (50-64%, 65-74%, Gold) and
  points. Label 0/1 and Gold 0/1 for every municipality; the regional label "Sensebezirk" (2291)
  and the Liechtenstein members are left out.
"""
from __future__ import annotations

import datetime as dt
import json
import zipfile

import numpy as np
import pandas as pd
import pyogrio

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.helpers import emit, infer_vintage, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfe_energy.fetch import energiestaedte, energyreporter_historized, solar_potential

SOURCE = "bfe_energy"
REF_IDS: set[int] | None = None

# reporter column -> (metric id, factor, precision)
COUNTS = {
    "electric_car_count": ("en_ecar_count", 1, "exact"),
    "electric_car_charging_spot_count": ("en_charging_spots", 1, "exact"),
    "solar_power_installed_kwp": ("en_pv_installed_kwp", 1, "exact"),
    "renewable_heating_count": ("en_heat_renewable_count", 1, "exact"),
    "non_renewable_heating_count": ("en_heat_nonrenewable_count", 1, "exact"),
    "elec_consumption_mwh_per_year": ("en_elec_consumption_mwh", 1, "modelled"),
    "renelec_production_mwh_per_year": ("en_renelec_production_mwh", 1, "modelled"),
    "renelec_production_water_mwh_per_year": ("en_renelec_hydro_mwh", 1, "modelled"),
    "renelec_production_solar_mwh_per_year": ("en_renelec_solar_mwh", 1, "modelled"),
}
SHARES = {
    "electric_car_share": ("en_ecar_share", 100, "exact"),
    "solar_potential_usage": ("en_solar_potential_used", 100, "modelled"),
}
PER_CAPITA = {  # metric id -> (total metric id, factor)
    "en_pv_kwp_per_capita": ("en_pv_installed_kwp", 1),
    "en_elec_consumption_per_capita": ("en_elec_consumption_mwh", 1),
    "en_renelec_per_capita": ("en_renelec_production_mwh", 1),
}
WINDOW = {  # rolling 12-month window columns, recorded in the note
    "en_elec_consumption_mwh": ("elec_consumption_date_from", "elec_consumption_date_until"),
    "en_renelec_production_mwh": ("renelec_production_date_from", "renelec_production_date_until"),
    "en_renelec_hydro_mwh": ("renelec_production_date_from", "renelec_production_date_until"),
    "en_renelec_solar_mwh": ("renelec_production_date_from", "renelec_production_date_until"),
}


def _read(name: str) -> pd.DataFrame:
    with zipfile.ZipFile(energyreporter_historized()) as z:
        return pd.read_csv(z.open(name))


def _slice_obs(g: pd.DataFrame, vintage: dt.date, period: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts = []
    w_counts, unm1 = to_reference(g, vintage, list(COUNTS), [], rule="sum")
    w_shares, unm2 = to_reference(g, vintage, list(SHARES), [], rule="not_aggregatable")
    for wide, spec in ((w_counts, COUNTS), (w_shares, SHARES)):
        wide = wide.assign(period=period)
        for col, (mid, f, prec) in spec.items():
            wide[col] = wide[col] * f
            o = emit(wide, {col: mid}, "period", SOURCE)
            o["precision"] = np.where(o["precision"] == "boundary_estimate", "boundary_estimate", prec)
            if mid in WINDOW:
                a, b = WINDOW[mid]
                win = g[a].dropna()
                if len(win):
                    o["note"] = f"12-month window {win.mode().iloc[0]}..{g[b].dropna().mode().iloc[0]}"
            parts.append(o)
    return pd.concat(parts, ignore_index=True), pd.concat([unm1, unm2])


def _pop() -> pd.DataFrame:
    p = interim_path("observation", "bfs_statpop.parquet")
    if not p.exists():
        raise FileNotFoundError("run bfs_statpop first (needed for per-capita values)")
    o = pd.read_parquet(p, columns=["unit_id", "level", "metric_id", "period", "value"])
    o = o[(o["level"] == "gemeinde") & (o["metric_id"] == "pop_total")]
    return o[["unit_id", "period", "value"]].rename(columns={"value": "pop"})


def _pop_year(period: str, years: list[int]) -> str:
    y, m = int(period[:4]), int(period[5:7])
    y = y if m == 12 else y - 1
    return str(min(y, max(years)))


def _per_capita(obs: pd.DataFrame) -> pd.DataFrame:
    pop = _pop()
    years = sorted(int(p) for p in pop["period"].unique())
    out = []
    for mid, (tot, f) in PER_CAPITA.items():
        t = obs[(obs["metric_id"] == tot) & (obs["status"] == "ok")].copy()
        t["pop_period"] = t["period"].map(lambda p: _pop_year(p, years))
        t = t.merge(pop, left_on=["unit_id", "pop_period"], right_on=["unit_id", "period"],
                    suffixes=("", "_p")).drop(columns=["period_p"])
        t["value"] = t["value"] / t["pop"].replace(0, np.nan) * f
        t["status"] = np.where(t["value"].notna(), "ok", "no_data")
        t["metric_id"] = mid
        t["precision"] = np.where(t["precision"] == "boundary_estimate", "boundary_estimate", "modelled")
        t["note"] = "per resident (STATPOP " + t["pop_period"] + ")" + np.where(
            t["note"].notna(), "; " + t["note"].fillna(""), "")
        out.append(t[OBS_COLUMNS])
    return pd.concat(out, ignore_index=True)


def _native(level: str, name: str, unit_col: str) -> pd.DataFrame:
    df = _read(name)
    df["period"] = df["energyreporter_date"].str[:7]
    if level == "schweiz":
        df["unit"] = "CH"
        unit_col = "unit"
    spec = {**COUNTS, **SHARES}
    parts = []
    for col, (mid, f, prec) in spec.items():
        d = df[[unit_col, "period", col]].copy()
        d[col] = d[col] * f
        o = emit(d, {col: mid}, "period", SOURCE, level=level, unit_col=unit_col, precision=prec,
                 provenance="native")
        parts.append(o[o["status"] == "ok"])
    return pd.concat(parts, ignore_index=True)


def _reporter() -> pd.DataFrame:
    m = _read("energyreporter_municipality_historized.csv")
    states: dict[frozenset, tuple[dt.date, float]] = {}
    parts, unmapped, skipped = [], [], []
    for date, g in m.groupby("energyreporter_date"):
        key = frozenset(g["bfs_nr"])
        if key not in states:
            states[key] = infer_vintage(key)
        vintage, jac = states[key]
        if jac < 1:
            # transitional slice right after a merger date: holds both the old and the new numbers,
            # with some indicators on the old and others on the new municipality -> not usable
            skipped.append(date)
            continue
        o, unm = _slice_obs(g, vintage, date[:7])
        parts.append(o)
        if len(unm):
            unmapped.append(unm.assign(slice=date))
    obs = pd.concat(parts, ignore_index=True)
    obs = pd.concat([obs, _per_capita(obs), _native("kanton", "energyreporter_canton_historized.csv", "canton"),
                     _native("schweiz", "energyreporter_national_historized.csv", "country")], ignore_index=True)
    if skipped:
        print("energie reporter: skipped transitional slices", skipped)
    if unmapped:
        u = pd.concat(unmapped)
        print("energie reporter: unmapped rows", len(u), sorted(set(zip(u["slice"], u["bfs_nr"])))[:20])
    return obs


def _solar() -> pd.DataFrame:
    d = pd.DataFrame(json.load(open(solar_potential(), encoding="utf-8")))
    d = d[d["Country"] == "CH"].rename(columns={"MunicipalityNumber": "bfs_nr"})
    cols = {"Scenario1_RoofsOnly_PotentialSolarElectricity_GWh": "en_solar_roof_potential_gwh",
            "Scenario3_RoofsFacades_PotentialSolarElectricity_GWh": "en_solar_roof_facade_potential_gwh"}
    vintage, _ = infer_vintage(d["bfs_nr"])
    wide, _ = to_reference(d.assign(period="2025"), vintage, list(cols), ["period"], rule="sum")
    o = emit(wide, cols, "period", SOURCE)
    o["precision"] = np.where(o["precision"] == "boundary_estimate", "boundary_estimate", "modelled")
    return o


def _energiestadt() -> pd.DataFrame:
    e = pyogrio.read_dataframe(energiestaedte(), read_geometry=False)
    units = pd.read_parquet(interim_path("backbone", "membership_2026-01-01.parquet"), columns=["bfs_nr"])
    ids = units["bfs_nr"].astype(int)
    e = e[e["bfsnummer"].isin(set(ids))].set_index("bfsnummer")
    w = pd.DataFrame({"bfs_nr": ids})
    w["label"] = w["bfs_nr"].isin(e.index).astype(float)
    w["gold"] = w["bfs_nr"].map(e["kategorie_de"].eq("Energiestadt Gold")).fillna(False).astype(float)
    w["score"] = w["bfs_nr"].map(e["punktezahl"]).astype(float)
    w["period"] = "2026"
    o = emit(w, {"label": "energiestadt_label", "gold": "energiestadt_gold", "score": "energiestadt_score"},
             "period", SOURCE, precision="exact", provenance="source_current_state")
    na = (o["metric_id"] == "energiestadt_score") & o["value"].isna()
    o.loc[na, "status"] = "not_applicable"
    o.loc[na, "note"] = "no Energiestadt label"
    return o


def observations() -> pd.DataFrame:
    return pd.concat([_reporter(), _solar(), _energiestadt()], ignore_index=True)[OBS_COLUMNS]
