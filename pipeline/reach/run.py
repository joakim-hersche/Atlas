"""Build all reach data: `uv run python -m pipeline.reach.run [hub_slug ...]`

Outputs
  data/interim/reach/travel_times.parquet   hub, mode, bfs_nr, minutes, status, method (+ extras)
  data/interim/reach/validation.json        PT spot checks and GTFS vs NPVM PT agreement
  data/out/reach/<hub>_<mode>.json          growing-network line files
  data/out/reach/index.json                 file list with sizes
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from pipeline.common import interim_path, out_path
from pipeline.reach import draw, npvm, pt
from pipeline.reach.csa import Network
from pipeline.reach.gtfs_prep import SERVICE_DATE, build as prep, outdir
from pipeline.reach.hubs import HUBS
from pipeline.sources.otd_gtfs.fetch import FEED

SPOT = [("zuerich", "Bern", 56), ("zuerich", "Basel SBB", 53), ("geneve", "Lausanne", 36)]


def car_rows(stations: pd.DataFrame, hubs) -> pd.DataFrame:
    r = npvm.municipality_times("car", stations)
    r = r[r.hub.isin([h[0] for h in hubs])]
    status = np.where(r.minutes.notna(), "ok",
                      np.where(r.pop_no_connection > 0, "no road access (car-free)",
                               np.where(r["pop"].fillna(0) == 0, "no populated hectare", "no data")))
    return pd.DataFrame({"hub": r.hub, "mode": "car", "bfs_nr": r.bfs_nr.astype(int),
                         "minutes": r.minutes.round(1).where(r.minutes.notna()),
                         "minutes_incl_wait": np.nan, "status": status, "method": "npvm2023_ttc_popweighted",
                         "pop_share_with_stop": np.nan,
                         "pop_share_no_car_access": (r.pop_no_connection / r["pop"]).round(4)})


def validate(net: Network, ptres: pd.DataFrame, stations: pd.DataFrame, hubs) -> dict:
    out = {"spot_checks": []}
    sta = net.stations
    for slug, dest, expected in SPOT:
        p = interim_path("reach", "pt_station_times", f"{slug}.parquet")
        if not p.exists():
            continue
        t = pd.read_parquet(p).merge(sta[["idx", "name"]], on="idx")
        r = t[t.name == dest].iloc[0]
        out["spot_checks"].append({"hub": slug, "to": dest, "expected_min": expected,
                                   "median_journey_min": r.median_journey_s / 60,
                                   "fastest_min": r.min_journey_s / 60,
                                   "median_incl_wait_min": r.median_incl_wait_s / 60})
    # GTFS (population-weighted, incl. egress walk) vs NPVM PT (RITA+ACT+EGT, pop-weighted zones)
    nv = npvm.municipality_times("pt", stations)
    nv = nv[nv.hub.isin([h[0] for h in hubs])][["hub", "bfs_nr", "minutes"]].rename(columns={"minutes": "npvm"})
    g = ptres[(ptres.method == "gtfs_csa_popweighted") & (ptres.status == "ok")][["hub", "bfs_nr", "minutes", "minutes_incl_wait"]]
    m = g.merge(nv, on=["hub", "bfs_nr"]).dropna()
    rows = []
    for col in ["minutes", "minutes_incl_wait"]:
        d = m[col] - m.npvm
        rel = d / m.npvm
        rows.append({"gtfs_variant": col, "n_pairs": int(len(m)),
                     "pearson_r": round(float(np.corrcoef(m[col], m.npvm)[0, 1]), 3),
                     "median_diff_min": round(float(d.median()), 1),
                     "median_abs_diff_min": round(float(d.abs().median()), 1),
                     "median_ratio_gtfs_npvm": round(float((m[col] / m.npvm).median()), 3),
                     "share_within_15pct": round(float((rel.abs() <= 0.15).mean()), 3),
                     "share_within_25pct": round(float((rel.abs() <= 0.25).mean()), 3)})
    out["gtfs_vs_npvm_pt"] = rows
    per_hub = m.assign(ratio=m.minutes / m.npvm).groupby("hub").agg(
        n=("ratio", "size"), median_ratio=("ratio", "median"),
        r=("minutes", lambda s: float(np.corrcoef(s, m.loc[s.index, "npvm"])[0, 1])))
    out["gtfs_vs_npvm_pt_per_hub"] = per_hub.round(3).reset_index().to_dict("records")
    sample = m[m.hub == "zuerich"].set_index("bfs_nr").loc[
        [b for b in [351, 2701, 6621, 5586, 1061, 3203, 230, 5192, 3901, 6300, 2939, 5002] if b in set(m.bfs_nr)]]
    out["sample_zuerich"] = sample.reset_index()[["bfs_nr", "minutes", "minutes_incl_wait", "npvm"]].round(1).to_dict("records")
    return out


def main(slugs: list[str] | None = None):
    hubs = [h for h in HUBS if not slugs or h[0] in slugs]
    if not (outdir() / "connections.parquet").exists():
        prep()
    net = Network.load(outdir())
    stations = net.stations
    ptres, rep = pt.run(hubs)
    car = car_rows(stations, hubs)
    tt = pd.concat([ptres, car], ignore_index=True)
    tt["minutes"] = tt.minutes.where(tt.status == "ok")
    tt.attrs = {}
    p = interim_path("reach", "travel_times.parquet")
    if slugs and p.exists():   # partial run: replace these hubs only
        old = pd.read_parquet(p)
        tt = pd.concat([old[~old.hub.isin([h[0] for h in hubs])], tt], ignore_index=True)
    tt = tt.sort_values(["hub", "mode", "method", "bfs_nr"]).reset_index(drop=True)
    tt.to_parquet(p)
    print("travel_times rows", len(tt))

    val = validate(net, ptres, stations, hubs)
    val["service_date"] = SERVICE_DATE.isoformat()
    val["feed"] = FEED
    val["representative_departure_min_after_0730"] = rep

    rail = draw.RailGraph(stations)
    rg = draw.RoadGraph()
    gem = draw.reference_municipalities()
    car_ok = car[car.status == "ok"]
    files = []
    for slug, name, didok in hubs:
        src = pt.hub_sources(net, didok)
        files.append(draw.build_pt(net, rail, slug, name, src, rep[slug], pt.CUTOFF))
        s = stations[stations.idx == src[0]].iloc[0]
        times = car_ok[car_ok.hub == slug].set_index("bfs_nr").minutes
        files.append(draw.build_car(rg, slug, name, (s.x, s.y), times, gem))
        print(files[-2], files[-1])
    idx_path = out_path("reach", "index.json")
    old_files = []
    if slugs and idx_path.exists():
        old_files = [f for f in json.loads(idx_path.read_text())["files"] if f["hub"] not in [h[0] for h in hubs]]
    allf = sorted(old_files + files, key=lambda f: (f["hub"], f["mode"]))
    idx_path.write_text(json.dumps({"service_date": SERVICE_DATE.isoformat(), "feed": FEED,
                                    "hubs": [{"slug": h[0], "name": h[1], "didok": h[2]} for h in HUBS],
                                    "files": allf}, ensure_ascii=False, indent=1))
    vp = interim_path("reach", "validation.json")
    val["hubs_in_run"] = [h[0] for h in hubs]
    vp.write_text(json.dumps(val, ensure_ascii=False, indent=1, default=float))
    print(json.dumps(val, ensure_ascii=False, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main(sys.argv[1:] or None)
