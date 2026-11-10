"""Travel times from the 20 reach hubs to every municipality, as metrics (one per hub and mode).

Input: data/interim/reach/travel_times.parquet, built by pipeline/reach (`python -m pipeline.reach.run`)
from the cached GTFS feed (otd_gtfs) and the NPVM 2023 car matrix (are_npvm). Already on the
reference state (populated hectares placed in reference-state polygons), so rows are emitted as is.

  reach_pt_<hub>   method gtfs_csa_popweighted: population-weighted median over the municipality's
                   populated STATPOP 2025 hectares of the timetable journey time 07:30–08:30 on a
                   weekday (median over departures, initial wait at the hub excluded), including the
                   walk from the hectare's nearest served stop (<= 1.5 km)
  reach_car_<hub>  method npvm2023_ttc_popweighted: ARE NPVM 2023 car travel time (average weekday),
                   population-weighted mean over the municipality's NPVM zones
  reach_pt_nearest_hub / reach_car_nearest_hub: minimum over the 20 hubs.
Status from the file: 'no PT within walking distance' (no populated hectare within 1.5 km of a
served stop) -> no_data with that note. Values are minutes, period '2026' (timetable 2026 /
reference state 2026; the car model year 2023 is stated in the note).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.reach.hubs import HUBS

SOURCE = "reach_metrics"
PERIOD = "2026"
METHODS = {"pt": "gtfs_csa_popweighted", "car": "npvm2023_ttc_popweighted"}
NOTES = {"pt": "GTFS timetable, weekday departures 07:30–08:30, median journey time incl. walk from nearest stop",
         "car": "ARE NPVM 2023 car travel time (average weekday), population-weighted over zones"}


def _rows(d: pd.DataFrame, metric: str, mode: str) -> pd.DataFrame:
    ok = d["status"].eq("ok") & d["minutes"].notna()
    o = pd.DataFrame({
        "unit_id": d["bfs_nr"].astype(int).astype(str), "level": "gemeinde",
        "vintage": REFERENCE_DATE.isoformat(), "metric_id": metric, "period": PERIOD,
        "value": d["minutes"].astype(float).where(ok),
        "status": np.where(ok, "ok", "no_data"), "precision": "modelled",
        "provenance": "source_current_state", "source_id": SOURCE,
        "note": np.where(ok, NOTES[mode], d["status"].astype(str)),
    })
    return o


def observations() -> pd.DataFrame:
    tt = pd.read_parquet(interim_path("reach", "travel_times.parquet"))
    slugs = [h[0] for h in HUBS]
    parts = []
    for mode, method in METHODS.items():
        d = tt[(tt["mode"] == mode) & (tt["method"] == method)].copy()
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
        allm = pd.DataFrame({"bfs_nr": sorted(d["bfs_nr"].unique())}).merge(best, on="bfs_nr", how="left")
        st = d.groupby("bfs_nr")["status"].agg(lambda s: "; ".join(sorted(set(s) - {"ok"})))
        allm["status"] = np.where(allm["minutes"].notna(), "ok", allm["bfs_nr"].map(st))
        o = _rows(allm, f"reach_{mode}_nearest_hub", mode)
        names = dict((h[0], h[1]) for h in HUBS)
        o.loc[o["status"] == "ok", "note"] = "nearest hub: " + allm.loc[allm["minutes"].notna(), "hub"].map(names).values
        parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
