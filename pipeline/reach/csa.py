"""Connection Scan Algorithm (earliest arrival) over one service day, in numba.

Model
- Stations are GTFS parent stations (platforms collapsed). A connection is one vehicle moving between
  two consecutive stops of a trip; connections are sorted by departure time.
- Changing to another trip at a station needs the station's minimum change time (mct_s);
  staying on the same trip needs none; in-seat transfers (GTFS transfer_type 4) continue the
  journey on the linked trip without a change.
- Footpaths link stations within 400 m (and pairs given in transfers.txt); they are relaxed once
  after every improved arrival (not transitively closed).
- pickup_type / drop_off_type = 1 are respected (board / alight flags).

`run()` returns the earliest arrival (seconds after midnight, INF if not reached) at every station
for one departure time from a set of source stations, plus the journey tree:
  in_conn[s]   connection by which s was first reached (-1 if by footpath or source)
  in_foot[s]   station the footpath into s started from (-1 otherwise)
  entry[t]     first connection used on trip t; -(i + 2) if t was entered in-seat from connection i;
               NONE (-1) if unused
"""
from __future__ import annotations

from dataclasses import dataclass

import numba as nb
import numpy as np
import pandas as pd

INF = np.int32(2 ** 30)
NONE = -1


@dataclass
class Network:
    dep: np.ndarray
    arr: np.ndarray
    frm: np.ndarray
    to: np.ndarray
    trip: np.ndarray
    board: np.ndarray
    alight: np.ndarray
    chain: np.ndarray
    mct: np.ndarray
    fp_start: np.ndarray
    fp_to: np.ndarray
    fp_w: np.ndarray
    n_trips: int
    stations: pd.DataFrame
    connections: pd.DataFrame
    trips: pd.DataFrame

    @classmethod
    def load(cls, d):
        sta = pd.read_parquet(d / "stations.parquet")
        con = pd.read_parquet(d / "connections.parquet")
        fp = pd.read_parquet(d / "footpaths.parquet").sort_values(["from_idx", "walk_s"])
        trips = pd.read_parquet(d / "trips.parquet")
        n = len(sta)
        counts = np.bincount(fp.from_idx.to_numpy(), minlength=n)
        start = np.zeros(n + 1, np.int64)
        start[1:] = np.cumsum(counts)
        return cls(con.dep.to_numpy(np.int32), con.arr.to_numpy(np.int32), con.from_idx.to_numpy(np.int32),
                   con.to_idx.to_numpy(np.int32), con.trip.to_numpy(np.int32), con.board.to_numpy(np.bool_),
                   con.alight.to_numpy(np.bool_), con.chain_trip.to_numpy(np.int32),
                   sta.mct_s.to_numpy(np.int32), start, fp.to_idx.to_numpy(np.int32),
                   fp.walk_s.to_numpy(np.int32), int(trips.trip.max()) + 1, sta, con, trips)

    def run(self, sources, t0: int, cutoff: int):
        src = np.asarray(sources, np.int32)
        i0 = int(np.searchsorted(self.dep, t0, side="left"))
        return _csa(src, np.int32(t0), np.int32(cutoff), i0, self.dep, self.arr, self.frm, self.to, self.trip,
                    self.board, self.alight, self.chain, self.mct, self.fp_start, self.fp_to, self.fp_w,
                    self.n_trips)


@nb.njit(cache=True)
def _csa(src, t0, cutoff, i0, dep, arr, frm, to, trip, board, alight, chain, mct, fp_start, fp_to, fp_w,
         n_trips):
    n = mct.shape[0]
    ea = np.full(n, INF, np.int32)
    ready = np.full(n, INF, np.int32)
    in_conn = np.full(n, -1, np.int32)
    in_foot = np.full(n, -1, np.int32)
    entry = np.full(n_trips, -1, np.int64)
    for k in range(src.shape[0]):
        s = src[k]
        ea[s] = t0
        ready[s] = t0
    for k in range(src.shape[0]):
        s = src[k]
        for j in range(fp_start[s], fp_start[s + 1]):
            u = fp_to[j]
            t = t0 + fp_w[j]
            if t < ea[u]:
                ea[u] = t
                in_foot[u] = s
            if t < ready[u]:
                ready[u] = t
    m = dep.shape[0]
    for i in range(i0, m):
        if dep[i] > cutoff:
            break
        tr = trip[i]
        if entry[tr] == -1:
            if board[i] and ready[frm[i]] <= dep[i]:
                entry[tr] = i
            else:
                continue
        c = chain[i]
        if c >= 0 and entry[c] == -1:
            entry[c] = -(i + 2)
        if not alight[i]:
            continue
        v = to[i]
        t = arr[i]
        if t < ea[v]:
            ea[v] = t
            in_conn[v] = i
            in_foot[v] = -1
            r = t + mct[v]
            if r < ready[v]:
                ready[v] = r
            for j in range(fp_start[v], fp_start[v + 1]):
                u = fp_to[j]
                tw = t + fp_w[j]
                if tw < ready[u]:
                    ready[u] = tw
                if tw < ea[u]:
                    ea[u] = tw
                    in_conn[u] = -1
                    in_foot[u] = v
    return ea, in_conn, in_foot, entry


@nb.njit(cache=True)
def _prev_in_trip(trip, order_by_trip):
    """prev[i] = previous connection of the same trip (by sequence), or -1."""
    prev = np.full(trip.shape[0], -1, np.int64)
    for k in range(1, order_by_trip.shape[0]):
        a = order_by_trip[k - 1]
        b = order_by_trip[k]
        if trip[a] == trip[b]:
            prev[b] = a
    return prev


@nb.njit(cache=True)
def _trace(targets, in_conn, in_foot, entry, trip, frm, to, prev, used_conn, used_foot_from):
    """Mark the connections (and footpaths) on the journeys to the target stations."""
    for k in range(targets.shape[0]):
        v = targets[k]
        guard = 0
        while v >= 0 and guard < 100000:
            guard += 1
            if in_conn[v] >= 0:
                i = in_conn[v]
                # walk back along the trip(s) until the entry connection
                while True:
                    if used_conn[i]:
                        # rest of this path already traced
                        v = -2
                        break
                    used_conn[i] = True
                    e = entry[trip[i]]
                    if e == i:
                        v = frm[i]
                        break
                    if e <= -2:
                        feed = -(e + 2)
                        if frm[i] == to[feed]:
                            i = feed       # in-seat continuation: jump to the feeding trip
                            continue
                    if prev[i] == -1:
                        v = frm[i]
                        break
                    i = prev[i]
                if v == -2:
                    break
            elif in_foot[v] >= 0:
                if used_foot_from[v] >= 0:
                    break
                used_foot_from[v] = in_foot[v]
                v = in_foot[v]
            else:
                break


def journey_tree(net: Network, res, targets):
    ea, in_conn, in_foot, entry = res
    if not hasattr(net, "_prev"):
        order = np.lexsort((net.connections.seq.to_numpy(), net.trip))
        net._prev = _prev_in_trip(net.trip, order.astype(np.int64))
    used = np.zeros(net.dep.shape[0], np.bool_)
    foot = np.full(ea.shape[0], -1, np.int32)
    _trace(np.asarray(targets, np.int32), in_conn, in_foot, entry, net.trip, net.frm, net.to, net._prev, used, foot)
    return np.flatnonzero(used), foot
