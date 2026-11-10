"""National Council rules applied inside the metrics build (decision D37), called by pipeline.build.metrics.

1. FDP and LPS (D37 rule 3): from 2011, BFS counts LPS (e.g. LDP Basel-Stadt) under FDP in the national
   party strength (cube 104 CH; BFS statement "Berechnung der nationalen Parteistärken", DAM 30887041).
   ATLAS does the same at every level above the canton (Switzerland, major regions, language regions,
   agglomerations, typologies): nrw_fw_fdp += nrw_fw_lps and nrw_fw_lps becomes not_applicable there.
   Municipalities, districts and cantons keep LPS separate. Before 2011 LPS stays separate everywhere.

2. Majority-election cantons (D37 rule 2): cantons with a single National Council seat in an election
   year (BFS cube px-x-1702020000_103, seats = 1: UR, OW, NW, GL, AI since 1971, AR from 2003) elect by
   majority, so votes go to candidates, not party lists. For every derived metric with
   `majority_election: true` in metrics.yaml (party shares, blocs, leaning; not turnout):
   - municipality, district and canton rows of those canton-years get status `majority_election`
     (value kept, shown in the card, left out of classes, ranks and statistics by default);
   - regions and typologies (every level between canton and Switzerland) are recomputed from the
     municipalities of proportional cantons only, with a note saying so; a unit made only of
     single-seat cantons gets status `majority_election`;
   - Switzerland keeps all cantons, as BFS's national party strength does (cube 104: CH SVP 2023 =
     27.93 %), with a note. Fictitious-voter sums (nrw_fw_*) are not changed anywhere, so canton and
     national totals stay equal to cube 104.
"""
from __future__ import annotations

import pandas as pd

ABOVE_KANTON_FROM = 2011
LPS_NOTE = "from 2011 counted under FDP above canton level, as in BFS's national party strength"
MAJ_NOTE = ("majority election (single-seat canton): votes for candidates, not party lists; "
            "not comparable with proportional cantons")
MAJ_REGION_ONLY = ("only single-seat cantons (majority election): votes for candidates, not party lists; "
                   "not comparable with proportional cantons")
CH_NOTE = "includes the single-seat (majority-election) cantons, as BFS's national party strength"
PARTY_PREFIX = "nrw_fw_"


