"""Public-transport reach from the 21 hubs (decisions D10, D39), computed with the CSA in csa.py.

Departures every minute 07:30-08:30 on the service day (gtfs_prep.SERVICE_DATE). For every
departure minute t the earliest arrival EA_s(t) at every station is computed.

Journey time. EA(t) - t would include the wait at the hub for the next departure. We report the
timetable journey time instead (as journey planners show it): EA(t) - LD(t), where LD(t) is the
latest departure minute t' >= t with EA(t') = EA(t). Departures are scanned up to 09:30 so that LD
is found for the 08:30 departure as well. The median over the 61 departure minutes is then taken.
The median including the initial wait is kept in `minutes_incl_wait`.

Towards the hub (decision D31, methods gtfs_rcsa_*): reverse scan (csa.run_reverse) for every
arrival deadline T at the hub, 06:00-08:30 each minute. LD(T) = latest departure still arriving by T;
the journey actually arrives at the earliest deadline T_a <= T with LD(T_a) = LD(T); journey time =
T_a - LD(T) (as a journey planner shows it: no initial wait, no wait at the hub). Median over the 61
deadlines 07:30-08:30.
  (deadlines before the earliest possible arrival are left out of the median; if the hub cannot be
  reached by 08:30 at all, the hour from the earliest possible arrival is used if that is by 10:30,
  column window_start_min; otherwise status 'no arrival at the hub by 10:30')
  gtfs_rcsa_mainstation  from the municipality's main station (main_stations(): chosen by the residents
                         it serves within 1.5 km, rail preferred, then most departures; without a stop
                         inside, the same choice within 2 km of the population-weighted centre)
  Station times are the median day of three weekdays (gtfs_prep.REVERSE_DAYS, combine_days()).
  gtfs_rcsa_popweighted  door-to-door: each populated hectare walks to the best stop within 1.5 km
                         (min over stops of walk + stop's median journey), population-weighted median

Hub-outward (kept for the growing-lines drawing and comparison), methods gtfs_csa_*.
Two municipality values (method column):
  gtfs_csa_station    earliest arrival at any station inside the municipality (reference-state
                      polygon, point-in-polygon), no access/egress walk
  gtfs_csa_popweighted each populated STATPOP 2025 hectare uses the best served station within
                      1.5 km straight line: min over those stations of (station median journey time
                      + walk = d * 1.3 / 1.2 m/s). (Until 2026-11-10 the nearest station was used,
                      which let a sparse bus stop beat a nearby rail station: Oberweningen 419 min.)
                      Municipality value =
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
# towards the hub (decision D31): arrival deadlines every minute 06:00 .. 08:30; the median is taken
# over the 61 deadlines 07:30 .. 08:30 (the earlier ones only serve to find the actual arrival time)
R_FIRST = 6 * 3600
N_RSCAN = 271              # deadlines 06:00 .. 10:30
R_WIN0 = 90                # index of 07:30
R_WIN1 = 150               # index of 08:30
R_LOOKBACK = 6 * 3600      # connections departing up to 6 h before the deadline
MAIN_FALLBACK_RADIUS = 2000.0


def ea_matrix(net: Network, src: list[int]) -> np.ndarray:
    out = np.empty((N_SCAN, len(net.mct)), np.int64)
    for k in range(N_SCAN):
        out[k] = net.run(src, T_FIRST + 60 * k, CUTOFF)[0]
    return out


def journey_times(ea: np.ndarray, cap_unreached: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """ea: (N_SCAN, n) earliest arrivals. Returns (journey, incl_wait) for the first N_DEP rows,
    in seconds, INF-like large values where unreached.

    The latest departure LD is searched up to the last scan (09:30). Where the arrival stays the same up to
    that scan the vehicle leaves later and the true journey is unknown (EA - 09:30 is only an upper bound,
    typically a rural stop with a gap of two hours or more). cap_unreached=True sets the journey of those
    departures to inf (incl_wait stays valid); the hub-outward spread uses it, the older methods do not."""
    n_scan = ea.shape[0]
    ld = np.empty_like(ea)
    ld[-1] = n_scan - 1
    for k in range(n_scan - 2, -1, -1):
        ld[k] = np.where(ea[k] == ea[k + 1], ld[k + 1], k)
    t = T_FIRST + 60 * np.arange(n_scan)[:, None]
    unreached = ea >= INF
    journey = np.where(unreached | (cap_unreached & (ld == n_scan - 1)), np.inf,
                       ea - (T_FIRST + 60 * ld)).astype(float)
    wait = np.where(unreached, np.inf, ea - t).astype(float)
    return journey[:N_DEP], wait[:N_DEP]


def ld_matrix(net: Network, tgt: list[int]) -> np.ndarray:
    """Latest departure (s) at every station for each arrival deadline 06:00 .. 08:30 at the hub."""
    out = np.empty((N_RSCAN, len(net.mct)), np.int64)
    for k in range(N_RSCAN):
        T = R_FIRST + 60 * k
        out[k] = net.run_reverse(tgt, T, T - R_LOOKBACK)
    return out


def reverse_journey_times(ld: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ld: (N_RSCAN, n) latest departures. For deadline T_k the journey leaves at LD(T_k) and actually
    arrives at the earliest deadline T_a <= T_k with LD(T_a) = LD(T_k) (deadlines are whole minutes,
    like GTFS times). Returns (journey = T_a - LD, incl_wait = T_k - LD) for the deadlines 07:30-08:30,
    in seconds, inf where the hub cannot be reached."""
    n_scan = ld.shape[0]
    a = np.empty_like(ld)
    a[0] = 0
    for k in range(1, n_scan):
        a[k] = np.where(ld[k] == ld[k - 1], a[k - 1], k)
    T = R_FIRST + 60 * np.arange(n_scan)[:, None]
    unreached = ld <= -INF
    journey = np.where(unreached, np.inf, (R_FIRST + 60 * a) - ld).astype(float)
    wait = np.where(unreached, np.inf, T - ld).astype(float)
    return journey[R_WIN0:], wait[R_WIN0:]   # rows: deadlines 07:30 .. 10:30


