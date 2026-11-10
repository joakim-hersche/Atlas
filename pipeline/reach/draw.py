"""Growing-network line files for the reach animation (CLAUDE.md 5.1).

One compact JSON per hub and mode: data/out/reach/<hub>_<mode>.json

  {"hub": slug, "name": ..., "mode": "pt"|"car", "unit": "min", "kinds": {...},
   "segments": [[t_start, t_end, kind, [lon, lat, lon, lat, ...]], ...], ...}

t_start / t_end are minutes at the first / last vertex; the frontend interpolates linearly along
the segment's length. Coordinates are WGS84 rounded to 5 decimals, geometry simplified.

PT: the CSA journey tree at the representative departure (pt.representative_departure: the
departure minute whose station journey times are closest to the per-station medians), restricted
to the journeys to each municipality's earliest-reached station. Used connections become
stop-to-stop legs. Rail, tram and funicular legs follow the BAV rail network (Schienennetz:
stations are projected onto the nearest Netzsegment within 150 m and the shortest path on the
segment graph is taken); legs that cannot be matched, and bus/boat/cableway legs, are straight
lines. Footpaths are straight lines. Times are minutes after the representative departure
(they include the wait at the hub for the first vehicle).

Car: shortest-path tree from the hub on the swissTLMRegio road graph with assumed speeds per road
class (SPEEDS; drawing only), restricted to the paths to every municipality's centroid node. The
tree times are then rescaled so that arrivals at municipality centroids follow the NPVM car times
(official values; see `rescale`).
"""
from __future__ import annotations

import gzip
import heapq
import json
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pyogrio
import shapely
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import linemerge, substring

from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.reach.csa import Network, journey_tree
from pipeline.reach.fetch import tlmregio
from pipeline.reach.gtfs_prep import SERVICE_DATE
from pipeline.sources.bav_rail.fetch import schienennetz

warnings.filterwarnings("ignore", message="Measured")
TO_WGS = Transformer.from_crs(2056, 4326, always_xy=True)
KINDS = {0: "road", 1: "rail", 2: "bus/boat/cableway (straight line)", 3: "walk"}
RAIL_TYPES = set(range(100, 118)) | {2, 0, 400, 401, 402, 403, 900, 901, 902, 1400}
SIMPLIFY_M = {"pt": 25.0, "car": 40.0}

# assumed free-flow speeds (km/h) per swissTLMRegio road class, for the drawing only
SPEEDS = {
    "Autobahn": 110, "Autob_Ri": 110, "Autobahn_Rampe": 60, "Autob_Ri_Rampe": 60,
    "Autostr": 90, "Autostr_Rampe": 50,
    "HauptStrAB6": 70, "HauptStrAB4": 60, "HauptStrAB_Rampe": 50,
    "VerbindStr6": 60, "VerbindStr4": 50, "VerbindStr_Rampe": 40,
    "NebenStr6": 40, "NebenStr3": 30, "NebenStr_Rampe": 30,
    "Fahrstraes": 20,
    # "Fussweg" (footpaths) excluded; roads flagged banned=True excluded
}


# ----------------------------------------------------------------------------- output helpers
def _coords(geom: LineString, tol: float) -> list[float]:
    g = geom.simplify(tol, preserve_topology=False) if tol else geom
    xy = np.asarray(g.coords)[:, :2]
    lon, lat = TO_WGS.transform(xy[:, 0], xy[:, 1])
    flat = np.round(np.column_stack([lon, lat]).ravel(), 5)
    # drop consecutive duplicates after rounding
    pts = flat.reshape(-1, 2)
    keep = np.r_[True, np.any(np.diff(pts, axis=0) != 0, axis=1)]
    pts = pts[keep]
    if len(pts) < 2:
        pts = np.vstack([pts, pts])
    return [float(v) for v in pts.ravel()]


def write(slug: str, mode: str, payload: dict) -> dict:
    p = out_path("reach", f"{slug}_{mode}.json")
    txt = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    p.write_text(txt, encoding="utf-8")
    gz = len(gzip.compress(txt.encode("utf-8"), 9))
    return {"hub": slug, "mode": mode, "file": p.name, "bytes": len(txt.encode()), "gzip_bytes": gz,
            "segments": len(payload["segments"])}


