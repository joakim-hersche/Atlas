"""Helpers shared by the cantonal `*` connectors (kt_finance, kt_hazards, kt_pupils, kt_landprice,
kt_unemployment, kt_crime). Kept inside this source directory so shared modules stay untouched.

- fetch_retry():   pipeline.common.fetch with extra rounds for flaky hosts (Opendatasoft portals
                   drop the TLS tunnel right after the ClientHello from this machine).
- ods_csv():       full CSV export of an Opendatasoft dataset (one request, cached).
- zh_indicator():  one ZH Gemeindeporträt OGD indicator file (KANTON_ZUERICH_<id>.csv).
- canton_vintage(): municipality state of a cantonal file, inferred from the BFS numbers of that
                   canton only (the national infer_vintage would compare against all 2,110).
- to_ref():        per canton × period reprojection to the reference state (via
                   estv_dbst.refhelp.per_period_to_reference: suppression propagates, ratios are
                   kept only where the mapping is 1:1).
- complete():      adds a row for every reference municipality × metric × period:
                   `not_covered` (canton without a source, note names the reason) or `no_data`
                   (canton covered but no value for that municipality/period). Never a number.
"""
from __future__ import annotations

import datetime as dt
import time
from functools import lru_cache

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE, fetch
from pipeline.harmonize.helpers import _candidate_dates
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.estv_dbst.refhelp import native_rows, per_period_to_reference  # noqa: F401

CANTONS = ["ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR",
           "AI", "SG", "GR", "AG", "TG", "TI", "VD", "VS", "NE", "GE", "JU"]


def fetch_retry(url: str, source_id: str, filename: str, *, params: dict | None = None,
                rounds: int = 6, timeout: int = 600):
    last = None
    for i in range(rounds):
        try:
            return fetch(url, source_id, filename, params=params, timeout=timeout, retries=3)
        except RuntimeError as e:  # fetch gave up after its own retries
            last = e
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"{url}: still failing after {rounds} rounds") from last


def ods_csv(host: str, dataset: str, source_id: str, *, where: str | None = None,
            select: str | None = None, filename: str | None = None) -> pd.DataFrame:
    """Full CSV export of an Opendatasoft (explore v2.1) dataset, ';'-separated."""
    params = {"delimiter": ";", "use_labels": "false"}
    if where:
        params["where"] = where
    if select:
        params["select"] = select
    url = f"https://{host}/api/explore/v2.1/catalog/datasets/{dataset}/exports/csv"
    p = fetch_retry(url, source_id, filename or f"{host.split('.')[1]}_{dataset}.csv", params=params)
    return pd.read_csv(p, sep=";", low_memory=False)


def ods_meta(host: str, dataset: str, source_id: str) -> dict:
    import json
    p = fetch_retry(f"https://{host}/api/explore/v2.1/catalog/datasets/{dataset}", source_id,
                    f"{host.split('.')[1]}_{dataset}_meta.json")
    return json.loads(p.read_text(encoding="utf-8"))


ZH_OGD = "https://www.web.statistik.zh.ch/ogd/data/KANTON_ZUERICH_{}.csv"


def zh_indicator(ind: int, source_id: str) -> pd.DataFrame:
    """Long table BFS_NR, GEBIET_NAME, year, value, unit for one ZH Gemeindeporträt indicator.
    BFS_NR 0 is the canton; district rows have other codes (kept as delivered)."""
    p = fetch_retry(ZH_OGD.format(ind), source_id, f"KANTON_ZUERICH_{ind}.csv")
    d = pd.read_csv(p, encoding="utf-8-sig")
    d = d.rename(columns={"INDIKATOR_JAHR": "year", "INDIKATOR_VALUE": "value"})
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    return d[["BFS_NR", "GEBIET_NAME", "INDIKATOR_NAME", "year", "value", "EINHEIT_KURZ"]]


@lru_cache(maxsize=1)
def ref_units() -> pd.DataFrame:
    mv, _ = load_backbone()
    v = versions_at(mv, REFERENCE_DATE)
    return v[["bfs_nr", "canton", "name"]].astype({"bfs_nr": int}).sort_values("bfs_nr").reset_index(drop=True)


@lru_cache(maxsize=32)
def _canton_states(canton: str) -> tuple[tuple[dt.date, frozenset], ...]:
    mv, _ = load_backbone()
    out, prev = [], None
    for d in _candidate_dates():
        s = frozenset(versions_at(mv, d).query("canton == @canton")["bfs_nr"].astype(int))
        if s != prev:
            out.append((d, s))
            prev = s
    return tuple(out)


