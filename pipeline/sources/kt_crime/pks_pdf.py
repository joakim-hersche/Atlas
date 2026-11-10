"""Parser for the cantonal PKS annual reports produced on the BFS template ('BFS Polizeiliche
Kriminalstatistik (PKS) Jahresbericht <Kanton>'). Table 'Strafgesetzbuch: Straftaten nach Gemeinde'
(section 4.1.3 Zeitreihen): StGB offences per municipality for the last 7 years, with rows
'Total Kanton', 'Unbekannt <KT>' (offences without a known municipality) and, in larger cantons,
'Übrige Gemeinden' (the template lists at most 40 municipalities, ordered by the latest year).
Text is extracted with `pdftotext -layout` (poppler), as in pipeline/sources/bag_premiums."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

TITLE = "Strafgesetzbuch: Straftaten nach Gemeinde"
NUM = re.compile(r"^\d{1,3}(?: \d{3})*$")


def _text(pdf: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True,
                         text=True).stdout
    return out.splitlines()


def stgb_by_gemeinde(pdf: Path) -> pd.DataFrame:
    """Long table: label, period, offences. Raises if the table is not found or a row does not
    parse into one value per year."""
    lines = _text(pdf)
    for i, ln in enumerate(lines):
        if ln.strip() != TITLE:
            continue
        # the table proper: a header line with the years follows within a few lines
        for j in range(i + 1, min(i + 8, len(lines))):
            years = re.findall(r"\b(20\d\d)\b", lines[j])
            if len(years) >= 5 and re.fullmatch(r"[\s\d]+", lines[j]):
                break
        else:
            continue
        rows = []
        for ln2 in lines[j + 1:]:
            s = ln2.strip()
            if not s:
                continue
            if s.startswith("Quelle"):
                break
            parts = re.split(r"\s{2,}", s)
            label, vals = parts[0], parts[1:]
            if len(vals) != len(years) or not all(NUM.match(v) or v in ("–", "-") for v in vals):
                raise ValueError(f"{pdf.name}: cannot parse row {s!r}")
            for y, v in zip(years, vals):
                rows.append((label, y, float(v.replace(" ", "")) if NUM.match(v) else float("nan")))
        if not rows:
            raise ValueError(f"{pdf.name}: empty table")
        return pd.DataFrame(rows, columns=["label", "period", "n"])
    raise ValueError(f"{pdf.name}: table '{TITLE}' not found")