# ----------------------------------------------------------------------------- rail network
class RailGraph:
    """BAV Schienennetz segments split at projected GTFS stations."""

    MAX_SNAP = 150.0

    def __init__(self, stations: pd.DataFrame):
        p = schienennetz()
        seg = pyogrio.read_dataframe(p, layer="Netzsegment", columns=["rAnfangsknoten", "rEndknoten"])
        seg["geometry"] = seg.geometry.apply(lambda g: linemerge(g) if g.geom_type == "MultiLineString" else g)
        seg["geometry"] = shapely.force_2d(seg.geometry.values)
        seg = seg[seg.geometry.geom_type == "LineString"].reset_index(drop=True)
        self.seg = seg
        st = stations[stations.served_in_window].reset_index(drop=True)
        pts = shapely.points(st.x.to_numpy(), st.y.to_numpy())
        tree = shapely.STRtree(seg.geometry.values)
        # every segment within 150 m of a station gets a cut point (parallel lines of different
        # gauges/operators at one station are all attached)
        si, gi = tree.query(pts, predicate="dwithin", distance=self.MAX_SNAP)
        snaps = pd.DataFrame({"idx": st.idx.to_numpy()[si], "seg": gi})
        geoms = seg.geometry.values
        snaps["pos"] = [geoms[g].project(pts[s]) for s, g in zip(si, gi)]
        snaps["d"] = [geoms[g].distance(pts[s]) for s, g in zip(si, gi)]
        self.snapped = set(snaps.idx)
        G = nx.Graph()

        def node(xy):  # segment end points: merged on a 2 m grid (robust to id gaps)
            return f"n:{round(xy[0] / 2)}:{round(xy[1] / 2)}"

        by_seg = {g: grp.sort_values("pos") for g, grp in snaps.groupby("seg")}
        refs_a, refs_b = seg.rAnfangsknoten.to_numpy(), seg.rEndknoten.to_numpy()
        for k, line in enumerate(geoms):
            c = line.coords
            # topology from the node references as well (segment ends do not always coincide)
            for ref, xy in ((refs_a[k], c[0]), (refs_b[k], c[-1])):
                if isinstance(ref, str) and ref:
                    G.add_edge(f"id:{ref}", node(xy), length=1.0, geom=None, start=None)
            cuts = [(0.0, node(c[0]))]
            if k in by_seg:
                for r in by_seg[k].itertuples():
                    cuts.append((r.pos, f"c:{r.idx}:{k}"))
                    G.add_edge(f"s:{r.idx}", f"c:{r.idx}:{k}", length=r.d + 50.0, geom=None, start=None)
            cuts.append((line.length, node(c[-1])))
            for (p0, u), (p1, v) in zip(cuts[:-1], cuts[1:]):
                if u == v:
                    continue
                piece = substring(line, p0, p1) if p1 > p0 else LineString([line.interpolate(p0)] * 2)
                L = max(p1 - p0, 0.01)
                if G.has_edge(u, v) and G[u][v]["length"] <= L:
                    continue
                G.add_edge(u, v, length=L, geom=piece, start=u)
        self.G = G
        self._cache: dict[tuple[int, int], LineString | None] = {}

    def path(self, a: int, b: int, straight: float) -> LineString | None:
        key = (a, b)
        if key in self._cache:
            return self._cache[key]
        res = None
        if a in self.snapped and b in self.snapped:
            try:
                L, nodes = nx.bidirectional_dijkstra(self.G, f"s:{a}", f"s:{b}", weight="length")
                if L <= 2.5 * straight + 1000:
                    parts = []
                    for u, v in zip(nodes[:-1], nodes[1:]):
                        e = self.G[u][v]
                        if e["geom"] is None:      # station connector: no geometry
                            continue
                        c = list(e["geom"].coords)
                        if e["start"] != u:
                            c = c[::-1]
                        if parts and parts[-1] == c[0]:
                            c = c[1:]
                        parts.extend(c)
                    if len(parts) >= 2:
                        res = LineString(parts)
            except nx.NetworkXNoPath:
                res = None
        self._cache[key] = res
        return res


def pt_segments(net: Network, rail: RailGraph, src: list[int], t0: int, cutoff: int) -> list:
    res = net.run(src, t0, cutoff)
    ea = res[0]
    sta = net.stations
    ins = sta[sta.bfs_nr.notna()].assign(ea=lambda d: ea[d.idx.to_numpy()])
    ins = ins[ins.ea < cutoff]
    targets = ins.sort_values("ea").drop_duplicates("bfs_nr").idx.to_numpy()
    used, foot = journey_tree(net, res, targets)
    con = net.connections.iloc[used]
    xy = sta[["x", "y"]].to_numpy()
    segs = []
    # group consecutive used connections of a trip into legs between drawn stops
    for c in con.itertuples():
        a, b = int(c.from_idx), int(c.to_idx)
        ts, te = (c.dep - t0) / 60, (c.arr - t0) / 60
        straight = float(np.hypot(*(xy[a] - xy[b])))
        geom, kind = None, 2
        if c.route_type in RAIL_TYPES:
            geom = rail.path(a, b, straight)
            kind = 1 if geom is not None else 2
        if geom is None:
            geom = LineString([xy[a], xy[b]])
        segs.append([round(ts, 1), round(te, 1), kind, geom])
    for v in np.flatnonzero(foot >= 0):
        u = int(foot[v])
        t_u, t_v = (ea[u] - t0) / 60, (ea[v] - t0) / 60
        segs.append([round(max(t_u, 0), 1), round(t_v, 1), 3, LineString([xy[u], xy[v]])])
    return segs