def reverse_summary(journey: np.ndarray, wait: np.ndarray):
    """Per station: median journey, median incl. wait, P10, P90 (seconds), the first deadline used
    (minutes after midnight), and P10, P90 of the journey incl. wait (the 7-tuple SUMMARY_FIELDS).
    journey/wait rows are the deadlines 07:30 .. 10:30.

    Window: the deadlines 07:30-08:30 that can be met (deadlines before the earliest possible arrival
    have no journey and are left out). If the hub cannot be reached by 08:30 at all (far hubs: the
    first trains of the day arrive later), the window is the hour from the earliest deadline that can
    be met, if that is by 10:30; its start is returned so the value can be labelled. Otherwise inf."""
    import warnings
    n_win = R_WIN1 - R_WIN0 + 1
    j = np.where(np.isfinite(journey), journey, np.nan)
    w = np.where(np.isfinite(wait), wait, np.nan)
    in_win = np.isfinite(j[:n_win]).any(axis=0)
    first = np.argmax(np.isfinite(j), axis=0)               # first deadline that can be met
    reach = np.isfinite(j).any(axis=0)
    start = np.where(in_win, 0, np.where(reach, first, 0))
    rows = start[None, :] + np.arange(n_win)[:, None]
    rows = np.minimum(rows, j.shape[0] - 1)
    cols = np.arange(j.shape[1])[None, :]
    jj, ww = j[rows, cols], w[rows, cols]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        out = [np.nanmedian(jj, axis=0), np.nanmedian(ww, axis=0), np.nanpercentile(jj, 10, axis=0),
               np.nanpercentile(jj, 90, axis=0), np.nanpercentile(ww, 10, axis=0), np.nanpercentile(ww, 90, axis=0)]
    out = [np.where(np.isnan(x) | ~reach, np.inf, x) for x in out]
    late = np.where(reach & ~in_win, (R_FIRST // 60) + R_WIN0 + start, np.nan)
    return (*out[:4], late, *out[4:])


# per-station summary tuple (seconds; inf = not reached; late = start minute of a shifted window or NaN)
SUMMARY_FIELDS = ("median", "median_incl_wait", "p10", "p90", "window_start_min", "wait_p10", "wait_p90")


def _pct_inf(x: np.ndarray, q: float) -> np.ndarray:
    """Percentile along axis 0 where inf marks 'not reached': inf if the value would depend on an unreached row."""
    big = 1e9
    y = np.where(np.isfinite(x), x, big)
    r = np.percentile(y, q, axis=0)
    return np.where(np.percentile(y, q, axis=0, method="higher") >= big, np.inf, r)


def forward_summary(journey: np.ndarray, wait: np.ndarray) -> tuple:
    """Hub-outward counterpart of reverse_summary: per station the median journey, median incl. wait, P10, P90
    over the 61 departures 07:30-08:30 (rows of journey_times()), no shifted window (late = NaN), and P10, P90
    of the journey incl. wait. Seconds; inf where not reached (a station reached at some departures only has
    inf in the percentiles that need an unreached departure)."""
    return (np.median(journey, axis=0), np.median(wait, axis=0), _pct_inf(journey, 10), _pct_inf(journey, 90),
            np.full(journey.shape[1], np.nan), _pct_inf(wait, 10), _pct_inf(wait, 90))


RAIL_TYPES = set(range(100, 118)) | {2}
MODE_OF_TYPE = [  # (label, GTFS route types: basic + extended)
    ("rail", RAIL_TYPES), ("metro", {1} | set(range(400, 406))), ("tram", {0, 5} | set(range(900, 907))),
    ("boat", {4, 1200} | set(range(1000, 1022))), ("cableway", {6} | set(range(1300, 1308))),
    ("funicular", {7, 1400}), ("bus", {3, 11} | set(range(200, 210)) | set(range(700, 718)) | set(range(1500, 1508))),
]
MAIN_SIMILAR = 0.5       # stations serving >= half the best coverage compete on departures (drops outlying halts)
MAIN_RAIL_MIN = 1 / 3    # rail is preferred when its best station serves >= a third of what the best stop serves


def station_modes(net: Network) -> pd.Series:
    """Main mode per station (idx -> 'rail', 'bus', 'boat', 'tram', 'metro', 'cableway', 'funicular'):
    rail if any rail departure 06:30-18:00, else the mode with the most boardable departures."""
    from pipeline.reach.gtfs_prep import SERVED
    c = net.connections
    c = c[c.board & (c.dep >= SERVED[0]) & (c.dep <= SERVED[1])]
    lab = pd.Series("bus", index=pd.Index(np.unique(c.route_type), name="route_type"))
    for name, types in MODE_OF_TYPE[::-1]:
        lab[lab.index.isin(types)] = name
    k = pd.DataFrame({"idx": c.from_idx.to_numpy(), "mode": c.route_type.map(lab).to_numpy()})
    n = k.groupby(["idx", "mode"]).size().unstack(fill_value=0)
    out = n.idxmax(axis=1)
    if "rail" in n:
        out[n["rail"] > 0] = "rail"
    return out.reindex(net.stations.idx).fillna("none")


def main_stations(net: Network, gem_ids: np.ndarray, access: pd.DataFrame | None = None,
                  hub_didoks: list[int] | None = None) -> pd.DataFrame:
    """Main station per municipality, chosen by the population it serves (expert audit MUST 2; before
    2026-11-11 it was the station with the most departures, which picked intermediate halts such as
    Grafenort for Engelberg).

    Candidates: the stations served 06:30-18:00 inside the municipality (reference polygon). Coverage
    of a candidate = residents (STATPOP 2025) of the municipality's inhabited hectares within 1.5 km
    straight line of it (the door-to-door access radius). Rail first: if the best rail station
    covers at least MAIN_RAIL_MIN (a third) of what the best stop of any mode covers, only rail stations
    compete. Among the competing stations, those covering at least MAIN_SIMILAR (half) of the best
    coverage remain (this drops outlying halts such as Grafenort, St. Peter-Molinis, Alp Grüm,
    Riazzino) and the one with the most departures 06:30-18:00 (rail departures for rail) wins
    (so Rapperswil SG beats the more central Jona; 0.9 picked Kempten for Wetzikon, see reach_method.md). A hub municipality takes its hub station. A municipality with no served stop inside
    takes the station chosen the same way among those within 2 km of its population-weighted centre
    (inside = False). Columns: bfs_nr, idx, inside, name, didok, mode, pop_share (coverage share)."""
    sta = net.stations
    if access is None:
        access = access_links(sta)
    cand = sta[sta.served_in_window].copy()
    modes = station_modes(net)
    cand["mode"] = cand.idx.map(modes)
    a = access.dropna(subset=["bfs_nr", "idx"])
    cov = a.groupby(["bfs_nr", "idx"]).BBTOT.sum().rename("cov").reset_index().astype({"bfs_nr": int, "idx": int})
    pop = access.dropna(subset=["bfs_nr"]).drop_duplicates("RELI").groupby("bfs_nr").BBTOT.sum()
    pop.index = pop.index.astype(int)
    cov_by = {int(b): g.set_index("idx")["cov"] for b, g in cov.groupby("bfs_nr")}

    def pick(b: int, c: pd.DataFrame):
        c = c.assign(cov=c.idx.map(cov_by.get(b, pd.Series(dtype=float))).fillna(0.0))
        best_any = c["cov"].max()
        rail = c[c.n_dep_rail > 0]
        if len(rail) and rail["cov"].max() >= MAIN_RAIL_MIN * best_any:
            c, key = rail, "n_dep_rail"
        else:
            key = "n_dep"
        top = c[c["cov"] >= MAIN_SIMILAR * c["cov"].max()]
        r = top.sort_values([key, "n_dep", "cov"], ascending=False, kind="stable").iloc[0]
        return int(r.idx), float(r["cov"])

    rows = []
    hub_idx = {}
    for d in hub_didoks or []:
        h = sta[sta.didok == str(d)]
        if len(h) and h.bfs_nr.notna().iloc[0]:
            hub_idx[int(h.bfs_nr.iloc[0])] = int(h.idx.iloc[0])
    ins = cand[cand.bfs_nr.notna()].astype({"bfs_nr": int})
    for b, c in ins.groupby("bfs_nr"):
        if b in hub_idx:
            i = hub_idx[b]
            cv = float(cov_by.get(b, pd.Series(dtype=float)).get(i, 0.0))
        else:
            i, cv = pick(b, c)
        rows.append({"bfs_nr": b, "idx": i, "inside": True, "cov": cv})
    out = pd.DataFrame(rows)
    miss = sorted(set(int(b) for b in gem_ids) - set(out.bfs_nr))
    if miss:
        h = hectares_in_zones().dropna(subset=["bfs_nr"])
        h = h[h.bfs_nr.astype(int).isin(miss)]
        cen = h.assign(wx=h.x * h.BBTOT, wy=h.y * h.BBTOT).groupby("bfs_nr")[["wx", "wy", "BBTOT"]].sum()
        extra = []
        for b, r in cen.iterrows():
            cx, cy = r.wx / r.BBTOT, r.wy / r.BBTOT
            near = cand[np.hypot(cand.x - cx, cand.y - cy) <= MAIN_FALLBACK_RADIUS]
            if len(near):
                i, cv = pick(int(b), near)
                extra.append({"bfs_nr": int(b), "idx": i, "inside": False, "cov": cv})
        if extra:
            out = pd.concat([out, pd.DataFrame(extra)], ignore_index=True)
    out["pop_share"] = (out["cov"] / out.bfs_nr.map(pop)).round(3)
    out = out.drop(columns="cov").merge(sta[["idx", "name", "didok"]], on="idx", how="left")
    out["mode"] = out.idx.map(modes)
    return out.astype({"idx": int})


def main_stations_by_departures(net: Network, gem_ids: np.ndarray) -> pd.DataFrame:
    """The rule used until 2026-11-10 (most rail departures, else most departures), kept for the
    before/after report (pipeline/reach/run.py)."""
    sta = net.stations
    cand = sta[sta.served_in_window].sort_values(["n_dep_rail", "n_dep"], ascending=False, kind="stable")
    ins = cand[cand.bfs_nr.notna()].drop_duplicates("bfs_nr")
    return pd.DataFrame({"bfs_nr": ins.bfs_nr.astype(int), "idx": ins.idx.astype(int), "name": ins.name})


def weighted_median(v: np.ndarray, w: np.ndarray) -> float:
    o = np.argsort(v)
    v, w = v[o], w[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, 0.5 * c[-1])])


