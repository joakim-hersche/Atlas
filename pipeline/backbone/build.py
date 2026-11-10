"""Build the backbone: register tables, split weights, crosswalk to the reference date, levels.

    uv run python -m pipeline.backbone.build
"""
from __future__ import annotations

import pandas as pd

from pipeline.backbone import levels, weights
from pipeline.backbone.crosswalk import build_crosswalk, load_backbone
from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.sources.bfs_agvch import parse as agvch


def run() -> None:
    print("register + mutations:", agvch.run())
    print("split weights:", weights.run())
    mv, pair = load_backbone()
    sw = pd.read_parquet(interim_path("backbone", "split_weights.parquet"))
    cw = build_crosswalk(mv, pair, sw, REFERENCE_DATE)
    p = interim_path("backbone", f"crosswalk_{REFERENCE_DATE.isoformat()}.parquet")
    cw.to_parquet(p, index=False)
    print("crosswalk:", p, len(cw), "rows")
    print("level membership:", levels.run())


if __name__ == "__main__":
    run()