def canton_vintage(bfs_numbers, canton: str) -> tuple[dt.date, float]:
    """Best-matching municipality state of one canton (latest date among equal matches).
    Returns (date, share of the given BFS numbers valid in that state)."""
    s = {int(b) for b in bfs_numbers if pd.notna(b) and 0 < int(b) < 9000}
    best, bj = None, -1.0
    states = _canton_states(canton)
    for i, (d, cur) in enumerate(states):
        # score: share of the file's numbers valid in that state (a file may cover only part of
        # the canton, e.g. BL before 1994 without Laufen), then jaccard
        j = (len(s & cur) / len(s) if s else 0.0, len(s & cur) / len(s | cur) if s | cur else 0.0)
        # a state holds until the day before the next state starts: use that last day
        end = states[i + 1][0] - dt.timedelta(days=1) if i + 1 < len(states) else REFERENCE_DATE
        end = min(end, REFERENCE_DATE)
        if bj == -1.0 or j >= bj:
            best, bj = end, j
    return best, bj[0]


def to_ref(wide: pd.DataFrame, metric_map: dict[str, str], source_id: str, canton: str, *,
           period_col: str = "period", rules: dict[str, str] | None = None,
           min_jaccard: float = 0.97, log: dict | None = None, vintage: dt.date | None = None,
           precision: str | None = None, na_notes: dict[str, str] | None = None) -> pd.DataFrame:
    """Reproject one canton's municipality rows (bfs_nr, period, value columns) per period.

    Optional boolean '<col>__na' columns mark values the source declares not computable; those
    rows get status `not_applicable` with na_notes[metric_id]. '<col>__sup' marks suppression."""
    parts = []
    w = wide[wide["bfs_nr"].notna()].copy()
    w["bfs_nr"] = w["bfs_nr"].astype(int)
    rules = dict(rules or {})
    metric_map = dict(metric_map)
    na_notes = na_notes or {}
    for c in list(metric_map):  # '<col>__na' flags: value not computable/applicable in source
        if f"{c}__na" in w:
            w[f"{c}__na"] = w[f"{c}__na"].fillna(False).astype(float)
            w.loc[w[f"{c}__na"] > 0, c] = np.nan
            metric_map[f"{c}__na"] = f"__na__{metric_map[c]}"
            rules[f"{c}__na"] = "sum"
    for c in [c for c in list(metric_map) if rules.get(c) == "not_aggregatable"]:
        # missing in the source (not suppressed / not applicable) -> no_data, not 'not 1:1'
        flag = w[c].isna()
        for extra in (f"{c}__sup", f"{c}__na"):
            if extra in w:
                flag &= ~(w[extra].fillna(False).astype(float) > 0)
        w[f"{c}__nan"] = flag.astype(float)
        metric_map[f"{c}__nan"] = f"__nan__{metric_map[c]}"
        rules[f"{c}__nan"] = "sum"
    groups = ([((p, v), d.drop(columns="src_vintage")) for (p, v), d in w.groupby([period_col, "src_vintage"], sort=True)]
              if "src_vintage" in w else [((p, vintage), d) for p, d in w.groupby(period_col, sort=True)])
    for (p, vin), d in groups:
        v, jac = (vin, None) if vin else canton_vintage(d["bfs_nr"].unique(), canton)
        if jac is not None and jac < min_jaccard:
            raise ValueError(f"{source_id} {canton} {p}: municipality state unclear "
                             f"(best {v}, jaccard {jac:.3f})")
        if log is not None:
            log[f"{canton} {p}"] = {"vintage": v.isoformat(), "jaccard": jac, "rows": int(len(d))}
        parts.append(per_period_to_reference(d, metric_map, source_id, period_col=period_col,
                                             rules=rules, vintage=v, precision=precision))
    if not parts:
        return pd.DataFrame(columns=OBS_COLUMNS)
    o = pd.concat(parts, ignore_index=True)
    isnan = o["metric_id"].str.startswith("__nan__")
    nanf, o = o[isnan], o[~isnan].copy()
    if len(nanf):
        f = nanf[nanf["value"] > 0].assign(metric_id=lambda x: x["metric_id"].str[7:])
        key = pd.MultiIndex.from_frame(o[["unit_id", "metric_id", "period"]])
        hit = key.isin(pd.MultiIndex.from_frame(f[["unit_id", "metric_id", "period"]])) & o["status"].eq("not_applicable").to_numpy()
        o.loc[hit, "status"] = "no_data"
        o.loc[hit, "note"] = None
    isna = o["metric_id"].str.startswith("__na__")
    flags, o = o[isna], o[~isna].copy()
    if len(flags):
        f = flags[flags["value"] > 0].assign(metric_id=lambda x: x["metric_id"].str[6:])
        key = pd.MultiIndex.from_frame(o[["unit_id", "metric_id", "period"]])
        hit = key.isin(pd.MultiIndex.from_frame(f[["unit_id", "metric_id", "period"]])) & o["value"].isna().to_numpy()
        o.loc[hit, "status"] = "not_applicable"
        o.loc[hit, "note"] = o.loc[hit, "metric_id"].map(lambda m: na_notes.get(m, "not computable in the source"))
    return o.reset_index(drop=True)


