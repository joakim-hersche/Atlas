"""Federal population census 1970, 1980, 1990, 2000: main language, religion, household type and
household size by municipality (BFS PxWeb px-x-4001000000_123/_122/_102/_101).

All years are published on the 2000 municipality state; Gemeindebank reprojects the counts to the
reference state (decisions D3/D15: census values per municipality, labelled by census year).
Where splits are involved the values are population-weighted estimates (precision
boundary_estimate, set by to_reference()). Canton and national rows are kept as published.
Census population = residents at their economic place of residence (wirtschaftlicher Wohnsitz).
"""
from __future__ import annotations

import pandas as pd

from pipeline.harmonize.helpers import emit, infer_vintage, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.common import interim_path
from pipeline.sources.bfs_census_1970_2000.fetch import CUBES, cube, geo_table

SOURCE = "bfs_census_1970_2000"

# metric -> category codes summed (codes per cube metadata)
GROUPS = {
    "language": {
        "vz_lang_total": ["0"], "vz_lang_de": ["1"], "vz_lang_fr": ["2"], "vz_lang_it": ["3"],
        "vz_lang_rm": ["4"], "vz_lang_en": ["5"],
        "vz_lang_other": [str(i) for i in range(6, 14)],
    },
    "religion": {
        "vz_rel_total": ["0"], "vz_rel_reformed": ["1"], "vz_rel_catholic": ["6"],
        "vz_rel_orthodox": ["8"], "vz_rel_other_christian": ["2", "3", "4", "5", "7", "9"],
        "vz_rel_jewish": ["10"], "vz_rel_muslim": ["11"], "vz_rel_other": ["12"],
        "vz_rel_none": ["13"], "vz_rel_no_answer": ["14"],
    },
    "hh_type": {
        "vz_hh_total": ["0"], "vz_hh_one_person": ["1"], "vz_hh_couple_no_children": ["2"],
        "vz_hh_couple_children": ["3"], "vz_hh_single_parent": ["4"], "vz_hh_with_parents": ["5"],
        "vz_hh_non_family": ["6"], "vz_hh_collective": ["7"],
    },
    "hh_size": {
        "vz_hh_private": ["0"], "vz_hh_size_2": ["2"], "vz_hh_size_3": ["3"], "vz_hh_size_4": ["4"],
        "vz_hh_size_5plus": [str(i) for i in range(5, 11)],
    },
}


def _wide(kind: str) -> pd.DataFrame:
    df = cube(kind)
    out = None
    for metric, codes in GROUPS[kind].items():
        s = (df[df["cat"].isin(codes)].groupby(["geo", "year"])["value"].sum(min_count=len(codes))
             .rename(metric).reset_index())
        out = s if out is None else out.merge(s, on=["geo", "year"], how="outer")
    return out


def observations() -> pd.DataFrame:
    dbid = CUBES["language"][0]
    geo = geo_table(dbid)
    wide = None
    for kind in GROUPS:
        assert geo_table(CUBES[kind][0]).equals(geo), f"geography differs in {kind}"
        w = _wide(kind)
        wide = w if wide is None else wide.merge(w, on=["geo", "year"], how="outer")
    wide = wide.merge(geo, on="geo")
    metrics = [m for g in GROUPS.values() for m in g]
    mm = {m: m for m in metrics}
    parts = []

    mun = wide[wide["level"] == "gemeinde"].copy()
    mun["bfs_nr"] = mun["unit"].astype(int)
    vintage, jac = infer_vintage(mun["bfs_nr"].unique())
    if jac < 0.98:
        raise ValueError(f"cannot identify municipality state (best {vintage}, jaccard {jac:.3f})")
    ref, unm = to_reference(mun[["bfs_nr", "year", *metrics]], vintage, metrics, ["year"], rule="sum")
    if len(unm):
        raise ValueError(f"{len(unm)} unmapped municipality rows")
    parts.append(emit(ref, mm, "year", SOURCE))

    ct = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    abbr = dict(zip(ct["canton_id"].astype(int), ct["canton"]))
    k = wide[wide["level"] == "kanton"].copy()
    k["u"] = k["unit"].astype(int).map(abbr)
    parts.append(emit(k, mm, "year", SOURCE, level="kanton", unit_col="u", vintage=vintage,
                      precision="exact", provenance="native"))
    ch = wide[wide["level"] == "schweiz"].assign(u="CH")
    parts.append(emit(ch, mm, "year", SOURCE, level="schweiz", unit_col="u", vintage=vintage,
                      precision="exact", provenance="native"))
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
