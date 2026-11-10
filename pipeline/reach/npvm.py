"""NPVM 2023 travel-time matrices (ARE, average weekday): hub zone -> all zones.

Matrices ($O format, 'from to value' lines, sorted by origin) are streamed from the zip and only
rows whose origin is a hub zone are kept:
  car: 4_TTC_PW_NPVM_2023 (Reisezeit PW, minutes)
  pt:  4_RITA_ACT_EGT_NPVM_2023 (Reisezeit OeV = Befoerderungszeit RITA + Zugangszeit ACT +
       Abgangszeit EGT, minutes; 999999 = no PT connection)

Hub zone = NPVM zone polygon containing the hub's main station (GTFS parent-station coordinates).

Municipality value (car, decision D11): population-weighted mean over the zones of the municipality,
with weights from STATPOP 2025 hectares (the NPVM record ships no zone population; its structural
data are on SWISSUbase behind registration). Each populated hectare centre is placed in its NPVM
zone and in its reference-state (2026-01-01) municipality by point-in-polygon, so the 2023 zone
municipality ids are not needed and boundary changes 2023 -> 2026 are handled spatially
(equivalent to pipeline.backbone.vintage.to_vintage with rule weighted_mean:population, but exact
for zones split by a merger).
"""
from __future__ import annotations

import subprocess
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.reach.hubs import HUBS
from pipeline.sources.are_npvm.fetch import get

NO_PT = 999999


def zones() -> gpd.GeoDataFrame:
    p = get("zones")
    z = gpd.read_file(f"zip://{p}!1_Verkehrszonen_Schweiz_NPVM_2023.gpkg")
    return z.rename(columns={"No": "zone"}).astype({"zone": "int64"})


def hub_zones(stations: pd.DataFrame) -> pd.DataFrame:
    z = zones()
    rows = []
    for slug, name, didok in HUBS:
        s = stations[stations.didok == str(didok)].iloc[0]
        pt = gpd.GeoSeries(gpd.points_from_xy([s.x], [s.y]), crs=2056)
        hit = z[z.contains(pt.iloc[0])]
        rows.append({"hub": slug, "zone": int(hit.zone.iloc[0]), "zone_gem": hit.N_Gem.iloc[0]})
    return pd.DataFrame(rows)


def extract_rows(kind: str, origins: list[int], column: bool = False) -> pd.DataFrame:
    """Stream one matrix and keep the rows of the given origin zones (cached as parquet).
    column=True keeps the columns instead (all origins -> the given destination zones), with the
    result's 'origin' holding the hub zone and 'dest' the other zone (same layout as the rows)."""
    cache = interim_path("reach", f"npvm_{kind}_hub{'cols' if column else 'rows'}.parquet")
    if cache.exists():
        df = pd.read_parquet(cache)
        if df.origin.dtype == "int64" and set(origins) <= set(df.origin.unique()):
            return df[df.origin.isin(origins)]
    zp = get("car_time" if kind == "car" else "pt_time")
    inner = zipfile.ZipFile(zp).namelist()[0]
    keys = " ".join(str(o) for o in origins)
    awk = ("BEGIN{n=split(K,a,\" \");for(i=1;i<=n;i++)s[a[i]]=1} "
           + ("($2 in s){print $2\",\"$1\",\"$3}" if column else "($1 in s){print $1\",\"$2\",\"$3}"))
    proc = subprocess.run(f"unzip -p '{zp}' '{inner}' | awk -v K='{keys}' '{awk}'", shell=True,
                          capture_output=True, text=True, check=True)
    from io import StringIO
    df = pd.read_csv(StringIO(proc.stdout), names=["origin", "dest", "minutes"], dtype=str)
    # the $O file ends with a zone-name block ('<zone> <name>'): keep numeric triples only
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    df = df.astype({"origin": "int64", "dest": "int64", "minutes": "float64"})
    df.to_parquet(cache)
    return df