def complete(obs: pd.DataFrame, source_id: str, covered: dict[str, set[str]],
             reasons: dict[str, str], default_reason: str, *, precision: str = "exact",
             periods: dict[str, list[str]] | None = None,
             covered_periods: dict[tuple[str, str], set[str]] | None = None) -> pd.DataFrame:
    """Add a row for every reference municipality × metric × period.

    covered: metric -> cantons that publish it. Municipalities of other cantons get `not_covered`
    with reasons[canton] (or default_reason). Municipalities of covered cantons without a row get
    `no_data` ('no value in the <KT> source for this period'); with covered_periods
    {(metric, canton): periods}, a covered canton's period outside its published range is
    `no_data` with a note stating the published range.
    """
    units = ref_units()
    gem = obs[obs["level"] == "gemeinde"]
    have = set(zip(gem["unit_id"].astype(str), gem["metric_id"], gem["period"].astype(str)))
    rows = []
    any_cov = set().union(*covered.values()) if covered else set()
    for metric, cants in covered.items():
        pers = (periods or {}).get(metric) or sorted(set(gem.loc[gem["metric_id"] == metric, "period"].astype(str)))
        for per in pers:
            for u, kt in zip(units["bfs_nr"].astype(str), units["canton"]):
                if (u, metric, per) in have:
                    continue
                if kt in cants:
                    status = "no_data"
                    rng = (covered_periods or {}).get((metric, kt))
                    if rng is not None and per not in rng:
                        note = f"{kt} source has no value for {per} (published: {_span(rng)})"
                    else:
                        note = f"no value in the {kt} source for this municipality and period"
                else:
                    status = "not_covered"
                    if kt in any_cov and kt not in reasons:
                        note = f"not covered: the {kt} source does not publish this indicator"
                    else:
                        note = f"not covered: {reasons.get(kt, default_reason)}"
                rows.append((u, metric, per, status, note))
    if not rows:
        return obs
    add = pd.DataFrame(rows, columns=["unit_id", "metric_id", "period", "status", "note"])
    add = add.assign(level="gemeinde", vintage=REFERENCE_DATE.isoformat(), value=np.nan,
                     precision=precision, provenance="native", source_id=source_id)
    return pd.concat([obs, add[OBS_COLUMNS]], ignore_index=True)


def _span(periods) -> str:
    p = sorted(periods)
    return p[0] if len(p) == 1 else f"{p[0]}–{p[-1]}"


def canton_of(bfs) -> pd.Series:
    m = ref_units().set_index("bfs_nr")["canton"]
    return pd.Series(bfs).astype(int).map(m)


