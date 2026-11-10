"""Series-break markers (pipeline/series_breaks.yaml): where a metric's method or definition changed.

  load()          the YAML
  validate()      schema check against the metric catalog (raised by web.run on any error)
  place()         the metric period that carries a break (first period on the new basis)
  resolve()       metric_id -> {period: {label_en, label_de, label_fr}} for metrics.json, with
                  propagation to derived ratios and the breaks read from the connectors' notes
  check_evidence() every quote of the YAML found in its cached file (pipeline/tests)

    .venv/bin/python -m pipeline.build.series_breaks fetch   # cache the evidence pages (data/raw/series_breaks)
    .venv/bin/python -m pipeline.build.series_breaks check   # validate + quote check
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import yaml

from pipeline.common import ROOT

PATH = ROOT / "pipeline" / "series_breaks.yaml"
SOURCE_ID = "series_breaks"   # evidence cache: data/raw/series_breaks/<date>/
KEYS = {"id", "period", "metrics", "source", "exclude", "propagate", "note_en", "note_de", "note_fr",
        "evidence", "cantons", "from_note"}
REQUIRED = {"id", "note_en", "note_de", "note_fr", "evidence"}
PERIOD = re.compile(r"^\d{4}(-\d{2})?$")
LANGS = ("en", "de", "fr")
# evidence pages that no connector caches (url -> file name under data/raw/series_breaks/<date>/)
EVIDENCE_DOWNLOADS = {
    "https://www.pxweb.bfs.admin.ch/DownloadFile.aspx?file=px-x-0102020000_201": "px-x-0102020000_201.px",
    "https://www.pxweb.bfs.admin.ch/DownloadFile.aspx?file=px-x-0904030000_105": "px-x-0904030000_105.px",
    "https://www.pxweb.bfs.admin.ch/DownloadFile.aspx?file=px-x-0904030000_106": "px-x-0904030000_106.px",
    "https://www.pxweb.bfs.admin.ch/DownloadFile.aspx?file=px-x-1702020000_105": "px-x-1702020000_105.px",
    "https://data.geo.admin.ch/api/stac/v1/collections/ch.bfs.bildungsstand": "stac_ch.bfs.bildungsstand.json",
    "https://www.bfs.admin.ch/bfs/de/home/statistiken/bildung-wissenschaft/bildungsstand/bildungsstand-regionaler-ebene.html":
        "bfs_bildungsstand_regionaler_ebene.html",
    "https://www.web.statistik.zh.ch/ogd/daten/zhweb.json": "zhweb.json",
}


def load(path: Path = PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------- periods
def period_end(p: str):
    """Comparable end point (year, month) of a period of any shape used in the catalog: '2025', '2025-10',
    '2022-2024' (pooled window: its last year), '1979/85' (survey window: its last year), vote periods
    'YYYY-MM-DD#id'. None for anything else (e.g. '1961-1990' climate normals end in 1990 and are fine)."""
    p = str(p)
    if m := re.match(r"^(\d{4})-(\d{2})-\d{2}#", p):
        return int(m[1]), int(m[2])
    if m := re.fullmatch(r"(\d{4})-(\d{2})", p):
        return int(m[1]), int(m[2])
    if m := re.fullmatch(r"(\d{4})-(\d{4})", p):
        return int(m[2]), 0
    if m := re.fullmatch(r"(\d{4})/(\d{2})", p):
        y1, yy = int(m[1]), int(m[2])
        y2 = y1 - y1 % 100 + yy
        return (y2 + 100 if y2 < y1 else y2), 0
    if m := re.fullmatch(r"(\d{4})", p):
        return int(m[1]), 0
    return None


def place(brk: str, periods: list[str]) -> str | None:
    """The period of a metric that carries a break starting at `brk` ('YYYY' or 'YYYY-MM'): the first period
    whose end is on or after it. None when no period of the metric lies before the break (nothing to compare
    across) or none on or after it."""
    b = period_end(brk)
    keyed = sorted(((period_end(p), p) for p in periods if period_end(p) is not None), key=lambda x: (x[0], x[1]))
    before = [p for k, p in keyed if k < b]
    after = [p for k, p in keyed if k >= b]
    return after[0] if before and after else None


# ---------------------------------------------------------------- schema
def validate(cfg: dict, metric_ids: set[str], source_ids: set[str] | None = None) -> list[str]:
    errors = []
    seen = set()
    for i, e in enumerate(cfg.get("breaks") or []):
        bid = e.get("id", f"#{i}")
        if bid in seen:
            errors.append(f"{bid}: duplicate id")
        seen.add(bid)
        unknown = set(e) - KEYS
        if unknown:
            errors.append(f"{bid}: unknown keys {sorted(unknown)}")
        missing = REQUIRED - {k for k, v in e.items() if v not in (None, "", [])}
        if missing:
            errors.append(f"{bid}: missing {sorted(missing)}")
        fn = e.get("from_note")
        if fn:
            if not isinstance(fn, dict) or not fn.get("regex") or not fn.get("source"):
                errors.append(f"{bid}: from_note needs source and regex")
            else:
                try:
                    re.compile(fn["regex"])
                except re.error as err:
                    errors.append(f"{bid}: bad regex ({err})")
                if source_ids is not None and fn["source"] not in source_ids:
                    errors.append(f"{bid}: unknown source {fn['source']!r}")
            if e.get("period") or e.get("metrics"):
                errors.append(f"{bid}: from_note takes its periods and metrics from the notes")
        else:
            if not PERIOD.match(str(e.get("period", ""))):
                errors.append(f"{bid}: period must be 'YYYY' or 'YYYY-MM', got {e.get('period')!r}")
            if not e.get("metrics") and not e.get("source"):
                errors.append(f"{bid}: needs metrics or source")
        for m in (e.get("metrics") or []) + (e.get("exclude") or []):
            if m not in metric_ids:
                errors.append(f"{bid}: unknown metric {m!r}")
        if e.get("source") and source_ids is not None and e["source"] not in source_ids:
            errors.append(f"{bid}: unknown source {e['source']!r}")
        for lg in LANGS:
            v = e.get(f"note_{lg}")
            if v is not None and (not isinstance(v, str) or len(v) > 240):
                errors.append(f"{bid}: note_{lg} must be a string of at most 240 characters")
        ev = e.get("evidence") or []
        if not isinstance(ev, list):
            errors.append(f"{bid}: evidence must be a list")
            ev = []
        for x in ev:
            if not isinstance(x, dict) or not (x.get("url") or x.get("ref")):
                errors.append(f"{bid}: each evidence item needs a url or a ref")
            elif x.get("url") and not (x.get("file") and x.get("quote")):
                errors.append(f"{bid}: evidence with a url needs the cached file and a verbatim quote")
        if ev and not any(isinstance(x, dict) and x.get("url") for x in ev) and not fn:
            errors.append(f"{bid}: at least one evidence item must quote the publisher (url + file + quote)")
        for c in e.get("cantons") or []:
            if not re.fullmatch(r"[A-Z]{2}", str(c)):
                errors.append(f"{bid}: bad canton {c!r}")
    if not isinstance(cfg.get("rejected", {}), dict):
        errors.append("rejected must be a mapping id -> reason")
    return errors


# ---------------------------------------------------------------- resolve
def _inputs(agg: str) -> list[str]:
    """Metrics a derived metric is computed from, for ratios and pooled ratios only (a break in an input
    is a break in the ratio; weighted means and changes over N years are not propagated)."""
    agg = str(agg)
    if not agg.startswith(("ratio:", "pooled:")):
        return []
    body = agg.split(":", 2)[1]
    return re.findall(r"[a-z][a-z0-9_]*", body)


def _targets(e: dict, meta) -> list[str]:
    ids = list(e.get("metrics") or [])
    if e.get("source"):
        ids += [m for m in meta.index[meta["source_id"] == e["source"]] if m not in ids]
    ex = set(e.get("exclude") or [])
    return [m for m in ids if m not in ex]


def _derived_closure(seeds: set[str], meta) -> set[str]:
    deps = {mid: set(_inputs(meta.loc[mid, "aggregation"])) for mid in meta.index if meta.loc[mid, "kind"] == "derived"}
    out = set(seeds)
    while True:
        new = {d for d, ins in deps.items() if d not in out and ins & out}
        if not new:
            return out
        out |= new


def _add(out: dict, mid: str, per: str, labels: dict):
    cur = out.setdefault(mid, {}).get(per)
    if cur is None:
        out[mid][per] = dict(labels)
        return
    for k, v in labels.items():   # two breaks on one period: both notes, once each
        if v not in cur[k].split(" · "):
            cur[k] = f"{cur[k]} · {v}"


def resolve(cfg: dict, meta, periods: dict[str, list[str]], notes: list[tuple[str, str, str]] = ()) -> tuple[dict, list[dict]]:
    """metric_id -> {period: {label_en, label_de, label_fr}} for the metrics that ship (keys of `periods`),
    and one summary row per break and period for sources.json. `notes`: (metric_id, period, note) of the
    connectors' notes for the `from_note` rules (one row per metric and period is enough)."""
    out: dict[str, dict] = {}
    summary: list[dict] = []
    for e in cfg.get("breaks") or []:
        labels = {f"label_{lg}": e[f"note_{lg}"] for lg in LANGS}
        if e.get("from_note"):
            fn = e["from_note"]
            rx = re.compile(fn["regex"])
            hits: dict[tuple, dict] = {}
            for mid, per, note in notes:
                m = rx.match(str(note or ""))
                if not m or mid not in periods or mid not in meta.index or meta.loc[mid, "source_id"] != fn["source"]:
                    continue
                if per not in periods[mid] or periods[mid].index(per) == 0:
                    continue
                pct = m.group(1) if m.groups() else ""
                lab = {k: v.replace("{pct}", pct) for k, v in labels.items()}
                _add(out, mid, per, lab)
                hits.setdefault((per, pct), {"labels": lab, "metrics": []})["metrics"].append(mid)
            for (per, _), h in sorted(hits.items()):
                summary.append({"id": e["id"], "source": fn["source"], "period": per, **h["labels"],
                                "metrics": sorted(h["metrics"]), "evidence": _evidence_public(e)})
            continue
        seeds = set(_targets(e, meta))
        ids = _derived_closure(seeds, meta) if e.get("propagate", True) else seeds
        placed = []
        for mid in sorted(ids):
            if mid not in periods:
                continue
            per = place(str(e["period"]), periods[mid])
            if per is None:
                continue
            _add(out, mid, per, labels)
            placed.append(mid)
        src = e.get("source") or (meta.loc[_targets(e, meta)[0], "source_id"] if _targets(e, meta) else None)
        if placed:
            summary.append({"id": e["id"], "source": src, "period": str(e["period"]), **labels,
                            "cantons": e.get("cantons"), "metrics": placed, "evidence": _evidence_public(e)})
    return out, summary


