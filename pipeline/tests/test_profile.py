"""Checks on the profile/search browser files (make profile). Skipped when they are not built."""
import json

import pytest

from pipeline.common import OUT

WEB = OUT / "web"
FILES = ["units.json", "search.json", "identity.json", "history.json", "neighbours.json"]
pytestmark = pytest.mark.skipif(not all((WEB / f).exists() for f in FILES),
                                reason="web files not built (make web profile)")


def _load(name):
    return json.loads((WEB / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def units():
    return _load("units.json")


@pytest.fixture(scope="module")
def gemeinden(units):
    return {u["id"] for u in units if u["level"] == "gemeinde"}


def test_search_covers_every_unit(units, gemeinden):
    s = _load("search.json")
    got = {(r[1], r[0]) for r in s["units"]}
    assert {("gemeinde", g) for g in gemeinden} <= got
    assert {(u["level"], u["id"]) for u in units} == got
    assert all(isinstance(r[2], str) and r[2] and isinstance(r[4], list) for r in s["units"])


def test_search_has_language_variants():
    by = {(r[1], r[0]): r for r in _load("search.json")["units"]}
    assert "Genf" in by[("gemeinde", "6621")][4]
    assert {"Genf", "Ginevra", "Geneva"} <= set(by[("kanton", "GE")][4])


def test_plz_maps_to_existing_gemeinden(gemeinden):
    plz = _load("search.json")["plz"]
    assert len(plz) > 3000
    for code, rows in plz.items():
        assert len(code) == 4 and code.isdigit()
        assert rows, code
        for gid, locality, share in rows:
            assert gid in gemeinden, (code, gid)
            assert locality and 0 < share <= 100
    assert plz["8001"][0][0] == "261"


def test_identity_ids(gemeinden):
    ident = _load("identity.json")["units"]
    assert set(ident) == gemeinden
    assert all(len(e["coa"]) == 3 for e in ident.values() if "coa" in e)


def test_history_references_valid_ids(gemeinden):
    h = _load("history.json")
    assert h["n_municipalities"] == len(h["units"]) > 0
    assert set(h["units"]) <= gemeinden
    for uid, events in h["units"].items():
        dates = [e["d"] for e in events]
        assert dates == sorted(dates) and dates[0] >= h["since"]
        for e in events:
            assert e["t"] in h["types"]
            assert e["from"] and e["to"]
            for bfs, name in e["from"] + e["to"]:
                assert bfs.isdigit() and name
        # the municipality itself is the result of its latest event that has it as a successor
        assert any(bfs == uid for e in events for bfs, _ in e["to"]) or any(
            bfs == uid for e in events for bfs, _ in e["from"]), uid


def test_neighbours_symmetric_and_valid(units):
    nb = _load("neighbours.json")["levels"]
    ids = {}
    for u in units:
        ids.setdefault(u["level"], set()).add(u["id"])
    for lvl in ("gemeinde", "bezirk", "kanton"):
        d = nb[lvl]
        assert set(d) == ids[lvl], lvl
        for a, bs in d.items():
            assert a not in bs
            for b in bs:
                assert b in ids[lvl] and a in d[b], (lvl, a, b)
    assert all(d for d in nb["gemeinde"].values())  # no municipality without a neighbour
    assert nb["kanton"]["GE"] == ["VD"]