def access_links(stations: pd.DataFrame) -> pd.DataFrame:
    """Every served station within 1.5 km of every populated hectare (one row per pair; hectares with
    none keep one row with idx NaN). Served = at least one connection departing or arriving
    06:30-18:00 on the service day (a stop served only in the evening is not a usable access)."""
    cache = interim_path("reach", "hectare_access_all.parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    h = hectares_in_zones()
    hp = gpd.GeoDataFrame(h[["RELI"]], geometry=gpd.points_from_xy(h.x, h.y), crs=2056)
    served = stations[stations.served_in_window]
    sp = gpd.GeoDataFrame(served[["idx"]], geometry=gpd.points_from_xy(served.x, served.y), crs=2056)
    j = gpd.sjoin(hp, sp, how="left", predicate="dwithin", distance=ACCESS_RADIUS)
    j = j[["RELI", "idx"]].merge(served[["idx", "x", "y"]], on="idx", how="left")
    a = h.merge(j, on="RELI", how="left", suffixes=("", "_st"))
    a["dist"] = np.hypot(a["x"] - a["x_st"], a["y"] - a["y_st"])
    a["walk_s"] = a.dist * DETOUR / WALK_SPEED
    a = a.drop(columns=["x_st", "y_st"])
    a.to_parquet(cache)
    return a


def best_access(access: pd.DataFrame, med_station: np.ndarray, med_wait_station: np.ndarray) -> pd.DataFrame:
    """One row per hectare: best station (min of station median journey + walk) among those in reach.
    Columns j / jw in seconds (NaN: no station within 1.5 km; inf: none of them reached)."""
    a = access.dropna(subset=["bfs_nr"])
    ok = a.idx.notna()
    a = a.assign(j=np.nan, jw=np.nan)
    ii = a.loc[ok, "idx"].astype(int).to_numpy()
    a.loc[ok, "j"] = med_station[ii] + a.loc[ok, "walk_s"].to_numpy()
    a.loc[ok, "jw"] = med_wait_station[ii] + a.loc[ok, "walk_s"].to_numpy()
    g = a.groupby("RELI", sort=False)
    best = g.agg(bfs_nr=("bfs_nr", "first"), BBTOT=("BBTOT", "first"), j=("j", "min"), jw=("jw", "min"),
                 has_stop=("idx", "count"))
    best["idx"] = np.where(best["has_stop"] > 0, 1.0, np.nan)  # marker: a station is within reach
    return best.reset_index()


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
    rows += popweighted_rows(slug, med_station, np.median(wait, axis=0), access, gem_ids)
    return pd.DataFrame(rows, columns=["hub", "mode", "bfs_nr", "minutes", "minutes_incl_wait", "status",
                                       "method", "pop_share_with_stop"])


def popweighted_rows(slug: str, med_station: np.ndarray, med_wait_station: np.ndarray,
                     access: pd.DataFrame, gem_ids: np.ndarray, method: str = "gtfs_csa_popweighted",
                     unreached: str = "not reached by 18:00") -> list[tuple]:
    rows = []
    a = best_access(access, med_station, med_wait_station)
    for bfs, g in a.groupby("bfs_nr"):
        pop = g.BBTOT.sum()
        cov = g[g.idx.notna()]
        share = cov.BBTOT.sum() / pop if pop else 0.0
        if cov.empty:
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "no PT within walking distance", method, 0.0))
            continue
        fin = cov[np.isfinite(cov.j)]
        if fin.BBTOT.sum() < 0.5 * cov.BBTOT.sum():
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, unreached, method, share))
            continue
        # unreached hectares count as +inf in the median
        v = cov.j.to_numpy()
        vw = cov.jw.to_numpy()
        w = cov.BBTOT.to_numpy(float)
        rows.append((slug, "pt", int(bfs), round(weighted_median(v, w) / 60, 1),
                     round(weighted_median(vw, w) / 60, 1), "ok", method, round(share, 4)))
    done = set(a.bfs_nr.astype(int))
    for bfs in gem_ids:
        if int(bfs) not in done:
            rows.append((slug, "pt", int(bfs), np.nan, np.nan, "no populated hectare", method, np.nan))
    return rows


