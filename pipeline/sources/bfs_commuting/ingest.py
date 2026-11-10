"""Commuting per municipality from the BFS commuter matrix (employed persons by municipality of
residence and municipality of work, 2014, 2018, 2020; register linkage AHV × STATPOP × STATENT).

Source file: one row per (perspective, year, residence municipality, work municipality) with
VALUE = employed persons. PERSPECTIVE R lists, per residence municipality, every work municipality
with at least 5 persons; W lists, per work municipality, every residence municipality with at
least 5 persons. Code 7777 (XLSX note): "Relationen mit weniger als 5 Erwerbstätigen wurden
gruppiert zu «Andere Gemeinden» (Gemeindenummer 7777) und «andere Kantone» (Kantonsnummer 77)",
i.e. 7777 is the sum of all relations below 5 persons (same canton: canton code of that canton;
other cantons: canton 77). It is not a place; it is kept in the totals and never counted as
"own municipality". Explicit pairs are identical in R and W (checked), and the R and W grand
totals are equal per year.

Municipality state: the file says "Gemeindestand 18.10.2020" for all years; infer_vintage on
each year's BFS numbers confirms the 2020 state (jaccard 1.0) for 2014, 2018 and 2020.
The matrix is reprojected to the reference state at flow level (residence and work municipality
each mapped through the crosswalk, weights multiplied), so a merged municipality's "works in own
municipality" includes the flows between its predecessors. Relations below 5 persons between two
predecessors are inside 7777 and are therefore counted as commuting (undercount < 5 per pair).

Metrics per municipality and year:
  com_employed_residents  sum over R rows of the residence municipality (incl. 7777)
  com_jobs                sum over W rows of the work municipality (incl. 7777): employed persons
                          residing in Switzerland who work in the municipality (cross-border
                          commuters from abroad are not in the matrix)
  com_work_in_own         flows with residence = work (after reprojection)
  com_out_commuters       com_employed_residents - com_work_in_own
  com_in_commuters        com_jobs - com_work_in_own
  com_balance             com_jobs - com_employed_residents (in-commuters - out-commuters)
Where a municipality's own flow is below 5 (absent, inside 7777), com_work_in_own and the metrics
derived from it are 'suppressed' (2014: 3, 2018: 1, 2020: 5 municipalities).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.backbone.vintage import crosswalk
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit, infer_vintage
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_commuting.fetch import matrix_csv

SOURCE = "bfs_commuting"
OTHER = 7777
VINTAGE_LOG: dict = {}


def _load() -> pd.DataFrame:
    d = pd.read_csv(matrix_csv(), encoding="utf-8-sig")
    d.columns = [c.strip() for c in d.columns]
    return d.rename(columns={"GEO_COMM_RESID": "res", "GEO_COMM_WORK": "work", "REF_YEAR": "year",
                             "VALUE": "value", "PERSPECTIVE": "persp"})[["persp", "year", "res", "work", "value"]]


def _mapping(state) -> pd.DataFrame:
    """bfs_nr on the source state -> reference bfs_nr with population weight (> 0)."""
    mv, _ = load_backbone()
    v = versions_at(mv, state)[["hist_id", "bfs_nr"]]
    cw = crosswalk(REFERENCE_DATE)
    ref = set(versions_at(mv, REFERENCE_DATE)["hist_id"].astype(int))
    cw = cw[cw["to_hist_id"].isin(ref) & (cw["weight"] > 0)]
    m = v.merge(cw[["from_hist_id", "to_bfs_nr", "weight"]], left_on="hist_id", right_on="from_hist_id")
    return m[["bfs_nr", "to_bfs_nr", "weight"]].astype({"bfs_nr": int, "to_bfs_nr": int})


def _map(df: pd.DataFrame, col: str, m: pd.DataFrame) -> pd.DataFrame:
    """Replace municipality column col by the reference municipality; 7777 is kept as is."""
    other = df[df[col] == OTHER].assign(**{f"w_{col}": 1.0})
    x = df[df[col] != OTHER].merge(m.rename(columns={"bfs_nr": col, "to_bfs_nr": f"{col}_ref",
                                                    "weight": f"w_{col}"}), on=col, how="left")
    if x[f"{col}_ref"].isna().any():
        raise ValueError(f"unmapped {col} codes: {sorted(x.loc[x[f'{col}_ref'].isna(), col].unique())[:10]}")
    x[col] = x.pop(f"{col}_ref").astype(int)
    return pd.concat([x, other], ignore_index=True)


def _year(d: pd.DataFrame, year: int) -> pd.DataFrame:
    state, jac = infer_vintage(d.loc[d["persp"] == "R", "res"].unique())
    VINTAGE_LOG[str(year)] = {"vintage": state.isoformat(), "jaccard": jac}
    if jac < 0.99:
        raise ValueError(f"commuting {year}: municipality state unclear ({state}, {jac:.3f})")
    m = _mapping(state)
    src_units = sorted(set(d.loc[d["persp"] == "R", "res"]) - {OTHER})
    own_src = set(d.loc[(d["persp"] == "R") & (d["res"] == d["work"]), "res"])
    no_own = set(src_units) - own_src
    exact_w = m.groupby("to_bfs_nr")["weight"].min()

    r = d[d["persp"] == "R"]
    w = d[d["persp"] == "W"]
    r = _map(_map(r, "res", m), "work", m)
    w = _map(_map(w, "res", m), "work", m)
    r["v"] = r["value"] * r["w_res"] * r["w_work"]
    w["v"] = w["value"] * w["w_res"] * w["w_work"]
    emp = r.groupby("res")["v"].sum()
    jobs = w.groupby("work")["v"].sum()
    own = r[(r["res"] == r["work"])].groupby("res")["v"].sum()
    units = sorted(set(m["to_bfs_nr"]))
    out = pd.DataFrame({"bfs_nr": units})
    out["emp"] = out["bfs_nr"].map(emp).fillna(0.0)
    out["jobs"] = out["bfs_nr"].map(jobs).fillna(0.0)
    out["own"] = out["bfs_nr"].map(own).fillna(0.0)
    # own flow of a source municipality below 5 -> the target's own count is unknown
    sup_targets = set(m.loc[m["bfs_nr"].isin(no_own), "to_bfs_nr"])
    out["sup"] = out["bfs_nr"].isin(sup_targets)
    out["out"] = out["emp"] - out["own"]
    out["inc"] = out["jobs"] - out["own"]
    out["bal"] = out["jobs"] - out["emp"]
    exact = out["bfs_nr"].map(exact_w).fillna(1.0) >= 1 - 1e-9
    out["precision"] = np.where(exact, "exact", "boundary_estimate")
    out["provenance"] = np.where(exact, "aggregated_mergers", "reprojected_weighted")
    out["year"] = str(year)
    return out


METRICS = {"emp": "com_employed_residents", "jobs": "com_jobs", "own": "com_work_in_own",
           "out": "com_out_commuters", "inc": "com_in_commuters", "bal": "com_balance"}
NEEDS_OWN = {"own", "out", "inc"}


def national(d: pd.DataFrame) -> pd.DataFrame:
    """Switzerland totals from the source (sum of all R rows per year), kept as native rows."""
    t = d[d["persp"] == "R"].groupby("year")["value"].sum().reset_index()
    t["unit"] = "CH"
    t["year"] = t["year"].astype(str)
    o = emit(t, {"value": "com_employed_residents"}, "year", SOURCE, level="schweiz", unit_col="unit",
             precision="exact", provenance="native")
    return o


def observations() -> pd.DataFrame:
    d = _load()
    parts = []
    for year, g in d.groupby("year"):
        w = _year(g, int(year))
        for col, mid in METRICS.items():
            o = emit(w, {col: mid}, "year", SOURCE)
            if col in NEEDS_OWN:
                s = w["sup"].to_numpy()
                o.loc[s, "value"] = np.nan
                o.loc[s, "status"] = "suppressed"
                o.loc[s, "note"] = "own-municipality flow below 5 persons (grouped into code 7777 in the source)"
            parts.append(o)
    parts.append(national(d))
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
