"""Turn PxWeb cubes on BFS institutional geography into observations.

Municipality rows are brought to the reference state (the cube's own state is inferred from its
municipality codes). Canton, district and national rows are kept as published ('native') so the
plausibility sweep can compare our aggregates with them.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit, infer_vintage, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_pxweb.fetch import geo_level_of_code

GEO = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"


def wide_by_geo(df: pd.DataFrame, geo_col: str, period_col: str, series: dict[str, dict]) -> pd.DataFrame:
    """Pick series out of a long PxWeb frame.

    series: {column_name: {variable_code: category_code, ...}} — each series is the value where
    the listed variables take the listed categories.
    """
    out = None
    for name, filt in series.items():
        m = pd.Series(True, index=df.index)
        for var, cat in filt.items():
            m &= df[var] == cat
        s = df.loc[m, [geo_col, period_col, "value"]].rename(columns={"value": name})
        out = s if out is None else out.merge(s, on=[geo_col, period_col], how="outer")
    return out


def to_observations(wide: pd.DataFrame, geo_col: str, period_col: str, metric_map: dict[str, str],
                    source_id: str, rule_by_col: dict[str, str] | None = None,
                    published_on_current_state: bool = True) -> pd.DataFrame:
    """wide: one row per geo code × period, value columns named as in metric_map."""
    wide = wide.copy()
    wide["_level"] = wide[geo_col].map(geo_level_of_code)
    parts = []

    # municipalities -> reference state
    mun = wide[wide["_level"] == "gemeinde"].copy()
    mun["bfs_nr"] = mun[geo_col].astype(int)
    vintage, jac = infer_vintage(mun["bfs_nr"].unique())
    if jac < 0.98:
        raise ValueError(f"cannot identify municipality state (best {vintage}, jaccard {jac:.3f})")
    cols = list(metric_map)
    rules = rule_by_col or {}
    for rule in sorted(set(rules.get(c, "sum") for c in cols)):
        cc = [c for c in cols if rules.get(c, "sum") == rule]
        ref, unm = to_reference(mun[["bfs_nr", period_col, *cc]], vintage, cc, [period_col], rule=rule,
                                bfs_already_current=published_on_current_state)
        parts.append(emit(ref, {c: metric_map[c] for c in cc}, period_col, source_id))

    # published higher levels (kept as native for validation and for canton/district views)
    mv, _ = load_backbone()
    for level in ("kanton", "bezirk", "schweiz", "other"):
        sub = wide[wide["_level"] == level].copy()
        if sub.empty:
            continue
        if level == "other":
            # e.g. 'Ohne Angabe': persons BFS cannot attribute to a municipality. Kept so national
            # totals can be reconciled (level 'unallocated').
            sub["unit"] = "unallocated"
            sub["precision"], sub["provenance"] = "exact", "native"
            parts.append(emit(sub, metric_map, period_col, source_id, level="unallocated",
                              unit_col="unit", vintage=vintage))
            continue
        if level == "bezirk":
            sub["unit"] = sub[geo_col].str[-4:].astype(int).astype(str)  # 000101 -> 101
        elif level == "schweiz":
            sub["unit"] = "CH"
        else:
            sub["unit"] = sub[geo_col]
        sub["precision"], sub["provenance"] = "exact", "native"
        parts.append(emit(sub, metric_map, period_col, source_id, level=level, unit_col="unit",
                          vintage=vintage))
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
