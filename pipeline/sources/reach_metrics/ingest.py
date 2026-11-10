"""Travel times between the 20 reach hubs and every municipality, as metrics (one per hub and mode).

Input: data/interim/reach/travel_times.parquet, built by pipeline/reach (`python -m pipeline.reach.run`)
from the cached GTFS feed (otd_gtfs) and the NPVM 2023 car matrix (are_npvm). Already on the
reference state (populated hectares placed in reference-state polygons), so rows are emitted as is.

  reach_ptst_<hub>  method gtfs_rcsa_mainstation (decision D31): timetable journey time from the
                    municipality's main station TO the hub, median over arrival minutes 07:30-08:30
  reach_pt_<hub>    method gtfs_rcsa_popweighted: door-to-door towards the hub, inhabited hectares
                    walking to the best stop within 1.5 km, population-weighted median
  reach_car_<hub>   method npvm2023_ttc_popweighted: ARE NPVM 2023 car travel time (average weekday)
  reach_*_nearest_hub: minimum over the 20 hubs.
A status other than ok in the file (no stop within walking distance, no arrival by 10:30, ...) becomes
no_data with that reason as note. Values are minutes, period '2026' (timetable 2026 / reference
state 2026; the car model year 2023 is stated in the note).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.reach.hubs import HUBS

SOURCE = "reach_metrics"
PERIOD = "2026"
METHODS = {"ptst": "gtfs_rcsa_mainstation", "pt": "gtfs_rcsa_popweighted", "car": "npvm2023_ttc_popweighted"}
NOTES = {"ptst": "GTFS timetable 2026, from the main station, arrivals at the hub 07:30–08:30 (median journey time)",
         "pt": "GTFS timetable 2026, door-to-door towards the hub (walk to the best stop within 1.5 km), arrivals 07:30–08:30",
         "car": "ARE NPVM 2023 car travel time (average weekday), population-weighted over zones"}
REASONS = {"no PT within walking distance": "no stop within walking distance (1.5 km) of where people live",
           "no stop within 2 km": "no stop in or near the municipality",
           "no arrival at the hub by 10:30": "no arrival at the hub by 10:30 on the service day",
           "no road access (car-free)": "no road access (car-free)"}
# Blatten VS (6192): the village was destroyed by the landslide of May 2025 (review round 1); the 2026 timetable has
# no served stop within 1.5 km of its inhabited hectares (checked in pipeline/reach, see reach_method.md).
SPECIAL = {6192: "village destroyed by the landslide of May 2025; no public transport service in the 2026 timetable"}


def _late_note(row) -> str | None:
    w = row.get("window_start_min")
    if w is None or w != w:
        return None
    return f"no arrival by 08:30: median over the hour from the earliest possible arrival ({int(w) // 60:02d}:{int(w) % 60:02d})"


def _rows(d: pd.DataFrame, metric: str, mode: str) -> pd.DataFrame:
    ok = d["status"].eq("ok") & d["minutes"].notna()
    o = pd.DataFrame({
        "unit_id": d["bfs_nr"].astype(int).astype(str), "level": "gemeinde",
        "vintage": REFERENCE_DATE.isoformat(), "metric_id": metric, "period": PERIOD,
        "value": d["minutes"].astype(float).where(ok),
        "status": np.where(ok, "ok", "no_data"), "precision": "modelled",
        "provenance": "source_current_state", "source_id": SOURCE,
        "note": np.where(ok, NOTES[mode], d["status"].astype(str).map(lambda x: REASONS.get(x, x))),
    })
    sp = d["bfs_nr"].astype(int).map(SPECIAL)
    o.loc[~ok.values & sp.notna().values, "note"] = sp[~ok.values & sp.notna().values].values
    if "window_start_min" in d:
        late = d.apply(_late_note, axis=1)
        m = ok.values & late.notna().values
        o.loc[m, "note"] = (NOTES[mode] + "; " + late[m]).values
    return o


def observations() -> pd.DataFrame:
    tt = pd.read_parquet(interim_path("reach", "travel_times.parquet"))
    slugs = [h[0] for h in HUBS]
    parts = []
    for mode, method in METHODS.items():
        d = tt[(tt["mode"] == ("pt" if mode == "ptst" else mode)) & (tt["method"] == method)].copy()
        missing = set(slugs) - set(d["hub"])
        if missing:
            raise ValueError(f"reach {mode}: hubs missing in travel_times.parquet: {sorted(missing)}")
        if d.groupby("hub")["bfs_nr"].nunique().min() < 2110 and REFERENCE_DATE.isoformat() == "2026-01-01":
            raise ValueError(f"reach {mode}: not every municipality present")
        d["minutes"] = pd.to_numeric(d["minutes"], errors="coerce").astype(float)
        for slug in slugs:
            parts.append(_rows(d[d["hub"] == slug], f"reach_{mode}_{slug}", mode))
        ok = d[d["status"].eq("ok") & d["minutes"].notna()]
        best = ok.loc[ok.groupby("bfs_nr")["minutes"].idxmin(), ["bfs_nr", "hub", "minutes"]]
        if "window_start_min" in d:
            best = best.merge(d[["bfs_nr", "hub", "window_start_min"]], on=["bfs_nr", "hub"], how="left")
        allm = pd.DataFrame({"bfs_nr": sorted(d["bfs_nr"].unique())}).merge(best, on="bfs_nr", how="left")
        st = d.groupby("bfs_nr")["status"].agg(lambda s: "; ".join(sorted(set(s) - {"ok"})))
        allm["status"] = np.where(allm["minutes"].notna(), "ok", allm["bfs_nr"].map(st))
        o = _rows(allm, f"reach_{mode}_nearest_hub", mode)
        names = dict((h[0], h[1]) for h in HUBS)
        o.loc[o["status"] == "ok", "note"] = "nearest hub: " + allm.loc[allm["minutes"].notna(), "hub"].map(names).values
        parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
