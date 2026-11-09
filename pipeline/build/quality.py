"""Data plausibility sweep (decision D13, docs/validation_plan.md) -> docs/quality_report.md.

Checks per metric
  A  additivity: our aggregate of municipalities vs. the value the source publishes for districts,
     cantons and Switzerland ('native' rows). Differences explained by canton transfers on current
     boundaries (D16) are computed and labeled, not flagged.
  B  ranges: shares within 0–100, counts >= 0
  C  jumps: year-on-year changes of counts beyond thresholds, with known causes labeled
  D  coverage: municipalities with a value per metric and latest period; reasons for gaps
  E  cross-source: the same quantity from two sources (pairs listed in CROSS_CHECKS)
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE, ROOT, interim_path
from pipeline.harmonize.schema import load_metrics

TOL_REL = 0.005  # 0.5 % for sources with rounding/suppression
JUMP_REL, JUMP_MIN_ABS = 0.5, 200
# (metric_a, metric_b, description, relative tolerance) – same quantity from different sources
CROSS_CHECKS = [
    ("pop_total", "bilanz_stock_end", "STATPOP population vs. demographic balance stock at 31 Dec", 0.001),
    ("pop_total", "tax_population", "STATPOP population vs. population used in tax statistics", 0.05),
    ("gws_dwellings_total", "vac_dwelling_stock", "GWS dwellings vs. dwelling stock in the vacancy count", 0.02),
]


def transfer_effect(metric_rows: pd.DataFrame, source_state: dt.date, level: str) -> pd.Series:
    """Per canton or district: value of territory whose canton/district differs between
    source_state and the reference state (positive = gained on current boundaries)."""
    col = {"kanton": "canton", "bezirk": "district_nr"}[level]
    mv, _ = load_backbone()
    cw = pd.read_parquet(interim_path("backbone", f"crosswalk_{REFERENCE_DATE.isoformat()}.parquet"))
    then_v = versions_at(mv, source_state)[["hist_id", col]].rename(columns={col: "u_then"})
    now_v = versions_at(mv, REFERENCE_DATE)[["hist_id", col]].rename(columns={col: "u_now"})
    m = cw.merge(then_v, left_on="from_hist_id", right_on="hist_id").merge(
        now_v, left_on="to_hist_id", right_on="hist_id", suffixes=("", "_now"))
    m = m[m["u_then"].astype(str) != m["u_now"].astype(str)]
    if m.empty:
        return pd.Series(dtype=float)
    vals = metric_rows.set_index("unit_id")["value"]
    m["v"] = m["to_bfs_nr"].astype(str).map(vals) * m["weight"]
    gain = m.groupby(m["u_now"].astype(str))["v"].sum()
    loss = m.groupby(m["u_then"].astype(str))["v"].sum()
    return gain.sub(loss, fill_value=0)


def check_additivity(metrics_all: pd.DataFrame, obs: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    sums = set(meta.loc[(meta["aggregation"] == "sum") & (meta["kind"] == "base"), "id"])
    native = obs[(obs["provenance"] == "native") & obs["metric_id"].isin(sums) & (obs["status"] == "ok")]
    rows = []
    for (sid, lvl, metric), nat in native.groupby(["source_id", "level", "metric_id"]):
        agg = metrics_all[(metrics_all["level"] == lvl) & (metrics_all["metric_id"] == metric)]
        j = nat.merge(agg[["unit_id", "period", "value", "n_missing"]], on=["unit_id", "period"],
                      suffixes=("_pub", "_agg"))
        if j.empty:
            continue
        j["diff"] = j["value_agg"] - j["value_pub"]
        j["explained"] = 0.0
        if lvl in ("kanton", "bezirk"):
            state = dt.date.fromisoformat(nat["vintage"].iloc[0])
            gem = metrics_all[(metrics_all["level"] == "gemeinde") & (metrics_all["metric_id"] == metric)]
            for per, jj in j.groupby("period"):
                eff = transfer_effect(gem[gem["period"] == per], state, lvl)
                j.loc[jj.index, "explained"] = jj["unit_id"].astype(str).map(eff).fillna(0).values
        if lvl == "schweiz":
            # persons the source could not attribute to a municipality are in the national total
            un = obs[(obs["source_id"] == sid) & (obs["level"] == "unallocated") & (obs["metric_id"] == metric)]
            j["explained"] = -j["period"].map(un.set_index("period")["value"]).fillna(0).values
        j["residual"] = j["diff"] - j["explained"]
        j["rel"] = j["residual"].abs() / j["value_pub"].abs().replace(0, np.nan)
        bad = j[(j["residual"].abs() > 0.5) & ((j["rel"] > TOL_REL) | j["rel"].isna())]
        rows.append({"source_id": sid, "level": lvl, "metric_id": metric, "n_compared": len(j),
                     "n_exact": int((j["diff"].abs() <= 0.5).sum()),
                     "n_explained_canton_transfer": int(((j["diff"].abs() > 0.5) & (j["residual"].abs() <= 0.5)).sum()),
                     "n_within_tol": int(((j["residual"].abs() > 0.5) & (j["rel"] <= TOL_REL)).sum()),
                     "n_fail": len(bad), "max_rel_residual": float(j["rel"].max(skipna=True) or 0),
                     "worst": bad.reindex(bad["rel"].sort_values(ascending=False).index).head(3)[
                         ["unit_id", "period", "value_pub", "value_agg", "explained"]].to_dict("records")})
    return pd.DataFrame(rows)


def check_ranges(metrics_all: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    out = []
    pct = set(meta.loc[meta["unit"].astype(str).str.strip() == "%", "id"])
    counts = set(meta.loc[(meta["aggregation"] == "sum"), "id"])
    ok = metrics_all[metrics_all["status"] == "ok"]
    for m, g in ok.groupby("metric_id"):
        issues = []
        if m in pct and not m.startswith(("change", "pop_change")) and "change" not in m:
            n = int(((g["value"] < -1e-9) | (g["value"] > 100 + 1e-9)).sum())
            if n:
                issues.append(f"{n} values outside 0–100")
        if m in counts:
            n = int((g["value"] < -1e-9).sum())
            if n:
                issues.append(f"{n} negative counts")
        if issues:
            out.append({"metric_id": m, "issues": "; ".join(issues),
                        "examples": g[(g["value"] < 0) | ((m in pct) & (g["value"] > 100))].head(3)[
                            ["level", "unit_id", "period", "value"]].to_dict("records")})
    return pd.DataFrame(out)


def check_jumps(metrics_all: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    counts = set(meta.loc[(meta["aggregation"] == "sum") & (meta["kind"] == "base"), "id"])
    g = metrics_all[(metrics_all["level"] == "gemeinde") & metrics_all["metric_id"].isin(counts)
                    & (metrics_all["status"] == "ok") & metrics_all["period"].str.fullmatch(r"\d{4}")].copy()
    g["year"] = g["period"].astype(int)
    g = g.sort_values(["metric_id", "unit_id", "year"])
    g["prev"] = g.groupby(["metric_id", "unit_id"])["value"].shift()
    g["prev_year"] = g.groupby(["metric_id", "unit_id"])["year"].shift()
    g = g[g["year"] - g["prev_year"] == 1]
    g["abs"] = (g["value"] - g["prev"]).abs()
    g["rel"] = g["abs"] / g[["value", "prev"]].max(axis=1).replace(0, np.nan)
    flag = g[(g["rel"] > JUMP_REL) & (g["abs"] > JUMP_MIN_ABS)]
    out = []
    for m, f in flag.groupby("metric_id"):
        out.append({"metric_id": m, "n_flags": len(f), "n_series": g[g.metric_id == m]["unit_id"].nunique(),
                    "top": f.sort_values("abs", ascending=False).head(5)[
                        ["unit_id", "year", "prev", "value", "precision"]].to_dict("records")})
    return pd.DataFrame(out)


def check_coverage(metrics_all: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    gem = metrics_all[metrics_all["level"] == "gemeinde"]
    n_ref = 2110
    out = []
    for m, g in gem.groupby("metric_id"):
        latest = sorted(g["period"].unique())[-1]
        gl = g[g["period"] == latest]
        out.append({"metric_id": m, "periods": g["period"].nunique(), "first": sorted(g["period"].unique())[0],
                    "latest": latest, "n_ok": int((gl["status"] == "ok").sum()), "n_ref": n_ref,
                    "status_counts": gl["status"].value_counts().to_dict()})
    return pd.DataFrame(out)


def check_cross_source(metrics_all: pd.DataFrame) -> pd.DataFrame:
    gem = metrics_all[(metrics_all["level"] == "gemeinde") & (metrics_all["status"] == "ok")]
    out = []
    for a, b, desc, tol in CROSS_CHECKS:
        A, B = gem[gem["metric_id"] == a], gem[gem["metric_id"] == b]
        if A.empty or B.empty:
            out.append({"check": desc, "result": "not run (metric missing)"})
            continue
        j = A.merge(B, on=["unit_id", "period"], suffixes=("_a", "_b"))
        j["rel"] = (j["value_a"] - j["value_b"]).abs() / j["value_a"].abs().replace(0, np.nan)
        out.append({"check": desc, "result": f"{int((j['rel'] <= tol).sum())} of {len(j)} within {tol:.1%}",
                    "worst": j.sort_values("rel", ascending=False).head(3)[["unit_id", "period", "value_a", "value_b"]].to_dict("records")})
    return pd.DataFrame(out)


def run() -> str:
    meta = load_metrics().drop_duplicates("id")
    allm = pd.read_parquet(interim_path("metrics_all.parquet"))
    obs = pd.read_parquet(interim_path("observation.parquet"))
    A = check_additivity(allm, obs, meta)
    B = check_ranges(allm, meta)
    C = check_jumps(allm, meta)
    D = check_coverage(allm, meta)
    E = check_cross_source(allm)
    L = ["# Data quality report", "",
         f"Generated {dt.datetime.now().isoformat(timespec='minutes')} · reference state {REFERENCE_DATE} · "
         "regenerate with `make quality`. Plan: [`validation_plan.md`](validation_plan.md).", "",
         f"Metrics: {meta['id'].nunique()} defined ({(meta['kind'] == 'base').sum()} base, "
         f"{(meta['kind'] == 'derived').sum()} derived) · rows: {len(allm):,}", ""]
    L += ["## A. Additivity — municipalities vs. published district/canton/national values", ""]
    if len(A):
        L += ["| Source | Level | Metric | Compared | Exact | Explained (transfers / unallocated) | Within 0.5% | Fail | Max rel. residual |",
              "|---|---|---|---|---|---|---|---|---|"]
        L += [f"| {r.source_id} | {r.level} | {r.metric_id} | {r.n_compared} | {r.n_exact} | {r.n_explained_canton_transfer} | "
              f"{r.n_within_tol} | {'**' + str(r.n_fail) + '**' if r.n_fail else 0} | {r.max_rel_residual:.3%} |"
              for r in A.sort_values(["n_fail", "source_id"], ascending=[False, True]).itertuples()]
        fails = A[A["n_fail"] > 0]
        if len(fails):
            L += ["", "Worst unexplained differences:", ""]
            for r in fails.itertuples():
                L += [f"- {r.source_id} / {r.level} / {r.metric_id}: {r.worst}"]
    else:
        L += ["No published higher-level values available yet."]
    L += ["", "## B. Ranges", ""]
    L += ([f"- **{r.metric_id}**: {r.issues} — e.g. {r.examples}" for r in B.itertuples()] or ["All shares within 0–100, no negative counts."])
    L += ["", f"## C. Year-on-year jumps (> {JUMP_REL:.0%} and > {JUMP_MIN_ABS} units)", ""]
    if len(C):
        L += ["| Metric | Flags | Series | Largest |", "|---|---|---|---|"]
        L += [f"| {r.metric_id} | {r.n_flags} | {r.n_series} | {r.top[:2]} |" for r in C.sort_values("n_flags", ascending=False).itertuples()]
    else:
        L += ["No jumps above the thresholds."]
    L += ["", "## D. Coverage (municipality level, latest period)", "",
          "| Metric | Periods | First | Latest | With value | Gap reasons |", "|---|---|---|---|---|---|"]
    L += [f"| {r.metric_id} | {r.periods} | {r.first} | {r.latest} | {r.n_ok} / {r.n_ref} | "
          f"{ {k: v for k, v in r.status_counts.items() if k != 'ok'} or '–'} |" for r in D.sort_values("metric_id").itertuples()]
    L += ["", "## E. Cross-source consistency", ""]
    L += [f"- {r.check}: {r.result}" + (f" — worst: {r.worst}" if isinstance(getattr(r, 'worst', None), list) else "")
          for r in E.itertuples()]
    path = ROOT / "docs" / "quality_report.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    print(run())
