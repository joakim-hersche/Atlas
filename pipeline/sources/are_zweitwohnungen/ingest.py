"""ARE Wohnungsinventar / Zweitwohnungsanteil – dwellings, primary homes and second homes per
municipality, one release per data date (2016-12, 2017-12, then March and October since 2019).

Each release is on its own municipality state (metadata sheet: 'Gemeindestand 1.1.<year>'); the
state is inferred from the BFS numbers per release and reprojected to the reference state
(counts summed). Period = month of the data date ('YYYY-MM').
Second homes = total dwellings − primary homes − dwellings assimilated to primary homes
(ZWG_3150 − ZWG_3010 − ZWG_3100); their share reproduces the published ZWG_3120.
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from pipeline.sources.are_zweitwohnungen.fetch import SOURCE, items, release
from pipeline.sources.estv_dbst.refhelp import per_period_to_reference

VINTAGE_LOG: dict = {}


def _read(href: str) -> pd.DataFrame:
    z = zipfile.ZipFile(release(href))
    raw = z.read(z.namelist()[0])
    x = pd.ExcelFile(io.BytesIO(raw))
    sheet = [s for s in x.sheet_names if not s.startswith("Metadaten")][0]
    df = x.parse(sheet)
    df = df.rename(columns={"GdeNr": "Gem_No"})
    df = df[pd.to_numeric(df["Gem_No"], errors="coerce").notna()].copy()
    df["bfs_nr"] = df["Gem_No"].astype(int)
    if "Status" not in df:
        df["Status"] = pd.NA
    return df


def load_wide() -> pd.DataFrame:
    parts = []
    for rel, ddate, href in items():
        df = _read(href)
        tot, prim, assim = (pd.to_numeric(df[c], errors="coerce") for c in ("ZWG_3150", "ZWG_3010", "ZWG_3100"))
        parts.append(pd.DataFrame({
            "bfs_nr": df["bfs_nr"], "period": ddate[:7],
            "dw_total": tot, "dw_primary": prim + assim, "dw_second": tot - prim - assim,
            "law": pd.to_numeric(df["Status"], errors="coerce"),
            "pub_share": pd.to_numeric(df["ZWG_3120"], errors="coerce"),
        }))
    return pd.concat(parts, ignore_index=True)


def observations() -> pd.DataFrame:
    w = load_wide()
    # check: recomputed share reproduces the published ZWG_3120
    chk = (w["dw_second"] / w["dw_total"] * 100 - w["pub_share"]).abs()
    if (chk > 0.06).sum() > 0:
        raise ValueError(f"second-home share does not reproduce ZWG_3120 for {(chk > 0.06).sum()} rows")
    obs = per_period_to_reference(
        w, {"dw_total": "zw_dwellings_total", "dw_primary": "zw_primary_dwellings",
            "dw_second": "zw_second_homes", "law": "zw_subject_to_law"},
        SOURCE, rules={"law": "not_aggregatable"}, log=VINTAGE_LOG)
    # 2016-12 and 2017-12 releases carry no Status column
    m = (obs["metric_id"] == "zw_subject_to_law") & obs["period"].isin(["2016-12", "2017-12"])
    obs = obs[~m]
    return obs.reset_index(drop=True)
