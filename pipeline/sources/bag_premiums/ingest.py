"""Health insurance (OKP/LAMal) premiums per municipality via its premium region, 2026 and 2027.

Two sets of metrics, all CHF per month and not re-aggregatable (regional tariffs):
1. BAG mean premium (praemienregionen-2027.xlsx, sheet D_PRIM): the BAG's estimated mean monthly
   premium per canton/region for children, young adults and adults, over all insurers, models and
   franchises, weighted by expected insured persons (premium year 2027).
2. Standard-model adult premium, franchise CHF 300, accident cover INCLUDED (the left-hand table
   "Mit Unfall" of the BAG premium overview PDF; the reference premium of the BAG/priminfo
   overviews): unweighted mean, median and minimum over the insurers listed for the canton/region
   ("Prämien – Grundversicherung", "Erwachsene"), premium years 2026 and 2027. Insurers listed for a
   canton may have restricted their activity to some regions; the PDF values are rounded to 10 Rp.

Region of each municipality:
  2027: D_PRIM (BFS numbers on the state of 1.1.2027). The eight reference municipalities that
        merge on 1.1.2027 (VD: Lucens, La Vallée de Joux, Gimel, Mathod-Suscévaz; sheet COM-MUT)
        take the value of the merged municipality (all mergers, one region each).
  2026: annex of the EDI ordinance, state 1.1.2026 (= reference state) for the multi-region
        cantons; municipalities of single-region cantons are region 0.
"""
from __future__ import annotations

import re
import subprocess

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bag_premiums.fetch import CURRENT_YEAR, annex_2026, overview, regions

SOURCE = "bag_premiums"
NUM = re.compile(r"^\d{2,4}\.\d$")
LOG: dict = {}


def _pages(year: int) -> list[str]:
    txt = subprocess.run(["pdftotext", "-layout", str(overview(year)), "-"], check=True,
                         capture_output=True, text=True).stdout
    return txt.split("\f")


def standard_adult_f300(year: int) -> pd.DataFrame:
    """Per canton, region and insurer: standard-model adult premium, franchise 300, with and
    without accident cover, from the PDF overview."""
    rows = []
    for p in _pages(year):
        head = p[:900]
        if "Prämien – Grundversicherung" not in head:
            continue
        if re.search(r"Junge Erwachsene\s*/|Kinder\s*/", head) or not re.search(r"Erwachsene\s*/", head):
            continue
        kt = re.search(rf"{year}\s+([A-Z]{{2}})\b", head).group(1)
        reg = int(re.search(r"Region / R[ée]gion[e]? (\d)", head).group(1))
        for line in p.splitlines():
            toks = re.split(r"\s{2,}", line.strip())
            names = [i for i, t in enumerate(toks) if t and not NUM.match(t)]
            if len(names) != 1 or names[0] == 0 or names[0] == len(toks) - 1:
                continue
            i = names[0]
            if not (NUM.match(toks[0]) and NUM.match(toks[i + 1])):
                continue
            if i > 6 or len(toks) - i - 1 > 6:
                continue
            rows.append({"canton": kt, "region": reg, "insurer": toks[i],
                         "with_acc": float(toks[0]), "without_acc": float(toks[i + 1])})
    d = pd.DataFrame(rows)
    if d.duplicated(["canton", "region", "insurer"]).any():
        raise ValueError(f"premiums {year}: duplicate insurer rows")
    LOG[year] = {"tables": int(d.groupby(["canton", "region"]).ngroups), "rows": len(d)}
    return d


def _ref() -> pd.DataFrame:
    mv, _ = load_backbone()
    return versions_at(mv, REFERENCE_DATE)[["bfs_nr", "canton"]].astype({"bfs_nr": int})


