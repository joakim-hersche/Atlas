"""Federal popular votes by municipality, 1960–today (BFS PxWeb px-x-1703030000_101).

BFS publishes every vote re-aggregated to the current municipality state (decision D14); the
remaining step to the reference state is merger-only.

Period convention: one period per Vorlage, 'YYYY-MM-DD#<vorlagenId>' (vote date and the BFS
vorlagenId, the key shared with voteinfo). Titles are in vorlagen.csv next to this file.

Pseudo-units (decision D17): Swiss abroad (90x0), postal/correspondence voting (90x1) and
'Anderes' (90x2) are kept as level 'pseudo' rows with unit_id = their BFS code (digits 2–3 are
the canton number), so canton and national totals can include them. They are not municipalities.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.common import REFERENCE_DATE
from pipeline.harmonize.helpers import emit
from pipeline.harmonize.pxweb import GEO, to_observations
from pipeline.harmonize.schema import OBS_COLUMNS
from pipeline.sources.bfs_votes_gemeinde.fetch import RESULTS, VORLAGE, results, voteinfo, vorlagen_labels

SOURCE = "bfs_votes_gemeinde"
HERE = Path(__file__).resolve().parent
METRICS = {f"vote_{v}": f"vote_{v}" for v in RESULTS.values()}


def _wide() -> pd.DataFrame:
    df = results()
    lab = vorlagen_labels().set_index("vorlagen_id")["date"]
    df["period"] = df[VORLAGE].map(lab) + "#" + df[VORLAGE]
    df["col"] = "vote_" + df["Ergebnis"].map(RESULTS)
    w = df.set_index([GEO, "period", "col"])["value"].unstack("col").reset_index()
    w.columns.name = None
    return w


def _pseudo(wide: pd.DataFrame) -> pd.DataFrame:
    p = wide[wide[GEO].str.fullmatch(r"9\d{3}")].copy()
    rows = emit(p, METRICS, "period", SOURCE, level="pseudo", unit_col=GEO, vintage=REFERENCE_DATE,
                precision="exact", provenance="native")
    rows = rows[rows["status"] == "ok"]  # pseudo-units that did not exist for a vote carry no row
    rows["note"] = "pseudo-unit (Swiss abroad / postal voting / other), not a municipality"
    return rows


GAP_NOTE = ("no municipal result published by BFS for this Vorlage (counted jointly with another "
            "municipality, or historical municipal results not available)")


def observations() -> pd.DataFrame:
    wide = _wide()
    obs = to_observations(wide[~wide[GEO].str.fullmatch(r"9\d{3}")], GEO, "period", METRICS, SOURCE)
    gap = (obs["level"] == "gemeinde") & (obs["status"] != "ok")
    obs.loc[gap, "status"], obs.loc[gap, "note"] = "not_published", GAP_NOTE
    # national rows ('CH' code) are emitted by to_observations; pseudo-units are kept here so that
    # only published ones (status ok) are listed
    return pd.concat([obs, _pseudo(wide)], ignore_index=True)[OBS_COLUMNS]


def write_vorlagen() -> pd.DataFrame:
    """Lookup of all Vorlagen: id, date, titles (voteinfo for 1981+, else the PxWeb label), accepted."""
    lab = vorlagen_labels()
    info = {}
    for d in sorted(lab["date"].unique()):
        if d < "1981-06-14":
            continue
        js = voteinfo(d)
        if not js:
            continue
        for v in js["schweiz"]["vorlagen"]:
            t = {x["langKey"]: x["text"] for x in v.get("vorlagenTitel", [])}
            info[str(v["vorlagenId"])] = {
                "title_de": t.get("de"), "title_fr": t.get("fr"), "title_it": t.get("it"),
                "title_rm": t.get("rm"), "title_en": t.get("en"),
                "accepted": v.get("vorlageAngenommen"), "title_source": "voteinfo",
                "voteinfo_yes_pct": (v.get("resultat") or {}).get("jaStimmenInProzent"),
                "voteinfo_yes": (v.get("resultat") or {}).get("jaStimmenAbsolut"),
                "voteinfo_valid": (v.get("resultat") or {}).get("gueltigeStimmen"),
            }
    rows = []
    for r in lab.itertuples():
        i = info.get(r.vorlagen_id)
        rows.append({"vorlagen_id": int(r.vorlagen_id), "date": r.date,
                     "title_de": (i or {}).get("title_de") or r.title_px,
                     "title_fr": (i or {}).get("title_fr"), "title_it": (i or {}).get("title_it"),
                     "title_rm": (i or {}).get("title_rm"), "title_en": (i or {}).get("title_en"),
                     "accepted": (i or {}).get("accepted"),
                     "title_source": (i or {}).get("title_source", "pxweb_label"),
                     "voteinfo_yes": (i or {}).get("voteinfo_yes"),
                     "voteinfo_valid": (i or {}).get("voteinfo_valid")})
    out = pd.DataFrame(rows).sort_values(["date", "vorlagen_id"])
    out["accepted"] = out["accepted"].map({True: "true", False: "false"})
    out.drop(columns=["voteinfo_yes", "voteinfo_valid"]).to_csv(HERE / "vorlagen.csv", index=False)
    return out


if __name__ == "__main__":
    print(write_vorlagen().head())
