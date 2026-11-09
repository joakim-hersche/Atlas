"""Helpers for connectors: detect the municipality state of a source, bring municipality data to
the reference state with provenance and precision, and emit observation rows.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.backbone.vintage import to_vintage
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.schema import OBS_COLUMNS


@lru_cache(maxsize=1)
def _candidate_dates() -> list[dt.date]:
    mv, pair = load_backbone()
    dates = set(pd.to_datetime(pair["date"]).dt.date)
    # a state is valid from a mutation date until the next; also test the day before each
    out = set()
    for d in dates:
        out.add(d)
        out.add(d - dt.timedelta(days=1))
    return sorted(x for x in out if x >= dt.date(1960, 1, 1))


def infer_vintage(bfs_numbers, min_year: int | None = None) -> tuple[dt.date, float]:
    """Municipality state (date) whose set of BFS numbers best matches the given set.

    Returns (date, jaccard). A jaccard of 1.0 means an exact match. Pseudo-codes (>= 9000) and
    non-municipal codes are ignored.
    """
    mv, _ = load_backbone()
    s = {int(b) for b in bfs_numbers if b is not None and not pd.isna(b) and 0 < int(b) < 9000}
    best, best_j = None, -1.0
    for d in _candidate_dates():
        if min_year and d.year < min_year:
            continue
        cur = set(versions_at(mv, d)["bfs_nr"].astype(int))
        j = len(s & cur) / len(s | cur)
        if j > best_j or (j == best_j and d > best):
            best, best_j = d, j
    return best, best_j


def to_reference(df: pd.DataFrame, source_vintage: dt.date | None, value_cols: list[str],
                 group_cols: list[str], rule: str = "sum", bfs_already_current: bool = False):
    """Reproject municipality rows (bfs_nr or hist_id keyed) to the reference state.

    Returns (wide DataFrame keyed by bfs_nr + group_cols with value_cols, provenance per row,
    unmapped rows). provenance is 'aggregated_mergers' where every contributing weight is 1,
    else 'reprojected_weighted'. If the source is BFS-published on the current state and the
    crosswalk to the reference is merger-only, 'source_current_state' is used.
    """
    out, unm_all = None, []
    prov = None
    extra = [rule.split(":", 1)[1]] if rule.startswith("weighted_mean:") else []
    for col in value_cols:
        r, unm = to_vintage(df[[*([c for c in ("bfs_nr", "hist_id") if c in df]), *group_cols, col,
                                *[e for e in extra if e != col]]]
                            .rename(columns={col: "value"}),
                            source_vintage=source_vintage, rule=rule, group_cols=group_cols,
                            return_unmapped=True)
        unm_all.append(unm)
        if prov is None:
            prov = r[["bfs_nr", *group_cols, "min_weight"]]
        r = r[["bfs_nr", *group_cols, "value"]].rename(columns={"value": col})
        out = r if out is None else out.merge(r, on=["bfs_nr", *group_cols], how="outer")
    out = out.merge(prov, on=["bfs_nr", *group_cols], how="left")
    exact = out["min_weight"] >= 1 - 1e-9
    if bfs_already_current:
        out["provenance"] = np.where(exact, "source_current_state", "reprojected_weighted")
    else:
        out["provenance"] = np.where(exact, "aggregated_mergers", "reprojected_weighted")
    out["precision"] = np.where(exact, "exact", "boundary_estimate")
    return out.drop(columns="min_weight"), pd.concat(unm_all) if unm_all else pd.DataFrame()


def emit(wide: pd.DataFrame, metric_map: dict[str, str], period_col: str, source_id: str,
         level: str = "gemeinde", unit_col: str = "bfs_nr", vintage: dt.date = REFERENCE_DATE,
         precision: str | None = None, provenance: str | None = None) -> pd.DataFrame:
    """Wide table (one column per value) -> observation rows. metric_map: column -> metric_id."""
    rows = []
    for col, metric in metric_map.items():
        d = pd.DataFrame({
            "unit_id": wide[unit_col].astype(str),
            "level": level,
            "vintage": vintage.isoformat(),
            "metric_id": metric,
            "period": wide[period_col].astype(str),
            "value": pd.to_numeric(wide[col], errors="coerce").astype(float),
            "precision": wide["precision"] if precision is None and "precision" in wide else (precision or "exact"),
            "provenance": wide["provenance"] if provenance is None and "provenance" in wide else (provenance or "native"),
            "source_id": source_id,
        })
        d["status"] = np.where(d["value"].notna(), "ok", "no_data")
        d["note"] = None
        rows.append(d)
    return pd.concat(rows, ignore_index=True)[OBS_COLUMNS]
