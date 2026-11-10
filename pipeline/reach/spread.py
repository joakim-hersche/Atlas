"""Travel-time spread over the morning window, per hub (docs/reach_method.md "Spread over the morning").

Reads data/interim/reach/travel_times.parquet (python -m pipeline.reach.run) and writes
  data/out/reach/spread.json          index: unit order, hubs, definitions (en/de/fr), file pattern
  data/out/reach/<hub>_spread.json    per hub: P10 / median / P90 per unit for both directions
                                      (to the hub, from the hub), station time and door-to-door,
                                      journey time and journey time including waiting
The files sit next to the growing-line files (data/out/reach/), which the web copy step already
picks up (every *.json of that directory). Values are minutes with one decimal, null = no value.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from pipeline.common import interim_path, out_path
from pipeline.reach.gtfs_prep import REVERSE_DAYS, SERVICE_DATE
from pipeline.reach.hubs import HUBS

# (direction, kind) -> method in travel_times.parquet
METHODS = {("to", "pt_station"): "gtfs_rcsa_mainstation", ("to", "pt"): "gtfs_rcsa_popweighted",
           ("from", "pt_station"): "gtfs_fcsa_mainstation", ("from", "pt"): "gtfs_fcsa_popweighted"}
# series -> (P10, median, P90) columns of travel_times.parquet
SERIES = {"journey": ("minutes_p10", "minutes", "minutes_p90"),
          "with_wait": ("minutes_wait_p10", "minutes_incl_wait", "minutes_wait_p90")}
STATS = ("p10", "p50", "p90")

DEFINITIONS = {
    "to": {"en": "Towards the hub: for every arrival minute 07:30-08:30 at the hub, the latest departure that still arrives in time; P10, median and P90 over the 61 arrival minutes (median day of three weekdays).",
           "de": "Richtung Zentrum: für jede Ankunftsminute 07:30-08:30 am Zentrum die späteste Abfahrt, die noch rechtzeitig ankommt; P10, Median und P90 über die 61 Ankunftsminuten (mittlerer von drei Werktagen).",
           "fr": "Vers le pôle : pour chaque minute d'arrivée 07:30-08:30 au pôle, le dernier départ qui arrive à temps ; P10, médiane et P90 sur les 61 minutes d'arrivée (jour médian de trois jours ouvrables)."},
    "from": {"en": "From the hub: for every departure minute 07:30-08:30 at the hub, the earliest arrival; P10, median and P90 over the 61 departure minutes (median day of three weekdays).",
             "de": "Ab Zentrum: für jede Abfahrtsminute 07:30-08:30 am Zentrum die früheste Ankunft; P10, Median und P90 über die 61 Abfahrtsminuten (mittlerer von drei Werktagen).",
             "fr": "Depuis le pôle : pour chaque minute de départ 07:30-08:30 au pôle, l'arrivée la plus précoce ; P10, médiane et P90 sur les 61 minutes de départ (jour médian de trois jours ouvrables)."},
    "journey": {"en": "Journey time as a journey planner shows it: arrival minus the departure of the vehicle actually taken (no initial wait, no wait at the hub). A narrow range means the same journey time whichever train you take.",
                "de": "Reisezeit wie im Fahrplan: Ankunft minus Abfahrt des tatsächlich genommenen Fahrzeugs (ohne Anfangswartezeit, ohne Wartezeit am Zentrum). Eine schmale Spanne heisst: unabhängig vom Zug gleiche Reisezeit.",
                "fr": "Temps de trajet comme dans l'horaire : arrivée moins départ du véhicule réellement pris (sans attente initiale ni attente au pôle). Une fourchette étroite signifie le même temps quel que soit le train."},
    "with_wait": {"en": "Journey time including waiting: towards the hub from the arrival minute back to the departure (wait at the hub and slack included); from the hub from the departure minute to the arrival (initial wait included). Wide where service is infrequent.",
                  "de": "Reisezeit inklusive Wartezeit: Richtung Zentrum von der Ankunftsminute bis zur Abfahrt (Wartezeit am Zentrum eingerechnet); ab Zentrum von der Abfahrtsminute bis zur Ankunft (Anfangswartezeit eingerechnet). Breit bei seltenem Verkehr.",
                  "fr": "Temps de trajet attente comprise : vers le pôle de la minute d'arrivée au départ (attente au pôle comprise) ; depuis le pôle de la minute de départ à l'arrivée (attente initiale comprise). Large si l'offre est rare."},
    "pt_station": {"en": "Station time: between the municipality's main station and the hub station.",
                   "de": "Bahnhofszeit: zwischen dem Hauptbahnhof der Gemeinde und dem Bahnhof des Zentrums.",
                   "fr": "Temps de gare à gare : entre la gare principale de la commune et la gare du pôle."},
    "pt": {"en": "Door to door: hectare by hectare the walk to the best stop within 1.5 km plus that stop's P10 / median / P90; population-weighted median over the hectares (P10 and P90 are approximations: minimum over stops of the stops' percentiles).",
           "de": "Tür zu Tür: je Hektare der Fussweg zur besten Haltestelle innerhalb 1,5 km plus P10 / Median / P90 dieser Haltestelle; bevölkerungsgewichteter Median über die Hektaren (P10 und P90 sind Näherungen: Minimum über die Haltestellen der jeweiligen Perzentile).",
           "fr": "Porte à porte : par hectare la marche jusqu'au meilleur arrêt à moins de 1,5 km plus le P10 / la médiane / le P90 de cet arrêt ; médiane pondérée par la population sur les hectares (P10 et P90 sont des approximations : minimum sur les arrêts des percentiles)."},
}


def _arr(v: pd.Series, units: list[str]) -> list:
    x = v.reindex([int(u) for u in units]).to_numpy(float)
    return [None if not np.isfinite(a) else round(float(a), 1) for a in x]


def hub_file(tt: pd.DataFrame, slug: str, units: list[str]) -> dict:
    out: dict = {"hub": slug, "to": {}, "from": {}, "late_from": {}, "reasons": {"to": {}, "from": {}}}
    uid = [int(u) for u in units]
    for (direction, kind), method in METHODS.items():
        d = tt[(tt.hub == slug) & (tt["mode"] == "pt") & (tt.method == method)].drop_duplicates("bfs_nr").set_index("bfs_nr")
        if d.empty:
            continue
        ok = d.status.eq("ok")
        blk = {}
        for name, cols in SERIES.items():
            blk[name] = {s: _arr(d[c].where(ok), units) for s, c in zip(STATS, cols)}
        out[direction][kind] = blk
        bad = d.loc[~ok, "status"].reindex(uid)
        out["reasons"][direction][kind] = {str(i): t for i, t in enumerate(bad) if isinstance(t, str)}
        if direction == "to" and "window_start_min" in d:
            w = d["window_start_min"].where(ok).reindex(uid)
            late = {str(i): f"{int(m) // 60:02d}:{int(m) % 60:02d}" for i, m in enumerate(w) if m == m}
            if late:
                out["late_from"][kind] = late
    return out


def build(tt: pd.DataFrame | None = None, hubs=HUBS) -> list[str]:
    tt = pd.read_parquet(interim_path("reach", "travel_times.parquet")) if tt is None else tt
    units = sorted({str(int(b)) for b in tt.bfs_nr.unique()}, key=int)
    written = []
    for slug, _name, _didok in hubs:
        p = out_path("reach", f"{slug}_spread.json")
        p.write_text(json.dumps(hub_file(tt, slug, units), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        written.append(p.name)
    idx = {"units": units, "hubs": [[h[0], h[1]] for h in HUBS], "file": "<hub>_spread.json",
           "stats": list(STATS), "series": list(SERIES), "directions": ["to", "from"], "kinds": ["pt_station", "pt"],
           "unit": "minutes (one decimal); null = no value (reasons in the hub file, 'to' reasons as in reach_times.json)",
           "window": {"to": "arrival at the hub 07:30-08:30", "from": "departure from the hub 07:30-08:30"},
           "service_date": SERVICE_DATE.isoformat(), "reverse_days": [d.isoformat() for d in REVERSE_DAYS],
           "definitions": DEFINITIONS}
    out_path("reach", "spread.json").write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return written


if __name__ == "__main__":
    print(len(build()), "hub files")
