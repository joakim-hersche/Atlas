"""Road traffic accidents with personal injury per municipality and year (ASTRA, 2011–latest).

One row per accident with MunicipalityCode. Inferring the municipality state per year
(infer_vintage) gives the reference state 2026-01-01 for every year: ASTRA codes all years on the
municipality state at extraction (2026-02). Counts are therefore emitted directly as
'source_current_state'; municipalities without an accident in a year get 0 (the file is the full
police record of injury accidents). Accidents coded to territory outside any municipality
(Kommunanz 5394 in Ticino on the A2 at Monte Ceneri, lake area 9073) are not counted.
Motorway accidents (RoadType rt430 motorway, rt434 motorway side installation) are attributed to
the municipality where they happen; a separate count without them is delivered.
"""
from __future__ import annotations

import zipfile

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit, infer_vintage
from pipeline.sources.astra_accidents.fetch import accidents

SOURCE = "astra_accidents"
MOTORWAY = {"rt430", "rt434"}


def _load() -> pd.DataFrame:
    with zipfile.ZipFile(accidents()) as z:
        return pd.read_csv(z.open("RoadTrafficAccidentLocations.csv"), low_memory=False,
                           usecols=["AccidentSeverityCategory", "AccidentInvolvingPedestrian",
                                    "AccidentInvolvingBicycle", "AccidentInvolvingMotorcycle", "RoadType",
                                    "MunicipalityCode", "AccidentYear"])


def observations() -> pd.DataFrame:
    d = _load()
    mv, _ = load_backbone()
    ref_ids = set(versions_at(mv, REFERENCE_DATE)["bfs_nr"].astype(int))
    for year, g in d.groupby("AccidentYear"):
        vintage, _ = infer_vintage(g["MunicipalityCode"])
        if vintage != REFERENCE_DATE:
            raise ValueError(f"accidents {year} on state {vintage}, expected the reference state")
    d = d[d["MunicipalityCode"].isin(ref_ids)]
    sev = d["AccidentSeverityCategory"]
    flags = {
        "acc_injury_count": pd.Series(True, index=d.index),
        "acc_severe_count": sev.isin(["as1", "as2"]),
        "acc_fatal_count": sev.eq("as1"),
        "acc_pedestrian_count": d["AccidentInvolvingPedestrian"].astype(str).eq("True"),
        "acc_bicycle_count": d["AccidentInvolvingBicycle"].astype(str).eq("True"),
        "acc_motorcycle_count": d["AccidentInvolvingMotorcycle"].astype(str).eq("True"),
        "acc_nonmotorway_count": ~d["RoadType"].isin(MOTORWAY),
    }
    c = pd.DataFrame({k: v.astype(int) for k, v in flags.items()})
    c["bfs_nr"], c["year"] = d["MunicipalityCode"].astype(int), d["AccidentYear"].astype(int)
    counts = c.groupby(["bfs_nr", "year"]).sum()
    years = sorted(c["year"].unique())
    grid = pd.MultiIndex.from_product([sorted(ref_ids), years], names=["bfs_nr", "year"])
    wide = counts.reindex(grid, fill_value=0).reset_index()
    return emit(wide, {k: k for k in flags}, "year", SOURCE, precision="exact",
                provenance="source_current_state")
