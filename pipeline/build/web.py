"""Files the static web app loads (brief 6.3; format to be confirmed at Checkpoint 3).

data/out/web/
  units.json                 every unit of every level: id, level, name, canton, district, parents, label point
  metrics.json               metric catalog: labels, unit, decimals, direction, theme, aggregation, precision,
                             coverage, source, levels available, periods
  latest/<level>.json        columnar latest-period values of all metrics for one level
  series/<metric_id>.json    all periods for municipalities, districts and cantons (loaded on demand)
  sources.json               per source: title, publisher, url, license, attribution, vintage

Values are rounded to the metric's decimals (+1 for shares). Gaps are explicit (decision D21):
value null plus a status code from STATUS_CODES.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import yaml

from pipeline.backbone.levels import membership
from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.harmonize.schema import SOURCES_DIR, load_metrics

STATUS_CODES = {"ok": 0, "no_data": 1, "suppressed": 2, "not_published": 3, "not_covered": 4,
                "not_applicable": 5}
PRECISION_CODES = {"exact": 0, "survey": 1, "modelled": 2, "boundary_estimate": 3}
SERIES_LEVELS = ("gemeinde", "bezirk", "kanton", "schweiz")


def _dump(obj, *parts) -> str:
    p = out_path("web", *parts)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    return str(p)


def _round(v, d):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(float(v), int(d)) if d > 0 else int(round(float(v)))


def _period_key(p: str):
    return (p[:4], p)


def build_units() -> list[dict]:
    m = membership()
    labels = json.loads(out_path("geo", "labels.json").read_text(encoding="utf-8"))
    lab = {lvl: {d["id"]: d["label"] for d in items} for lvl, items in labels.items()}
    units = []
    for r in m.itertuples():
        units.append({"id": str(r.bfs_nr), "level": "gemeinde", "name": r.name, "kanton": r.kanton,
                      "bezirk": r.bezirk, "label": lab.get("gemeinde", {}).get(str(r.bfs_nr)),
                      **{lvl: getattr(r, lvl) for lvl in ("grossregion", "sprachgebiet", "agglomeration",
                                                          "arbeitsmarktgebiet", "stadt_land", "gemeindetyp")
                         if hasattr(r, lvl) and isinstance(getattr(r, lvl), str)}})
    for lvl in ("bezirk", "kanton", "grossregion", "sprachgebiet", "agglomeration", "arbeitsmarktgebiet",
                "stadt_land", "gemeindetyp"):
        if lvl not in m.columns:
            continue
        name_col = f"{lvl}_name" if f"{lvl}_name" in m.columns else None
        for uid, g in m.dropna(subset=[lvl]).groupby(lvl):
            name = g[name_col].iloc[0] if name_col else uid
            if lvl == "bezirk":
                name = _district_name(uid)
            units.append({"id": str(uid), "level": lvl, "name": name, "label": lab.get(lvl, {}).get(str(uid)),
                          "n_gemeinden": len(g), "kanton": g["kanton"].iloc[0] if g["kanton"].nunique() == 1 else None})
    units.append({"id": "CH", "level": "schweiz", "name": "Schweiz", "n_gemeinden": len(m)})
    return units


def _district_name(nr: str) -> str:
    dv = pd.read_parquet(interim_path("backbone", "district_version.parquet"))
    ref = pd.Timestamp(REFERENCE_DATE)
    cur = dv[(dv["valid_from"] <= ref) & (dv["valid_to"].isna() | (dv["valid_to"] >= ref))]
    hit = cur[cur["district_nr"].astype(str) == str(nr)]
    return hit["name"].iloc[0] if len(hit) else str(nr)


def build_sources() -> list[dict]:
    out = []
    for f in sorted(SOURCES_DIR.glob("*/meta.yaml")):
        m = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if not (f.parent / "ingest.py").exists():
            continue
        out.append({k: m.get(k) for k in ("source_id", "title", "publisher", "url", "license", "attribution",
                                          "vintage", "years")})
    return out


def run() -> dict:
    meta = load_metrics().drop_duplicates("id").set_index("id")
    allm = pd.read_parquet(interim_path("metrics_all.parquet"))
    allm = allm[allm["metric_id"].isin(meta.index)]
    written = {"units": _dump(build_units(), "units.json"), "sources": _dump(build_sources(), "sources.json")}

    catalog = []
    for mid, g in allm.groupby("metric_id"):
        md = meta.loc[mid]
        periods = sorted(g["period"].unique(), key=_period_key)
        catalog.append({
            "id": mid, "theme": md["theme"], "label_en": md["label_en"], "label_de": md["label_de"],
            "unit": md["unit"], "decimals": int(md["decimals"]), "direction": md["direction"],
            "aggregation": md["aggregation"], "precision": md["precision"], "coverage": md["coverage"],
            "source": md["source_id"], "description": md.get("description") if isinstance(md.get("description"), str) else None,
            "levels": sorted(g.loc[g["status"] == "ok", "level"].unique().tolist()),
            "periods": periods, "latest": periods[-1],
        })
    written["metrics"] = _dump(catalog, "metrics.json")

    # latest period per metric and level, columnar
    for lvl, g in allm.groupby("level"):
        if lvl in ("unallocated", "pseudo"):
            continue
        g = g.copy()
        latest = g[g["status"] == "ok"].groupby("metric_id")["period"].max()
        g = g[g["period"] == g["metric_id"].map(latest)]
        ids = sorted(g["unit_id"].unique(), key=lambda x: (len(x), x))
        idx = {u: i for i, u in enumerate(ids)}
        cols = {}
        for mid, gm in g.groupby("metric_id"):
            d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
            vals = [None] * len(ids)
            status, prec = {}, {}
            for r in gm.itertuples():
                i = idx[r.unit_id]
                vals[i] = _round(r.value, d)
                if r.status != "ok":
                    status[i] = STATUS_CODES.get(r.status, 1)
                if r.precision not in ("exact", None) and isinstance(r.precision, str):
                    prec[i] = PRECISION_CODES.get(r.precision, 0)
            cols[mid] = {"period": gm["period"].iloc[0], "v": vals,
                         **({"s": status} if status else {}), **({"p": prec} if prec else {})}
        written[f"latest_{lvl}"] = _dump({"level": lvl, "units": ids, "metrics": cols,
                                          "status_codes": STATUS_CODES, "precision_codes": PRECISION_CODES},
                                         "latest", f"{lvl}.json")

    # time series per metric
    ser = allm[allm["level"].isin(SERIES_LEVELS)]
    for mid, g in ser.groupby("metric_id"):
        periods = sorted(g["period"].unique(), key=_period_key)
        if len(periods) < 2:
            continue
        pidx = {p: i for i, p in enumerate(periods)}
        d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
        out = {"metric": mid, "periods": periods, "levels": {}}
        for lvl, gl in g.groupby("level"):
            series = {}
            for uid, gu in gl.groupby("unit_id"):
                row = [None] * len(periods)
                for r in gu.itertuples():
                    row[pidx[r.period]] = _round(r.value, d)
                series[uid] = row
            out["levels"][lvl] = series
        _dump(out, "series", f"{mid}.json")
    written["series_count"] = ser["metric_id"].nunique()
    return written


if __name__ == "__main__":
    import os
    w = run()
    for k, v in w.items():
        if isinstance(v, str):
            print(f"{k:22s} {os.path.getsize(v)/1024:9.0f} KB")
        else:
            print(k, v)
