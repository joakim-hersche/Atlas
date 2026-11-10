"""Prepare one service day of the Swiss GTFS feed for the Connection Scan Algorithm.

Output (data/interim/reach/gtfs_<date>/):
  stations.parquet     one row per GTFS parent station (= one didok number): idx, station_id, didok,
                       name, lon, lat, x, y (LV95), mct_s (minimum change time), rail (bool),
                       bfs_nr (municipality on the reference state, point-in-polygon; NaN abroad)
  connections.parquet  elementary connections (one vehicle between two consecutive stops) of the
                       day, sorted by departure: dep, arr (seconds after midnight), from_idx, to_idx,
                       trip (int), seq, board (pickup allowed at from), alight (drop-off allowed at to),
                       route_type, chain_trip (trip continued in-seat at to via transfer_type 4, or -1)
                       n_dep / n_dep_rail (boardable departures 06:30-18:00, all modes / rail),
                       served_in_window (any departure or arrival 06:30-18:00)
  footpaths.parquet    from_idx, to_idx, walk_s (stations within 400 m straight line, time =
                       d * 1.3 / 1.2 m/s, overridden by transfers.txt between stations where given;
                       a station with no neighbour within 400 m is linked to its nearest station
                       within 1 km)
  trips.parquet        trip (int), trip_id, route_id, route_type, route_short_name, agency_id

Platforms are collapsed onto their parent station (every parent has exactly one didok number).
Minimum change time per station: the station-level transfers.txt rule (from_stop == to_stop on the
station's generic stop); otherwise the median of the rules between different platforms of the station; otherwise the
same-platform rules (at least 120 s); otherwise 120 s (task default). Capped at 900 s. Trip-specific transfer rules (transfer_type 2 with trip ids) are not
used; in-seat transfers (transfer_type 4) are.
"""
from __future__ import annotations

import datetime as dt
import json
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pcsv
from pyproj import Transformer

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.sources.otd_gtfs.fetch import FEED, gtfs

SERVICE_DATE = dt.date(2026, 11, 17)   # Tuesday, see reach.md for the choice
WINDOW = (7 * 3600 + 30 * 60, 18 * 3600)   # forward runs: departures 07:30 .. 18:00
EARLIEST_DEP = 4 * 3600 + 30 * 60          # keep connections from 04:30 (reverse runs: arrivals at the hub 07:30-08:30)
SERVED = (WINDOW[0] - 3600, WINDOW[1])     # a stop is "served" with a departure/arrival 06:30-18:00
DEFAULT_MCT = 120
MAX_MCT = 900   # a few bus stops carry implausible rules (e.g. 5940 s); capped
FOOT_RADIUS = 400.0
ISOLATED_RADIUS = 1000.0
WALK_SPEED = 1.2
DETOUR = 1.3
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def outdir(date: dt.date = SERVICE_DATE):
    p = interim_path("reach", f"gtfs_{date:%Y%m%d}", "x")
    return p.parent


def _csv(z, name, **kw):
    return pd.read_csv(z.open(name), dtype=str, encoding="utf-8-sig", keep_default_na=False,
                       na_values=[""], **kw)


def active_services(z, date: dt.date) -> set[str]:
    cal = _csv(z, "calendar.txt")
    ds = date.strftime("%Y%m%d")
    act = set(cal[(cal[DAYS[date.weekday()]] == "1") & (cal.start_date <= ds) & (cal.end_date >= ds)].service_id)
    cd = _csv(z, "calendar_dates.txt")
    x = cd[cd.date == ds]
    act -= set(x[x.exception_type == "2"].service_id)
    act |= set(x[x.exception_type == "1"].service_id)
    return act


def _hms(arr: pa.ChunkedArray | pa.Array) -> np.ndarray:
    s = pc.split_pattern(arr, ":")
    h = pc.cast(pc.list_element(s, 0), pa.int32())
    m = pc.cast(pc.list_element(s, 1), pa.int32())
    sec = pc.cast(pc.list_element(s, 2), pa.int32())
    return (h.to_numpy(zero_copy_only=False) * 3600 + m.to_numpy(zero_copy_only=False) * 60
            + sec.to_numpy(zero_copy_only=False)).astype(np.int32)


