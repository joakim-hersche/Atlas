"""Demographic balance per municipality, 1981–latest (BFS PxWeb px-x-0102020000_201).

Components of population change (ESPOP to 2010, STATPOP/BEVNAT from 2011), published by BFS on
the latest municipality state. Geo value codes are running indices; BFS numbers are parsed from
the labels (pxgeo.geo_codes).

Three Thurgau units of the 1990s municipal reform (cube codes 4505 Neukirch an der Thur,
4670 Illighausen, 4695 Scherzingen) could not be assigned to one current municipality by BFS.
The cube lists them with their values up to their abolition and zeros afterwards; their values are
needed for the TG and CH totals to add up. They are mapped to the register versions of the same
name (hist_id 12510, 11544, 13036) and reprojected with the crosswalk weights (successor rows
become 'boundary_estimate' for those years); the zero rows after abolition are dropped.

Units created in that reform (4501, 4546, 4621, 4643, 4683, 4691, 4716, 4723, 4724, 4786, 4826)
and 0630 Allmendingen (BE, 1993) are listed with zeros before their creation (their residents are
in other units then): those municipality-years are 'not_published', never 0.

The geo unit 'Ohne Angabe' (from 2011; mostly emigrations of persons without a known place of
residence) is part of the Swiss total but of no canton: kept as level 'unallocated'.
Switzerland = Σ cantons + Ohne Angabe (checked 2011–2025, e.g. emigration 2013: 3,726).
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import geo_codes, to_obs, unallocated_rows
from pipeline.sources.bfs_pxweb.fetch import query_codes

SOURCE = "bfs_bevnat_bilanz"
DB = "px-x-0102020000_201"
G = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"
NAT, SEX, COMP = "Staatsangehörigkeit (Kategorie)", "Geschlecht", "Demografische Komponente"
LEGACY = {4505: 12510, 4670: 11544, 4695: 13036}

COMPONENTS = {  # component code -> metric id (nationality total)
    "0": "bil_pop_jan",
    "1": "bil_births",
    "2": "bil_deaths",
    "3": "bil_natural_balance",
    "4": "bil_immigration",
    "5": "bil_intercant_in",
    "6": "bil_intracant_in",
    "7": "bil_emigration",
    "8": "bil_intercant_out",
    "9": "bil_intracant_out",
    "10": "bil_net_migration",
    "16": "bil_pop_dec",
}


def wide() -> pd.DataFrame:
    codes, _, _ = geo_codes(DB, G)
    tot = query_codes(DB, {"Jahr": "*", G: "*", NAT: ["0"], SEX: ["0"], COMP: "*"})
    w = tot[tot[COMP].isin(COMPONENTS)].pivot_table(index=[G, "Jahr"], columns=COMP, values="value",
                                                     aggfunc="first")
    w = w.rename(columns=COMPONENTS)
    nat = query_codes(DB, {"Jahr": "*", G: "*", NAT: ["1", "2"], SEX: ["0"], COMP: ["0", "12"]})
    fj = nat[(nat[NAT] == "2") & (nat[COMP] == "0")].set_index([G, "Jahr"])["value"]
    nz = nat[(nat[NAT] == "1") & (nat[COMP] == "12")].set_index([G, "Jahr"])["value"]
    w["bil_pop_foreign_jan"] = fj
    w["bil_naturalisations"] = nz
    # net international / intercantonal migration as counts (sum-aggregatable)
    w["bil_net_international"] = w["bil_immigration"] - w["bil_emigration"]
    w["bil_net_intercant"] = w["bil_intercant_in"] - w["bil_intercant_out"]
    w = w.reset_index()
    w["geo"] = w[G].map(codes)
    return w


def observations(report: dict | None = None) -> pd.DataFrame:
    w = wide()
    cols = [c for c in w.columns if c.startswith("bil_")]
    # Units created by the 1990s Thurgau reform (and Allmendingen BE, 1993) are listed with zeros
    # for the years before their creation; their residents of those years are counted in other
    # units of the cube. A zero population stock on 1 Jan and 31 Dec is not a value -> blank.
    geo = w["geo"].astype(str)
    empty = (geo.str.fullmatch(r"\d{4}") & ~geo.astype(str).isin([f"{c:04d}" for c in LEGACY])
             & (w["bil_pop_jan"] == 0) & (w["bil_pop_dec"] == 0))
    blank = set(zip(geo[empty].astype(int).astype(str), w.loc[empty, "Jahr"].astype(str)))
    w.loc[empty, cols] = float("nan")
    obs = to_obs(w, "geo", "Jahr", {c: c for c in cols}, SOURCE, legacy_hist=LEGACY, report=report)
    hit = (obs["level"] == "gemeinde") & pd.Series([(u, p) in blank for u, p in zip(obs["unit_id"], obs["period"])],
                                                   index=obs.index)
    obs.loc[hit, "value"], obs.loc[hit, "status"] = float("nan"), "not_published"
    obs.loc[hit, "note"] = ("BFS lists this municipality only from its creation (Thurgau reform 1990s / "
                            "Allmendingen 1993); its residents of earlier years are counted in other units")
    # 'Ohne Angabe' (from 2011, emigrants etc. without a known place of residence) is in the
    # Swiss total only -> level 'unallocated' so the national check can reconcile it
    return pd.concat([obs, unallocated_rows(w, G, "Jahr", cols, SOURCE, DB)], ignore_index=True)