COLS = ["hub", "mode", "bfs_nr", "minutes", "minutes_incl_wait", "status", "method", "pop_share_with_stop"]


SPREAD_COLS = ["minutes_p10", "minutes_p90", "minutes_wait_p10", "minutes_wait_p90"]


class AccessIndex:
    """The hectare -> stop links (access_links) in arrays, to take the population-weighted municipality
    median of several per-station time vectors in one pass (door-to-door median, P10, P90 ...)."""

    def __init__(self, access: pd.DataFrame):
        a = access.dropna(subset=["bfs_nr"])
        if not a.RELI.is_monotonic_increasing:
            a = a.sort_values("RELI", kind="stable")
        reli = a.RELI.to_numpy()
        self.starts = np.r_[0, np.flatnonzero(reli[1:] != reli[:-1]) + 1]
        idx = a.idx.to_numpy(float)
        self.has = ~np.isnan(idx)
        self.ii = np.where(self.has, idx, 0).astype(int)
        self.walk = a.walk_s.to_numpy(float)
        self.bfs = a.bfs_nr.to_numpy()[self.starts].astype(int)
        self.pop = a.BBTOT.to_numpy(float)[self.starts]
        self.has_stop = np.add.reduceat(self.has.astype(np.int32), self.starts) > 0
        order = np.argsort(self.bfs, kind="stable")
        cuts = np.r_[0, np.flatnonzero(np.diff(self.bfs[order])) + 1, len(order)]
        self.groups = {int(self.bfs[order[c0]]): order[c0:c1] for c0, c1 in zip(cuts[:-1], cuts[1:])}

    def hectare_times(self, station_s: np.ndarray) -> np.ndarray:
        """Per hectare the best (walk + station time) over the stops within reach, seconds (inf: none reached)."""
        v = np.where(self.has, station_s[self.ii] + self.walk, np.inf)
        return np.minimum.reduceat(v, self.starts)

    def municipality(self, station_s: np.ndarray, gem_ids: np.ndarray) -> pd.DataFrame:
        """Population-weighted median over the inhabited hectares of every municipality (same rule as
        popweighted_rows: hectares with a stop within 1.5 km only; unreached hectares count as +inf; a municipality
        where fewer than half of those residents reach the hub has no value). Columns bfs_nr, minutes
        (round(s / 60, 1), NaN without value), status, share (residents with a stop in reach)."""
        j = self.hectare_times(station_s)
        rows = []
        for b in gem_ids:
            g = self.groups.get(int(b))
            if g is None:
                rows.append((int(b), np.nan, "no populated hectare", np.nan))
                continue
            pop_all = self.pop[g].sum()
            c = g[self.has_stop[g]]
            share = self.pop[c].sum() / pop_all if pop_all else 0.0
            if len(c) == 0:
                rows.append((int(b), np.nan, "no PT within walking distance", 0.0))
                continue
            fin = np.isfinite(j[c])
            if self.pop[c][fin].sum() < 0.5 * self.pop[c].sum():
                rows.append((int(b), np.nan, "unreached", round(share, 4)))
                continue
            rows.append((int(b), round(weighted_median(j[c], self.pop[c]) / 60, 1), "ok", round(share, 4)))
        return pd.DataFrame(rows, columns=["bfs_nr", "minutes", "status", "share"])


