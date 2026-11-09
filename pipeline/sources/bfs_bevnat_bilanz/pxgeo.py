"""Adapter for PxWeb cubes whose geography variable uses running indices (0, 1, 2, ...) instead of
BFS codes. Labels carry the structure: 'Schweiz', '- Zürich', '>> Bezirk Affoltern',
'......0261 Zürich' (also plain '261 Zürich' in some cubes).

recode_geo() rewrites the index codes into the codes pipeline.harmonize.pxweb.to_observations
expects: '8100' (Switzerland), canton abbreviation, 6-digit district number, 4-digit BFS number.
Canton and district codes are taken from the municipalities listed under each header, at the
municipality state inferred from the cube's BFS numbers.

Used by the bfs_bevnat_bilanz, bfs_migration, bfs_naturalisation, bfs_statent, bfs_udemo,
bfs_agriculture and bfs_construction connectors (one helper, kept here; a generic version could
move to pipeline/harmonize/pxweb.py).
"""
from __future__ import annotations

import re

import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import infer_vintage
from pipeline.sources.bfs_pxweb.fetch import metadata

_MUN = re.compile(r"^(?:\.{6})?(\d{1,4})\s+(.+)$")


def parse_label(label: str) -> tuple[str, int | None]:
    s = label.strip()
    if s.lower() in ("schweiz", "suisse", "total"):
        return "schweiz", None
    if s.startswith(">>"):
        return "bezirk", None
    if s.startswith("- "):
        return "kanton", None
    m = _MUN.match(s)
    if m:
        return "gemeinde", int(m.group(1))
    return "other", None


def geo_codes(dbid: str, geo_var: str, exclude=lambda label: False) -> tuple[dict[str, str], object, float]:
    """Map the cube's geo value codes to standard codes. Returns (mapping, vintage, jaccard).

    exclude(label) -> True marks labels to map to 'other' (dropped by to_observations), e.g.
    'Unzuteilbar' pseudo-units.
    """
    var = next(v for v in metadata(dbid)["variables"] if v["code"] == geo_var)
    parsed = [(c, t, *parse_label(t)) for c, t in zip(var["values"], var["valueTexts"])]
    parsed = [(c, t, "other" if exclude(t) else lvl, nr) for c, t, lvl, nr in parsed]
    bfs = [nr for _, _, lvl, nr in parsed if lvl == "gemeinde"]
    vintage, jac = infer_vintage(bfs)
    mv, _ = load_backbone()
    ver = versions_at(mv, vintage).drop_duplicates("bfs_nr").set_index("bfs_nr")
    out = {}
    for i, (code, _, lvl, nr) in enumerate(parsed):
        if lvl == "gemeinde":
            out[code] = f"{nr:04d}"
        elif lvl == "schweiz":
            out[code] = "8100"
        elif lvl in ("kanton", "bezirk"):
            # first following municipality that exists in the state
            nxt = None
            for _, _, l2, n2 in parsed[i + 1:]:
                if l2 == "gemeinde" and n2 in ver.index:
                    nxt = ver.loc[n2]
                    break
                if l2 == lvl or (lvl == "bezirk" and l2 == "kanton"):
                    break
            if nxt is None:
                out[code] = f"other:{code}"
            elif lvl == "kanton":
                out[code] = str(nxt["canton"])
            else:
                out[code] = f"{int(nxt['district_nr']):06d}"
        else:
            out[code] = f"other:{code}"
    return out, vintage, jac


def recode(df: pd.DataFrame, dbid: str, geo_var: str, new_col: str | None = None, **kw) -> pd.DataFrame:
    mapping, _, _ = geo_codes(dbid, geo_var, **kw)
    df = df.copy()
    df[new_col or geo_var] = df[geo_var].map(mapping)
    return df


# ---------------------------------------------------------------------------------------------
# Querying with cell status (JSON-stat 'status', e.g. 'X' = suppressed) — query_codes() drops it.

