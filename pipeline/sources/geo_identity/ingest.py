"""Area and elevation per municipality on the reference state.

Area (ha): swissBOUNDARIES3D 2026-01 (swisstopo), layer tlm_hoheitsgebiet, objektart Gemeindegebiet:
  gem_flaeche = total area incl. lake share, see_flaeche = lake share; land = total - lake.
  The 2026-01 release holds exactly the 2110 municipalities of the reference state (keyed on
  bfs_nummer), so no reprojection is needed. Lake areas and state forest outside any municipality
  (objektart Kantonsgebiet, BFS codes 9xxx and 2391 Staatswald Galm) and the two Kommunanzen are not
  part of any municipality; they are emitted as level 'pseudo' rows ('<KT>:<bfs_nummer>') that the
  build adds to canton and Swiss sums (include_pseudo), plus the published canton / Swiss areas
  (native) for the plausibility check.
  Area refers to the reference boundaries and is the same for every year (decision D16), so it is
  emitted for every STATPOP year (2010–latest) and the release year: density
  (pop_total / land area) can then be computed per year by the build.
Elevation (m a.s.l.): BFS historized boundaries G1, Z_AVG / Z_MED / Z_MIN / Z_MAX of the versions
  valid on the reference date (decision D19: G1 is the web geometry).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyogrio

from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_hist_boundaries.fetch import fetch_all as fetch_g1
from pipeline.sources.geo_identity.fetch import RELEASE, swissboundaries

SOURCE = "geo_identity"
GPKG = "swissBOUNDARIES3D_1_5_LV95_LN02.gpkg"
POP_YEARS = [str(y) for y in range(2010, 2026)]
AREA_PERIODS = [*POP_YEARS, RELEASE[:4]]


def _rows(df: pd.DataFrame, unit_col: str, level: str, metric_cols: dict[str, str], periods,
          provenance: str, note: str | None = None) -> pd.DataFrame:
    parts = []
    for col, mid in metric_cols.items():
        for p in periods:
            d = pd.DataFrame({"unit_id": df[unit_col].astype(str), "level": level,
                              "vintage": REFERENCE_DATE.isoformat(), "metric_id": mid, "period": p,
                              "value": pd.to_numeric(df[col], errors="coerce").astype(float)})
            parts.append(d)
    out = pd.concat(parts, ignore_index=True)
    out["status"] = np.where(out["value"].notna(), "ok", "no_data")
    out["precision"] = "exact"
    out["provenance"] = provenance
    out["source_id"] = SOURCE
    out["note"] = note
    return out[OBS_COLUMNS]


def _area() -> pd.DataFrame:
    path = f"/vsizip/{swissboundaries()}/{GPKG}"
    h = pyogrio.read_dataframe(path, layer="tlm_hoheitsgebiet", read_geometry=False)
    g = h[(h["icc"] == "CH") & (h["objektart"] == "Gemeindegebiet")].copy()
    assert g["bfs_nummer"].is_unique
    g["land"] = g["gem_flaeche"] - g["see_flaeche"]
    note = f"swissBOUNDARIES3D {RELEASE}, reference boundaries (same area for every year)"
    mun = _rows(g, "bfs_nummer", "gemeinde",
                {"gem_flaeche": "geo_area_total_ha", "see_flaeche": "geo_area_lake_ha", "land": "geo_area_land_ha"},
                AREA_PERIODS, "source_current_state", note)
    # native canton and national land area. Total and lake area are not emitted at those levels:
    # the published canton/Swiss totals include lake areas that belong to no municipality (e.g.
    # most of Lake Neuchâtel, Lake Thun, Lake Constance), so they are not comparable with sums of
    # municipalities. Land area differs only by the Kommunanzen (TI) and Staatswald Galm (FR).
    k = pyogrio.read_dataframe(path, layer="tlm_kantonsgebiet", read_geometry=False)
    cant = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    k = k[k["icc"] == "CH"].merge(cant[["canton_id", "canton"]], left_on="kantonsnummer", right_on="canton_id")
    k["land"] = k["kantonsflaeche"] - k["see_flaeche"]
    l = pyogrio.read_dataframe(path, layer="tlm_landesgebiet", read_geometry=False)
    l = l[l["icc"] == "CH"].assign(unit="CH")
    l["land"] = l["landesflaeche"] - l["see_flaeche"]
    nnote = f"swissBOUNDARIES3D {RELEASE}; includes lakes, Kommunanzen and state forest outside municipalities"
    k["total"] = k["kantonsflaeche"]
    l["total"] = l["landesflaeche"]
    cols = {"land": "geo_area_land_ha", "total": "geo_area_total_ha", "see_flaeche": "geo_area_lake_ha"}
    nat = [_rows(k, "canton", "kanton", cols, [RELEASE[:4]], "native", nnote),
           _rows(l, "unit", "schweiz", cols, [RELEASE[:4]], "native", nnote)]
    # territory outside municipalities (review round 1, defect 5): cantonal lake areas (BFS 9xxx),
    # Staatswald Galm and the two Ticino Kommunanzen, as level 'pseudo' rows '<KT>:<bfs_nummer>'.
    # metrics.yaml include_pseudo adds them to canton and Swiss sums, which then equal the published
    # canton areas (kantonsflaeche, see_flaeche).
    o = h[(h["icc"] == "CH") & (h["objektart"] != "Gemeindegebiet")].copy()
    o = o.merge(cant[["canton_id", "canton"]], left_on="kantonsnummer", right_on="canton_id")
    o["land"] = o["gem_flaeche"] - o["see_flaeche"]
    o["unit"] = o["canton"] + ":" + o["bfs_nummer"].astype(int).astype(str)
    ps = _rows(o, "unit", "pseudo", {"gem_flaeche": "geo_area_total_ha", "see_flaeche": "geo_area_lake_ha",
                                     "land": "geo_area_land_ha"}, AREA_PERIODS, "native",
               f"swissBOUNDARIES3D {RELEASE}: territory of the canton outside any municipality (objektart "
               "Kantonsgebiet / Kommunanz)")
    # review round 3 (X7): municipalities on a lake that is canton territory (Zürichsee in ZH, Thunersee,
    # Bodensee ...) have no lake area of their own; their lake share 0 % gets a note saying why
    shore = _lakeside_without_lake(path)
    lake0 = (mun["metric_id"] == "geo_area_lake_ha") & mun["unit_id"].isin(shore)
    mun.loc[lake0, "note"] = mun.loc[lake0, "unit_id"].map(shore)
    return pd.concat([mun, *nat, ps], ignore_index=True)


def _lakeside_without_lake(path: str) -> dict[str, str]:
    """BFS number -> note, for municipalities without lake area whose boundary touches (within 20 m) a lake
    area that belongs to no municipality (objektart Kantonsgebiet with see_flaeche > 0)."""
    h = pyogrio.read_dataframe(path, layer="tlm_hoheitsgebiet", columns=["icc", "objektart", "bfs_nummer", "name", "see_flaeche"])
    lk = h[(h["icc"] == "CH") & (h["objektart"] != "Gemeindegebiet") & (h["see_flaeche"].fillna(0) > 0)]
    g = h[(h["icc"] == "CH") & (h["objektart"] == "Gemeindegebiet") & (h["see_flaeche"].fillna(0) == 0)]
    out = {}
    for lake in lk.itertuples():
        near = g[g.geometry.intersects(lake.geometry.buffer(20))]
        name = str(lake.name).split(" (")[0]
        for b in near["bfs_nummer"].astype(int).astype(str):
            out[b] = (f"lake share 0 %: the municipality borders {name}, but that lake is canton territory, not divided "
                      f"among the municipalities")
    return out


def _elevation() -> pd.DataFrame:
    g = pyogrio.read_dataframe(fetch_g1()["g1"], read_geometry=False)
    ref = pd.Timestamp(REFERENCE_DATE)
    vf, vt = pd.to_datetime(g["VALID_FROM"]), pd.to_datetime(g["VALID_TO"])
    g = g[(g["GARTE"] == 11) & (g["CODE_ISO"] == "CH") & (vf <= ref) & (vt.isna() | (vt >= ref))]
    assert g["GDENR"].is_unique
    return _rows(g, "GDENR", "gemeinde",
                 {"Z_AVG": "geo_elev_mean", "Z_MED": "geo_elev_median", "Z_MIN": "geo_elev_min",
                  "Z_MAX": "geo_elev_max"}, [RELEASE[:4]], "source_current_state",
                 "BFS G1 generalized boundaries, version valid on the reference date")


def observations() -> pd.DataFrame:
    return pd.concat([_area(), _elevation()], ignore_index=True)
