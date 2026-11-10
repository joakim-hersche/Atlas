"""Tests of the bazl_aircraft_noise connector (FOCA/BAZL noise cadastre of civil aerodromes)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from pipeline.common import RAW
from pipeline.harmonize.schema import OBS_COLUMNS, SOURCES_DIR, validate_metrics, validate_observations

SRC = "bazl_aircraft_noise"


def _metrics() -> pd.DataFrame:
    return pd.DataFrame(yaml.safe_load((SOURCES_DIR / SRC / "metrics.yaml").read_text(encoding="utf-8")))


def test_metrics_valid():
    m = _metrics()
    m["source_id"] = SRC
    assert not validate_metrics(m)
    ids = set(m["id"])
    for agg in m.loc[m["kind"] == "derived", "aggregation"]:
        num, den = agg.split(":")[1].split("*")[0].split("/")
        assert num in ids and den in ids
    assert set(m["coverage"]) == {"partial:ZH,GE,BE,TI,GR,SG,BS"}


def test_labels_registered():
    reg = yaml.safe_load((SOURCES_DIR.parent / "i18n" / "labels.yaml").read_text(encoding="utf-8"))
    for i in _metrics()["id"]:
        assert i in reg and reg[i].get("label_fr")


def test_exposure_aggregation():
    from pipeline.sources.bazl_aircraft_noise import parse as P
    t = pd.DataFrame({"bfs_nr": [1, 1, 2], "residents": [10.0, 20.0, 5.0]})
    flags = {"day": np.array([True, False, False]), "night1": np.array([False, True, False])}
    e = P.exposure(t, flags).set_index("bfs_nr")
    assert e.loc[1, "residents"] == 30 and e.loc[1, "day"] == 10 and e.loc[1, "night1"] == 20 and e.loc[1, "any"] == 30
    assert e.loc[2, "any"] == 0


def test_inside_polygon_union():
    import geopandas as gpd
    from shapely.geometry import Polygon
    from pipeline.sources.bazl_aircraft_noise import parse as P
    polys = gpd.GeoDataFrame({"aerodrome": ["a", "b"]}, geometry=[Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
                                                                  Polygon([(20, 0), (30, 0), (30, 10), (20, 10)])])
    r = P.inside(np.array([5.0, 25.0, 15.0]), np.array([5.0, 5.0, 5.0]), polys)
    assert r.tolist() == [True, True, False]


@pytest.mark.skipif(not list((RAW / SRC).glob("*/laermbelastungskataster-zivilflugplaetze_2056.gpkg")),
                    reason="cadastre not cached")
def test_curves_real_data():
    from pipeline.sources.bazl_aircraft_noise import parse as P
    day = P.curves(*P.LAYERS["day"])
    assert {"LBK Zürich", "CDB Genève", "LBK Bern", "CDR Lugano-Agno"} <= set(day["aerodrome"])
    assert day.geometry.is_valid.all() and (day.geometry.area > 0).all()
    night = P.curves(*P.LAYERS["night1"])
    assert {"LBK Zürich", "CDB Genève"} <= set(night["aerodrome"])


@pytest.mark.skipif(not (list((RAW / SRC).glob("*/laermbelastungskataster-zivilflugplaetze_2056.gpkg"))
                         and list((RAW / "bafu_noise").glob("*/laerm-strassenlaerm_tag_2056.tif"))
                         and list((RAW / "bfs_gwr").glob("*/gwr_ch.zip"))),
                    reason="cadastre, noise grids or GWR extract not cached")
def test_real_data():
    from pipeline.sources.bazl_aircraft_noise import parse as P
    o = P.observations()
    assert list(o.columns) == OBS_COLUMNS
    assert not validate_observations(o, set(_metrics()["id"]))
    v = o.pivot_table(index="unit_id", columns="metric_id", values="value")
    # exposures nest
    assert (v["aircraft_igw2_residents"] >= v[["aircraft_day_60_residents", "aircraft_night_55_residents"]].max(axis=1) - 1e-6).all()
    assert (v["aircraft_igw2_residents"] <= v["aircraft_noise_residents"] + 1e-6).all()
    # Kloten (66) and Opfikon (62) lie under the Zürich airport; Meyrin (6630) next to Genève airport; Bern city is not exposed
    assert v.loc["66", "aircraft_day_60_residents"] > 5000 and v.loc["62", "aircraft_igw2_residents"] > 3000
    assert v.loc["6630", "aircraft_igw2_residents"] > 2000
    assert v.loc["351", "aircraft_igw2_residents"] < 100  # Bern
    # only the covered cantons are emitted (Aargau, Vaud: no value)
    assert "4001" not in v.index and "5586" not in v.index
    # national order of magnitude: well below 1 % of the 4.4 M residents of the covered cantons
    assert 50_000 < v["aircraft_igw2_residents"].sum() < 150_000
