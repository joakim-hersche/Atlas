"""Files the static web app loads (brief 6.3; format to be confirmed at Checkpoint 3).

data/out/web/
  units.json                 every unit of every level: id, level, name, canton, district, parents, label point
  metrics.json               metric catalog: labels, unit, decimals, direction, theme, aggregation, precision,
                             coverage, source, levels available, periods
  latest/<level>.json        columnar latest-period values of all metrics for one level
  series/<metric_id>.json    all periods for municipalities, districts and cantons (loaded on demand)
  sources.json               per source: title, publisher, url, license, attribution, vintage

Values are rounded to the metric's decimals (+1 for shares). Gaps are explicit (decision D21):
value null plus a status code from STATUS_CODES, and the reason in the column's notes.
Shapes added in review round 1 are specified in docs/web_data_contract.md (default period rule,
coverage from the shipped data, per-unit flags and notes, votes/index.json, typology names).
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
FLAG_BITS = {"small_base": 1, "small_count": 2, "majority_election": 4, "published_value": 8, "provisional": 16}
COVERAGE_MIN = 0.95          # default period: newest with >= 95 % of the metric's best coverage (F)
CANTON_COVERED = 0.5         # a canton counts as covered when >= 50 % of its municipalities have data (G)
TYPOLOGY_COLS = {"grossregion": "REGCH", "sprachgebiet": "SPRGEB2020", "agglomeration": "AGGL2020",
                 "arbeitsmarktgebiet": "BAE2018", "stadt_land": "STALAN2020", "gemeindetyp": "GDETYP2020_9"}
LEVEL_WORD = {"gemeinde": "municipality", "bezirk": "district", "kanton": "canton", "schweiz": "national"}
# notes of ok values worth showing (fallback provenance, provisional results, reach details)
OK_NOTE = re.compile(r"published|provisional|no arrival|nearest hub|computed from published", re.I)
PUBLIC_TEXT = [(re.compile(r"\bPARTLY_UNVERIFIED\b"), "partly not yet confirmed"),
               (re.compile(r"\bUNVERIFIED\b"), "not yet confirmed"),
               (re.compile(r"\s*\(?brief rule 5\)?", re.I), "")]


def public_text(v):
    """Plain wording for public files (no internal jargon such as UNVERIFIED or 'brief rule 5')."""
    if not isinstance(v, str):
        return v
    for rx, rep in PUBLIC_TEXT:
        v = rx.sub(rep, v)
    return v


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
    lv = pd.read_parquet(interim_path("backbone", f"levels_{REFERENCE_DATE.isoformat()}.parquet"))
    names_of = {}
    for lvl, col in TYPOLOGY_COLS.items():   # official BFS labels (register levels table), H
        langs = [l for l in ("de", "fr", "it", "en") if f"{col}_{l}" in lv.columns]
        g = lv.dropna(subset=[col]).astype({col: str}).drop_duplicates(col).set_index(col)
        names_of[lvl] = {k: {l: r[f"{col}_{l}"] for l in langs if isinstance(r[f"{col}_{l}"], str) and r[f"{col}_{l}"].strip()}
                         for k, r in g.iterrows()}
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
            u = {"id": str(uid), "level": lvl, "name": name, "label": lab.get(lvl, {}).get(str(uid)),
                 "n_gemeinden": len(g), "kanton": g["kanton"].iloc[0] if g["kanton"].nunique() == 1 else None}
            if lvl in names_of and names_of[lvl].get(str(uid)):
                u["names"] = names_of[lvl][str(uid)]
            units.append(u)
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


def fetched_date(sid: str, meta: dict) -> str | None:
    """Newest download date of a source: its own manifest (data/raw/<sid>/manifest.jsonl), the shared
    PxWeb / SDMX caches for the cubes and dataflows its code or meta.yaml names, and meta `inputs`."""
    from pipeline.common import RAW
    import json as _json

    def newest(manifest, match=None):
        if not manifest.exists():
            return None
        best = None
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try:
                r = _json.loads(line)
            except ValueError:
                continue
            if match and not any(k in (r.get("url") or "") or k in (r.get("file") or "") for k in match):
                continue
            t = (r.get("fetched_at") or "")[:10]
            best = max(best or t, t)
        return best
    dates = [newest(RAW / sid / "manifest.jsonl")]
    d = SOURCES_DIR / sid
    text = " ".join(f.read_text(encoding="utf-8") for f in d.glob("*.py")) + str(meta.get("cubes", "")) \
        + str(meta.get("dataflows", ""))
    cubes = sorted(set(re.findall(r"px-x-\d{10}_\d{3}", text)))
    flows = sorted(set(re.findall(r"DF_[A-Z0-9_]+", text)))
    if cubes:
        dates.append(newest(RAW / "bfs_pxweb" / "manifest.jsonl", cubes))
    if flows:
        dates.append(newest(RAW / "bfs_sdmx" / "manifest.jsonl", flows))
    for other in meta.get("inputs") or []:
        dates.append(newest(RAW / other / "manifest.jsonl"))
    dates = [x for x in dates if x]
    return max(dates) if dates else None


def license_cleared(m: dict) -> tuple[bool, str]:
    """Only sources whose terms are stated as open are shipped by default (CLAUDE.md rule 5)."""
    lic = str(m.get("license") or m.get("licence") or "")
    st = str(m.get("license_status") or "").upper()
    if st == "UNVERIFIED" or re.search(r"UNVERIFIED|proprietary|per publisher|unclear", lic, re.I):
        return False, "licence to verify"
    if re.search(r"OPEN-BY|CC.?BY|CC0|ODbL|terms_by|open use|freie nutzung|reproduction|wiedergabe", lic, re.I):
        return True, "open"
    return False, "licence not stated"


UNIT_PLURAL_EN = {"gemeinde": "municipalities", "bezirk": "districts", "kanton": "cantons"}
UNIT_PLURAL_DE = {"gemeinde": "Gemeinden", "bezirk": "Bezirken", "kanton": "Kantonen"}
STATUS_REASON = {"suppressed": "values suppressed (small numbers)", "not_published": "not published at this level",
                 "not_covered": "not covered", "not_applicable": "not applicable", "no_data": "no data"}


def membership_counts() -> dict:
    """Number of units per level (reference state)."""
    m = membership()
    out = {"gemeinde": len(m), "schweiz": 1}
    for lvl in ("bezirk", "kanton", *TYPOLOGY_COLS):
        if lvl in m.columns:
            out[lvl] = int(m[lvl].dropna().nunique())
    return out


def _formula(agg: str):
    """(numerator terms, denominator terms, pooled years, denominator lag) of a ratio/pooled formula."""
    from pipeline.build.metrics import POOLED, RATIO, _terms
    if (r := RATIO.match(agg)):
        return _terms(r["num"]), _terms(r["den"]), 1, 0
    if (p := POOLED.match(agg)):
        return _terms(p["num"]), _terms(p["den"]), int(p["k"]), int(p["lag"] or 0)
    return None


def _reliability(mid: str, meta: pd.DataFrame, cfg: dict) -> dict | None:
    """Small-number rule of one metric (pipeline/reliability.yaml, D32)."""
    d = cfg.get("defaults") or {}
    o = (cfg.get("metrics") or {}).get(mid) or {}
    f = _formula(str(meta.loc[mid, "aggregation"]))
    count = o["count"] if "count" in o else ("+".join(f[0]) if f else None)
    base = o.get("base") or (f[1][0] if f else None)
    if not count and not base:
        return None
    return {"count": count, "base": base, "min_count": d.get("min_count", 20) if count else None,
            "min_base": d.get("min_base", 1000) if base else None,
            "years": f[2] if f else 1, "rule_en": d.get("rule_en"), "rule_de": d.get("rule_de")}


def _pooled_meta(md) -> dict | None:
    f = _formula(str(md["aggregation"]))
    if not f or f[2] == 1:
        return None
    of = re.sub(r"_\dy$", "", str(md.name))
    return {"of": of, "years": f[2]}


def load_i18n() -> dict:
    """French labels and German/French units (pipeline/i18n/labels.yaml, research agent), by metric id.
    Accepts a mapping {id: {label_fr, unit_de, unit_fr}} or a list of such dicts with 'id'."""
    p = SOURCES_DIR.parent / "i18n" / "labels.yaml"
    if not p.exists():
        return {}
    y = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if isinstance(y, dict) and "metrics" in y:
        y = y["metrics"]
    if isinstance(y, list):
        y = {r["id"]: r for r in y if isinstance(r, dict) and "id" in r}
    return {k: {f: v.get(f) for f in ("label_fr", "unit_de", "unit_fr") if isinstance(v, dict)}
            for k, v in (y or {}).items() if isinstance(v, dict)}


def build_glossary() -> str | None:
    """pipeline/i18n/glossary.yaml (research agent) -> data/out/web/glossary.json for the frontend."""
    p = SOURCES_DIR.parent / "i18n" / "glossary.yaml"
    if not p.exists():
        return None
    return _dump(yaml.safe_load(p.read_text(encoding="utf-8")) or {}, "glossary.json")


def majority_by_year() -> dict:
    """Election year -> cantons with one National Council seat (majority election), BFS cube 103."""
    try:
        from pipeline.sources.bfs_nrw.fetch import majority_cantons
        return majority_cantons()
    except Exception as e:  # noqa: BLE001 — offline without a cached cube: no flag, and say so
        print("majority cantons not available:", e)
        return {}


def load_vote_titles() -> dict:
    """period 'YYYY-MM-DD#id' -> {de, fr, it, en} title (vorlagen.csv); languages without a title left out."""
    p = SOURCES_DIR / "bfs_votes_gemeinde" / "vorlagen.csv"
    if not p.exists():
        return {}
    v = pd.read_csv(p, dtype=str)
    out = {}
    for r in v.itertuples():
        t = {l: getattr(r, f"title_{l}") for l in ("de", "fr", "it", "en")
             if isinstance(getattr(r, f"title_{l}", None), str)}
        out[f"{r.date}#{r.vorlagen_id}"] = t
    return out


def _unavailable_reason(md, level: str, gap_status: str | None) -> str:
    """Why a metric has no values at a level (D: the real reason, not 'no data for this year')."""
    if isinstance(md.get("unavailable_note"), str) and level not in ("gemeinde",):
        return md["unavailable_note"]
    nat = str(md["native_level"])
    word = LEVEL_WORD.get(nat, nat)
    survey = " (survey)" if md["precision"] == "survey" else ""
    if nat != "gemeinde" and level != nat:
        return f"published only at {word} level{survey}"
    if md["aggregation"] == "not_aggregatable":
        return "cannot be aggregated (median, index or published rate) and the source publishes no value at this level"
    if gap_status:
        return "incomplete at this level: " + STATUS_REASON.get(gap_status, gap_status) + " for some municipalities"
    return "no data at this level"


def _notes_fields(notes: dict) -> dict:
    """{index: text} -> {'notes': [...], 'n': {index: k}} with repeated texts stored once."""
    if not notes:
        return {}
    texts = sorted(set(notes.values()))
    k = {t: i for i, t in enumerate(texts)}
    return {"notes": texts, "n": {str(i): k[t] for i, t in notes.items()}}


def unit_flags(con, lvl: str, g: pd.DataFrame, idx: dict, reliability: dict, majority: dict,
               meta: pd.DataFrame) -> dict:
    """Per metric: {unit index: bitmask} (FLAG_BITS) for one level's default-period columns."""
    out: dict[str, dict] = {}

    def add(mid, i, bit):
        out.setdefault(mid, {})
        out[mid][i] = out[mid].get(i, 0) | bit
    # published value used (fallback) and provisional results
    for mid, u, pv, nt, st in zip(g["metric_id"], g["unit_id"], g["provenance"], g["note"], g["status"]):
        if st != "ok":
            continue
        if lvl != "gemeinde" and pv == "native" and str(meta.loc[mid, "aggregation"]) != "not_aggregatable" \
                and str(meta.loc[mid, "native_level"]) == "gemeinde":
            add(mid, idx[u], FLAG_BITS["published_value"])
        if isinstance(nt, str) and "provisional" in nt:
            add(mid, idx[u], FLAG_BITS["provisional"])
    # majority-election cantons (NRW)
    if majority and lvl in ("gemeinde", "bezirk", "kanton"):
        mem = membership()
        kt_of = (dict(zip(mem["bfs_nr"].astype(str), mem["kanton"])) if lvl == "gemeinde" else
                 dict(zip(mem["bezirk"].astype(str), mem["kanton"])) if lvl == "bezirk" else None)
        nrw = g[g["metric_id"].str.startswith("nrw_") & (g["status"] == "ok")]
        for mid, u, per in zip(nrw["metric_id"], nrw["unit_id"], nrw["period"]):
            kt = u if kt_of is None else kt_of.get(u)
            if kt in set(majority.get(str(per)[:4], [])):
                add(mid, idx[u], FLAG_BITS["majority_election"])
    # small numbers (D32)
    for mid, rule in reliability.items():
        gm = g[(g["metric_id"] == mid) & (g["status"] == "ok")]
        if gm.empty:
            continue
        per = gm["period"].iloc[0]
        years = [per]
        if re.fullmatch(r"\d{4}-\d{4}", per):
            a, b = int(per[:4]), int(per[5:])
            years = [str(y) for y in range(a, b + 1)]
        for kind, bit in (("count", "small_count"), ("base", "small_base")):
            expr, lim = rule.get(kind), rule.get(f"min_{kind}")
            if not expr or lim is None:
                continue
            ids = expr.split("+")
            v = con.execute(f"""SELECT unit_id, SUM(value) AS v, COUNT(DISTINCT period) AS ny FROM m
                                WHERE level = '{lvl}' AND status = 'ok' AND metric_id IN ({", ".join("'" + i + "'" for i in ids)})
                                  AND period IN ({", ".join("'" + y + "'" for y in years)})
                                GROUP BY 1""").df()
            # per-unit sum over the terms and years
            shown = set(gm["unit_id"])
            for u in v.loc[v["v"] < lim, "unit_id"]:
                if u in idx and u in shown:
                    add(mid, idx[u], FLAG_BITS[bit])
    return out


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
    credited = {c for c in meta.get("credit_source", pd.Series(dtype=object)).dropna().unique() if c in srcs}
    src_rows = []
    for sid, v in srcs.items():
        # lookups (kind: lookup) feed search/profile files (pipeline.build.profile); credited sources
        # (credit_source) are shown as the source of metrics computed from them
        if not ((SOURCES_DIR / sid / "ingest.py").exists() or v.get("kind") == "lookup" or sid in credited):
            continue
        shipped = include_all or (sid not in excluded if (SOURCES_DIR / sid / "ingest.py").exists() else cleared[sid][0])
        row = {k: public_text(v.get(k)) for k in ("source_id", "title", "publisher", "url", "license",
                                                   "attribution", "vintage", "years")}
        row.update({"shipped": shipped, "fetched": fetched_date(sid, v),
                    "status_text": "shipped" if shipped else ("held back: licence not yet confirmed"
                                                              if "verify" in str(cleared[sid][1]) or "not stated" in str(cleared[sid][1])
                                                              else "held back: licence review")})
        src_rows.append(row)
    written = {"units": _dump(build_units(), "units.json"),
               "sources": _dump(src_rows, "sources.json"),
               "excluded": _dump({"note": "held back until their licence is confirmed",
                                  "sources": excluded if not include_all else {}}, "excluded_sources.json")}

    # ---- per metric × level × period coverage (default-period rule F, coverage labels G)
    cov = con.execute("""SELECT metric_id, level, period, COUNT(*) FILTER (WHERE status = 'ok') AS n_ok,
                                COUNT(*) AS n_rows, mode(status) FILTER (WHERE status <> 'ok') AS gap_status
                         FROM m GROUP BY 1, 2, 3""").df()
    per_vote = cov["metric_id"].str.startswith("vote_")
    cov["key"] = cov["period"].map(_period_key)
    n_units_level = pd.Series({lvl: n for lvl, n in membership_counts().items()})
    lp_rows, incomplete, avail, gap_mode = [], {}, {}, {}
    for (mid, lvl), g in cov.groupby(["metric_id", "level"], sort=False):
        g = g.sort_values("key")
        ok = g[g["n_ok"] > 0]
        if ok.empty:
            gap_mode[(mid, lvl)] = g["gap_status"].mode().iloc[0] if g["gap_status"].notna().any() else "no_data"
            continue
        best = ok["n_ok"].max()
        if str(mid).startswith("vote_"):
            dflt = ok["period"].iloc[-1]
        else:
            dflt = ok.loc[ok["n_ok"] >= COVERAGE_MIN * best, "period"].iloc[-1]
        lp_rows.append((mid, lvl, dflt))
        newer = ok[ok["key"] > _period_key(dflt)]
        if len(newer):
            of = int(n_units_level.get(lvl, best))
            incomplete[(mid, lvl)] = {p: {"n": int(n), "of": of, "level": lvl,
                                          "label_en": f"in progress: {n:,} of {of:,} {UNIT_PLURAL_EN.get(lvl, 'units')}",
                                          "label_de": f"in Bearbeitung: {n:,} von {of:,} {UNIT_PLURAL_DE.get(lvl, 'Einheiten')}".replace(",", "'")}
                                      for p, n in zip(newer["period"], newer["n_ok"])}
        avail[(mid, lvl)] = ok["period"].iloc[-1]
    lp = pd.DataFrame(lp_rows, columns=["metric_id", "level", "p"])
    con.register("lp_df", lp)
    con.execute("CREATE TABLE lp AS SELECT * FROM lp_df")

    # coverage of the default period by canton (G), on the lowest level with values
    mem_all = membership()
    canton_n = mem_all.groupby("kanton").size()
    con.register("mem_kt2", mem_all[["bfs_nr", "kanton", "bezirk"]].astype(str))
    cg = con.execute("""SELECT m.metric_id, k.kanton,
                               COUNT(*) FILTER (WHERE m.status IN ('ok', 'suppressed', 'not_applicable')) AS n_cov,
                               COUNT(*) FILTER (WHERE m.status = 'ok') AS n_ok
                        FROM m JOIN lp ON m.metric_id = lp.metric_id AND m.level = lp.level AND m.period = lp.p
                        JOIN mem_kt2 k ON m.unit_id = k.bfs_nr
                        WHERE m.level = 'gemeinde' GROUP BY 1, 2""").df()
    cb = con.execute("""SELECT m.metric_id, k.kanton, COUNT(*) FILTER (WHERE m.status = 'ok') AS n_ok
                        FROM m JOIN lp ON m.metric_id = lp.metric_id AND m.level = lp.level AND m.period = lp.p
                        JOIN (SELECT DISTINCT bezirk, kanton FROM mem_kt2) k ON m.unit_id = k.bezirk
                        WHERE m.level = 'bezirk' GROUP BY 1, 2""").df()
    ck = con.execute("""SELECT m.metric_id, m.unit_id AS kanton FROM m JOIN lp ON m.metric_id = lp.metric_id
                        AND m.level = lp.level AND m.period = lp.p WHERE m.level = 'kanton' AND m.status = 'ok'""").df()
    covered = {}
    for mid, g in cg.groupby("metric_id"):
        share = g.set_index("kanton")["n_cov"] / canton_n.reindex(g["kanton"]).values
        covered[mid] = ("gemeinde", sorted(share[share >= CANTON_COVERED].index))
    for mid, g in cb.groupby("metric_id"):
        covered.setdefault(mid, ("bezirk", sorted(g.loc[g["n_ok"] > 0, "kanton"].unique())))
    for mid, g in ck.groupby("metric_id"):
        covered.setdefault(mid, ("kanton", sorted(g["kanton"].unique())))
    all_cantons = sorted(canton_n.index)

    rel_cfg = yaml.safe_load((SOURCES_DIR.parent / "reliability.yaml").read_text(encoding="utf-8")) or {}
    reliability = {mid: _reliability(mid, meta, rel_cfg) for mid in (rel_cfg.get("metrics") or {}) if mid in meta.index}
    reliability = {k: v for k, v in reliability.items() if v}
    i18n = load_i18n()
    majority = majority_by_year()
    vote_titles = load_vote_titles()

    per = con.execute("""SELECT metric_id, list(DISTINCT period) AS periods,
                                list(DISTINCT level) FILTER (WHERE status = 'ok') AS levels
                         FROM m GROUP BY 1""").df()
    hl = yaml.safe_load((SOURCES_DIR.parent / "headline_metrics.yaml").read_text(encoding="utf-8")) or {}
    headline_rank = {m: i for i, m in enumerate(x for v in (hl.get("headline") or {}).values() for x in v)}
    hidden = set(hl.get("hidden") or [])
    file_of = {}
    for mid in meta.index:
        file_of[mid] = "core" if mid in headline_rank else re.sub(r"[^a-z]+", "_", meta.loc[mid, "theme"].lower()).strip("_")
    lp_by = {(r.metric_id, r.level): r.p for r in lp.itertuples()}
    catalog = []
    all_levels = ["gemeinde", "bezirk", "kanton", *TYPOLOGY_COLS, "schweiz"]
    for r in per.itertuples():
        md = meta.loc[r.metric_id]
        periods = sorted(r.periods, key=_period_key)
        levels = sorted(r.levels) if r.levels is not None else []
        prim = next((l for l in all_levels if l in levels), None)
        dflt = lp_by.get((r.metric_id, prim), periods[-1])
        newest = max((avail[(r.metric_id, l)] for l in levels if (r.metric_id, l) in avail), key=_period_key,
                     default=periods[-1])
        cv_level, cv = covered.get(r.metric_id, (prim, []))
        coverage = "national" if set(all_cantons) <= set(cv) else ("partial:" + ",".join(cv) if cv else str(md["coverage"]))
        cnt = cov[(cov["metric_id"] == r.metric_id) & (cov["level"] == prim) & (cov["period"] == dflt)] if prim else cov.iloc[:0]
        lab = i18n.get(r.metric_id, {})
        unav = {l: _unavailable_reason(md, l, gap_mode.get((r.metric_id, l))) for l in all_levels
                if l not in levels and (l != "gemeinde" or md["native_level"] == "gemeinde")}
        entry = {
            "id": r.metric_id, "theme": md["theme"], "label_en": md["label_en"], "label_de": md["label_de"],
            "label_fr": lab.get("label_fr"), "unit": md["unit"], "unit_de": lab.get("unit_de"), "unit_fr": lab.get("unit_fr"),
            "decimals": int(md["decimals"]), "direction": md["direction"],
            "aggregation": md["aggregation"], "precision": md["precision"], "coverage": coverage,
            "coverage_meta": md["coverage"],
            "coverage_detail": {"level": cv_level, "period": dflt, "n": int(cnt["n_ok"].sum()) if len(cnt) else 0,
                                "of": int(n_units_level.get(prim, 0)) if prim else 0, "n_cantons": len(cv)},
            "source": md.get("credit_source") if isinstance(md.get("credit_source"), str) else md["source_id"],
            "description": md.get("description") if isinstance(md.get("description"), str) else None,
            "levels": levels,
            "n_periods": len(periods), "periods": periods if len(periods) <= 60 else periods[-60:],
            "latest": dflt, "latest_available": newest,
            "incomplete_periods": incomplete.get((r.metric_id, prim)) if prim else None,
            "unavailable_levels": unav or None,
            "reliability": reliability.get(r.metric_id),
            "pooled": _pooled_meta(md),
            "majority_cantons": majority if str(r.metric_id).startswith("nrw_") else None,
            "per_vote": str(r.metric_id).startswith("vote_"),
            "vote_index": "votes/index.json" if str(r.metric_id).startswith("vote_") else None,
            "latest_title": vote_titles.get(dflt) if str(r.metric_id).startswith("vote_") else None,
            "headline": headline_rank.get(r.metric_id), "hidden": r.metric_id in hidden,
            "file": file_of[r.metric_id],
        }
        catalog.append(entry)
    written["metrics"] = _dump(catalog, "metrics.json")
    written["glossary"] = build_glossary()

    # default period per metric and level (columnar)
    for lvl in [l[0] for l in con.execute("SELECT DISTINCT level FROM m").fetchall()]:
        g = con.execute(f"""SELECT m.unit_id, m.metric_id, m.period, m.value, m.status, m.precision,
                                   m.provenance, m.note
                            FROM m JOIN lp ON m.metric_id = lp.metric_id AND m.period = lp.p AND lp.level = '{lvl}'
                            WHERE m.level = '{lvl}'""").df()
        ids = sorted(g["unit_id"].unique(), key=lambda x: (len(x), x))
        idx = {u: i for i, u in enumerate(ids)}
        flags = unit_flags(con, lvl, g, idx, reliability, majority, meta)
        cols = {}
        for mid, gm in g.groupby("metric_id"):
            d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
            vals = [None] * len(ids)
            status, prec, notes = {}, {}, {}
            for u, v, st, pr, pv, nt in zip(gm["unit_id"], gm["value"], gm["status"], gm["precision"],
                                            gm["provenance"], gm["note"]):
                i = idx[u]
                vals[i] = _round(v, d)
                if st != "ok":
                    status[i] = STATUS_CODES.get(st, 1)
                if isinstance(pr, str) and pr != "exact":
                    prec[i] = PRECISION_CODES.get(pr, 0)
                if isinstance(nt, str) and (st != "ok" or OK_NOTE.search(nt)):
                    notes[i] = public_text(nt)
            col = {"period": gm["period"].iloc[0], "v": vals,
                   **({"s": status} if status else {}), **({"p": prec} if prec else {})}
            col.update(_notes_fields(notes))
            fl = flags.get(mid)
            if fl:
                col["f"] = {str(i): b for i, b in fl.items()}
            cols[mid] = col
        # D23: one core file (headline metrics) loaded at start, one file per theme on demand
        groups: dict[str, dict] = {}
        for mid, col in cols.items():
            groups.setdefault(file_of[mid], {})[mid] = col
        for fname, gcols in groups.items():
            written[f"latest_{lvl}_{fname}"] = _dump(
                {"level": lvl, "units": ids, "metrics": gcols, "status_codes": STATUS_CODES,
                 "precision_codes": PRECISION_CODES, "flag_bits": FLAG_BITS}, "latest", lvl, f"{fname}.json")

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
    # votes: one file per vote with yes share and turnout for every level, plus votes/index.json (B)
    from pipeline.build.votes import build_index
    vt = con.execute("""SELECT period, level, unit_id, metric_id, value FROM m
                        WHERE metric_id IN ('vote_yes_share', 'vote_turnout') AND status = 'ok'""").df()
    index = build_index(con, vote_titles)
    prov = {v["period"] for v in index["votes"] if v["provisional"]}
    n_votes = 0
    for per_, gv in vt.groupby("period"):
        vid = per_.replace("#", "_")
        out = {"period": per_, "title": vote_titles.get(per_), "provisional": per_ in prov, "levels": {}}
        for lvl_, gl in gv.groupby("level"):
            out["levels"][lvl_] = {mid: dict(zip(gm["unit_id"], [_round(v, 2) for v in gm["value"]]))
                                   for mid, gm in gl.groupby("metric_id")}
        _dump(out, "votes", f"{vid}.json")
        n_votes += 1
    written["votes_index"] = _dump(index, "votes", "index.json")
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
