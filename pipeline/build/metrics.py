"""Compute derived metrics and aggregate to every spatial level (brief 4.2 / 4.3), in DuckDB.

Input:  data/interim/observation.parquet (from pipeline.harmonize.run) and all metrics.yaml
Output: data/interim/metrics_all.parquet with columns
        unit_id, level, metric_id, period, value, status, precision, provenance, n_units, n_missing, note

Rules
- Base metrics with aggregation 'sum' are summed from municipalities to every level. A unit gets a
  value only if all its municipalities have one (else status 'no_data' with n_missing > 0).
- 'weighted_mean:<w>' uses metric <w> of the same period as weight.
- 'not_aggregatable' stays at its native level.
- Optional metrics.yaml key `zero_when: [<status>, ...]` on a base metric: rows with one of these
  statuses count as 0 in sums and in ratio terms (e.g. a party that did not stand; a municipality
  counted with a neighbour whose figures include its votes). The row itself keeps its status.
- Derived 'ratio:<a>[+<b>...]/<c>[+...][*<factor>]' and 'change:<metric>:<years>' are computed at every
  level from that level's base values, so ratios are re-computed, never averaged.
- Rows the sources publish at higher levels ('native') are not used for aggregation; they are kept
  in observation.parquet for the plausibility sweep (pipeline.build.quality). Base metrics whose
  native level is above the municipality (e.g. district survey values) are passed through.
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
RATIO = re.compile(r"^ratio:(?P<num>[^/]+)/(?P<den>[^*]+)(?:\*(?P<f>[\d.]+))?$")
CHANGE = re.compile(r"^change:(?P<m>[a-z0-9_]+):(?P<n>\d+)$")
PREC_RANK = "CASE precision WHEN 'exact' THEN 0 WHEN 'survey' THEN 1 WHEN 'modelled' THEN 2 ELSE 3 END"
PREC_NAME = "CASE MAX({r}) WHEN 0 THEN 'exact' WHEN 1 THEN 'survey' WHEN 2 THEN 'modelled' ELSE 'boundary_estimate' END"


def _terms(expr: str) -> list[str]:
    return [t.strip() for t in expr.split("+") if t.strip()]


def _q(ids) -> str:
    return ", ".join("'" + i.replace("'", "''") + "'" for i in ids)


def run() -> str:
    meta = load_metrics().drop_duplicates("id")
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
    # base metrics published natively above municipality level (passed through)
    con.execute(f"""
        CREATE TABLE native_only AS
        SELECT o.unit_id, o.level, o.metric_id, o.period, o.value, o.status, o.precision, o.provenance,
               1 AS n_units, CASE WHEN o.status = 'ok' THEN 0 ELSE 1 END AS n_missing, o.note
        FROM read_parquet('{obs}') o JOIN meta m ON o.metric_id = m.id
        WHERE m.kind = 'base' AND m.native_level <> 'gemeinde' AND o.level NOT IN ('gemeinde', 'unallocated', 'pseudo')""")

    # aggregation input: zero_when statuses count as 0
    con.execute("""
        CREATE TABLE gem_sum AS
        SELECT g.unit_id, g.metric_id, g.period,
               CASE WHEN g.value IS NULL AND z.metric_id IS NOT NULL THEN 0 ELSE g.value END AS value,
               g.precision
        FROM gem g LEFT JOIN zw z ON g.metric_id = z.metric_id AND g.status = z.status""")

    parts = ["""SELECT unit_id, 'gemeinde' AS level, metric_id, period, value, status, precision, provenance,
                       1 AS n_units, CASE WHEN status = 'ok' THEN 0 ELSE 1 END AS n_missing, note FROM gem"""]
    sums = meta.loc[(meta["kind"] == "base") & (meta["aggregation"] == "sum"), "id"].tolist()
    wmeans = {r["id"]: r["aggregation"].split(":", 1)[1] for r in meta.to_dict("records")
              if r["kind"] == "base" and str(r["aggregation"]).startswith("weighted_mean:")}
    for lvl in AGG_LEVELS:
        con.execute(f"""CREATE TABLE n_{lvl} AS SELECT {lvl} AS u, COUNT(*) AS n FROM mem
                        WHERE {lvl} IS NOT NULL AND {lvl} NOT IN ('nan', '<NA>', 'None') GROUP BY 1""")
        parts.append(f"""
            SELECT g.u AS unit_id, '{lvl}' AS level, g.metric_id, g.period,
                   CASE WHEN g.n_with = n.n THEN g.s END AS value,
                   CASE WHEN g.n_with = n.n THEN 'ok' ELSE 'no_data' END AS status,
                   g.precision, 'aggregated' AS provenance, n.n AS n_units, n.n - g.n_with AS n_missing,
                   NULL AS note
            FROM (SELECT m.{lvl} AS u, gem.metric_id, gem.period, SUM(gem.value) AS s,
                         COUNT(gem.value) AS n_with, {PREC_NAME.format(r=PREC_RANK)} AS precision
                  FROM gem_sum gem JOIN mem m USING (unit_id)
                  WHERE gem.metric_id IN ({_q(sums)}) AND m.{lvl} NOT IN ('nan', '<NA>', 'None')
                  GROUP BY 1, 2, 3) g JOIN n_{lvl} n ON g.u = n.u""")
        for mid, w in wmeans.items():
            parts.append(f"""
                SELECT g.u AS unit_id, '{lvl}' AS level, '{mid}' AS metric_id, g.period,
                       CASE WHEN g.n_with = n.n AND g.w > 0 THEN g.vw / g.w END AS value,
                       CASE WHEN g.n_with = n.n AND g.w > 0 THEN 'ok' ELSE 'no_data' END AS status,
                       g.precision, 'aggregated' AS provenance, n.n AS n_units, n.n - g.n_with AS n_missing,
                       NULL AS note
                FROM (SELECT m.{lvl} AS u, v.period, SUM(v.value * w.value) AS vw,
                             SUM(CASE WHEN v.value IS NOT NULL THEN w.value END) AS w,
                             COUNT(v.value) AS n_with, {PREC_NAME.format(r='CASE v.precision WHEN \'exact\' THEN 0 WHEN \'survey\' THEN 1 WHEN \'modelled\' THEN 2 ELSE 3 END')} AS precision
                      FROM gem v JOIN gem w ON v.unit_id = w.unit_id AND v.period = w.period
                           AND w.metric_id = '{w}'
                      JOIN mem m ON v.unit_id = m.unit_id
                      WHERE v.metric_id = '{mid}' AND m.{lvl} NOT IN ('nan', '<NA>', 'None')
                      GROUP BY 1, 2) g JOIN n_{lvl} n ON g.u = n.u""")
    parts.append("SELECT * FROM native_only")
    con.execute("CREATE TABLE base_all AS " + " UNION ALL ".join(parts))
    # ratio inputs: usable base rows (ok, or a zero_when status counted as 0), materialized once
    con.execute(f"""
        CREATE TABLE base_terms AS
        SELECT b.unit_id, b.level, b.metric_id, b.period, COALESCE(b.value, 0) AS value, b.precision, b.n_units
        FROM base_all b LEFT JOIN zw z ON b.metric_id = z.metric_id AND b.status = z.status
        WHERE b.status = 'ok' OR z.metric_id IS NOT NULL""")

    # derived metrics, computed at every level from that level's base values
    derived = []
    for m in meta[meta["kind"] == "derived"].to_dict("records"):
        agg = str(m["aggregation"])
        if (r := RATIO.match(agg)):
            num, den = _terms(r["num"]), _terms(r["den"])
            f = float(r["f"]) if r["f"] else 1.0
            derived.append(f"""
                SELECT a.unit_id, a.level, '{m["id"]}' AS metric_id, a.period,
                       a.s / NULLIF(b.s, 0) * {f} AS value, 'ok' AS status,
                       CASE WHEN GREATEST(a.p, b.p) = 0 THEN 'exact' WHEN GREATEST(a.p, b.p) = 1 THEN 'survey'
                            WHEN GREATEST(a.p, b.p) = 2 THEN 'modelled' ELSE 'boundary_estimate' END AS precision,
                       'derived' AS provenance, a.n_units, 0 AS n_missing, NULL AS note
                FROM (SELECT unit_id, level, period, SUM(value) AS s, MAX({PREC_RANK}) AS p, MAX(n_units) AS n_units
                      FROM base_terms WHERE metric_id IN ({_q(num)})
                      GROUP BY 1, 2, 3 HAVING COUNT(DISTINCT metric_id) = {len(set(num))}) a
                JOIN (SELECT unit_id, level, period, SUM(value) AS s, MAX({PREC_RANK}) AS p
                      FROM base_terms WHERE metric_id IN ({_q(den)})
                      GROUP BY 1, 2, 3 HAVING COUNT(DISTINCT metric_id) = {len(set(den))}) b
                USING (unit_id, level, period)
                WHERE b.s IS NOT NULL AND b.s <> 0""")
        elif (c := CHANGE.match(agg)):
            base, n = c["m"], int(c["n"])
            derived.append(f"""
                SELECT a.unit_id, a.level, '{m["id"]}' AS metric_id, a.period,
                       (a.value / NULLIF(b.value, 0) - 1) * 100 AS value, 'ok' AS status,
                       a.precision, 'derived' AS provenance, a.n_units, 0 AS n_missing, NULL AS note
                FROM base_all a JOIN base_all b
                  ON a.unit_id = b.unit_id AND a.level = b.level AND b.metric_id = '{base}'
                 AND regexp_full_match(a.period, '\\d{{4}}') AND regexp_full_match(b.period, '\\d{{4}}')
                 AND CAST(b.period AS INTEGER) = CAST(a.period AS INTEGER) - {n}
                WHERE a.metric_id = '{base}' AND a.status = 'ok' AND b.status = 'ok' AND b.value <> 0""")
    out = interim_path("metrics_all.parquet")
    union = "SELECT * FROM base_all" + "".join(f" UNION ALL ({d})" for d in derived)
    con.execute(f"COPY ({union}) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.close()
    return str(out)


if __name__ == "__main__":
    print(run())