def query_status(dbid: str, select: dict[str, list[str] | str]) -> pd.DataFrame:
    """Like query_codes(), but one request per call (caller keeps it below the cell limit) and
    with a 'status' column holding the cell symbol PxWeb attaches (None for ordinary cells)."""
    import hashlib
    import itertools
    import json

    from pipeline.common import latest_snapshot
    from pipeline.sources.bfs_pxweb.fetch import SOURCE as PX, _post

    meta = metadata(dbid)
    q = []
    for v in meta["variables"]:
        want = select.get(v["code"])
        codes = v["values"] if want == "*" else (list(want) if want else [v["values"][0]])
        q.append({"code": v["code"], "selection": {"filter": "item", "values": list(codes)}})
    body = {"query": q, "response": {"format": "json-stat2"}}
    key = hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    fname = f"{dbid}.{key}.json"
    path = latest_snapshot(PX, fname) or _post(dbid, body, fname)
    js = json.loads(path.read_bytes())
    cats = []
    for d in js["id"]:
        idx = js["dimension"][d]["category"]["index"]
        cats.append(sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx))
    n = 1
    for c in cats:
        n *= len(c)
    vals = js["value"]
    if isinstance(vals, dict):
        dense = [None] * n
        for k, v in vals.items():
            dense[int(k)] = v
        vals = dense
    st = js.get("status") or {}
    status = [None] * n
    if isinstance(st, dict):
        for k, v in st.items():
            status[int(k)] = v
    elif isinstance(st, list):
        status = list(st) + [None] * (n - len(st))
    elif isinstance(st, str):
        status = [st] * n
    df = pd.DataFrame(list(itertools.product(*cats)), columns=js["id"])
    df["value"] = pd.to_numeric(pd.Series(vals), errors="coerce")
    df["status"] = status
    return df


# ---------------------------------------------------------------------------------------------
# Wide frame with standard geo codes -> observations (variant of harmonize.pxweb.to_observations)

def to_obs(wide: pd.DataFrame, geo_col: str, period_col: str, metric_map: dict[str, str],
           source_id: str, *, vintage=None, per_year_state: bool = False,
           legacy_hist: dict[int, int] | None = None, suppressed: pd.DataFrame | None = None,
           published_on_current_state: bool = True, native_levels=("kanton", "bezirk", "schweiz"),
           report: dict | None = None) -> pd.DataFrame:
    """Like pipeline.harmonize.pxweb.to_observations, plus:

    vintage          municipality state of the cube (inferred from its BFS numbers if None);
    per_year_state   the cube lists every municipality of its period, each year on the state of
                     31 Dec of that year (mixed-state cubes); rows not valid then are dropped;
    legacy_hist      {cube BFS code: register hist_id} for codes the cube uses for abolished units
                     that are not valid on the cube's state (values reprojected with the
                     crosswalk weights, so successors become 'boundary_estimate');
    suppressed       same keys as wide, boolean columns named like the value columns: True where
                     the source suppressed the cell. Any suppressed contribution makes the target
                     value NaN with status 'suppressed'.
    report           dict filled with diagnostics (vintage, jaccard, unmapped rows).
    """
    import datetime as dt

    import numpy as np

    from pipeline.harmonize.helpers import emit, to_reference
    from pipeline.harmonize.schema import OBS_COLUMNS
    from pipeline.sources.bfs_pxweb.fetch import geo_level_of_code

    rep = report if report is not None else {}
    wide = wide.copy()
    wide["_level"] = wide[geo_col].map(geo_level_of_code)
    cols = list(metric_map)
    mun = wide[wide["_level"] == "gemeinde"].copy()
    mun["bfs_nr"] = mun[geo_col].astype(int)
    if suppressed is not None:
        sup = suppressed.copy()
        sup = sup[sup[geo_col].map(geo_level_of_code) == "gemeinde"]
        sup["bfs_nr"] = sup[geo_col].astype(int)
        sup = sup[["bfs_nr", period_col, *cols]].rename(columns={c: f"_s_{c}" for c in cols})
        mun = mun.merge(sup, on=["bfs_nr", period_col], how="left")
        for c in cols:
            mun[f"_s_{c}"] = mun[f"_s_{c}"].fillna(False).astype(float)
    mv, _ = load_backbone()
    legacy_hist = legacy_hist or {}
    if per_year_state:
        parts = []
        for p, g in mun.groupby(period_col):
            d = dt.date(int(str(p)[:4]), 12, 31)
            ver = versions_at(mv, d, municipalities_only=False).drop_duplicates("bfs_nr").set_index("bfs_nr")
            parts.append(g.assign(hist_id=g["bfs_nr"].map(ver["hist_id"])))
        mun = pd.concat(parts)
        rep["state"] = "per year (31 Dec)"
    else:
        if vintage is None:
            vintage, jac = infer_vintage(mun["bfs_nr"].unique())
            rep["jaccard"] = round(jac, 4)
            if jac < 0.98:
                raise ValueError(f"cannot identify municipality state (best {vintage}, jaccard {jac:.3f})")
        rep["state"] = str(vintage)
        ver = versions_at(mv, vintage, municipalities_only=False).drop_duplicates("bfs_nr").set_index("bfs_nr")
        mun["hist_id"] = mun["bfs_nr"].map(ver["hist_id"])
    for code, hid in legacy_hist.items():
        # only for the years the unit existed (the cube shows zeros afterwards)
        valid_to = mv.loc[mv["hist_id"] == hid, "valid_to"].max()
        yr = mun[period_col].astype(str).str[:4].astype(int)
        is_code = mun["bfs_nr"] == code
        mun.loc[is_code & (yr <= valid_to.year), "hist_id"] = hid
        mun = mun[~(is_code & (yr > valid_to.year))]
    unm = mun[mun["hist_id"].isna()]
    rep["unmapped_rows"] = int(len(unm))
    rep["unmapped_nonzero_rows"] = int((unm[cols].fillna(0).abs().sum(axis=1) > 0).sum())
    rep["unmapped_codes"] = sorted(unm["bfs_nr"].unique().tolist())[:30]
    mun = mun[mun["hist_id"].notna()].astype({"hist_id": "int64"})
    flag_cols = [f"_s_{c}" for c in cols] if suppressed is not None else []
    ref, _ = to_reference(mun[["hist_id", period_col, *cols, *flag_cols]], None, cols + flag_cols,
                          [period_col], rule="sum", bfs_already_current=published_on_current_state)
    obs = emit(ref, {c: metric_map[c] for c in cols}, period_col, source_id)
    if flag_cols:
        flags = pd.concat([pd.DataFrame({"unit_id": ref["bfs_nr"].astype(str), "metric_id": metric_map[c],
                                         "period": ref[period_col].astype(str), "_sup": ref[f"_s_{c}"] > 0})
                           for c in cols], ignore_index=True)
        obs = obs.merge(flags, on=["unit_id", "metric_id", "period"], how="left")
        s = obs["_sup"].fillna(False).astype(bool)
        obs.loc[s, "value"] = np.nan
        obs.loc[s, "status"] = "suppressed"
        obs.loc[s, "note"] = "suppressed by the source (small numbers)"
        obs = obs.drop(columns="_sup")
    parts = [obs]
    for level in native_levels:
        sub = wide[wide["_level"] == level].copy()
        if sub.empty:
            continue
        if level == "bezirk":
            sub["unit"] = sub[geo_col].str[-4:].astype(int).astype(str)
        elif level == "schweiz":
            sub["unit"] = "CH"
        else:
            sub["unit"] = sub[geo_col]
        sub["precision"], sub["provenance"] = "exact", "native"
        e = emit(sub, metric_map, period_col, source_id, level=level, unit_col="unit",
                 vintage=vintage if isinstance(vintage, dt.date) else REFERENCE_DATE)
        if suppressed is not None:
            ss = suppressed.copy()
            ss = ss[ss[geo_col].isin(sub[geo_col])]
            ss["unit"] = sub.set_index(geo_col)["unit"].reindex(ss[geo_col]).values
            fl = pd.concat([pd.DataFrame({"unit_id": ss["unit"].astype(str), "metric_id": metric_map[c],
                                          "period": ss[period_col].astype(str), "_sup": ss[c].astype(bool)})
                            for c in cols], ignore_index=True)
            e = e.merge(fl, on=["unit_id", "metric_id", "period"], how="left")
            s = e["_sup"].fillna(False).astype(bool)
            e.loc[s, "value"], e.loc[s, "status"] = np.nan, "suppressed"
            e = e.drop(columns="_sup")
        parts.append(e)
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]


