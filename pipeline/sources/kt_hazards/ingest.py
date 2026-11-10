"""Residents in natural-hazard zones per municipality, from the cantonal hazard maps on geodienste.ch
(`*` metric, decision D6; MGDM 166.1 v1.3, layer synoptisches_gefahrengebiet).

Method (zonal statistics on the 100 m STATPOP lattice, pipeline/sources/meteoswiss_climate/zonal.py):
- STATPOP 2025 hectare residents (BBTOT) at the hectare centre, assigned to the reference-state
  municipality (zonal.population: centre in polygon, lake-shore hectares snapped within 500 m).
- The hazard polygons of the municipality's own canton are rasterized at the hectare centres:
  the process-wise hazard areas (layer gefahrengebiet, gefahrenstufe) and the synoptic map
  (synoptisches_gefahrengebiet, maximale_gefahrenstufe), whichever the canton delivers (AI only
  synoptic; AG, FR, GE, JU, SO, VS, ZH only process-wise). Overlaps keep the highest level, so
  all mapped processes are combined (flood, landslide, rockfall, avalanche; AG delivers floods
  only). The processes present per canton are in the row note.
  Order: nicht_gefaehrdet < Restgefaehrdung < gering (yellow) < mittel (blue) < erheblich (red).
- haz_residents_high:     residents in hectares whose centre lies in a red (erheblich) zone
  haz_residents_medium:   ... in a blue (mittel) zone (highest level = mittel)
  haz_residents_assessed: ... in any hazard polygon (any level incl. 'nicht gefährdet' and
                          residual hazard) or in the survey perimeter (erhebungsgebiet) where the
                          canton delivers one. Outside it the hazard is not assessed, not zero.
  haz_hectare_residents:  all hectare residents assigned to the municipality (denominator).
Cantons without free data (NW, OW, UR, VD: approval required; BS: not yet published) -> not_covered.
Period '2026' = state of the hazard maps at download (Nov 2026); population STATPOP 2025.
"""
from __future__ import annotations

import shutil

import numpy as np
import pandas as pd
import pyogrio
from rasterio.features import rasterize

from pipeline.common import interim_path
from pipeline.harmonize.helpers import emit
from pipeline.sources.kt_finance.kthelp import complete, ref_units
from pipeline.sources.kt_hazards.fetch import CANTONS, gpkg_zip, services
from pipeline.sources.meteoswiss_climate import zonal

SOURCE = "kt_hazards"
PERIOD = "2026"
POP_YEAR = 2025
LEVEL = {"nicht_gefaehrdet": 1, "Restgefaehrdung": 2, "restgefaehrdung": 2, "gering": 3, "mittel": 4,
         "erheblich": 5}
PROC = {"wasser": "flood", "rutschung": "landslide", "sturz": "rockfall", "lawine": "avalanche"}
METRICS = {"high": "haz_residents_high", "medium": "haz_residents_medium",
           "assessed": "haz_residents_assessed", "total": "haz_hectare_residents"}
NOT_COVERED = {
    "NW": "Nidwalden's hazard map on geodienste.ch requires approval for download ('Freigabe erforderlich')",
    "OW": "Obwalden's hazard map on geodienste.ch requires approval for download ('Freigabe erforderlich')",
    "UR": "Uri's hazard map on geodienste.ch requires approval for download ('Freigabe erforderlich')",
    "VD": "Vaud's hazard map on geodienste.ch requires approval for download ('Freigabe erforderlich')",
    "BS": "Basel-Stadt's hazard map is not yet published on geodienste.ch ('Im Aufbau')",
}


def _gpkg(kt: str):
    """The canton's GeoPackage, extracted from the cached zip to data/interim/kt_hazards/ (random
    access inside a deflated zip is too slow); derived file, regenerated when missing."""
    import zipfile
    out = interim_path("kt_hazards", f"gefahrenkarten_v1_3_{kt}_2056.gpkg")
    if not out.exists():
        with zipfile.ZipFile(gpkg_zip(kt)) as z:
            name = next(n for n in z.namelist() if n.endswith(".gpkg"))
            tmp = out.with_suffix(".part")
            with z.open(name) as src, open(tmp, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 24)
            tmp.replace(out)
    return out


def _layer(kt: str, layer: str, columns: list[str]):
    path = _gpkg(kt)
    try:
        if pyogrio.read_info(path, layer=layer)["features"] == 0:
            return None
        g = pyogrio.read_dataframe(path, layer=layer, columns=columns)
    except Exception:  # layer missing
        return None
    return g[g.geometry.notna() & ~g.geometry.is_empty]


