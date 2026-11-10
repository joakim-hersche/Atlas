"""Public data release: package what the site shows, and only what may be redistributed.

    uv run python -m pipeline.release          (or: make release)

Writes data/out/release/ (never touches other outputs; the folder is rebuilt on every run):
  observations.parquet  harmonized long table on the reference municipality state, all levels
  metrics.csv           one row per metric with source, licence and attribution columns
  sources.csv           one row per source: licence, attribution, review status, cantons, flags
  boundaries.gpkg       current boundaries (full-resolution BFS G1 polygons, LV95) per level
  excluded.csv          sources, metrics and cantons left out, with the reason
  README.md             contents, columns, licences, attribution

Licence gate: the same rule as the site (pipeline.build.web.run: automatic text check, overridden by
pipeline/licence_review.yaml, per-metric and per-canton clearance) plus pipeline/release_flags.yaml.
Raw downloads and interim files are only read.
"""
from __future__ import annotations

import csv
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from pipeline.common import OUT, REFERENCE_DATE, interim_path
from pipeline.harmonize.schema import SOURCES_DIR, load_metrics

RELEASE_DIR = OUT / "release"
PIPELINE_DIR = SOURCES_DIR.parent
BOUNDARY_ATTRIBUTION = "(c) swisstopo (swissBOUNDARIES3D), generalised boundaries G1 distributed by BFS"


@dataclass
class Gate:
    """Result of the licence check."""
    sources: dict                                   # source_id -> meta.yaml
    excluded: dict                                  # source_id -> reason (source not released)
    metric_only: dict                               # source_id -> {metric ids cleared}
    cantons: dict                                   # source_id -> sorted list of cleared cantons
    dropped_cantons: dict = field(default_factory=dict)   # source_id -> {canton: reason}
    noncommercial: dict = field(default_factory=dict)     # source_id -> note
    review: dict = field(default_factory=dict)


def _is_open(meta: dict) -> tuple[bool, str]:
    from pipeline.build.web import license_cleared
    return license_cleared(meta)


def load_sources() -> dict:
    out = {}
    for f in sorted(SOURCES_DIR.glob("*/meta.yaml")):
        out[f.parent.name] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    return out


def build_gate(sources: dict, review: dict, flags: dict | None = None, has_ingest=None) -> Gate:
    """Pure function (unit-tested). `has_ingest(sid)` tells whether a source delivers observations."""
    flags = flags or {}
    has_ingest = has_ingest or (lambda sid: (SOURCES_DIR / sid / "ingest.py").exists())
    cleared = {sid: _is_open(m) for sid, m in sources.items()}
    metric_only, cantons = {}, {}
    for sid, r in review.items():
        if r.get("status") == "cleared":
            cleared[sid] = (True, "reviewed")
            if r.get("metrics"):
                metric_only[sid] = set(r["metrics"])
            if r.get("cantons"):
                cantons[sid] = sorted(r["cantons"])
        elif r.get("status") == "blocked":
            cleared[sid] = (False, "blocked by review")
    dropped = {sid: dict(d) for sid, d in (flags.get("drop_cantons") or {}).items()}
    for sid, d in dropped.items():
        if sid in cantons:
            cantons[sid] = [c for c in cantons[sid] if c not in d]
    excluded = {sid: why for sid, (ok, why) in cleared.items() if not ok and has_ingest(sid)}
    return Gate(sources=sources, excluded=excluded, metric_only=metric_only, cantons=cantons,
                dropped_cantons=dropped, noncommercial=dict(flags.get("noncommercial") or {}), review=review)