def read_stop_times(z, trip_ids: set[str]) -> pd.DataFrame:
    cols = ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "pickup_type", "drop_off_type"]
    ro = pcsv.ReadOptions(column_names=cols, skip_rows=1, block_size=64 << 20)
    co = pcsv.ConvertOptions(column_types={c: pa.string() for c in cols})
    vs = pa.array(sorted(trip_ids))
    parts = []
    with z.open("stop_times.txt") as fh:
        reader = pcsv.open_csv(fh, read_options=ro, convert_options=co)
        for batch in reader:
            m = pc.is_in(batch.column(0), value_set=vs)
            b = batch.filter(m)
            if b.num_rows:
                parts.append(b)
    t = pa.Table.from_batches(parts)
    df = pd.DataFrame({
        "trip_id": t.column("trip_id").to_pandas(),
        "arr": _hms(t.column("arrival_time")),
        "dep": _hms(t.column("departure_time")),
        "stop_id": t.column("stop_id").to_pandas(),
        "seq": pc.cast(t.column("stop_sequence"), pa.int32()).to_numpy(zero_copy_only=False),
        "pickup": pc.fill_null(t.column("pickup_type"), "0").to_pandas(),
        "dropoff": pc.fill_null(t.column("drop_off_type"), "0").to_pandas(),
    })
    return df


