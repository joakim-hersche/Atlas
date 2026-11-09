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
        r = to_vintage(g[["hist_id", "value"]], source_vintage=None, rule="sum")
        unm = r.attrs["unmapped"]
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
    if bc["worst"]:
        L += ["| Year | histId | BFS nr | Ours | BFS | Rel. diff |", "|---|---|---|---|---|---|"]
        L += [f"| {w['year']} | {w['hist_id']} | {w['bfs_nr_ours']} | {w['value_ours']} | {w['value_bfs']} | {float(w['rel']):.2%} |" for w in bc["worst"]]
    path = ROOT / "docs" / "backbone_report.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(path)


def run() -> str:
    mv, _ = load_backbone()
    cw = crosswalk(REFERENCE_DATE)
    results = {"R1": check_register(mv), "R2": check_geometry(mv), "C1": check_weights(cw),
               "C2": check_official_correspondence(cw, mv), "C3": check_dead_ends(cw, mv),
               "T1": check_population_totals(mv)}
    pd.to_pickle(results, interim_path("backbone", "validation_results.pkl"))
    return write_report(results)


if __name__ == "__main__":
    print(run())