def select_metrics(meta: pd.DataFrame, gate: Gate) -> tuple[list[str], dict]:
    """Metric ids that may be released, and {metric_id: reason} for the others."""
    meta = meta.drop_duplicates("id").set_index("id")

    def shippable(mid):
        sid = meta.loc[mid, "source_id"]
        return sid not in gate.excluded and (sid not in gate.metric_only or mid in gate.metric_only[sid])

    keep, why = [], {}
    for mid in meta.index:
        sid = meta.loc[mid, "source_id"]
        if sid in gate.excluded:
            why[mid] = f"source {sid}: {gate.excluded[sid]}"
        elif sid in gate.metric_only and mid not in gate.metric_only[sid]:
            why[mid] = f"source {sid}: metric not cleared by licence review"
        elif meta.loc[mid, "kind"] == "derived":
            agg = str(meta.loc[mid, "aggregation"])
            ids = re.findall(r"[a-z][a-z0-9_]+", agg.split(":", 1)[1]) if ":" in agg else []
            bad = [i for i in ids if i in meta.index and not shippable(i)]
            if bad:
                why[mid] = f"derived from held-back metric {bad[0]}"
            else:
                keep.append(mid)
        else:
            keep.append(mid)
    return keep, why


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_observations(keep: list[str], meta: pd.DataFrame, gate: Gate, dst: Path) -> int:
    import duckdb
    from pipeline.backbone.levels import membership
    meta = meta.drop_duplicates("id")
    src = interim_path("metrics_all.parquet")
    if not src.exists():
        raise SystemExit(f"{src} missing: run `make metrics` first")
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{os.environ.get('GB_DUCKDB_MEMORY', '3GB')}'")
    con.register("keep_df", meta[meta["id"].isin(keep)][["id", "source_id"]]
                 .rename(columns={"id": "metric_id"}))
    limited_rows = [(mid, kt) for sid, kts in gate.cantons.items()
                    for mid in meta.loc[meta["source_id"] == sid, "id"] for kt in kts]
    con.register("kt_ok", pd.DataFrame(limited_rows or [("", "")], columns=["metric_id", "kanton"]))
    mem = membership()[["bfs_nr", "kanton"]].assign(unit_id=lambda d: d["bfs_nr"].astype(str))
    con.register("mem_kt", mem[["unit_id", "kanton"]])
    ref = REFERENCE_DATE.isoformat()
    # Unlimited metrics: every row except unallocated / pseudo units (as on the site). Cantonally
    # limited metrics: only the municipalities and the canton rows of the cleared cantons.
    con.execute(f"""COPY (
        WITH base AS (SELECT a.*, k.source_id FROM read_parquet('{src}') a JOIN keep_df k USING (metric_id)
                      WHERE a.level NOT IN ('unallocated', 'pseudo')),
             limited AS (SELECT DISTINCT metric_id FROM kt_ok WHERE metric_id <> '')
        SELECT '{ref}' AS vintage, unit_id, level, metric_id, period, value, status, precision, provenance,
               source_id, n_units, n_missing, note
        FROM (
          SELECT b.* FROM base b WHERE b.metric_id NOT IN (SELECT metric_id FROM limited)
          UNION ALL
          SELECT b.* FROM base b JOIN mem_kt g ON b.level = 'gemeinde' AND b.unit_id = g.unit_id
            JOIN kt_ok k ON k.metric_id = b.metric_id AND k.kanton = g.kanton
          UNION ALL
          SELECT b.* FROM base b JOIN kt_ok k ON b.level = 'kanton' AND b.metric_id = k.metric_id
                                            AND b.unit_id = k.kanton)
        ORDER BY metric_id, level, unit_id, period
    ) TO '{dst}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 500000)""")
    return con.execute(f"SELECT count(*) FROM read_parquet('{dst}')").fetchone()[0]


def source_rows(gate: Gate, meta: pd.DataFrame, kept: set[str]) -> list[dict]:
    from pipeline.build.web import public_text
    sub = meta[meta["id"].isin(kept)]
    used = set(sub["source_id"].unique())
    if "credit_source" in sub:
        used |= set(sub["credit_source"].dropna().unique())
    rows = []
    for sid in sorted(used):
        m = gate.sources.get(sid, {})
        r = gate.review.get(sid, {})
        rows.append({
            "source_id": sid, "title": public_text(m.get("title")), "publisher": public_text(m.get("publisher")),
            "url": m.get("url"), "licence": public_text(m.get("license") or m.get("licence")),
            "attribution": public_text(m.get("attribution")), "vintage": public_text(m.get("vintage")),
            "years": m.get("years"),
            "licence_review": r.get("status") or "automatic (open terms stated in meta.yaml)",
            "cleared_cantons": " ".join(gate.cantons.get(sid, [])),
            "noncommercial": "yes" if sid in gate.noncommercial else "no",
            "licence_evidence": public_text(r.get("evidence")) or "",
        })
    return rows


