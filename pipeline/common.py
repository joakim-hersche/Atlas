"""Shared helpers: paths, cached downloads with a manifest, small IO utilities.

Raw downloads live in data/raw/<source_id>/<YYYY-MM-DD>/ and are never edited.
Each download is recorded in data/raw/<source_id>/manifest.jsonl (url, file, sha256, size, time).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
OUT = DATA / "out"

USER_AGENT = "gemeindebank-pipeline/0.1 (personal open-data project)"
# Reference date of the target municipality state (decision D8: latest state).
# Overridable for rebuilds, e.g. GB_REFERENCE_DATE=2027-01-01 make data
REFERENCE_DATE = dt.date.fromisoformat(os.environ.get("GB_REFERENCE_DATE", "2026-01-01"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_snapshot(source_id: str, filename: str) -> Path | None:
    """Return the most recent cached copy of filename for a source, if any."""
    base = RAW / source_id
    if not base.exists():
        return None
    hits = sorted(base.glob(f"*/{filename}"))
    return hits[-1] if hits else None


def fetch(url: str, source_id: str, filename: str, *, params: dict | None = None,
          headers: dict | None = None, refresh: bool = False, timeout: int = 600,
          retries: int = 4) -> Path:
    """Download url to data/raw/<source_id>/<today>/<filename> unless a cached copy exists.

    With refresh=False (default) the latest cached snapshot is reused, so rebuilds are
    reproducible and offline. Set GB_REFRESH=1 (or refresh=True) to download again.
    """
    refresh = refresh or os.environ.get("GB_REFRESH") == "1"
    cached = latest_snapshot(source_id, filename)
    if cached and not refresh:
        return cached
    day = dt.date.today().isoformat()
    target = RAW / source_id / day / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with requests.get(url, params=params, headers=hdrs, stream=True, timeout=timeout) as r:
                if r.status_code == 429:
                    raise requests.HTTPError("429 Too Many Requests", response=r)
                r.raise_for_status()
                tmp = target.with_suffix(target.suffix + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
                tmp.replace(target)
                final_url = r.url
            break
        except (requests.RequestException, OSError) as err:  # network hiccups, 429
            last_err = err
            time.sleep(2 ** (attempt + 1))
    else:
        raise RuntimeError(f"download failed after {retries} attempts: {url}") from last_err
    entry = {
        "file": str(target.relative_to(RAW / source_id)),
        "url": final_url,
        "params": params,
        "sha256": _sha256(target),
        "bytes": target.stat().st_size,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    with open(RAW / source_id / "manifest.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return target


def interim_path(*parts: str) -> Path:
    p = INTERIM.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def out_path(*parts: str) -> Path:
    p = OUT.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def ddmmyyyy(d: dt.date) -> str:
    """Date format used by the BFS register API."""
    return d.strftime("%d-%m-%Y")


def parse_ch_date(s: str | None) -> dt.date | None:
    """Parse 'DD.MM.YYYY' (BFS) or ISO 'YYYY-MM-DD'; empty -> None."""
    if s is None:
        return None
    s = str(s).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    if "." in s:
        d, m, y = s.split(".")
        return dt.date(int(y), int(m), int(d))
    return dt.date.fromisoformat(s[:10])
