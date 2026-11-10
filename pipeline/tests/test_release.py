"""Licence gate of the public data release (no data needed)."""
import pandas as pd

from pipeline.release import build_gate, select_metrics

SOURCES = {
    "open_src": {"license": "OPEN-BY – open use, the source must be provided"},
    "unclear_src": {"license": "licence not yet confirmed (UNVERIFIED)"},
    "blocked_src": {"license": "OPEN-BY"},
    "partial_src": {"license": "Per publisher (UNVERIFIED)"},
    "nc_src": {"license": "OPEN-BY"},
}
REVIEW = {
    "blocked_src": {"status": "blocked"},
    "partial_src": {"status": "cleared", "cantons": ["ZH", "NE", "BL"], "metrics": ["p_a"]},
}
FLAGS = {"drop_cantons": {"partial_src": {"NE": "permission needed"}}, "noncommercial": {"nc_src": "ask BFS"}}


def _meta():
    rows = [("o1", "open_src", "base", "sum"), ("u1", "unclear_src", "base", "sum"),
            ("b1", "blocked_src", "base", "sum"), ("p_a", "partial_src", "base", "sum"),
            ("p_b", "partial_src", "base", "sum"), ("n1", "nc_src", "base", "sum"),
            ("d_ok", "open_src", "derived", "ratio:o1/n1"), ("d_bad", "open_src", "derived", "ratio:o1/u1")]
    return pd.DataFrame(rows, columns=["id", "source_id", "kind", "aggregation"])


def test_gate_excludes_unclear_and_blocked_sources():
    gate = build_gate(SOURCES, REVIEW, FLAGS, has_ingest=lambda sid: True)
    assert set(gate.excluded) == {"unclear_src", "blocked_src"}


def test_review_overrides_and_flags():
    gate = build_gate(SOURCES, REVIEW, FLAGS, has_ingest=lambda sid: True)
    assert gate.cantons["partial_src"] == ["BL", "ZH"]            # NE dropped by the release flags
    assert gate.noncommercial == {"nc_src": "ask BFS"}


def test_select_metrics_applies_source_metric_and_derived_rules():
    gate = build_gate(SOURCES, REVIEW, FLAGS, has_ingest=lambda sid: True)
    keep, why = select_metrics(_meta(), gate)
    assert set(keep) == {"o1", "p_a", "n1", "d_ok"}
    assert "p_b" in why and "not cleared" in why["p_b"]           # per-metric clearance
    assert "d_bad" in why and "u1" in why["d_bad"]                # derived from a held-back metric
    assert "u1" in why and "b1" in why
