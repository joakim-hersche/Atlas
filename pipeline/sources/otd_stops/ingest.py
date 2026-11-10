"""Public transport stops per municipality (atlas service points, current) and daily rail
boardings + alightings per municipality (SBB "Ein- und Aussteigende", 2018, 2022–2025).

Stops: service-point-v2 actual-date file (valid on the download day, 2026-11-10), Swiss service
points with stopPoint = true, status VALIDATED, stopPointType not OUT_OF_ORDER. fsoNumber is the
BFS number on the current state (6 boat stops coded to lake areas 9040, 9155, 9329 are assigned
to the nearest reference-state municipality polygon); infer_vintage gives the reference state (municipalities without
any stop are the only difference), and every fsoNumber is checked to be a reference municipality.
A stop serving several modes (meansOfTransport 'BUS|TRAM') counts once in the total and once in
each of its modes, so mode counts do not add up to the total. The register is complete, so a
municipality without a stop of a mode gets 0. Period '2026' (state of 2026-11-10).

Rail ridership: per station (UIC = service point number) the average daily boardings + alightings
(DTV, Monday–Sunday) and the weekday average (DWV), summed over the municipality's stations.
Caveats from the source: only the rail undertakings listed per station are counted (remarks name
the missing ones at large stations); transfers count twice; stations with fewer than 50 are
reported as a fixed 49. Infrastructure managers covered: SBB, BLS, RhB, MGB, ZB, SOB, MOB, MVR,
TRAVYS, OeBB, STB, BOB (e.g. RBS, SZU, Forchbahn are missing). Municipalities with no current rail
service point get 0; municipalities with a rail service point but no station in the file for that
year are 'not_covered'. Foreign stations (canton 'Ausland') are dropped.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit, infer_vintage
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.meteoswiss_climate import zonal
from pipeline.sources.otd_stops.fetch import ridership, service_points

SOURCE = "otd_stops"
PERIOD = "2026"
MODES = {
    "pt_stops_bus": {"BUS"},
    "pt_stops_tram_metro": {"TRAM", "METRO"},
    "pt_stops_rail": {"TRAIN", "RACK_RAILWAY"},
    "pt_stops_cableway": {"CABLE_CAR", "CHAIRLIFT", "CABLE_RAILWAY", "ELEVATOR"},
    "pt_stops_boat": {"BOAT"},
}
RAIL = MODES["pt_stops_rail"]


def _ref_ids() -> list[int]:
    mv, _ = load_backbone()
    return sorted(versions_at(mv, REFERENCE_DATE)["bfs_nr"].astype(int))


def stops() -> pd.DataFrame:
    sp = pd.read_csv(service_points(), sep=";", encoding="utf-8-sig", dtype=str)
    sp = sp[(sp["isoCountryCode"] == "CH") & (sp["stopPoint"] == "true") & (sp["status"] == "VALIDATED")
            & (sp["stopPointType"].fillna("") != "OUT_OF_ORDER")].copy()
    sp["bfs_nr"] = sp["fsoNumber"].astype(int)
    sp["number"] = sp["number"].astype(int)
    sp["modes"] = sp["meansOfTransport"].fillna("").str.split("|").map(set)
    lake = sp["bfs_nr"] >= 9000  # boat stops coded to a lake area (no municipality)
    if lake.any():
        pts = gpd.GeoDataFrame(sp.loc[lake, ["number"]], crs=2056, geometry=gpd.points_from_xy(
            sp.loc[lake, "lv95East"].astype(float), sp.loc[lake, "lv95North"].astype(float)))
        j = gpd.sjoin_nearest(pts, zonal._polygons(), how="left", max_distance=2000)
        j = j[~j.index.duplicated()]
        if j["id"].isna().any():
            raise ValueError(f"lake stops without a municipality within 2 km: {j.loc[j['id'].isna(), 'number'].tolist()}")
        sp.loc[lake, "bfs_nr"] = j["id"].astype(int)
    return sp


def observations() -> pd.DataFrame:
    ref = _ref_ids()
    sp = stops()
    state, jac = infer_vintage(sp["bfs_nr"].unique())
    bad = set(sp["bfs_nr"]) - set(ref)
    if state != REFERENCE_DATE or bad:
        raise ValueError(f"service points not on the reference state ({state}, {jac:.3f}; unknown {sorted(bad)[:10]})")
    wide = pd.DataFrame({"bfs_nr": ref})
    wide["pt_stops_total"] = wide["bfs_nr"].map(sp.groupby("bfs_nr").size()).fillna(0)
    for mid, modes in MODES.items():
        has = sp["modes"].map(lambda s, m=modes: bool(s & m))
        wide[mid] = wide["bfs_nr"].map(sp[has].groupby("bfs_nr").size()).fillna(0)
    wide["period"] = PERIOD
    o1 = emit(wide, {c: c for c in ["pt_stops_total", *MODES]}, "period", SOURCE, precision="exact",
              provenance="source_current_state")
    o1["note"] = "atlas service points valid on 2026-11-10"

    # rail ridership
    r = pd.read_excel(ridership(), sheet_name="data")
    r = r[r["Kt_Ct_Cantone"] != "Ausland"]
    allsp = pd.read_csv(service_points(), sep=";", encoding="utf-8-sig", dtype=str,
                        usecols=["number", "fsoNumber", "isoCountryCode"])
    allsp = allsp[allsp["isoCountryCode"] == "CH"].assign(number=lambda d: d["number"].astype(int))
    r = r.merge(allsp[["number", "fsoNumber"]], left_on="UIC", right_on="number", how="left")
    if r["fsoNumber"].isna().any():
        raise ValueError(f"ridership stations without service point: {r.loc[r['fsoNumber'].isna(), 'UIC'].unique()[:10]}")
    r["bfs_nr"] = r["fsoNumber"].astype(int)
    rail_munis = set(sp.loc[sp["modes"].map(lambda s: bool(s & RAIL)), "bfs_nr"]) | set(r["bfs_nr"])
    parts = [o1]
    for year, g in r.groupby("Jahr_Annee_Anno"):
        w = pd.DataFrame({"bfs_nr": ref})
        agg = g.groupby("bfs_nr").agg(dtv=("DTV_TJM_TGM", "sum"), dwv=("DWV_TMJO_TFM", "sum"),
                                      n=("UIC", "size"), n49=("DTV_TJM_TGM", lambda s: int((s == 49).sum())))
        w = w.merge(agg, on="bfs_nr", how="left")
        covered = w["n"].notna()
        rail = w["bfs_nr"].isin(rail_munis)
        for c in ("dtv", "dwv"):
            w[c] = np.where(covered, w[c], np.where(rail, np.nan, 0.0))
        w["period"] = str(int(year))
        for col, mid in (("dtv", "rail_boardings_daily"), ("dwv", "rail_boardings_weekday")):
            o = emit(w, {col: mid}, "period", SOURCE, precision="survey", provenance="source_current_state")
            cov = covered.to_numpy()
            o.loc[cov, "note"] = (w.loc[covered, "n"].astype(int).astype(str) + " station(s), "
                                  + w.loc[covered, "n49"].astype(int).astype(str) + " reported as fixed 49").to_numpy()
            nc = (~covered & rail).to_numpy()
            o.loc[nc, "status"] = "not_covered"
            o.loc[nc, "note"] = "rail service point(s) in the municipality but no station in the ridership file for this year (operator not covered)"
            zero = (~covered & ~rail).to_numpy()
            o.loc[zero, "note"] = "no rail service point in the municipality"
            parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