def doortodoor_spread(ai: AccessIndex, summary: tuple, gem_ids: np.ndarray) -> pd.DataFrame:
    """Door-to-door P10 / P90 (journey, and journey incl. wait) per municipality, minutes: every hectare takes
    min over its stops of (walk + the stop's P10 or P90), then the population-weighted median over hectares,
    like the median itself (so P10 <= median <= P90 holds). The per-hectare minimum of the stops' percentiles is
    an approximation of the percentile of the per-minute minimum (it can only be slightly too high at P10 and
    too low at P90 where two stops alternate). Index bfs_nr; columns SPREAD_COLS."""
    _med, _medw, p10, p90, _late, w10, w90 = summary
    out = {}
    for col, arr in zip(SPREAD_COLS, (p10, p90, w10, w90)):
        out[col] = ai.municipality(arr, gem_ids).set_index("bfs_nr").minutes
    return pd.DataFrame(out)


def towards_hub_results(net: Network, slug: str, summary: tuple, access: pd.DataFrame,
                        gem_ids: np.ndarray, mains: pd.DataFrame, by_day: dict | None = None,
                        ai: AccessIndex | None = None) -> pd.DataFrame:
    """D31: station time (main station -> hub) and door-to-door towards the hub, morning arrivals.
    summary = SUMMARY_FIELDS per station (median, median incl. wait, P10, P90, late-window start, P10 and P90
    incl. wait), as from reverse_summary() or combine_days(); by_day = {date: per-station median (s)}.
    Columns minutes_p10/p90 (journey) and minutes_wait_p10/p90 (journey incl. wait) are filled for both methods."""
    med, medw, p10, p90, late, w10, w90 = summary
    ms = mains.set_index("bfs_nr")
    rows = []
    nan2 = (np.nan, np.nan)
    for bfs in gem_ids:
        b = int(bfs)
        if b not in ms.index:
            rows.append((slug, "pt", b, np.nan, np.nan, "no stop within 2 km", "gtfs_rcsa_mainstation", np.nan,
                         None, None, None, np.nan, np.nan, np.nan, None, np.nan, None, *nan2))
            continue
        r = ms.loc[b]
        i = int(r.idx)
        ok = np.isfinite(med[i])
        st = "ok" if ok else "no arrival at the hub by 10:30"

        def m(x):
            return round(x[i] / 60, 1) if ok and np.isfinite(x[i]) else np.nan
        rows.append((slug, "pt", b, m(med), m(medw), st, "gtfs_rcsa_mainstation", np.nan,
                     r["name"], str(r.didok), bool(r.inside), m(p10), m(p90),
                     late[i], r["mode"], r.pop_share,
                     ";".join(f"{k}:{v[i] / 60:.0f}" if np.isfinite(v[i]) else f"{k}:-" for k, v in (by_day or {}).items())
                     or None, m(w10), m(w90)))
    d = pd.DataFrame(rows, columns=COLS + ["main_station", "main_didok", "main_inside", "minutes_p10", "minutes_p90",
                                           "window_start_min", "main_mode", "main_pop_share", "minutes_by_day",
                                           "minutes_wait_p10", "minutes_wait_p90"])
    pw = pd.DataFrame(popweighted_rows(slug, med, medw, access, gem_ids, method="gtfs_rcsa_popweighted",
                                       unreached="no arrival at the hub by 10:30"), columns=COLS)
    sp = doortodoor_spread(ai or AccessIndex(access), summary, gem_ids)
    pw = pw.merge(sp, left_on="bfs_nr", right_index=True, how="left")
    pw.loc[pw.status != "ok", SPREAD_COLS] = np.nan
    return pd.concat([d, pw], ignore_index=True)


