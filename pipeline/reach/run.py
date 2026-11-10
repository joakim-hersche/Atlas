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
# towards the hub (D31): (hub, municipality bfs_nr, label, expected station time range in minutes)
SPOT_TO_HUB = [("zuerich", 230, "Winterthur", (20, 25)), ("zuerich", 2701, "Basel", (50, 60)),
               ("basel", 2829, "Liestal", (10, 15)), ("zuerich", 1711, "Zug", (21, 30)),
               ("zuerich", 351, "Bern", (54, 62)), ("zuerich", 93, "Oberweningen", (25, 50))]


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


def _compare(m: pd.DataFrame, cols) -> list[dict]:
    rows = []
    for col in cols:
        d = m[col] - m.npvm
        rel = d / m.npvm
        rows.append({"gtfs_variant": col, "n_pairs": int(len(m)),
                     "pearson_r": round(float(np.corrcoef(m[col], m.npvm)[0, 1]), 3),
                     "median_diff_min": round(float(d.median()), 1),
                     "median_abs_diff_min": round(float(d.abs().median()), 1),
                     "median_ratio_gtfs_npvm": round(float((m[col] / m.npvm).median()), 3),
                     "share_within_15pct": round(float((rel.abs() <= 0.15).mean()), 3),
                     "share_within_25pct": round(float((rel.abs() <= 0.25).mean()), 3)})
    return rows


def validate_to_hub(ptres: pd.DataFrame, stations: pd.DataFrame, hubs) -> dict:
    """D31 figures: spot checks and agreement with the NPVM PT matrix column (zone -> hub zone)."""
    out = {"spot_checks_to_hub": []}
    st = ptres[ptres.method == "gtfs_rcsa_mainstation"].set_index(["hub", "bfs_nr"])
    dd = ptres[ptres.method == "gtfs_rcsa_popweighted"].set_index(["hub", "bfs_nr"])
    for slug, bfs, label, (lo, hi) in SPOT_TO_HUB:
        if (slug, bfs) not in st.index:
            continue
        r = st.loc[(slug, bfs)]
        out["spot_checks_to_hub"].append({
            "hub": slug, "from": label, "bfs_nr": bfs, "main_station": r.main_station,
            "station_min": r.minutes, "p10": r.minutes_p10, "p90": r.minutes_p90,
            "door_to_door_min": dd.loc[(slug, bfs)].minutes if (slug, bfs) in dd.index else None,
            "expected": [lo, hi], "ok": bool(lo <= r.minutes <= hi) if r.minutes == r.minutes else False})
    nv = npvm.municipality_times("pt", stations, to_hub=True)
    nv = nv[nv.hub.isin([h[0] for h in hubs])][["hub", "bfs_nr", "minutes"]].rename(columns={"minutes": "npvm"})
    a = ptres[(ptres.method == "gtfs_rcsa_popweighted") & (ptres.status == "ok")][["hub", "bfs_nr", "minutes"]]
    b = ptres[(ptres.method == "gtfs_rcsa_mainstation") & (ptres.status == "ok")][["hub", "bfs_nr", "minutes"]]
    m = a.rename(columns={"minutes": "door_to_door"}).merge(
        b.rename(columns={"minutes": "station_time"}), on=["hub", "bfs_nr"]).merge(nv, on=["hub", "bfs_nr"]).dropna()
    m = m[m.npvm > 0]   # the hub's own zone
    out["gtfs_vs_npvm_pt_to_hub"] = _compare(m, ["door_to_door", "station_time"])
    out["gtfs_vs_npvm_pt_to_hub_per_hub"] = m.groupby("hub").apply(
        lambda g: pd.Series({"n": len(g), "r_door_to_door": float(np.corrcoef(g.door_to_door, g.npvm)[0, 1]),
                             "r_station": float(np.corrcoef(g.station_time, g.npvm)[0, 1]),
                             "median_ratio_door_to_door": float((g.door_to_door / g.npvm).median())}),
        include_groups=False).round(3).reset_index().to_dict("records")
    return out


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
    out["gtfs_vs_npvm_pt"] = _compare(m, ["minutes", "minutes_incl_wait"])
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
    val.update(validate_to_hub(ptres, stations, hubs))
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