def query_status_split(dbid: str, select: dict[str, list[str] | str], max_cells: int | None = None) -> pd.DataFrame:
    """query_status() split into requests below the PxWeb cell limit, the same way query_codes()
    splits (so cached responses are shared)."""
    from pipeline.sources.bfs_pxweb.fetch import MAX_CELLS

    max_cells = max_cells or MAX_CELLS
    sel = {}
    for v in metadata(dbid)["variables"]:
        want = select.get(v["code"])
        sel[v["code"]] = v["values"] if want == "*" else (list(want) if want else [v["values"][0]])
    cells = 1
    for codes in sel.values():
        cells *= len(codes)
    if cells > max_cells:
        time_var = next((c for c in sel if c in ("Jahr", "Zeitperiode", "Jahr / Periode")), None)
        split_var = time_var if time_var and len(sel[time_var]) > 1 else max(sel, key=lambda c: len(sel[c]))
        per = max(1, int(len(sel[split_var]) * max_cells / cells))
        parts = []
        for i in range(0, len(sel[split_var]), per):
            sub = dict(sel)
            sub[split_var] = sel[split_var][i:i + per]
            parts.append(query_status_split(dbid, sub, max_cells))
        return pd.concat(parts, ignore_index=True)
    return query_status(dbid, sel)


SUPPRESSED_SYMBOLS = {"X", "x", "( )", "()"}  # BFS: suppressed for data protection / reliability
