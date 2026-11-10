"""Build the small sample dataset in web/sample-data/ from a full pipeline build (data/out/).

    uv run python scripts/make_sample_data.py

web/sample-data/ has the same layout as data/out/ (geo/, web/), so `npm run dev` works right after
cloning, without running the pipeline: web/scripts/copy-data.mjs falls back to it when data/out/web
is missing. Nothing is invented: every value is copied from the built files, restricted to

- a handful of national, fully open metrics (see METRICS; each source must pass the licence gate of
  pipeline/licence_review.yaml and must not be flagged non-commercial in pipeline/release_flags.yaml),
- the levels gemeinde, bezirk, kanton and schweiz (all 2,110 municipalities),
- the geometry already shipped to the site (no extra simplification).
Reach, the other themes and the other levels are left out; the app treats them as optional.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.release import PIPELINE_DIR, _load_yaml, build_gate, load_sources  # noqa: E402

OUT = ROOT / "data" / "out"
DEST = ROOT / "web" / "sample-data"
LEVELS = ["gemeinde", "bezirk", "kanton", "schweiz"]
GEO = ["gemeinde", "bezirk", "kanton", "lakes"]
METRICS = ["pop_total", "pop_change_10y", "share_age_65plus", "share_foreign", "hh_avg_size", "geo_pop_density",
           "geo_elev_mean", "vac_rate"]
SERIES = ["pop_total", "share_foreign", "vac_rate"]     # time series (year slider); the others show the latest year
# sources of the lookup files that stay whole (search, identity, history, neighbours)
LOOKUP_SOURCES = {"geo_identity", "swisstopo_plz", "wikidata_identity", "wikidata_cantons", "bfs_hist_boundaries"}
WHOLE = ["units.json", "search.json", "identity.json", "history.json", "neighbours.json"]


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(obj, p: Path) -> int:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return p.stat().st_size


def main() -> None:
    web = OUT / "web"
    if not (web / "metrics.json").exists():
        raise SystemExit("data/out/web is missing: run `make data` first")
    gate = build_gate(load_sources(), _load_yaml(PIPELINE_DIR / "licence_review.yaml"),
                      _load_yaml(PIPELINE_DIR / "release_flags.yaml"))
    all_metrics = {m["id"]: m for m in load(web / "metrics.json")}
    chosen = [m for m in METRICS if m in all_metrics]
    for mid in chosen:
        m, sid = all_metrics[mid], all_metrics[mid]["source"]
        assert sid not in gate.excluded and sid not in gate.noncommercial and sid not in gate.cantons, \
            f"{mid}: source {sid} is not fully open for redistribution"
        assert sid not in gate.metric_only or mid in gate.metric_only[sid], f"{mid}: not cleared"
        assert m["coverage"] == "national" and m["file"] == "core", f"{mid}: expected a national core metric"

    shutil.rmtree(DEST, ignore_errors=True)
    total = 0
    (DEST / "geo").mkdir(parents=True, exist_ok=True)
    for g in GEO:
        shutil.copyfile(OUT / "geo" / f"{g}.topojson", DEST / "geo" / f"{g}.topojson")
        total += (DEST / "geo" / f"{g}.topojson").stat().st_size

    metas = []
    for mid in chosen:
        m = dict(all_metrics[mid])
        m["levels"] = [lv for lv in m["levels"] if lv in LEVELS]
        metas.append(m)
    total += dump(metas, DEST / "web" / "metrics.json")

    used = {m["source"] for m in metas} | LOOKUP_SOURCES
    srcs = [s for s in load(web / "sources.json") if s["source_id"] in used]
    total += dump(srcs, DEST / "web" / "sources.json")

    units = [u for u in load(web / "units.json") if u["level"] in LEVELS]
    total += dump(units, DEST / "web" / "units.json")
    keep_ids = {(u["level"], u["id"]) for u in units}
    for name in ("search.json", "identity.json", "history.json", "neighbours.json"):
        d = load(web / name)
        if name == "search.json":
            d["units"] = [u for u in d["units"] if (u[1], u[0]) in keep_ids]
        elif name == "neighbours.json":
            d["levels"] = {lv: v for lv, v in d["levels"].items() if lv in LEVELS}
        total += dump(d, DEST / "web" / name)

    for lv in LEVELS:
        f = web / "latest" / lv / "core.json"
        if not f.exists():
            continue
        d = load(f)
        d["metrics"] = {k: v for k, v in d["metrics"].items() if k in chosen}
        total += dump(d, DEST / "web" / "latest" / lv / "core.json")

    for mid in [m for m in chosen if m in SERIES]:
        f = web / "series" / f"{mid}.json"
        if f.exists():
            d = load(f)
            if isinstance(d.get("levels"), dict):
                d["levels"] = {lv: v for lv, v in d["levels"].items() if lv in LEVELS}
            total += dump(d, DEST / "web" / "series" / f"{mid}.json")

    print(f"sample data: {len(chosen)} metrics, {len(units)} units, {total / 1048576:.2f} MB in {DEST}")


if __name__ == "__main__":
    main()
