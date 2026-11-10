"""Structural Survey (SE): main languages by district, 3-year pooled, with 95 % confidence intervals
(BFS table su-d-40.02.01.08.09, editions 2011-2013 … latest).

Districts are keyed by canton abbreviation + district NAME; they are matched to the district
number valid at the end of the pooling period (data/interim/backbone/district_version.parquet).
Rows are level 'bezirk' (unit_id = district number, vintage = 31 Dec of the last pooled year) and
'schweiz', precision 'survey', provenance 'native'. Population: permanent residents in private
households. Respondents could name up to three main languages, so language counts add up to more
than the total.

Per language x the connector delivers
  lang_se_<x>         extrapolated persons (survey estimate)
  lang_se_<x>_ci      published 95 % CI half-width of that estimate, relative (± % of the count)
  lang_se_<x>_share_ci  CI half-width of the share in percentage points, approximated as
                       share × relative CI / 100 (BFS publishes CIs for counts only; treating the
                       district total as fixed makes this a slightly conservative approximation)
and the share as a derived ratio lang_se_<x> / lang_se_pop.
BFS flags: 'X' (≤ 4 observations) -> status suppressed; '( )' (≤ 49 observations, read from the
cell number format) -> value kept, note 'low reliability'.
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from pipeline.common import interim_path
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_se_language_bezirk.fetch import edition_file, editions

SOURCE = "bfs_se_language_bezirk"
LANG = {"Total Bevölkerung": "pop", "Deutsch": "de", "Französisch": "fr", "Italienisch": "it",
        "Rätoromanisch": "rm", "Englisch": "en", "Andere": "other", "Hauptsprache unbekannt": "unknown"}
LOW_NOTE = "low reliability: extrapolation from 49 or fewer observations (BFS '( )')"
SUPPRESSED_NOTE = "suppressed: 4 or fewer observations (BFS 'X')"


def _grid(path):
    """(values, bracketed) as 2-D lists; bracketed = cell number format shows '( )'."""
    if open(path, "rb").read(4) == b"\xd0\xcf\x11\xe0":  # legacy .xls (first editions; cached as .xlsx)
        import xlrd
        wb = xlrd.open_workbook(path, formatting_info=True)
        sh = wb.sheet_by_index(0)
        vals, br = [], []
        for r in range(sh.nrows):
            vrow, brow = [], []
            for c in range(sh.ncols):
                cell = sh.cell(r, c)
                v = cell.value if cell.ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK) else None
                fmt = wb.format_map[wb.xf_list[cell.xf_index].format_key].format_str
                vrow.append(v)
                brow.append("(" in fmt)
            vals.append(vrow)
            br.append(brow)
        return vals, br
    import openpyxl
    ws = openpyxl.load_workbook(path).worksheets[0]
    vals = [[c.value for c in row] for row in ws.iter_rows()]
    br = [["(" in (c.number_format or "") for c in row] for row in ws.iter_rows()]
    return vals, br


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"\s*/\s*", "/", s)
    return re.sub(r"\s+", " ", s).strip()


def _districts(end: pd.Timestamp) -> dict[tuple[str, str], int]:
    dv = pd.read_parquet(interim_path("backbone", "district_version.parquet"))
    ct = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    dv = dv.merge(ct[["canton_id", "canton"]], on="canton_id")
    cur = dv[(dv["valid_from"] <= end) & (dv["valid_to"].isna() | (dv["valid_to"] >= end))]
    return {(r.canton, _norm(r.name)): int(r.district_nr) for r in cur.itertuples()}


def parse_edition(path, period: str) -> tuple[pd.DataFrame, list]:
    vals, br = _grid(path)
    hdr_row = next(i for i, r in enumerate(vals) if "Total Bevölkerung" in [str(v).strip() for v in r])
    hdr = vals[hdr_row]
    c0 = [str(v).strip() for v in hdr].index("Total Bevölkerung")
    cols = {}
    for j, v in enumerate(hdr):
        if v is None:
            continue
        key = next((k for k in LANG if str(v).strip().startswith(k)), None)
        if key:
            cols[LANG[key]] = j
    end = pd.Timestamp(f"{period[-4:]}-12-31")
    lookup = _districts(end)
    # CI unit: the first editions give the CI as a fraction, later ones in percent
    first = next(r for r in vals[hdr_row + 2:] if isinstance(r[c0], (int, float)))
    ci_factor = 100.0 if first[c0 + 1] < 0.05 else 1.0
    rows, unmatched = [], []
    for i, r in enumerate(vals[hdr_row + 2:], start=hdr_row + 2):
        kt, name = r[c0 - 2], r[c0 - 1]
        if not isinstance(r[c0], (int, float)):
            continue
        if str(kt).strip() in ("Total", "Schweiz"):
            level, unit = "schweiz", "CH"
        else:
            nr = lookup.get((str(kt).strip(), _norm(name)))
            if nr is None:
                unmatched.append((period, kt, name))
                continue
            level, unit = "bezirk", str(nr)
        for lang, j in cols.items():
            v, ci = r[j], r[j + 1]
            low = br[i][j]
            if isinstance(v, (int, float)):
                rec = dict(value=float(v), status="ok", note=LOW_NOTE if low else None)
                cival = float(ci) * ci_factor if isinstance(ci, (int, float)) else np.nan
            else:
                rec = dict(value=np.nan, status="suppressed" if str(v).strip() == "X" else "no_data",
                           note=SUPPRESSED_NOTE if str(v).strip() == "X" else f"BFS '{v}'")
                cival = np.nan
            rows.append(dict(level=level, unit_id=unit, lang=lang, ci=cival, **rec))
    df = pd.DataFrame(rows)
    df["period"], df["vintage"] = period, end.date().isoformat()
    return df, unmatched


def _to_obs(df: pd.DataFrame) -> pd.DataFrame:
    base = df.assign(metric_id="lang_se_" + df["lang"])
    ci = df.assign(metric_id="lang_se_" + df["lang"] + "_ci", value=df["ci"])
    ci["status"] = np.where(ci["value"].notna(), "ok", ci["status"].where(ci["status"] != "ok", "no_data"))
    pop = df[df["lang"] == "pop"].set_index(["level", "unit_id", "period"])["value"]
    sh = df[df["lang"] != "pop"].copy()
    share = sh["value"] / pop.reindex(pd.MultiIndex.from_frame(sh[["level", "unit_id", "period"]])).to_numpy() * 100
    sh = sh.assign(metric_id="lang_se_" + sh["lang"] + "_share_ci", value=share * sh["ci"] / 100)
    sh["status"] = np.where(sh["value"].notna(), "ok", sh["status"].where(sh["status"] != "ok", "no_data"))
    out = pd.concat([base, ci, sh], ignore_index=True)
    out["precision"], out["provenance"], out["source_id"] = "survey", "native", SOURCE
    return out[OBS_COLUMNS]


UNMATCHED: list = []


def observations() -> pd.DataFrame:
    parts = []
    UNMATCHED.clear()
    for e in editions().itertuples():
        df, un = parse_edition(edition_file(e.dam_id, e.period), e.period)
        UNMATCHED.extend(un)
        parts.append(df)
    if UNMATCHED:
        print("unmatched district names:", UNMATCHED)
    return _to_obs(pd.concat(parts, ignore_index=True))
