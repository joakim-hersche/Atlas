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

import json
from pathlib import Path

import pandas as pd

from pipeline.backbone.levels import membership
from pipeline.common import RAW, REFERENCE_DATE, interim_path
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


DAM_FIELDS = {"anzahlStimmberechtigte": "vote_eligible", "eingelegteStimmzettel": "vote_ballots",
              "gueltigeStimmen": "vote_valid", "jaStimmenAbsolut": "vote_yes", "neinStimmenAbsolut": "vote_no"}


def dam_newer(after: str) -> list[dict]:
    """Votes newer than the PxWeb cube, from the BFS DAM JSON files (source bfs_votes, voteinfo schema,
    variant re-aggregated to the latest municipality state). The cube (checked 2026-11-10) ends at
    2026-06-14 while BFS has published the 2026-09-27 results (marked provisional) in the DAM.
    Returns the parsed JSON documents, newest last."""
    import glob
    from pipeline.sources.bfs_votes.fetch import fetch_vote, list_vote_assets
    docs = []
    try:
        assets = list_vote_assets()
        paths = [fetch_vote(int(r.current), r.vote_date, "current") for r in assets.itertuples() if r.vote_date > after]
    except Exception:  # offline rebuild: use the cached files
        paths = [p for p in sorted(glob.glob(str(RAW / "bfs_votes" / "*" / "vote_*_current.json")))
                 if Path(p).name[5:15] > after]
        paths = list({Path(p).name: p for p in paths}.values())
    for pth in paths:
        d = json.loads(Path(pth).read_text(encoding="utf-8"))
        voge = next(x["spatial_date"] for x in d["spatial_reference"] if x["spatial_unit"] == "voge")
        if voge != REFERENCE_DATE.isoformat():
            raise ValueError(f"DAM vote {d['abstimmtag']}: municipality state {voge} is not the reference state")
        docs.append(d)
    return docs


def _dam_wide(docs: list[dict]) -> pd.DataFrame:
    """Same layout as _wide(): municipality '0261', district '00' + 4 digits, canton code, 'CH', pseudo 9xxx."""
    ct = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    code = dict(zip(ct["canton_id"].astype(int), ct["canton"]))
    rows = []
    for d in docs:
        date = f"{d['abstimmtag'][:4]}-{d['abstimmtag'][4:6]}-{d['abstimmtag'][6:]}"
        for v in d["schweiz"]["vorlagen"]:
            per = f"{date}#{v['vorlagenId']}"
            rows.append({GEO: "CH", "period": per, **{c: v["resultat"].get(k) for k, c in DAM_FIELDS.items()}})
            for k in v["kantone"]:
                rows.append({GEO: code[int(k["geoLevelnummer"])], "period": per,
                             **{c: k["resultat"].get(f) for f, c in DAM_FIELDS.items()}})
                for b in k.get("bezirke") or []:
                    rows.append({GEO: f"00{int(b['geoLevelnummer']):04d}", "period": per,
                                 **{c: b["resultat"].get(f) for f, c in DAM_FIELDS.items()}})
                for g in k["gemeinden"]:
                    n = int(g["geoLevelnummer"])
                    rows.append({GEO: f"{n:04d}", "period": per,
                                 **{c: g["resultat"].get(f) for f, c in DAM_FIELDS.items()}})
    w = pd.DataFrame(rows)
    # municipalities without a result (counted with a neighbour) get an empty row, as in the cube
    allm = {f"{int(b):04d}" for b in membership()["bfs_nr"]}
    extra = [{GEO: m, "period": per} for per, g in w.groupby("period") for m in sorted(allm - set(g[GEO]))]
    w = pd.concat([w, pd.DataFrame(extra)], ignore_index=True) if extra else w
    for c in DAM_FIELDS.values():
        w[c] = pd.to_numeric(w[c], errors="coerce").astype(float)
    return w