def _sql(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def majority_cantons() -> dict[str, list[str]]:
    """Election year -> cantons with one seat (BFS cube 103). Fails loudly: the build must not skip D37."""
    from pipeline.sources.bfs_nrw.fetch import majority_cantons as mc
    return mc()


def _register_majority(con, majority: dict[str, list[str]]) -> None:
    rows = [(kt, y) for y, kts in majority.items() for kt in kts]
    con.register("maj_df", pd.DataFrame(rows or [("", "")], columns=["kanton", "period"]))
    con.execute("CREATE OR REPLACE TABLE maj AS SELECT * FROM maj_df")


def merge_lps(con) -> int:
    """Rule 1 on base_all (before ratios are computed). Returns the number of FDP rows changed."""
    above = "level NOT IN ('gemeinde', 'bezirk', 'kanton', 'pseudo', 'unallocated')"
    yr = f"TRY_CAST(substr(period, 1, 4) AS INTEGER) >= {ABOVE_KANTON_FROM}"
    con.execute(f"""CREATE OR REPLACE TEMP TABLE lps_add AS
        SELECT unit_id, level, period, value FROM base_all
        WHERE metric_id = 'nrw_fw_lps' AND {above} AND {yr} AND status = 'ok'""")
    n = con.execute("""SELECT COUNT(*) FROM base_all b JOIN lps_add l USING (unit_id, level, period)
                       WHERE b.metric_id = 'nrw_fw_fdp' AND b.status = 'ok' AND b.provenance = 'aggregated'""").fetchone()[0]
    con.execute("""UPDATE base_all SET value = base_all.value + l.value FROM lps_add l
                   WHERE base_all.metric_id = 'nrw_fw_fdp' AND base_all.status = 'ok'
                     AND base_all.provenance = 'aggregated' AND base_all.unit_id = l.unit_id
                     AND base_all.level = l.level AND base_all.period = l.period""")
    con.execute(f"""UPDATE base_all SET value = NULL, status = 'not_applicable', note = {_sql(LPS_NOTE)}
                    WHERE metric_id = 'nrw_fw_lps' AND {above} AND {yr}""")
    return int(n)


def apply_majority(con, meta: pd.DataFrame, region_levels: list[str], majority: dict[str, list[str]]) -> dict:
    """Rule 2 on the derived table `der` (after ratios). Needs tables mem, gem_sum, ps, der."""
    from pipeline.build.metrics import RATIO, _q, _terms
    _register_majority(con, majority)
    flag = meta.get("majority_election")
    ids = meta.loc[flag.fillna(False).astype(bool), "id"].tolist() if flag is not None else []
    if not ids:
        return {}
    q = _q(ids)
    stats = {}
    # municipality, district, canton rows of single-seat canton-years: status majority_election, value kept
    for lvl, src in (("gemeinde", "SELECT DISTINCT m.unit_id AS u, j.period FROM mem m JOIN maj j ON m.kanton = j.kanton"),
                     ("bezirk", "SELECT DISTINCT m.bezirk AS u, j.period FROM mem m JOIN maj j ON m.kanton = j.kanton"),
                     ("kanton", "SELECT kanton AS u, period FROM maj")):
        stats[lvl] = con.execute(f"""SELECT COUNT(*) FROM der d JOIN ({src}) k ON d.unit_id = k.u AND d.period = k.period
                                     WHERE d.level = '{lvl}' AND d.metric_id IN ({q}) AND d.status = 'ok'""").fetchone()[0]
        con.execute(f"""UPDATE der SET status = 'majority_election', note = {_sql(MAJ_NOTE)} FROM ({src}) k
                        WHERE der.level = '{lvl}' AND der.metric_id IN ({q}) AND der.status = 'ok'
                          AND der.unit_id = k.u AND der.period = k.period""")
    con.execute(f"""UPDATE der SET note = {_sql(CH_NOTE)} WHERE level = 'schweiz' AND metric_id IN ({q})
                    AND status = 'ok' AND period IN (SELECT DISTINCT period FROM maj)""")

    # regions and typologies: proportional cantons only
    formulas = {}
    for r in meta[meta["id"].isin(ids)].to_dict("records"):
        m = RATIO.match(str(r["aggregation"]))
        if m:
            formulas[r["id"]] = (_terms(m["num"]), _terms(m["den"]), float(m["f"]) if m["f"] else 1.0)
    kt_gr = con.execute("SELECT DISTINCT kanton, grossregion FROM mem").df()
    out = []
    for lvl in region_levels:
        pm = con.execute(f"""
            SELECT m.{lvl} AS unit_id, g.metric_id, g.period, SUM(g.value) AS s, COUNT(g.value) AS n_with,
                   COUNT(*) FILTER (WHERE g.real) AS n_real
            FROM gem_sum g JOIN mem m USING (unit_id)
            LEFT JOIN maj j ON j.kanton = m.kanton AND j.period = g.period
            WHERE starts_with(g.metric_id, '{PARTY_PREFIX}') AND j.kanton IS NULL
              AND m.{lvl} NOT IN ('nan', '<NA>', 'None')
            GROUP BY 1, 2, 3""").df()
        cnt = con.execute(f"""
            SELECT m.{lvl} AS unit_id, p.period, COUNT(*) FILTER (WHERE j.kanton IS NULL) AS n_prop,
                   COUNT(*) FILTER (WHERE j.kanton IS NOT NULL) AS n_maj, COUNT(*) AS n,
                   string_agg(DISTINCT j.kanton, ', ' ORDER BY j.kanton) AS kts
            FROM mem m CROSS JOIN (SELECT DISTINCT period FROM maj) p
            LEFT JOIN maj j ON j.kanton = m.kanton AND j.period = p.period
            WHERE m.{lvl} NOT IN ('nan', '<NA>', 'None') GROUP BY 1, 2""").df()
        cnt = cnt[cnt["n_maj"] > 0]
        if cnt.empty:
            continue
        mun_tot = pm[pm["metric_id"] == "nrw_fw_total"].set_index(["unit_id", "period"])["s"].copy()
        if lvl == "grossregion":   # Swiss abroad / postal voting of proportional cantons (include_pseudo)
            ps = con.execute(f"""SELECT u AS kanton, metric_id, period, value FROM ps
                                 WHERE lvl = 'kanton' AND starts_with(metric_id, '{PARTY_PREFIX}')""").df()
            ps = ps.merge(kt_gr, on="kanton")
            ps = ps[~ps.apply(lambda r: r["kanton"] in set(majority.get(str(r["period"])[:4], [])), axis=1)]
            add = ps.groupby(["grossregion", "metric_id", "period"])["value"].sum().rename("ps").reset_index()
            pm = pm.merge(add.rename(columns={"grossregion": "unit_id"}), on=["unit_id", "metric_id", "period"], how="left")
            pm["s"] = pm["s"].fillna(0) + pm["ps"].fillna(0)
        # share of fictitious voters in single-seat cantons (for the note)
        tot_all = con.execute(f"""SELECT m.{lvl} AS unit_id, g.period, SUM(g.value) AS s_all FROM gem_sum g
                                  JOIN mem m USING (unit_id) WHERE g.metric_id = 'nrw_fw_total'
                                  AND m.{lvl} NOT IN ('nan', '<NA>', 'None') GROUP BY 1, 2""").df()
        w = pm.pivot_table(index=["unit_id", "period"], columns="metric_id", values="s", aggfunc="first")
        nw = pm.pivot_table(index=["unit_id", "period"], columns="metric_id", values="n_with", aggfunc="first")
        nr = pm.pivot_table(index=["unit_id", "period"], columns="metric_id", values="n_real", aggfunc="first")
        yr = w.index.get_level_values("period").str[:4].astype(int)
        if "nrw_fw_lps" in w and "nrw_fw_fdp" in w:   # rule 1 above canton level
            late = yr >= ABOVE_KANTON_FROM
            w.loc[late, "nrw_fw_fdp"] = w.loc[late, "nrw_fw_fdp"] + w.loc[late, "nrw_fw_lps"].fillna(0)
            nr.loc[late, "nrw_fw_fdp"] = nr.loc[late, "nrw_fw_fdp"] + nr.loc[late, "nrw_fw_lps"].fillna(0)
            w.loc[late, "nrw_fw_lps"] = 0.0
            nr.loc[late, "nrw_fw_lps"] = 0
        c = cnt.set_index(["unit_id", "period"])
        ta = tot_all.set_index(["unit_id", "period"])["s_all"]
        for (u, per), cr in c.iterrows():
            maj_share = None
            if (u, per) in mun_tot.index and (u, per) in ta.index and ta[(u, per)]:
                maj_share = 100 * (1 - mun_tot[(u, per)] / ta[(u, per)])
            for mid, (num, den, f) in formulas.items():
                if cr["n_prop"] == 0:
                    out.append((u, lvl, mid, per, None, "majority_election", MAJ_REGION_ONLY, True))
                    continue
                note = (f"proportional-representation cantons only: excludes {int(cr['n_maj'])} of {int(cr['n'])} "
                        f"municipalities in single-seat cantons ({cr['kts']}"
                        + (f"; {maj_share:.1f} % of fictitious voters" if maj_share is not None else "") + ")")
                terms = num + den
                if (u, per) not in w.index or any(t not in w.columns for t in terms):
                    out.append((u, lvl, mid, per, None, "no_data", note, False))
                    continue
                row_w, row_n, row_r = w.loc[(u, per)], nw.loc[(u, per)], nr.loc[(u, per)]
                complete = all(row_n.get(t, 0) == cr["n_prop"] for t in terms)
                a = sum(row_w[t] for t in num)
                b = sum(row_w[t] for t in den)
                ra = sum(row_r[t] for t in num)
                rb = sum(row_r[t] for t in den)
                if complete and rb == 0:   # the proportional cantons held no vote (tacit election)
                    out.append((u, lvl, mid, per, None, "majority_election", MAJ_REGION_ONLY, True))
                elif not complete or not b or rb == 0:
                    out.append((u, lvl, mid, per, None, "no_data", note, False))
                elif ra == 0:
                    out.append((u, lvl, mid, per, None, "not_applicable", "party did not stand; " + note, False))
                else:
                    out.append((u, lvl, mid, per, a / b * f, "ok", note, False))
    if out:
        df = pd.DataFrame(out, columns=["unit_id", "level", "metric_id", "period", "value", "status", "note", "keep"])
        con.register("prop_df", df)
        # a unit made only of single-seat cantons keeps its value under status majority_election; where its
        # own computation is a gap (party did not stand there) the gap and its reason stay
        con.execute("""UPDATE der SET value = CASE WHEN p.keep THEN der.value ELSE p.value END,
                                      status = CASE WHEN p.keep AND der.status <> 'ok' THEN der.status ELSE p.status END,
                                      note = CASE WHEN p.keep AND der.status <> 'ok' THEN der.note ELSE p.note END,
                                      provenance = 'derived'
                       FROM prop_df p WHERE der.unit_id = p.unit_id AND der.level = p.level
                         AND der.metric_id = p.metric_id AND der.period = p.period""")
        stats["regions"] = len(df)
        stats["regions_majority_only"] = int(df["keep"].sum())
    return stats
