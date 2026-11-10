"""Backbone validation (brief section 4, "Validation (must pass)") -> docs/backbone_report.md.

Checks
  R1  register snapshot at the reference date: number of municipalities vs. API snapshot
  R2  every current municipality has geometry (G1 historized boundaries, swissBOUNDARIES3D)
  C1  crosswalk weights sum to 1 for every version that maps to the target state
  C2  crosswalk vs. the official BFS correspondence table 1960 -> reference date (target sets)
  C3  versions that do not reach the target state (dead ends), with reasons
  T1  population totals: STATPOP per-year municipality files (each year on its own state, keyed by
      histId) reprojected to the reference state; national and canton totals vs. the unprojected
      totals, and per municipality vs. BFS's own re-projection (PxWeb px-x-0102010000_101)
"""
from __future__ import annotations

import datetime as dt

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.backbone.vintage import crosswalk, to_vintage
from pipeline.common import REFERENCE_DATE, ROOT, interim_path
from pipeline.sources.bfs_agvch.fetch import fetch_all as fetch_agvch
from pipeline.sources.bfs_hist_boundaries.fetch import fetch_all as fetch_bounds
from pipeline.sources.bfs_pxweb.fetch import metadata, parse_geo_label, query
from pipeline.sources.bfs_statpop_geodata.fetch import FIRST_LV95_YEAR, LAST_YEAR, municipalities

TOL_ABS = 0.5  # persons; reprojection of counts must be exact up to float rounding


def check_register(mv: pd.DataFrame) -> dict:
    snap = pd.read_csv(fetch_agvch()["snapshot"], dtype=str, encoding="utf-8-sig")
    n_api = int((snap["Level"] == "3").sum())
    cur = versions_at(mv, REFERENCE_DATE)
    return {"n_register": len(cur), "n_api_snapshot": n_api, "pass": len(cur) == n_api}


def check_geometry(mv: pd.DataFrame) -> dict:
    g1 = gpd.read_file(fetch_bounds()["g1"], ignore_geometry=True)
    cur = versions_at(mv, REFERENCE_DATE)
    have = set(g1.loc[g1["GARTE"] == 11, "GDEHISTID"].astype(int))
    missing = cur[~cur["hist_id"].isin(have)]
    return {"n_current": len(cur), "n_missing_geometry": len(missing),
            "missing": missing[["hist_id", "bfs_nr", "name"]].to_dict("records"),
            "pass": missing.empty}


def check_weights(cw: pd.DataFrame) -> dict:
    s = cw.groupby("from_hist_id")["weight"].sum()
    bad = s[(s - 1).abs() > 1e-6]
    return {"n_versions_mapped": int(s.size), "n_bad_sums": int(bad.size),
            "bad": bad.head(20).to_dict(), "pass": bad.empty,
            "by_source": cw.drop_duplicates("from_hist_id")["weight_source"].value_counts().to_dict()}


def check_official_correspondence(cw: pd.DataFrame, mv: pd.DataFrame) -> dict:
    off = pd.read_csv(fetch_agvch()["correspondences_1960"], dtype=str, encoding="utf-8-sig")
    off = off.astype({"InitialHistoricalCode": int, "TerminalHistoricalCode": int})
    start = versions_at(mv, dt.date(1960, 1, 1))
    off = off[off["InitialHistoricalCode"].isin(start["hist_id"])]
    o = off.groupby("InitialHistoricalCode")["TerminalHistoricalCode"].apply(set)
    ours = cw[cw["from_hist_id"].isin(o.index)].groupby("from_hist_id")["to_hist_id"].apply(set)
    both = o.index.intersection(ours.index)
    diff = [(h, sorted(o[h]), sorted(ours[h])) for h in both if o[h] != ours[h]]
    only_off = sorted(set(o.index) - set(ours.index))
    return {"n_1960_versions": int(o.size), "n_agree": int(len(both) - len(diff)),
            "n_differ": len(diff), "differ": diff[:30], "n_missing_in_ours": len(only_off),
            "missing_in_ours": only_off[:30], "pass": not diff and not only_off}


def check_dead_ends(cw: pd.DataFrame, mv: pd.DataFrame) -> dict:
    mun = mv[mv["entry_mode"] == "11"]
    dead = mun[~mun["hist_id"].isin(cw["from_hist_id"])]
    return {"n_dead_ends": len(dead),
            "dead_ends": dead[["hist_id", "bfs_nr", "name", "canton", "valid_from", "valid_to",
                               "abolition_type"]].astype(str).to_dict("records")[:50]}