def _pseudo(wide: pd.DataFrame) -> pd.DataFrame:
    p = wide[wide[GEO].str.fullmatch(r"9\d{3}")].copy()
    rows = emit(p, METRICS, "period", SOURCE, level="pseudo", unit_col=GEO, vintage=REFERENCE_DATE,
                precision="exact", provenance="native")
    rows = rows[rows["status"] == "ok"]  # pseudo-units that did not exist for a vote carry no row
    rows["note"] = "pseudo-unit (Swiss abroad / postal voting / other), not a municipality"
    return rows


GAP_NOTE = ("no municipal result published by BFS for this Vorlage (historical municipal results not "
            "available)")
POOLED = ("counted with another municipality in the BFS results (its votes are included there); "
          "no separate result")


def _pooled(obs: pd.DataFrame) -> pd.DataFrame:
    """Municipalities without a result whose votes are inside a neighbour's figures.

    BFS counts a few very small municipalities with a neighbour (e.g. Meienried, Hellsau, Deisswil
    b. M., Oberhünigen, Niedermuhlern BE), so their votes are inside the neighbour's figures (same
    cause as bfs_nrw._pooled). Test per district and Vorlage: the district result BFS publishes (on
    the same municipality state as the cube) equals the sum of the district's municipal results
    (valid ballots, within 0.5 %). Then the missing municipalities are pooled: status not_published
    with that note, and metrics.yaml `zero_when: [not_published]` keeps district and canton sums
    complete. Otherwise the results are really missing (e.g. Bern and its district on 1978-02-26):
    no_data, and the canton's published result is used (pipeline.build.metrics, published fallback).
    """
    mem = membership()[["bfs_nr", "bezirk"]].assign(unit_id=lambda d: d["bfs_nr"].astype(str))
    gem = obs["level"] == "gemeinde"
    v = obs[gem & (obs["metric_id"] == "vote_valid")][["unit_id", "period", "value", "status"]]
    v = v.merge(mem[["unit_id", "bezirk"]], on="unit_id", how="left")
    s_ok = v[v["status"] == "ok"].groupby(["bezirk", "period"])["value"].sum()
    pub = obs[(obs["level"] == "bezirk") & (obs["metric_id"] == "vote_valid") & (obs["status"] == "ok")]
    pub = pub.set_index(["unit_id", "period"])["value"]
    j = pd.concat([s_ok.rename("sum"), pub.rename("pub")], axis=1, join="inner")
    complete = set(j.index[(j["sum"] - j["pub"]).abs() <= 0.005 * j["pub"].abs() + 0.5])
    g = obs.loc[gem, ["unit_id", "period", "status"]].merge(mem[["unit_id", "bezirk"]], on="unit_id", how="left")
    g.index = obs.index[gem]
    gap = g["status"] != "ok"
    pooled = gap & pd.Series([k in complete for k in zip(g["bezirk"], g["period"])], index=g.index)
    obs.loc[pooled[pooled].index, ["status", "note"]] = ["not_published", POOLED]
    rest = gap & ~pooled
    obs.loc[rest[rest].index, ["status", "note"]] = ["no_data", GAP_NOTE]
    return obs


DAM_FIELDS = {"anzahlStimmberechtigte": "vote_eligible", "eingelegteStimmzettel": "vote_ballots",
              "gueltigeStimmen": "vote_valid", "jaStimmenAbsolut": "vote_yes", "neinStimmenAbsolut": "vote_no"}


