"""Review round 3 (data/pipeline fixes A1-A6): small-number base of sum denominators, ESTV normal-case
income metrics, translated pipeline texts and former municipality names in the search index."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from pipeline.common import out_path


# ---- A1 (D1): the small-number base is the whole denominator ------------------------------------------
def _meta(rows):
    return pd.DataFrame(rows).set_index("id")


def test_auto_rule_uses_every_denominator_term():
    from pipeline.build.web import _auto_rule
    meta = _meta([
        {"id": "vote_yes_share", "kind": "derived", "aggregation": "ratio:vote_yes/vote_yes+vote_no*100", "unit": "%",
         "native_level": "gemeinde"},
        {"id": "vote_yes", "kind": "base", "aggregation": "sum", "unit": "votes", "native_level": "gemeinde"},
        {"id": "vote_no", "kind": "base", "aggregation": "sum", "unit": "votes", "native_level": "gemeinde"},
        {"id": "x_rate", "kind": "derived", "aggregation": "ratio:x/bil_pop_jan+bil_pop_dec*2000", "unit": "per 1,000 residents",
         "native_level": "gemeinde"},
        {"id": "x", "kind": "base", "aggregation": "sum", "unit": "persons", "native_level": "gemeinde"},
        {"id": "bil_pop_jan", "kind": "base", "aggregation": "sum", "unit": "persons", "native_level": "gemeinde"},
        {"id": "bil_pop_dec", "kind": "base", "aggregation": "sum", "unit": "persons", "native_level": "gemeinde"},
        {"id": "y_share", "kind": "derived", "aggregation": "ratio:x/x+area*100", "unit": "%", "native_level": "gemeinde"},
        {"id": "area", "kind": "base", "aggregation": "sum", "unit": "ha", "native_level": "gemeinde"},
    ])
    cfg = {"auto": {"share": {"min_base": 100}, "rate": {"min_base": 1000}, "mean": {"min_base": 500}}}
    r = _auto_rule("vote_yes_share", meta, cfg)
    assert r["base"] == "vote_yes+vote_no" and r["min_base"] == 100
    # a mean population (1 January + 31 December) / 2 is compared as residents
    r = _auto_rule("x_rate", meta, cfg)
    assert r["base"] == "mean:bil_pop_jan+bil_pop_dec" and r["min_base"] == 1000
    # any non-count term (area) means no rule
    assert _auto_rule("y_share", meta, cfg) is None


def test_listed_rule_uses_every_denominator_term():
    from pipeline.build.web import _reliability
    meta = _meta([{"id": "s", "kind": "derived", "aggregation": "ratio:a/a+b*100", "unit": "%", "native_level": "gemeinde"}])
    r = _reliability("s", meta, {"defaults": {"min_base": 100}, "metrics": {"s": {"count": None}}})
    assert r["base"] == "a+b"


def test_vote_yes_share_flags_on_yes_plus_no():
    """Shipped data: the yes share is flagged where yes + no < 100 (about 117 municipalities), not where the
    yes votes alone are < 100 (864 before the fix)."""
    p = out_path("web", "metrics.json")
    if not p.exists():
        pytest.skip("web data not built")
    meta = {m["id"]: m for m in json.loads(p.read_text(encoding="utf-8"))}
    m = meta.get("vote_yes_share")
    if not m or not m.get("reliability"):
        pytest.skip("no vote_yes_share")
    assert m["reliability"]["base"] == "vote_yes+vote_no"
    col = None
    for f in out_path("web", "latest", "gemeinde").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "vote_yes_share" in d["metrics"]:
            col = d["metrics"]["vote_yes_share"]
    assert col is not None
    n = sum(1 for b in (col.get("f") or {}).values() if b & 1)
    assert 50 <= n <= 300, n
