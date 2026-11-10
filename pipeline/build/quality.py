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

import duckdb

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


class Store:
    """Lazy access to metrics_all.parquet via DuckDB (the full table does not fit in memory)."""

    def __init__(self, path):
        self.path = str(path)
        self.con = duckdb.connect()
        self.con.execute("SET memory_limit='3GB'")

    def rows(self, level: str, metric: str, period: str | None = None) -> pd.DataFrame:
        cond = f" AND period = '{period}'" if period else ""
        return self.con.execute(f"SELECT * FROM read_parquet('{self.path}') WHERE level = ? AND metric_id = ?{cond}",
                                [level, metric]).df()

    def sql(self, body: str) -> pd.DataFrame:
        return self.con.execute(body.replace("{M}", f"read_parquet('{self.path}')")).df()


def check_additivity(metrics_all: "Store", obs: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    sums = set(meta.loc[(meta["aggregation"] == "sum") & (meta["kind"] == "base"), "id"])
    native = obs[(obs["provenance"] == "native") & obs["metric_id"].isin(sums) & (obs["status"] == "ok")]
    rows = []
    for (sid, lvl, metric), nat in native.groupby(["source_id", "level", "metric_id"]):
        agg = metrics_all.rows(lvl, metric)
        j = nat.merge(agg[["unit_id", "period", "value", "n_missing"]], on=["unit_id", "period"],
                      suffixes=("_pub", "_agg"))
        if j.empty:
            continue
        j["diff"] = j["value_agg"] - j["value_pub"]
        j["explained"] = 0.0
        if lvl in ("kanton", "bezirk"):
            state = dt.date.fromisoformat(nat["vintage"].iloc[0])
            gem = metrics_all.rows("gemeinde", metric)
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


def check_ranges(metrics_all: "Store", meta: pd.DataFrame) -> pd.DataFrame:
    pct = meta.loc[(meta["unit"].astype(str).str.strip() == "%") & ~meta["id"].str.contains("change"), "id"].tolist()
    counts = meta.loc[(meta["aggregation"] == "sum"), "id"].tolist()
    lst = lambda ids: ", ".join("'" + i + "'" for i in ids) or "''"
    r = metrics_all.sql(f"""SELECT metric_id,
            SUM(CASE WHEN metric_id IN ({lst(pct)}) AND (value < -1e-9 OR value > 100 + 1e-9) THEN 1 ELSE 0 END) AS out_pct,
            SUM(CASE WHEN metric_id IN ({lst(counts)}) AND value < -1e-9 THEN 1 ELSE 0 END) AS neg,
            ANY_VALUE(CASE WHEN (metric_id IN ({lst(pct)}) AND (value < 0 OR value > 100)) OR (metric_id IN ({lst(counts)}) AND value < 0)
                      THEN level || ' ' || unit_id || ' ' || period || ': ' || CAST(round(value, 3) AS VARCHAR) END) AS example
          FROM {{M}} WHERE status = 'ok' GROUP BY 1 HAVING out_pct > 0 OR neg > 0""")
    out = []
    for x in r.itertuples():
        issues = ([f"{x.out_pct} values outside 0–100"] if x.out_pct else []) + ([f"{x.neg} negative counts"] if x.neg else [])
        out.append({"metric_id": x.metric_id, "issues": "; ".join(issues), "examples": x.example})
    return pd.DataFrame(out)


def check_jumps(metrics_all: "Store", meta: pd.DataFrame) -> pd.DataFrame:
    counts = meta.loc[(meta["aggregation"] == "sum") & (meta["kind"] == "base"), "id"].tolist()
    lst = ", ".join("'" + i + "'" for i in counts)
    f = metrics_all.sql(f"""WITH g AS (
            SELECT metric_id, unit_id, CAST(period AS INTEGER) AS year, value, precision,
                   LAG(value) OVER w AS prev, LAG(CAST(period AS INTEGER)) OVER w AS prev_year
            FROM {{M}} WHERE level = 'gemeinde' AND status = 'ok' AND metric_id IN ({lst})
              AND regexp_full_match(period, '[0-9]{{4}}')
            WINDOW w AS (PARTITION BY metric_id, unit_id ORDER BY CAST(period AS INTEGER)))
        SELECT *, abs(value - prev) AS abs, abs(value - prev) / NULLIF(greatest(value, prev), 0) AS rel,
               COUNT(*) OVER (PARTITION BY metric_id) AS n_flags
        FROM g WHERE year - prev_year = 1 AND abs(value - prev) > {JUMP_MIN_ABS}
          AND abs(value - prev) / NULLIF(greatest(value, prev), 0) > {JUMP_REL}""")
    out = []
    for m, g in f.groupby("metric_id"):
        out.append({"metric_id": m, "n_flags": len(g), "n_series": g["unit_id"].nunique(),
                    "top": g.sort_values("abs", ascending=False).head(5)[
                        ["unit_id", "year", "prev", "value", "precision"]].to_dict("records")})
    return pd.DataFrame(out)


def check_coverage(metrics_all: "Store", meta: pd.DataFrame) -> pd.DataFrame:
    r = metrics_all.sql("""WITH g AS (SELECT metric_id, period, status FROM {M} WHERE level = 'gemeinde'),
        p AS (SELECT metric_id, COUNT(DISTINCT period) AS periods, MIN(period) AS first, MAX(period) AS latest FROM g GROUP BY 1)
        SELECT p.metric_id, p.periods, p.first, p.latest, g.status, COUNT(*) AS n
        FROM p JOIN g ON g.metric_id = p.metric_id AND g.period = p.latest GROUP BY ALL""")
    out = []
    for m, g in r.groupby("metric_id"):
        sc = dict(zip(g["status"], g["n"]))
        out.append({"metric_id": m, "periods": int(g["periods"].iloc[0]), "first": g["first"].iloc[0],
                    "latest": g["latest"].iloc[0], "n_ok": int(sc.get("ok", 0)), "n_ref": 2110, "status_counts": sc})
    return pd.DataFrame(out)


def check_cross_source(metrics_all: pd.DataFrame) -> pd.DataFrame:
    out = []
    for a, b, desc, tol in CROSS_CHECKS:
        A = metrics_all.rows("gemeinde", a)
        B = metrics_all.rows("gemeinde", b)
        A, B = A[A["status"] == "ok"], B[B["status"] == "ok"]
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
    allm = Store(interim_path("metrics_all.parquet"))
    obs = duckdb.connect().execute(
        f"SELECT * FROM read_parquet('{interim_path('observation.parquet')}') "
        "WHERE provenance = 'native' OR level = 'unallocated'").df()
    A = check_additivity(allm, obs, meta)
    B = check_ranges(allm, meta)
    C = check_jumps(allm, meta)
    D = check_coverage(allm, meta)
    E = check_cross_source(allm)
    L = ["# Data quality report", "",
         f"Generated {dt.datetime.now().isoformat(timespec='minutes')} · reference state {REFERENCE_DATE} · "
         "regenerate with `make quality`. Plan: [`validation_plan.md`](validation_plan.md).", "",
         f"Metrics: {meta['id'].nunique()} defined ({(meta['kind'] == 'base').sum()} base, "
         f"{(meta['kind'] == 'derived').sum()} derived) · rows: {int(allm.sql('SELECT COUNT(*) AS n FROM {M}').n[0]):,}", ""]
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
