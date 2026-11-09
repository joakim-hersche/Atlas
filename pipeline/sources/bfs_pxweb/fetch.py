"""Generic BFS PxWeb (STAT-TAB) connector.

API: https://www.pxweb.bfs.admin.ch/api/v1/de/<dbid>/<dbid>.px
  GET  -> table metadata (variables, value codes and texts)
  POST -> data, JSON query {"query": [...], "response": {"format": "csv"}}
The service rate-limits at about 1 request per second (HTTP 429); fetch() retries with backoff.
CSV responses are Latin-1 encoded.
"""
from __future__ import annotations

import hashlib
import io
import json
import time

import pandas as pd
import requests

from pipeline.common import RAW, USER_AGENT, fetch, latest_snapshot

SOURCE = "bfs_pxweb"
BASE = "https://www.pxweb.bfs.admin.ch/api/v1/de"


def metadata(dbid: str) -> dict:
    p = fetch(f"{BASE}/{dbid}/{dbid}.px", SOURCE, f"{dbid}.meta.json")
    return json.loads(p.read_text(encoding="utf-8"))


def query(dbid: str, select: dict[str, list[str] | str]) -> pd.DataFrame:
    """Query a cube. select maps variable code -> list of value codes, or '*' for all.

    Variables not in select are set to their first value (usually the total).
    Results are cached under data/raw/bfs_pxweb/<date>/<dbid>.<hash>.csv.
    """
    meta = metadata(dbid)
    q = []
    for v in meta["variables"]:
        want = select.get(v["code"])
        codes = v["values"] if want == "*" else (want if want else [v["values"][0]])
        q.append({"code": v["code"], "selection": {"filter": "item", "values": list(codes)}})
    body = {"query": q, "response": {"format": "csv"}}
    key = hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    fname = f"{dbid}.{key}.csv"
    cached = latest_snapshot(SOURCE, fname)
    if cached is None:
        cached = _post(dbid, body, fname)
    text = cached.read_bytes().decode("latin-1")
    return pd.read_csv(io.StringIO(text), dtype=str)


MAX_CELLS = 80_000  # PxWeb answers 403 above its cell limit; stay well below it


def query_codes(dbid: str, select: dict[str, list[str] | str]) -> pd.DataFrame:
    """Like query(), but returns value codes (not labels) via JSON-stat 2.0.

    Columns: one per variable code (category codes as strings) plus 'value'. Requests above
    MAX_CELLS are split along the time variable (or else the largest variable) and concatenated.
    """
    meta = metadata(dbid)
    sel = {}
    for v in meta["variables"]:
        want = select.get(v["code"])
        sel[v["code"]] = v["values"] if want == "*" else (list(want) if want else [v["values"][0]])
    cells = 1
    for codes in sel.values():
        cells *= len(codes)
    if cells > MAX_CELLS:
        time_var = next((c for c in sel if c in ("Jahr", "Zeitperiode", "Jahr / Periode")), None)
        split_var = time_var if time_var and len(sel[time_var]) > 1 else max(sel, key=lambda c: len(sel[c]))
        per = max(1, int(len(sel[split_var]) * MAX_CELLS / cells))
        parts = []
        for i in range(0, len(sel[split_var]), per):
            sub = dict(sel)
            sub[split_var] = sel[split_var][i:i + per]
            parts.append(query_codes(dbid, sub))
        return pd.concat(parts, ignore_index=True)
    return _query_codes_single(dbid, sel)


def _query_codes_single(dbid: str, select: dict[str, list[str]]) -> pd.DataFrame:
    import itertools
    meta = metadata(dbid)
    q = []
    for v in meta["variables"]:
        want = select.get(v["code"])
        codes = v["values"] if want == "*" else (want if want else [v["values"][0]])
        q.append({"code": v["code"], "selection": {"filter": "item", "values": list(codes)}})
    body = {"query": q, "response": {"format": "json-stat2"}}
    key = hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    fname = f"{dbid}.{key}.json"
    cached = latest_snapshot(SOURCE, fname) or _post(dbid, body, fname)
    js = json.loads(cached.read_bytes())
    dims = js["id"]
    cats = []
    for d in dims:
        idx = js["dimension"][d]["category"]["index"]
        order = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx)
        cats.append(order)
    vals = js["value"]
    if isinstance(vals, dict):  # sparse form
        dense = [None] * int(pd.Series(js["size"]).prod())
        for k, v in vals.items():
            dense[int(k)] = v
        vals = dense
    rows = list(itertools.product(*cats))
    df = pd.DataFrame(rows, columns=dims)
    df["value"] = pd.to_numeric(pd.Series(vals), errors="coerce")
    return df


def geo_level_of_code(code: str) -> str:
    """BFS PxWeb institutional geography codes: 8100 CH, 2-letter canton, 6-digit district, 4-digit municipality."""
    if code in ("8100", "CH"):
        return "schweiz"
    if code.isdigit() and len(code) == 4 and int(code) >= 9000:
        return "pseudo"  # e.g. Swiss abroad, postal-vote districts (votes)
    if code.isalpha() and len(code) == 2:
        return "kanton"
    if code.isdigit() and len(code) == 6:
        return "bezirk"
    if code.isdigit() and len(code) == 4:
        return "gemeinde"
    return "other"


def _post(dbid: str, body: dict, fname: str):
    import datetime as dt
    url = f"{BASE}/{dbid}/{dbid}.px"
    target = RAW / SOURCE / dt.date.today().isoformat() / fname
    target.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(6):
        r = requests.post(url, json=body, headers={"User-Agent": USER_AGENT}, timeout=600)
        if r.status_code == 429:
            time.sleep(2 ** (attempt + 1))
            continue
        r.raise_for_status()
        target.write_bytes(r.content)
        with open(RAW / SOURCE / "manifest.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"file": str(target.relative_to(RAW / SOURCE)), "url": url,
                                 "query": body, "bytes": len(r.content),
                                 "sha256": hashlib.sha256(r.content).hexdigest(),
                                 "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")},
                                ensure_ascii=False) + "\n")
        time.sleep(1.2)  # stay under the rate limit
        return target
    raise RuntimeError(f"PxWeb rate limit not cleared for {dbid}")


def parse_geo_label(label: str) -> tuple[str, int | None, str]:
    """PxWeb geography labels: 'Schweiz', '- Zürich', '>> Bezirk Affoltern', '......0261 Zürich'.

    Returns (level, bfs_nr or None, name).
    """
    s = label.strip()
    if s.startswith("......"):
        code, _, name = s[6:].partition(" ")
        return "gemeinde", int(code), name
    if s.startswith(">>"):
        return "bezirk", None, s[2:].strip()
    if s.startswith("- "):
        return "kanton", None, s[2:].strip()
    return "other", None, s
