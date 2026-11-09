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
