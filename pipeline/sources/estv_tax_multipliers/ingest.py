"""ESTV tax multipliers (Steuerfüsse) per municipality and tax year 2010-2026: cantonal and
municipal multiplier for the income and the wealth tax of natural persons, in %.

Each year lists the municipalities of that tax year; the state is inferred per year and the values
are mapped to the reference state with rule 'not_aggregatable' (kept only where the municipality is
1:1 with a reference municipality; merged/split cases get status not_applicable).
Multipliers apply to different cantonal tariffs, so they are comparable within a canton only.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.estv_dbst.refhelp import per_period_to_reference
from pipeline.sources.estv_tax_multipliers.fetch import SOURCE, YEARS, rates

VINTAGE_LOG: dict = {}
COLS = {4: "cant_inc", 5: "mun_inc", 9: "cant_wlth", 10: "mun_wlth"}
METRICS = {"cant_inc": "tax_mult_cantonal_income", "mun_inc": "tax_mult_municipal_income",
           "cant_wlth": "tax_mult_cantonal_wealth", "mun_wlth": "tax_mult_municipal_wealth"}


def load_wide() -> pd.DataFrame:
    parts = []
    for y in YEARS:
        d = pd.read_excel(rates(y), header=None)
        hdr = d.index[d[2].astype(str).str.strip() == "BfS-Id"][0]
        if str(d.iloc[1, 0]) != str(y) or list(d.iloc[hdr, 4:6]) != ["Kanton", "Gemeinde"] \
                or list(d.iloc[hdr, 9:11]) != ["Kanton", "Gemeinde"]:
            raise ValueError(f"unexpected layout in tax-rates export {y}")
        d = d.iloc[hdr + 1:]
        d = d[pd.to_numeric(d[2], errors="coerce").notna()]
        w = pd.DataFrame({"bfs_nr": d[2].astype(int).to_numpy(), "period": str(y)})
        for c, name in COLS.items():
            w[name] = pd.to_numeric(d[c], errors="coerce").to_numpy()
        parts.append(w)
    return pd.concat(parts, ignore_index=True)


def observations() -> pd.DataFrame:
    w = load_wide()
    return per_period_to_reference(w, METRICS, SOURCE, rules={c: "not_aggregatable" for c in METRICS},
                                   log=VINTAGE_LOG)
