"""Public-transport reach from the 20 hubs (decision D10), computed with the CSA in csa.py.

Departures every minute 07:30-08:30 on the service day (gtfs_prep.SERVICE_DATE). For every
departure minute t the earliest arrival EA_s(t) at every station is computed.

Journey time. EA(t) - t would include the wait at the hub for the next departure. We report the
timetable journey time instead (as journey planners show it): EA(t) - LD(t), where LD(t) is the
latest departure minute t' >= t with EA(t') = EA(t). Departures are scanned up to 09:30 so that LD
is found for the 08:30 departure as well. The median over the 61 departure minutes is then taken.
The median including the initial wait is kept in `minutes_incl_wait`.

Two municipality values (method column):
  gtfs_csa_station    earliest arrival at any station inside the municipality (reference-state
                      polygon, point-in-polygon), no access/egress walk
  gtfs_csa_popweighted each populated STATPOP 2025 hectare uses its nearest served station within
                      1.5 km straight line, plus walk = d * 1.3 / 1.2 m/s; municipality value =
                      population-weighted median over hectares of the hectare's median journey time.
                      Municipalities where no populated hectare has a station within 1.5 km get
                      status 'no PT within walking distance' and no number.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.reach.csa import INF, Network
from pipeline.reach.gtfs_prep import DETOUR, WALK_SPEED, outdir
from pipeline.reach.hubs import HUBS
from pipeline.reach.npvm import hectares_in_zones

T_FIRST = 7 * 3600 + 30 * 60
N_DEP = 61                 # 07:30 .. 08:30
N_SCAN = 121               # 07:30 .. 09:30 (for the latest departure)
CUTOFF = 18 * 3600
ACCESS_RADIUS = 1500.0


def ea_matrix(net: Network, src: list[int]) -> np.ndarray:
    out = np.empty((N_SCAN, len(net.mct)), np.int64)
    for k in range(N_SCAN):
        out[k] = net.run(src, T_FIRST + 60 * k, CUTOFF)[0]
    return out


def journey_times(ea: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ea: (N_SCAN, n) earliest arrivals. Returns (journey, incl_wait) for the first N_DEP rows,
    in seconds, INF-like large values where unreached."""
    n_scan = ea.shape[0]
    ld = np.empty_like(ea)
    ld[-1] = n_scan - 1
    for k in range(n_scan - 2, -1, -1):
        ld[k] = np.where(ea[k] == ea[k + 1], ld[k + 1], k)
    t = T_FIRST + 60 * np.arange(n_scan)[:, None]
    unreached = ea >= INF
    journey = np.where(unreached, np.inf, ea - (T_FIRST + 60 * ld)).astype(float)
    wait = np.where(unreached, np.inf, ea - t).astype(float)
    return journey[:N_DEP], wait[:N_DEP]


def weighted_median(v: np.ndarray, w: np.ndarray) -> float:
    o = np.argsort(v)
    v, w = v[o], w[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, 0.5 * c[-1])])


