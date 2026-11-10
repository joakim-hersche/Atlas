"""Parse the locality directory to a tidy table on the reference municipality state.

    python -m pipeline.sources.swisstopo_plz.parse

Output data/interim/swisstopo_plz/plz.parquet, one row per (locality = PLZ4 + Zusatzziffer,
current municipality):
  plz, zusatz, zip_id, locality, language, valid_since   as delivered
  src_bfs_nr, src_name, src_kanton                        municipality as delivered
  address_share                                           share (%) of the locality's addresses in
                                                          that municipality (Adressenanteil)
  bfs_nr, name, kanton                                    municipality on the reference state
  weight, weight_source                                   crosswalk weight (1 / single_successor
                                                          unless the municipality changed since)
  e, n                                                    locality point (LV95)
Rows whose municipality cannot be mapped (Liechtenstein localities, municipality-free territories
such as Staatswald Galm or the Comunanza Cadenazzo/Monteceneri) go to unmapped.csv next to it.

The directory carries BFS numbers of its own date; that state is detected from the set of numbers
(helpers.infer_vintage) and reprojected with the backbone crosswalk. Where a crosswalk weight is
below 1 (a split since), the address share is multiplied by it and weight_source says so.
"""
from __future__ import annotations

import zipfile

import pandas as pd

from pipeline.backbone.crosswalk import load_backbone, versions_at
from pipeline.backbone.vintage import _municipal_targets, crosswalk
from pipeline.common import REFERENCE_DATE, interim_path
from pipeline.harmonize.helpers import infer_vintage
from pipeline.sources.swisstopo_plz.fetch import MEMBER, SOURCE, directory_zip

COLS = {"Ortschaftsname": "locality", "PLZ4": "plz", "Zusatzziffer": "zusatz", "ZIP_ID": "zip_id",
        "Gemeindename": "src_name", "BFS-Nr": "src_bfs_nr", "Kantonskürzel": "src_kanton",
        "Adressenanteil": "address_share", "E": "e", "N": "n", "Sprache": "language",
        "Validity": "valid_since"}


def read_raw() -> pd.DataFrame:
    with zipfile.ZipFile(directory_zip()) as z, z.open(MEMBER) as fh:
        df = pd.read_csv(fh, sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False)
    missing = set(COLS) - set(df.columns)
    if missing:
        raise ValueError(f"unexpected directory layout, missing columns: {sorted(missing)}")
    df = df.rename(columns=COLS)[list(COLS.values())]
    share = df["address_share"].str.replace("%", "", regex=False).str.strip()
    if not share.str.fullmatch(r"\d+(\.\d+)?").all():
        raise ValueError("Adressenanteil not in the expected 'NN.NNN %' form")
    df["address_share"] = share.astype(float)
    df["src_bfs_nr"] = pd.to_numeric(df["src_bfs_nr"]).astype("Int64")
    df["e"] = pd.to_numeric(df["e"])
    df["n"] = pd.to_numeric(df["n"])
    df["src_kanton"] = df["src_kanton"].replace("", None)
    return df


def run() -> dict:
    raw = read_raw()
    vintage, jac = infer_vintage(raw["src_bfs_nr"].dropna().unique())
    mv, _ = load_backbone()
    ver = versions_at(mv, vintage, municipalities_only=False).drop_duplicates("bfs_nr")
    raw["hist_id"] = raw["src_bfs_nr"].map(ver.set_index("bfs_nr")["hist_id"])
    cw = crosswalk(REFERENCE_DATE)
    cw = cw[cw["to_hist_id"].isin(_municipal_targets(REFERENCE_DATE)) & (cw["weight"] > 0)]
    m = raw.merge(cw[["from_hist_id", "to_bfs_nr", "to_name", "to_canton", "weight", "weight_source"]],
                  left_on="hist_id", right_on="from_hist_id", how="left")
    unmapped = m[m["to_bfs_nr"].isna()][list(COLS.values())].copy()
    unmapped["reason"] = [
        "outside Switzerland (no canton; Liechtenstein)" if pd.isna(k) else "not a municipality on the "
        f"directory state {vintage} (unassigned territory or unknown number)" for k in unmapped["src_kanton"]]
    out = m[m["to_bfs_nr"].notna()].rename(columns={"to_bfs_nr": "bfs_nr", "to_name": "name",
                                                    "to_canton": "kanton"})
    out["address_share"] = (out["address_share"] * out["weight"]).round(3)
    out = out[["plz", "zusatz", "zip_id", "locality", "language", "valid_since", "src_bfs_nr", "src_name",
               "src_kanton", "address_share", "bfs_nr", "name", "kanton", "weight", "weight_source", "e", "n"]]
    out = out.sort_values(["plz", "zusatz", "address_share"], ascending=[True, True, False])
    p = interim_path(SOURCE, "plz.parquet")
    out.to_parquet(p, index=False)
    unmapped.to_csv(interim_path(SOURCE, "unmapped.csv"), index=False)
    return {"rows": len(raw), "mapped_rows": len(out), "unmapped_rows": len(unmapped),
            "plz4": out["plz"].nunique(), "localities": out["zip_id"].nunique(),
            "municipalities": out["bfs_nr"].nunique(), "directory_state": str(vintage),
            "state_jaccard": round(jac, 4), "weighted_rows": int((out["weight"] < 1).sum()), "path": str(p)}


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:16s} {v}")
