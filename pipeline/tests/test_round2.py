"""Audit round 2 (docs/audit_round2.md, decisions D40–D42): aggregation helpers, small-number rules and
the D38 map curation."""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import pytest

from pipeline.build import curation
from pipeline.build.metrics import native_state_date, nearest_periods, period_year
from pipeline.common import out_path


# ---- M5: nearest-period weights -------------------------------------------------------------------
def test_period_year():
    assert period_year("2025") == 2025
    assert period_year("2022-2024") == 2024
    assert period_year("1991-2020") == 2020
    assert period_year("2026-10") == 2026
    assert period_year("2020/25") == 2020
    assert period_year("abc") is None


def test_nearest_periods():
    m = nearest_periods(["1991-2020", "2026-10", "2015", "x"], ["2010", "2015", "2024", "2025"])
    assert m == {"1991-2020": "2024", "2026-10": "2025", "2015": "2015"}


# ---- M2: state of a published row -----------------------------------------------------------------
def test_native_state_date():
    # a value 'for 2025' published with the default vintage is on the 2025 boundaries (Moutier still in BE)
    assert native_state_date("2026-01-01", "2025") == dt.date(2025, 12, 31)
    # a connector naming an older state is trusted
    assert native_state_date("2023-12-31", "2016") == dt.date(2023, 12, 31)
    # a 2026 value is on the reference state
    assert native_state_date("2026-01-01", "2026-10") == dt.date(2026, 1, 1)


# ---- D38: the coverage rule -----------------------------------------------------------------------
RULE = {"show": {"min_unit_share": 0.8, "min_pop_share": 0.8},
        "note": {"min_unit_share": 0.25, "min_pop_share": 0.5, "min_units": 20}, "small_level_units": 20}


@pytest.mark.parametrize("n,N,pop,verdict", [
    (2110, 2110, 1.0, "show"),
    (1700, 2110, 0.85, "show"),
    (1700, 2110, 0.70, "note"),
    (600, 2110, 0.55, "note"),        # 28 % of units, 55 % of residents
    (180, 2110, 0.49, "hide"),        # city tax burden: 179–180 cities, 49 % of residents
    (30, 2110, 0.05, "hide"),         # land price
    (25, 26, 0.99, "show"),           # canton level has 26 units: the general rule applies
    (3, 3, 1.0, "show"),              # small level, complete
    (1, 3, 0.4, "hide"),              # tertiary education by urban/rural: 1 of 3
    (8, 9, 0.95, "hide"),             # municipality types: a single gap hides a small level
    (0, 144, 0.0, "hide"),
])
def test_rule_verdict(n, N, pop, verdict):
    assert curation.rule_verdict(n, N, pop, RULE)[0] == verdict


def test_decide_overrides():
    cfg = {"rule": RULE,
           "levels": {"stadt_land": {"hide": True, "except": ["^vote_.*"], "reason": "three units"}},
           "metrics": {"dup": {"hide": True, "reason": "duplicate"},
                       "den": {"maps": False, "reason": "denominator"},
                       "re:haz_.*": {"only_levels": ["gemeinde"], "reason": "19 of 26 cantons"},
                       "com": {"levels": {"gemeinde": {"v": "hide", "reason": "identical"}}}}}
    assert curation.decide("dup", "gemeinde", 2110, 2110, 1.0, cfg)[:2] == ("hidden", "duplicate")
    assert curation.decide("den", "kanton", 26, 26, 1.0, cfg)[0] == "hide"
    assert curation.decide("haz_share_high", "gemeinde", 1595, 2110, 0.8, cfg)[0] in ("show", "note")
    assert curation.decide("haz_share_high", "kanton", 19, 26, 0.8, cfg)[0] == "hide"
    assert curation.decide("com", "gemeinde", 2110, 2110, 1.0, cfg)[0] == "hide"
    assert curation.decide("com", "kanton", 26, 26, 1.0, cfg)[0] == "show"
    # the urban/rural level is hidden even when complete, except for votes
    assert curation.decide("edu_share_tertiary", "stadt_land", 3, 3, 1.0, cfg)[0] == "hide"
    assert curation.decide("vote_yes_share", "stadt_land", 3, 3, 1.0, cfg)[0] == "show"


def test_apply_keeps_profile_levels_and_hidden_levels():
    e = {"id": "x", "levels": ["gemeinde", "kanton", "schweiz"], "unavailable_levels": None}
    v = {"gemeinde": ("hide", "30 of 2,110", "rule"), "kanton": ("show", "26 of 26", "rule")}
    curation.apply(e, v, ["gemeinde", "kanton", "schweiz"])
    assert e["levels"] == ["kanton", "schweiz"]
    assert e["profile_levels"] == ["gemeinde", "kanton", "schweiz"]
    assert "30 of 2,110" in e["unavailable_levels"]["gemeinde"]
    # a hidden metric keeps its levels (confidence-interval companions are looked up through them)
    h = {"id": "y_ci", "levels": ["bezirk", "schweiz"], "unavailable_levels": None}
    curation.apply(h, {"bezirk": ("hidden", "confidence interval", "file")}, ["bezirk", "schweiz"])
    assert h["hidden"] and h["levels"] == ["bezirk", "schweiz"]


