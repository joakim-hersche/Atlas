"""Fine boundaries (pipeline/build/geometry_fine.py) against the generalized files.

Checks on the built files; skipped when `python -m pipeline.build.geometry` and
`python -m pipeline.build.geometry_fine` have not been run.
"""
import json

import numpy as np
import pyproj
import pytest
import shapely
from shapely.geometry import Polygon

from pipeline.common import OUT

GEO = OUT / "geo"
LEVELS = ("gemeinde", "bezirk", "kanton")
TO_LV95 = pyproj.Transformer.from_crs(4326, 2056, always_xy=True).transform

pytestmark = pytest.mark.skipif(
    not all((GEO / f"{lv}{sfx}.topojson").exists() for lv in LEVELS for sfx in ("", "_fine")),
    reason="geometry not built (make geometry)")


def decode(path, level):
    """TopoJSON -> {id: shapely geometry in LV95} (small decoder: arcs are delta-encoded and quantized)."""
    t = json.loads(path.read_text())
    sx, sy = t["transform"]["scale"]
    tx, ty = t["transform"]["translate"]
    arcs = []
    for a in t["arcs"]:
        pts = np.cumsum(np.array(a, dtype=float), axis=0)
        arcs.append(np.column_stack([pts[:, 0] * sx + tx, pts[:, 1] * sy + ty]))

    def ring(idx):
        out = []
        for i in idx:
            c = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(c.tolist() if not out else c[1:].tolist())
        return out

    res = {}
    for g in t["objects"][level]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        ps = [Polygon(ring(p[0]), [ring(h) for h in p[1:]]) for p in polys]
        geom = shapely.MultiPolygon(ps) if len(ps) > 1 else ps[0]
        res[str(g["properties"]["id"])] = shapely.transform(geom, lambda c: np.column_stack(TO_LV95(c[:, 0], c[:, 1])))
    return res, t


@pytest.fixture(scope="module", params=LEVELS)
def pair(request):
    lv = request.param
    return lv, decode(GEO / f"{lv}.topojson", lv), decode(GEO / f"{lv}_fine.topojson", lv)


def test_same_ids_as_generalized(pair):
    lv, (coarse, _), (fine, ft) = pair
    assert set(fine) == set(coarse)
    assert len(fine) == len(ft["objects"][lv]["geometries"])        # no duplicate ids
    assert {k for g in ft["objects"][lv]["geometries"] for k in g["properties"]} == {"id"}


def test_geometries_valid(pair):
    _, (coarse, _), (fine, _) = pair
    assert not [k for k, g in fine.items() if g.is_empty]
    bad = [k for k, g in fine.items() if not g.is_valid]
    # a few rings touch themselves at a single point (pinched enclaves) in the source; the generalized
    # files have the same, so the fine ones must not have more, and repairing must not change the area
    assert len(bad) <= sum(not g.is_valid for g in coarse.values())
    assert all(shapely.make_valid(fine[k]).area == pytest.approx(fine[k].buffer(0).area, rel=0.01) for k in bad)


def test_area_matches_generalized(pair):
    lv, (coarse, _), (fine, _) = pair
    ac = sum(g.area for g in coarse.values())
    af = sum(g.area for g in fine.values())
    assert af == pytest.approx(ac, rel=0.005), (ac, af)             # national land area within 0.5 %
    if lv == "gemeinde":
        # per municipality: the two files follow the same border; allow generalization differences
        ratio = np.array([fine[k].area / coarse[k].area for k in coarse])
        assert np.percentile(ratio, 1) > 0.9 and np.percentile(ratio, 99) < 1.1
        assert ratio.min() > 0.5 and ratio.max() < 1.5


def test_fine_is_finer_and_small(pair):
    lv, (_, ct), (_, ft) = pair
    nv = lambda t: sum(len(a) for a in t["arcs"])
    assert nv(ft) > 1.5 * nv(ct)
    gz = len(__import__("gzip").compress((GEO / f"{lv}_fine.topojson").read_bytes(), 9))
    assert gz < 1_500_000                                           # nationwide municipal file stays under ~2 MB gzip


def test_borders_shared(pair):
    """Topology: neighbouring units share borders (no gaps beyond slivers) after simplification."""
    lv, _, (fine, _) = pair
    if lv != "gemeinde":
        pytest.skip("checked on municipalities")
    u = shapely.union_all([shapely.make_valid(g) for g in fine.values()])
    # holes in the union = gaps between municipalities; lakes are the only legitimate holes
    holes = [Polygon(r) for p in shapely.get_parts(u) if p.geom_type == "Polygon" for r in p.interiors]
    assert sum(h.area for h in holes if h.area < 1e5) < 1.5e5      # holes below 0.1 km2 (slivers, one small enclosed water body) add up to < 15 ha
