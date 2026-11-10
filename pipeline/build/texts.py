"""German and French for the texts the pipeline writes into the app's data (review round 3, A4: R5, E1, C4).

The pipeline writes its notes, gap reasons, curation reasons, reach footnotes and the Sources page texts in
English. This step ships their translations as keyed messages, so no data file changes shape:

  data/out/web/texts.json  {"version": 1, "langs": ["de", "fr"],
                            "exact":    {"<English text>": {"de": "...", "fr": "..."}},
                            "patterns": [{"en": "<regex>", "de": "<template>", "fr": "<template>"}],
                            "numbers":  {"de": {"group": "'", "decimal": "."}, "fr": {"group": " ", "decimal": ","}}}

Translating one text (translate() below is the reference the frontend mirrors):
  1. the whole text in `exact`, else the first pattern whose `en` regex matches the whole text;
  2. otherwise the text is split at "; " into segments and each segment is translated the same way
     (a run of segments that together match an entry is taken as one); segments without a match stay English;
  3. a template inserts the regex groups: {1} as is, {1|n} with the language's number format (1,234.5 ->
     1'234.5 / 1 234,5), {1|t} translated recursively (a nested note), {1|l} as a ", " list translated item by item.
Place names, station and hub names, party abbreviations and dates stay as they are.

Sources: pipeline/i18n/texts.yaml (notes, reasons, reach texts; patterns and exact strings) and
pipeline/i18n/texts_sources.yaml (Sources page: publisher, licence, attribution, vintage, years, notes).
Coverage (strings shipped vs translated) goes to data/interim/texts_coverage.json and the quality report;
untranslated strings are listed in data/interim/texts_untranslated.csv.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml

from pipeline.common import interim_path, out_path

I18N = Path(__file__).resolve().parents[1] / "i18n"
LANGS = ("de", "fr")
NUMBERS = {"de": {"group": "'", "decimal": "."}, "fr": {"group": " ", "decimal": ","}}
NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+")
PLACEHOLDER = re.compile(r"\{(\d+)(?:\|([ntl]))?\}")


def load() -> dict:
    """exact {en: {de, fr}} and patterns [(compiled, {de, fr}, en)] from pipeline/i18n/texts*.yaml."""
    exact, patterns = {}, []
    for name in ("texts.yaml", "texts_sources.yaml"):
        p = I18N / name
        if not p.exists():
            continue
        y = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for e in y.get("exact") or []:
            exact[e["en"]] = {l: e[l] for l in LANGS if e.get(l)}
        for e in y.get("patterns") or []:
            patterns.append((re.compile(e["en"]), {l: e[l] for l in LANGS if e.get(l)}, e["en"]))
    return {"exact": exact, "patterns": patterns}


def fmt_numbers(s: str, lang: str) -> str:
    """English number format (1,234.5) -> the language's (1'234.5 / 1 234,5)."""
    g, d = NUMBERS[lang]["group"], NUMBERS[lang]["decimal"]

    def one(m):
        x = m.group(0)
        return x.replace(",", "\x00").replace(".", d).replace("\x00", g)
    return NUM.sub(one, s)


def _fill(tpl: str, m: re.Match, lang: str, tx: dict) -> str | None:
    bad = []

    def rep(p):
        v = m.group(int(p.group(1))) or ""
        mod = p.group(2)
        if mod == "n":
            return fmt_numbers(v, lang)
        if mod == "t":
            r = translate(v, lang, tx, strict=True)
            if r is None:
                bad.append(v)
                return v
            return r
        if mod == "l":
            items = [translate(x, lang, tx, strict=True) for x in v.split(", ")]
            if any(i is None for i in items):
                bad.append(v)
                return v
            return ", ".join(items)
        return v
    out = PLACEHOLDER.sub(rep, tpl)
    return None if bad else out


def _one(s: str, lang: str, tx: dict) -> str | None:
    e = tx["exact"].get(s)
    if e and lang in e:
        return e[lang]
    for rx, tpl, _ in tx["patterns"]:
        if lang in tpl and (m := rx.fullmatch(s)):
            r = _fill(tpl[lang], m, lang, tx)
            if r is not None:
                return r
    return None


def translate(s: str, lang: str, tx: dict, strict: bool = False) -> str | None:
    """Translation of one shipped text, or None (strict: when any part stays untranslated)."""
    if not isinstance(s, str) or not s.strip():
        return s
    r = _one(s, lang, tx)
    if r is not None:
        return r
    segs = s.split("; ")
    if len(segs) == 1:
        return None if strict else s
    out, i, missing = [], 0, False
    while i < len(segs):
        for j in range(len(segs), i, -1):     # longest run of segments that matches as one text
            r = _one("; ".join(segs[i:j]), lang, tx)
            if r is not None:
                out.append(r)
                i = j
                break
        else:
            out.append(segs[i])
            missing = True
            i += 1
    if missing and strict:
        return None
    return "; ".join(out)


def untranslated_parts(s: str, lang: str, tx: dict) -> list[str]:
    """Segments of s that have no translation (for the coverage report)."""
    if translate(s, lang, tx, strict=True) is not None:
        return []
    segs = s.split("; ")
    out, i = [], 0
    while i < len(segs):
        for j in range(len(segs), i, -1):
            if _one("; ".join(segs[i:j]), lang, tx) is not None:
                i = j
                break
        else:
            out.append(segs[i])
            i += 1
    return out or [s]


# ---- what the app shows: strings in the shipped files ------------------------------------------------
SOURCE_FIELDS = ("title", "publisher", "license", "attribution", "vintage", "years", "status_note", "status_text")


def shipped_strings() -> Counter:
    """English texts in the shipped data files that the app displays (notes, reasons, Sources page)."""
    c: Counter = Counter()
    web = out_path("web")
    for f in sorted((web / "latest").glob("*/*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for col in d.get("metrics", {}).values():
            c.update(col.get("notes") or [])
    p = web / "metrics.json"
    if p.exists():
        for m in json.loads(p.read_text(encoding="utf-8")):
            c.update((m.get("unavailable_levels") or {}).values())
            c.update(v.get("why") for v in (m.get("curation") or {}).values() if v.get("v") == "note")
    p = web / "sources.json"
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")):
            c.update(r.get(k) for k in SOURCE_FIELDS if isinstance(r.get(k), str))
    p = web / "excluded_sources.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        c.update([d.get("note")])
        c.update(v for v in (d.get("sources") or {}).values() if isinstance(v, str))
    p = web / "reach_times.json"
    if p.exists():
        r = json.loads(p.read_text(encoding="utf-8"))
        for key in ("reasons", "notes"):
            for hubs in (r.get(key) or {}).values():
                for d in hubs.values():
                    c.update(d.values())
    for f in sorted(out_path("reach").glob("*_spread.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        for dirn in (r.get("reasons") or {}).values():
            for d in dirn.values():
                c.update(d.values())
    for f in sorted((web / "vintage").glob("*/*.json")) if (web / "vintage").exists() else []:
        d = json.loads(f.read_text(encoding="utf-8"))
        for cols in (d.get("metrics") or {}).values():   # vintage files: a list of period columns per metric
            for col in (cols if isinstance(cols, list) else [cols]):
                c.update(col.get("notes") or [])
    c.pop(None, None)
    return c


def build() -> dict:
    tx = load()
    strings = shipped_strings()
    rows, cov = [], {}
    for lang in LANGS:
        n_ok = n_all = 0
        seg = Counter()
        for s, k in strings.items():
            n_all += 1
            parts = untranslated_parts(s, lang, tx)
            if not parts:
                n_ok += 1
            for p_ in parts:
                seg[p_] += k
        cov[lang] = {"strings": n_all, "translated": n_ok, "untranslated_segments": len(seg)}
        rows += [(lang, p_, k) for p_, k in seg.most_common()]
    payload = {"version": 1, "langs": list(LANGS),
               "note": "German and French for pipeline texts (pipeline/build/texts.py); unknown texts stay English",
               "exact": {k: v for k, v in sorted(tx["exact"].items())},
               "patterns": [{"en": en, **tpl} for _, tpl, en in tx["patterns"]],
               "numbers": NUMBERS}
    p = out_path("web", "texts.json")
    p.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    import csv
    with open(interim_path("texts_untranslated.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["lang", "segment", "occurrences"])
        w.writerows(rows)
    interim_path("texts_coverage.json").write_text(json.dumps(cov, indent=1), encoding="utf-8")
    return {"file": str(p), "coverage": cov, "kb": round(p.stat().st_size / 1024)}


if __name__ == "__main__":
    print(build())
