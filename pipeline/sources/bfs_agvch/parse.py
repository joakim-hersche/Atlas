"""Parse the BFS register (eCH-0071 v1.2.0) and mutation API output into tidy tables.

Outputs (data/interim/backbone/):
  municipality_version.parquet  one row per municipality version (histId)
  district_version.parquet      one row per district version
  canton.parquet                cantons
  mutation_pair.parquet         one row per (mutation, initial version -> terminal version)
  mutation.parquet              one row per mutation, with type and from/to lists
  levels_<date>.parquet         spatial levels valid on the reference date
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path, parse_ch_date
from pipeline.sources.bfs_agvch.fetch import fetch_all

# eCH-0071 v1.2.0 column layouts (tab-separated, no header, Latin-1)
GDE_COLS = ["hist_id", "district_hist_id", "canton", "bfs_nr", "name", "short_name", "entry_mode",
            "status", "admission_number", "admission_mode", "admission_date", "abolition_number",
            "abolition_mode", "abolition_date", "date_of_change"]
BEZ_COLS = ["hist_id", "canton_id", "district_nr", "name", "short_name", "entry_mode",
            "admission_number", "admission_mode", "admission_date", "abolition_number",
            "abolition_mode", "abolition_date", "date_of_change"]
KT_COLS = ["canton_id", "canton", "name", "admission_date"]

# Step / mode codes (eCH-0071). Labels verified against the mutation list contents.
STEP = {
    "20": "first registration",
    "21": "creation",
    "22": "district renamed",
    "23": "municipality renamed",
    "24": "district/canton reassignment",
    "26": "territory change",
    "27": "renumbering",
    "29": "abolition",
}
# entry_mode: 11 = political municipality, 12 = territory not assigned to a municipality,
# 13 = cantonal lake area (as seen in the 2026 register: 2110 / 3 / 41 active records)
ENTRY_MODE = {"11": "municipality", "12": "unassigned territory", "13": "cantonal lake area"}


def _read_register_member(zf: zipfile.ZipFile, suffix: str, cols: list[str]) -> pd.DataFrame:
    names = [n for n in zf.namelist() if n.startswith("1.2.0/") and n.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"expected one 1.2.0/*{suffix} in register zip, found {names}")
    raw = zf.read(names[0]).decode("latin-1")
    df = pd.read_csv(io.StringIO(raw), sep="\t", header=None, names=cols, dtype=str,
                     keep_default_na=False)
    return df


def _dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_datetime(df[c].map(parse_ch_date))
    return df


def parse_register(zip_path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(zip_path) as zf:
        gde = _read_register_member(zf, "_GDE.txt", GDE_COLS)
        bez = _read_register_member(zf, "_BEZ.txt", BEZ_COLS)
        kt = _read_register_member(zf, "_KT.txt", KT_COLS)
    for df in (gde, bez):
        for c in ("hist_id", "admission_number", "abolition_number"):
            df[c] = pd.to_numeric(df[c].replace("", None), errors="raise").astype("Int64")
    gde["district_hist_id"] = gde["district_hist_id"].astype("Int64")
    gde["bfs_nr"] = gde["bfs_nr"].astype("Int64")
    bez["district_nr"] = bez["district_nr"].astype("Int64")
    bez["canton_id"] = bez["canton_id"].astype("Int64")
    kt["canton_id"] = kt["canton_id"].astype("Int64")
    gde = _dates(gde, ["admission_date", "abolition_date", "date_of_change"])
    bez = _dates(bez, ["admission_date", "abolition_date", "date_of_change"])
    kt = _dates(kt, ["admission_date"])
    gde["entry_type"] = gde["entry_mode"].map(ENTRY_MODE).fillna("other")
    gde["admission_type"] = gde["admission_mode"].map(STEP)
    gde["abolition_type"] = gde["abolition_mode"].map(STEP)
    # valid_from / valid_to (inclusive). An abolished version is valid through its abolition date;
    # its successors start the next day (e.g. abolished 31.12.2000, successor admitted 01.01.2001).
    gde = gde.rename(columns={"admission_date": "valid_from", "abolition_date": "valid_to"})
    bez = bez.rename(columns={"admission_date": "valid_from", "abolition_date": "valid_to"})
    gde = gde.merge(bez[["hist_id", "district_nr", "name"]].rename(
        columns={"hist_id": "district_hist_id", "name": "district_name"}), on="district_hist_id", how="left")
    cols = ["hist_id", "bfs_nr", "name", "short_name", "canton", "district_hist_id", "district_nr",
            "district_name", "entry_mode", "entry_type", "valid_from", "valid_to", "admission_number",
            "admission_mode", "admission_type", "abolition_number", "abolition_mode", "abolition_type",
            "date_of_change"]
    return gde[cols], bez, kt


def parse_mutations(csv_path) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    pair = pd.DataFrame({
        "mutation_id": m["MutationNumber"].astype(int),
        "date": pd.to_datetime(m["MutationDate"].map(parse_ch_date)),
        "from_hist_id": m["InitialHistoricalCode"].astype(int),
        "from_bfs_nr": m["InitialCode"].astype(int),
        "from_name": m["InitialName"],
        "from_step": m["InitialStep"],
        "to_hist_id": m["TerminalHistoricalCode"].astype(int),
        "to_bfs_nr": m["TerminalCode"].astype(int),
        "to_name": m["TerminalName"],
        "to_step": m["TerminalStep"],
    })

    def classify(g: pd.DataFrame) -> str:
        steps = set(g["from_step"]) | set(g["to_step"])
        n_from, n_to = g["from_hist_id"].nunique(), g["to_hist_id"].nunique()
        if "29" in steps and n_to == 1:
            return "merger"
        if "21" in steps and n_from == 1 and n_to > 1:
            return "split"
        if "29" in steps or "21" in steps:
            return "reorganisation"
        if steps == {"26"}:
            return "territory_exchange"
        if steps == {"23"}:
            return "rename"
        if steps == {"22"}:
            return "district_rename"
        if steps == {"24"}:
            return "reassignment"
        if steps == {"27"}:
            return "renumbering"
        return "other:" + "+".join(sorted(steps))

    rows = []
    for mid, g in pair.groupby("mutation_id", sort=True):
        rows.append({
            "mutation_id": mid,
            "date": g["date"].iloc[0],
            "type": classify(g),
            "from_hist_ids": sorted(set(g["from_hist_id"])),
            "to_hist_ids": sorted(set(g["to_hist_id"])),
            "from_bfs": sorted(set(g["from_bfs_nr"])),
            "to_bfs": sorted(set(g["to_bfs_nr"])),
            "n_pairs": len(g),
        })
    return pair, pd.DataFrame(rows)


def parse_levels(csv_path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    for c in ("HistoricalCode", "BfsCode", "CantonId", "DistrictId"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    return df


def run() -> dict[str, str]:
    files = fetch_all()
    gde, bez, kt = parse_register(files["register_zip"])
    pair, mutation = parse_mutations(files["mutations"])
    levels = parse_levels(files["levels"])
    out = {}
    for name, df in [("municipality_version", gde), ("district_version", bez), ("canton", kt),
                     ("mutation_pair", pair), ("mutation", mutation),
                     (f"levels_{REFERENCE_DATE.isoformat()}", levels)]:
        p = interim_path("backbone", f"{name}.parquet")
        df.to_parquet(p, index=False)
        out[name] = str(p)
    return out


if __name__ == "__main__":
    for k, v in run().items():
        print(k, v)
