"""Reproject municipality data from one boundary vintage to another.

    to_vintage(df, source_vintage, target_vintage, rule, ...)

df        long table with at least: a municipality key column and a value column.
          Key is either `hist_id` (preferred, from sources with GDEHISTID) or `bfs_nr`
          (resolved to versions valid on `source_vintage`).
source_vintage
          date of the municipality state the data uses (e.g. 2023-01-01), or the string
          "per_row" when df has a `vintage` column (one state per row, e.g. per-year files).
target_vintage
          date of the target state (default: reference date, decision D8).
rule      'sum'                       counts: values distributed by crosswalk weights and summed
          'weighted_mean:<weight_col>' rates/means: weighted by the column (e.g. population),
                                       which must itself be a count in df
          'not_aggregatable'          medians, indices: kept only where the mapping is 1:1
                                       (single source, single target, weight 1); else NaN

Returns a DataFrame keyed by target hist_id and bfs_nr, with the group columns preserved, plus
`n_sources` and `min_weight_source` for traceability. Unmapped source rows are returned separately
in the attribute `.attrs["unmapped"]` so the quality report can log them.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import build_crosswalk, load_backbone, versions_at
from pipeline.common import REFERENCE_DATE, interim_path

_CW_CACHE: dict[pd.Timestamp, pd.DataFrame] = {}


def crosswalk(target_vintage: dt.date = REFERENCE_DATE) -> pd.DataFrame:
    key = pd.Timestamp(target_vintage)
    if key not in _CW_CACHE:
        p = interim_path("backbone", f"crosswalk_{key.date().isoformat()}.parquet")
        if p.exists():
            _CW_CACHE[key] = pd.read_parquet(p)
        else:
            mv, pair = load_backbone()
            sw = pd.read_parquet(interim_path("backbone", "split_weights.parquet"))
            _CW_CACHE[key] = build_crosswalk(mv, pair, sw, target_vintage)
    return _CW_CACHE[key]


def _attach_hist_id(df: pd.DataFrame, source_vintage) -> pd.DataFrame:
    if "hist_id" in df.columns:
        return df
    mv, _ = load_backbone()
    if isinstance(source_vintage, str) and source_vintage == "per_row":
        parts = []
        for v, g in df.groupby("vintage"):
            ver = versions_at(mv, pd.Timestamp(v).date(), municipalities_only=False)
            lk = ver.drop_duplicates("bfs_nr").set_index("bfs_nr")["hist_id"]
            parts.append(g.assign(hist_id=g["bfs_nr"].map(lk)))
        return pd.concat(parts)
    ver = versions_at(mv, pd.Timestamp(source_vintage).date(), municipalities_only=False)
    lk = ver.drop_duplicates("bfs_nr").set_index("bfs_nr")["hist_id"]
    return df.assign(hist_id=df["bfs_nr"].map(lk))


def to_vintage(df: pd.DataFrame, source_vintage, target_vintage: dt.date = REFERENCE_DATE,
               rule: str = "sum", value_col: str = "value",
               group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = list(group_cols or [])
    d = _attach_hist_id(df.copy(), source_vintage)
    unmapped = d[d["hist_id"].isna()]
    d = d[d["hist_id"].notna()].astype({"hist_id": "int64"})
    cw = crosswalk(target_vintage)[["from_hist_id", "to_hist_id", "to_bfs_nr", "weight", "weight_source"]]
    m = d.merge(cw, left_on="hist_id", right_on="from_hist_id", how="left")
    no_target = m[m["to_hist_id"].isna()]
    m = m[m["to_hist_id"].notna()]
    keys = ["to_hist_id", "to_bfs_nr", *group_cols]

    if rule == "sum":
        m["_v"] = m[value_col] * m["weight"]
        out = m.groupby(keys, dropna=False).agg(value=("_v", lambda s: s.sum(min_count=1)),
                                                n_sources=("hist_id", "nunique"),
                                                min_weight=("weight", "min"))
    elif rule.startswith("weighted_mean:"):
        wcol = rule.split(":", 1)[1]
        m["_w"] = m[wcol] * m["weight"]
        m["_vw"] = m[value_col] * m["_w"]
        g = m.groupby(keys, dropna=False)
        out = pd.DataFrame({
            "value": g["_vw"].sum(min_count=1) / g["_w"].sum(min_count=1),
            "n_sources": g["hist_id"].nunique(),
            "min_weight": g["weight"].min(),
        })
    elif rule == "not_aggregatable":
        g = m.groupby(keys, dropna=False)
        exact = (g["hist_id"].nunique() == 1) & (g["weight"].min() >= 1 - 1e-9) & (g.size() == 1)
        out = pd.DataFrame({"value": g[value_col].first().where(exact, np.nan),
                            "n_sources": g["hist_id"].nunique(),
                            "min_weight": g["weight"].min()})
        # a source split across several targets is also not exact for the targets
        split_src = m.groupby("hist_id")["to_hist_id"].nunique()
        split_src = set(split_src[split_src > 1].index)
        bad = m[m["hist_id"].isin(split_src)].groupby(keys).size().index
        out.loc[out.index.isin(bad), "value"] = np.nan
    else:
        raise ValueError(f"unknown rule: {rule}")
    out = out.reset_index().rename(columns={"to_hist_id": "hist_id", "to_bfs_nr": "bfs_nr"})
    out.attrs["unmapped"] = pd.concat([unmapped, no_target.drop(columns=cw.columns, errors="ignore")])
    return out
