"""Series-break markers: YAML schema, evidence quotes, placement on a metric's periods, propagation."""
import json

import pandas as pd
import pytest

from pipeline.build import series_breaks as sb
from pipeline.common import ROOT
from pipeline.harmonize.schema import SOURCES_DIR, load_metrics


def test_yaml_is_valid():
    cfg = sb.load()
    errs = sb.validate(cfg, set(load_metrics()["id"]), {p.name for p in SOURCES_DIR.iterdir() if p.is_dir()})
    assert errs == []
    assert len(cfg["breaks"]) >= 10 and cfg["rejected"]


def test_every_quote_is_in_its_cached_file():
    problems, skipped = sb.check_evidence(sb.load())
    assert problems == []
    if skipped:
        pytest.skip(f"{len(skipped)} evidence files not cached here (data/raw is not in git)")


def test_validate_catches_mistakes():
    bad = {"breaks": [
        {"id": "x", "period": "2011/12", "metrics": ["nope"], "note_en": "a", "note_de": "b", "note_fr": "c",
         "evidence": [{"url": "https://example.org"}], "colour": "red"},
        {"id": "x", "period": "2011", "note_en": "a", "note_de": "b", "evidence": [{"ref": "r"}]},
    ]}
    errs = " | ".join(sb.validate(bad, {"pop_total"}))
    for s in ("period must be", "unknown metric 'nope'", "unknown keys ['colour']", "needs the cached file",
              "duplicate id", "missing ['note_fr']", "needs metrics or source", "must quote the publisher"):
        assert s in errs, s


def test_period_end_shapes():
    assert sb.period_end("2025") == (2025, 0)
    assert sb.period_end("2024-07") == (2024, 7)
    assert sb.period_end("2009-2011") == (2011, 0)
    assert sb.period_end("1979/85") == (1985, 0)
    assert sb.period_end("1992/97") == (1997, 0)
    assert sb.period_end("2004/09") == (2009, 0)
    assert sb.period_end("2020-09-27#6320") == (2020, 9)


def test_place():
    years = [str(y) for y in range(1981, 2026)]
    assert sb.place("2011", years) == "2011"
    assert sb.place("2011", [str(y) for y in range(2011, 2026)]) is None   # nothing before the break
    assert sb.place("2011", ["1990", "2000", "2017"]) == "2017"            # first period on the new basis
    assert sb.place("2017", ["1990", "2000", "2017", "2018"]) == "2017"
    windows = [f"{y}-{y + 2}" for y in range(2005, 2022)]
    assert sb.place("2011", windows) == "2009-2011"                         # first window with new-basis years
    months = ["2024-05", "2024-06", "2024-07", "2024-08"]
    assert sb.place("2024-07", months) == "2024-07"
    assert sb.place("2018", ["2017-11", "2017-12", "2018-01"]) == "2018-01"
    assert sb.place("2030", years) is None


def _meta():
    rows = [("a", "s1", "base", "sum"), ("b", "s2", "base", "sum"),
            ("r", "s1", "derived", "ratio:a/b*100"), ("rr", "s3", "derived", "ratio:r+b/b"),
            ("pl", "s1", "derived", "pooled:a/b*100:3"), ("w", "s1", "derived", "weighted_mean:b"),
            ("c", "s1", "derived", "change:a:10"), ("e", "s4", "base", "sum")]
    return pd.DataFrame(rows, columns=["id", "source_id", "kind", "aggregation"]).set_index("id")


def test_resolve_propagates_to_ratios_only():
    cfg = {"breaks": [{"id": "x", "period": "2011", "metrics": ["a"], "note_en": "E", "note_de": "D", "note_fr": "F",
                       "evidence": []}]}
    yrs = [str(y) for y in range(2005, 2020)]
    periods = {"a": yrs, "b": yrs, "r": yrs, "rr": yrs, "pl": [f"{y}-{y + 2}" for y in range(2005, 2018)], "w": yrs, "c": yrs}
    out, rows = sb.resolve(cfg, _meta(), periods)
    assert set(out) == {"a", "r", "rr", "pl"}
    assert out["a"] == {"2011": {"label_en": "E", "label_de": "D", "label_fr": "F"}}
    assert list(out["pl"]) == ["2009-2011"]
    assert rows[0]["source"] == "s1" and rows[0]["metrics"] == ["a", "pl", "r", "rr"]
    cfg["breaks"][0]["propagate"] = False
    out, _ = sb.resolve(cfg, _meta(), periods)
    assert set(out) == {"a"}


def test_resolve_source_exclude_and_merge():
    cfg = {"breaks": [
        {"id": "x", "period": "2011", "source": "s1", "exclude": ["pl", "r"], "propagate": False,
         "note_en": "one", "note_de": "eins", "note_fr": "un", "evidence": []},
        {"id": "y", "period": "2011", "metrics": ["a"], "propagate": False,
         "note_en": "two", "note_de": "zwei", "note_fr": "deux", "evidence": []}]}
    yrs = [str(y) for y in range(2005, 2020)]
    out, _ = sb.resolve(cfg, _meta(), {m: yrs for m in _meta().index})
    assert set(out) == {"a", "w", "c"}
    assert out["a"]["2011"]["label_de"] == "eins · zwei"


def test_resolve_from_notes():
    cfg = {"breaks": [{"id": "n", "from_note": {"source": "s4", "regex": r"^step ([+-]\d+) %"},
                       "note_en": "step {pct} %", "note_de": "Stufe {pct} %", "note_fr": "saut {pct} %", "evidence": []}]}
    ms = ["2024-01", "2024-02", "2024-03"]
    notes = [("e", "2024-02", "step +12 % against the previous month"), ("e", "2024-01", "step -5 %"),
             ("a", "2024-02", "step +3 %"), ("e", "2024-03", "something else")]
    out, rows = sb.resolve(cfg, _meta(), {"e": ms, "a": ms}, notes)
    assert out == {"e": {"2024-02": {"label_en": "step +12 %", "label_de": "Stufe +12 %", "label_fr": "saut +12 %"}}}
    assert rows[0]["period"] == "2024-02" and rows[0]["metrics"] == ["e"]


def test_shipped_metrics_json_has_the_breaks():
    p = ROOT / "data" / "out" / "web" / "metrics.json"
    if not p.exists():
        pytest.skip("no web build here")
    cat = {m["id"]: m for m in json.loads(p.read_text(encoding="utf-8"))}
    if not any(m.get("series_breaks") for m in cat.values()):
        pytest.skip("web build predates series breaks")
    assert "2011" in cat["bil_pop_jan"]["series_breaks"]
    assert "2023" in cat["nrw_share_mitte"]["series_breaks"]
    assert {"2018", "2025"} <= set(cat["mfz_cars_per_1000"]["series_breaks"])   # propagated to the ratio
    assert "nrw_share_bloc_right" not in cat or not cat["nrw_share_bloc_right"].get("series_breaks")
    for m in cat.values():
        for per, v in (m.get("series_breaks") or {}).items():
            assert per in m["periods"][1:], (m["id"], per)
            assert v["label_en"] and v["label_de"] and v["label_fr"]
