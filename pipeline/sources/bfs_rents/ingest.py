"""BFS rents from the Structural Survey (SE): average monthly net rent by canton (2010-2024, CHF and
CHF per m², with 95 % CI) and by city for the 3- and 4-room flats of the Swiss cities statistics (SSV,
180 cities, survey years 2022 and 2023).

Rent = monthly net rent without service and heating charges, tenant and cooperative dwellings.
Canton rows: level 'kanton' (unit_id = abbreviation) and 'schweiz', provenance 'native'.
City rows: level 'gemeinde', mapped from the SSV municipality state (REGION_STATE) to the reference
state with rule 'not_aggregatable' (kept only where the city is 1:1 with a reference municipality).
Averages are not additive, so no value is computed for other units.

BFS flags: '( )' in the canton tables (cell number format, < 50 observations) and OBS_STATUS 'U' in
SSV -> value kept, note 'low reliability'; 'X' / OBS_STATUS 'Q' (<= 5 observations) -> suppressed;
'*' -> not_applicable. 2000 (census) and 2003 sheets have another layout and are not ingested.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from pipeline.harmonize.helpers import emit, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_rents.fetch import SOURCE, SSV_VERSIONS, canton_table, ssv_city_rents

# canton names exactly as in the BFS tables -> abbreviation
CANTON = {"Zürich": "ZH", "Bern": "BE", "Luzern": "LU", "Uri": "UR", "Schwyz": "SZ", "Obwalden": "OW",
          "Nidwalden": "NW", "Glarus": "GL", "Zug": "ZG", "Freiburg": "FR", "Solothurn": "SO",
          "Basel-Stadt": "BS", "Basel-Landschaft": "BL", "Schaffhausen": "SH", "Appenzell A.Rh.": "AR",
          "Appenzell I.Rh.": "AI", "St.Gallen": "SG", "Graubünden": "GR", "Aargau": "AG", "Thurgau": "TG",
          "Tessin": "TI", "Waadt": "VD", "Wallis": "VS", "Neuenburg": "NE", "Genf": "GE", "Jura": "JU"}
ROOMS = ["total", "r1", "r2", "r3", "r4", "r5", "r6p"]
HEADER = ["Total", "1", "2", "3", "4", "5", "6+"]
LOW_NOTE = "low reliability: extrapolation from fewer than 50 observations (BFS '( )')"
SUP_NOTE = "suppressed: 5 or fewer observations (BFS 'X')"
FIRST_YEAR = 2010
VINTAGE_LOG: dict = {}


def _metric(kind: str, room: str) -> str:
    base = "rent_avg_chf" if kind == "chf" else "rent_avg_m2"
    return base if room == "total" else f"{base}_{room}"


def parse_canton_table(path, kind: str) -> pd.DataFrame:
    import openpyxl
    wb = openpyxl.load_workbook(path)
    rows = []
    for ws in wb.worksheets:
        if not ws.title.isdigit() or int(ws.title) < FIRST_YEAR:
            continue
        year = ws.title
        cells = [list(r) for r in ws.iter_rows()]
        vals = [[c.value for c in r] for r in cells]
        if str(vals[1][0]).strip() != year:
            raise ValueError(f"{SOURCE} {kind} {year}: year cell {vals[1][0]!r}")
        hdr = next(i for i, r in enumerate(vals) if r[1] is not None and str(r[1]).strip() == "Total")
        cols = {}
        for j, v in enumerate(vals[hdr]):
            if v is not None and str(v).strip() in HEADER:
                cols[ROOMS[HEADER.index(str(v).strip())]] = j
        if kind == "chf" and len(cols) != 7 or kind == "m2" and "total" not in cols:
            raise ValueError(f"{SOURCE} {kind} {year}: unexpected header {vals[hdr]}")
        for i in range(hdr + 1, len(vals)):
            name = str(vals[i][0]).strip() if vals[i][0] is not None else ""
            if name == "Schweiz":
                level, unit = "schweiz", "CH"
            elif name in CANTON:
                level, unit = "kanton", CANTON[name]
            else:
                continue
            for room, j in cols.items():
                v, ci = vals[i][j], vals[i][j + 1]
                low = "(" in (cells[i][j].number_format or "")
                for mid, x, is_ci in ((_metric(kind, room), v, False), (_metric(kind, room) + "_ci", ci, True)):
                    if isinstance(x, (int, float)):
                        rec = dict(value=float(x), status="ok", note=LOW_NOTE if low and not is_ci else None)
                    else:
                        # some cells hold text formulas such as '="X   "'
                        s = str(x if isinstance(v, (int, float)) else v).strip().strip('="').strip()
                        st = "suppressed" if s == "X" else "not_applicable" if s == "*" else "no_data"
                        rec = dict(value=np.nan, status=st,
                                   note=SUP_NOTE if st == "suppressed" else f"BFS '{s}'")
                    rows.append(dict(level=level, unit_id=unit, metric_id=mid, period=year,
                                     vintage=f"{year}-12-31", **rec))
    return pd.DataFrame(rows)


SSV_ITEMS = {"bew_woh_loy_chf_3z": "rent_city_r3", "bew_woh_loy_chf_4z": "rent_city_r4"}


def _ssv_one(version: str) -> pd.DataFrame:
    d = pd.read_csv(ssv_city_rents(version), dtype=str)
    # the 2025 edition prefixes the attribute columns with DIFF_
    d = d.rename(columns={c: c[5:] for c in d.columns if c.startswith("DIFF_")})
    d = d[d["SSV_BUILD_HOUSING_OC"].isin(SSV_ITEMS) & (d["SSV_SWISS_CITY"] != "_ST")]
    if set(d["REGION_REF"]) != {"POLG"} or d["REGION_STATE"].nunique() != 1 or d["PERIOD"].nunique() != 1:
        raise ValueError(f"{SOURCE} SSV {version}: unexpected REGION_REF/REGION_STATE/PERIOD")
    state = dt.datetime.strptime(d["REGION_STATE"].iloc[0], "%d.%m.%Y").date()
    period = str(d["PERIOD"].iloc[0])[-4:]  # '31.12.2023' (2026 edition) or '2022' (2025 edition)
    d = d.assign(metric=d["SSV_BUILD_HOUSING_OC"].map(SSV_ITEMS)
                 + np.where(d["STATISTICAL_OPERATION"] == "CI", "_ci", ""))
    d["value"] = pd.to_numeric(d["OBS_VALUE"], errors="coerce")
    wide = d.pivot_table(index="SSV_SWISS_CITY", columns="metric", values="value", aggfunc="first")
    flag = d[d["STATISTICAL_OPERATION"] == "OBS"].pivot_table(
        index="SSV_SWISS_CITY", columns="metric", values="OBS_STATUS", aggfunc="first")
    wide = wide.reset_index().rename(columns={"SSV_SWISS_CITY": "bfs_nr"})
    wide["bfs_nr"] = wide["bfs_nr"].astype(int)
    wide["period"] = period
    cols = [c for c in wide.columns if c.startswith("rent_city")]
    ref, unm = to_reference(wide, state, cols, ["period"], rule="not_aggregatable")
    VINTAGE_LOG[period] = {"version": version, "region_state": state.isoformat(), "cities": int(len(wide)),
                           "unmapped": int(len(unm)), "mapped": int(ref[cols[0]].notna().sum())}
    # status per city from the source flags (mapped 1:1 cities keep their BFS number)
    flag = flag.reset_index().rename(columns={"SSV_SWISS_CITY": "bfs_nr"})
    flag["bfs_nr"] = flag["bfs_nr"].astype(int)
    obs = emit(ref, {c: c for c in cols}, "period", SOURCE, precision="survey")
    fl = flag.melt(id_vars="bfs_nr", var_name="metric_id", value_name="flag")
    fl = pd.concat([fl, fl.assign(metric_id=fl["metric_id"] + "_ci")])
    fl["unit_id"] = fl["bfs_nr"].astype(str)
    obs = obs.merge(fl[["unit_id", "metric_id", "flag"]], on=["unit_id", "metric_id"], how="left")
    sup = obs["flag"].eq("Q")
    obs.loc[sup, ["value", "status", "note"]] = [np.nan, "suppressed", SUP_NOTE]
    low = obs["flag"].eq("U") & ~obs["metric_id"].str.endswith("_ci") & obs["value"].notna()
    obs.loc[low, "note"] = "low reliability: 50 or fewer observations (BFS OBS_STATUS U)"
    nod = obs["value"].isna() & obs["status"].eq("no_data") & obs["flag"].isna()
    obs.loc[nod, "note"] = "not 1:1 with a reference municipality or not in the SSV city list"
    return obs[OBS_COLUMNS]


def observations() -> pd.DataFrame:
    parts = []
    for kind in ("chf", "m2"):
        c = parse_canton_table(canton_table(kind), kind)
        c["precision"], c["provenance"], c["source_id"] = "survey", "native", SOURCE
        parts.append(c[OBS_COLUMNS])
    for v in SSV_VERSIONS:
        parts.append(_ssv_one(v))
    out = pd.concat(parts, ignore_index=True)
    out["value"] = out["value"].astype(float)
    return out
