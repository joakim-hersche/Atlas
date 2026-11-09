"""Compute derived metrics and aggregate to every spatial level (brief 4.2 / 4.3).

Input:  data/interim/observation.parquet (from pipeline.harmonize.run) and all metrics.yaml
Output: data/interim/metrics_all.parquet with columns
        unit_id, level, metric_id, period, value, status, precision, provenance, n_units, n_missing

Rules
- Base metrics with aggregation 'sum' are summed from municipalities to every level. A unit gets a
  value only if all its municipalities have one (else status 'no_data' with n_missing > 0).
- 'weighted_mean:<w>' uses metric <w> (same period, else the nearest earlier period) as weight.
- 'not_aggregatable' stays at its native level; higher levels get status 'not_applicable'.
- Derived 'ratio:<a>[+<b>...]/<c>[+...][*<factor>]' and 'change:<metric>:<years>' are computed at every
  level from that level's base values, so ratios are re-computed, never averaged.
- Rows the sources publish at higher levels ('native') are not used for aggregation; they are kept
  for the plausibility sweep (pipeline.build.quality).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from pipeline.backbone.levels import LEVEL_COLUMNS, membership
from pipeline.common import interim_path
from pipeline.harmonize.schema import load_metrics

AGG_LEVELS = ["bezirk", "kanton", *LEVEL_COLUMNS, "schweiz"]
PRECISION_ORDER = ["exact", "survey", "modelled", "boundary_estimate"]
RATIO = re.compile(r"^ratio:(?P<num>[^/]+)/(?P<den>[^*]+)(?:\*(?P<f>[\d.]+))?$")
CHANGE = re.compile(r"^change:(?P<m>[a-z0-9_]+):(?P<n>\d+)$")


def _worst(series: pd.Series) -> str:
    vals = [v for v in series.dropna().unique() if v in PRECISION_ORDER]
    return max(vals, key=PRECISION_ORDER.index) if vals else "exact"


def aggregate_levels(gem: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """gem: gemeinde observations (unit_id = BFS nr) of base metrics."""
    mem = membership()
    mem["schweiz"] = "CH"
    mem["unit_id"] = mem["bfs_nr"].astype(str)
    n_units = {lvl: mem.groupby(lvl).size() for lvl in AGG_LEVELS}
    aggs = meta.set_index("id")["aggregation"].to_dict()
    out = []
    sums = [m for m, a in aggs.items() if a == "sum"]
    wmeans = {m: a.split(":", 1)[1] for m, a in aggs.items() if str(a).startswith("weighted_mean:")}
    g = gem.merge(mem[["unit_id", *AGG_LEVELS]], on="unit_id", how="inner")
    for lvl in AGG_LEVELS:
        # sums
        s = g[g["metric_id"].isin(sums)]
        grp = s.groupby([lvl, "metric_id", "period"])
        r = grp.agg(value=("value", lambda v: v.sum(min_count=1)),
                    n_with=("value", "count"), precision=("precision", _worst)).reset_index()
        r["n_units"] = r[lvl].map(n_units[lvl])
        r["n_missing"] = r["n_units"] - r["n_with"]
        r.loc[r["n_missing"] > 0, "value"] = np.nan
        # weighted means
        parts = [r]
        for m, w in wmeans.items():
            vm = g[g["metric_id"] == m][[lvl, "unit_id", "period", "value", "precision"]]
            wm = g[g["metric_id"] == w][["unit_id", "period", "value"]].rename(columns={"value": "w"})
            if vm.empty or wm.empty:
                continue
            j = vm.merge(wm, on=["unit_id", "period"], how="left")
            if j["w"].isna().all():  # weight not available for these periods: nearest earlier period
                latest_w = wm.sort_values("period").groupby("unit_id")["w"].last()
                j["w"] = j["unit_id"].map(latest_w)
            j["vw"] = j["value"] * j["w"]
            jj = j.groupby([lvl, "period"]).agg(vw=("vw", "sum"), w=("w", lambda x: x[j.loc[x.index, "value"].notna()].sum()),
                                                n_with=("value", "count"), precision=("precision", _worst)).reset_index()
            jj["value"] = jj["vw"] / jj["w"].replace(0, np.nan)
            jj["metric_id"] = m
            jj["n_units"] = jj[lvl].map(n_units[lvl])
            jj["n_missing"] = jj["n_units"] - jj["n_with"]
            parts.append(jj.drop(columns=["vw", "w"]))
        r = pd.concat(parts, ignore_index=True).rename(columns={lvl: "unit_id"})
        r["level"] = lvl
        r["status"] = np.where(r["value"].notna(), "ok", "no_data")
        r["provenance"] = "aggregated"
        out.append(r.drop(columns=["n_with"]))
    return pd.concat(out, ignore_index=True)


def _terms(expr: str) -> list[str]:
    return [t.strip() for t in expr.split("+") if t.strip()]


def derive(df: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Compute derived metrics for every level present in df (long format)."""
    derived = meta[meta["kind"] == "derived"]
    if derived.empty:
        return df.iloc[0:0]
    wide = df.pivot_table(index=["level", "unit_id", "period"], columns="metric_id", values="value",
                          aggfunc="first")
    prec = df.groupby(["level", "unit_id", "period"])["precision"].agg(_worst)
    out = []
    for m in derived.to_dict("records"):
        agg = m["aggregation"]
        if (r := RATIO.match(agg)):
            num, den = _terms(r["num"]), _terms(r["den"])
            if not set(num + den) <= set(wide.columns):
                continue
            f = float(r["f"]) if r["f"] else 1.0
            val = wide[num].sum(axis=1, min_count=len(num)) / wide[den].sum(axis=1, min_count=len(den)).replace(0, np.nan) * f
        elif (c := CHANGE.match(agg)):
            base, n = c["m"], int(c["n"])
            if base not in wide.columns:
                continue
            s = wide[base].reset_index()
            s = s[s["period"].str.fullmatch(r"\d{4}")]
            s["prev"] = (s["period"].astype(int) - n).astype(str)
            prev = s.set_index(["level", "unit_id", "period"])[base]
            s["v0"] = [prev.get((l, u, p), np.nan) for l, u, p in zip(s["level"], s["unit_id"], s["prev"])]
            val = pd.Series(((s[base] / s["v0"]) - 1).values * 100,
                            index=pd.MultiIndex.from_frame(s[["level", "unit_id", "period"]]))
        else:
            continue
        val = val.replace([np.inf, -np.inf], np.nan).dropna()
        d = val.rename("value").reset_index()
        d["metric_id"] = m["id"]
        d["precision"] = d.set_index(["level", "unit_id", "period"]).index.map(prec).fillna("exact")
        d["status"] = "ok"
        d["provenance"] = "derived"
        out.append(d)
    return pd.concat(out, ignore_index=True) if out else df.iloc[0:0]