def dam_newer(after: str) -> list[dict]:
    """Votes newer than the PxWeb cube, from the BFS DAM JSON files (source bfs_votes, voteinfo schema,
    variant re-aggregated to the latest municipality state). The cube (checked 2026-11-10) ends at
    2026-06-14 while BFS has published the 2026-09-27 results (marked provisional) in the DAM.
    Returns the parsed JSON documents, newest last."""
    import glob
    from pipeline.sources.bfs_votes.fetch import fetch_vote, list_vote_assets
    docs = []
    try:
        assets = list_vote_assets()
        paths = [fetch_vote(int(r.current), r.vote_date, "current") for r in assets.itertuples() if r.vote_date > after]
    except Exception:  # offline rebuild: use the cached files
        paths = [p for p in sorted(glob.glob(str(RAW / "bfs_votes" / "*" / "vote_*_current.json")))
                 if Path(p).name[5:15] > after]
        paths = list({Path(p).name: p for p in paths}.values())
    for pth in paths:
        d = json.loads(Path(pth).read_text(encoding="utf-8"))
        voge = next(x["spatial_date"] for x in d["spatial_reference"] if x["spatial_unit"] == "voge")
        if voge != REFERENCE_DATE.isoformat():
            raise ValueError(f"DAM vote {d['abstimmtag']}: municipality state {voge} is not the reference state")
        docs.append(d)
    return docs


def _dam_wide(docs: list[dict]) -> pd.DataFrame:
    """Same layout as _wide(): municipality '0261', district '00' + 4 digits, canton code, 'CH', pseudo 9xxx."""
    ct = pd.read_parquet(interim_path("backbone", "canton.parquet"))
    code = dict(zip(ct["canton_id"].astype(int), ct["canton"]))
    rows = []
    for d in docs:
        date = f"{d['abstimmtag'][:4]}-{d['abstimmtag'][4:6]}-{d['abstimmtag'][6:]}"
        for v in d["schweiz"]["vorlagen"]:
            per = f"{date}#{v['vorlagenId']}"
            rows.append({GEO: "CH", "period": per, **{c: v["resultat"].get(k) for k, c in DAM_FIELDS.items()}})
            for k in v["kantone"]:
                rows.append({GEO: code[int(k["geoLevelnummer"])], "period": per,
                             **{c: k["resultat"].get(f) for f, c in DAM_FIELDS.items()}})
                for b in k.get("bezirke") or []:
                    rows.append({GEO: f"00{int(b['geoLevelnummer']):04d}", "period": per,
                                 **{c: b["resultat"].get(f) for f, c in DAM_FIELDS.items()}})
                for g in k["gemeinden"]:
                    n = int(g["geoLevelnummer"])
                    rows.append({GEO: f"{n:04d}", "period": per,
                                 **{c: g["resultat"].get(f) for f, c in DAM_FIELDS.items()}})
    w = pd.DataFrame(rows)
    # municipalities without a result (counted with a neighbour) get an empty row, as in the cube
    allm = {f"{int(b):04d}" for b in membership()["bfs_nr"]}
    extra = [{GEO: m, "period": per} for per, g in w.groupby("period") for m in sorted(allm - set(g[GEO]))]
    w = pd.concat([w, pd.DataFrame(extra)], ignore_index=True) if extra else w
    for c in DAM_FIELDS.values():
        w[c] = pd.to_numeric(w[c], errors="coerce").astype(float)
    return w


def _pseudo(wide: pd.DataFrame) -> pd.DataFrame:
    p = wide[wide[GEO].str.fullmatch(r"9\d{3}")].copy()
    rows = emit(p, METRICS, "period", SOURCE, level="pseudo", unit_col=GEO, vintage=REFERENCE_DATE,
                precision="exact", provenance="native")
    rows = rows[rows["status"] == "ok"]  # pseudo-units that did not exist for a vote carry no row
    rows["note"] = "pseudo-unit (Swiss abroad / postal voting / other), not a municipality"
    return rows


GAP_NOTE = ("no municipal result published by BFS for this Vorlage (historical municipal results not "
            "available)")
POOLED = ("counted with another municipality in the BFS results (its votes are included there); "
          "no separate result")


