"""ESTV tax burden on gross income per municipality, 2010-2026, for five standard cases
(see fetch.CASES): total burden in % of gross income (federal + cantonal + municipal + church +
personal tax) and the federal, cantonal, municipal and church parts (CHF / gross income * 100).
Church tax for a member of the reformed church; no wealth (fortune 0).

Tax burdens are model results for one case, not counts: rule 'not_aggregatable' when mapping to
the reference state (kept only where the municipality maps 1:1) and at higher levels.
"""
from __future__ import annotations

import pandas as pd

from pipeline.sources.estv_dbst.refhelp import per_period_to_reference
from pipeline.sources.estv_tax_burden.fetch import CASES, SOURCE, YEARS, burden

VINTAGE_LOG: dict = {}
PARTS = {"federal": "Bundessteuer\nCHF", "cantonal": "Kantonssteuer\nCHF",
         "municipal": "Gemeindesteuer\nCHF", "church": "Kirchensteuer\nCHF"}


def _read(case: str, year: int) -> pd.DataFrame:
    model, income, label = CASES[case]
    d = pd.read_excel(burden(case, year), header=None)
    if (str(d.iloc[1, 0]).strip(), str(d.iloc[3, 0]), float(d.iloc[4, 2])) != (label, str(year), float(income)) \
            or str(d.iloc[2, 0]).strip() != "Reformiert":
        raise ValueError(f"unexpected header in burden export {case} {year}")
    hdr = d.index[d[2].astype(str).str.strip() == "BfS-Id"][0]
    cols = [str(c).strip() for c in d.iloc[hdr]]
    d = d.iloc[hdr + 1:].copy()
    d.columns = cols
    d = d[pd.to_numeric(d["BfS-Id"], errors="coerce").notna()]
    if d["BfS-Id"].duplicated().any():
        raise ValueError(f"duplicate municipalities in {case} {year}")
    out = pd.DataFrame({"bfs_nr": d["BfS-Id"].astype(int).to_numpy(), "period": str(year)})
    out[f"{case}__total"] = pd.to_numeric(d["Gesamtsteuerbelastung in\n%"], errors="coerce").to_numpy()
    for k, c in PARTS.items():
        out[f"{case}__{k}"] = pd.to_numeric(d[c], errors="coerce").to_numpy() / income * 100
    return out.set_index(["bfs_nr", "period"])


def load_wide() -> pd.DataFrame:
    years = []
    for y in YEARS:
        years.append(pd.concat([_read(c, y) for c in CASES], axis=1))
    return pd.concat(years).reset_index()


def metric_map() -> dict[str, str]:
    m = {}
    for c in CASES:
        m[f"{c}__total"] = f"tax_burden_{c}"
        for k in PARTS:
            m[f"{c}__{k}"] = f"tax_burden_{c}_{k}"
    return m


def observations() -> pd.DataFrame:
    w = load_wide()
    mm = metric_map()
    return per_period_to_reference(w, mm, SOURCE, rules={c: "not_aggregatable" for c in mm},
                                   precision="modelled", log=VINTAGE_LOG)
