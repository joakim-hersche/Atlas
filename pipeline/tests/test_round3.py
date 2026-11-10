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


# ---- A2 (D2, X2, X3, X13, D10): ESTV normal-case income metrics ---------------------------------------
def test_estv_normal_case_metrics_defined():
    from pipeline.harmonize.schema import load_metrics, validate_metrics
    m = load_metrics("estv_dbst").set_index("id")
    assert not validate_metrics(m.reset_index())
    agg = m["aggregation"].to_dict()
    assert agg["tax_np_mean_taxable_income_normal"] == "ratio:tax_np_taxable_income_normal_chf/tax_np_taxpayers_normal"
    assert agg["tax_np_share_no_federal_tax_normal"] == "ratio:tax_np_taxpayers_no_federal_tax_normal/tax_np_taxpayers_normal*100"
    assert agg["tax_np_federal_tax_per_taxpayer_normal"] == "ratio:tax_np_federal_tax_normal_chf/tax_np_taxpayers_normal"
    # the all-cases means say what they include
    for mid in ("tax_np_mean_taxable_income", "tax_np_mean_net_income", "tax_np_share_no_federal_tax",
                "tax_np_federal_tax_per_taxpayer"):
        assert "special cases (ESTV)" in m.loc[mid, "label_en"], mid
        assert "Sonderfälle" in m.loc[mid, "label_de"], mid
        assert isinstance(m.loc[mid, "description"], str) and "Art. 14" in m.loc[mid, "description"]
    from pipeline.sources.estv_dbst.ingest import METRICS
    assert METRICS["taxable_normal"] == "tax_np_taxable_income_normal_chf"


def test_median_definition_has_no_internal_references():
    from pipeline.harmonize.schema import load_metrics
    m = load_metrics("estv_median_income").set_index("id").loc["tax_np_median_taxable_income"]
    assert "pipeline/" not in m["description"] and "test" not in m["description"]
    assert m["native_note"].startswith("ATLAS estimate")


def test_headline_income_is_the_normal_case_mean():
    import yaml
    from pipeline.harmonize.schema import SOURCES_DIR
    hl = yaml.safe_load((SOURCES_DIR.parent / "headline_metrics.yaml").read_text(encoding="utf-8"))
    assert hl["headline"]["Income & tax"][0] == "tax_np_mean_taxable_income_normal"


def test_bellwald_normal_mean_matches_estv():
    """Bellwald (6052) 2023, ESTV file 500: taxable income 9,402,600 over 203 normal-case taxpayers = 46,318
    (all cases incl. 326 special cases: 22,297)."""
    from pipeline.common import interim_path
    p = interim_path("observation", "estv_dbst.parquet")
    if not p.exists():
        pytest.skip("estv_dbst not ingested")
    o = pd.read_parquet(p)
    o = o[(o["unit_id"] == "6052") & (o["period"] == "2023") & (o["level"] == "gemeinde")].set_index("metric_id")["value"]
    if "tax_np_taxable_income_normal_chf" not in o:
        pytest.skip("normal-case metrics not ingested yet")
    assert round(o["tax_np_taxable_income_normal_chf"] / o["tax_np_taxpayers_normal"]) == 46318
    assert round(o["tax_np_taxable_income_chf"] / o["tax_np_taxpayers"]) == 22297


def test_canton_median_note_is_not_published_value():
    p = out_path("web", "latest", "kanton")
    if not p.exists():
        pytest.skip("web data not built")
    for f in p.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        c = d["metrics"].get("tax_np_median_taxable_income")
        if c:
            assert not any(n.startswith("published value") for n in c.get("notes") or []), c.get("notes")
            assert any(n.startswith("ATLAS estimate") for n in c.get("notes") or [])
            return
    pytest.skip("median not shipped at canton level")