def fetch_session(warmup: list[str], url: str, source_id: str, filename: str, *,
                  retries: int = 4, timeout: int = 300):
    """Cached GET of `url` inside a requests session that first visits the `warmup` pages
    (e.g. a portal that only serves its CSV export with a session cookie). Same cache layout and
    manifest as pipeline.common.fetch; no headers are spoofed."""
    import hashlib
    import json
    import os

    import requests

    from pipeline.common import RAW, USER_AGENT, latest_snapshot
    cached = latest_snapshot(source_id, filename)
    if cached and os.environ.get("GB_REFRESH") != "1":
        return cached
    target = RAW / source_id / dt.date.today().isoformat() / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers["User-Agent"] = USER_AGENT
                for w in warmup:
                    s.get(w, timeout=timeout).raise_for_status()
                r = s.get(url, timeout=timeout)
                r.raise_for_status()
                if b"<html" in r.content[:500].lower():
                    raise RuntimeError(f"{url}: got an HTML page instead of the export")
                tmp = target.with_suffix(target.suffix + ".part")
                tmp.write_bytes(r.content)
                tmp.replace(target)
            break
        except (requests.RequestException, OSError, RuntimeError) as e:
            last = e
            time.sleep(2 ** (attempt + 1))
    else:
        raise RuntimeError(f"session download failed: {url}") from last
    entry = {"file": str(target.relative_to(RAW / source_id)), "url": url, "warmup": warmup,
             "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size,
             "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with open(RAW / source_id / "manifest.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    time.sleep(1)
    return target


def _norm(s: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    s = re.sub(r"\s*\((?:[a-z]{2})\)\s*$", "", s)  # canton suffix '(GE)'
    s = re.sub(r"^(le|la|les|l')\s*", "", s)
    s = s.replace("st.", "st ").replace("saint", "st")
    return re.sub(r"[^a-z0-9]", "", s)


def match_names(names, canton: str, extra: dict[str, int] | None = None) -> dict[str, int]:
    """Map municipality names of one canton (reference state) to BFS numbers; unmatched names are
    left out (callers check)."""
    u = ref_units()
    u = u[u["canton"] == canton]
    lk = {_norm(n): int(b) for n, b in zip(u["name"], u["bfs_nr"])}
    out = {}
    for n in names:
        if extra and n in extra:
            out[n] = extra[n]
        elif _norm(n) in lk:
            out[n] = lk[_norm(n)]
    return out


def zh_current(ind: int, source_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ZH indicator rows per year, plus the canton row ('Zürich - ganzer Kanton').

    ZH files keep pre-merger municipalities ('Adlikon (bis 2022)') next to the merged ones and
    back-cast some, but not all, merged municipalities. Per year: a reference-state municipality
    with a value keeps it (src_vintage = reference date); one without a value is represented by
    its predecessors valid on 31 Dec of that year (src_vintage = that date), which to_ref()
    aggregates (counts) or keeps only if 1:1 (ratios)."""
    from pipeline.backbone.vintage import crosswalk
    d = zh_indicator(ind, source_id)
    kt = d[d["GEBIET_NAME"].str.contains("ganzer Kanton", na=False)]
    d = d[d["BFS_NR"] > 0].rename(columns={"BFS_NR": "bfs_nr"})
    cur = set(ref_units().query("canton == 'ZH'")["bfs_nr"])
    mv, _ = load_backbone()
    cw = crosswalk()
    parts = []
    for y, g in d.groupby("year"):
        have = set(g.loc[g["bfs_nr"].isin(cur) & g["value"].notna(), "bfs_nr"])
        a = g[g["bfs_nr"].isin(have)].assign(src_vintage=REFERENCE_DATE)
        day = dt.date(int(y), 12, 31)
        ver = versions_at(mv, day).query("canton == 'ZH'")[["bfs_nr", "hist_id"]].astype(int)
        old = ver[~ver["bfs_nr"].isin(cur)]
        tgt = old.merge(cw[["from_hist_id", "to_bfs_nr"]], left_on="hist_id", right_on="from_hist_id")
        need = set(tgt.loc[~tgt["to_bfs_nr"].isin(have), "bfs_nr"])
        # unchanged municipalities without a value (suppressed) stay on the reference state
        rest = g[g["bfs_nr"].isin(cur) & ~g["bfs_nr"].isin(have)]
        rest = rest[~rest["bfs_nr"].isin(set(tgt["to_bfs_nr"]))].assign(src_vintage=REFERENCE_DATE)
        b = g[g["bfs_nr"].isin(need)].assign(src_vintage=day)
        parts += [a, rest, b]
    gem = pd.concat(parts, ignore_index=True)
    return gem, kt


def match_names_at(names, canton: str, year: int, extra: dict[str, int] | None = None) -> dict[str, int]:
    """Map municipality names of one canton to BFS numbers valid around `year` (state on 31 Dec of
    the year, then 1 Jan of the year, then 31 Dec of the following year), for sources that list
    historical municipalities by name only. Unmatched names are left out (callers check)."""
    mv, _ = load_backbone()
    lk: dict[str, int] = {}
    for day in (dt.date(year, 12, 31), dt.date(year, 1, 1), dt.date(year + 1, 12, 31)):
        v = versions_at(mv, min(day, REFERENCE_DATE)).query("canton == @canton")
        for n, b in zip(v["name"], v["bfs_nr"]):
            lk.setdefault(_norm(n), int(b))
    out = {}
    for n in names:
        if extra and n in extra:
            out[n] = extra[n]
        elif _norm(n) in lk:
            out[n] = lk[_norm(n)]
    return out