def test_curation_file():
    cfg = curation.load()
    assert cfg["rule"]["show"]["min_unit_share"] == 0.8
    assert len(cfg["featured"]) == 15
    for k, v in (cfg.get("metrics") or {}).items():
        ok = v.get("reason") or all(isinstance(x, dict) and x.get("reason") for x in (v.get("levels") or {}).values())
        assert ok and (v.get("reason") or v.get("levels")), f"{k}: every explicit decision needs a reason"


# ---- built output (skipped before the first build) ------------------------------------------------
def _metrics():
    p = out_path("web", "metrics.json")
    if not p.exists():
        pytest.skip("web output not built")
    return {m["id"]: m for m in json.loads(p.read_text(encoding="utf-8"))}


def test_built_curation_enforced():
    ms = _metrics()
    if not any("profile_levels" in m for m in ms.values()):
        pytest.skip("web output built before D38")
    for m in ms.values():
        if m.get("hidden"):
            continue      # never offered; its levels are kept for companion lookups
        for lvl, c in (m.get("curation") or {}).items():
            if c["v"] == "hide":
                assert lvl not in m["levels"], (m["id"], lvl)
                assert lvl in (m.get("unavailable_levels") or {}), (m["id"], lvl)
    assert ms["en_ecar_share"]["levels"] in (["schweiz"], [])         # M7: BFS share is the one on maps
    assert "gemeinde" in ms["mfz_bev_share"]["levels"]
    assert ms["haz_share_high_medium"]["levels"] in (["gemeinde"], ["gemeinde", "schweiz"])  # M8
    assert "stadt_land" not in ms["edu_share_tertiary"]["levels"]      # D38 owner example


def test_built_featured_maps_available():
    p = out_path("web", "featured.json")
    if not p.exists():
        pytest.skip("featured.json not built")
    maps = json.loads(p.read_text(encoding="utf-8"))["maps"]
    assert len(maps) == 15
    missing = [f"{f['metric']}@{f['level']}" for f in maps if not f["available"]]
    assert not missing, missing


def test_built_aggregates_not_blank():
    """M1: one suppressed municipality no longer blanks canton totals (STATENT 2024: 5315 in TI)."""
    from pipeline.common import interim_path
    import duckdb
    p = interim_path("metrics_all.parquet")
    if not p.exists():
        pytest.skip("metrics not built")
    r = duckdb.sql(f"""SELECT unit_id, status FROM read_parquet('{p}') WHERE metric_id = 'ent_jobs'
                       AND level = 'kanton' AND period = '2024' AND unit_id IN ('TI', 'VD', 'VS')""").df()
    if r.empty:
        pytest.skip("no STATENT 2024")
    assert (r["status"] == "ok").all(), r


# ---- M9: generic small-number rule ----------------------------------------------------------------
def test_auto_reliability_rule():
    from pipeline.build.web import _auto_rule
    meta = pd.DataFrame([
        {"id": "a_share", "kind": "derived", "aggregation": "ratio:a/b*100", "unit": "%", "native_level": "gemeinde"},
        {"id": "a_rate", "kind": "derived", "aggregation": "ratio:a/pop_total*1000", "unit": "per 1000", "native_level": "gemeinde"},
        {"id": "a_mean", "kind": "derived", "aggregation": "ratio:chf/b", "unit": "CHF", "native_level": "gemeinde"},
        {"id": "a_density", "kind": "derived", "aggregation": "ratio:a/area", "unit": "per km²", "native_level": "gemeinde"},
        {"id": "a", "kind": "base", "aggregation": "sum", "unit": "persons", "native_level": "gemeinde"},
        {"id": "b", "kind": "base", "aggregation": "sum", "unit": "taxpayers", "native_level": "gemeinde"},
        {"id": "chf", "kind": "base", "aggregation": "sum", "unit": "CHF", "native_level": "gemeinde"},
        {"id": "pop_total", "kind": "base", "aggregation": "sum", "unit": "persons", "native_level": "gemeinde"},
        {"id": "area", "kind": "base", "aggregation": "sum", "unit": "ha", "native_level": "gemeinde"},
    ]).set_index("id")
    cfg = {"auto": {"share": {"min_base": 100}, "rate": {"min_base": 1000}, "mean": {"min_base": 500}}}
    assert _auto_rule("a_share", meta, cfg)["min_base"] == 100
    assert _auto_rule("a_rate", meta, cfg)["min_base"] == 1000
    r = _auto_rule("a_mean", meta, cfg)
    assert r["min_base"] == 500 and r["base"] == "b" and r["count"] is None
    assert _auto_rule("a_density", meta, cfg) is None      # area denominators are exact
    assert _auto_rule("a", meta, cfg) is None              # base metrics need an explicit rule