def from_hub_results(slug: str, summary: tuple, gem_ids: np.ndarray, mains: pd.DataFrame, ai: AccessIndex,
                     by_day: dict | None = None) -> pd.DataFrame:
    """Hub-outward counterpart of towards_hub_results, with the same definitions (D31) mirrored: station time =
    journey from the hub station to the municipality's main station, departures from the hub 07:30-08:30 (median
    day of the three weekdays), journey = arrival - latest departure giving that arrival (no initial wait);
    door-to-door = hectares walking from the best stop within 1.5 km. Methods gtfs_fcsa_mainstation and
    gtfs_fcsa_popweighted; columns as in towards_hub_results (window_start_min is NaN)."""
    med, medw, p10, p90, late, w10, w90 = summary
    ms = mains.set_index("bfs_nr")
    rows = []
    for bfs in gem_ids:
        b = int(bfs)
        if b not in ms.index:
            rows.append((slug, "pt", b, np.nan, np.nan, "no stop within 2 km", "gtfs_fcsa_mainstation", np.nan,
                         None, None, None, np.nan, np.nan, np.nan, None, np.nan, None, np.nan, np.nan))
            continue
        r = ms.loc[b]
        i = int(r.idx)
        ok = np.isfinite(med[i])

        def m(x):
            return round(x[i] / 60, 1) if ok and np.isfinite(x[i]) else np.nan
        rows.append((slug, "pt", b, m(med), m(medw), "ok" if ok else NO_MORNING_FROM, "gtfs_fcsa_mainstation",
                     np.nan, r["name"], str(r.didok), bool(r.inside), m(p10), m(p90), np.nan, r["mode"],
                     r.pop_share, ";".join(f"{k}:{v[i] / 60:.0f}" if np.isfinite(v[i]) else f"{k}:-"
                                           for k, v in (by_day or {}).items()) or None, m(w10), m(w90)))
    d = pd.DataFrame(rows, columns=COLS + ["main_station", "main_didok", "main_inside", "minutes_p10", "minutes_p90",
                                           "window_start_min", "main_mode", "main_pop_share", "minutes_by_day",
                                           "minutes_wait_p10", "minutes_wait_p90"])
    base = ai.municipality(med, gem_ids).set_index("bfs_nr")
    sp = doortodoor_spread(ai, summary, gem_ids)
    wm = ai.municipality(medw, gem_ids).set_index("bfs_nr").minutes
    pw = pd.DataFrame({"hub": slug, "mode": "pt", "bfs_nr": base.index, "minutes": base.minutes.to_numpy(),
                       "minutes_incl_wait": wm.reindex(base.index).to_numpy(),
                       "status": base.status.replace({"unreached": NO_MORNING_FROM}).to_numpy(),
                       "method": "gtfs_fcsa_popweighted", "pop_share_with_stop": base.share.to_numpy()})
    pw = pw.merge(sp, left_on="bfs_nr", right_index=True, how="left")
    pw.loc[pw.status != "ok", SPREAD_COLS + ["minutes_incl_wait"]] = np.nan
    return pd.concat([d, pw], ignore_index=True)


