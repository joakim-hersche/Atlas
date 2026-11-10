"""Older boundary vintages: municipality maps on a past municipality state (docs/older_boundaries.md).

Only values that exist on that state are shipped:
  native    the source publishes on that state (census 1970-2000 on the 2000 state; the STATPOP
            municipality file of year Y on the state of 31.12.Y)
  forward   the source publishes on an older state; carried forward with the backbone crosswalk
            (to_vintage: mergers summed, splits population-weighted -> precision boundary_estimate)
Nothing is projected backwards from a newer state (that would need splitting merged municipalities).
Derived shares use the `ratio:` definitions of the harmonised catalog, computed from the counts on
the older state.

Outputs (all new files; nothing else in data/out is touched):
  data/out/geo/vintage_<id>.topojson     objects 'gemeinde' (id, name, canton) and 'lakes', WGS84
  data/out/web/vintages.json             index: vintages, metrics per vintage, sources, gzip sizes
  data/out/web/vintage/<id>/units.json   units of the state: id, hist id, name, canton, district,
                                         label point, successors on the reference state
  data/out/web/vintage/<id>/<file>.json  values: {units, metrics: {id: [column per period]}, ...}
                                         grouped by the metric's theme file of the harmonised build
Run: python -m pipeline.build.vintages  (needs make backbone and make web for metrics.json)
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import math
import subprocess
from dataclasses import dataclass
from functools import lru_cache

import geopandas as gpd
import numpy as np
import pandas as pd
import yaml

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.backbone.vintage import crosswalk, to_vintage
from pipeline.build.geometry import MAPSHAPER, DETAIL, _label_points
from pipeline.build.metrics import RATIO, _terms
from pipeline.build.web import PRECISION_CODES, STATUS_CODES, license_cleared, public_text
from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.harmonize.helpers import infer_vintage
from pipeline.harmonize.schema import SOURCES_DIR
from pipeline.sources.bfs_hist_boundaries.fetch import fetch_all as fetch_bounds


@dataclass(frozen=True)
class Vintage:
    id: str
    date: dt.date
    label_en: str
    label_de: str
    label_fr: str


VINTAGES = [
    Vintage("2010", dt.date(2010, 12, 31), "Boundaries of 31 Dec 2010", "Gemeindestand 31.12.2010",
            "Communes au 31.12.2010"),
    Vintage("2000", dt.date(2000, 12, 31), "Boundaries of 31 Dec 2000 (census 2000)",
            "Gemeindestand 31.12.2000 (Volkszählung 2000)", "Communes au 31.12.2000 (recensement 2000)"),
]
GEOMETRY_SOURCE = "bfs_hist_boundaries"
# STATPOP municipality file (state 31.12. of the year): column -> harmonised metric id. Checked
# against the PxWeb STATPOP series shipped by ATLAS (tests: identical wherever the municipality is
# unchanged to the reference state). The file's own foreigners column and age classes differ from
# the published series by a few persons and are not used.
STATPOP_COLUMNS = {"pop_total": "BBTOT", "pop_swiss": "BB11", "pop_male": "BBMTOT", "pop_female": "BBWTOT"}
DECIMALS_PLUS = 1  # shares get one more decimal, as in pipeline/build/web.py


# ---------------------------------------------------------------- geometry
def versions_on(date: dt.date) -> gpd.GeoDataFrame:
    """G1 polygons valid on a date (all GARTE)."""
    g = gpd.read_file(fetch_bounds()["g1"])
    ref = pd.Timestamp(date)
    vf, vt = pd.to_datetime(g["VALID_FROM"]), pd.to_datetime(g["VALID_TO"])
    return g[(vf <= ref) & (vt.isna() | (vt >= ref))].copy()


def municipalities_on(date: dt.date, g: gpd.GeoDataFrame | None = None) -> gpd.GeoDataFrame:
    """Swiss municipalities (GARTE 11) valid on a date; id = BFS number, hist_id = GDEHISTID."""
    g = versions_on(date) if g is None else g
    mun = g[(g["GARTE"] == 11) & (g["CODE_ISO"] == "CH")].copy()
    mun = mun.rename(columns={"GDENR": "id", "GDENAME": "name", "KTKZ": "canton", "GDEHISTID": "hist_id"})
    mun["id"] = mun["id"].astype(int)
    mun["hist_id"] = mun["hist_id"].astype(int)
    if mun["id"].duplicated().any():
        raise ValueError(f"duplicate BFS numbers on {date}")
    return mun


def build_geometry(v: Vintage) -> tuple[str, gpd.GeoDataFrame]:
    g = versions_on(v.date)
    mun = municipalities_on(v.date, g)
    lakes = g[g["GARTE"] == 13].copy()
    tmp = interim_path("geo", f"vintage_{v.id}")
    tmp.mkdir(parents=True, exist_ok=True)
    src_g = tmp / "gemeinde.geojson"
    mun.assign(id=mun["id"].astype(str))[["id", "name", "canton", "geometry"]].to_crs(4326).to_file(src_g, driver="GeoJSON")
    inputs = [str(src_g)]
    if not lakes.empty:
        lk = lakes.assign(name=lakes["SEENAME"].fillna(lakes["GDENAME"]))
        lk = lk[["SEENR", "name", "geometry"]].dissolve(by="SEENR", as_index=False, aggfunc="first")
        src_l = tmp / "lakes.geojson"
        lk.to_crs(4326).to_file(src_l, driver="GeoJSON")
        inputs.append(str(src_l))
    dst = out_path("geo", f"vintage_{v.id}.topojson")
    # one topology for municipalities and lakes (shared edges stay shared after simplification)
    cmd = [*MAPSHAPER, "-i", *inputs, "combine-files", "-simplify", DETAIL["gemeinde"], "keep-shapes",
           "-clean", "target=*", "-o", str(dst), "format=topojson", "quantization=100000", "target=*", "force"]
    subprocess.run(cmd, check=True, capture_output=True)
    return str(dst), mun


# ---------------------------------------------------------------- values
def _hist_lookup(date: dt.date) -> pd.Series:
    mv, _ = load_backbone()
    ver = versions_at(mv, date, municipalities_only=False)
    return ver.drop_duplicates("bfs_nr").set_index("bfs_nr")["hist_id"].astype(int)


def census_counts() -> tuple[dt.date, pd.DataFrame]:
    """Census 1970-2000 counts per municipality of the 2000 state: (state date, long frame
    bfs_nr, period, metric_id, value)."""
    from pipeline.sources.bfs_census_1970_2000.fetch import CUBES, geo_table
    from pipeline.sources.bfs_census_1970_2000.ingest import GROUPS, _wide

    geo = geo_table(CUBES["language"][0])
    wide = None
    for kind in GROUPS:
        w = _wide(kind)
        wide = w if wide is None else wide.merge(w, on=["geo", "year"], how="outer")
    wide = wide.merge(geo, on="geo")
    mun = wide[wide["level"] == "gemeinde"].copy()
    mun["bfs_nr"] = mun["unit"].astype(int)
    state, jac = infer_vintage(mun["bfs_nr"].unique())
    if jac < 0.999:
        raise ValueError(f"census municipality state unclear (best {state}, jaccard {jac:.3f})")
    metrics = [m for g in GROUPS.values() for m in g]
    long = mun.melt(id_vars=["bfs_nr", "year"], value_vars=metrics, var_name="metric_id", value_name="value")
    return state, long.rename(columns={"year": "period"})


def statpop_counts(year: int) -> pd.DataFrame:
    """STATPOP municipality file of a year (state 31.12.year): hist_id, period, metric_id, value."""
    from pipeline.sources.bfs_statpop_geodata.fetch import municipalities

    d = pd.read_parquet(municipalities(year))
    out = []
    for mid, col in STATPOP_COLUMNS.items():
        out.append(pd.DataFrame({"hist_id": d["GDEHISTID"].astype(int), "period": str(year),
                                 "metric_id": mid, "value": d[col].astype(float)}))
    # foreigners = residents - Swiss (matches the published series; the file's BB12 does not)
    out.append(pd.DataFrame({"hist_id": d["GDEHISTID"].astype(int), "period": str(year), "metric_id": "pop_foreign",
                             "value": (d["BBTOT"] - d["BB11"]).astype(float)}))
    return pd.concat(out, ignore_index=True)


def _native(df: pd.DataFrame, source_id: str, note: str) -> pd.DataFrame:
    return df.assign(precision="exact", provenance="native", kind="native", source_id=source_id, note=note)


def _forward(long: pd.DataFrame, source_state: dt.date, target: dt.date, source_id: str, note: str) -> pd.DataFrame:
    """Carry counts from an older state forward to `target` (sum rule, crosswalk weights)."""
    parts = []
    for mid, g in long.groupby("metric_id"):
        r = to_vintage(g[["bfs_nr", "period", "value"]], source_vintage=source_state, target_vintage=target,
                       rule="sum", group_cols=["period"])
        parts.append(r.assign(metric_id=mid))
    out = pd.concat(parts, ignore_index=True)
    exact = out["min_weight"] >= 1 - 1e-9
    return pd.DataFrame({
        "hist_id": out["hist_id"].astype(int), "period": out["period"].astype(str), "metric_id": out["metric_id"],
        "value": out["value"].astype(float), "precision": np.where(exact, "exact", "boundary_estimate"),
        "provenance": np.where(exact, "aggregated_mergers", "reprojected_weighted"), "kind": "forward",
        "source_id": source_id, "note": note})


def base_values(v: Vintage) -> pd.DataFrame:
    """Count metrics on the vintage state, keyed by hist_id."""
    parts = []
    state, cen = census_counts()
    if state == v.date:
        cen = cen.assign(hist_id=cen["bfs_nr"].map(_hist_lookup(state)))
        if cen["hist_id"].isna().any():
            raise ValueError("census municipalities without a register version")
        parts.append(_native(cen.drop(columns="bfs_nr").astype({"hist_id": int}), "bfs_census_1970_2000",
                             f"BFS, published on the {state:%d.%m.%Y} municipality state"))
    elif state < v.date:
        parts.append(_forward(cen, state, v.date, "bfs_census_1970_2000",
                              f"census on the {state:%d.%m.%Y} state, carried forward to the {v.date:%d.%m.%Y} "
                              "boundaries by ATLAS (mergers summed; splits population-weighted)"))
    if v.date.month == 12 and v.date.day == 31:
        from pipeline.sources.bfs_statpop_geodata.fetch import FIRST_LV95_YEAR, LAST_YEAR
        if FIRST_LV95_YEAR <= v.date.year <= LAST_YEAR:
            parts.append(_native(statpop_counts(v.date.year), "bfs_statpop_geodata",
                                 f"BFS STATPOP municipality file, state {v.date:%d.%m.%Y}"))
    return pd.concat(parts, ignore_index=True)


def derive(base: pd.DataFrame, catalog: dict[str, dict]) -> pd.DataFrame:
    """Ratio metrics of the harmonised catalog whose inputs all exist on this state."""
    have = set(base["metric_id"])
    piv = base.pivot_table(index=["hist_id", "period"], columns="metric_id", values="value", aggfunc="first")
    prec_rank = base.assign(r=(base["precision"] != "exact").astype(int)).pivot_table(
        index=["hist_id", "period"], columns="metric_id", values="r", aggfunc="max")
    src = base.groupby("metric_id")[["source_id", "note", "kind"]].first()
    out = []
    for mid, m in catalog.items():
        mm = RATIO.match(str(m.get("aggregation") or ""))
        if not mm:
            continue
        num, den = _terms(mm["num"]), _terms(mm["den"])
        if not set(num + den) <= have or mid in have:
            continue
        f = float(mm["f"]) if mm["f"] else 1.0
        n = piv[num].sum(axis=1, min_count=len(num))
        d = piv[den].sum(axis=1, min_count=len(den))
        n = n.where(piv[num].notna().all(axis=1))
        d = d.where(piv[den].notna().all(axis=1))
        val = (n / d.where(d > 0)) * f
        # periods of other sources sit in the same pivot: keep the periods where the inputs exist
        has = val.notna().groupby(level=1).transform("any")
        val = val[has]
        est = (prec_rank[num + den].max(axis=1) > 0)[has]
        sid, note, kind = src.loc[num[0], "source_id"], src.loc[num[0], "note"], src.loc[num[0], "kind"]
        out.append(pd.DataFrame({"hist_id": val.index.get_level_values(0), "period": val.index.get_level_values(1),
                                 "metric_id": mid, "value": val.values,
                                 "precision": np.where(est.values, "boundary_estimate", "exact"),
                                 "provenance": "derived", "kind": kind, "source_id": sid, "note": note}))
    return pd.concat(out, ignore_index=True) if out else base.iloc[:0]


def national(base: pd.DataFrame, catalog: dict[str, dict]) -> dict[tuple[str, str], float]:
    """Switzerland per (metric, period): counts summed over the vintage's municipalities, ratios
    from the summed counts (same rule as the harmonised build)."""
    sums = base.groupby(["metric_id", "period"])["value"].sum(min_count=1)
    out = {k: float(v) for k, v in sums.items() if pd.notna(v)}
    for mid, m in catalog.items():
        mm = RATIO.match(str(m.get("aggregation") or ""))
        if not mm:
            continue
        num, den = _terms(mm["num"]), _terms(mm["den"])
        f = float(mm["f"]) if mm["f"] else 1.0
        for p in sorted({p for (x, p) in out if x == den[0]}):
            if all((t, p) in out for t in num + den):
                dd = sum(out[(t, p)] for t in den)
                if dd > 0:
                    out[(mid, p)] = sum(out[(t, p)] for t in num) / dd * f
    return out


# ---------------------------------------------------------------- output
def _round(v, d):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(float(v), int(d)) if d > 0 else int(round(float(v)))


def _gz(path) -> int:
    return len(gzip.compress(open(path, "rb").read(), 9))


def _dump(obj, *parts) -> str:
    p = out_path(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    return str(p)


def load_catalog() -> dict[str, dict]:
    """Shipped metric catalog of the harmonised build (labels and rules come from there)."""
    return {m["id"]: m for m in json.loads(out_path("web", "metrics.json").read_text(encoding="utf-8"))}


def source_meta(source_id: str) -> dict:
    m = yaml.safe_load((SOURCES_DIR / source_id / "meta.yaml").read_text(encoding="utf-8")) or {}
    return {k: public_text(m.get(k)) for k in ("source_id", "title", "publisher", "url", "license", "attribution", "vintage")}


@lru_cache(maxsize=None)
def cleared(source_id: str) -> bool:
    review = yaml.safe_load((SOURCES_DIR.parent / "licence_review.yaml").read_text(encoding="utf-8")) or {}
    if source_id in review:
        return review[source_id].get("status") == "cleared"
    m = yaml.safe_load((SOURCES_DIR / source_id / "meta.yaml").read_text(encoding="utf-8")) or {}
    return license_cleared(m)[0]


def successors(units: gpd.GeoDataFrame) -> dict[int, list]:
    """hist_id -> [[current bfs_nr, current name, weight], ...] on the reference state."""
    cw = crosswalk(REFERENCE_DATE)
    cw = cw[cw["from_hist_id"].isin(set(units["hist_id"])) & (cw["weight"] > 0)]
    out: dict[int, list] = {}
    for r in cw.sort_values(["from_hist_id", "weight"], ascending=[True, False]).itertuples():
        out.setdefault(int(r.from_hist_id), []).append([str(int(r.to_bfs_nr)), r.to_name, round(float(r.weight), 3)])
    return out


def build_vintage(v: Vintage, catalog: dict[str, dict]) -> dict:
    geo_file, mun = build_geometry(v)
    base = base_values(v)
    ok_src = {s for s in base["source_id"].unique() if cleared(s)}
    base = base[base["metric_id"].isin(catalog) & base["source_id"].isin(ok_src)]
    known = set(mun["hist_id"])
    stray = base[~base["hist_id"].isin(known)]
    if len(stray):
        raise ValueError(f"vintage {v.id}: {stray['hist_id'].nunique()} units without geometry")
    vals = pd.concat([base, derive(base, catalog)], ignore_index=True)
    vals = vals[vals["metric_id"].map(lambda m: not catalog[m].get("hidden"))]
    ch = national(base, catalog)

    mun = mun.sort_values("id")
    ids = [str(i) for i in mun["id"]]
    pos = {h: k for k, h in enumerate(mun["hist_id"])}
    labels = {d["id"]: d["label"] for d in _label_points(mun.assign(id=mun["id"].astype(str)), "id")}
    succ = successors(mun)
    units = [{"id": str(r.id), "hist_id": int(r.hist_id), "name": r.name, "kanton": r.canton,
              "bezirk": r.BEZNAME if isinstance(r.BEZNAME, str) else None, "label": labels.get(str(r.id)),
              "to": succ.get(int(r.hist_id), [])} for r in mun.itertuples()]
    units_file = _dump({"vintage": v.id, "date": v.date.isoformat(), "units": units}, "web", "vintage", v.id, "units.json")

    groups: dict[str, dict] = {}
    metrics_ix: dict[str, dict] = {}
    for mid, gm in vals.groupby("metric_id"):
        meta = catalog[mid]
        d = int(meta["decimals"]) + (DECIMALS_PLUS if str(meta["unit"]).strip() == "%" else 0)
        cols = []
        periods = sorted(gm["period"].unique())
        for p in periods:
            g = gm[gm["period"] == p]
            v_ = [None] * len(ids)
            prec, status = {}, {}
            for h, x, pr in zip(g["hist_id"], g["value"], g["precision"]):
                i = pos[h]
                v_[i] = _round(x, d)
                if pr != "exact":
                    prec[str(i)] = PRECISION_CODES[pr]
            for i, x in enumerate(v_):
                if x is None:
                    status[str(i)] = STATUS_CODES["no_data"]
            col = {"period": p, "v": v_, **({"s": status} if status else {}), **({"p": prec} if prec else {})}
            if (mid, p) in ch:
                col["ch"] = _round(ch[(mid, p)], d)
            cols.append(col)
        groups.setdefault(meta["file"], {})[mid] = cols
        first = gm.iloc[0]
        metrics_ix[mid] = {"periods": periods, "file": meta["file"], "source": first["source_id"],
                           "provenance": first["kind"], "note": first["note"],
                           "n_estimate": int(gm.loc[gm["period"] == periods[-1], "precision"].ne("exact").sum())}
    files = {}
    for fname, gcols in groups.items():
        p = _dump({"vintage": v.id, "level": "gemeinde", "units": ids, "metrics": gcols, "status_codes": STATUS_CODES,
                   "precision_codes": PRECISION_CODES, "flag_bits": {}}, "web", "vintage", v.id, f"{fname}.json")
        files[fname] = {"path": f"web/vintage/{v.id}/{fname}.json", "gzip_bytes": _gz(p)}
    return {
        "id": v.id, "date": v.date.isoformat(), "label_en": v.label_en, "label_de": v.label_de, "label_fr": v.label_fr,
        "n_units": len(ids),
        "geometry": {"path": f"geo/vintage_{v.id}.topojson", "gzip_bytes": _gz(geo_file)},
        "units": {"path": f"web/vintage/{v.id}/units.json", "gzip_bytes": _gz(units_file)},
        "files": files, "metrics": metrics_ix,
    }


def run() -> dict:
    catalog = load_catalog()
    out = {"reference": REFERENCE_DATE.isoformat(), "generated": dt.date.today().isoformat(), "vintages": []}
    used = {GEOMETRY_SOURCE}
    for v in VINTAGES:
        info = build_vintage(v, catalog)
        out["vintages"].append(info)
        used |= {m["source"] for m in info["metrics"].values()}
    out["sources"] = {s: source_meta(s) for s in sorted(used)}
    _dump(out, "web", "vintages.json")
    return out


if __name__ == "__main__":
    res = run()
    for v in res["vintages"]:
        kb = lambda b: f"{b / 1024:.0f} KB"
        print(f"{v['id']}: {v['n_units']} units, {len(v['metrics'])} metrics; geometry {kb(v['geometry']['gzip_bytes'])}, "
              f"units {kb(v['units']['gzip_bytes'])}, values " +
              ", ".join(f"{k} {kb(f['gzip_bytes'])}" for k, f in v["files"].items()) + " (gzip)")
