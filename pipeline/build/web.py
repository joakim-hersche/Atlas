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
import os
import re

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
            elif lvl == "kanton":
                name = _canton_name(uid)
            units.append({"id": str(uid), "level": lvl, "name": name, "label": lab.get(lvl, {}).get(str(uid)),
                          "n_gemeinden": len(g), "kanton": g["kanton"].iloc[0] if g["kanton"].nunique() == 1 else None})
    units.append({"id": "CH", "level": "schweiz", "name": "Schweiz", "n_gemeinden": len(m)})
    return units


def _canton_name(code: str) -> str:
    """Official register name of the canton (BFS register, e.g. 'Bern / Berne'); the code if missing."""
    reg = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    hit = reg[reg["canton"] == str(code)]
    return hit["name"].iloc[0] if len(hit) else str(code)


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


def license_cleared(m: dict) -> tuple[bool, str]:
    """Brief rule 5: only sources whose terms are stated as open are shipped by default."""
    lic = str(m.get("license") or m.get("licence") or "")
    st = str(m.get("license_status") or "").upper()
    if st == "UNVERIFIED" or re.search(r"UNVERIFIED|proprietary|per publisher|unclear", lic, re.I):
        return False, "licence to verify"
    if re.search(r"OPEN-BY|CC.?BY|CC0|ODbL|terms_by|open use|freie nutzung|reproduction|wiedergabe", lic, re.I):
        return True, "open"
    return False, "licence not stated"


