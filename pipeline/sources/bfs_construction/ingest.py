"""Construction and dwelling statistics per municipality (BFS Bau- und Wohnbaustatistik, PxWeb).

New dwellings and new residential buildings
  2013–latest  px-x-0904030000_105 (dwellings × rooms; index geo codes), _106 (buildings × type),
               _107 (dwellings × building type); one municipality state (BFS re-projection)
  1995–2012    px-x-0904030000_101 / _102 / _103: the geography lists every municipality that
               existed in the period, each year on its own state -> mapped per year (state of
               31 December), crosswalked to the reference state
Construction expenditure and investment (unit: CHF 1000)
  1994–latest  px-x-0904010000_201 (by client, works) and _203 (by category of structure);
               one municipality state. '76xx … (Unzuteilbar)' pseudo-units (amounts not allocatable
               to a municipality; 7601–7626 per canton, 7600 'Schweiz (Unzuteilbar)' for amounts
               not allocatable to any canton) are not municipality rows. They are kept as level
               'pseudo' rows (unit_id '<canton>:76cc', 'CH:7600') and their national sum as level
               'unallocated', so that canton = Σ municipalities + 76cc and
               Switzerland = Σ cantons + 7600 can be reconciled (verified for every year/metric:
               canton residual 0 except canton transfers, Clavaleyres BE→FR).
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.bfs_bevnat_bilanz.pxgeo import geo_codes, to_obs
from pipeline.sources.bfs_pxweb.fetch import metadata, query_codes

SOURCE = "bfs_construction"
CANTONS = "ZH BE LU UR SZ OW NW GL ZG FR SO BS BL SH AR AI SG GR AG TG TI VD VS NE GE JU".split()


def _years(db: str) -> dict[str, str]:
    v = next(v for v in metadata(db)["variables"] if v["code"] == "Jahr")
    return dict(zip(v["values"], v["valueTexts"]))


def _series(db: str, select: dict, var: str, groups: dict[str, list[str]], exclude=lambda t: False) -> pd.DataFrame:
    """Sum the codes of `var` per group; returns a wide frame keyed by geo × year."""
    geo_var = metadata(db)["variables"][0]["code"]
    codes, _, _ = geo_codes(db, geo_var, exclude=exclude)
    df = query_codes(db, {geo_var: "*", "Jahr": "*", var: sorted({c for v in groups.values() for c in v}), **select})
    yrs = _years(db)
    df["year"] = df["Jahr"].map(yrs)
    df["geo"] = df[geo_var].map(codes)
    out = None
    for name, cc in groups.items():
        s = df[df[var].isin(cc)].groupby(["geo", "year"])["value"].sum(min_count=len(cc)).rename(name)
        out = s.to_frame() if out is None else out.join(s, how="outer")
    return out


def _dwellings(report: dict) -> list[pd.DataFrame]:
    parts = []
    rooms, btype = "Anzahl Zimmer", "Gebäudetyp"
    new = (_series("px-x-0904030000_105", {}, rooms, {"con_new_dwellings": ["0"]})
           .join(_series("px-x-0904030000_107", {}, btype,
                         {"con_new_dw_sfh": ["1"], "con_new_dw_mfh": ["2"]}), how="outer")
           .join(_series("px-x-0904030000_106", {}, btype,
                         {"con_new_res_buildings": ["0"], "con_new_sfh_buildings": ["1"]}), how="outer")
           .reset_index())
    cols = [c for c in new.columns if c.startswith("con_")]
    r = {}
    parts.append(to_obs(new, "geo", "year", {c: c for c in cols}, SOURCE, report=r))
    report["dwellings_2013"] = r
    old = (_series("px-x-0904030000_101", {}, rooms, {"con_new_dwellings": ["0"]})
           .join(_series("px-x-0904030000_103", {}, btype,
                         {"con_new_dw_sfh": ["1", "2"], "con_new_dw_mfh": ["3"]}), how="outer")
           .join(_series("px-x-0904030000_102", {}, btype,
                         {"con_new_res_buildings": ["0"], "con_new_sfh_buildings": ["1", "2"]}), how="outer")
           .reset_index())
    r = {}
    parts.append(to_obs(old, "geo", "year", {c: c for c in cols}, SOURCE, per_year_state=True,
                        published_on_current_state=False, report=r))
    report["dwellings_1995"] = r
    return parts


def _unalloc(label: str) -> bool:
    return "Unzuteilbar" in label


def _unalloc_rows(w: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """'Unzuteilbar' amounts: per 76xx code as level 'pseudo', national sum as 'unallocated'."""
    from pipeline.harmonize.helpers import emit
    u = w[w["geo"].astype(str).str.fullmatch(r"76\d\d")].copy()
    # 76cc: cc = canton number (01 ZH … 26 JU); 7600 = not allocatable to a canton
    u["unit"] = [("CH" if int(g) == 7600 else CANTONS[int(g) - 7601]) + ":" + g for g in u["geo"]]
    ps = emit(u, {c: c for c in cols}, "year", SOURCE, level="pseudo", unit_col="unit", precision="exact",
              provenance="native")
    ps = ps[ps["status"] == "ok"]
    ps["note"] = "amount BFS cannot allocate to a municipality (76cc = canton cc, 7600 = no canton)"
    nat = u.groupby("year")[cols].sum(min_count=1).reset_index().assign(unit="unallocated")
    un = emit(nat, {c: c for c in cols}, "year", SOURCE, level="unallocated", unit_col="unit",
              precision="exact", provenance="native")
    un = un[un["status"] == "ok"]
    un["note"] = "sum of the 'Unzuteilbar' (76xx) amounts: in the Swiss total, not in any municipality"
    return pd.concat([ps, un], ignore_index=True)


def _investment(report: dict) -> pd.DataFrame:
    db, cl, st, wk, ob = ("px-x-0904010000_201", "Art der Auftraggeber", "Art der Bauwerke", "Art der Arbeiten",
                          "Beobachtungseinheit")
    a = _series(db, {cl: ["0"], st: ["0"], ob: ["kost_j"]}, wk,
                {"con_exp_total": ["0"], "con_inv_total": ["4"], "con_inv_new": ["1"], "con_inv_renovation": ["2"],
                 "con_exp_maintenance": ["3"]}, exclude=_unalloc)
    b = _series(db, {wk: ["0"], st: ["0"], ob: ["kost_j"]}, cl,
                {"con_exp_public": ["1"], "con_exp_private": ["2"]}, exclude=_unalloc)
    c = _series("px-x-0904010000_203", {"Art der Auftraggeber": ["0"], ob: ["kost_j"]}, "Kategorie der Bauwerke",
                {"con_inv_residential": ["900"]}, exclude=_unalloc)
    w = a.join(b, how="outer").join(c, how="outer").reset_index()
    cols = [x for x in w.columns if x.startswith("con_")]
    r = {}
    out = to_obs(w, "geo", "year", {x: x for x in cols}, SOURCE, report=r)
    report["investment"] = r
    # the same cubes again with the 76xx units mapped to their own codes (cached responses)
    keep = lambda t: False
    a2 = _series(db, {cl: ["0"], st: ["0"], ob: ["kost_j"]}, wk,
                 {"con_exp_total": ["0"], "con_inv_total": ["4"], "con_inv_new": ["1"], "con_inv_renovation": ["2"],
                  "con_exp_maintenance": ["3"]}, exclude=keep)
    b2 = _series(db, {wk: ["0"], st: ["0"], ob: ["kost_j"]}, cl,
                 {"con_exp_public": ["1"], "con_exp_private": ["2"]}, exclude=keep)
    c2 = _series("px-x-0904010000_203", {"Art der Auftraggeber": ["0"], ob: ["kost_j"]}, "Kategorie der Bauwerke",
                 {"con_inv_residential": ["900"]}, exclude=keep)
    w2 = a2.join(b2, how="outer").join(c2, how="outer").reset_index()
    return pd.concat([out, _unalloc_rows(w2, cols)], ignore_index=True)


def observations(report: dict | None = None) -> pd.DataFrame:
    rep = report if report is not None else {}
    return pd.concat([*_dwellings(rep), _investment(rep)], ignore_index=True)
