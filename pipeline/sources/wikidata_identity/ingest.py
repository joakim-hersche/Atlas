"""Wikidata identity: one numeric metric (number of Wikipedia language editions per municipality).

The lookup table identity.csv (QID, labels, website, coat of arms with licence, Wikipedia links) is
built by fetch.build() from cached SPARQL / Commons API responses and rewritten on every run.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.harmonize.helpers import emit
from pipeline.sources.wikidata_identity.fetch import build

SOURCE = "wikidata_identity"
PERIOD = "2026"  # snapshot of November 2026


def observations() -> pd.DataFrame:
    df = build()
    w = df[["bfs_nr", "wikipedia_editions"]].assign(period=PERIOD)
    o = emit(w, {"wikipedia_editions": "wiki_sitelinks"}, "period", SOURCE, precision="exact",
             provenance="source_current_state")
    qid = df["qid"].to_numpy()  # emit keeps the row order of w
    o["note"] = np.where(pd.isna(qid), "no Wikidata item matched", "Wikidata " + pd.Series(qid).fillna("").astype(str))
    return o