def statpop_per_year() -> pd.DataFrame:
    rows = []
    for y in range(FIRST_LV95_YEAR, LAST_YEAR + 1):
        d = pd.read_parquet(municipalities(y))
        hcol = "GDEHISTID" if "GDEHISTID" in d.columns else "GDE_HISTID"
        rows.append(pd.DataFrame({"year": y, "hist_id": d[hcol].astype("int64"),
                                  "bfs_nr": d["GDENR"].astype("int64"),
                                  "value": d["BBTOT"].astype(float)}))
    return pd.concat(rows, ignore_index=True)


def statpop_bfs_reprojected() -> tuple[pd.DataFrame, str]:
    dbid = "px-x-0102010000_101"
    meta = metadata(dbid)
    geo = next(v for v in meta["variables"] if v["code"] not in ("Jahr",) and len(v["values"]) > 2000)
    year = next(v for v in meta["variables"] if v["code"] == "Jahr")
    df = query(dbid, {geo["code"]: "*", year["code"]: "*"})
    gcol = df.columns[1]
    parsed = df[gcol].map(parse_geo_label)
    df = df.assign(level=[p[0] for p in parsed], bfs_nr=[p[1] for p in parsed])
    df = df[df["level"] == "gemeinde"]
    val = [c for c in df.columns if c not in ("level", "bfs_nr")][-1]  # value is the last column
    out = pd.DataFrame({"year": df["Jahr"].astype(int), "bfs_nr": df["bfs_nr"].astype(int),
                        "value": pd.to_numeric(df[val], errors="coerce")})
    return out, geo["text"]


def check_population_totals(mv: pd.DataFrame) -> dict:
    sp = statpop_per_year()
    res = {"years": [], "pass": True}
    reproj = []
    for y, g in sp.groupby("year"):
        # rows carry hist_id, so no source date is needed to resolve them
        r, unm = to_vintage(g[["hist_id", "value"]], source_vintage=None, rule="sum",
                            return_unmapped=True)
        nat_src, nat_tgt = g["value"].sum(), r["value"].sum()
        ok = abs(nat_src - nat_tgt) <= TOL_ABS
        res["years"].append({"year": int(y), "national_source": float(nat_src),
                             "national_reprojected": float(nat_tgt), "unmapped_rows": len(unm),
                             "pass": bool(ok)})
        res["pass"] &= bool(ok)
        reproj.append(r.assign(year=y))
    rp = pd.concat(reproj)
    # canton totals: source (canton of the version at the time) vs target canton
    cur = versions_at(mv, REFERENCE_DATE).set_index("hist_id")["canton"]
    rp["canton"] = rp["hist_id"].map(cur)
    canton_t = rp.groupby(["year", "canton"])["value"].sum()
    allv = mv.set_index("hist_id")["canton"]
    sp["canton"] = sp["hist_id"].map(allv)
    canton_s = sp.groupby(["year", "canton"])["value"].sum()
    cdiff = (canton_t - canton_s).dropna()
    res["canton_diffs"] = {f"{y}-{k}": float(v) for (y, k), v in cdiff[cdiff.abs() > TOL_ABS].items()}
    # per municipality vs BFS re-projection (state 31.12.<latest>), itself mapped to the reference
    bfs, geo_text = statpop_bfs_reprojected()
    bfs_state = dt.date(LAST_YEAR, 12, 31)
    bfs_r = pd.concat([to_vintage(g[["bfs_nr", "value"]], source_vintage=bfs_state, rule="sum").assign(year=y)
                       for y, g in bfs.groupby("year")])
    cmp_ = rp.merge(bfs_r, on=["year", "hist_id"], suffixes=("_ours", "_bfs"), how="outer")
    cmp_["diff"] = cmp_["value_ours"] - cmp_["value_bfs"]
    cmp_["rel"] = cmp_["diff"] / cmp_["value_bfs"]
    mism = cmp_[cmp_["diff"].abs() > TOL_ABS]
    names = versions_at(mv, REFERENCE_DATE).set_index("hist_id")["name"]
    by_mun = (mism.assign(name=mism["hist_id"].map(names), absdiff=mism["diff"].abs())
              .groupby(["hist_id", "name"])
              .agg(years=("year", "count"), max_abs=("absdiff", "max"),
                   max_rel=("rel", lambda s: s.abs().max())).reset_index()
              .sort_values("max_rel", ascending=False))
    res["bfs_compare_by_municipality"] = by_mun.astype(str).to_dict("records")
    res["bfs_compare"] = {
        "pxweb_geo_variable": geo_text,
        "n_comparisons": int(len(cmp_)),
        "n_exact": int((cmp_["diff"].abs() <= TOL_ABS).sum()),
        "n_differ": int(len(mism)),
        "max_abs_rel": float(mism["rel"].abs().max()) if len(mism) else 0.0,
        "worst": mism.reindex(mism["rel"].abs().sort_values(ascending=False).index)
                     .head(15)[["year", "hist_id", "bfs_nr_ours", "value_ours", "value_bfs", "rel"]]
                     .astype(str).to_dict("records") if len(mism) else [],
    }
    return res


