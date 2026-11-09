"""Small helpers shared by this agent's connectors (estv_*, bfs_education, bfs_social_assistance,
are_*). Kept here instead of pipeline/harmonize so shared modules stay untouched.

per_period_to_reference(): one municipality state per period (inferred from the BFS numbers of that
period, or GDEHISTID), reprojected to the reference state with to_reference(), and emitted as
observations. Suppressed source cells propagate: a target unit that receives any suppressed
contribution gets status 'suppressed' (value NaN), never a partial sum.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import hashlib

import numpy as np
import pandas as pd
import requests

from pipeline.common import RAW, USER_AGENT, latest_snapshot
from pipeline.harmonize.helpers import emit, infer_vintage, to_reference
from pipeline.harmonize.schema import OBS_COLUMNS

SUP = "__sup"  # suffix of the boolean "suppressed in source" companion column


def per_period_to_reference(wide: pd.DataFrame, metric_map: dict[str, str], source_id: str, *,
                            period_col: str = "period", rules: dict[str, str] | None = None,
                            key: str = "bfs_nr", vintage: dt.date | None = None,
                            min_jaccard: float = 0.98, precision: str | None = None,
                            log: dict | None = None) -> pd.DataFrame:
    """wide: one row per municipality × period with value columns (keys of metric_map) and optional
    boolean '<col>__sup' columns. key: 'bfs_nr' (state inferred per period unless vintage is given)
    or 'hist_id' (GDEHISTID, no state needed). rules: column -> to_reference rule (default 'sum').
    """
    rules = rules or {}
    cols = list(metric_map)
    parts = []
    for p, d in wide.groupby(period_col, sort=True):
        d = d.copy()
        if key == "hist_id":
            v, jac = None, None
        elif vintage is not None:
            v, jac = vintage, None
        else:
            v, jac = infer_vintage(d["bfs_nr"].unique())
            if jac < min_jaccard:
                raise ValueError(f"{source_id} {p}: cannot identify municipality state "
                                 f"(best {v}, jaccard {jac:.3f})")
        if log is not None:
            log[str(p)] = {"vintage": None if v is None else v.isoformat(), "jaccard": jac,
                           "rows": int(len(d))}
        supcols = []
        for c in cols:
            sc = c + SUP
            if sc not in d:
                d[sc] = False
            d[sc] = d[sc].fillna(False).astype(float)
            d.loc[d[sc] > 0, c] = np.nan
            supcols.append(sc)
        keycols = [key]
        for rule in sorted(set(rules.get(c, "sum") for c in cols)):
            cc = [c for c in cols if rules.get(c, "sum") == rule]
            if rule.startswith("weighted_mean:"):
                # to_reference() passes only key, group and value columns to to_vintage(), so the
                # weight column would be lost: sum value×weight and weight, then divide.
                wcol = rule.split(":", 1)[1]
                tmp = d[[*keycols, period_col]].copy()
                for c in cc:
                    ok = d[c].notna()
                    tmp[c + "__vw"] = (d[c] * d[wcol]).where(ok)
                    tmp[c + "__w"] = d[wcol].where(ok)
                tc = [x for c in cc for x in (c + "__vw", c + "__w")]
                ref, _ = to_reference(tmp, v, tc, [period_col], rule="sum")
                for c in cc:
                    ref[c] = ref[c + "__vw"] / ref[c + "__w"].replace(0, np.nan)
            else:
                ref, _ = to_reference(d[[*keycols, period_col, *cc]], v, cc, [period_col], rule=rule)
            sup, _ = to_reference(d[[*keycols, period_col, *[c + SUP for c in cc]]], v,
                                  [c + SUP for c in cc], [period_col], rule="sum")
            ref = ref.merge(sup[["bfs_nr", period_col, *[c + SUP for c in cc]]],
                            on=["bfs_nr", period_col], how="left")
            if precision:
                ref.loc[ref["precision"] == "exact", "precision"] = precision
            for c in cc:
                o = emit(ref, {c: metric_map[c]}, period_col, source_id)
                s = (ref[c + SUP].fillna(0) > 0).to_numpy()
                o.loc[s, "value"] = np.nan
                o.loc[s, "status"] = "suppressed"
                o.loc[s, "note"] = "suppressed in source (small numbers)"
                if rule == "not_aggregatable":
                    na = (~s) & o["value"].isna().to_numpy()
                    o.loc[na, "note"] = "not 1:1 with the reference state (merger/split); not re-aggregatable"
                    o.loc[na, "status"] = "not_applicable"
                parts.append(o)
    out = pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
    return out


def native_rows(df: pd.DataFrame, unit_col: str, level: str, metric_map: dict[str, str],
                source_id: str, period_col: str = "period", precision: str = "exact") -> pd.DataFrame:
    """Published canton / national rows kept as 'native' for the plausibility sweep."""
    from pipeline.common import REFERENCE_DATE
    o = emit(df, metric_map, period_col, source_id, level=level, unit_col=unit_col,
             vintage=REFERENCE_DATE, precision=precision, provenance="native")
    return o


def fetch_post(url: str, source_id: str, filename: str, payload: dict, *, refresh: bool = False,
               timeout: int = 300, retries: int = 4, pause: float = 1.0) -> "os.PathLike":
    """POST-JSON counterpart of pipeline.common.fetch: cached in data/raw/<source_id>/<date>/,
    reused unless refresh / GB_REFRESH=1, manifest line with the request body."""
    import time
    refresh = refresh or os.environ.get("GB_REFRESH") == "1"
    cached = latest_snapshot(source_id, filename)
    if cached and not refresh:
        return cached
    day = dt.date.today().isoformat()
    target = RAW / source_id / day / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    hdrs = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(url, data=json.dumps(payload), headers=hdrs, timeout=timeout)
            if r.status_code in (429, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code}", response=r)
            r.raise_for_status()
            tmp = target.with_suffix(target.suffix + ".part")
            tmp.write_bytes(r.content)
            tmp.replace(target)
            break
        except (requests.RequestException, OSError) as e:
            last = e
            time.sleep(2 ** (attempt + 1))
    else:
        raise RuntimeError(f"POST failed after {retries} attempts: {url} {payload}") from last
    h = hashlib.sha256(target.read_bytes()).hexdigest()
    entry = {"file": str(target.relative_to(RAW / source_id)), "url": url, "method": "POST",
             "body": payload, "sha256": h, "bytes": target.stat().st_size,
             "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with open(RAW / source_id / "manifest.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    time.sleep(pause)
    return target