def run() -> dict:
    """Builds data/out/web from metrics_all.parquet with DuckDB (the table does not fit in memory).

    Sources whose licence is not cleared are left out unless GB_INCLUDE_UNVERIFIED=1 (local preview
    only); the excluded list is written to data/out/web/excluded_sources.json.
    """
    import duckdb
    meta = load_metrics().drop_duplicates("id").set_index("id")
    srcs = {}
    for f in sorted(SOURCES_DIR.glob("*/meta.yaml")):
        m = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        srcs[f.parent.name] = m
    include_all = os.environ.get("GB_INCLUDE_UNVERIFIED") == "1"
    review = yaml.safe_load((SOURCES_DIR.parent / "licence_review.yaml").read_text(encoding="utf-8")) or {}
    cleared = {sid: license_cleared(m) for sid, m in srcs.items()}
    metric_only = {}
    for sid, r in review.items():
        if r.get("status") == "cleared":
            cleared[sid] = (True, "reviewed")
            if r.get("metrics"):
                metric_only[sid] = set(r["metrics"])
        elif r.get("status") == "blocked":
            cleared[sid] = (False, "blocked by review")
    excluded = {sid: why for sid, (ok, why) in cleared.items() if not ok and (SOURCES_DIR / sid / "ingest.py").exists()}

    def shippable(mid):
        sid = meta.loc[mid, "source_id"]
        return sid not in excluded and (sid not in metric_only or mid in metric_only[sid])
    keep = [mid for mid in meta.index if include_all or shippable(mid)]
    # derived metrics whose inputs come from an excluded source are dropped too
    if not include_all:
        def inputs_ok(mid):
            agg = str(meta.loc[mid, "aggregation"])
            ids = re.findall(r"[a-z][a-z0-9_]+", agg.split(":", 1)[1]) if ":" in agg else []
            return all(i not in meta.index or shippable(i) for i in ids)
        keep = [m for m in keep if meta.loc[m, "kind"] != "derived" or inputs_ok(m)]
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{os.environ.get('GB_DUCKDB_MEMORY', '3GB')}'")
    con.register("keep_df", pd.DataFrame({"metric_id": keep}))
    src = f"read_parquet('{interim_path('metrics_all.parquet')}')"
    # per-canton clearance (licence_review `cantons:`): municipalities of other cantons become
    # 'not_covered' with a licence note; only cleared cantons keep canton rows; other levels dropped
    canton_rows = []
    if not include_all:
        for sid, r in review.items():
            if r.get("status") == "cleared" and r.get("cantons"):
                for mid in meta.index[meta["source_id"] == sid]:
                    for kt in r["cantons"]:
                        canton_rows.append((mid, kt))
    con.register("kt_ok", pd.DataFrame(canton_rows or [("", "")], columns=["metric_id", "kanton"]))
    mem = membership()[["bfs_nr", "kanton"]].assign(unit_id=lambda d: d["bfs_nr"].astype(str))
    con.register("mem_kt", mem[["unit_id", "kanton"]])
    con.execute(f"""CREATE VIEW m AS
        WITH base AS (SELECT * FROM {src} WHERE metric_id IN (SELECT metric_id FROM keep_df)
                      AND level NOT IN ('unallocated', 'pseudo')),
             limited AS (SELECT DISTINCT metric_id FROM kt_ok WHERE metric_id <> '')
        SELECT b.* FROM base b WHERE b.metric_id NOT IN (SELECT metric_id FROM limited)
        UNION ALL
        SELECT b.unit_id, b.level, b.metric_id, b.period,
               CASE WHEN k.kanton IS NOT NULL THEN b.value END AS value,
               CASE WHEN k.kanton IS NOT NULL THEN b.status ELSE 'not_covered' END AS status,
               b.precision, b.provenance, b.n_units, b.n_missing,
               CASE WHEN k.kanton IS NOT NULL THEN b.note
                    ELSE 'not shipped: licence of this canton''s publisher not cleared' END AS note
        FROM base b JOIN mem_kt g ON b.level = 'gemeinde' AND b.unit_id = g.unit_id
        LEFT JOIN kt_ok k ON k.metric_id = b.metric_id AND k.kanton = g.kanton
        WHERE b.metric_id IN (SELECT metric_id FROM limited)
        UNION ALL
        SELECT b.* FROM base b JOIN kt_ok k ON b.level = 'kanton' AND b.metric_id = k.metric_id
                                         AND b.unit_id = k.kanton""")
    written = {"units": _dump(build_units(), "units.json"),
               "sources": _dump([{**{k: v.get(k) for k in ("source_id", "title", "publisher", "url", "license",
                                                              "attribution", "vintage", "years")},
                                  "shipped": include_all or (sid not in excluded if (SOURCES_DIR / sid / "ingest.py").exists()
                                                             else cleared[sid][0])}
                                 # lookups (kind: lookup) feed search/profile files (pipeline.build.profile)
                                 for sid, v in srcs.items() if (SOURCES_DIR / sid / "ingest.py").exists()
                                 or v.get("kind") == "lookup"], "sources.json"),
               "excluded": _dump({"note": "left out until their licence is cleared (brief rule 5)",
                                  "sources": excluded if not include_all else {}}, "excluded_sources.json")}

    per = con.execute("""SELECT metric_id, list(DISTINCT period) AS periods,
                                list(DISTINCT level) FILTER (WHERE status = 'ok') AS levels
                         FROM m GROUP BY 1""").df()
    hl = yaml.safe_load((SOURCES_DIR.parent / "headline_metrics.yaml").read_text(encoding="utf-8")) or {}
    headline_rank = {m: i for i, m in enumerate(x for v in (hl.get("headline") or {}).values() for x in v)}
    hidden = set(hl.get("hidden") or [])
    file_of = {}
    for mid in meta.index:
        file_of[mid] = "core" if mid in headline_rank else re.sub(r"[^a-z]+", "_", meta.loc[mid, "theme"].lower()).strip("_")
    catalog = []
    for r in per.itertuples():
        md = meta.loc[r.metric_id]
        periods = sorted(r.periods, key=_period_key)
        catalog.append({
            "id": r.metric_id, "theme": md["theme"], "label_en": md["label_en"], "label_de": md["label_de"],
            "unit": md["unit"], "decimals": int(md["decimals"]), "direction": md["direction"],
            "aggregation": md["aggregation"], "precision": md["precision"], "coverage": md["coverage"],
            "source": md["source_id"],
            "description": md.get("description") if isinstance(md.get("description"), str) else None,
            "levels": sorted(r.levels) if r.levels is not None else [],
            "n_periods": len(periods), "periods": periods if len(periods) <= 60 else periods[-60:],
            "latest": periods[-1], "per_vote": str(r.metric_id).startswith("vote_"),
            "headline": headline_rank.get(r.metric_id), "hidden": r.metric_id in hidden,
            "file": file_of[r.metric_id],
        })
    written["metrics"] = _dump(catalog, "metrics.json")

    # latest period per metric and level (columnar)
    for lvl in [l[0] for l in con.execute("SELECT DISTINCT level FROM m").fetchall()]:
        g = con.execute(f"""WITH lp AS (SELECT metric_id, max(period) AS p FROM m
                                       WHERE level = '{lvl}' AND status = 'ok' GROUP BY 1)
                            SELECT m.unit_id, m.metric_id, m.period, m.value, m.status, m.precision
                            FROM m JOIN lp ON m.metric_id = lp.metric_id AND m.period = lp.p
                            WHERE m.level = '{lvl}'""").df()
        ids = sorted(g["unit_id"].unique(), key=lambda x: (len(x), x))
        idx = {u: i for i, u in enumerate(ids)}
        cols = {}
        for mid, gm in g.groupby("metric_id"):
            d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
            vals = [None] * len(ids)
            status, prec = {}, {}
            for u, v, st, pr in zip(gm["unit_id"], gm["value"], gm["status"], gm["precision"]):
                i = idx[u]
                vals[i] = _round(v, d)
                if st != "ok":
                    status[i] = STATUS_CODES.get(st, 1)
                if isinstance(pr, str) and pr != "exact":
                    prec[i] = PRECISION_CODES.get(pr, 0)
            cols[mid] = {"period": gm["period"].iloc[0], "v": vals,
                         **({"s": status} if status else {}), **({"p": prec} if prec else {})}
        # D23: one core file (headline metrics) loaded at start, one file per theme on demand
        groups: dict[str, dict] = {}
        for mid, col in cols.items():
            groups.setdefault(file_of[mid], {})[mid] = col
        for fname, gcols in groups.items():
            written[f"latest_{lvl}_{fname}"] = _dump(
                {"level": lvl, "units": ids, "metrics": gcols, "status_codes": STATUS_CODES,
                 "precision_codes": PRECISION_CODES}, "latest", lvl, f"{fname}.json")

    # time series per metric (municipality, district, canton, Switzerland); votes get one file per vote
    lv = ", ".join(f"'{x}'" for x in SERIES_LEVELS)
    n_series = 0
    for (mid,) in con.execute("SELECT DISTINCT metric_id FROM m").fetchall():
        if str(mid).startswith("vote_"):
            continue
        g = con.execute(f"SELECT level, unit_id, period, value FROM m WHERE metric_id = ? AND level IN ({lv})",
                        [mid]).df()
        periods = sorted(g["period"].unique(), key=_period_key)
        if len(periods) < 2:
            continue
        pidx = {p: i for i, p in enumerate(periods)}
        d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
        out = {"metric": mid, "periods": periods, "levels": {}}
        for lvl_, gl in g.groupby("level"):
            series = {}
            for uid, gu in gl.groupby("unit_id"):
                row = [None] * len(periods)
                for p, v in zip(gu["period"], gu["value"]):
                    row[pidx[p]] = _round(v, d)
                series[uid] = row
            out["levels"][lvl_] = series
        _dump(out, "series", f"{mid}.json")
        n_series += 1
    # votes: one file per vote with yes share and turnout for every level
    vt = con.execute("""SELECT period, level, unit_id, metric_id, value FROM m
                        WHERE metric_id IN ('vote_yes_share', 'vote_turnout') AND status = 'ok'""").df()
    n_votes = 0
    for per_, gv in vt.groupby("period"):
        vid = per_.replace("#", "_")
        out = {"period": per_, "levels": {}}
        for lvl_, gl in gv.groupby("level"):
            out["levels"][lvl_] = {mid: dict(zip(gm["unit_id"], [_round(v, 2) for v in gm["value"]]))
                                   for mid, gm in gl.groupby("metric_id")}
        _dump(out, "votes", f"{vid}.json")
        n_votes += 1
    written["series_count"], written["vote_files"] = n_series, n_votes
    written["excluded_sources"] = len(excluded) if not include_all else 0
    return written


if __name__ == "__main__":
    import os
    w = run()
    for k, v in w.items():
        if isinstance(v, str):
            print(f"{k:22s} {os.path.getsize(v)/1024:9.0f} KB")
        else:
            print(k, v)
