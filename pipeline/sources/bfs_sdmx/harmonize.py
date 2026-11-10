"""SDMX long tables -> wide series -> observation rows (shared by connectors reading BFS SDMX).

Municipality rows are on one snapshot state of the flow's geo codelist (SNAP_2025 / SNAP_2026,
history re-mapped by BFS). The state is inferred from the BFS numbers present
(pipeline.harmonize.helpers.infer_vintage), then brought to the reference state with
to_reference(); provenance 'source_current_state' (decision D14) where the remaining step is
merger-only. Cantons, districts and Switzerland are kept as native rows.

Gaps: OBS_STATUS Q (suppressed for confidentiality) -> status 'suppressed', M -> 'not_applicable',
L -> 'not_published', any other empty value -> 'no_data'. A municipality at the reference state
whose predecessors include a gap gets the gap (never a partial sum).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.harmonize.helpers import emit, infer_vintage, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_sdmx.fetch import geo_level, native_unit

STATUS_OF = {"Q": "suppressed", "M": "not_applicable", "L": "not_published"}
GAP_RANK = ["no_data", "not_published", "not_applicable", "suppressed"]  # strongest last
NOTE_OF = {"suppressed": "suppressed by BFS (confidentiality)",
           "not_applicable": "BFS: value cannot exist",
           "not_published": "BFS: value exists but is not disseminated"}


def source_state(codes, min_jaccard: float = 0.98):
    gem = sorted({int(c) for c in codes if geo_level(c) == "gemeinde"})
    vintage, jac = infer_vintage(gem)
    if jac < min_jaccard:
        raise ValueError(f"cannot identify municipality state (best {vintage}, jaccard {jac:.3f})")
    return vintage, jac


def _row_status(df: pd.DataFrame) -> pd.Series:
    st = df["OBS_STATUS"].map(STATUS_OF).fillna("no_data")
    return st.where(df["value"].isna(), "ok")


def pivot(df: pd.DataFrame, geo_col: str, series: dict[str, dict],
          period_col: str = "TIME_PERIOD", absent_is_zero: bool = False) -> pd.DataFrame:
    """Pick series out of a long SDMX frame.

    series: {column: {dimension: code or [codes]}}; a list of codes is summed and is a value only
    if every component is a value. Adds '<column>__status' columns.
    absent_is_zero: for sparse flows that omit zero cells of a complete register (MFZ/IVS): a
    component without a row counts as 0, over the full grid of geo codes x periods in df.
    """
    df = df.assign(_st=_row_status(df))
    if absent_is_zero:
        keys = pd.MultiIndex.from_product([df[geo_col].unique(), df[period_col].unique()],
                                          names=[geo_col, period_col]).to_frame(index=False)
    else:
        keys = df[[geo_col, period_col]].drop_duplicates()
    out = keys.copy()
    for name, filt in series.items():
        m = pd.Series(True, index=df.index)
        n_codes = 1
        for dim, code in filt.items():
            if isinstance(code, (list, tuple, set)):
                m &= df[dim].isin(list(code))
                n_codes *= len(code)
            else:
                m &= df[dim] == code
        sub = df.loc[m]
        g = sub.groupby([geo_col, period_col])
        val = g["value"].sum(min_count=1)
        n_ok = g["value"].count()
        n_rows = g.size()
        gap = g["_st"].agg(lambda s: max((x for x in s if x != "ok"), key=GAP_RANK.index, default="no_data"))
        if absent_is_zero:  # rows present but empty are gaps; missing rows are zeros
            val = val.where(n_ok == n_rows)
        else:
            val = val.where(n_ok == n_codes)
        st = pd.Series(np.where(val.notna(), "ok", gap.reindex(val.index)), index=val.index)
        s = pd.DataFrame({name: val, f"{name}__status": st}).reset_index()
        out = out.merge(s, on=[geo_col, period_col], how="left")
        if absent_is_zero:
            miss = out[name].isna() & out[f"{name}__status"].isna()
            out.loc[miss, name] = 0.0
            out.loc[miss, f"{name}__status"] = "ok"
        out[f"{name}__status"] = out[f"{name}__status"].fillna("no_data")
    return out


def to_observations(wide: pd.DataFrame, geo_col: str, period_col: str, metric_map: dict[str, str],
                    source_id: str, rule_by_col: dict[str, str] | None = None, vintage=None,
                    levels=("kanton", "bezirk", "schweiz"), precision: str = "exact",
                    notes: dict[str, str] | None = None) -> tuple[pd.DataFrame, dict]:
    """wide: one row per geo code x period with the metric_map columns (and optional
    '<col>__status' columns from pivot()). Returns (observations, info)."""
    wide = wide.copy()
    for c in metric_map:
        if f"{c}__status" not in wide:
            wide[f"{c}__status"] = np.where(wide[c].notna(), "ok", "no_data")
        wide[f"{c}__status"] = wide[f"{c}__status"].fillna("no_data")
    wide["_level"] = wide[geo_col].map(geo_level)
    mun = wide[wide["_level"] == "gemeinde"].copy()
    mun["bfs_nr"] = mun[geo_col].astype(int)
    jac = None
    if vintage is None:
        vintage, jac = source_state(mun["bfs_nr"].unique())
    rules = rule_by_col or {}
    notes = notes or {}
    parts, unmapped = [], []
    for c, metric in metric_map.items():
        st = mun[f"{c}__status"]
        tmp = mun[["bfs_nr", period_col, c]].copy()
        for gap in GAP_RANK:
            tmp[f"_g_{gap}"] = (st == gap).astype(float)
        gap_cols = [f"_g_{g}" for g in GAP_RANK]
        ref, unm = to_reference(tmp, vintage, [c, *gap_cols], [period_col], rule="sum",
                                bfs_already_current=True) if rules.get(c, "sum") == "sum" else (None, None)
        if ref is None:
            ref, unm = to_reference(tmp, vintage, [c], [period_col], rule=rules[c], bfs_already_current=True)
            g2, _ = to_reference(tmp, vintage, gap_cols, [period_col], rule="sum", bfs_already_current=True)
            ref = ref.merge(g2[["bfs_nr", period_col, *gap_cols]], on=["bfs_nr", period_col], how="left")
        status = pd.Series("ok", index=ref.index)
        for gap in GAP_RANK:
            status = status.where(~(ref[f"_g_{gap}"] > 0), gap)
        ref.loc[status != "ok", c] = np.nan
        status = status.where(ref[c].notna() | (status != "ok"), "no_data")
        if precision != "exact":
            ref["precision"] = ref["precision"].where(ref["precision"] != "exact", precision)
        unmapped.append(unm)
        e = emit(ref, {c: metric}, period_col, source_id)
        e["status"] = status.values
        e["note"] = [NOTE_OF.get(s, notes.get(c)) if s != "ok" else notes.get(c) for s in status]
        parts.append(e)
    for level in levels:
        sub = wide[wide["_level"] == level].copy()
        if sub.empty:
            continue
        sub["unit"] = [native_unit(x, level) for x in sub[geo_col]]
        sub["precision"], sub["provenance"] = precision, "native"
        for c, metric in metric_map.items():
            e = emit(sub, {c: metric}, period_col, source_id, level=level, unit_col="unit", vintage=vintage)
            e["status"] = sub[f"{c}__status"].values
            e["note"] = [NOTE_OF.get(s, notes.get(c)) if s != "ok" else notes.get(c) for s in e["status"]]
            parts.append(e)
    obs = pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
    obs.loc[obs["status"] != "ok", "value"] = np.nan
    # municipality rows only for municipalities of the reference state (the crosswalk also carries
    # non-municipal units such as condominium areas / Kommunanzen, which stay in canton totals)
    ref_units = _reference_units()
    is_gem = obs["level"] == "gemeinde"
    extra = obs.loc[is_gem & ~obs["unit_id"].isin(ref_units), "unit_id"].unique()
    obs = obs[~(is_gem & obs["unit_id"].isin(extra))]
    # drop 'no_data' rows that only say a series does not exist: all native-level ones, and
    # municipality ones for metric x period combinations without any value
    nd = obs["status"] == "no_data"
    gem_ok = obs[(obs["level"] == "gemeinde") & (obs["status"] != "no_data")][["metric_id", "period"]].drop_duplicates()
    key = pd.MultiIndex.from_frame(obs[["metric_id", "period"]])
    has = key.isin(pd.MultiIndex.from_frame(gem_ok))
    obs = obs[~(nd & ((obs["level"] != "gemeinde") | ~has))].reset_index(drop=True)
    return obs, {"vintage": vintage, "jaccard": jac, "unmapped": pd.concat(unmapped),
                 "non_municipal_units": list(extra)}


def _reference_units() -> set[str]:
    from pipeline.backbone.crosswalk import load_backbone, versions_at
    from pipeline.common import REFERENCE_DATE
    mv, _ = load_backbone()
    return set(versions_at(mv, REFERENCE_DATE)["bfs_nr"].astype(int).astype(str))