def expand_frequencies(z, st: pd.DataFrame, trips: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trips listed in frequencies.txt are templates: replicate them at headway_secs."""
    fr = _csv(z, "frequencies.txt")
    fr = fr[fr.trip_id.isin(set(trips.trip_id))]
    if fr.empty:
        return st, trips
    fr = fr.assign(start=_hms(pa.array(fr.start_time)), end=_hms(pa.array(fr.end_time)),
                   hw=fr.headway_secs.astype(int))
    tmpl_ids = set(fr.trip_id)
    base = st[st.trip_id.isin(tmpl_ids)]
    keep = st[~st.trip_id.isin(tmpl_ids)]
    new_st, new_trips = [keep], [trips[~trips.trip_id.isin(tmpl_ids)]]
    for tid, g in base.groupby("trip_id"):
        g = g.sort_values("seq")
        t0 = int(g.dep.iloc[0])
        trow = trips[trips.trip_id == tid].iloc[0]
        k = 0
        for _, f in fr[fr.trip_id == tid].iterrows():
            for start in range(int(f.start), int(f.end), int(f.hw)):
                if start + (g.arr.max() - t0) < EARLIEST_DEP or start > WINDOW[1]:
                    continue
                nid = f"{tid}#f{k}"
                k += 1
                new_st.append(g.assign(trip_id=nid, arr=g.arr - t0 + start, dep=g.dep - t0 + start))
                new_trips.append(pd.DataFrame([{**trow.to_dict(), "trip_id": nid}]))
    return pd.concat(new_st, ignore_index=True), pd.concat(new_trips, ignore_index=True)


def pairs_within(xy: np.ndarray, r: float) -> np.ndarray:
    """All index pairs (i < j) with Euclidean distance <= r (grid hashing, no scipy needed)."""
    cell = np.floor(xy / r).astype(np.int64)
    df = pd.DataFrame({"i": np.arange(len(xy)), "cx": cell[:, 0], "cy": cell[:, 1]})
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            o = df.assign(cx=df.cx + dx, cy=df.cy + dy)
            m = df.merge(o, on=["cx", "cy"], suffixes=("", "_o"))
            m = m[m.i < m.i_o]
            out.append(m[["i", "i_o"]].to_numpy())
    p = np.unique(np.vstack(out), axis=0)
    d = np.hypot(*(xy[p[:, 0]] - xy[p[:, 1]]).T)
    return p[d <= r]


def build(date: dt.date = SERVICE_DATE, feed: str = FEED) -> dict:
    z = zipfile.ZipFile(gtfs(feed))
    services = active_services(z, date)
    trips = _csv(z, "trips.txt", usecols=["route_id", "service_id", "trip_id"])
    trips = trips[trips.service_id.isin(services)].drop(columns="service_id")
    routes = _csv(z, "routes.txt")[["route_id", "agency_id", "route_short_name", "route_type"]]
    trips = trips.merge(routes, on="route_id", how="left")
    print(f"{date}: {len(services)} services, {len(trips)} trips")

    st = read_stop_times(z, set(trips.trip_id))
    print("stop_times rows", len(st))
    st, trips = expand_frequencies(z, st, trips)

    # ---- stations
    stops = _csv(z, "stops.txt")
    parents = stops[stops.location_type == "1"].copy()
    parents["station_id"] = parents.stop_id
    child = stops[stops.location_type != "1"].set_index("stop_id").parent_station
    st["station_id"] = st.stop_id.map(child)
    miss = st.station_id.isna()
    if miss.any():  # platform stops without parent: they become their own station
        print("stop_times stops without parent:", miss.sum())
        st.loc[miss, "station_id"] = st.loc[miss, "stop_id"]
        orphans = stops[stops.stop_id.isin(set(st.loc[miss, "stop_id"]))].assign(station_id=lambda d: d.stop_id)
        parents = pd.concat([parents, orphans])
    used = pd.Index(st.station_id.unique())
    sta = parents[parents.station_id.isin(used)][["station_id", "didok", "stop_name", "stop_lon", "stop_lat"]]
    sta = sta.rename(columns={"stop_name": "name", "stop_lon": "lon", "stop_lat": "lat"})
    sta[["lon", "lat"]] = sta[["lon", "lat"]].astype(float)
    sta = sta.sort_values("station_id").reset_index(drop=True)
    sta["idx"] = np.arange(len(sta), dtype=np.int32)
    tf = Transformer.from_crs(4326, 2056, always_xy=True)
    sta["x"], sta["y"] = tf.transform(sta.lon.values, sta.lat.values)
    sidx = sta.set_index("station_id").idx

    # ---- connections
    trips = trips.reset_index(drop=True)
    trips["trip"] = np.arange(len(trips), dtype=np.int32)
    tnum = trips.set_index("trip_id").trip
    st["trip"] = st.trip_id.map(tnum).astype(np.int32)
    st["sidx"] = st.station_id.map(sidx).astype(np.int32)
    st = st.sort_values(["trip", "seq"]).reset_index(drop=True)
    nxt = st.shift(-1)
    same = (nxt.trip == st.trip).to_numpy()
    con = pd.DataFrame({
        "dep": st.dep.to_numpy()[same], "arr": nxt.arr.to_numpy()[same].astype(np.int32),
        "from_idx": st.sidx.to_numpy()[same], "to_idx": nxt.sidx.to_numpy()[same].astype(np.int32),
        "trip": st.trip.to_numpy()[same], "seq": st.seq.to_numpy()[same],
        "board": (st.pickup.to_numpy()[same] != "1"), "alight": (nxt.dropoff.to_numpy()[same] != "1"),
        "from_stop_id": st.stop_id.to_numpy()[same], "to_stop_id": nxt.stop_id.to_numpy()[same],
    })
    con = con[(con.from_idx != con.to_idx) | (con.arr > con.dep)]  # drop zero moves at one station
    rt = trips.set_index("trip").route_type.astype(int)
    con["route_type"] = con.trip.map(rt).astype(np.int16)

    # in-seat transfers (transfer_type 4): trip A arriving at stop s continues as trip B
    trf = _csv(z, "transfers.txt")
    tid = set(trips.trip_id)
    seat = trf[(trf.transfer_type == "4") & trf.from_trip_id.isin(tid) & trf.to_trip_id.isin(tid)]
    con["chain_trip"] = np.int32(-1)
    if len(seat):
        seat = seat.assign(a=seat.from_trip_id.map(tnum), b=seat.to_trip_id.map(tnum),
                           s=seat.from_stop_id.map(child).fillna(seat.from_stop_id).map(sidx))
        seat = seat.dropna(subset=["s"]).astype({"s": np.int32})
        key = pd.MultiIndex.from_arrays([seat.a, seat.s])
        lk = pd.Series(seat.b.to_numpy(), index=key)
        lk = lk[~lk.index.duplicated()]
        k2 = pd.MultiIndex.from_arrays([con.trip, con.to_idx])
        con["chain_trip"] = lk.reindex(k2).fillna(-1).astype(np.int32).to_numpy()
    con = con[(con.dep >= EARLIEST_DEP) & (con.dep <= WINDOW[1])]
    con = con.sort_values(["dep", "arr", "trip", "seq"]).reset_index(drop=True)
    print("connections", len(con))

    # ---- minimum change times
    s = trf[trf.from_trip_id.isna() & trf.from_route_id.isna() & (trf.transfer_type == "2")].copy()
    s["fp"] = s.from_stop_id.map(child)
    s["tp"] = s.to_stop_id.map(child)
    s["mt"] = s.min_transfer_time.astype(float)
    inside = s[s.fp == s.tp]
    generic = inside[(inside.from_stop_id == inside.to_stop_id)
                     & (inside.fp.str.replace("Parent", "", regex=False) == inside.from_stop_id)]
    mct = generic.groupby("fp").mt.min()
    cross = inside[inside.from_stop_id != inside.to_stop_id].groupby("fp").mt.median()
    selfr = inside[inside.from_stop_id == inside.to_stop_id].groupby("fp").mt.median().clip(lower=DEFAULT_MCT)
    v = sta.station_id.map(mct).fillna(sta.station_id.map(cross)).fillna(sta.station_id.map(selfr))
    sta["mct_s"] = v.fillna(DEFAULT_MCT).clip(upper=MAX_MCT).astype(np.int32)
    sta["mct_source"] = np.select(
        [sta.station_id.isin(mct.index), sta.station_id.isin(cross.index), sta.station_id.isin(selfr.index)],
        ["station rule", "median of platform-to-platform rules", "same-platform rules (at least 120 s)"],
        "default 120 s")

    # ---- footpaths
    xy = sta[["x", "y"]].to_numpy()
    pairs = pairs_within(xy, FOOT_RADIUS)
    d = np.hypot(*(xy[pairs[:, 0]] - xy[pairs[:, 1]]).T)
    fp = pd.DataFrame({"from_idx": np.r_[pairs[:, 0], pairs[:, 1]], "to_idx": np.r_[pairs[:, 1], pairs[:, 0]],
                       "walk_s": np.r_[d, d] * DETOUR / WALK_SPEED, "source": "distance"})
    # isolated stations (nothing within 400 m, e.g. a cableway valley station off the bus line):
    # link to the nearest station within 1 km so that they are not cut off
    iso = np.setdiff1d(np.arange(len(xy)), pairs.ravel())
    far = pairs_within(xy, ISOLATED_RADIUS)
    far = far[np.isin(far[:, 0], iso) | np.isin(far[:, 1], iso)]
    df_far = pd.DataFrame({"a": np.r_[far[:, 0], far[:, 1]], "b": np.r_[far[:, 1], far[:, 0]]})
    df_far = df_far[df_far.a.isin(iso)]
    df_far["d"] = np.hypot(*(xy[df_far.a] - xy[df_far.b]).T)
    df_far = df_far.sort_values("d").drop_duplicates("a")
    extra = pd.DataFrame({"from_idx": np.r_[df_far.a, df_far.b], "to_idx": np.r_[df_far.b, df_far.a],
                          "walk_s": np.r_[df_far.d, df_far.d] * DETOUR / WALK_SPEED, "source": "isolated station link"})
    fp = pd.concat([fp, extra]).drop_duplicates(["from_idx", "to_idx"])
    between = s[(s.fp != s.tp) & s.fp.isin(sidx.index) & s.tp.isin(sidx.index)]
    between = between.groupby(["fp", "tp"]).mt.median().reset_index()
    between = pd.DataFrame({"from_idx": between.fp.map(sidx).to_numpy(), "to_idx": between.tp.map(sidx).to_numpy(),
                            "walk_s": between.mt.to_numpy(), "source": "transfers.txt"})
    fp = pd.concat([between, fp]).drop_duplicates(["from_idx", "to_idx"], keep="first")
    fp["walk_s"] = np.ceil(fp.walk_s).astype(np.int32)
    fp = fp.astype({"from_idx": np.int32, "to_idx": np.int32}).sort_values(["from_idx", "walk_s"]).reset_index(drop=True)

    # ---- stations -> municipality (reference state)
    gem = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde")[["id", "geometry"]]
    pts = gpd.GeoDataFrame(sta[["idx"]], geometry=gpd.points_from_xy(sta.x, sta.y), crs=2056)
    j = gpd.sjoin(pts, gem, how="left", predicate="within").drop_duplicates("idx").set_index("idx")
    sta["bfs_nr"] = sta.idx.map(j["id"]).astype("Int32")
    rail_types = set(range(100, 118)) | {2}
    rail_st = set(con.loc[con.route_type.isin(rail_types), "from_idx"]) | set(con.loc[con.route_type.isin(rail_types), "to_idx"])
    sta["rail"] = sta.idx.isin(rail_st)
    sv = con[(con.dep >= SERVED[0]) & (con.dep <= SERVED[1])]
    sta["served_in_window"] = sta.idx.isin(set(sv.from_idx) | set(sv.to_idx))
    # departures 06:30-18:00 per station (boardable), all modes and rail only: main-station choice (pt.py)
    dep_all = sv[sv.board].groupby("from_idx").size()
    dep_rail = sv[sv.board & sv.route_type.isin(rail_types)].groupby("from_idx").size()
    sta["n_dep"] = sta.idx.map(dep_all).fillna(0).astype(np.int32)
    sta["n_dep_rail"] = sta.idx.map(dep_rail).fillna(0).astype(np.int32)

    od = outdir(date)
    sta.to_parquet(od / "stations.parquet")
    con.to_parquet(od / "connections.parquet")
    fp.to_parquet(od / "footpaths.parquet")
    trips.drop(columns=[]).to_parquet(od / "trips.parquet")
    meta = {"feed": feed, "service_date": date.isoformat(), "services": len(services), "trips": len(trips),
            "connections": len(con), "stations": len(sta), "footpaths": len(fp),
            "stations_in_ch": int(sta.bfs_nr.notna().sum()),
            "window": [EARLIEST_DEP, WINDOW[1]], "served_window": list(SERVED)}
    (od / "meta.json").write_text(json.dumps(meta, indent=1))
    print(meta)
    return meta


if __name__ == "__main__":
    build()