def _evidence_public(e: dict) -> list[str]:
    """Publisher links of a break (for the Sources page); internal refs stay in the YAML."""
    return sorted({x["url"] for x in e.get("evidence") or [] if isinstance(x, dict) and x.get("url")})


# ---------------------------------------------------------------- evidence
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def text_of(path: Path) -> str:
    """Searchable text of a cached evidence file (PX header, JSON, HTML/XML, CSV, xlsx/xls cells)."""
    suf = path.suffix.lower()
    if suf == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True)
        return "\n".join(str(c) for ws in wb.worksheets for row in ws.iter_rows(values_only=True) for c in row if isinstance(c, str))
    if suf == ".xls":
        import xlrd
        wb = xlrd.open_workbook(str(path))
        return "\n".join(str(c) for sh in wb.sheets() for r in range(sh.nrows) for c in sh.row_values(r) if isinstance(c, str))
    raw = path.read_bytes()
    if suf == ".px":
        raw = raw.split(b"\nDATA=", 1)[0]
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("iso-8859-15")
    if suf == ".px":
        txt = re.sub(r'"\s*\r?\n\s*"', "", txt)          # PX strings continue over lines: "...""\n"..."
    elif suf == ".json":
        txt = json.dumps(json.loads(txt), ensure_ascii=False)
        txt = txt.replace("\\n", "\n").replace('\\"', '"')
    elif suf in (".html", ".htm", ".xml"):
        txt = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", txt, flags=re.S))
    return txt