def metric_rows(meta: pd.DataFrame, kept: list[str], gate: Gate, srcs: dict[str, dict]) -> list[dict]:
    cols = ["id", "theme", "label_en", "label_de", "unit", "decimals", "direction", "aggregation", "kind",
            "precision", "coverage", "native_level", "source_id", "credit_source", "description", "source_note"]
    m = meta.drop_duplicates("id").set_index("id", drop=False)
    rows = []
    for mid in sorted(kept):
        r = {c: ("" if pd.isna(m.at[mid, c]) else m.at[mid, c]) if c in m.columns else "" for c in cols}
        r["metric_id"] = r.pop("id")
        sid = r["source_id"]
        s = srcs.get(sid) or {}
        cr = srcs.get(r["credit_source"]) if r["credit_source"] else None
        r["cantons_released"] = " ".join(gate.cantons.get(sid, []))
        r["licence"] = s.get("licence", "")
        r["attribution"] = " | ".join(x for x in (s.get("attribution"), cr and cr.get("attribution")) if x)
        r["noncommercial"] = "yes" if sid in gate.noncommercial else "no"
        r["vintage"] = "reference state " + REFERENCE_DATE.isoformat()
        rows.append(r)
    return rows


def write_csv(path: Path, rows: list[dict], first: list[str] | None = None) -> None:
    cols = list(first or [])
    for r in rows:
        cols += [k for k in r if k not in cols]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def write_boundaries(dst: Path) -> dict[str, int]:
    import geopandas as gpd
    import pyogrio
    srcf = interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg")
    if not srcf.exists():
        raise SystemExit(f"{srcf} missing: run `make geometry` first")
    layers = [str(r[0]) for r in pyogrio.list_layers(srcf)]
    canton = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    cname = dict(zip(canton["canton"].astype(str), canton["name"]))
    counts = {}
    for lay in layers:
        g = gpd.read_file(srcf, layer=lay)
        g["id"] = g["id"].astype(str)
        if lay == "kanton" and "name" not in g.columns:
            g["name"] = g["id"].map(cname)
        g = g[[c for c in ("id", "name", "canton", "district", "geometry") if c in g.columns]]
        g.to_file(dst, layer=lay, driver="GPKG")
        counts[lay] = len(g)
    return counts


README = """# ATLAS data release

Open data on Swiss municipalities, districts, cantons and regions, on the boundaries of the
reference state {ref}. Built by the ATLAS pipeline (https://github.com/joakim-hersche/Atlas) from
open sources. Every value traces to a downloaded source file; nothing is invented.

## Files

| File | Contents |
|---|---|
| `observations.parquet` | {n_obs:,} rows, long table: one row per unit x metric x period |
| `metrics.csv` | {n_metrics} metrics with label, unit, aggregation rule, precision, coverage, source, licence, attribution |
| `sources.csv` | {n_sources} sources with licence, attribution, review status and the evidence for it |
| `boundaries.gpkg` | boundary layers (EPSG:2056, LV95): {layers} |
| `excluded.csv` | what the site may show but this release leaves out, and why |

### observations.parquet

- `vintage`: municipality state all values are expressed on.
- `unit_id`: BFS number for `gemeinde`, district number for `bezirk`, canton code for `kanton`, the
  level's code for other levels, `CH` for `schweiz`.
- `level`, `metric_id` (join to `metrics.csv`), `period` (`2025`, survey period `2020/25`, pooled
  `2022-2024`, month `2026-03`).
- `value`: empty unless `status` is `ok`. `status`: `ok`, `suppressed`, `not_published`,
  `not_covered`, `not_applicable`, `no_data`.
- `precision`: `exact`, `survey`, `modelled`, `boundary_estimate`.
- `provenance`: `source_current_state`, `aggregated_mergers`, `reprojected_weighted`, `native`, `aggregated`.
- `source_id`; `n_units` and `n_missing` (municipalities behind an aggregate, and how many lacked a
  value); `note`.

Historical values are reprojected onto the reference boundaries: mergers are exact, splits use
population weights and are marked `boundary_estimate`. Rates are recomputed from summed numerators and
denominators; medians and indices that cannot be re-aggregated exist at their native level only.

### boundaries.gpkg

Layers `gemeinde`, `bezirk`, `kanton` and the BFS analysis levels (`grossregion`, `sprachgebiet`,
`agglomeration`, `arbeitsmarktgebiet`, `stadt_land`): full-resolution generalised boundaries (G1).
`id` joins to `unit_id` of the matching `level`. Lakes and territory not assigned to a municipality are
not part of any unit.

## Licences and attribution

A source is released only where its terms allow redistribution; the terms and the evidence are in
`sources.csv`. Most data are published by Swiss federal offices under "free use, source must be cited"
(OPEN BY, `terms_by` on opendata.swiss), CC BY or CC0. Cantonal sources are included only for the
cantons whose terms were checked (`cleared_cantons` in `sources.csv`).

**When you use this data, cite the publisher of each metric (`attribution` in `metrics.csv`) and ATLAS
as the compiler.** Values on reference boundaries are ATLAS derivations and can differ from the
published figures.

Boundaries: {boundary_attr}. Terms:
https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices (reference required).

{noncomm}
### Left out

Sources whose licence is not cleared: {ex_src}. Partly cleared sources (cantons, single metrics) and
held-back metrics are listed in `excluded.csv`.

The ATLAS code is in the repository above. This release carries no warranty.

## Sources included

{source_list}
"""


