"""Compute derived metrics and aggregate to every spatial level (brief 4.2 / 4.3), in DuckDB.

Input:  data/interim/observation.parquet (from pipeline.harmonize.run) and all metrics.yaml
Output: data/interim/metrics_all.parquet with columns
        unit_id, level, metric_id, period, value, status, precision, provenance, n_units, n_missing, note

Rules
- Base metrics with aggregation 'sum' are summed from municipalities to every level. A unit gets a
  value only if all its municipalities have one; otherwise the gap carries the real reason
  ("3 of 352 municipalities without a value: 3 suppressed (small numbers)").
- 'weighted_mean:<w>' uses metric <w> as weight, of the same period or, where <w> has no value for that
  period, of its nearest period (audit round 2, M5: climate normals '1991-2020', monthly energy data).
- Suppression tolerance (audit round 2, M1): a sum or weighted mean whose only gaps are municipalities
  suppressed for small numbers, together holding at most SUPPRESSED_MAX (1 %) of the unit's residents
  (STATPOP, nearest year), is computed from the published municipalities and kept as an estimate (note
  'estimate: ...'). The published value of the unit, where there is one, is preferred.
- 'not_aggregatable' stays at its native level; values the source publishes at higher levels are
  passed through (provenance native, note "published value").
- Published fallback (review round 1, defect 6): where the sum (or weighted mean) of municipalities is
  incomplete and the source publishes a value for that unit (provenance native), the published value
  is used: status ok, provenance native, note "published <level> value; municipal values incomplete
  (...)". The plausibility sweep (pipeline.build.quality) compares only provenance 'aggregated' rows.
  Only a published value on the current boundaries is used (audit round 2, M2): a canton or district row
  whose territory changed between the row's state and the reference date (e.g. BE and JU before Moutier
  moved on 2026-01-01) is not a fallback; the gap keeps its reason. Pass-through values of such units
  (medians, district survey values) are kept with a note naming the boundary state.
- Optional metrics.yaml key `zero_when: [<status>, ...]` on a base metric: rows with one of these
  statuses count as 0 in sums and ratio terms (a party that did not stand; a municipality counted with
  a neighbour). They count as 0 **only next to a real value**: a sum whose contributing rows are all
  zero_when rows is a gap with that status (e.g. not_applicable "party did not stand"), and a derived
  ratio none of whose numerator (or denominator) terms has a real value is a gap too.
- Optional key `include_pseudo: true`: level 'pseudo' rows (Swiss abroad and postal voting in votes
  and elections, lakes outside municipalities in the boundary data; D17) are added to the canton,
  major-region and Swiss sums, as the source counts them. Owner canton: unit id '<KT>:<code>' or a
  4-digit code 9KKx (KK = canton number). Completeness is judged on the municipalities only.
  Level 'unallocated' rows (national sums of what no municipality holds) add their remainder over the
  pseudo rows to the Swiss sum (audit round 2, M3: migration 'Ohne Angabe', vehicles without a canton).
  District and typology sums of such metrics carry the note 'excludes amounts not allocatable to a
  municipality'.
- Derived 'ratio:<a>[+<b>...]/<c>[+...][*<factor>]' and 'change:<metric>:<years>' are computed at every
  level from that level's base values, so ratios are re-computed, never averaged. A ratio that cannot
  be computed gets a gap row with the status and note of its first missing input.
- Derived 'pooled:<num terms>/<den terms>[*<factor>]:<k>[:<lag>]' is a pooled k-year rate: sum of the
  numerator over years t-k+1..t divided by the sum of the denominator over the same years (shifted by
  <lag> years, e.g. previous-year population), period 't-k+1-t'. All k years must be present.
- Base metrics whose native level is above the municipality (e.g. district survey values) are passed through.
- National Council (decision D37, pipeline/build/elections.py): LPS counted under FDP above canton level from
  2011; derived metrics with `majority_election: true` get status 'majority_election' in single-seat cantons
  (value kept) and are computed from proportional cantons only for regions and typologies.
Runs out of core with a memory cap, so the full catalog (≈20M rows) fits the build machine.
"""
from __future__ import annotations

import os
import re

import duckdb
import pandas as pd

from pipeline.backbone.levels import LEVEL_COLUMNS, membership
from pipeline.common import interim_path
from pipeline.harmonize.schema import load_metrics

AGG_LEVELS = ["bezirk", "kanton", *LEVEL_COLUMNS, "schweiz"]
PSEUDO_LEVELS = ("kanton", "grossregion", "schweiz")   # levels made of whole cantons
RATIO = re.compile(r"^ratio:(?P<num>[^/]+)/(?P<den>[^*]+)(?:\*(?P<f>[\d.]+))?$")
CHANGE = re.compile(r"^change:(?P<m>[a-z0-9_]+):(?P<n>\d+)$")
POOLED = re.compile(r"^pooled:(?P<num>[^/]+)/(?P<den>[^*:]+)(?:\*(?P<f>[\d.]+))?:(?P<k>\d+)(?::(?P<lag>\d+))?$")
PREC_RANK = "CASE precision WHEN 'exact' THEN 0 WHEN 'survey' THEN 1 WHEN 'modelled' THEN 2 ELSE 3 END"
PREC_NAME = "CASE MAX({r}) WHEN 0 THEN 'exact' WHEN 1 THEN 'survey' WHEN 2 THEN 'modelled' ELSE 'boundary_estimate' END"
PREC_OF = ("CASE {x} WHEN 0 THEN 'exact' WHEN 1 THEN 'survey' WHEN 2 THEN 'modelled' ELSE 'boundary_estimate' END")
# which input decides the status of a derived gap (most specific first)
GAP_RANK = ("CASE status WHEN 'not_applicable' THEN 1 WHEN 'suppressed' THEN 2 WHEN 'not_published' THEN 3 "
            "WHEN 'not_covered' THEN 4 WHEN 'no_data' THEN 5 ELSE 9 END")
