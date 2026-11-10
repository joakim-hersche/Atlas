"""Files the static web app loads (brief 6.3; format to be confirmed at Checkpoint 3).

data/out/web/
  units.json                 every unit of every level: id, level, name, canton, district, parents, label point
  metrics.json               metric catalog: labels, unit, decimals, direction, theme, aggregation, precision,
                             coverage, source, levels available, periods
  latest/<level>.json        columnar latest-period values of all metrics for one level
  series/<metric_id>.json    all periods for municipalities, districts and cantons (loaded on demand)
  sources.json               per source: title, publisher, url, license, attribution, vintage, series breaks

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
from pipeline.build import series_breaks as sbreaks
from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.harmonize.schema import SOURCES_DIR, load_metrics

STATUS_CODES = {"ok": 0, "no_data": 1, "suppressed": 2, "not_published": 3, "not_covered": 4,
                "not_applicable": 5, "majority_election": 6}
# statuses that count as covered when choosing the default period (D37 rule 1, generic): the party did not
# stand / does not apply, a single-seat canton (value kept), a value suppressed for small numbers
COVERED = ("ok", "not_applicable", "majority_election", "suppressed")
PRECISION_CODES = {"exact": 0, "survey": 1, "modelled": 2, "boundary_estimate": 3}
SERIES_LEVELS = ("gemeinde", "bezirk", "kanton", "schweiz")
FLAG_BITS = {"small_base": 1, "small_count": 2, "majority_election": 4, "published_value": 8, "provisional": 16,
             "estimate": 32, "special": 64}
# estimate (M1): a sum leaving out a few suppressed municipalities (<= 1 % of residents);
# special (M9): a value distorted by how the source counts (e.g. company fleets registered in one place)
COVERAGE_MIN = 0.95          # default period: step back over newer periods with < 95 % of the previous one (F)
CANTON_COVERED = 0.5         # a canton counts as covered when >= 50 % of its municipalities have data (G)
TYPOLOGY_COLS = {"grossregion": "REGCH", "sprachgebiet": "SPRGEB2020", "agglomeration": "AGGL2020",
                 "arbeitsmarktgebiet": "BAE2018", "stadt_land": "STALAN2020", "gemeindetyp": "GDETYP2020_9"}
LEVEL_WORD = {"gemeinde": "municipality", "bezirk": "district", "kanton": "canton", "schweiz": "national",
              "arbeitsmarktgebiet": "labour-market area", "agglomeration": "agglomeration", "grossregion": "major region",
              "sprachgebiet": "language region", "stadt_land": "urban/rural", "gemeindetyp": "municipality type"}
# notes of ok values worth showing (fallback provenance, provisional results, reach details)
OK_NOTE = re.compile(r"published|provisional|no arrival|nearest hub|computed from published|proportional-representation|"
                     r"single-seat|counted under FDP|estimate|not allocatable|boundaries of|today's boundaries|"
                     r"demographic balance|series break", re.I)
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


def fmtp(p: str) -> str:
    """Period for notes: a vote period 'YYYY-MM-DD#id' without its internal id."""
    return str(p).split("#")[0]


# typos in the BFS register's labels (round-2 audit): corrected on output, the cached source is unchanged
LABEL_FIXES = [(re.compile(r"agglomertation"), "agglomeration")]


def fix_label(v):
    if not isinstance(v, str):
        return v
    for rx, rep in LABEL_FIXES:
        v = rx.sub(rep, v)
    return v


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
        names_of[lvl] = {k: {l: fix_label(r[f"{col}_{l}"]) for l in langs if isinstance(r[f"{col}_{l}"], str) and r[f"{col}_{l}"].strip()}
                         for k, r in g.iterrows()}
    for lvl in ("bezirk", "kanton", "grossregion", "sprachgebiet", "agglomeration", "arbeitsmarktgebiet",
                "stadt_land", "gemeindetyp"):
        if lvl not in m.columns:
            continue
        name_col = f"{lvl}_name" if f"{lvl}_name" in m.columns else None
        for uid, g in m.dropna(subset=[lvl]).groupby(lvl):
            name = fix_label(g[name_col].iloc[0]) if name_col else uid
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
UNIT_PLURAL_FR = {"gemeinde": "communes", "bezirk": "districts", "kanton": "cantons"}
STATUS_REASON = {"suppressed": "values suppressed (small numbers)", "not_published": "not published at this level",
                 "not_covered": "not covered", "not_applicable": "not applicable", "no_data": "no data"}


def default_period(counts: list[tuple[str, int]], per_vote: bool = False) -> str:
    """Default ('latest') period (review round 1, defect 8): starting from the newest period, step back
    while a period has fewer than COVERAGE_MIN (95 %) of the units of the period before it.
    counts: (period, n_covered) for periods with at least one value; covered = a status in COVERED, so a
    party that did not stand or a single-seat canton does not make an election look incomplete (D37).
    Per-vote metrics: the newest vote. The period is chosen once per metric, on its primary level
    (primary_level), and used at every level (D37 / all-data audit: no level silently shows an older year)."""
    c = sorted(counts, key=lambda x: _period_key(x[0]))
    if per_vote:
        return c[-1][0]
    i = len(c) - 1
    # step back while a period has clearly fewer units than the one before it (an incomplete newer
    # round, e.g. Arealstatistik 2020/25: 1,007 vs 2,110); a steadily small partial metric stays put
    while i > 0 and c[i][1] < COVERAGE_MIN * c[i - 1][1]:
        i -= 1
    return c[i][0]


LEVEL_ORDER = ["gemeinde", "bezirk", "kanton", *TYPOLOGY_COLS, "schweiz"]


def primary_level(native: str, levels_with_values: list[str]) -> str | None:
    """Level whose coverage decides a metric's default period: its native level if it has values there,
    else the lowest level with values (municipality first)."""
    if native in levels_with_values:
        return native
    return next((l for l in LEVEL_ORDER if l in levels_with_values), None)


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


# Denominators that are the same stock at two dates, averaged by the formula's factor (BFS mean population
# = (1 January + 31 December) / 2, written 'bil_pop_jan+bil_pop_dec*2000'): their base is the mean of the
# terms, written 'mean:<a>+<b>', so the 1,000-resident threshold means residents, not twice the residents.
MEAN_DENOMINATORS = [["bil_pop_jan", "bil_pop_dec"]]


def base_expr(terms: list[str]) -> str:
    """Small-number base of a ratio: the sum of all its denominator terms ('a+b'), or 'mean:a+b' where the
    terms are one stock at two dates (MEAN_DENOMINATORS)."""
    terms = [t for t in terms if t]
    if len(terms) > 1 and sorted(terms) in [sorted(m) for m in MEAN_DENOMINATORS]:
        return "mean:" + "+".join(terms)
    return "+".join(terms)


NOT_COUNTS = re.compile(r"\bha\b|m²|m2|km|chf|wh\b|kw|tonne|\bt\b|%|minutes|min\b|metres|\bm\b|°|mm|index", re.I)


def _auto_rule(mid: str, meta: pd.DataFrame, cfg: dict) -> dict | None:
    """Generic small-number rule (audit round 2, M9) for a ratio not listed in reliability.yaml `metrics`:
    shares get a minimum base of `auto.share_min_base`, other ratios `auto.rate_min_base` (per-resident
    rates) or `auto.mean_min_base` (means per taxpayer, household, dwelling ...). Denominators that are
    not counts of people or things (areas, money, energy) get no rule: those ratios are exact.
    The base is the whole denominator, every term (review round 3, D1: the yes share's base is yes + no
    votes, not the yes votes alone); see base_expr for denominators that average two dates."""
    a = cfg.get("auto") or {}
    if not a or mid not in meta.index or meta.loc[mid, "kind"] != "derived":
        return None
    f = _formula(str(meta.loc[mid, "aggregation"]))
    if not f or f[2] != 1 or str(meta.loc[mid, "native_level"]) != "gemeinde":
        return None
    terms = f[1]
    if any(t not in meta.index or NOT_COUNTS.search(str(meta.loc[t, "unit"])) for t in terms):
        return None
    den = base_expr(terms)
    unit = str(meta.loc[mid, "unit"])
    if unit.strip().startswith("%") or "share" in unit.lower():
        kind = "share"
    elif re.search(r"per (1[,' ]?000|100|10[,' ]?000)\b|per resident|per capita|per inhabitant", unit, re.I) or terms == ["pop_total"]:
        kind = "rate"
    else:
        kind = "mean"
    k = a.get(kind) or {}
    if not k:
        return None
    return {"count": None, "base": den, "min_count": None, "min_base": k["min_base"], "years": 1, "auto": kind,
            **{x: k.get(x) for x in ("rule_en", "rule_de", "rule_fr")}}


def _special(mid: str, cfg: dict) -> dict | None:
    """Plausibility cap (M9): values above `max` are flagged 'special' with the metric's explanation."""
    o = (cfg.get("metrics") or {}).get(mid) or {}
    s = o.get("special")
    return dict(s) if isinstance(s, dict) and "max" in s else None