def access_links(stations: pd.DataFrame) -> pd.DataFrame:
    """Nearest station within 1.5 km for every populated hectare, among stations with at least one
    connection departing or arriving 06:30-18:00 on the service day (a stop served only in the
    evening would otherwise capture the hectare)."""
    cache = interim_path("reach", "hectare_access.parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    h = hectares_in_zones()
    hp = gpd.GeoDataFrame(h[["RELI"]], geometry=gpd.points_from_xy(h.x, h.y), crs=2056)
    served = stations[stations.served_in_window]
    sp = gpd.GeoDataFrame(served[["idx"]], geometry=gpd.points_from_xy(served.x, served.y), crs=2056)
    j = gpd.sjoin_nearest(hp, sp, how="left", max_distance=ACCESS_RADIUS, distance_col="dist")
    j = j.drop_duplicates("RELI")
    a = h.merge(j[["RELI", "idx", "dist"]], on="RELI", how="left")
    a["walk_s"] = a.dist * DETOUR / WALK_SPEED
    a.to_parquet(cache)
    return a


def hub_sources(net: Network, didok: int) -> list[int]:
    s = net.stations
    return s.loc[s.didok == str(didok), "idx"].astype(int).tolist()


def municipality_results(net: Network, slug: str, ea: np.ndarray, journey: np.ndarray, wait: np.ndarray,
                         access: pd.DataFrame, gem_ids: np.ndarray) -> pd.DataFrame:
    sta = net.stations
    rows = []
    # --- station variant: municipal EA function = min over its stations, then journey times
    ins = sta[sta.bfs_nr.notna()].sort_values("bfs_nr")
    cols = ins.idx.to_numpy()
    bfs_sorted = ins.bfs_nr.astype(int).to_numpy()
    starts = np.r_[0, np.flatnonzero(np.diff(bfs_sorted)) + 1]
    ea_m = np.minimum.reduceat(ea[:, cols], starts, axis=1)
    jm_all, wm_all = journey_times(ea_m)
    pos = {b: i for i, b in enumerate(bfs_sorted[starts])}
    med_station = np.median(journey, axis=0)          # per station, seconds (inf if mostly unreached)
    for bfs in gem_ids:
        if bfs not in pos:
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "no stop in municipality", "gtfs_csa_station", np.nan))
            continue
        m, mw = np.median(jm_all[:, pos[bfs]]), np.median(wm_all[:, pos[bfs]])
        if not np.isfinite(m):
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "not reached by 18:00", "gtfs_csa_station", np.nan))
        else:
            rows.append((slug, "pt", int(bfs), round(m / 60, 1), round(mw / 60, 1), "ok", "gtfs_csa_station", np.nan))
    # --- population-weighted variant
    med_wait_station = np.median(wait, axis=0)
    a = access.dropna(subset=["bfs_nr"])
    ok = a.idx.notna()
    a = a.assign(j=np.nan, jw=np.nan)
    ii = a.loc[ok, "idx"].astype(int).to_numpy()
    a.loc[ok, "j"] = med_station[ii] + a.loc[ok, "walk_s"].to_numpy()
    a.loc[ok, "jw"] = med_wait_station[ii] + a.loc[ok, "walk_s"].to_numpy()
    for bfs, g in a.groupby("bfs_nr"):
        pop = g.BBTOT.sum()
        cov = g[g.idx.notna()]
        share = cov.BBTOT.sum() / pop if pop else 0.0
        if cov.empty:
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "no PT within walking distance", "gtfs_csa_popweighted", 0.0))
            continue
        fin = cov[np.isfinite(cov.j)]
        if fin.BBTOT.sum() < 0.5 * cov.BBTOT.sum():
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "not reached by 18:00", "gtfs_csa_popweighted", share))
            continue
        # unreached hectares count as +inf in the median
        v = cov.j.to_numpy()
        vw = cov.jw.to_numpy()
        w = cov.BBTOT.to_numpy(float)
        rows.append((slug, "pt", int(bfs), round(weighted_median(v, w) / 60, 1),
                     round(weighted_median(vw, w) / 60, 1), "ok", "gtfs_csa_popweighted", round(share, 4)))
    done = set(a.bfs_nr.astype(int))
    for bfs in gem_ids:
        if int(bfs) not in done:
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "no populated hectare", "gtfs_csa_popweighted", np.nan))
    return pd.DataFrame(rows, columns=["hub", "mode", "bfs_nr", "minutes", "minutes_incl_wait", "status",
                                       "method", "pop_share_with_stop"])


def representative_departure(journey: np.ndarray, net: Network) -> int:
    """Departure minute index whose station journey times are closest to the medians (L1 over
    Swiss stations reached at every departure)."""
    ch = net.stations.bfs_nr.notna().to_numpy()
    fin = np.isfinite(journey).all(axis=0) & ch
    med = np.median(journey[:, fin], axis=0)
    dev = np.abs(journey[:, fin] - med).mean(axis=1)
    return int(np.argmin(dev))


def run(hubs=HUBS, save_station_times: bool = True):
    net = Network.load(outdir())
    access = access_links(net.stations)
    gem = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde",
                        ignore_geometry=True)
    gem_ids = gem["id"].astype(int).to_numpy()
    res, rep = [], {}
    for slug, name, didok in hubs:
        src = hub_sources(net, didok)
        ea = ea_matrix(net, src)
        journey, wait = journey_times(ea)
        k = representative_departure(journey, net)
        rep[slug] = k
        if save_station_times:
            st = pd.DataFrame({"idx": net.stations.idx, "median_journey_s": np.median(journey, axis=0),
                               "median_incl_wait_s": np.median(wait, axis=0),
                               "min_journey_s": journey.min(axis=0)})
            st.to_parquet(interim_path("reach", "pt_station_times", f"{slug}.parquet"))
        r = municipality_results(net, slug, ea, journey, wait, access, gem_ids)
        res.append(r)
        ok = r[(r.method == "gtfs_csa_station") & (r.status == "ok")]
        print(f"{slug}: sources {src}, representative departure 07:30+{k} min, "
              f"{len(ok)} municipalities reached, median {ok.minutes.median():.0f} min")
    out = pd.concat(res, ignore_index=True)
    return out, rep
