"""Structural Survey (SE): main languages by statistical city, 5-year pooled, with 95 % confidence intervals
(BFS table su-d-40.02.01.08.31, editions 2010-2014 ... latest). Partial coverage: the ~170 statistical cities.

Cities are keyed by NAME only. The name is matched to the municipality register state at the end of the
pooling period (data/interim/backbone/municipality_version.parquet); the match must be unique. A city whose
territory changed since the survey (merger or split between the end of the pooling period and the reference state,
including absorbing other municipalities) is not delivered for that edition (counts would describe another
territory), and is logged in UNCHANGED_REJECTED.
Rows: level gemeinde (vintage = reference state; the unit is unchanged), precision survey, provenance native; and
the national row 'Schweiz' (level schweiz). Population: permanent residents in private households. Several main
languages per person (up to three) are possible, so the shares add up to more than 100 %.
BFS flags: 'X' (4 or fewer observations) -> status suppressed; '( )' (49 or fewer observations, read from the
cell number format) -> value kept, note 'low reliability'.
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_se_language_cities.fetch import SOURCE, edition_file, editions

LANG = {"Total Bevölkerung": "pop", "Deutsch": "de", "Französisch": "fr", "Italienisch": "it",
        "Rätoromanisch": "rm", "Englisch": "en", "Andere": "other", "Hauptsprache unbekannt": "unknown"}
LOW_NOTE = "low reliability: extrapolation from 49 or fewer observations (BFS '( )')"
SUPPRESSED_NOTE = "suppressed: 4 or fewer observations (BFS 'X')"
UNMATCHED: list = []
CHANGED: list = []


def _grid(path):
    """(values, bracketed) as 2-D lists; bracketed = number format shows '( )'. Legacy .xls are read by magic bytes."""
    if open(path, "rb").read(4) == b"\xd0\xcf\x11\xe0":
        import xlrd
        wb = xlrd.open_workbook(path, formatting_info=True)
        sh = wb.sheet_by_index(0)
        vals, br = [], []
        for r in range(sh.nrows):
            vrow, brow = [], []
            for c in range(sh.ncols):
                cell = sh.cell(r, c)
                v = cell.value if cell.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK) else None
                brow.append("(" in wb.format_map[wb.xf_list[cell.xf_index].format_key].format_str)
                vrow.append(v)
            vals.append(vrow)
            br.append(brow)
        return vals, br
    import openpyxl
    ws = openpyxl.load_workbook(path).worksheets[0]
    vals = [[c.value for c in row] for row in ws.iter_rows()]
    br = [["(" in (c.number_format or "") for c in row] for row in ws.iter_rows()]
    return vals, br


def _norm(s) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(s)).lower()).strip()


def _lookup(end: pd.Timestamp) -> tuple[dict[str, int], set[int]]:
    """name -> BFS number of the municipalities valid at `end` (unique names only), and the BFS numbers touched by a
    merger / split / transfer between `end` and the reference date."""
    mv, pair = load_backbone()
    cur = versions_at(mv, end.date())
    names = cur.assign(k=cur["name"].map(_norm)).drop_duplicates(["k", "bfs_nr"])
    uniq = names.groupby("k")["bfs_nr"].nunique()
    look = {k: int(b) for k, b in zip(names["k"], names["bfs_nr"]) if uniq[k] == 1}
    w = pair[(pd.to_datetime(pair["date"]) > end) & (pd.to_datetime(pair["date"]) <= pd.Timestamp(REFERENCE_DATE))]
    mv_ = w[w["from_bfs_nr"] != w["to_bfs_nr"]]
    return look, set(mv_["from_bfs_nr"].astype(int)) | set(mv_["to_bfs_nr"].astype(int))


def parse_edition(path, period: str) -> pd.DataFrame:
    vals, br = _grid(path)
    hdr_row = next(i for i, r in enumerate(vals) if "Total Bevölkerung" in [str(v).strip() for v in r])
    hdr = vals[hdr_row]
    c0 = [str(v).strip() for v in hdr].index("Total Bevölkerung")
    cols = {}
    for j, v in enumerate(hdr):
        key = next((k for k in LANG if v is not None and str(v).strip().startswith(k)), None)
        if key:
            cols[LANG[key]] = j
    end = pd.Timestamp(f"{period[-4:]}-12-31")
    look, touched = _lookup(end)
    # the first editions give the CI as a fraction, later ones in percent: decide on the largest population CI
    pop_ci = [r[c0 + 1] for r in vals[hdr_row + 2:] if isinstance(r[c0 + 1], (int, float))]
    ci_factor = 100.0 if pop_ci and max(pop_ci) < 0.5 else 1.0
    rows = []
    for i, r in enumerate(vals[hdr_row + 2:], start=hdr_row + 2):
        name = r[c0 - 1]
        if not isinstance(r[c0], (int, float)) or name is None:
            continue
        nm = str(name).strip()
        if nm == "Schweiz":
            level, unit = "schweiz", "CH"
        elif nm.startswith("Total"):
            continue
        else:
            nr = look.get(_norm(nm))
            if nr is None:
                UNMATCHED.append((period, nm))
                continue
            if nr in touched:
                CHANGED.append((period, nm, nr))
                continue
            level, unit = "gemeinde", str(nr)
        for lang, j in cols.items():
            v, ci = r[j], r[j + 1]
            if isinstance(v, (int, float)):
                rec = dict(value=float(v), status="ok", note=LOW_NOTE if br[i][j] else None)
                cival = float(ci) * ci_factor if isinstance(ci, (int, float)) else np.nan
            else:
                x = str(v).strip() == "X"
                rec = dict(value=np.nan, status="suppressed" if x else "no_data",
                           note=SUPPRESSED_NOTE if x else f"BFS '{v}'")
                cival = np.nan
            rows.append(dict(level=level, unit_id=unit, lang=lang, ci=cival, **rec))
    df = pd.DataFrame(rows)
    df["period"] = period
    return df


SHARE_LANGS = ["de", "fr", "it", "rm", "en", "other"]


def to_obs(df: pd.DataFrame) -> pd.DataFrame:
    """Population count, language shares (% of the city's residents) and approximate CI half-widths (pp)."""
    key = ["level", "unit_id", "period"]
    pop = df[df["lang"] == "pop"].set_index(key)["value"]
    sh = df[df["lang"].isin(SHARE_LANGS)].copy()
    popv = pop.reindex(pd.MultiIndex.from_frame(sh[key])).to_numpy()
    sh["share"] = sh["value"] / popv * 100
    base = sh.assign(metric_id="lang_sec_" + sh["lang"] + "_share", value=sh["share"])
    base["status"] = np.where(base["value"].notna(), "ok", base["status"].where(base["status"] != "ok", "no_data"))
    ci = sh.assign(metric_id="lang_sec_" + sh["lang"] + "_share_ci", value=sh["share"] * sh["ci"] / 100)
    ci["status"] = np.where(ci["value"].notna(), "ok", ci["status"].where(ci["status"] != "ok", "no_data"))
    ci["note"] = np.where(ci["value"].isna(), ci["note"], None)
    pop_rows = df[df["lang"] == "pop"].assign(metric_id="lang_sec_pop")
    out = pd.concat([pop_rows, base, ci], ignore_index=True)
    out["precision"], out["provenance"], out["source_id"] = "survey", "native", SOURCE
    out["vintage"] = REFERENCE_DATE.isoformat()
    return out[OBS_COLUMNS]


def observations() -> pd.DataFrame:
    UNMATCHED.clear()
    CHANGED.clear()
    parts = [parse_edition(edition_file(e.dam_id, e.period), e.period) for e in editions().itertuples()]
    if UNMATCHED:
        print("city names not matched to the register:", sorted(set(UNMATCHED))[:40], len(UNMATCHED))
    return to_obs(pd.concat(parts, ignore_index=True))