def _raster(kt: str) -> tuple[np.ndarray, np.ndarray, dict]:
    """Highest hazard level per lattice cell (centre in polygon) from the process-wise hazard areas
    (gefahrengebiet) and the synoptic map (synoptisches_gefahrengebiet), whichever the canton
    delivers; plus the survey perimeter (erhebungsgebiet) where delivered."""
    shape = (zonal.HEIGHT, zonal.WIDTH)
    lvl = np.zeros(shape, dtype="uint8")
    info = {}
    procs = set()
    for layer, col in (("gefahrengebiet", "gefahrenstufe"), ("synoptisches_gefahrengebiet", "maximale_gefahrenstufe")):
        cols = [col, "hauptprozess"] if layer == "gefahrengebiet" else [col, "wasser", "rutschung", "sturz", "lawine"]
        g = _layer(kt, layer, cols)
        if g is None:
            info[layer] = 0
            continue
        lv = g[col].map(LEVEL)
        info[layer] = int(len(g))
        info[layer + "_unknown_levels"] = g.loc[lv.isna(), col].value_counts(dropna=False).to_dict()
        if layer == "gefahrengebiet":
            procs |= set(g["hauptprozess"].dropna().astype(str).str.lower())
        else:
            procs |= {p for p in ("wasser", "rutschung", "sturz", "lawine") if g[p].notna().any()}
        info["not_endangered_mapped"] = info.get("not_endangered_mapped", False) or bool(lv.eq(1).any())
        g = g.assign(lv=lv).dropna(subset=["lv"]).sort_values("lv")
        r = rasterize(((geom, int(v)) for geom, v in zip(g.geometry, g["lv"])), out_shape=shape,
                      transform=zonal.TRANSFORM, fill=0, dtype="uint8")  # later (higher) overwrite
        np.maximum(lvl, r, out=lvl)
        del g, r
    e = _layer(kt, "erhebungsgebiet", [])
    surveyed = np.zeros(shape, dtype=bool)
    info["erhebungsgebiet"] = 0 if e is None else int(len(e))
    if e is not None and len(e):
        surveyed = rasterize(((geom, 1) for geom in e.geometry), out_shape=shape,
                             transform=zonal.TRANSFORM, fill=0, dtype="uint8").astype(bool)
    info["processes"] = sorted(procs)
    return lvl, surveyed, info


def observations() -> pd.DataFrame:
    pop, ids, pinfo = zonal.population(POP_YEAR)
    print("kt_hazards population", pinfo)
    units = ref_units()
    kt_of = units.set_index("bfs_nr")["canton"]
    upd = {s["canton"]: (s.get("updated_at") or "")[:10] for s in services()}
    n = int(ids.max()) + 1
    canton_arr = np.zeros(n, dtype=object)
    canton_arr[kt_of.index.to_numpy()] = kt_of.to_numpy()
    cell_kt = canton_arr[ids]
    parts = []
    for kt in CANTONS:
        lvl, surveyed, info = _raster(kt)
        print("kt_hazards", kt, info)
        inkt = (cell_kt == kt) & (ids > 0)
        sel = inkt & (pop > 0)
        idx = ids[sel]
        w = pop[sel]
        lv = lvl[sel]
        res = pd.DataFrame({
            "bfs_nr": np.arange(n),
            "high": np.bincount(idx, weights=w * (lv == 5), minlength=n),
            "medium": np.bincount(idx, weights=w * (lv == 4), minlength=n),
            "assessed": np.bincount(idx, weights=w * ((lv > 0) | surveyed[sel]), minlength=n),
            "total": np.bincount(idx, weights=w, minlength=n),
        })
        res = res[res["bfs_nr"].isin(units.loc[units["canton"] == kt, "bfs_nr"])].assign(period=PERIOD)
        o = emit(res, METRICS, "period", SOURCE, precision="modelled", provenance="source_current_state")
        pr = ", ".join(PROC.get(p, p) for p in info["processes"]) or "?"
        o["note"] = (f"geodienste.ch Gefahrenkarte {kt} (updated {upd.get(kt, '?')}; processes: {pr}); "
                     f"STATPOP {POP_YEAR} hectare residents")
        if not info.get("not_endangered_mapped") and not info["erhebungsgebiet"]:
            # neither a survey perimeter nor 'not endangered' areas: the assessed area is unknown
            a = o["metric_id"].eq(METRICS["assessed"])
            o.loc[a, "value"] = np.nan
            o.loc[a, "status"] = "no_data"
            o.loc[a, "note"] = (f"{kt} delivers neither the survey perimeter nor 'not endangered' areas: "
                                "assessed perimeter unknown")
        parts.append(o)
    obs = pd.concat(parts, ignore_index=True)
    covered = {m: set(CANTONS) for m in METRICS.values()}
    return complete(obs, SOURCE, covered, NOT_COVERED,
                    "no cantonal hazard map available", precision="modelled")
