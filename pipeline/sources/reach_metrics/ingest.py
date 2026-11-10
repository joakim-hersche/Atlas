"""Travel times between the 21 reach hubs and every municipality, as metrics (one per hub and mode).

Input: data/interim/reach/travel_times.parquet, built by pipeline/reach (`python -m pipeline.reach.run`)
from the cached GTFS feed (otd_gtfs) and the NPVM 2023 car matrix (are_npvm). Already on the
reference state (populated hectares placed in reference-state polygons), so rows are emitted as is.

  reach_ptst_<hub>  method gtfs_rcsa_mainstation (decision D31): timetable journey time from the
                    municipality's main station TO the hub, median over arrival minutes 07:30-08:30
                    (median day of three weekdays, pipeline.reach.gtfs_prep.REVERSE_DAYS)
  reach_pt_<hub>    method gtfs_rcsa_popweighted: door-to-door towards the hub, inhabited hectares
                    walking to the best stop within 1.5 km, population-weighted median
  reach_car_<hub>   method npvm2023_ttc_popweighted: ARE NPVM 2023 car travel time towards the hub
                    (matrix column), average weekday model incl. congestion
  reach_*_nearest_hub: minimum over the nearest-hub set only (decision D39: the 15 core-city stations of the
                    agglomerations with >= 100,000 residents, pipeline.reach.hubs.nearest_hubs(), derived
                    from STATPOP at build time); the hub is named in the note.
Gaps: 'no arrival at the hub by 10:30' becomes not_applicable (the hub is not reachable on a morning
trip; it is not missing data, so it does not make the coverage partial; expert audit SHOULD 9); other
statuses (no stop within walking distance, ...) become no_data. The reason is the note. A station time
measured from a stop without rail (bus, boat, ...) says so in the note ("from <stop> (bus)").
Values are minutes, period '2026' (timetable 2026 / reference state 2026; the car model year 2023 is
stated in the note).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.reach.hubs import HUBS, NAMES, nearest_hubs

SOURCE = "reach_metrics"
PERIOD = "2026"
METHODS = {"ptst": "gtfs_rcsa_mainstation", "pt": "gtfs_rcsa_popweighted", "car": "npvm2023_ttc_popweighted"}
NOTES = {"ptst": "GTFS timetable 2026, from the main station, arrivals at the hub 07:30–08:30 (median journey time, median of three weekdays)",
         "pt": "GTFS timetable 2026, door-to-door towards the hub (walk to the best stop within 1.5 km), arrivals 07:30–08:30",
         "car": "ARE NPVM 2023 car travel time towards the hub, average weekday model incl. congestion, population-weighted over zones"}
NO_ARRIVAL = "no arrival at the hub by 10:30"
REASONS = {"no PT within walking distance": "no stop within walking distance (1.5 km) of where people live",
           "no stop within 2 km": "no stop in or near the municipality",
           NO_ARRIVAL: "no arrival at the hub by 10:30 on a weekday morning (first connections arrive later)",
           "no road access (car-free)": "no road access (car-free)"}
# statuses that mean "the measure does not apply here" rather than missing data
NOT_APPLICABLE = {NO_ARRIVAL}
# Blatten VS (6192): the village was destroyed by the landslide of May 2025 (review round 1); the 2026 timetable has
# no served stop within 1.5 km of its inhabited hectares (checked in pipeline/reach, see reach_method.md).
SPECIAL = {6192: "village destroyed by the landslide of May 2025; no public transport service in the 2026 timetable"}


def _late_note(row) -> str | None:
    w = row.get("window_start_min")
    if w is None or w != w:
        return None
    return f"no arrival by 08:30: median over the hour from the earliest possible arrival ({int(w) // 60:02d}:{int(w) % 60:02d})"


def _from_note(row) -> str | None:
    """Station time measured from a stop without rail service: name the stop and its mode."""
    m = row.get("main_mode")
    if not isinstance(m, str) or m in ("rail", "none"):
        return None
    return f"from {row.get('main_station')} ({m}), no rail station in the municipality"


def _rows(d: pd.DataFrame, metric: str, mode: str) -> pd.DataFrame:
    d = d.reset_index(drop=True)
    ok = d["status"].eq("ok") & d["minutes"].notna()
    na = ~ok & d["status"].astype(str).str.split("; ").map(lambda xs: bool(xs) and set(xs) <= NOT_APPLICABLE)
    o = pd.DataFrame({
        "unit_id": d["bfs_nr"].astype(int).astype(str), "level": "gemeinde",
        "vintage": REFERENCE_DATE.isoformat(), "metric_id": metric, "period": PERIOD,
        "value": d["minutes"].astype(float).where(ok),
        "status": np.where(ok, "ok", np.where(na, "not_applicable", "no_data")), "precision": "modelled",
        "provenance": "source_current_state", "source_id": SOURCE,
        "note": np.where(ok, NOTES[mode], d["status"].astype(str).map(
            lambda x: "; ".join(REASONS.get(y, y) for y in x.split("; ")))),
    })
    sp = d["bfs_nr"].astype(int).map(SPECIAL)
    o.loc[~ok.values & sp.notna().values, "note"] = sp[~ok.values & sp.notna().values].values
    extra = pd.Series([None] * len(d), dtype=object)
    for f in ((_late_note,) if "window_start_min" in d else ()) + ((_from_note,) if "main_mode" in d else ()):
        x = d.apply(f, axis=1)
        extra = extra.combine(x, lambda a, b: b if a is None else (a if b is None else f"{a}; {b}"))
    m = ok.values & extra.notna().values
    o.loc[m, "note"] = (o.loc[m, "note"] + "; " + extra[m]).values
    return o


def observations() -> pd.DataFrame:
    tt = pd.read_parquet(interim_path("reach", "travel_times.parquet"))
    slugs = [h[0] for h in HUBS]
    nearest, _ = nearest_hubs()          # D39: derived from STATPOP, checked against the approved 15
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
        dn = d[d["hub"].isin(nearest)]
        ok = dn[dn["status"].eq("ok") & dn["minutes"].notna()]
        best = ok.loc[ok.groupby("bfs_nr")["minutes"].idxmin()]
        keep = ["bfs_nr", "hub", "minutes"] + [c for c in ("window_start_min", "main_mode", "main_station") if c in best]
        allm = pd.DataFrame({"bfs_nr": sorted(d["bfs_nr"].unique())}).merge(best[keep], on="bfs_nr", how="left")
        st = dn.groupby("bfs_nr")["status"].agg(lambda s: "; ".join(sorted(set(s) - {"ok"})))
        allm["status"] = np.where(allm["minutes"].notna(), "ok", allm["bfs_nr"].map(st))
        o = _rows(allm, f"reach_{mode}_nearest_hub", mode)
        okm = (o["status"] == "ok").values
        hubname = "nearest hub: " + allm.loc[okm, "hub"].map(NAMES).values
        # keep the per-unit additions (late window, from a bus/boat stop), drop the generic method note
        o.loc[okm, "note"] = [h + n[len(NOTES[mode]):] for h, n in zip(hubname, o.loc[okm, "note"])]
        parts.append(o)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