def build_pt(net: Network, rail: RailGraph, slug: str, name: str, src: list[int], k: int, cutoff: int) -> dict:
    from pipeline.reach.pt import T_FIRST
    t0 = T_FIRST + 60 * k
    segs = pt_segments(net, rail, src, t0, cutoff)
    segs.sort(key=lambda s: s[0])
    out = [[s[0], s[1], s[2], _coords(s[3], SIMPLIFY_M["pt"] if s[2] == 1 else 0)] for s in segs]
    hh, mm = divmod(t0 // 60, 60)
    payload = {"hub": slug, "name": name, "mode": "pt", "unit": "min", "departure": f"{hh:02d}:{mm:02d}",
               "service_date": SERVICE_DATE.isoformat(),
               "note": "times are minutes after the departure time (include the wait at the hub)",
               "kinds": KINDS, "segments": out}
    return write(slug, "pt", payload)


# ----------------------------------------------------------------------------- road network
class RoadGraph:
    def __init__(self):
        p = tlmregio()
        path = f"/vsizip/{p}/swissTLMRegio_Product_LV95.gpkg"
        r = pyogrio.read_dataframe(path, layer="tlmregio_transportation_road", columns=["objval", "banned"])
        r = r[r.objval.isin(SPEEDS) & (r.banned.astype(str) != "True")].reset_index(drop=True)
        r["geometry"] = shapely.force_2d(r.geometry.values)
        self.roads = r
        xy0 = shapely.get_coordinates(shapely.get_point(r.geometry.values, 0))
        xy1 = shapely.get_coordinates(shapely.get_point(r.geometry.values, -1))
        key = lambda a: [f"{x:.1f},{y:.1f}" for x, y in a]
        k0, k1 = key(xy0), key(xy1)
        nodes = pd.Index(pd.unique(np.r_[k0, k1]))
        self.node_xy = np.array([tuple(map(float, n.split(","))) for n in nodes])
        self.u = nodes.get_indexer(k0)
        self.v = nodes.get_indexer(k1)
        self.length = r.geometry.length.to_numpy()
        self.speed = r.objval.map(SPEEDS).to_numpy(float)
        self.w = self.length / (self.speed / 3.6) / 60.0  # minutes
        n = len(nodes)
        adj = [[] for _ in range(n)]
        for e, (a, b, w) in enumerate(zip(self.u, self.v, self.w)):
            adj[a].append((b, w, e))
            adj[b].append((a, w, e))
        self.adj = adj
        self.n = n

    def nearest_node(self, x: float, y: float) -> int:
        return int(np.argmin(np.hypot(self.node_xy[:, 0] - x, self.node_xy[:, 1] - y)))

    def tree(self, root: int):
        dist = np.full(self.n, np.inf)
        pred_e = np.full(self.n, -1, np.int64)
        dist[root] = 0.0
        h = [(0.0, root)]
        while h:
            d, a = heapq.heappop(h)
            if d > dist[a]:
                continue
            for b, w, e in self.adj[a]:
                nd = d + w
                if nd < dist[b]:
                    dist[b] = nd
                    pred_e[b] = e
                    heapq.heappush(h, (nd, b))
        return dist, pred_e

    def other(self, e: int, a: int) -> int:
        return int(self.v[e]) if self.u[e] == a else int(self.u[e])


def rescale(rg: RoadGraph, dist, pred_e, anchors: dict[int, float], iters: int = 6):
    """Rescale tree times so that anchor nodes (municipality centroids) arrive at the NPVM time.

    Edge time multiplier kappa(v) for the edge into node v = mean of (target / current) over the
    anchors in v's subtree; repeated a few times (iterative proportional fitting). Times stay
    monotone along every path (kappa > 0). Returns new node times (minutes)."""
    reach = np.flatnonzero(np.isfinite(dist))
    parent = np.full(rg.n, -1, np.int64)
    kids: dict[int, list[int]] = {}
    root = -1
    for v in reach:
        e = pred_e[v]
        if e >= 0:
            parent[v] = rg.other(e, v)
            kids.setdefault(int(parent[v]), []).append(int(v))
        else:
            root = int(v)
    order, q = [], [root]                                  # BFS: parents before children
    while q:
        a = q.pop()
        order.append(a)
        q.extend(kids.get(a, ()))
    order = np.array(order, np.int64)
    base = np.zeros(rg.n)
    for v in order:
        e = pred_e[v]
        if e >= 0:
            base[v] = rg.w[e]
    kappa = np.ones(rg.n)
    t = dist.copy()
    an = np.array(list(anchors.keys()), np.int64)
    tgt = np.array(list(anchors.values()))
    for _ in range(iters):
        ratio_sum = np.zeros(rg.n)
        cnt = np.zeros(rg.n)
        cur = t[an]
        rr = np.where(cur > 0, tgt / np.maximum(cur, 1e-6), 1.0)
        np.add.at(ratio_sum, an, rr)
        np.add.at(cnt, an, 1.0)
        for v in order[::-1]:                              # children before parents
            p = parent[v]
            if p >= 0:
                ratio_sum[p] += ratio_sum[v]
                cnt[p] += cnt[v]
        f = np.where(cnt > 0, ratio_sum / np.maximum(cnt, 1), 1.0)
        kappa = kappa * f
        t = np.full(rg.n, np.inf)
        t[root] = 0.0
        for v in order[1:]:
            t[v] = t[parent[v]] + base[v] * kappa[v]
    return t, parent


def build_car(rg: RoadGraph, slug: str, name: str, hub_xy, npvm_times: pd.Series, gem: gpd.GeoDataFrame) -> dict:
    root = rg.nearest_node(*hub_xy)
    dist, pred_e = rg.tree(root)
    # municipality centroid -> nearest reached road node within 3 km
    reached = np.flatnonzero(np.isfinite(dist))
    rp = gem.geometry.representative_point()
    cen = gem.geometry.centroid
    cen = cen.where(gem.geometry.contains(cen), rp)
    pts = shapely.points(rg.node_xy[reached])
    tree = shapely.STRtree(pts)
    qi, ni = tree.query_nearest(cen.values, max_distance=3000, return_distance=False, all_matches=False)
    anchor_node = pd.Series(reached[ni], index=gem["id"].to_numpy()[qi])
    anchors = {}
    for bfs, node in anchor_node.items():
        v = npvm_times.get(bfs)
        if v is not None and np.isfinite(v):
            anchors[int(node)] = max(anchors.get(int(node), 0), float(v))
    t, parent = rescale(rg, dist, pred_e, anchors)
    # keep only the edges on paths to the anchors
    keep = np.zeros(len(rg.u), bool)
    seen = np.zeros(rg.n, bool)
    for a in anchor_node.to_numpy():
        v = int(a)
        while v != root and not seen[v]:
            seen[v] = True
            e = pred_e[v]
            if e < 0:
                break
            keep[e] = True
            v = int(parent[v])
    # anchor fit diagnostics
    an = np.array(list(anchors.keys()))
    err = t[an] - np.array([anchors[a] for a in an])
    segs = []
    # merge chains of kept edges with the same speed (time linear in length) into polylines
    E = np.flatnonzero(keep)
    child = {}
    for e in E:
        a, b = int(rg.u[e]), int(rg.v[e])
        c = b if parent[b] == a else a                      # the endpoint farther from the root
        child[e] = c
    deg = np.zeros(rg.n, int)
    for e in E:
        deg[rg.u[e]] += 1
        deg[rg.v[e]] += 1
    out_of = {}
    for e, c in child.items():
        out_of.setdefault(int(parent[c]), []).append(e)
    done = set()
    for e0 in sorted(E, key=lambda e: t[parent[child[e]]]):
        if e0 in done:
            continue
        chain = [e0]
        done.add(e0)
        c = child[e0]
        while deg[c] == 2 and c in out_of and len(out_of[c]) == 1:
            nxt = out_of[c][0]
            if nxt in done or rg.speed[nxt] != rg.speed[e0]:
                break
            chain.append(nxt)
            done.add(nxt)
            c = child[nxt]
        start = int(parent[child[chain[0]]])
        coords = []
        node = start
        for e in chain:
            g = np.asarray(rg.roads.geometry.iloc[e].coords)
            if int(rg.u[e]) != node:
                g = g[::-1]
            coords.extend(g.tolist() if not coords else g[1:].tolist())
            node = child[e]
        segs.append([round(float(t[start]), 1), round(float(t[node]), 1), 0, LineString(coords)])
    segs.sort(key=lambda s: s[0])
    out = [[s[0], s[1], 0, _coords(s[3], SIMPLIFY_M["car"])] for s in segs]
    payload = {"hub": slug, "name": name, "mode": "car", "unit": "min",
               "note": ("swissTLMRegio roads; tree times rescaled to the ARE NPVM 2023 car travel "
                        "times (average weekday) at municipality centroids"),
               "kinds": {0: "road"}, "segments": out}
    info = write(slug, "car", payload)
    info.update({"anchors": len(anchors), "anchor_mae_min": round(float(np.mean(np.abs(err))), 2),
                 "anchor_p90_abs_err_min": round(float(np.percentile(np.abs(err), 90)), 2)})
    return info


def reference_municipalities() -> gpd.GeoDataFrame:
    return gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde")[["id", "geometry"]]
