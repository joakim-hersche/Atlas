"""votes/index.json for the vote picker (review round 1, defect 4 / D32), see docs/web_data_contract.md §5.

National result: yes / (yes + no) and ballots / eligible, summed over all municipalities plus the
pseudo-units (Swiss abroad, postal and other votes; D17) — the aggregated 'schweiz' rows of
metrics_all, which pipeline.build.metrics builds with include_pseudo (the same counting as BFS).
Canton results and the Ständemehr use the canton results as BFS publishes them for the canton
territory at the vote date (provenance native): a canton accepts when yes > no; full cantons count 1,
the six half-cantons (OW, NW, BS, BL, AR, AI) ½. Before 1979 there is no canton Jura (22 votes
in total), from 1979 23. Whether a double majority was required is not derived; `accepted` is the
official outcome from voteinfo (1981+) where known.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from pipeline.common import interim_path
from pipeline.harmonize.schema import SOURCES_DIR

HALF = ["OW", "NW", "BS", "BL", "AR", "AI"]
SOURCE = "bfs_votes_gemeinde"


def _r(v, d=2):
    return None if v is None or v != v else round(float(v), d)


def staende(canton: pd.DataFrame) -> tuple[float, float, float]:
    """canton: rows with kanton, yes, no -> (cantons yes, cantons no, total) in Standesstimmen."""
    w = canton["kanton"].map(lambda k: 0.5 if k in HALF else 1.0)
    acc = canton["yes"] > canton["no"]
    return float(w[acc].sum()), float(w[~acc].sum()), float(w.sum())


def build_index(con, titles: dict) -> dict:
    obs = interim_path("observation.parquet")
    nat = con.execute(f"""
        SELECT period, unit_id AS kanton, metric_id, value FROM read_parquet('{obs}')
        WHERE source_id = '{SOURCE}' AND level = 'kanton' AND provenance = 'native' AND status = 'ok'
          AND metric_id IN ('vote_yes', 'vote_no')""").df()
    kt = nat.pivot_table(index=["period", "kanton"], columns="metric_id", values="value").reset_index()
    kt = kt.rename(columns={"vote_yes": "yes", "vote_no": "no"})
    ch = con.execute("""SELECT period, metric_id, value FROM m WHERE level = 'schweiz' AND status = 'ok'
                        AND metric_id IN ('vote_yes', 'vote_no', 'vote_eligible', 'vote_ballots')""").df()
    ch = ch.pivot_table(index="period", columns="metric_id", values="value")
    v = pd.read_csv(SOURCES_DIR / SOURCE / "vorlagen.csv", dtype=str)
    v["period"] = v["date"] + "#" + v["vorlagen_id"]
    meta = v.set_index("period")
    cantons = sorted(set(kt["kanton"]), key=lambda k: ["ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR",
                                                        "SO", "BS", "BL", "SH", "AR", "AI", "SG", "GR", "AG", "TG",
                                                        "TI", "VD", "VS", "NE", "GE", "JU"].index(k))
    votes = []
    for per in sorted(set(ch.index) | set(kt["period"]), key=lambda p: (p[:10], int(p.split("#")[1]))):
        c = kt[kt["period"] == per]
        by = c.set_index("kanton")
        y_, n_, tot = staende(c) if len(c) else (None, None, None)
        r = ch.loc[per] if per in ch.index else None
        m = meta.loc[per] if per in meta.index else None
        yes, no = (r.get("vote_yes"), r.get("vote_no")) if r is not None else (None, None)
        votes.append({
            "id": per.split("#")[1], "period": per, "date": per[:10],
            "title": titles.get(per) or {},
            "title_source": None if m is None else m.get("title_source"),
            "yes_pct": _r(yes / (yes + no) * 100) if yes is not None and (yes + no) else None,
            "turnout_pct": _r(r["vote_ballots"] / r["vote_eligible"] * 100)
            if r is not None and r.get("vote_eligible") else None,
            "yes": None if yes is None else int(yes), "no": None if no is None else int(no),
            "accepted": None if m is None or not isinstance(m.get("accepted"), str) else m["accepted"] == "true",
            "cantons_yes": y_, "cantons_no": n_, "cantons_total": tot,
            "canton_yes_pct": [_r(by.loc[k, "yes"] / (by.loc[k, "yes"] + by.loc[k, "no"]) * 100)
                               if k in by.index and (by.loc[k, "yes"] + by.loc[k, "no"]) else None for k in cantons],
            "provisional": bool(m is not None and str(m.get("provisional")) == "true"),
            "file": "votes/" + per.replace("#", "_") + ".json",
        })
    return {"source": SOURCE, "generated": dt.date.today().isoformat(), "cantons": cantons, "half_cantons": HALF,
            "note": ("National values: yes/(yes+no) and ballots/eligible summed over municipalities and "
                     "pseudo-units (Swiss abroad, postal/other votes). Ständemehr: cantons with yes > no as "
                     "published for the canton territory at the vote date; half-cantons count ½."),
            "votes": votes}
