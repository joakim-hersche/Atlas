"""Municipal tax multiplier (Steuerfuss) for natural persons from cantonal open data: canton Zürich only (so far).

ZH: column STF_O_KIRCHE1 = municipal multiplier without church tax (political + school municipality) in % of the simple
cantonal tax; verified on Zürich city 2026 = 119 %. The few municipalities with two multipliers (STF_O_KIRCHE2: Uster,
Turbenthal) get no value (two areas, no population weights). Periods 2012-2026; mergers: values kept only where the
mapping to the reference state is 1:1 (kthelp.to_ref). Other cantons: not_covered.
A multiplier is a percentage of the canton's *simple tax*, whose scale differs by canton: values are comparable within
a canton only, never across cantons.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.kt_finance import kthelp as K
from pipeline.sources.kt_tax_multipliers.fetch import SOURCE, zh

METRIC = "tax_mult_muni_nat"
NC = "no open municipal tax multiplier source cleared for this canton yet"


def zh_wide() -> pd.DataFrame:
    d = pd.read_csv(zh("timeseries"))
    two = d["STF_O_KIRCHE2"].fillna(0) > 0
    v = d["STF_O_KIRCHE1"].where(~two)
    return pd.DataFrame({"bfs_nr": d["BFSNR"], "period": d["YEAR"].astype(str), "mult": v})


def observations() -> pd.DataFrame:
    w = zh_wide()
    o = K.to_ref(w, {"mult": METRIC}, SOURCE, "ZH", rules={"mult": "not_aggregatable"})
    pers = sorted(set(w["period"]))
    covered = {METRIC: {"ZH"}}
    cp = {(METRIC, "ZH"): set(w.loc[w["mult"].notna(), "period"])}
    o = K.complete(o, SOURCE, covered, {}, NC, periods={METRIC: pers}, covered_periods=cp)
    gap = o["status"].eq("no_data") & o["note"].isna()
    o.loc[gap, "note"] = "two multipliers in the municipality (school areas) or no value in the ZH source"
    return o