def run() -> str:
    obs = pd.read_parquet(interim_path("observation.parquet"))
    meta = load_metrics()
    meta = meta.drop_duplicates("id")
    base_ids = set(meta.loc[meta["kind"] == "base", "id"])
    # municipality rows, plus rows natively published only above municipality level (e.g. district
    # survey values, canton-only metrics) which are passed through as they are
    gem = obs[(obs["level"] == "gemeinde") & obs["metric_id"].isin(base_ids)].copy()
    native_only = meta[(meta["kind"] == "base") & (meta["native_level"] != "gemeinde")]["id"]
    native = obs[obs["metric_id"].isin(native_only) & (obs["level"] != "gemeinde")].copy()
    agg = aggregate_levels(gem, meta[meta["kind"] == "base"])
    gem["n_units"], gem["n_missing"] = 1, (gem["status"] != "ok").astype(int)
    base_all = pd.concat([gem, agg, native], ignore_index=True)
    der = derive(base_all, meta)
    cols = ["unit_id", "level", "metric_id", "period", "value", "status", "precision", "provenance",
            "n_units", "n_missing", "note"]
    allm = pd.concat([base_all, der], ignore_index=True).reindex(columns=cols)
    p = interim_path("metrics_all.parquet")
    allm.to_parquet(p, index=False)
    return str(p)


if __name__ == "__main__":
    print(run())