def _reliability(mid: str, meta: pd.DataFrame, cfg: dict) -> dict | None:
    """Small-number rule of one metric (pipeline/reliability.yaml, D32)."""
    d = cfg.get("defaults") or {}
    o = (cfg.get("metrics") or {}).get(mid) or {}
    if o.get("count", 1) is None and o.get("base", 1) is None:
        return None
    f = _formula(str(meta.loc[mid, "aggregation"]))
    count = o["count"] if "count" in o else ("+".join(f[0]) if f else None)
    base = o.get("base") or (base_expr(f[1]) if f else None)
    if not count and not base:
        return None
    # per-metric thresholds and wording override the defaults (e.g. elections: valid ballots)
    return {"count": count, "base": base, "min_count": o.get("min_count", d.get("min_count", 20)) if count else None,
            "min_base": o.get("min_base", d.get("min_base", 1000)) if base else None,
            "years": f[2] if f else 1, **{k: o.get(k, d.get(k)) for k in ("rule_en", "rule_de", "rule_fr")}}


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
    return {k: {f: v.get(f) for f in ("label_fr", "unit_de", "unit_fr", "description_de", "description_fr") if isinstance(v, dict)}
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


def _unavailable_reason(md, level: str, gap_status: str | None, input_status: str | None = None) -> str:
    """Why a metric has no values at a level (D: the real reason, not 'no data for this year')."""
    if isinstance(md.get("unavailable_note"), str) and level not in ("gemeinde",):
        return md["unavailable_note"]
    nat = str(md["native_level"])
    word = LEVEL_WORD.get(nat, nat)
    survey = " (survey)" if md["precision"] == "survey" else ""
    if nat != "gemeinde" and level != nat:
        return f"published only at {word} level{survey}"
    if md["aggregation"] == "not_aggregatable":
        return "cannot be aggregated; no published value at this level"
    if gap_status:
        return "incomplete at this level: " + STATUS_REASON.get(gap_status, gap_status) + " for some municipalities"
    if input_status:
        return "incomplete at this level: " + STATUS_REASON.get(input_status, input_status) + " for some municipalities"
    return "no data at this level"


def _notes_fields(notes: dict) -> dict:
    """{index: text} -> {'notes': [...], 'n': {index: k}} with repeated texts stored once."""
    if not notes:
        return {}
    texts = sorted(set(notes.values()))
    k = {t: i for i, t in enumerate(texts)}
    return {"notes": texts, "n": {str(i): k[t] for i, t in notes.items()}}


def majority_metric_ids(meta: pd.DataFrame) -> set:
    col = meta["majority_election"] if "majority_election" in meta else pd.Series(dtype=object)
    return set(col[col.fillna(False).astype(bool)].index)


def majority_rows(g: pd.DataFrame, lvl: str, majority: dict, meta: pd.DataFrame):
    """(metric, unit, period) of rows in single-seat canton-years for metrics with majority_election."""
    if not majority or lvl not in ("gemeinde", "bezirk", "kanton"):
        return []
    ids = majority_metric_ids(meta)
    mem = membership()
    kt_of = (dict(zip(mem["bfs_nr"].astype(str), mem["kanton"])) if lvl == "gemeinde" else
             dict(zip(mem["bezirk"].astype(str), mem["kanton"])) if lvl == "bezirk" else None)
    sub = g[g["metric_id"].isin(ids)]
    out = []
    for mid, u, per in zip(sub["metric_id"], sub["unit_id"], sub["period"]):
        kt = u if kt_of is None else kt_of.get(u)
        if kt in set(majority.get(str(per)[:4], [])):
            out.append((mid, u, per))
    return out


def unit_flags(con, lvl: str, g: pd.DataFrame, idx: dict, reliability: dict, majority: dict,
               meta: pd.DataFrame, special: dict | None = None) -> dict:
    """Per metric: {unit index: bitmask} (FLAG_BITS) for one level's default-period columns."""
    out: dict[str, dict] = {}
    for mid, sp in (special or {}).items():
        gm = g[(g["metric_id"] == mid) & (g["status"] == "ok") & (g["value"] > float(sp["max"]))]
        for u in gm["unit_id"]:
            out.setdefault(mid, {})
            out[mid][idx[u]] = out[mid].get(idx[u], 0) | FLAG_BITS["special"]

    def add(mid, i, bit):
        out.setdefault(mid, {})
        out[mid][i] = out[mid].get(i, 0) | bit
    # published value used (fallback) and provisional results
    for mid, u, pv, nt, st in zip(g["metric_id"], g["unit_id"], g["provenance"], g["note"], g["status"]):
        if st != "ok":
            continue
        # (a published total preferred over a complete sum, D7, is no fallback: its note says what it is)
        if lvl != "gemeinde" and ((pv == "native" and str(meta.loc[mid, "aggregation"]) != "not_aggregatable"
                                   and str(meta.loc[mid, "native_level"]) == "gemeinde"
                                   and not (isinstance(nt, str) and nt.startswith("published total")))
                                  or (isinstance(nt, str) and nt.startswith("computed from published"))):
            add(mid, idx[u], FLAG_BITS["published_value"])
        if isinstance(nt, str) and "provisional" in nt:
            add(mid, idx[u], FLAG_BITS["provisional"])
        if isinstance(nt, str) and nt.startswith("estimate"):
            add(mid, idx[u], FLAG_BITS["estimate"])
    # majority-election cantons (D37): every row of a party share / bloc / leaning metric in a single-seat
    # canton-year, whatever its status (also "party did not stand"); turnout is not affected
    for mid, u, per in majority_rows(g, lvl, majority, meta):
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
            mean = expr.startswith("mean:")
            ids = expr.removeprefix("mean:").split("+")
            v = con.execute(f"""SELECT unit_id, SUM(value) / {len(ids) if mean else 1} AS v, COUNT(DISTINCT period) AS ny FROM m
                                WHERE level = '{lvl}' AND status = 'ok' AND metric_id IN ({", ".join("'" + i + "'" for i in ids)})
                                  AND period IN ({", ".join("'" + y + "'" for y in years)})
                                GROUP BY 1""").df()
            # per-unit sum over the terms and years
            shown = set(gm["unit_id"])
            for u in v.loc[v["v"] < lim, "unit_id"]:
                if u in idx and u in shown:
                    add(mid, idx[u], FLAG_BITS[bit])
    return out


def curation_coverage(con, mem: pd.DataFrame) -> dict:
    """(metric, level) -> (units covered, units of the level, share of residents covered) at the metric's
    default period (table lp); residents = STATPOP pop_total of its newest period, summed per unit."""
    pop = con.execute("""SELECT unit_id, value FROM m WHERE metric_id = 'pop_total' AND level = 'gemeinde'
                         AND status = 'ok' AND period = (SELECT max(period) FROM m WHERE metric_id = 'pop_total'
                                                         AND level = 'gemeinde' AND status = 'ok')""").df()
    pmap = dict(zip(pop["unit_id"].astype(str), pop["value"]))
    mm = mem.assign(gemeinde=mem["bfs_nr"].astype(str), pop=mem["bfs_nr"].astype(str).map(pmap).fillna(0))
    rows = []
    for lvl in ["gemeinde", "bezirk", "kanton", *TYPOLOGY_COLS]:
        if lvl not in mm.columns:
            continue
        g = mm.dropna(subset=[lvl]).groupby(mm[lvl].astype(str))["pop"].sum()
        rows += [(lvl, u, float(v)) for u, v in g.items()]
    con.register("upop_df", pd.DataFrame(rows, columns=["level", "unit_id", "pop"]))
    tot = pd.DataFrame(rows, columns=["level", "unit_id", "pop"]).groupby("level").agg(n=("unit_id", "size"), p=("pop", "sum"))
    c = con.execute("""SELECT m.metric_id, m.level, COUNT(DISTINCT m.unit_id) AS n, SUM(u.pop) AS p
                       FROM m JOIN lp ON m.metric_id = lp.metric_id AND m.level = lp.level AND m.period = lp.p
                       JOIN upop_df u ON u.level = m.level AND u.unit_id = m.unit_id
                       WHERE m.status IN ('ok', 'majority_election', 'not_applicable')
                       GROUP BY 1, 2""").df()
    out = {}
    for mid, lvl, n, p_ in zip(c["metric_id"], c["level"], c["n"], c["p"]):
        if lvl in tot.index:
            out[(mid, lvl)] = (int(n), int(tot.loc[lvl, "n"]), float(p_ or 0) / float(tot.loc[lvl, "p"] or 1))
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
    brk_cfg = sbreaks.load()
    brk_err = sbreaks.validate(brk_cfg, set(meta.index), set(srcs))
    if brk_err:
        raise ValueError("pipeline/series_breaks.yaml: " + "; ".join(brk_err))
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
                                                   "attribution", "vintage", "years", "status_note")}
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
    cov_in = ", ".join(f"'{x}'" for x in COVERED)
    cov = con.execute(f"""SELECT metric_id, level, period, COUNT(*) FILTER (WHERE status = 'ok') AS n_ok,
                                 COUNT(*) FILTER (WHERE status IN ({cov_in})) AS n_cov,
                                 COUNT(*) AS n_rows, mode(status) FILTER (WHERE status <> 'ok') AS gap_status
                          FROM m GROUP BY 1, 2, 3""").df()
    cov["key"] = cov["period"].map(_period_key)
    n_units_level = pd.Series({lvl: n for lvl, n in membership_counts().items()})
    incomplete, avail, gap_mode, okp = {}, {}, {}, {}
    for (mid, lvl), g in cov.groupby(["metric_id", "level"], sort=False):
        g = g.sort_values("key")
        ok = g[g["n_ok"] > 0]
        if ok.empty:
            gap_mode[(mid, lvl)] = g["gap_status"].mode().iloc[0] if g["gap_status"].notna().any() else "no_data"
            continue
        okp[(mid, lvl)] = ok
        avail[(mid, lvl)] = ok["period"].iloc[-1]
    # one default period per metric (D37 rule 1, generalised after the all-data audit): chosen on the
    # metric's primary level and used at every level; a level without a value for it shows the gap
    lp_rows, dflt_of, prim_of, before = [], {}, {}, {}
    levels_of: dict[str, list[str]] = {}
    for (mid, lvl) in okp:
        levels_of.setdefault(mid, []).append(lvl)
    for mid, lvls in levels_of.items():
        prim = primary_level(str(meta.loc[mid, "native_level"]) if mid in meta.index else "gemeinde", lvls)
        ok = okp[(mid, prim)]
        dflt = default_period(list(zip(ok["period"], ok["n_cov"])), str(mid).startswith("vote_"))
        dflt_of[mid], prim_of[mid] = dflt, prim
        newer = ok[ok["key"] > _period_key(dflt)]
        if len(newer):
            of = int(n_units_level.get(prim, ok["n_ok"].max()))
            incomplete[(mid, prim)] = {p: {"n": int(n), "of": of, "level": prim,
                                           "label_en": f"incomplete: {n:,} of {of:,} {UNIT_PLURAL_EN.get(prim, 'units')}",
                                           "label_de": f"unvollständig: {n:,} von {of:,} {UNIT_PLURAL_DE.get(prim, 'Einheiten')}".replace(",", "'"),
                                           "label_fr": f"incomplet : {n:,} sur {of:,} {UNIT_PLURAL_FR.get(prim, 'unités')}".replace(",", "\u202f")}
                                       for p, n in zip(newer["period"], newer["n_ok"])}
        for lvl in lvls:
            lp_rows.append((mid, lvl, dflt))
            o = okp[(mid, lvl)]
            before[(mid, lvl)] = default_period(list(zip(o["period"], o["n_ok"])), str(mid).startswith("vote_"))
    lp = pd.DataFrame(lp_rows, columns=["metric_id", "level", "p"])
    # audit numbers: metric × level defaults that are not the newest period with values at that level
    n_old = sum(1 for k, v in before.items() if v != avail[k])
    n_new = sum(1 for (mid, lvl) in before if dflt_of[mid] != avail[(mid, lvl)])
    n_mixed_old = sum(1 for mid, lvls in levels_of.items() if len({before[(mid, l)] for l in lvls}) > 1)
    written_stats = {"metric_levels": len(before), "default_not_newest_before": n_old, "default_not_newest_after": n_new,
                     "metrics_with_mixed_defaults_before": n_mixed_old, "metrics_with_mixed_defaults_after": 0,
                     "after_details": sorted(f"{mid}@{lvl}: {dflt_of[mid]} (newest there {avail[(mid, lvl)]})"
                                             for (mid, lvl) in before if dflt_of[mid] != avail[(mid, lvl)])}
    print("default periods:", {k: v for k, v in written_stats.items() if k != "after_details"})
    con.register("lp_df", lp)
    con.execute("CREATE TABLE lp AS SELECT * FROM lp_df")

    # coverage of the default period by canton (G), on the lowest level with values
    mem_all = membership()
    canton_n = mem_all.groupby("kanton").size()
    con.register("mem_kt2", mem_all[["bfs_nr", "kanton", "bezirk"]].astype(str))
    cg = con.execute("""SELECT m.metric_id, k.kanton,
                               COUNT(*) FILTER (WHERE m.status IN ('ok', 'suppressed', 'not_applicable', 'majority_election')) AS n_cov,
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
    n_listed = len(reliability)
    for mid in meta.index:   # M9: every other ratio gets the generic denominator rule
        if mid not in reliability and mid not in (rel_cfg.get("metrics") or {}):
            r_ = _auto_rule(mid, meta, rel_cfg)
            if r_:
                reliability[mid] = r_
    special = {mid: sp for mid in meta.index if (sp := _special(mid, rel_cfg))}
    print(f"small-number rules: {n_listed} listed, {len(reliability) - n_listed} generic; special caps: {len(special)}")
    i18n = load_i18n()
    majority = majority_by_year()
    maj_ids = majority_metric_ids(meta)
    vote_titles = load_vote_titles()

    per = con.execute("""SELECT metric_id, list(DISTINCT period) AS periods,
                                list(DISTINCT level) FILTER (WHERE status = 'ok') AS levels
                         FROM m GROUP BY 1""").df()
    # series breaks (pipeline/series_breaks.yaml): placed on each metric's periods, plus the publisher
    # breaks the connectors note on the values (from_note rules)
    note_rows = []
    for e in brk_cfg.get("breaks") or []:
        if e.get("from_note"):
            note_rows += con.execute("""SELECT metric_id, period, any_value(note) FROM m
                                         WHERE note IS NOT NULL AND regexp_matches(note, ?) GROUP BY 1, 2""",
                                     [e["from_note"]["regex"]]).fetchall()
    brk_of, brk_rows = sbreaks.resolve(brk_cfg, meta, {r.metric_id: sorted(r.periods, key=_period_key)
                                                       for r in per.itertuples()}, note_rows)
    print(f"series breaks: {sum(len(v) for v in brk_of.values())} markers on {len(brk_of)} metrics")
    hl = yaml.safe_load((SOURCES_DIR.parent / "headline_metrics.yaml").read_text(encoding="utf-8")) or {}
    headline_rank = {m: i for i, m in enumerate(x for v in (hl.get("headline") or {}).values() for x in v)}
    hidden = set(hl.get("hidden") or [])
    file_of = {}
    for mid in meta.index:
        file_of[mid] = "core" if mid in headline_rank else re.sub(r"[^a-z]+", "_", meta.loc[mid, "theme"].lower()).strip("_")
    lp_by = {(r.metric_id, r.level): r.p for r in lp.itertuples()}
    # D38 curation: coverage of each metric × level at its default period (units with a value, a
    # single-seat canton value or a defined 'does not apply'; and their share of residents)
    from pipeline.build import curation as cur_mod
    cur_cfg = cur_mod.load()
    cur_cov = curation_coverage(con, mem_all)
    # precision of the values actually shown (round 2: social assistance 2024/25 is modelled by BFS
    # weighting, so card and statistics must say the same); boundary estimates do not change the label
    prec_shown = dict(con.execute("""SELECT m.metric_id, mode(m.precision) FROM m JOIN lp ON m.metric_id = lp.metric_id
                                     AND m.level = lp.level AND m.period = lp.p
                                     WHERE m.status = 'ok' AND m.precision <> 'boundary_estimate' GROUP BY 1""").fetchall())
    cur_rows = []
    catalog = []
    all_levels = ["gemeinde", "bezirk", "kanton", *TYPOLOGY_COLS, "schweiz"]
    for r in per.itertuples():
        md = meta.loc[r.metric_id]
        periods = sorted(r.periods, key=_period_key)
        levels = sorted(r.levels) if r.levels is not None else []
        prim = prim_of.get(r.metric_id) or next((l for l in all_levels if l in levels), None)
        dflt = dflt_of.get(r.metric_id, periods[-1])
        newest = max((avail[(r.metric_id, l)] for l in levels if (r.metric_id, l) in avail), key=_period_key,
                     default=periods[-1])
        cv_level, cv = covered.get(r.metric_id, (prim, []))
        coverage = "national" if set(all_cantons) <= set(cv) else ("partial:" + ",".join(cv) if cv else str(md["coverage"]))
        cnt = cov[(cov["metric_id"] == r.metric_id) & (cov["level"] == prim) & (cov["period"] == dflt)] if prim else cov.iloc[:0]
        lab = i18n.get(r.metric_id, {})
        f_ = _formula(str(md["aggregation"])) if md["kind"] == "derived" else None
        unav = {l: _unavailable_reason(md, l, gap_mode.get((r.metric_id, l)),
                                       next((gap_mode[(t, l)] for t in (f_[0] if f_ else []) if (t, l) in gap_mode), None))
                for l in all_levels
                if l not in levels and (l != "gemeinde" or md["native_level"] == "gemeinde")}
        entry = {
            "id": r.metric_id, "theme": md["theme"], "label_en": md["label_en"], "label_de": md["label_de"],
            "label_fr": lab.get("label_fr"), "unit": md["unit"], "unit_de": lab.get("unit_de"), "unit_fr": lab.get("unit_fr"),
            "description_de": lab.get("description_de"), "description_fr": lab.get("description_fr"),
            "decimals": int(md["decimals"]), "direction": md["direction"],
            "aggregation": md["aggregation"], "precision": prec_shown.get(r.metric_id, md["precision"]), "coverage": coverage,
            "native_level": md["native_level"],
            "coverage_meta": md["coverage"],
            "coverage_detail": {"level": cv_level, "period": dflt, "n": int(cnt["n_ok"].sum()) if len(cnt) else 0,
                                "of": int(n_units_level.get(prim, 0)) if prim else 0, "n_cantons": len(cv)},
            "source": md.get("credit_source") if isinstance(md.get("credit_source"), str) else md["source_id"],
            "description": md.get("description") if isinstance(md.get("description"), str) else None,
            "levels": levels,
            "n_periods": len(periods), "periods": periods if len(periods) <= 60 else periods[-60:],
            "latest": dflt, "latest_available": newest,
            "incomplete_periods": incomplete.get((r.metric_id, prim)) if prim else None,
            # period -> {label_en, label_de, label_fr}: change of method or definition from this period on
            "series_breaks": {p: v for p, v in sorted((brk_of.get(r.metric_id) or {}).items(), key=lambda x: _period_key(x[0]))
                              if p in periods[-60:][1:]} or None,
            "unavailable_levels": unav or None,
            "reliability": reliability.get(r.metric_id),
            "special": special.get(r.metric_id),
            "pooled": _pooled_meta(md),
            "majority_cantons": majority if r.metric_id in maj_ids else None,
            "keywords": md.get("keywords") if isinstance(md.get("keywords"), str) else None,
            "until": int(md["until"]) if "until" in md and pd.notna(md.get("until")) else None,
            "per_vote": str(r.metric_id).startswith("vote_"),
            "vote_index": "votes/index.json" if str(r.metric_id).startswith("vote_") else None,
            "latest_title": vote_titles.get(dflt) if str(r.metric_id).startswith("vote_") else None,
            "headline": headline_rank.get(r.metric_id), "hidden": r.metric_id in hidden,
            "file": file_of[r.metric_id],
        }
        verdicts = {}
        for lvl in levels:
            if lvl in cur_mod.NEVER_CURATED:
                continue
            n_cov, n_all, pshare = cur_cov.get((r.metric_id, lvl), (0, int(n_units_level.get(lvl, 0)), 0.0))
            verdicts[lvl] = cur_mod.decide(r.metric_id, lvl, n_cov, n_all, pshare, cur_cfg)
            cur_rows.append((r.metric_id, md["theme"], lvl, n_cov, n_all, round(pshare, 4), *verdicts[lvl]))
        cur_mod.apply(entry, verdicts, levels)
        catalog.append(entry)
    cur_df = pd.DataFrame(cur_rows, columns=["metric_id", "theme", "level", "n", "n_units", "pop_share",
                                             "verdict", "reason", "basis"])
    cur_df.to_csv(interim_path("curation_verdicts.csv"), index=False)
    print("D38 curation:", cur_df.groupby("verdict").size().to_dict())
    written["featured"] = _dump({"note": "featured story maps (D38, pipeline/curation.yaml)",
                                 "maps": cur_mod.featured(cur_cfg, catalog)}, "featured.json")
    written["metrics"] = _dump(catalog, "metrics.json")
    # series breaks per source for the Sources page (only metrics that ship and are offered in the pickers)
    shipped_ids = {e["id"] for e in catalog if e.get("series_breaks") and not e.get("hidden")}
    for row in src_rows:
        rows = [{k: b.get(k) for k in ("period", "label_en", "label_de", "label_fr", "cantons", "evidence")}
                | {"metrics": [m for m in b["metrics"] if m in shipped_ids]}
                for b in brk_rows if b["source"] == row["source_id"]]
        rows = [b for b in rows if b["metrics"]]
        row["series_breaks"] = sorted(rows, key=lambda b: _period_key(b["period"])) or None
    written["sources"] = _dump(src_rows, "sources.json")
    written["glossary"] = build_glossary()

    # default period per metric and level (columnar)
    for lvl in [l[0] for l in con.execute("SELECT DISTINCT level FROM m").fetchall()]:
        g = con.execute(f"""SELECT m.unit_id, m.metric_id, m.period, m.value, m.status, m.precision,
                                   m.provenance, m.note
                            FROM m JOIN lp ON m.metric_id = lp.metric_id AND m.period = lp.p AND lp.level = '{lvl}'
                            WHERE m.level = '{lvl}'""").df()
        ids = sorted(g["unit_id"].unique(), key=lambda x: (len(x), x))
        idx = {u: i for i, u in enumerate(ids)}
        flags = unit_flags(con, lvl, g, idx, reliability, majority, meta, special)
        cols = {}
        for mid, gm in g.groupby("metric_id"):
            d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
            vals = [None] * len(ids)
            status, prec, notes, maj = {}, {}, {}, {}
            for u, v, st, pr, pv, nt in zip(gm["unit_id"], gm["value"], gm["status"], gm["precision"],
                                            gm["provenance"], gm["note"]):
                i = idx[u]
                if st == "majority_election":   # D37: value kept apart, so it is in no class, rank or statistic
                    if _round(v, d) is not None:
                        maj[str(i)] = _round(v, d)
                else:
                    vals[i] = _round(v, d)
                if st != "ok":
                    status[i] = STATUS_CODES.get(st, 1)
                if isinstance(pr, str) and pr != "exact":
                    prec[i] = PRECISION_CODES.get(pr, 0)
                if isinstance(nt, str) and (st != "ok" or OK_NOTE.search(nt)):
                    notes[i] = public_text(nt)
            col = {"period": gm["period"].iloc[0], "v": vals,
                   **({"s": status} if status else {}), **({"p": prec} if prec else {}), **({"m": maj} if maj else {})}
            col.update(_notes_fields(notes))
            fl = flags.get(mid)
            if fl:
                col["f"] = {str(i): b for i, b in fl.items()}
            cols[mid] = col
        # a level with values in other periods but none for the metric's default period: an explicit gap
        for mid in lp.loc[(lp["level"] == lvl) & ~lp["metric_id"].isin(list(cols)), "metric_id"]:
            nt = public_text(f"no value for {fmtp(dflt_of[mid])} at this level (newest here: {fmtp(avail[(mid, lvl)])})")
            cols[mid] = {"period": dflt_of[mid], "v": [None] * len(ids), "s": {str(i): STATUS_CODES["no_data"] for i in range(len(ids))},
                         "notes": [nt], "n": {str(i): 0 for i in range(len(ids))}}
        # D23: one core file (headline metrics) loaded at start, one file per theme on demand
        groups: dict[str, dict] = {}
        for mid, col in cols.items():
            groups.setdefault(file_of[mid], {})[mid] = col
        for fname, gcols in groups.items():
            written[f"latest_{lvl}_{fname}"] = _dump(
                {"level": lvl, "units": ids, "metrics": gcols, "status_codes": STATUS_CODES,
                 "precision_codes": PRECISION_CODES, "flag_bits": FLAG_BITS}, "latest", lvl, f"{fname}.json")

    _dump(written_stats, "default_periods.json")
    # time series per metric (municipality, district, canton, Switzerland); votes get one file per vote.
    # D37: party shares / blocs / leaning carry the single-seat cantons apart: value null in `levels`, the
    # value in `m` {level: {unit: {period index: value}}} and the flag in `f` {level: {unit: {index: bits}}}
    lv = ", ".join(f"'{x}'" for x in SERIES_LEVELS)
    n_series = 0
    for (mid,) in con.execute("SELECT DISTINCT metric_id FROM m").fetchall():
        if str(mid).startswith("vote_"):
            continue
        g = con.execute(f"SELECT level, unit_id, period, value, status FROM m WHERE metric_id = ? AND level IN ({lv})",
                        [mid]).df()
        periods = sorted(g["period"].unique(), key=_period_key)
        if len(periods) < 2:
            continue
        pidx = {p: i for i, p in enumerate(periods)}
        d = int(meta.loc[mid, "decimals"]) + (1 if str(meta.loc[mid, "unit"]).strip() == "%" else 0)
        out = {"metric": mid, "periods": periods, "levels": {}}
        mset = mid in maj_ids
        for lvl_, gl in g.groupby("level"):
            series = {}
            mv: dict = {}
            for uid, gu in gl.groupby("unit_id"):
                row = [None] * len(periods)
                for p, v, st in zip(gu["period"], gu["value"], gu["status"]):
                    if st == "majority_election":
                        if _round(v, d) is not None:
                            mv.setdefault(uid, {})[str(pidx[p])] = _round(v, d)
                    else:
                        row[pidx[p]] = _round(v, d)
                series[uid] = row
            out["levels"][lvl_] = series
            if mset:
                if mv:
                    out.setdefault("m", {})[lvl_] = mv
                fl: dict = {}
                for _, u, per in majority_rows(gl.assign(metric_id=mid), lvl_, majority, meta):
                    fl.setdefault(u, {})[str(pidx[per])] = FLAG_BITS["majority_election"]
                if fl:
                    out.setdefault("f", {})[lvl_] = fl
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
