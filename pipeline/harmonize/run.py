"""Run all source connectors and assemble the harmonized observation table.

A connector is pipeline/sources/<source_id>/ingest.py with a function `observations()` returning
rows in the schema of pipeline.harmonize.schema.OBS_COLUMNS, plus metrics.yaml next to it.

    uv run python -m pipeline.harmonize.run            # all connectors
    uv run python -m pipeline.harmonize.run bfs_statpop  # selected connectors

Output: data/interim/observation/<source_id>.parquet and data/interim/observation.parquet,
and a run log in data/interim/observation/_runlog.json.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
import traceback

import pandas as pd

from pipeline.common import interim_path
from pipeline.harmonize.schema import SOURCES_DIR, load_metrics, validate_metrics, validate_observations


def connectors() -> list[str]:
    return sorted(p.parent.name for p in SOURCES_DIR.glob("*/ingest.py"))


def run(selected: list[str] | None = None) -> dict:
    metrics = load_metrics()
    errs = validate_metrics(metrics)
    if errs:
        raise ValueError("metrics.yaml problems:\n" + "\n".join(errs))
    log = {}
    for sid in selected or connectors():
        t0 = time.time()
        try:
            mod = importlib.import_module(f"pipeline.sources.{sid}.ingest")
            obs = mod.observations()
            ids = set(metrics.loc[metrics["source_id"] == sid, "id"])
            problems = validate_observations(obs, ids)
            obs.to_parquet(interim_path("observation", f"{sid}.parquet"), index=False)
            log[sid] = {"rows": len(obs), "metrics": int(obs["metric_id"].nunique()),
                        "problems": problems, "seconds": round(time.time() - t0, 1)}
        except Exception as e:  # keep going; the run log records the failure
            log[sid] = {"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-2000:],
                        "seconds": round(time.time() - t0, 1)}
        print(sid, {k: v for k, v in log[sid].items() if k != "trace"})
    parts = [pd.read_parquet(p) for p in sorted(interim_path("observation", "x").parent.glob("*.parquet"))]
    if parts:
        pd.concat(parts, ignore_index=True).to_parquet(interim_path("observation.parquet"), index=False)
    prev = interim_path("observation", "_runlog.json")
    allog = json.loads(prev.read_text()) if prev.exists() else {}
    allog.update(log)
    prev.write_text(json.dumps(allog, indent=1, default=str))
    return log


if __name__ == "__main__":
    run(sys.argv[1:] or None)