def region_2026() -> pd.DataFrame:
    a = pd.read_excel(annex_2026(), sheet_name=0, header=None, skiprows=14).iloc[:, :4]
    a.columns = ["canton", "bfs_nr", "name", "region"]
    a = a[pd.to_numeric(a["bfs_nr"], errors="coerce").notna()].astype({"bfs_nr": int, "region": int})
    ref = _ref().merge(a[["bfs_nr", "region"]], on="bfs_nr", how="left")
    # municipalities formed on 1.1.2026 that the annex still lists under their predecessors
    # (e.g. Fétigny-Ménières 2056 = Fétigny 2016 + Ménières 2027): region of the predecessors
    miss = ref["region"].isna()
    if miss.any():
        import datetime as dt
        from pipeline.backbone.vintage import crosswalk
        mv, _ = load_backbone()
        old = versions_at(mv, REFERENCE_DATE - dt.timedelta(days=1))[["hist_id", "bfs_nr"]]
        cw = crosswalk(REFERENCE_DATE)
        cw = cw[cw["weight"] > 0].merge(old, left_on="from_hist_id", right_on="hist_id")
        pre = cw.merge(a[["bfs_nr", "region"]], on="bfs_nr").groupby("to_bfs_nr")["region"].agg(["min", "max"])
        pre = pre[pre["min"] == pre["max"]]["min"]
        ref.loc[miss, "region"] = ref.loc[miss, "bfs_nr"].map(pre)
    multi = set(a["canton"])
    if ref.loc[ref["canton"].isin(multi), "region"].isna().any():
        raise ValueError("2026 annex: municipality of a multi-region canton without region")
    ref["region"] = ref["region"].fillna(0).astype(int)
    return ref


def _read_2027(sheet: str, skip: int, cols: list[str]) -> pd.DataFrame:
    d = pd.read_excel(regions(CURRENT_YEAR), sheet_name=sheet, header=None, skiprows=skip).iloc[:, :len(cols)]
    d.columns = cols
    return d


def region_2027() -> pd.DataFrame:
    """Reference municipality -> 2027 municipality, region and BAG mean premiums."""
    p = _read_2027("D_PRIM", 16, ["bfs27", "canton", "name", "region", "child", "young", "adult"])
    p = p[pd.to_numeric(p["bfs27"], errors="coerce").notna()].astype({"bfs27": int, "region": int})
    m = _read_2027("COM-MUT", 11, ["year", "bfs", "canton", "name", "mutation"])
    m = m[(m["year"] == CURRENT_YEAR) & m["mutation"].astype(str).str.startswith("fus")]
    fus = {int(b): int(str(t).split()[1]) for b, t in zip(m["bfs"], m["mutation"])}
    ref = _ref()
    ref["bfs27"] = ref["bfs_nr"].map(lambda b: fus.get(b, b))
    ref["merged_2027"] = ref["bfs_nr"].isin(fus) & (ref["bfs27"] != ref["bfs_nr"])
    out = ref.merge(p.drop(columns=["canton", "name"]), on="bfs27", how="left")
    if out["region"].isna().any():
        raise ValueError(f"2027: reference municipalities without region {out.loc[out['region'].isna(), 'bfs_nr'].tolist()}")
    return out


def _obs(df: pd.DataFrame, col: str, metric: str, period: str, note) -> pd.DataFrame:
    ok = df[col].notna()
    return pd.DataFrame({
        "unit_id": df["bfs_nr"].astype(str), "level": "gemeinde", "vintage": REFERENCE_DATE.isoformat(),
        "metric_id": metric, "period": period, "value": df[col].astype(float),
        "status": np.where(ok, "ok", "no_data"), "precision": "exact",
        "provenance": "source_current_state", "source_id": SOURCE, "note": note,
    })


def observations() -> pd.DataFrame:
    parts = []
    r27 = region_2027()
    note27 = np.where(r27["merged_2027"], "premium region of the municipality formed on 1.1.2027",
                      "premium region " + r27["canton"] + " " + r27["region"].astype(int).astype(str))
    for col, mid in (("adult", "kvg_mean_premium_adult"), ("young", "kvg_mean_premium_young"),
                     ("child", "kvg_mean_premium_child")):
        o = _obs(r27, col, mid, str(CURRENT_YEAR), note27)
        o["precision"] = "modelled"  # BAG estimate from expected insured numbers
        parts.append(o)
    for year, reg, note in ((2026, region_2026(), None), (CURRENT_YEAR, r27, note27)):
        s = standard_adult_f300(year)
        st = s.groupby(["canton", "region"])["with_acc"].agg(["mean", "median", "min", "size"]).reset_index()
        d = reg[["bfs_nr", "canton", "region"]].merge(st, on=["canton", "region"], how="left")
        if d["mean"].isna().any():
            raise ValueError(f"premiums {year}: no premium table for {d.loc[d['mean'].isna(), ['canton', 'region']].drop_duplicates().values.tolist()}")
        n = ("premium region " + d["canton"] + " " + d["region"].astype(str) + ", "
             + d["size"].astype(str) + " insurers") if note is None else note
        for col, mid in (("mean", "kvg_std300_mean_adult"), ("median", "kvg_std300_median_adult"),
                         ("min", "kvg_std300_min_adult")):
            parts.append(_obs(d, col, mid, str(year), n))
    return pd.concat(parts, ignore_index=True)[OBS_COLUMNS]
