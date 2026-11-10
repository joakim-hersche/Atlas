"""Tests of the connectors added for backlog item "More data" (2026-11-10): estv_median_income, bafu_noise, bfs_gwr
(school buildings) and bfs_se_language_cities.

Pure-method tests run anywhere; tests on real data read the cached raw files (data/raw, not in git) and skip when
they are missing. Published totals used as checks are quoted next to each assertion.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from pipeline.common import RAW
from pipeline.harmonize.schema import OBS_COLUMNS, SOURCES_DIR, validate_metrics, validate_observations

NEW = ["estv_median_income", "bafu_noise", "bfs_gwr", "bfs_se_language_cities"]


def _metrics_file(source: str) -> Path:
    d = SOURCES_DIR / source
    return d / "metrics.yaml" if (d / "metrics.yaml").exists() else d / "metrics.wip.yaml"


def _has_raw(source: str, pattern: str) -> bool:
    return bool(list((RAW / source).glob(f"*/{pattern}")))


def _check(obs: pd.DataFrame, source: str) -> None:
    m = pd.DataFrame(yaml.safe_load(_metrics_file(source).read_text(encoding="utf-8")))
    ids = set(m["id"])
    assert list(obs.columns) == OBS_COLUMNS
    problems = validate_observations(obs, ids)
    assert not problems, problems


# ------------------------------------------------------------------------------ metrics metadata
@pytest.mark.parametrize("source", NEW)
def test_metrics_valid(source):
    m = pd.DataFrame(yaml.safe_load(_metrics_file(source).read_text(encoding="utf-8")))
    m["source_id"] = source
    assert not validate_metrics(m)
    # derived metrics refer to metrics that exist in the same file
    ids = set(m["id"])
    for agg in m.loc[m["kind"] == "derived", "aggregation"]:
        num, den = agg.split(":")[1].split("*")[0].split("/")
        assert num in ids and den in ids


def test_labels_staged_or_registered():
    ids = set()
    for s in NEW:
        ids |= {x["id"] for x in yaml.safe_load(_metrics_file(s).read_text(encoding="utf-8"))}
    reg = yaml.safe_load((SOURCES_DIR.parent / "i18n" / "labels.yaml").read_text(encoding="utf-8"))
    wip = SOURCES_DIR.parent / "i18n" / "labels.wip.yaml"
    labels = {**reg, **(yaml.safe_load(wip.read_text(encoding="utf-8")) if wip.exists() else {})}
    assert not ids - set(labels)
    for i in ids:
        assert all(str(labels[i].get(f) or "").strip() for f in ("label_fr", "unit_en", "unit_de", "unit_fr")), i


# ------------------------------------------------------------------------------ (a) median income
from pipeline.sources.estv_median_income.estimate import median_from_classes  # noqa: E402

EDGES = [-1, 0.5, 30e3, 40e3, 50e3, 75e3, 100e3, 200e3, 500e3, 1e6, 1e12]


def _classes(x: np.ndarray) -> list[float]:
    return list(np.histogram(x, bins=EDGES)[0].astype(float))


def test_median_known_cases():
    # all taxpayers in one class: linear inside the first class, log-linear above
    assert median_from_classes([0, 100, 0, 0, 0, 0, 0, 0, 0, 0]) == pytest.approx(15_000)
    m = median_from_classes([0, 0, 0, 0, 100, 0, 0, 0, 0, 0])
    assert m == pytest.approx(math.sqrt(50_000 * 75_000))  # geometric middle of the class
    # more than half with taxable income 0
    assert median_from_classes([60, 40, 0, 0, 0, 0, 0, 0, 0, 0]) == 0
    # the half-way point inside the open top class cannot be estimated
    assert math.isnan(median_from_classes([10, 0, 0, 0, 0, 0, 0, 0, 0, 90]))
    # monotone: moving a taxpayer to a higher class cannot lower the median
    base = [10, 20, 10, 10, 30, 10, 10, 0, 0, 0]
    up = [10, 20, 10, 10, 29, 11, 10, 0, 0, 0]
    assert median_from_classes(up) >= median_from_classes(base)


def test_median_suppressed_cells():
    full = [56, 180, 79, 80, 192, 151, 257, 71, 12, 6]  # Aeugst am Albis 2023
    total = sum(full)
    ref = median_from_classes(full)
    # cells below 4 hidden (here the two smallest tail cells): the remainder to the total restores the answer
    hidden = list(full)
    hidden[8] = hidden[9] = float("nan")
    assert median_from_classes(hidden, total) == pytest.approx(ref, rel=1e-9)
    # class 0 hidden together with a large cell (complementary suppression): either NaN or within 5 % of the truth
    hidden = list(full)
    hidden[0] = hidden[4] = float("nan")
    r = median_from_classes(hidden, total)
    assert math.isnan(r) or abs(r / ref - 1) < 0.05
    # no total, one hidden cell: cannot be bracketed
    one = list(full)
    one[0] = float("nan")
    assert math.isnan(median_from_classes(one, None))


@pytest.mark.parametrize("n,tol_mean", [(300, 0.025), (3000, 0.012)])
def test_median_error_on_simulated_incomes(n, tol_mean):
    """Log-normal taxable incomes with 7 % at 0: mean absolute error of the class estimate (seed fixed)."""
    rng = np.random.default_rng(7)
    errs = []
    for mu, sig in [(10.9, 0.9), (11.1, 1.0), (11.3, 0.8), (10.7, 1.1), (11.0, 0.7), (11.4, 1.0)]:
        for _ in range(12):
            x = rng.lognormal(mu, sig, n)
            x[rng.random(n) < 0.07] = 0
            errs.append(abs(median_from_classes(_classes(x)) / np.median(x) - 1))
    assert np.mean(errs) < tol_mean


@lru_cache(maxsize=1)
def _median_obs() -> pd.DataFrame:
    from pipeline.sources.estv_median_income import parse
    return parse.observations()


@pytest.mark.skipif(not _has_raw("estv_dbst", "statistik-dbst-np-gemeinden-2023-500.xlsx"), reason="ESTV workbooks not cached")
def test_median_income_real_data():
    from pipeline.sources.estv_median_income import parse
    o = _median_obs()
    _check(o, "estv_median_income")
    assert set(o["precision"]) == {"modelled"}
    # published class totals 2023: the national class counts add up to the national total of normal cases
    _, tot = parse.class_tables(2023)
    ch = tot.loc[27]
    s = ch[parse.CLASSES].sum(skipna=True)
    assert 0 <= ch["total"] - s <= 3 * ch[parse.CLASSES].isna().sum()  # only hidden cells (< 4 each) are missing
    assert ch["total"] == pytest.approx(4_839_709, abs=1)  # taxpayers of the normal cases 2023 (estv_dbst national row)
    # the national median lies in the class CHF 50,001-75,000, which holds the half-way point
    nat = o[(o["level"] == "schweiz") & (o["period"] == "2023")]["value"].iloc[0]
    cum_below_50k = ch[["0", "1_30k", "30_40k", "40_50k"]].sum()
    assert cum_below_50k < ch["total"] / 2 <= cum_below_50k + ch["50_75k"]
    assert 50_000 < nat < 75_000
    # municipalities 2023: nearly all have an estimate, values plausible, cantons inside their municipalities' range
    g = o[(o["level"] == "gemeinde") & (o["period"] == "2023")]
    assert g["status"].eq("ok").mean() > 0.99
    assert g["value"].dropna().between(10_000, 150_000).all()
    mun_total = parse.municipal_wide().query("period == '2023'")["taxpayers_normal"].sum()
    assert mun_total == pytest.approx(ch["total"], rel=0.005)  # municipalities add up to the national total
    # the 26 cantons are present for every year
    k = o[o["level"] == "kanton"]
    assert k.groupby("period")["unit_id"].nunique().eq(26).all()
    # known pattern: Zug (low taxes, high incomes) above Geneva and Ticino
    kv = k[k["period"] == "2023"].set_index("unit_id")["value"]
    assert kv["ZG"] > kv["GE"] and kv["ZG"] > kv["TI"]


# ------------------------------------------------------------------------------ (b) noise
def test_sample_points_and_neighbourhood(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    from pipeline.sources.bafu_noise.sample import sample_points
    a = np.full((50, 60), -9999.0)
    a[10, 10] = 61.0
    a[20, 30] = 40.0
    p = tmp_path / "g.tif"
    with rasterio.open(p, "w", driver="GTiff", height=50, width=60, count=1, dtype="float64", crs="EPSG:2056",
                       transform=from_origin(2_600_000, 1_200_000, 10, 10), nodata=-9999.0) as r:
        r.write(a, 1)
    e = np.array([2_600_000 + 10 * 10 + 5, 2_600_000 + 30 * 10 + 5, 2_600_000 + 11 * 10 + 5, 2_600_000 + 59 * 10 + 5])
    n = np.array([1_200_000 - 10 * 10 - 5, 1_200_000 - 20 * 10 - 5, 1_200_000 - 11 * 10 - 5, 1_200_000 - 49 * 10 - 5])
    v0 = sample_points(p, e, n, 0, strip=7)
    assert v0[0] == 61 and v0[1] == 40 and np.isnan(v0[2]) and np.isnan(v0[3])
    v1 = sample_points(p, e, n, 1, strip=7)
    assert v1[0] == 61 and v1[2] == 61  # a point one cell away sees the neighbour
    outside = sample_points(p, np.array([2_000_000.0]), np.array([1_000_000.0]), 1)
    assert np.isnan(outside[0])


def test_noise_exposure_aggregation():
    from pipeline.sources.bafu_noise import parse as N
    t = pd.DataFrame({"bfs_nr": [1, 1, 1, 2], "residents": [10.0, 20.0, 30.0, 5.0],
                      "road_day": [61, 50, np.nan, 66], "road_night": [45, 51, np.nan, 40],
                      "rail_day": [np.nan, np.nan, 62, np.nan], "rail_night": [np.nan, np.nan, 40, np.nan]})
    e = N.exposure(t).set_index("bfs_nr")
    assert e.loc[1, "residents"] == 60 and e.loc[1, "road_day"] == 10 and e.loc[1, "road_night"] == 20
    assert e.loc[1, "rail_day"] == 30 and e.loc[1, "any_60_50"] == 60  # all three buildings reach a limit
    assert e.loc[1, "any_65_55"] == 0 and e.loc[2, "any_65_55"] == 5


@pytest.mark.skipif(not (_has_raw("bafu_noise", "laerm-strassenlaerm_tag_2056.tif") and _has_raw("bfs_gwr", "gwr_ch.zip")),
                    reason="noise grids or GWR extract not cached")
def test_noise_real_data():
    from pipeline.sources.bafu_noise import parse as N
    o = N.observations()
    _check(o, "bafu_noise")
    v = o.pivot_table(index="unit_id", columns="metric_id", values="value")
    assert len(v) == 2110 or len(v) > 2000
    res = v["noise_residents"].sum()
    # STATPOP 2021 hectare total (BBTOT of the hectare file, about 8.81 M); at most a handful of hectares unassigned
    assert res == pytest.approx(8_811_084, abs=50)
    tot = {c: v[c].sum() for c in v.columns}
    # exposures nest: level III is a subset of level II, the union contains each part
    assert tot["noise_any_65_55_residents"] < tot["noise_any_60_50_residents"]
    assert tot["noise_any_60_50_residents"] >= max(tot["noise_road_day_60_residents"], tot["noise_road_night_50_residents"])
    assert tot["noise_rail_day_60_residents"] < 0.05 * tot["noise_road_day_60_residents"]
    # order of magnitude against BAFU's national figure for 2021: 740,000 people harmed or annoyed at home by road
    # traffic noise (BAFU, 18 Nov 2025); the level-III indicator (road and rail) is 745,000 here
    assert 600_000 < tot["noise_any_65_55_residents"] < 900_000
    # every share in 0..100 %; no residents above their municipality's total
    assert (v["noise_any_60_50_residents"] <= v["noise_residents"] + 1e-6).all()
    # Zermatt (no through road, small) is quieter than Geneva; Zürich is among the noisier large cities
    share = (v["noise_any_60_50_residents"] / v["noise_residents"] * 100)
    assert share.loc["261"] > 15 and share.loc["6300"] < 5 and share.loc["6621"] > 20  # Zürich, Zermatt, Genève


# ------------------------------------------------------------------------------ (d) schools (GWR)
@pytest.mark.skipif(not _has_raw("bfs_gwr", "gwr_ch.zip"), reason="GWR extract not cached")
def test_gwr_school_buildings_real_data():
    from pipeline.sources.bfs_gwr import parse as G
    from pipeline.sources.bfs_gwr.buildings import load
    o = G.observations()
    _check(o, "bfs_gwr")
    s = o[o["metric_id"] == "gwr_school_buildings"].set_index("unit_id")["value"]
    b = load()
    direct = int(((b["GSTAT"] == 1004) & (b["GKLAS"] == 1263)).sum())
    assert s.sum() == direct  # no building lost in the reprojection to the reference state
    assert len(s) >= 2100 and s.min() >= 0 and (s == 0).sum() > 100  # municipalities without a school building
    assert s.loc["261"] > 100 and s.loc["351"] > 50  # Zürich, Bern
    # register check: dwellings in existing buildings against the GWS stock of 31 Dec 2025 (4,883,159, BFS; the
    # reference of the vacancy rate, bfs_vacancy); the snapshot is ten months later
    dw = b.loc[b["GSTAT"] == 1004, "GANZWHG"].sum()
    assert 0.99 < dw / 4_883_159 < 1.02
    pop = o[o["metric_id"] == "gwr_resident_base"]["value"].sum()
    assert 9.0e6 < pop < 9.3e6  # STATPOP 31 Dec 2025


# ------------------------------------------------------------------------------ (e) Structural Survey, cities
@lru_cache(maxsize=1)
def _lang_obs() -> pd.DataFrame:
    from pipeline.sources.bfs_se_language_cities import parse
    return parse.observations()


@pytest.mark.skipif(not _has_raw("bfs_se_language_cities", "hauptsprachen_staedte_2020-2024.xlsx"), reason="SE city tables not cached")
def test_se_cities_real_data():
    from pipeline.sources.bfs_se_language_cities import parse as P
    o = _lang_obs()
    _check(o, "bfs_se_language_cities")
    assert set(o["precision"]) == {"survey"}
    assert not P.UNMATCHED  # every city name of every edition is found in the register
    last = o[o["period"] == "2020-2024"]
    assert last[last["level"] == "gemeinde"]["unit_id"].nunique() >= 165
    # internal consistency: the cities add up to the published row 'Total der Städte' (all cities, 2020-2024)
    vals, _ = P._grid(next((RAW / "bfs_se_language_cities").glob("*/hauptsprachen_staedte_2020-2024.xlsx")))
    hdr = next(r for r in vals if "Total Bevölkerung" in [str(c).strip() for c in r])
    c0 = [str(c).strip() for c in hdr].index("Total Bevölkerung")
    rows = [r for r in vals if r[c0 - 1] and isinstance(r[c0], (int, float))]
    total = next(r[c0] for r in rows if str(r[c0 - 1]).startswith("Total der"))
    cities = sum(r[c0] for r in rows if not str(r[c0 - 1]).startswith(("Total", "Schweiz")))
    assert cities == pytest.approx(total, rel=1e-4)
    # national row: German about 61 % (BFS: 61 % of the population in 2023), all national languages plausible
    ch = last[last["level"] == "schweiz"].set_index("metric_id")["value"]
    assert 59.5 < ch["lang_sec_de_share"] < 63 and 20 < ch["lang_sec_fr_share"] < 26
    # the language border: Zürich German, Genève and Lausanne French, Lugano Italian; CI >= 0
    g = last[last["level"] == "gemeinde"].pivot_table(index="unit_id", columns="metric_id", values="value")
    assert g.loc["261", "lang_sec_de_share"] > 70
    assert g.loc["6621", "lang_sec_fr_share"] > 75 and g.loc["5586", "lang_sec_fr_share"] > 75
    assert g.loc["5192", "lang_sec_it_share"] > 80
    assert (g.filter(like="_share_ci").stack().dropna() >= 0).all()
    assert (g.filter(regex=r"_share$").stack().dropna().between(0, 100.5)).all()
