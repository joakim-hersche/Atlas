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
# sources whose published higher-level values refer to the territory at the date in `period`
# (e.g. federal votes: canton results on the canton territory of the vote date)
STATE_FROM_PERIOD = {"bfs_votes_gemeinde", "bfs_nrw"}


def _state_from_period(period: str, default: dt.date) -> dt.date:
    p = period.split("#")[0]
    try:
        if len(p) >= 10:
            return dt.date.fromisoformat(p[:10])
        if len(p) == 4:
            return dt.date(int(p), 10, 1)  # National Council elections take place in October
    except ValueError:
        pass
    return default
# Same quantity from different sources. lag: b's period = a's period + lag (years);
# periods: explicit (period_a, period_b) pair; min_year: compare from this year on.
CROSS_CHECKS = [
    dict(a="pop_total", b="bil_pop_dec", tol=0.001, min_year=2011,
         desc="STATPOP population vs. demographic balance stock at 31 Dec (2011+; 2010 is ESPOP-based in the balance)"),
    dict(a="hh_persons", b="pop_total", tol=0.10,
         desc="Persons in private households vs. STATPOP population (institutions explain the gap)"),
    dict(a="gws_dwellings", b="vac_dwelling_stock", tol=0.001, lag=1,
         desc="GWS dwellings of year t vs. dwelling stock in the vacancy count of year t+1 (BFS's own denominator)"),
    dict(a="geo_area_land_ha", b="area_total_ha", tol=0.05, periods=("2026", "2013/18"),
         desc="Land area (swissBOUNDARIES3D 2026, without lakes) vs. land-use statistics total area 2013/18"),
]


def _is_share(m: dict) -> bool:
    """Bounded 0–100: derived ratios in % (not changes), or metrics flagged bounded_0_100."""
    if m.get("bounded_0_100") is True:
        return True
    agg = str(m.get("aggregation", ""))
    return (str(m.get("unit", "")).strip() == "%" and agg.startswith("ratio:") and "change" not in m["id"]
            and m.get("bounded_0_100") is not False)


def _may_be_negative(m: dict) -> bool:
    i = m["id"]
    return m.get("allow_negative") is True or any(k in i for k in ("net_", "_net", "balance", "change"))


_POP_CACHE: dict[int, pd.Series] = {}


def _pop_by_hist(year: int) -> pd.Series:
    """Population per municipality version (histId) from STATPOP geodata, years 2010–2025."""
    from pipeline.sources.bfs_statpop_geodata.fetch import FIRST_LV95_YEAR, LAST_YEAR, municipalities
    y = min(max(year, FIRST_LV95_YEAR), LAST_YEAR)
    if y not in _POP_CACHE:
        d = pd.read_parquet(municipalities(y))
        h = "GDEHISTID" if "GDEHISTID" in d.columns else "GDE_HISTID"
        _POP_CACHE[y] = d.set_index(d[h].astype("int64"))["BBTOT"].astype(float)
    return _POP_CACHE[y]


def transfer_effect(metric_rows: pd.DataFrame, source_state: dt.date, level: str) -> pd.Series:
    """Per canton or district: value of territory whose canton/district differs between
    source_state and the reference state (positive = gained on current boundaries).

    When the moved municipality merged into a larger one (Clavaleyres → Murten, Vellerat →
    Courrendlin), only its share of the merged target moved: the share is estimated from
    STATPOP population of the predecessor versions (nearest year 2010–2025; an estimate)."""
    col = {"kanton": "canton", "bezirk": "district_nr"}[level]
    mv, _ = load_backbone()
    cw = pd.read_parquet(interim_path("backbone", f"crosswalk_{REFERENCE_DATE.isoformat()}.parquet"))
    then_v = versions_at(mv, source_state)[["hist_id", col]].rename(columns={col: "u_then"})
    now_v = versions_at(mv, REFERENCE_DATE)[["hist_id", col]].rename(columns={col: "u_now"})
    m = cw.merge(then_v, left_on="from_hist_id", right_on="hist_id").merge(
        now_v, left_on="to_hist_id", right_on="hist_id", suffixes=("", "_now"))
    allpred = cw.merge(then_v, left_on="from_hist_id", right_on="hist_id")
    m = m[m["u_then"].astype(str) != m["u_now"].astype(str)]
    if m.empty:
        return pd.Series(dtype=float)
    vals = metric_rows.set_index("unit_id")["value"]
    pop = _pop_by_hist(source_state.year)
    allpred["p"] = allpred["from_hist_id"].map(pop).fillna(0) * allpred["weight"]
    tot = allpred.groupby("to_hist_id")["p"].sum()
    m["p"] = m["from_hist_id"].map(pop).fillna(0) * m["weight"]
    frac = (m["p"] / m["to_hist_id"].map(tot).replace(0, np.nan))
    # single predecessor (pure transfer) -> whole target moved
    n_pred = allpred.groupby("to_hist_id")["from_hist_id"].nunique()
    # no population for the predecessor versions (states before 2010): equal split, not 1 each
    # (1.0 each double-counted e.g. the Jura municipalities merged into Haute-Sorne in 2013)
    frac = frac.fillna(1.0 / m["to_hist_id"].map(n_pred))
    frac = frac.where(m["to_hist_id"].map(n_pred) > 1, 1.0)
    m["v"] = m["to_bfs_nr"].astype(str).map(vals) * frac
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