def recompute_popweighted(hubs=HUBS) -> pd.DataFrame:
    """Recompute only the population-weighted PT rows from the cached per-station medians
    (data/interim/reach/pt_station_times), without re-running the CSA. Returns the new rows."""
    net = Network.load(outdir())
    access = access_links(net.stations)
    gem = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde",
                        ignore_geometry=True)
    gem_ids = gem["id"].astype(int).to_numpy()
    out = []
    n = len(net.stations)
    for slug, _name, _didok in hubs:
        st = pd.read_parquet(interim_path("reach", "pt_station_times", f"{slug}.parquet"))
        med = np.full(n, np.inf); medw = np.full(n, np.inf)
        med[st.idx.to_numpy()] = st.median_journey_s.to_numpy()
        medw[st.idx.to_numpy()] = st.median_incl_wait_s.to_numpy()
        out += popweighted_rows(slug, med, medw, access, gem_ids)
    return pd.DataFrame(out, columns=["hub", "mode", "bfs_nr", "minutes", "minutes_incl_wait", "status",
                                      "method", "pop_share_with_stop"])


def representative_departure(journey: np.ndarray, net: Network) -> int:
    """Departure minute index whose station journey times are closest to the medians (L1 over
    Swiss stations reached at every departure)."""
    ch = net.stations.bfs_nr.notna().to_numpy()
    fin = np.isfinite(journey).all(axis=0) & ch
    med = np.median(journey[:, fin], axis=0)
    dev = np.abs(journey[:, fin] - med).mean(axis=1)
    return int(np.argmin(dev))


def day_networks(primary: Network) -> dict:
    """{date: (Network, primary idx -> that day's idx or -1)} for the reverse-scan days (REVERSE_DAYS).
    Stations are matched by GTFS station id; a station without service that day maps to -1."""
    import datetime as dt
    from pipeline.reach.gtfs_prep import REVERSE_DAYS, SERVICE_DATE, build
    out = {}
    pid = primary.stations.station_id.to_numpy()
    for d in REVERSE_DAYS:
        if d == SERVICE_DATE:
            out[d] = (primary, np.arange(len(pid)))
            continue
        if not (outdir(d) / "connections.parquet").exists():
            build(d)
        n = Network.load(outdir(d))
        m = pd.Series(n.stations.idx.to_numpy(), index=n.stations.station_id.to_numpy())
        out[d] = (n, m.reindex(pid).fillna(-1).astype(int).to_numpy())
    assert isinstance(next(iter(out)), dt.date)
    return out


