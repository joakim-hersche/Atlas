"""Spatial levels above the municipality and aggregation rules (brief 4.2 / 4.3).

membership()  one row per current municipality with the unit id of every level:
              bezirk, kanton, grossregion, sprachgebiet, agglomeration, arbeitsmarktgebiet,
              stadt_land, gemeindetyp (9 classes) — all valid on the reference date
aggregate(df, level, rule)
              df keyed by bfs_nr (reference state) -> one row per unit of `level`
              rules: 'sum' | 'ratio:<num>/<den>' | 'weighted_mean:<weight_col>' | 'not_aggregatable'
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE, interim_path

# level id -> column in the register API levels table (valid on the reference date)
LEVEL_COLUMNS = {
    "grossregion": "REGCH",
    "sprachgebiet": "SPRGEB2020",
    "agglomeration": "AGGL2020",
    "arbeitsmarktgebiet": "BAE2018",
    "stadt_land": "STALAN2020",
    "gemeindetyp": "GDETYP2020_9",
}
# codes meaning "not part of any unit" (excluded from aggregation)
NO_UNIT = {"agglomeration": {"0"}}
LEVELS = ["gemeinde", "bezirk", "kanton", *LEVEL_COLUMNS]


def membership() -> pd.DataFrame:
    mv, _ = load_backbone()
    cur = versions_at(mv, REFERENCE_DATE)[["hist_id", "bfs_nr", "name", "canton", "district_nr"]]
    lv = pd.read_parquet(interim_path("backbone", f"levels_{REFERENCE_DATE.isoformat()}.parquet"))
    m = cur.rename(columns={"canton": "kanton", "district_nr": "bezirk"}).copy()
    m["bezirk"] = m["bezirk"].astype("Int64").astype(str)
    lv = lv.set_index("BfsCode")
    for level, col in LEVEL_COLUMNS.items():
        if col in lv.columns:
            m[level] = m["bfs_nr"].map(lv[col].astype(str))
            if f"{col}_de" in lv.columns:
                m[f"{level}_name"] = m["bfs_nr"].map(lv[f"{col}_de"])
            m.loc[m[level].isin(NO_UNIT.get(level, set())), level] = pd.NA
    m["gemeinde"] = m["bfs_nr"].astype(str)
    return m.reset_index(drop=True)


def aggregate(df: pd.DataFrame, level: str, rule: str = "sum", value_col: str = "value",
              group_cols: list[str] | None = None) -> pd.DataFrame:
    """Aggregate municipality values (reference state) to a level.

    Units with any missing contributing value get NaN (no silent partial sums), and
    `n_missing` reports how many municipalities lacked a value.
    """
    group_cols = list(group_cols or [])
    m = membership()[["bfs_nr", level]].dropna(subset=[level])
    d = df.merge(m, on="bfs_nr", how="inner")
    keys = [level, *group_cols]
    g = d.groupby(keys, dropna=False)
    n_missing = g[value_col].apply(lambda s: int(s.isna().sum())) if value_col in d else None
    if rule == "sum":
        val = g[value_col].sum(min_count=1)
    elif rule.startswith("ratio:"):
        num, den = rule.split(":", 1)[1].split("/")
        val = g[num].sum(min_count=1) / g[den].sum(min_count=1)
        n_missing = g[num].apply(lambda s: int(s.isna().sum())) + g[den].apply(lambda s: int(s.isna().sum()))
    elif rule.startswith("weighted_mean:"):
        w = rule.split(":", 1)[1]
        d = d.assign(_vw=d[value_col] * d[w], _w=d[w].where(d[value_col].notna()))
        g = d.groupby(keys, dropna=False)
        val = g["_vw"].sum(min_count=1) / g["_w"].sum(min_count=1)
    elif rule == "not_aggregatable":
        val = g[value_col].apply(lambda s: s.iloc[0] if len(s) == 1 else np.nan)
    else:
        raise ValueError(f"unknown rule: {rule}")
    out = pd.DataFrame({"value": val})
    if n_missing is not None:
        out["n_missing"] = n_missing
        out.loc[out["n_missing"] > 0, "value"] = np.nan
    out["n_units"] = g.size()
    return out.reset_index().rename(columns={level: "unit_id"}).assign(level=level)


def run() -> str:
    m = membership()
    p = interim_path("backbone", f"membership_{REFERENCE_DATE.isoformat()}.parquet")
    m.to_parquet(p, index=False)
    return str(p)


if __name__ == "__main__":
    print(run())