from pipeline.build.metrics import pseudo_owner as _pseudo_owner  # noqa: E402


def check_additivity(metrics_all: "Store", obs: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    sums = set(meta.loc[(meta["aggregation"] == "sum") & (meta["kind"] == "base"), "id"])
    native = obs[(obs["provenance"] == "native") & obs["metric_id"].isin(sums) & (obs["status"] == "ok")
                 & obs["level"].isin(["kanton", "bezirk", "schweiz"])]
    kt = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    canton_by_nr = dict(zip(kt["canton_id"].astype(int), kt["canton"]))
    pseudo = obs[(obs["level"] == "pseudo") & (obs["status"] == "ok")].copy()
    pseudo["owner"] = pseudo["unit_id"].map(lambda u: _pseudo_owner(u, canton_by_nr))
    rows = []
    for (sid, lvl, metric), nat in native.groupby(["source_id", "level", "metric_id"]):
        agg = metrics_all.rows(lvl, metric)
        # true aggregates only: published fallbacks (provenance native) would compare with themselves
        agg = agg[agg["provenance"] == "aggregated"]
        # estimates (M1: a few suppressed municipalities left out) are lower bounds, not sums to compare
        agg = agg[~agg["note"].fillna("").str.startswith("estimate:")]
        md0 = meta.set_index("id").loc[metric] if metric in set(meta["id"]) else {}
        # include_pseudo: the build already added the pseudo-units to canton/Swiss sums (E1 built in)
        with_pseudo = bool(md0.get("include_pseudo") is True) and lvl in ("kanton", "schweiz")
        j = nat.merge(agg[["unit_id", "period", "value", "n_missing", "n_units"]], on=["unit_id", "period"],
                      suffixes=("_pub", "_agg"))
        if j.empty:
            continue
        j["diff"] = j["value_agg"] - j["value_pub"]
        j["explained"] = 0.0
        if lvl in ("kanton", "bezirk"):
            state0 = dt.date.fromisoformat(nat["vintage"].iloc[0])
            gem = metrics_all.rows("gemeinde", metric)
            for per, jj in j.groupby("period"):
                # published canton results refer to the territory of the vote/election date;
                # district results are on the source's own state (E2)
                state = _state_from_period(per, state0) if (sid in STATE_FROM_PERIOD and lvl == "kanton") else state0
                eff = transfer_effect(gem[gem["period"] == per], state, lvl)
                j.loc[jj.index, "explained"] = jj["unit_id"].astype(str).map(eff).fillna(0).values
        if lvl in ("kanton", "bezirk") and len(pseudo) and not with_pseudo:
            # amounts the source assigns to a canton/district but to no municipality (E1)
            ps = pseudo[(pseudo["source_id"] == sid) & (pseudo["metric_id"] == metric)]
            if len(ps):
                psum = ps.groupby(["owner", "period"])["value"].sum()
                key = list(zip(j["unit_id"].astype(str), j["period"]))
                j["explained"] = j["explained"] - pd.Series([psum.get(k, 0.0) for k in key], index=j.index)
        if lvl == "schweiz":
            # persons the source could not attribute to a municipality are in the national total
            un = obs[(obs["source_id"] == sid) & (obs["level"] == "unallocated") & (obs["metric_id"] == metric)]
            if with_pseudo:   # the unallocated remainder is the pseudo-units, already in the aggregate
                un = un.iloc[:0]
            j["explained"] = -j["period"].map(un.set_index("period")["value"]).fillna(0).values
            # NRW: pseudo-units (Swiss abroad, postal voting; D17) are in the national total too.
            # Other sources' pseudo rows are canton-level remainders already covered by 'unallocated'.
            ps = pseudo[(pseudo["source_id"] == sid) & (pseudo["metric_id"] == metric)]
            if sid == "bfs_nrw" and len(ps) and not with_pseudo:
                j["explained"] = j["explained"] - j["period"].map(ps.groupby("period")["value"].sum()).fillna(0).values
        j["residual"] = j["diff"] - j["explained"]
        j["rel"] = j["residual"].abs() / j["value_pub"].abs().replace(0, np.nan)
        md = meta.set_index("id").loc[metric] if metric in set(meta["id"]) else {}
        tol = float(md.get("additivity_tolerance")) if isinstance(md.get("additivity_tolerance"), (int, float)) and md.get("additivity_tolerance") == md.get("additivity_tolerance") else TOL_REL
        note = md.get("additivity_note") if isinstance(md.get("additivity_note"), str) else ""
        documented = (j["residual"].abs() > 0.5) & (j["rel"] > TOL_REL) & (j["rel"] <= tol)
        rnd = md.get("additivity_rounding") if isinstance(md.get("additivity_rounding"), (int, float)) else None
        if rnd and rnd == rnd:  # each municipal cell rounded to `rnd` units (E4)
            n_units = agg.set_index(["unit_id", "period"])["n_units"]
            lim = pd.Series([n_units.get(k, 1) for k in zip(j["unit_id"], j["period"])], index=j.index) * rnd / 2
            documented |= (j["residual"].abs() > 0.5) & (j["residual"].abs() <= lim)
        # published values the source itself estimated (precision modelled) (E5)
        documented |= (j["residual"].abs() > 0.5) & (j["precision"] == "modelled")
        bad = j[(j["residual"].abs() > 0.5) & ~documented & ((j["rel"] > TOL_REL) | j["rel"].isna())]
        rows.append({"source_id": sid, "level": lvl, "metric_id": metric, "n_compared": len(j),
                     "n_exact": int((j["diff"].abs() <= 0.5).sum()),
                     "n_explained_canton_transfer": int(((j["diff"].abs() > 0.5) & (j["residual"].abs() <= 0.5)).sum()),
                     "n_within_tol": int(((j["residual"].abs() > 0.5) & (j["rel"] <= TOL_REL) & ~documented).sum()),
                     "n_documented": int(documented.sum()), "note": note,
                     "n_fail": len(bad), "max_rel_residual": float(j["rel"].max(skipna=True) or 0),
                     "worst": bad.reindex(bad["rel"].sort_values(ascending=False).index).head(3)[
                         ["unit_id", "period", "value_pub", "value_agg", "explained"]].to_dict("records")})
    return pd.DataFrame(rows)


def check_ranges(metrics_all: "Store", meta: pd.DataFrame) -> pd.DataFrame:
    recs = meta.to_dict("records")
    pct = [m["id"] for m in recs if _is_share(m)]
    counts = [m["id"] for m in recs if m.get("aggregation") == "sum" and not _may_be_negative(m)]
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
    vol = meta["volatile"].fillna(False).astype(bool) if "volatile" in meta else False
    counts = meta.loc[(meta["aggregation"] == "sum") & (meta["kind"] == "base") & ~vol, "id"].tolist()
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
    for c in CROSS_CHECKS:
        a, b, desc, tol = c["a"], c["b"], c["desc"], c["tol"]
        A = metrics_all.rows("gemeinde", a)
        B = metrics_all.rows("gemeinde", b)
        A, B = A[A["status"] == "ok"].copy(), B[B["status"] == "ok"].copy()
        if A.empty or B.empty:
            out.append({"check": desc, "result": "not run (metric missing)"})
            continue
        if "periods" in c:
            A = A[A["period"] == c["periods"][0]]
            B = B[B["period"] == c["periods"][1]].assign(period=c["periods"][0])
        if c.get("lag"):
            B = B[B["period"].str.fullmatch(r"\d{4}")]
            B["period"] = (B["period"].astype(int) - c["lag"]).astype(str)
        if c.get("min_year"):
            A = A[A["period"].str[:4].astype(int) >= c["min_year"]]
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
        "WHERE provenance = 'native' OR level IN ('unallocated', 'pseudo')").df()
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
        L += [f"Summary: {len(A)} metric×level comparisons, {int((A['n_fail'] == 0).sum())} pass, "
              f"{int((A['n_fail'] > 0).sum())} with failures.", "",
              "| Source | Level | Metric | Compared | Exact | Explained (transfers / unallocated) | Within 0.5% | Documented difference | Fail | Max rel. residual |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        L += [f"| {r.source_id} | {r.level} | {r.metric_id} | {r.n_compared} | {r.n_exact} | {r.n_explained_canton_transfer} | "
              f"{r.n_within_tol} | {r.n_documented}{' ¹' if r.note else ''} | {'**' + str(r.n_fail) + '**' if r.n_fail else 0} | {r.max_rel_residual:.3%} |"
              for r in A.sort_values(["n_fail", "source_id"], ascending=[False, True]).itertuples()]
        notes = A[A["note"].astype(bool)].drop_duplicates("metric_id")
        if len(notes):
            L += ["", "¹ Documented differences (from metrics.yaml `additivity_note`):", ""]
            L += [f"- {r.metric_id}: {r.note}" for r in notes.itertuples()]
        fails = A[A["n_fail"] > 0]
        if len(fails):
            L += ["", "Worst unexplained differences:", ""]
            for r in fails.itertuples():
                L += [f"- {r.source_id} / {r.level} / {r.metric_id}: {r.worst}"]
    else:
        L += ["No published higher-level values available yet."]
    L += ["", "## B. Ranges", ""]
    L += ([f"- **{r.metric_id}**: {r.issues} — e.g. {r.examples}" for r in B.itertuples()] or ["All shares within 0–100, no negative counts."])
    L += ["", f"## C. Year-on-year jumps (> {JUMP_REL:.0%} and > {JUMP_MIN_ABS} units)", "",
          "Metrics marked `volatile` (lumpy series such as construction investment) are excluded.", ""]
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
    L += curation_section()
    path = ROOT / "docs" / "quality_report.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(path)


