"""Arealstatistik (land use statistics) per municipality and survey period, 1979/85 – 2020/25.

BFS SDMX (CH1.AREA): DF_AREA_NOAS 1.1.0 (standard nomenclature NOAS04, hectares; dims NOAS,
PERIOD A1..A5, REGION) and DF_AREA_IMPV 1.0.0 (soil sealing). Geo codes on the 2026 state
(codelist CL_AREA_HIER_REGION_2026_DIFF; the hectare points are re-assigned by BFS, so the series
are on constant boundaries). The 2020/25 survey (A5) is still running: only the municipalities
already surveyed have values; the rest get status 'not_covered'. Codes 9xxx (lake areas outside
municipalities) and the condominium areas 2391, 5391, 5394 are only in canton/national totals:
they are kept as level 'pseudo' rows (unit_id '<canton>:<code>', or '<canton>:<district>:<code>'
for the condominium areas, canton/district from the codelist parents) and their national sum as
level 'unallocated'. Checked for every period and class: canton = Σ municipalities + these units
exactly, Switzerland = Σ cantons exactly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_sdmx.fetch import data
from pipeline.sources.bfs_sdmx.harmonize import pivot, to_observations

SOURCE = "bfs_arealstatistik"
AG = "CH1.AREA"
GEO = "REGION"
PERIODS = {"A1": "1979/85", "A2": "1992/97", "A3": "2004/09", "A4": "2013/18", "A5": "2020/25"}
LATEST = "2020/25"
NOAS = {
    "area_settlement_ha": "1", "area_agriculture_ha": "2", "area_wooded_ha": "3", "area_unproductive_ha": "4",
    "area_industrial_ha": "101", "area_building_ha": "102", "area_transport_ha": "103",
    "area_water_ha": ["413", "414"], "area_glacier_ha": "417",
}
NOT_COVERED = "2020/25 survey not yet completed for this municipality (BFS publishes it canton by canton)"


def wide() -> pd.DataFrame:
    d = data(AG, "DF_AREA_NOAS", "1.1.0", {"NOAS": ["1", "2", "3", "4", "101", "102", "103", "413", "414", "417"]})
    w = pivot(d, GEO, {**{k: {"NOAS": v} for k, v in NOAS.items()},
                       "area_total_ha": {"NOAS": ["1", "2", "3", "4"]}}, period_col="PERIOD")
    s = data(AG, "DF_AREA_IMPV", "1.0.0", {"NOLC": ["1", "2"]})
    w = w.merge(pivot(s, GEO, {"area_sealed_ha": {"NOLC": "1"}}, period_col="PERIOD"), on=[GEO, "PERIOD"], how="left")
    # settlement area of the first survey, attached to every period as the base of the change index
    base = w.loc[w["PERIOD"] == "A1", [GEO, "area_settlement_ha"]].rename(columns={"area_settlement_ha": "area_settlement_base_ha"})
    w = w.merge(base, on=GEO, how="left")
    w["area_settlement_base_ha__status"] = np.where(w["area_settlement_base_ha"].notna(), "ok", "no_data")
    w["PERIOD"] = w["PERIOD"].map(PERIODS)
    return w


def _parents() -> dict[str, str]:
    """Parent of every code in the REGION codelist (cached structure file)."""
    import re

    from pipeline.sources.bfs_sdmx.fetch import BASE, _get
    p = _get(f"{BASE}/dataflow/{AG}/DF_AREA_NOAS/1.1.0", "DF_AREA_NOAS_1.1.0.structure.xml",
             params={"references": "all"})
    s = p.read_text(encoding="utf-8")
    blk = s[s.index('id="CL_AREA_HIER_REGION_2026_DIFF"'):]
    blk = blk[:blk.index("</structure:Codelist>")]
    out = {}
    for m in re.finditer(r'<structure:Code id="([^"]+)">(.*?)</structure:Code>', blk, re.S):
        r = re.search(r'Ref id="([^"]+)"', m.group(2))
        out[m.group(1)] = r.group(1) if r else None
    return out


def _outside_rows(w: pd.DataFrame, cols: list[str], obs: pd.DataFrame) -> pd.DataFrame:
    """Lake areas (9xxx) and condominium areas: level 'pseudo' + national sum 'unallocated'."""
    from pipeline.harmonize.helpers import emit
    from pipeline.sources.bfs_sdmx.fetch import geo_level
    par = _parents()

    def up(c, lvl):
        c = par.get(c)
        while c and geo_level(c) != lvl:
            c = par.get(c)
        return c

    ref_units = set(obs.loc[obs["level"] == "gemeinde", "unit_id"])
    geo = w[GEO].astype(str)
    is_lake = geo.str.fullmatch(r"9\d{3}")
    is_cond = (geo.map(geo_level) == "gemeinde") & ~geo.str.lstrip("0").isin(ref_units)
    x = w[is_lake | is_cond].copy()
    kt = x[GEO].map(lambda c: up(c, "kanton"))
    bz = x[GEO].map(lambda c: up(c, "bezirk"))
    x["unit"] = [f"{k}:{int(b[2:])}:{c}" if isinstance(b, str) else f"{k}:{c}" for k, b, c in zip(kt, bz, x[GEO])]
    ps = emit(x, {c: c for c in cols}, "PERIOD", SOURCE, level="pseudo", unit_col="unit", precision="exact",
              provenance="native")
    ps = ps[ps["status"] == "ok"]
    ps["note"] = "lake area outside municipalities (9xxx) or condominium area (Kommunanz): in canton totals only"
    nat = x.groupby("PERIOD")[cols].sum(min_count=1).reset_index().assign(unit="unallocated")
    un = emit(nat, {c: c for c in cols}, "PERIOD", SOURCE, level="unallocated", unit_col="unit",
              precision="exact", provenance="native")
    un = un[un["status"] == "ok"]
    un["note"] = "lake areas outside municipalities and condominium areas (in the Swiss total, in no municipality)"
    return pd.concat([ps, un], ignore_index=True)


def observations() -> pd.DataFrame:
    w = wide()
    cols = [*NOAS, "area_total_ha", "area_sealed_ha", "area_settlement_base_ha"]
    obs, _ = to_observations(w, GEO, "PERIOD", {c: c for c in cols}, SOURCE)
    outside = _outside_rows(w, cols, obs)
    obs = obs[~((obs["metric_id"] == "area_settlement_base_ha") & (obs["period"] == "1979/85"))]
    # municipalities without a 2020/25 value yet -> explicit 'not_covered' rows
    gem = obs[obs["level"] == "gemeinde"]
    units = sorted(set(gem["unit_id"]))
    have = set(zip(gem.loc[gem["period"] == LATEST, "unit_id"], gem.loc[gem["period"] == LATEST, "metric_id"]))
    extra = [(u, m) for m in cols for u in units if (u, m) not in have]
    add = pd.DataFrame(extra, columns=["unit_id", "metric_id"]).assign(
        level="gemeinde", vintage=REFERENCE_DATE.isoformat(), period=LATEST, value=np.nan,
        status="not_covered", precision="exact", provenance="source_current_state", source_id=SOURCE,
        note=NOT_COVERED)
    outside = outside[~((outside["metric_id"] == "area_settlement_base_ha") & (outside["period"] == "1979/85"))]
    return pd.concat([obs, add[OBS_COLUMNS], outside], ignore_index=True)
