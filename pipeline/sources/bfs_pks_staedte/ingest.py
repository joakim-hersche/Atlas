"""BFS PKS: selected Criminal Code offences per 1,000 residents (Häufigkeitszahl) for the 27 cities
with at least 30,000 residents, 2009-latest (BFS table je-d-19.02.01.01.04).

The table gives rates only (no counts), rounded in the file to ~9 decimals; one block per offence
group with one row per year and one column per city. Cities are named (no BFS numbers) and
matched by an explicit list below; the table is on the municipality state of 6 Apr 2025
('Gemeindestand 06.04.2025', back-cast by BFS) and is brought to the reference state 1:1
(rates: not_aggregatable). 'x' = 1 to 9 offences, withheld for data protection -> suppressed.
Cells carrying footnote 4 (e.g. '11.64)' = 11.6 with footnote 4, Neuchâtel threats 2017) are read
as the value without the footnote mark, with the footnote as note.
Partial coverage: municipality level for 27 cities only; all other municipalities have no row
(their district value is in bfs_pks).
Cross-check (2026-11-10): Zürich city = district 112 Zürich; the city theft, burglary, violent and
robbery rates equal bfs_pks district counts / population for 2009 and 2025 to 3 decimals.
"""
from __future__ import annotations

import datetime as dt
import json
import re

import numpy as np
import openpyxl
import pandas as pd

from pipeline.harmonize.helpers import emit, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_pks_staedte.fetch import SOURCE, asset_meta, table

STATE = dt.date(2025, 4, 6)
# header (hyphenation and spaces removed) -> BFS number on the 2025-04-06 state
CITIES = {"Dübendorf": 191, "Uster": 198, "Winterthur": 230, "Zürich": 261, "Bern": 351, "Köniz": 355,
          "Biel/Bienne": 371, "Thun": 942, "Emmen": 1024, "Kriens": 1059, "Luzern": 1061, "Zug": 1711,
          "Freiburg": 2196, "Basel": 2701, "Schaffhausen": 2939, "St.Gallen": 3203, "Chur": 3901,
          "Bellinzona": 5002, "Lugano": 5192, "Lausanne": 5586, "Yverdon-les-Bains": 5938, "Sion": 6266,
          "LaChaux-de-Fonds": 6421, "Neuenburg": 6458, "Genf": 6621, "Lancy": 6628, "Vernier": 6643}
# block title (start, whitespace-normalised) -> metric id
BLOCKS = {"Diebstahl (ohne Ladendiebstahl)": "pks_city_theft_hz",
          "davon Einbruch- /Einschleichdiebstahl": "pks_city_burglary_hz",
          "davon Fahrraddiebstahl": "pks_city_bicycle_theft_hz",
          "davon Fahrzeugdiebstahl": "pks_city_vehicle_theft_hz",
          "Sachbeschädigung (ohne Diebstahl)": "pks_city_damage_hz",
          "Betrug (Art.146)": "pks_city_fraud_hz",
          "Betrügerischer Missbrauch einer Datenverarbeitungsanlage": "pks_city_computer_fraud_hz",
          "Total Gewaltstrafaten": "pks_city_violent_hz",
          "davon Tätlichkeiten": "pks_city_assault_hz",
          "davon Drohung": "pks_city_threat_hz",
          "davon Körperverletzungen": "pks_city_injury_hz",
          "davon Gewalt und Drohung gegen Behörden und Beamte": "pks_city_officials_hz",
          "davon Raub": "pks_city_robbery_hz"}
NE_NOTE = ("BFS footnote 4: Neuchâtel has recorded fewer threats since 2017 (no threat recorded when "
           "other offences are recorded in the same case); value given to 1 decimal")
SUPPRESSED = "withheld by BFS for data protection: 1 to 9 offences ('x')"


def parse(path) -> pd.DataFrame:
    ws = openpyxl.load_workbook(path, data_only=True)["19.2.1.1.4"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    hdr_i = next(i for i, r in enumerate(rows) if r[1] == "Dübendorf")
    cols = {}
    for j, v in enumerate(rows[hdr_i]):
        if v is None:
            continue
        key = re.sub(r"\s+", "", str(v)).replace("-", "")
        hit = [c for c in CITIES if c.replace("-", "") == key]
        if len(hit) != 1:
            raise ValueError(f"unknown city header {v!r}")
        cols[j] = CITIES[hit[0]]
    if len(cols) != len(CITIES):
        raise ValueError(f"expected {len(CITIES)} cities, found {len(cols)}")
    out, metric, seen = [], None, set()
    for r in rows[hdr_i + 1:]:
        a = r[0]
        if isinstance(a, str) and all(v is None for v in r[1:]):
            t = re.sub(r"\s+", " ", a).strip()
            hit = [m for k, m in BLOCKS.items() if t.startswith(k)]
            metric = hit[0] if hit else None
            if t.startswith(("1)", "Quellen")):
                break
            if metric:
                seen.add(metric)
            continue
        y = re.match(r"^(\d{4})\b", str(a)) if a is not None else None
        if metric is None or y is None:
            continue   # blank rows, 'Differenz 2025-2024'
        for j, nr in cols.items():
            v = r[j]
            if isinstance(v, (int, float)):
                out.append((nr, y.group(1), metric, float(v), "ok", None))
            elif (fm := re.fullmatch(r"(\d+(?:\.\d+)?)\s?4\)", str(v).strip())):
                out.append((nr, y.group(1), metric, float(fm.group(1)), "ok", NE_NOTE))
            elif str(v).strip() == "x":
                out.append((nr, y.group(1), metric, np.nan, "suppressed", SUPPRESSED))
            else:
                out.append((nr, y.group(1), metric, np.nan, "no_data", f"BFS {v!r}"))
    if seen != set(BLOCKS.values()):
        raise ValueError(f"missing offence blocks: {set(BLOCKS.values()) - seen}")
    return pd.DataFrame(out, columns=["bfs_nr", "period", "metric_id", "value", "status", "note"])


def observations() -> pd.DataFrame:
    terms = json.loads(asset_meta().read_text(encoding="utf-8"))["description"]["categorization"]["termsOfUse"]
    if [t["code"] for t in terms] != ["OPEN-BY"]:
        raise ValueError(f"terms of use changed: {terms}")
    d = parse(table())
    w = d.pivot_table(index=["bfs_nr", "period"], columns="metric_id", values="value").reset_index()
    full = d[["bfs_nr", "period"]].drop_duplicates()
    w = full.merge(w, on=["bfs_nr", "period"], how="left")
    mids = sorted(d["metric_id"].unique())
    for m in mids:
        if m not in w:
            w[m] = np.nan
    ref, unm = to_reference(w, STATE, mids, ["period"], rule="not_aggregatable", bfs_already_current=True)
    if len(unm):
        raise ValueError(f"unmapped cities: {unm}")
    obs = emit(ref, {m: m for m in mids}, "period", SOURCE)
    # carry the source status ('x' suppressed) where the value is missing
    st = d.set_index(["bfs_nr", "period", "metric_id"])[["status", "note"]]
    key = pd.MultiIndex.from_arrays([obs["unit_id"].astype(int), obs["period"], obs["metric_id"]])
    miss = obs["value"].isna().to_numpy()
    src = st.reindex(key)
    obs.loc[miss, "status"] = src["status"].to_numpy()[miss]
    obs.loc[miss, "note"] = src["note"].to_numpy()[miss]
    obs["status"] = obs["status"].fillna("no_data")
    return obs[OBS_COLUMNS]