LEVEL_WORD = {"bezirk": "district", "kanton": "canton", "schweiz": "national", "grossregion": "major-region"}
UNIT_WORD = {"gemeinde": "municipalities"}
SUPPRESSED_MAX = 0.01        # M1: suppressed municipalities may hold at most 1 % of a unit's residents
POP_METRIC = "pop_total"     # reference population for the tolerance (STATPOP, 31 Dec)
EST_DERIVED = ("estimate: computed from sums that leave out a few municipalities suppressed for small numbers "
               "(at most 1 % of residents)")


def _terms(expr: str) -> list[str]:
    return [t.strip() for t in expr.split("+") if t.strip()]


def _q(ids) -> str:
    return ", ".join("'" + i.replace("'", "''") + "'" for i in ids) or "''"


def pseudo_owner(unit_id: str, canton_by_nr: dict) -> str:
    """Canton a pseudo-unit belongs to: '<KT>:<code>' or a vote/election code 9KKx (KK = canton nr)."""
    u = str(unit_id)
    if ":" in u:
        return u.split(":", 1)[0]
    if u.isdigit() and len(u) == 4 and u.startswith("9"):
        return canton_by_nr.get(int(u[1:3]), "")
    return ""


def period_year(p: str) -> int | None:
    """Year a period refers to: the last 4-digit year in it ('2022-2024' -> 2024, '1991-2020' -> 2020,
    '2026-10' -> 2026, '2020/25' -> 2020)."""
    ys = [int(y) for y in re.findall(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)", str(p))]
    return max(ys) if ys else None


def nearest_periods(periods: list[str], available: list[str]) -> dict[str, str]:
    """period -> the same period if available, else the available period with the nearest year (later on ties)."""
    av = [(period_year(a), a) for a in available if period_year(a) is not None]
    out = {}
    for p in periods:
        if p in available:
            out[p] = p
            continue
        y = period_year(p)
        if y is None or not av:
            continue
        out[p] = min(av, key=lambda t: (abs(t[0] - y), -t[0], t[1]))[1]
    return out


def changed_units(dates) -> pd.DataFrame:
    """(level, unit_id, date): cantons and districts whose territory on `date` differs from the reference
    state (a municipality, followed through the crosswalk, belonged to another canton / district)."""
    import datetime as _dt
    from pipeline.backbone.crosswalk import load_backbone, versions_at
    from pipeline.common import REFERENCE_DATE
    mv, _ = load_backbone()
    cw = pd.read_parquet(interim_path("backbone", f"crosswalk_{REFERENCE_DATE.isoformat()}.parquet"))
    ref = membership().set_index("bfs_nr")[["kanton", "bezirk"]]
    rows = []
    for d in sorted(set(dates)):
        if d is None or d >= REFERENCE_DATE:
            continue
        v = versions_at(mv, d)[["hist_id", "canton", "district_nr"]]
        x = v.merge(cw[["from_hist_id", "to_bfs_nr"]], left_on="hist_id", right_on="from_hist_id").join(ref, on="to_bfs_nr")
        kc = x[x["canton"].astype(str) != x["kanton"].astype(str)]
        for k in set(kc["canton"].astype(str)) | set(kc["kanton"].astype(str)):
            rows.append(("kanton", k, d))
        bc = x[x["district_nr"].astype(str) != x["bezirk"].astype(str)]
        for b in set(bc["district_nr"].astype(str)) | set(bc["bezirk"].astype(str)):
            rows.append(("bezirk", b, d))
    return pd.DataFrame(rows, columns=["level", "unit_id", "date"])


def native_state_date(vintage, period: str):
    """State of a published (native) row: its vintage when the connector names an older state, else the end
    of the period's year (a value 'for 2025' is on the 2025 boundaries), capped at the reference date."""
    import datetime as _dt
    from pipeline.common import REFERENCE_DATE
    try:
        v = _dt.date.fromisoformat(str(vintage)[:10])
    except ValueError:
        v = REFERENCE_DATE
    if v < REFERENCE_DATE:
        return v
    y = period_year(period)
    return min(REFERENCE_DATE, _dt.date(y, 12, 31)) if y else REFERENCE_DATE


def _missing_note(prefix: str = "") -> str:
    """SQL text: 'k of n municipalities without a value: a suppressed (small numbers), b not published, ...'."""
    parts = [(f"{prefix}n_supp", "suppressed (small numbers)"), (f"{prefix}n_np", "not published"),
             (f"{prefix}n_nc", "not covered"), (f"{prefix}n_na", "not applicable"), (f"{prefix}n_nd", "no data"),
             (f"(n.n - {prefix}n_rows)", "no row in the source")]
    items = ", ".join(f"CASE WHEN {c} > 0 THEN CAST({c} AS VARCHAR) || ' {t}' END" for c, t in parts)
    return (f"CAST(n.n - {prefix}n_with AS VARCHAR) || ' of ' || CAST(n.n AS VARCHAR) "
            f"|| ' municipalities without a value: ' || concat_ws(', ', {items})")


def run() -> str:
    meta = load_metrics().drop_duplicates("id")
    for c in ("include_pseudo", "zero_when", "majority_election"):
        if c not in meta:
            meta[c] = None
    tmp = interim_path("duckdb_tmp", "x").parent
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{os.environ.get('GB_DUCKDB_MEMORY', '4GB')}'")
    con.execute(f"SET temp_directory='{tmp}'")
    con.execute("SET preserve_insertion_order=false")

    mem = membership()
    mem["schweiz"] = "CH"
    mem["unit_id"] = mem["bfs_nr"].astype(str)
    con.register("mem_df", mem[["unit_id", *AGG_LEVELS]].astype(str))
    con.execute("CREATE TABLE mem AS SELECT * FROM mem_df")
    con.register("meta_df", meta[["id", "kind", "aggregation", "native_level"]].astype(str))
    con.execute("CREATE TABLE meta AS SELECT * FROM meta_df")
    obs = interim_path("observation.parquet")
    zw = [(r["id"], st) for r in meta.to_dict("records")
          if isinstance(r.get("zero_when"), list) for st in r["zero_when"]]
    con.register("zw_df", pd.DataFrame(zw or [("", "")], columns=["metric_id", "status"]))
    con.execute("CREATE TABLE zw AS SELECT * FROM zw_df")

    # base rows used for aggregation: municipality rows of base metrics
    con.execute(f"""
        CREATE TABLE gem AS
        SELECT o.unit_id, o.metric_id, o.period, o.value, o.status, o.precision, o.provenance, o.note
        FROM read_parquet('{obs}') o JOIN meta m ON o.metric_id = m.id AND m.kind = 'base'
        WHERE o.level = 'gemeinde'""")
    # published values at higher levels (fallback for incomplete sums; pass-through for not_aggregatable)
    con.execute(f"""
        CREATE TABLE nat_all AS
        SELECT o.unit_id, o.level, o.metric_id, o.period, o.value, o.precision, o.note,
               CAST(o.vintage AS VARCHAR) AS vintage
        FROM read_parquet('{obs}') o JOIN meta m ON o.metric_id = m.id AND m.kind = 'base'
        WHERE o.provenance = 'native' AND o.status = 'ok' AND o.level IN ({_q(AGG_LEVELS)})""")
    # M2: published canton / district rows on a state whose territory differs from the reference state
    sd = con.execute(f"""SELECT DISTINCT level, CAST(vintage AS VARCHAR) AS vintage, period
                         FROM read_parquet('{obs}') WHERE provenance = 'native'
                           AND level IN ('kanton', 'bezirk')""").df()
    sd["date"] = [native_state_date(v, p) for v, p in zip(sd["vintage"], sd["period"])]
    chg = changed_units(sd["date"].unique())
    vbad = sd.merge(chg, on=["level", "date"])
    word_of = {"kanton": "canton", "bezirk": "district"}
    vbad["why"] = [f"published {word_of[l]} value is on the boundaries of {d.isoformat()}; the territory has changed since"
                   for l, d in zip(vbad["level"], vbad["date"])]
    con.register("vbad_df", vbad[["level", "unit_id", "vintage", "period", "why"]] if len(vbad) else
                 pd.DataFrame(columns=["level", "unit_id", "vintage", "period", "why"]).astype(str))
    con.execute("CREATE TABLE vbad AS SELECT * FROM vbad_df")
    print("M2 published canton/district rows on other boundaries:", len(vbad), "unit-periods")
    con.execute("""CREATE TABLE nat AS SELECT n.* FROM nat_all n
                   ANTI JOIN vbad b ON b.level = n.level AND b.unit_id = n.unit_id AND b.vintage = n.vintage AND b.period = n.period""")
    con.execute("""CREATE TABLE nat_bad AS SELECT n.unit_id, n.level, n.metric_id, n.period, b.why FROM nat_all n
                   JOIN vbad b ON b.level = n.level AND b.unit_id = n.unit_id AND b.vintage = n.vintage AND b.period = n.period""")
    # base metrics published natively above municipality level (passed through; boundary state noted)
    con.execute(f"""
        CREATE TABLE native_only AS
        SELECT o.unit_id, o.level, o.metric_id, o.period, o.value, o.status, o.precision, o.provenance,
               1 AS n_units, CASE WHEN o.status = 'ok' THEN 0 ELSE 1 END AS n_missing,
               CASE WHEN b.why IS NOT NULL AND o.status = 'ok' THEN concat_ws('; ', o.note, b.why) ELSE o.note END AS note
        FROM read_parquet('{obs}') o JOIN meta m ON o.metric_id = m.id
        LEFT JOIN vbad b ON b.level = o.level AND b.unit_id = o.unit_id AND b.vintage = CAST(o.vintage AS VARCHAR)
                        AND b.period = o.period AND o.provenance = 'native'
        WHERE m.kind = 'base' AND m.native_level <> 'gemeinde' AND o.level NOT IN ('gemeinde', 'unallocated', 'pseudo')""")

    # pseudo-units added to canton / major-region / Swiss sums (include_pseudo)
    inc = meta.loc[meta["include_pseudo"].fillna(False).astype(bool), "id"].tolist()
    ps = con.execute(f"""SELECT unit_id, metric_id, period, value FROM read_parquet('{obs}')
                         WHERE level = 'pseudo' AND status = 'ok' AND metric_id IN ({_q(inc)})""").df()
    # M3: the national 'unallocated' sum minus the pseudo rows = amounts in no canton (Swiss sum only)
    un = con.execute(f"""SELECT metric_id, period, SUM(value) AS value FROM read_parquet('{obs}')
                         WHERE level = 'unallocated' AND status = 'ok' AND metric_id IN ({_q(inc)}) GROUP BY 1, 2""").df()
    if len(un):
        pss = ps.groupby(["metric_id", "period"])["value"].sum()
        un["rem"] = un["value"] - [pss.get((m_, p_), 0.0) for m_, p_ in zip(un["metric_id"], un["period"])]
        rem = un[un["rem"].abs() > 1e-6 * un["value"].abs().clip(lower=1)]
        ps = pd.concat([ps, pd.DataFrame({"unit_id": "CH:unallocated", "metric_id": rem["metric_id"],
                                          "period": rem["period"], "value": rem["rem"]})], ignore_index=True)
        print("M3 unallocated remainder added to Swiss sums:", len(rem), "metric-periods")
    kt = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    canton_by_nr = dict(zip(kt["canton_id"].astype(int), kt["canton"]))
    ps["kanton"] = ps["unit_id"].map(lambda u: pseudo_owner(u, canton_by_nr))
    gr = mem.drop_duplicates("kanton").set_index("kanton")["grossregion"]
    ps_rows = []
    for lvl in PSEUDO_LEVELS:
        u = ps["kanton"] if lvl == "kanton" else (ps["kanton"].map(gr) if lvl == "grossregion" else "CH")
        g = ps.assign(u=u, lvl=lvl).dropna(subset=["u"])
        g = g[g["u"].astype(str) != ""]
        ps_rows.append(g.groupby(["lvl", "u", "metric_id", "period"], as_index=False)["value"].sum())
    con.register("ps_df", pd.concat(ps_rows, ignore_index=True) if len(ps) else
                 pd.DataFrame(columns=["lvl", "u", "metric_id", "period", "value"]).astype({"value": float}))
    con.execute("CREATE TABLE ps AS SELECT lvl, CAST(u AS VARCHAR) AS u, metric_id, period, value FROM ps_df")
    # metric-periods with amounts outside municipalities (construction, vehicles, migration; not votes):
    # their district and typology sums say so
    con.execute(f"""CREATE TABLE psx AS SELECT DISTINCT metric_id, period FROM read_parquet('{obs}')
                    WHERE level = 'unallocated' AND status = 'ok' AND value <> 0 AND metric_id IN ({_q(inc)})""")

    # M1 / M5: reference population per municipality and period (STATPOP of the nearest year)
    pop_periods = [r[0] for r in con.execute(f"SELECT DISTINCT period FROM gem WHERE metric_id = '{POP_METRIC}' AND status = 'ok'").fetchall()]
    all_periods = [r[0] for r in con.execute("SELECT DISTINCT period FROM gem").fetchall()]
    pmap = nearest_periods(all_periods, pop_periods)
    con.register("pmap_df", pd.DataFrame(list(pmap.items()) or [("", "")], columns=["period", "pop_period"]))
    con.execute(f"""CREATE TABLE popb AS SELECT unit_id, period AS pop_period, value AS pop FROM gem
                    WHERE metric_id = '{POP_METRIC}' AND status = 'ok'""")

    # aggregation input: zero_when statuses count as 0 (flag zw), real = a published value
    con.execute("""
        CREATE TABLE gem_sum AS
        SELECT g.unit_id, g.metric_id, g.period,
               CASE WHEN g.value IS NULL AND z.metric_id IS NOT NULL THEN 0 ELSE g.value END AS value,
               g.status, g.status = 'ok' AS real, z.metric_id IS NOT NULL AS zw, g.note, g.precision, pb.pop
        FROM gem g LEFT JOIN zw z ON g.metric_id = z.metric_id AND g.status = z.status
        LEFT JOIN pmap_df pm ON pm.period = g.period
        LEFT JOIN popb pb ON pb.unit_id = g.unit_id AND pb.pop_period = pm.pop_period""")

    def counts(alias: str) -> str:
        a = alias
        return f"""COUNT(*) FILTER (WHERE {a}.real) AS n_real, COUNT({a}.value) AS n_with, COUNT(*) AS n_rows,
                   COUNT(*) FILTER (WHERE {a}.value IS NULL AND {a}.status = 'suppressed') AS n_supp,
                   COUNT(*) FILTER (WHERE {a}.value IS NULL AND {a}.status = 'not_published') AS n_np,
                   COUNT(*) FILTER (WHERE {a}.value IS NULL AND {a}.status = 'not_covered') AS n_nc,
                   COUNT(*) FILTER (WHERE {a}.value IS NULL AND {a}.status = 'not_applicable') AS n_na,
                   COUNT(*) FILTER (WHERE {a}.value IS NULL AND {a}.status NOT IN
                                    ('suppressed', 'not_published', 'not_covered', 'not_applicable')) AS n_nd,
                   SUM({a}.pop) FILTER (WHERE {a}.value IS NULL AND {a}.status = 'suppressed') AS supp_pop,
                   COUNT({a}.pop) FILTER (WHERE {a}.value IS NULL AND {a}.status = 'suppressed') AS n_supp_pop,
                   SUM({a}.pop) AS all_pop"""

    def gap_status(prefix: str = "g.") -> str:
        p = prefix
        return f"""CASE WHEN {p}n_with = n.n AND {p}n_real = 0 THEN {p}zw_status
                        WHEN {p}n_supp > 0 AND {p}n_supp >= greatest({p}n_np, {p}n_nc, {p}n_na, {p}n_nd, n.n - {p}n_rows) THEN 'suppressed'
                        WHEN {p}n_nc > 0 AND {p}n_nc >= greatest({p}n_np, {p}n_na, {p}n_nd, n.n - {p}n_rows) THEN 'not_covered'
                        WHEN {p}n_np > 0 AND {p}n_np >= greatest({p}n_na, {p}n_nd, n.n - {p}n_rows) THEN 'not_published'
                        ELSE 'no_data' END"""

    def estimate(p: str = "g.") -> str:
        """M1: only suppressed municipalities missing, holding at most SUPPRESSED_MAX of the residents."""
        return (f"({p}n_with < n.n AND {p}n_rows = n.n AND {p}n_with + {p}n_supp = n.n AND {p}n_real > 0 "
                f"AND {p}n_supp_pop = {p}n_supp AND {p}all_pop > 0 AND {p}supp_pop <= {SUPPRESSED_MAX} * {p}all_pop)")

    def estimate_note(p: str = "g.") -> str:
        return (f"'estimate: ' || CAST({p}n_supp AS VARCHAR) || ' of ' || CAST(n.n AS VARCHAR) || "
                f"' municipalities suppressed for small numbers (' || printf('%.2f', 100 * {p}supp_pop / {p}all_pop) || "
                f"' % of residents) are not included'")

    parts = ["""SELECT unit_id, 'gemeinde' AS level, metric_id, period, value, status, precision, provenance,
                       1 AS n_units, CASE WHEN status = 'ok' THEN 0 ELSE 1 END AS n_missing, note FROM gem"""]
    sums = meta.loc[(meta["kind"] == "base") & (meta["aggregation"] == "sum"), "id"].tolist()
    wmeans = {r["id"]: r["aggregation"].split(":", 1)[1] for r in meta.to_dict("records")
              if r["kind"] == "base" and str(r["aggregation"]).startswith("weighted_mean:")}
    notagg = meta.loc[(meta["kind"] == "base") & (meta["aggregation"] == "not_aggregatable")
                      & (meta["native_level"] == "gemeinde"), "id"].tolist()
    # M5: weight of the same period, else of the weight metric's nearest period
    wrows = []
    for mid, w in wmeans.items():
        vp = [r[0] for r in con.execute("SELECT DISTINCT period FROM gem WHERE metric_id = ?", [mid]).fetchall()]
        wp = [r[0] for r in con.execute("SELECT DISTINCT period FROM gem WHERE metric_id = ? AND status = 'ok'", [w]).fetchall()]
        wrows += [(mid, p_, q_) for p_, q_ in nearest_periods(vp, wp).items()]
    con.register("wmap_df", pd.DataFrame(wrows or [("", "", "")], columns=["metric_id", "period", "w_period"]))
    con.execute("CREATE TABLE wmap AS SELECT * FROM wmap_df")
    for lvl in AGG_LEVELS:
        con.execute(f"""CREATE TABLE n_{lvl} AS SELECT {lvl} AS u, COUNT(*) AS n FROM mem
                        WHERE {lvl} IS NOT NULL AND {lvl} NOT IN ('nan', '<NA>', 'None') GROUP BY 1""")
        word = LEVEL_WORD.get(lvl, lvl)
        use_nat = "x.complete = 0 AND nt.value IS NOT NULL"
        sub_note = ("'excludes amounts not allocatable to a municipality (in canton and Swiss totals only)'"
                    if lvl not in PSEUDO_LEVELS else "NULL")
        parts.append(f"""
            SELECT x.unit_id, '{lvl}' AS level, x.metric_id, x.period,
                   CASE WHEN {use_nat} THEN nt.value ELSE x.value END AS value,
                   CASE WHEN {use_nat} THEN 'ok' ELSE x.status END AS status,
                   CASE WHEN {use_nat} THEN nt.precision ELSE x.precision END AS precision,
                   CASE WHEN {use_nat} THEN 'native' ELSE 'aggregated' END AS provenance,
                   x.n_units, x.n_missing,
                   CASE WHEN {use_nat} THEN 'published {word} value; municipal values incomplete (' || x.mnote || ')'
                        WHEN x.status <> 'ok' AND nb.why IS NOT NULL THEN x.note || '; ' || nb.why || ', so it is not used'
                        ELSE x.note END AS note
            FROM (SELECT g.u AS unit_id, g.metric_id, g.period,
                         CASE WHEN (g.n_with = n.n AND g.n_real > 0) OR {estimate()} THEN g.s + COALESCE(p.value, 0) END AS value,
                         CASE WHEN (g.n_with = n.n AND g.n_real > 0) OR {estimate()} THEN 'ok' ELSE {gap_status()} END AS status,
                         CASE WHEN g.n_with = n.n THEN 1 ELSE 0 END AS complete,
                         g.precision, n.n AS n_units, n.n - g.n_with AS n_missing,
                         CASE WHEN g.n_with = n.n AND g.n_real > 0 THEN
                                   CASE WHEN p.value IS NOT NULL THEN 'includes units outside municipalities (pseudo-units)'
                                        WHEN px.metric_id IS NOT NULL THEN {sub_note} END
                              WHEN g.n_with = n.n THEN g.zw_note
                              WHEN {estimate()} THEN {estimate_note()}
                              ELSE {_missing_note('g.')} END AS note,
                         {_missing_note('g.')} AS mnote
                  FROM (SELECT m.{lvl} AS u, gem.metric_id, gem.period, SUM(gem.value) AS s, {counts('gem')},
                               mode(gem.status) FILTER (WHERE gem.zw) AS zw_status,
                               ANY_VALUE(gem.note) FILTER (WHERE gem.zw) AS zw_note,
                               {PREC_NAME.format(r=PREC_RANK)} AS precision
                        FROM gem_sum gem JOIN mem m USING (unit_id)
                        WHERE gem.metric_id IN ({_q(sums)}) AND m.{lvl} NOT IN ('nan', '<NA>', 'None')
                        GROUP BY 1, 2, 3) g
                  JOIN n_{lvl} n ON g.u = n.u
                  LEFT JOIN ps p ON p.lvl = '{lvl}' AND p.u = g.u AND p.metric_id = g.metric_id AND p.period = g.period
                  LEFT JOIN psx px ON px.metric_id = g.metric_id AND px.period = g.period) x
            LEFT JOIN nat nt ON nt.level = '{lvl}' AND nt.unit_id = x.unit_id AND nt.metric_id = x.metric_id
                            AND nt.period = x.period
            LEFT JOIN nat_bad nb ON nb.level = '{lvl}' AND nb.unit_id = x.unit_id AND nb.metric_id = x.metric_id
                            AND nb.period = x.period""")
        for mid, w in wmeans.items():
            full = "(g.n_with = n.n AND g.w > 0)"
            est = f"({estimate()} AND g.w > 0)"
            parts.append(f"""
                SELECT g.u AS unit_id, '{lvl}' AS level, '{mid}' AS metric_id, g.period,
                       CASE WHEN {full} THEN g.vw / g.w WHEN nt.value IS NOT NULL THEN nt.value WHEN {est} THEN g.vw / g.w END AS value,
                       CASE WHEN {full} OR nt.value IS NOT NULL OR {est} THEN 'ok' ELSE {gap_status()} END AS status,
                       CASE WHEN {full} OR (nt.value IS NULL AND {est}) THEN g.precision ELSE COALESCE(nt.precision, g.precision) END AS precision,
                       CASE WHEN NOT {full} AND nt.value IS NOT NULL THEN 'native' ELSE 'aggregated' END AS provenance,
                       n.n AS n_units, n.n - g.n_with AS n_missing,
                       CASE WHEN {full} THEN NULL
                            WHEN nt.value IS NOT NULL THEN 'published {word} value; municipal values incomplete'
                            WHEN {est} THEN {estimate_note()}
                            WHEN nb.why IS NOT NULL THEN {_missing_note('g.')} || '; ' || nb.why || ', so it is not used'
                            ELSE {_missing_note('g.')} END AS note
                FROM (SELECT m.{lvl} AS u, v.period, SUM(v.value * w.value) AS vw,
                             SUM(CASE WHEN v.value IS NOT NULL THEN w.value END) AS w,
                             {counts('v')},
                             NULL AS zw_status, NULL AS zw_note,
                             {PREC_NAME.format(r='CASE v.precision WHEN \'exact\' THEN 0 WHEN \'survey\' THEN 1 WHEN \'modelled\' THEN 2 ELSE 3 END')} AS precision
                      FROM gem_sum v JOIN wmap wm ON wm.metric_id = v.metric_id AND wm.period = v.period
                      JOIN gem w ON v.unit_id = w.unit_id AND w.period = wm.w_period AND w.metric_id = '{w}'
                      JOIN mem m ON v.unit_id = m.unit_id
                      WHERE v.metric_id = '{mid}' AND m.{lvl} NOT IN ('nan', '<NA>', 'None')
                      GROUP BY 1, 2) g JOIN n_{lvl} n ON g.u = n.u
                LEFT JOIN nat nt ON nt.level = '{lvl}' AND nt.unit_id = g.u AND nt.metric_id = '{mid}'
                                AND nt.period = g.period
                LEFT JOIN nat_bad nb ON nb.level = '{lvl}' AND nb.unit_id = g.u AND nb.metric_id = '{mid}'
                                AND nb.period = g.period""")
    # not aggregatable (medians, published rates): the source's own higher-level values; a value on other
    # boundaries is kept (it is the only one) with a note naming the boundary state (M2)
    parts.append(f"""SELECT n.unit_id, n.level, n.metric_id, n.period, n.value, 'ok' AS status, n.precision,
                            'native' AS provenance, 1 AS n_units, 0 AS n_missing,
                            CASE WHEN b.why IS NOT NULL THEN 'published value; ' || b.why ELSE 'published value' END AS note
                     FROM nat_all n LEFT JOIN nat_bad b ON b.level = n.level AND b.unit_id = n.unit_id
                          AND b.metric_id = n.metric_id AND b.period = n.period
                     WHERE n.metric_id IN ({_q(notagg)})""")
    parts.append("SELECT * FROM native_only")
    # survey counts published only by district (Structural Survey languages): canton = sum of its districts,
    # where every district has a value on the current boundaries and the source has no canton value
    bez_sums = meta.loc[(meta["kind"] == "base") & (meta["aggregation"] == "sum") & (meta["native_level"] == "bezirk"), "id"].tolist()
    if bez_sums:
        con.execute("""CREATE TABLE bez_kt AS SELECT DISTINCT bezirk, kanton FROM mem
                       WHERE bezirk NOT IN ('nan', '<NA>', 'None')""")
        con.execute("CREATE TABLE bez_n AS SELECT kanton, COUNT(*) AS n FROM bez_kt GROUP BY 1")
        parts.append(f"""
            SELECT d.kanton AS unit_id, 'kanton' AS level, o.metric_id, o.period, SUM(o.value) AS value, 'ok' AS status,
                   {PREC_NAME.format(r=PREC_RANK.replace('precision', 'o.precision'))} AS precision, 'aggregated' AS provenance,
                   COUNT(*) AS n_units, 0 AS n_missing, 'sum of the published district values' AS note
            FROM native_only o JOIN bez_kt d ON o.unit_id = d.bezirk JOIN bez_n k ON k.kanton = d.kanton
            WHERE o.level = 'bezirk' AND o.status = 'ok' AND o.metric_id IN ({_q(bez_sums)})
              AND (o.note IS NULL OR o.note NOT LIKE '%boundaries of%')
              AND NOT EXISTS (SELECT 1 FROM native_only x WHERE x.level = 'kanton' AND x.unit_id = d.kanton
                              AND x.metric_id = o.metric_id AND x.period = o.period)
            GROUP BY d.kanton, o.metric_id, o.period, k.n HAVING COUNT(DISTINCT o.unit_id) = k.n""")
    # one part at a time (a single UNION of all parts exceeds the memory cap)
    con.execute("CREATE TABLE base_all AS " + parts[0])
    for part in parts[1:]:
        con.execute("INSERT INTO base_all " + part)
    # National Council (D37): LPS under FDP above canton level from 2011 (pipeline/build/elections.py)
    from pipeline.build import elections
    has_nrw = "nrw_fw_fdp" in set(meta["id"])
    if has_nrw:
        print("D37 LPS -> FDP above canton level:", elections.merge_lps(con), "rows")
    # ratio inputs: usable base rows (ok, or a zero_when status counted as 0), materialized once
    con.execute(f"""
        CREATE TABLE base_terms AS
        SELECT b.unit_id, b.level, b.metric_id, b.period, COALESCE(b.value, 0) AS value, b.precision, b.n_units,
               CASE WHEN b.status = 'ok' THEN 1 ELSE 0 END AS real,
               CASE WHEN b.provenance = 'native' AND b.level <> 'gemeinde' THEN 1 ELSE 0 END AS nat,
               CASE WHEN b.note LIKE 'estimate:%' THEN 1 ELSE 0 END AS est
        FROM base_all b LEFT JOIN zw z ON b.metric_id = z.metric_id AND b.status = z.status
        WHERE b.status = 'ok' OR z.metric_id IS NOT NULL""")

    def side(ids: list[str]) -> str:
        return f"""SELECT unit_id, level, period, SUM(value) AS s, MAX({PREC_RANK}) AS p, MAX(n_units) AS n_units,
                          SUM(real) AS n_real, MAX(nat) AS nat, MAX(est) AS est
                   FROM base_terms WHERE metric_id IN ({_q(ids)})
                   GROUP BY 1, 2, 3 HAVING COUNT(DISTINCT metric_id) = {len(set(ids))}"""

    def gaps(mid: str, ids: list[str]) -> str:
        """Gap rows for a derived ratio: units with a missing input row but no computed value."""
        return f"""
            SELECT i.unit_id, i.level, '{mid}' AS metric_id, i.period, CAST(NULL AS DOUBLE) AS value,
                   i.status, i.precision, 'derived' AS provenance, 1 AS n_units, 1 AS n_missing, i.note
            FROM (SELECT unit_id, level, period, arg_min(status, {GAP_RANK}) AS status,
                         arg_min(note, {GAP_RANK}) AS note, arg_min(precision, {GAP_RANK}) AS precision
                  FROM base_all WHERE metric_id IN ({_q(ids)}) AND status <> 'ok' GROUP BY 1, 2, 3) i
            ANTI JOIN (SELECT unit_id, level, period FROM der WHERE metric_id = '{mid}') o
                 USING (unit_id, level, period)"""

    # derived metrics, computed at every level from that level's base values
    derived, gap_list = [], []
    for m in meta[meta["kind"] == "derived"].to_dict("records"):
        agg = str(m["aggregation"])
        if (r := RATIO.match(agg)):
            num, den = _terms(r["num"]), _terms(r["den"])
            f = float(r["f"]) if r["f"] else 1.0
            ok_sql = f"""
                SELECT a.unit_id, a.level, '{m["id"]}' AS metric_id, a.period,
                       a.s / NULLIF(b.s, 0) * {f} AS value, 'ok' AS status,
                       {PREC_OF.format(x='GREATEST(a.p, b.p)')} AS precision,
                       'derived' AS provenance, a.n_units, 0 AS n_missing,
                       CASE WHEN GREATEST(a.nat, b.nat) = 1 THEN 'computed from published values (municipal values incomplete)'
                            WHEN GREATEST(a.est, b.est) = 1 THEN '{EST_DERIVED}' END AS note
                FROM ({side(num)}) a JOIN ({side(den)}) b USING (unit_id, level, period)
                WHERE b.s IS NOT NULL AND b.s <> 0 AND a.n_real > 0 AND b.n_real > 0"""
            derived.append(ok_sql)
            gap_list.append((m["id"], num + den))
        elif (p := POOLED.match(agg)):
            num, den = _terms(p["num"]), _terms(p["den"])
            f = float(p["f"]) if p["f"] else 1.0
            k, lag = int(p["k"]), int(p["lag"] or 0)

            def win(ids):
                return f"""SELECT unit_id, level, y, SUM(s) OVER w AS s, MAX(p) OVER w AS p, SUM(n_real) OVER w AS n_real,
                                  MAX(nat) OVER w AS nat, MAX(est) OVER w AS est, COUNT(*) OVER w AS n, MIN(y) OVER w AS y0, n_units
                           FROM (SELECT *, CAST(period AS INTEGER) AS y FROM ({side(ids)})
                                 WHERE regexp_full_match(period, '\\d{{4}}'))
                           WINDOW w AS (PARTITION BY unit_id, level ORDER BY y ROWS BETWEEN {k - 1} PRECEDING AND CURRENT ROW)"""
            derived.append(f"""
                SELECT a.unit_id, a.level, '{m["id"]}' AS metric_id,
                       CAST(a.y - {k - 1} AS VARCHAR) || '-' || CAST(a.y AS VARCHAR) AS period,
                       a.s / NULLIF(b.s, 0) * {f} AS value, 'ok' AS status,
                       {PREC_OF.format(x='GREATEST(a.p, b.p)')} AS precision, 'derived' AS provenance,
                       a.n_units, 0 AS n_missing,
                       CASE WHEN GREATEST(a.nat, b.nat) = 1 THEN 'computed from published values (municipal values incomplete)'
                            WHEN GREATEST(a.est, b.est) = 1 THEN '{EST_DERIVED}' END AS note
                FROM ({win(num)}) a JOIN ({win(den)}) b
                  ON a.unit_id = b.unit_id AND a.level = b.level AND b.y = a.y - {lag}
                WHERE a.n = {k} AND b.n = {k} AND a.y - a.y0 = {k - 1} AND b.y - b.y0 = {k - 1}
                  AND b.s IS NOT NULL AND b.s <> 0 AND a.n_real > 0""")
        elif (c := CHANGE.match(agg)):
            base, n = c["m"], int(c["n"])
            derived.append(f"""
                SELECT a.unit_id, a.level, '{m["id"]}' AS metric_id, a.period,
                       (a.value / NULLIF(b.value, 0) - 1) * 100 AS value, 'ok' AS status,
                       a.precision, 'derived' AS provenance, a.n_units, 0 AS n_missing,
                       CASE WHEN a.note LIKE 'estimate:%' OR b.note LIKE 'estimate:%' THEN '{EST_DERIVED}' END AS note
                FROM base_all a JOIN base_all b
                  ON a.unit_id = b.unit_id AND a.level = b.level AND b.metric_id = '{base}'
                 AND regexp_full_match(a.period, '\\d{{4}}') AND regexp_full_match(b.period, '\\d{{4}}')
                 AND CAST(b.period AS INTEGER) = CAST(a.period AS INTEGER) - {n}
                WHERE a.metric_id = '{base}' AND a.status = 'ok' AND b.status = 'ok' AND b.value <> 0""")
    out = interim_path("metrics_all.parquet")
    cols = "unit_id, level, metric_id, period, value, status, precision, provenance, n_units, n_missing, note"
    con.execute(f"CREATE TABLE der AS SELECT {cols} FROM base_all WHERE false")
    for d in derived:
        con.execute(f"INSERT INTO der SELECT {cols} FROM ({d})")
    for mid, ids in gap_list:
        con.execute(f"INSERT INTO der SELECT {cols} FROM ({gaps(mid, ids)})")
    if has_nrw:  # D37: single-seat cantons (majority election) in party shares, blocs and leaning
        print("D37 majority election:", elections.apply_majority(
            con, meta, [l for l in AGG_LEVELS if l not in ("bezirk", "kanton", "schweiz")], elections.majority_cantons()))
    con.execute(f"COPY (SELECT {cols} FROM base_all UNION ALL SELECT {cols} FROM der) "
                f"TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.close()
    return str(out)


if __name__ == "__main__":
    print(run())