def newest(pattern: str) -> Path | None:
    hits = sorted(ROOT.glob(pattern))
    return hits[-1] if hits else None


def check_evidence(cfg: dict) -> tuple[list[str], list[str]]:
    """(problems, skipped): a quote not found in its cached file is a problem; a file not cached here
    (data/raw is not in git) is skipped."""
    problems, skipped, cache = [], [], {}
    for e in cfg.get("breaks") or []:
        for x in e.get("evidence") or []:
            if not x.get("file") or not x.get("quote"):
                continue
            p = newest(x["file"])
            if p is None:
                skipped.append(f"{e['id']}: {x['file']}")
                continue
            if p not in cache:
                cache[p] = _norm(text_of(p))
            if _norm(x["quote"]) not in cache[p]:
                problems.append(f"{e['id']}: quote not found in {p.relative_to(ROOT)}: {x['quote'][:80]!r}")
    return problems, skipped


def fetch_evidence():
    from pipeline.common import fetch
    for url, name in EVIDENCE_DOWNLOADS.items():
        print(fetch(url, SOURCE_ID, name))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "fetch":
        fetch_evidence()
    from pipeline.harmonize.schema import SOURCES_DIR, load_metrics
    cfg = load()
    errs = validate(cfg, set(load_metrics()["id"]), {p.name for p in SOURCES_DIR.iterdir() if p.is_dir()})
    probs, skipped = check_evidence(cfg)
    for x in errs + probs:
        print("ERROR", x)
    for x in skipped:
        print("skipped (not cached)", x)
    sys.exit(1 if errs or probs else 0)