VOTE_COLS = ["eligible", "ballots", "valid", "yes", "no"]


def check_votes(n_sample: int = 12) -> dict:
    """T2: reproject vote results from the state at the vote date to the reference state and
    compare with BFS's own re-aggregation, for a spread of vote dates 1981–latest."""
    from pipeline.sources.bfs_votes.fetch import fetch_vote, list_vote_assets, parse_vote
    assets = list_vote_assets()
    idx = np.unique(np.linspace(0, len(assets) - 1, n_sample).round().astype(int))
    sample = assets.iloc[idx]
    out = {"votes": [], "pass": True}
    for a in sample.itertuples():
        src, voge = parse_vote(fetch_vote(a.date, a.vote_date, "date"))
        ref, voge_ref = parse_vote(fetch_vote(a.current, a.vote_date, "current"))
        # 9xxx = pseudo-units (Swiss abroad, postal-vote districts); not municipalities
        n_pseudo = int((src["bfs_nr"] >= 9000).sum())
        src, ref = src[src["bfs_nr"] < 9000], ref[ref["bfs_nr"] < 9000]
        if voge_ref != REFERENCE_DATE.isoformat():
            out["votes"].append({"vote_date": a.vote_date, "skipped": f"BFS current state is {voge_ref}"})
            continue
        merged = None
        unm_rows = 0
        for col in VOTE_COLS:
            # vote results are reported per voting district (voge); some small municipalities are
            # counted with a neighbour and are absent from the file, so absence is not a gap here
            r, unm = to_vintage(src[["vorlagen_id", "bfs_nr", col]].rename(columns={col: "value"}),
                                source_vintage=dt.date.fromisoformat(voge), rule="sum",
                                group_cols=["vorlagen_id"], return_unmapped=True, strict_missing=False)
            unm_rows = max(unm_rows, len(unm))
            r = r[["vorlagen_id", "bfs_nr", "value"]].rename(columns={"value": col})
            merged = r if merged is None else merged.merge(r, on=["vorlagen_id", "bfs_nr"])
        cmp_ = merged.merge(ref[["vorlagen_id", "bfs_nr", *VOTE_COLS]], on=["vorlagen_id", "bfs_nr"],
                            suffixes=("_ours", "_bfs"), how="outer")
        diffs = {c: (cmp_[f"{c}_ours"] - cmp_[f"{c}_bfs"]).abs() for c in VOTE_COLS}
        n_rows = len(cmp_)
        exact = int((pd.concat(diffs, axis=1).fillna(np.inf) <= TOL_ABS).all(axis=1).sum())
        nat_ours = merged[["yes", "no"]].sum()
        worst = cmp_.assign(d=diffs["yes"]).sort_values("d", ascending=False).head(3)
        ok = abs(src["yes"].sum() - nat_ours["yes"]) <= TOL_ABS and unm_rows == 0
        out["pass"] &= bool(ok)
        out["votes"].append({
            "pass": bool(ok), "vote_date": a.vote_date, "source_state": voge, "n_vorlagen": int(src["vorlagen_id"].nunique()),
            "n_rows": n_rows, "n_exact": exact, "unmapped_source_rows": unm_rows, "pseudo_unit_rows": n_pseudo,
            "yes_src_total": float(src["yes"].sum()), "yes_reprojected_total": float(nat_ours["yes"]),
            "worst": worst[["vorlagen_id", "bfs_nr", "yes_ours", "yes_bfs"]].astype(str).to_dict("records"),
        })
    return out