def curation_section() -> list[str]:
    """H. Map curation (D38): verdicts per level from the last web build (data/interim/curation_verdicts.csv)."""
    p = interim_path("curation_verdicts.csv")
    L = ["", "## H. Map curation (D38, `pipeline/curation.yaml`)", ""]
    if not p.exists():
        return L + ["Not built yet (run `make web`)."]
    v = pd.read_csv(p)
    L += ["Verdicts from the last web build: shown, shown with a partial-coverage note, hidden as a map at that "
          "level (still on profiles), or hidden entirely (duplicates, confidence intervals). Rule: show at ≥ 80 % of "
          "units and of residents; note at ≥ 25 % of units, ≥ 50 % of residents and ≥ 20 units; levels with fewer "
          "than 20 units only when complete. Full list with reasons: `data/interim/curation_verdicts.csv`.", ""]
    t = v.groupby(["level", "verdict"]).size().unstack(fill_value=0)
    cols = [c for c in ("show", "note", "hide", "hidden") if c in t.columns]
    order = [l for l in ("gemeinde", "bezirk", "kanton", "grossregion", "sprachgebiet", "agglomeration",
                         "arbeitsmarktgebiet", "stadt_land", "gemeindetyp") if l in t.index]
    L += ["| Level | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    L += [f"| {l} | " + " | ".join(str(int(t.loc[l, c])) for c in cols) + " |" for l in order]
    L += [f"| **all** | " + " | ".join(str(int(t[c].sum())) for c in cols) + " |"]
    shown = v[v["verdict"].isin(["show", "note"])].groupby("metric_id").size()
    none = sorted(set(v["metric_id"]) - set(shown.index))
    L += ["", f"Metrics with no map at any level: {len(none)} (by theme: "
          + ", ".join(f"{k} {n}" for k, n in v[v["metric_id"].isin(none)].drop_duplicates("metric_id")
                      .groupby("theme").size().sort_values(ascending=False).items()) + ")."]
    return L


if __name__ == "__main__":
    print(run())