def write_readme(dst: Path, n_obs: int, metrics: list[dict], sources: list[dict], layers: dict,
                 gate: Gate, excluded_rows: list[dict]) -> None:
    nc = [s for s in sources if s["noncommercial"] == "yes"]
    noncomm = ""
    if nc:
        noncomm = ("### Non-commercial use only\n\nThese sources may be redistributed with attribution for "
                   "non-commercial use only (`noncommercial = yes` in `metrics.csv` and `sources.csv`):\n\n"
                   + "\n".join(f"- `{s['source_id']}`: {gate.noncommercial[s['source_id']]}" for s in nc) + "\n")
    ex_src = ", ".join(f"`{r['item']}`" for r in excluded_rows if r["kind"] == "source") or "none"
    lst = "\n".join(f"- **{s['source_id']}**: {s['title']} ({s['publisher']}). Licence: {s['licence']}. "
                    f"Attribution: {s['attribution']}" for s in sources)
    dst.write_text(README.format(
        ref=REFERENCE_DATE.isoformat(), n_obs=n_obs, n_metrics=len(metrics), n_sources=len(sources),
        layers=", ".join(f"`{k}` ({v})" for k, v in layers.items()), boundary_attr=BOUNDARY_ATTRIBUTION,
        noncomm=noncomm, ex_src=ex_src, source_list=lst), encoding="utf-8")


def excluded_rows(gate: Gate, why: dict) -> list[dict]:
    ex = [{"kind": "source", "item": sid, "reason": r} for sid, r in sorted(gate.excluded.items())]
    ex += [{"kind": "metric", "item": mid, "reason": r} for mid, r in sorted(why.items())
           if not any(r == f"source {sid}: {gate.excluded[sid]}" for sid in gate.excluded)]
    for sid, d in gate.dropped_cantons.items():
        ex += [{"kind": "canton", "item": f"{sid}:{kt}", "reason": r} for kt, r in d.items()]
    for sid, kts in gate.cantons.items():
        ex.append({"kind": "partial source", "item": sid, "reason": "released only for " + " ".join(kts)})
    return ex


def run(dest: Path | None = None) -> dict:
    dest = Path(dest or RELEASE_DIR)
    meta = load_metrics()
    gate = build_gate(load_sources(), _load_yaml(PIPELINE_DIR / "licence_review.yaml"),
                      _load_yaml(PIPELINE_DIR / "release_flags.yaml"))
    keep, why = select_metrics(meta, gate)
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    n_obs = write_observations(keep, meta, gate, dest / "observations.parquet")
    srows = source_rows(gate, meta, set(keep))
    mrows = metric_rows(meta, keep, gate, {r["source_id"]: r for r in srows})
    write_csv(dest / "metrics.csv", mrows, ["metric_id", "theme", "label_en", "label_de", "unit", "decimals"])
    write_csv(dest / "sources.csv", srows)
    layers = write_boundaries(dest / "boundaries.gpkg")
    ex = excluded_rows(gate, why)
    write_csv(dest / "excluded.csv", ex, ["kind", "item", "reason"])
    write_readme(dest / "README.md", n_obs, mrows, srows, layers, gate, ex)
    return {"dest": dest, "observations": n_obs, "metrics": len(mrows), "sources": len(srows),
            "excluded_sources": gate.excluded, "excluded_metrics": len(why), "layers": layers}


if __name__ == "__main__":
    res = run()
    for f in sorted(res["dest"].iterdir()):
        print(f"{f.stat().st_size / 1048576:8.2f} MB  {f.name}")
    print({k: v for k, v in res.items() if k != "dest"})