def check_jobs(years=(2011, 2018, 2024)) -> dict:
    """T3: STATENT per-year files (own state, histId) reprojected; totals must be preserved."""
    from pipeline.sources.bfs_statent_geodata.fetch import municipalities as statent
    out = {"years": [], "pass": True}
    for y in years:
        d = pd.read_parquet(statent(y))
        hcol = "GDEHISTID" if "GDEHISTID" in d.columns else "GDE_HISTID"
        g = pd.DataFrame({"hist_id": d[hcol].astype("int64"), "value": d["B08EMPT"].astype(float)})
        r, unm = to_vintage(g, source_vintage=None, rule="sum", return_unmapped=True)
        ok = abs(g["value"].sum() - r["value"].sum()) <= TOL_ABS and len(unm) == 0
        out["pass"] &= bool(ok)
        out["years"].append({"year": y, "n_source": len(g), "n_target": len(r), "jobs_source": float(g["value"].sum()),
                             "jobs_reprojected": float(r["value"].sum()), "unmapped": len(unm), "pass": bool(ok)})
    return out


def write_report(results: dict) -> str:
    L = ["# Backbone validation report", "",
         f"Generated {dt.datetime.now().isoformat(timespec='minutes')} · reference state "
         f"**{REFERENCE_DATE.isoformat()}** · regenerate with `make validate`.", ""]

    def status(ok):
        return "PASS" if ok else "CHECK"
    r1, r2, c1, c2, c3, t1 = (results[k] for k in ("R1", "R2", "C1", "C2", "C3", "T1"))
    L += ["## Summary", "", "| Check | Result | Detail |", "|---|---|---|",
          f"| R1 register vs. API snapshot | {status(r1['pass'])} | {r1['n_register']} vs. {r1['n_api_snapshot']} municipalities |",
          f"| R2 geometry for every municipality | {status(r2['pass'])} | {r2['n_missing_geometry']} missing of {r2['n_current']} |",
          f"| C1 crosswalk weights sum to 1 | {status(c1['pass'])} | {c1['n_bad_sums']} bad of {c1['n_versions_mapped']} versions |",
          f"| C2 crosswalk vs. official BFS correspondence 1960→ref | {status(c2['pass'])} | {c2['n_agree']} agree, {c2['n_differ']} differ, {c2['n_missing_in_ours']} missing |",
          f"| C3 versions not reaching the reference state | info | {c3['n_dead_ends']} |",
          f"| T1 population totals preserved (2010–{LAST_YEAR}) | {status(t1['pass'])} | national totals per year; canton diffs listed below |",
          f"| T1b vs. BFS's own re-projection | info | {t1['bfs_compare']['n_exact']} of {t1['bfs_compare']['n_comparisons']} municipality-years identical |",
          ""]
    t2, t3 = results.get("T2"), results.get("T3")
    if t2:
        L.insert(len(L) - 1,
                 f"| T2 votes: reprojected vs. BFS re-aggregation ({len(t2['votes'])} vote dates) | {status(t2['pass'])} | "
                 f"{sum(v.get('n_exact', 0) for v in t2['votes'])} of {sum(v.get('n_rows', 0) for v in t2['votes'])} municipality-proposition rows identical |")
    if t3:
        L.insert(len(L) - 1, f"| T3 jobs (STATENT) totals preserved | {status(t3['pass'])} | years {', '.join(str(y['year']) for y in t3['years'])} |")
    L += ["## Crosswalk weight sources", "", "| Source | Versions |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in c1["by_source"].items()] + [""]
    L += ["## C2 differences vs. official correspondence", ""]
    L += [f"- {h}: official {o} · ours {u}" for h, o, u in c2["differ"]] or ["None."]
    L += ["", "## C3 versions without a successor in the reference state", ""]
    L += [f"- {d['hist_id']} {d['name']} ({d['canton']}, BFS {d['bfs_nr']}), valid {d['valid_from'][:10]}–{d['valid_to'][:10]}, {d['abolition_type']}"
          for d in c3["dead_ends"]] or ["None."]
    L += ["", "## T1 national population totals", "", "| Year | Source | Reprojected | Unmapped rows |", "|---|---|---|---|"]
    L += [f"| {y['year']} | {y['national_source']:,.0f} | {y['national_reprojected']:,.0f} | {y['unmapped_rows']} |" for y in t1["years"]]
    L += ["", "Canton totals that change through reprojection (expected only for canton changes such as Moutier BE→JU, 2026):", ""]
    L += [f"- {k}: {v:+,.0f}" for k, v in t1["canton_diffs"].items()] or ["None."]
    bc = t1["bfs_compare"]
    L += ["", "## T1b comparison with BFS's re-projected STATPOP (PxWeb px-x-0102010000_101)", "",
          f"{bc['n_exact']} of {bc['n_comparisons']} municipality-years identical; {bc['n_differ']} differ "
          f"(max relative difference {bc['max_abs_rel']:.2%}). Differences are expected only where splits or "
          "territory exchanges required weights (BFS's method is unpublished).", ""]
    if t1.get("bfs_compare_by_municipality"):
        L += ["Municipalities with differences (all years 2010–latest):", "",
              "| histId | Municipality | Years differing | Max abs. diff (persons) | Max rel. diff |",
              "|---|---|---|---|---|"]
        L += [f"| {m['hist_id']} | {m['name']} | {m['years']} | {float(m['max_abs']):.0f} | {float(m['max_rel']):.2%} |"
              for m in t1["bfs_compare_by_municipality"]]
    if t2:
        L += ["", "## T2 federal votes: our reprojection vs. BFS's re-aggregation", "",
              "Source: BFS JSON per vote on the municipality state of the vote date, reprojected with the "
              "crosswalk (sum of eligible voters, ballots, valid, yes, no), compared per municipality and "
              "proposition with BFS's file on the latest state. Pseudo-units (Swiss abroad, 9xxx) excluded.", "",
              "| Vote date | Source state | Propositions | Rows identical | Yes total (source → reprojected) | Pseudo-unit rows |",
              "|---|---|---|---|---|---|"]
        for v in t2["votes"]:
            if "skipped" in v:
                L.append(f"| {v['vote_date']} | – | – | skipped: {v['skipped']} | – | – |")
                continue
            L.append(f"| {v['vote_date']} | {v['source_state']} | {v['n_vorlagen']} | {v['n_exact']} / {v['n_rows']} | "
                     f"{v['yes_src_total']:,.0f} → {v['yes_reprojected_total']:,.0f} | {v['pseudo_unit_rows']} |")
    if t3:
        L += ["", "## T3 jobs (STATENT employees, B08EMPT)", "", "| Year | Source units | Target units | Source total | Reprojected | Unmapped |", "|---|---|---|---|---|---|"]
        L += [f"| {y['year']} | {y['n_source']} | {y['n_target']} | {y['jobs_source']:,.0f} | {y['jobs_reprojected']:,.0f} | {y['unmapped']} |" for y in t3["years"]]
    L += ["", "## Notes", "",
          "- Versions from 1848–1849 have no geometry (the boundary series starts in 1850); their few "
          "splits use equal shares (`equal_no_geometry`). No dataset in the catalog is keyed on them.",
          "- `pop_ha_proxy_1990`: splits before 1991 are weighted with the 1990 population grid, the "
          "earliest available. Long series before 1990 (census 1850–1980) carry this approximation.",
          "- `_lookthrough`: the successor was a short-lived transitional version without geometry "
          "(e.g. Thurgau reform 1994–1998); weights go directly to the next versions with geometry.",
          "- Canton totals change only through canton transfers: Moutier BE→JU (2026) and "
          "Clavaleyres BE→FR (2022, merged into Murten)."]
    path = ROOT / "docs" / "backbone_report.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(path)


def run() -> str:
    mv, _ = load_backbone()
    cw = crosswalk(REFERENCE_DATE)
    results = {"R1": check_register(mv), "R2": check_geometry(mv), "C1": check_weights(cw),
               "C2": check_official_correspondence(cw, mv), "C3": check_dead_ends(cw, mv),
               "T1": check_population_totals(mv), "T2": check_votes(), "T3": check_jobs()}
    pd.to_pickle(results, interim_path("backbone", "validation_results.pkl"))
    return write_report(results)


if __name__ == "__main__":
    print(run())