def combine_days(per_day: list[tuple]) -> tuple:
    """Per station, the summary (SUMMARY_FIELDS) of the day whose median is the
    median of the daily medians (3 days: the middle one; unreached = inf sorts last). Choosing one day
    keeps P10/P90 and the late window consistent with the value, and drops a day with works."""
    meds = np.vstack([p[0] for p in per_day])
    k = meds.shape[0]
    pick = np.argsort(meds, axis=0, kind="stable")[(k - 1) // 2]
    cols = np.arange(meds.shape[1])
    return tuple(np.vstack([p[j] for p in per_day])[pick, cols] for j in range(len(per_day[0])))


def hub_reverse(days: dict, didok: int) -> tuple[tuple, dict]:
    """Reverse scans for one hub on every reverse day, mapped to the primary station index."""
    per_day, by_day = [], {}
    for d, (n, m) in days.items():
        rj, rw = reverse_journey_times(ld_matrix(n, hub_sources(n, didok)))
        summ = reverse_summary(rj, rw)
        del rj, rw
        ok = m >= 0
        mapped = []
        for j, x in enumerate(summ):
            y = np.full(len(m), np.nan if j == 4 else np.inf)
            y[ok] = x[m[ok]]
            mapped.append(y)
        per_day.append(tuple(mapped))
        by_day[d.isoformat()] = mapped[0]
    return combine_days(per_day), by_day


NO_MORNING_FROM = "no departure from the hub 07:30-09:30 reaches it by 18:00"


def hub_forward(days: dict, didok: int, primary: tuple | None = None) -> tuple[tuple, dict]:
    """Hub-outward summaries (forward scans, departures 07:30-08:30) on every reverse day, mapped to the primary
    station index, then the median day per station (combine_days), like hub_reverse. primary = (journey, wait)
    of the primary service day when already computed (journey_times(ea, cap_unreached=True))."""
    from pipeline.reach.gtfs_prep import SERVICE_DATE
    per_day, by_day = [], {}
    for d, (n, m) in days.items():
        if d == SERVICE_DATE and primary is not None:
            j, w = primary
        else:
            j, w = journey_times(ea_matrix(n, hub_sources(n, didok)), cap_unreached=True)
        summ = forward_summary(j, w)
        ok = m >= 0
        mapped = []
        for k, x in enumerate(summ):
            y = np.full(len(m), np.nan if k == 4 else np.inf)
            y[ok] = x[m[ok]]
            mapped.append(y)
        per_day.append(tuple(mapped))
        by_day[d.isoformat()] = mapped[0]
    return combine_days(per_day), by_day


def run(hubs=HUBS, save_station_times: bool = True):
    """Per hub the station-level summaries towards and from the hub (and the older hub-outward municipality
    results), then the municipality results of both directions."""
    import time
    net = Network.load(outdir())
    access = access_links(net.stations)
    gem = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde",
                        ignore_geometry=True)
    gem_ids = gem["id"].astype(int).to_numpy()
    res, rep, timing, store = [], {}, {}, {}
    mains = main_stations(net, gem_ids, access, [h[2] for h in HUBS])
    ai = AccessIndex(access)
    days = day_networks(net)
    for slug, name, didok in hubs:
        src = hub_sources(net, didok)
        t0 = time.time()
        # towards the hub (D31): reverse scans for morning arrivals on every reverse day, median day per station
        summ, by_day = hub_reverse(days, didok)
        t1 = time.time()
        if save_station_times:
            m_, mw_, p10_, p90_, late_, w10_, w90_ = summ
            pd.DataFrame({"idx": net.stations.idx, "median_journey_s": m_, "median_incl_wait_s": mw_,
                          "p10_s": p10_, "p90_s": p90_, "window_start_min": late_,
                          "wait_p10_s": w10_, "wait_p90_s": w90_,
                          **{f"median_journey_s_{k}": v for k, v in by_day.items()}}
                         ).to_parquet(interim_path("reach", "pt_station_times_to_hub", f"{slug}.parquet"))
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
        t2 = time.time()
        # hub-outward station time and door-to-door with the same definitions and spread (median day of three)
        fsumm, fby_day = hub_forward(days, didok, (journey_times(ea, cap_unreached=True)[0], wait))
        del ea
        if save_station_times:
            m_, mw_, p10_, p90_, _late, w10_, w90_ = fsumm
            pd.DataFrame({"idx": net.stations.idx, "median_journey_s": m_, "median_incl_wait_s": mw_,
                          "p10_s": p10_, "p90_s": p90_, "wait_p10_s": w10_, "wait_p90_s": w90_,
                          **{f"median_journey_s_{k}": v for k, v in fby_day.items()}}
                         ).to_parquet(interim_path("reach", "pt_station_times_from_hub", f"{slug}.parquet"))
        store[slug] = (summ, by_day, fsumm, fby_day)
        timing[slug] = {"reverse_s": round(t1 - t0, 1), "forward_s": round(t2 - t1, 1),
                        "forward_spread_s": round(time.time() - t2, 1)}
        ok = r[(r.method == "gtfs_csa_station") & (r.status == "ok")]
        print(f"{slug}: sources {src}, representative departure 07:30+{k} min, "
              f"{len(ok)} municipalities reached, median {ok.minutes.median():.0f} min")
    for slug, name, didok in hubs:
        summ, by_day, fsumm, fby_day = store[slug]
        tw = towards_hub_results(net, slug, summ, access, gem_ids, mains, by_day, ai)
        res.append(tw)
        res.append(from_hub_results(slug, fsumm, gem_ids, mains, ai, fby_day))
        okt = tw[(tw.method == "gtfs_rcsa_mainstation") & (tw.status == "ok")]
        print(f"{slug}: towards hub, {len(okt)} main stations reach it, median {okt.minutes.median():.0f} min")
    out = pd.concat(res, ignore_index=True)
    out.attrs["timing"] = timing
    return out, rep