def _pooled(obs: pd.DataFrame) -> pd.DataFrame:
    """Municipalities without a result although others in the same canton have one for that Vorlage.

    BFS counts a few very small municipalities with a neighbour (e.g. Meienried, Hellsau, Deisswil
    b. M., Oberhünigen, Niedermuhlern BE), so their votes are inside the neighbour's figures (same
    cause as bfs_nrw._pooled). They get status not_published with that note; metrics.yaml
    `zero_when: [not_published]` lets district and canton sums stay complete. Where a whole canton has
    no municipal results (early votes in AG, FR, TI, GE), the rows stay no_data and the canton's
    published result is used (pipeline.build.metrics, published fallback).
    """
    kt = membership()[["bfs_nr", "kanton"]].assign(unit_id=lambda d: d["bfs_nr"].astype(str))
    gem = obs["level"] == "gemeinde"
    g = obs.loc[gem, ["unit_id", "metric_id", "period", "status"]].merge(kt[["unit_id", "kanton"]], on="unit_id", how="left")
    has = g[g["status"] == "ok"].groupby(["kanton", "metric_id", "period"]).size().rename("n_ok")
    g = g.join(has, on=["kanton", "metric_id", "period"])
    g.index = obs.index[gem]
    gap = g["status"] != "ok"
    pooled = gap & (g["n_ok"].fillna(0) > 0)
    obs.loc[pooled[pooled].index, ["status", "note"]] = ["not_published", POOLED]
    rest = gap & ~pooled
    obs.loc[rest[rest].index, ["status", "note"]] = ["no_data", GAP_NOTE]
    return obs


PROVISIONAL = "provisional result (BFS DAM / voteinfo, 'provisorisch'); the PxWeb cube does not include this vote yet"


def observations() -> pd.DataFrame:
    wide = _wide()
    docs = dam_newer(max(p[:10] for p in wide["period"]))
    prov = {f"{d['abstimmtag'][:4]}-{d['abstimmtag'][4:6]}-{d['abstimmtag'][6:]}#{v['vorlagenId']}"
            for d in docs for v in d["schweiz"]["vorlagen"] if v.get("provisorisch")}
    if docs:
        wide = pd.concat([wide, _dam_wide(docs)], ignore_index=True)
    obs = to_observations(wide[~wide[GEO].str.fullmatch(r"9\d{3}")], GEO, "period", METRICS, SOURCE)
    obs = _pooled(obs)
    # national rows ('CH' code) are emitted by to_observations; pseudo-units are kept here so that
    # only published ones (status ok) are listed
    obs = pd.concat([obs, _pseudo(wide)], ignore_index=True)
    pv = obs["period"].isin(prov) & (obs["status"] == "ok")
    obs.loc[pv, "note"] = PROVISIONAL
    return obs[OBS_COLUMNS]


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
    known = {r["vorlagen_id"] for r in rows}
    for d in dam_newer(max(lab["date"])):
        date = f"{d['abstimmtag'][:4]}-{d['abstimmtag'][4:6]}-{d['abstimmtag'][6:]}"
        for v in d["schweiz"]["vorlagen"]:
            if int(v["vorlagenId"]) in known:
                continue
            t = {x["langKey"]: x["text"] for x in v.get("vorlagenTitel", [])}
            rows.append({"vorlagen_id": int(v["vorlagenId"]), "date": date, "title_de": t.get("de"),
                         "title_fr": t.get("fr"), "title_it": t.get("it"), "title_rm": t.get("rm"),
                         "title_en": t.get("en"), "accepted": v.get("vorlageAngenommen"),
                         "title_source": "bfs_dam", "provisional": bool(v.get("provisorisch"))})
    out = pd.DataFrame(rows).sort_values(["date", "vorlagen_id"])
    if "provisional" not in out:
        out["provisional"] = False
    out["provisional"] = out["provisional"].fillna(False).map({True: "true", False: "false"})
    out["accepted"] = out["accepted"].map({True: "true", False: "false"})
    out.drop(columns=["voteinfo_yes", "voteinfo_valid"]).to_csv(HERE / "vorlagen.csv", index=False)
    return out


if __name__ == "__main__":
    print(write_vorlagen().head())