def hectares_in_zones(year: int = 2025) -> pd.DataFrame:
    """Populated hectare centres with NPVM zone and reference-state municipality."""
    cache = interim_path("reach", f"hectares_{year}.parquet")
    if cache.exists():
        return pd.read_parquet(cache)
    from pipeline.sources.bfs_statpop_geodata.fetch import hectare
    h = pd.read_parquet(hectare(year), columns=["RELI", "E_KOORD", "N_KOORD", "BBTOT"])
    h = h[h.BBTOT > 0].copy()
    h["x"] = h.E_KOORD + 50.0   # BFS hectare coordinates are the south-west corner
    h["y"] = h.N_KOORD + 50.0
    pts = gpd.GeoDataFrame(h[["RELI"]], geometry=gpd.points_from_xy(h.x, h.y), crs=2056)
    gem = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde")[["id", "geometry"]]
    a = gpd.sjoin(pts, gem, how="left", predicate="within").drop_duplicates("RELI")
    miss = a["id"].isna()
    if miss.any():  # centres on a border / in a lake: nearest municipality
        b = gpd.sjoin_nearest(pts[miss.values], gem, how="left", max_distance=200).drop_duplicates("RELI")
        a.loc[miss, "id"] = a.loc[miss, "RELI"].map(b.set_index("RELI")["id"])
    z = zones()[["zone", "geometry"]]
    c = gpd.sjoin(pts, z, how="left", predicate="within").drop_duplicates("RELI")
    miss = c["zone"].isna()
    if miss.any():
        d = gpd.sjoin_nearest(pts[miss.values], z, how="left", max_distance=500).drop_duplicates("RELI")
        c.loc[miss, "zone"] = c.loc[miss, "RELI"].map(d.set_index("RELI")["zone"])
    h["bfs_nr"] = h.RELI.map(a.set_index("RELI")["id"]).astype("Int32")
    h["zone"] = h.RELI.map(c.set_index("RELI")["zone"]).astype("Int64")
    h = h[["RELI", "x", "y", "BBTOT", "bfs_nr", "zone"]]
    h.to_parquet(cache)
    return h


def municipality_times(kind: str, stations: pd.DataFrame, to_hub: bool = False) -> pd.DataFrame:
    """Population-weighted mean NPVM time from each hub zone to every reference municipality
    (to_hub=True: from every zone to the hub zone, the matrix column)."""
    hz = hub_zones(stations)
    m = extract_rows(kind, hz.zone.tolist(), column=to_hub)
    h = hectares_in_zones().dropna(subset=["bfs_nr", "zone"])
    gem = gpd.read_file(interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg"), layer="gemeinde",
                        ignore_geometry=True)[["id"]]
    out = []
    for r in hz.itertuples():
        mm = m[m.origin == r.zone].set_index("dest").minutes
        if kind == "car":   # intrazonal car time (hub zone itself) is not in the matrix: treat as 0
            mm.loc[r.zone] = mm.get(r.zone, 0.0)
        v = h.zone.map(mm)
        nopt = v >= NO_PT     # 999999: no connection (PT) / no road access (car-free zones)
        hh = h.assign(v=v.where(~nopt), nopt=nopt)
        g = hh.assign(w=hh.BBTOT.where(hh.v.notna(), 0), vw=hh.v * hh.BBTOT).groupby("bfs_nr")
        res = pd.DataFrame({"minutes": g.vw.sum(min_count=1) / g.w.sum().replace(0, np.nan),
                            "pop": g.BBTOT.sum(), "pop_covered": g.w.sum(),
                            "pop_no_connection": hh.assign(p=hh.BBTOT.where(hh.nopt, 0)).groupby("bfs_nr").p.sum(),
                            "zones": g.zone.nunique()})
        res = gem.set_index("id").join(res).reset_index().rename(columns={"id": "bfs_nr"})
        res["hub"] = r.hub
        res["hub_zone"] = r.zone
        out.append(res)
    return pd.concat(out, ignore_index=True)


def zone_station_check(stations: pd.DataFrame) -> pd.DataFrame:
    """For the PT sanity check: NPVM PT time hub zone -> the zone containing each rail station."""
    z = zones()[["zone", "geometry"]]
    rs = stations[stations.rail & stations.bfs_nr.notna()]
    pts = gpd.GeoDataFrame(rs[["idx", "name", "bfs_nr"]], geometry=gpd.points_from_xy(rs.x, rs.y), crs=2056)
    j = gpd.sjoin(pts, z, how="inner", predicate="within").drop_duplicates("idx")
    return j[["idx", "name", "bfs_nr", "zone"]]
