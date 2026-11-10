"""Browser files for the profile page and search (brief 6.1: profile, search).

    python -m pipeline.build.profile        (make profile)

data/out/web/
  search.json      every unit of every level in units.json with its display name and alternative
                   names, plus postal codes -> current municipalities
  identity.json    per municipality: names in other languages, website, Wikipedia, coat of arms
                   (Commons file + licence), district and canton name
  history.json     per current municipality: register events since 1960 that affected it or its
                   predecessors (mergers, absorptions, splits, renames, district/canton changes)
  neighbours.json  per level: ids of the units sharing a boundary (G1 polygons of the reference state)

Inputs: data/out/web/units.json (pipeline.build.web), the backbone tables, the reference-state
geometry (data/interim/geo/units_<ref>.gpkg), the lookups swisstopo_plz (parsed here),
wikidata_identity/identity.csv and wikidata_cantons/cantons.csv. Every name and value comes from
one of these files; nothing is typed in. Lookup sources are shipped only if their licence is
cleared (pipeline/licence_review.yaml or the automatic text check in pipeline.build.web).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

import numpy as np
import pandas as pd
import yaml

from pipeline.common import REFERENCE_DATE, interim_path, out_path
from pipeline.harmonize.schema import SOURCES_DIR

LANGS = ["de", "fr", "it", "rm", "en"]
WIKIS = ["de", "fr", "it", "en"]
SINCE = pd.Timestamp("1960-01-01")
# typology levels: register levels-table column (labels <col>_de/_fr/_it/_en), as in backbone.levels
LEVEL_LABEL_COLS = {"grossregion": "REGCH", "sprachgebiet": "SPRGEB2020", "agglomeration": "AGGL2020",
                    "arbeitsmarktgebiet": "BAE2018", "stadt_land": "STALAN2020", "gemeindetyp": "GDETYP2020_9"}
MIN_SHARE = 0.5   # % of a postal locality's addresses (search.json)
FREE_LICENCE = re.compile(r"^(public domain|pd|cc0|cc[ -]by(-sa)?[ -]\d(\.\d)?)", re.I)


def _dump(obj, name: str) -> str:
    p = out_path("web", name)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    return str(p)


def _clean(v) -> str | None:
    if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NA:
        return None
    s = str(v).strip()
    return s or None


def cleared(source_id: str) -> bool:
    """Same rule as pipeline.build.web: explicit review first, then the licence text check."""
    from pipeline.build.web import license_cleared
    review = yaml.safe_load((SOURCES_DIR.parent / "licence_review.yaml").read_text(encoding="utf-8")) or {}
    r = review.get(source_id) or {}
    if r.get("status") in ("cleared", "blocked"):
        return r["status"] == "cleared"
    meta = yaml.safe_load((SOURCES_DIR / source_id / "meta.yaml").read_text(encoding="utf-8")) or {}
    return license_cleared(meta)[0]


# ---------------------------------------------------------------- inputs

def load_units() -> list[dict]:
    return json.loads(out_path("web", "units.json").read_text(encoding="utf-8"))


def load_identity() -> pd.DataFrame:
    from pipeline.sources.wikidata_identity.fetch import OUT
    d = pd.read_csv(OUT, dtype=str, keep_default_na=False).replace("", None)
    d["id"] = d["bfs_nr"].astype(str)
    return d.set_index("id")


def load_cantons() -> pd.DataFrame:
    """kanton code -> official register name (BFS) and Wikidata names; row 'CH' for Switzerland."""
    from pipeline.sources.wikidata_cantons.fetch import OUT, build
    wd = pd.read_csv(OUT, dtype=str, keep_default_na=False).replace("", None) if OUT.exists() else build()
    reg = pd.read_parquet(interim_path("backbone", "canton.parquet"))[["canton", "name"]]
    return wd.merge(reg.rename(columns={"canton": "kanton", "name": "official"}), on="kanton", how="left") \
             .set_index("kanton")


def load_plz() -> pd.DataFrame:
    from pipeline.sources.swisstopo_plz.parse import run
    run()  # cached download; rewrites data/interim/swisstopo_plz/plz.parquet and unmapped.csv
    return pd.read_parquet(interim_path("swisstopo_plz", "plz.parquet"))


def _current_district_versions() -> pd.DataFrame:
    dv = pd.read_parquet(interim_path("backbone", "district_version.parquet"))
    ref = pd.Timestamp(REFERENCE_DATE)
    return dv[(dv["valid_from"] <= ref) & (dv["valid_to"].isna() | (dv["valid_to"] >= ref))]


def _alts(display: str | None, values) -> list[str]:
    seen, out = {display}, []
    for v in values:
        v = _clean(v)
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


# ---------------------------------------------------------------- search.json

def build_search(units, identity, cantons, plz) -> dict:
    lv = pd.read_parquet(interim_path("backbone", f"levels_{REFERENCE_DATE.isoformat()}.parquet"))
    level_alts: dict[str, dict[str, list]] = {}
    for lvl, col in LEVEL_LABEL_COLS.items():
        labs = [c for c in (f"{col}_{l}" for l in LANGS) if c in lv.columns]
        g = lv[[col, *labs]].dropna(subset=[col]).astype({col: str}).drop_duplicates(col).set_index(col)
        level_alts[lvl] = {k: list(r) for k, r in g.iterrows()}
    dshort = _current_district_versions().assign(id=lambda d: d["district_nr"].astype(str)) \
                                         .drop_duplicates("id").set_index("id")["short_name"]
    rows = []
    for u in units:
        uid, lvl, name = u["id"], u["level"], u.get("name")
        kt = u.get("kanton")
        if lvl == "gemeinde":
            alts = _alts(name, identity.loc[uid, [f"label_{l}" for l in LANGS]] if uid in identity.index else [])
        elif lvl == "bezirk":
            alts = _alts(name, [dshort.get(uid)])
        elif lvl in ("kanton", "schweiz"):
            key = uid if lvl == "kanton" else "CH"
            c = cantons.loc[key] if key in cantons.index else None
            if lvl == "kanton" and c is not None and _clean(c.get("official")):
                name = c["official"]  # units.json carries the code as name; the register name is shown
            parts = [] if c is None else [*(c.get(f"short_{l}") for l in LANGS),
                                          *(_clean(c.get("official")) or "").split(" / ")]
            alts = _alts(name, parts)
        else:
            alts = _alts(name, level_alts.get(lvl, {}).get(uid, []))
        rows.append([uid, lvl, name, kt, alts])
    out = {"fields": ["id", "level", "display_name", "kanton", "alt_names"], "units": rows,
           "plz_fields": ["gemeinde_id", "locality", "address_share_pct"],
           "plz_note": "one row per locality (PLZ + Zusatzziffer) and municipality, largest share first; "
                       "address_share_pct = share (%) of that locality's addresses lying in the "
                       "municipality (Adressenanteil, as delivered by swisstopo)",
           "plz": {},
           "sources": ["wikidata_identity", "wikidata_cantons", "bfs register (levels, districts)"]}
    if plz is None:
        out["plz_note"] = "postal codes not shipped: swisstopo_plz licence not cleared"
    if plz is not None:
        # a municipality holding a tiny fraction of a locality's addresses (Riehen 0.049 % of 4058 Basel)
        # would be listed as '0.0 %': rows below MIN_SHARE are left out unless they are the only one
        n_all = plz.groupby("plz")["bfs_nr"].transform("size")
        small = (plz["address_share"] < MIN_SHARE) & (n_all > 1)
        out["plz_note"] += (f"; municipalities with less than {MIN_SHARE:g} % of a locality's addresses are left "
                            f"out ({int(small.sum())} rows)")
        plz = plz[~small]
        plz = plz.sort_values(["plz", "address_share"], ascending=[True, False], kind="stable")
        for code, g in plz.groupby("plz", sort=True):
            out["plz"][code] = [[str(int(b)), loc, (int(s) if float(s).is_integer() else round(float(s), 3))]
                                for b, loc, s in zip(g["bfs_nr"], g["locality"], g["address_share"])]
        out["sources"].append("swisstopo_plz")
    return out


# ---------------------------------------------------------------- identity.json

def build_identity(units, identity, cantons) -> dict:
    gem = [u for u in units if u["level"] == "gemeinde"]
    bez = {u["id"]: u["name"] for u in units if u["level"] == "bezirk"}
    res = {}
    n_coa = 0
    for u in gem:
        uid = u["id"]
        e: dict = {"bezirk": bez.get(u.get("bezirk")),
                   "kanton": _clean(cantons.loc[u["kanton"], "official"]) if u.get("kanton") in cantons.index else None}
        if uid in identity.index:
            r = identity.loc[uid]
            disp = u["name"]
            base = re.sub(r"\s*\([A-Z]{2}\)$", "", disp)
            names = {}
            for l in LANGS:
                v = _clean(r.get(f"label_{l}"))
                # labels equal to the display name, or to it without/with a canton suffix, add nothing
                if v and v != disp and re.sub(r"\s*\(?[A-Z]{2}\)?$", "", v) != base:
                    names[l] = v
            if names:
                e["names"] = names
            if _clean(r.get("qid")):
                e["qid"] = r["qid"]
            if _clean(r.get("website")):
                e["web"] = r["website"]
            wiki = {}
            for w in WIKIS:
                v = _clean(r.get(f"wikipedia_{w}"))
                prefix = f"https://{w}.wikipedia.org/wiki/"
                if v and v.startswith(prefix):
                    wiki[w] = v[len(prefix):]
            if wiki:
                e["wiki"] = wiki
            f, lic = _clean(r.get("coat_of_arms_file")), _clean(r.get("license_short_name"))
            if f and lic and FREE_LICENCE.match(lic) and str(r.get("commons_missing")) != "True":
                e["coa"] = [f, lic, str(r.get("attribution_required")).lower() == "true"]
                n_coa += 1
        res[uid] = e
    return {
        "note": "names: Wikidata labels that differ from the display name; wiki: article path, link = "
                "wiki_url with {lang} and {path}; coa: [Commons file, licence, attribution required] — "
                "link to commons_url, do not embed. BFS municipality portrait links are not included: "
                "the portrait pages moved to dashboard.bfs.admin.ch, which could not be checked "
                "(host blocked from the build session), so no URL pattern is verified.",
        "wiki_url": "https://{lang}.wikipedia.org/wiki/{path}",
        "commons_url": "https://commons.wikimedia.org/wiki/File:{file}",
        "attribution": "Data: Wikidata (CC0); coats of arms: Wikimedia Commons (licence per file)",
        "n_coat_of_arms": n_coa,
        "units": res,
    }


# ---------------------------------------------------------------- history.json

def _event_type(mut, pairs: pd.DataFrame, mv: pd.DataFrame) -> str | None:
    t = mut.type
    if t == "merger":
        return "absorption" if (pairs["to_step"] == "26").any() else "merger"
    if t == "reassignment":
        f, to = mv.loc[pairs["from_hist_id"]], mv.loc[pairs["to_hist_id"]]
        if f["canton"].tolist() != to["canton"].tolist():
            return "canton_change"
        if f["district_name"].tolist() != to["district_name"].tolist():
            return "district_change"
        if f["bfs_nr"].tolist() != to["bfs_nr"].tolist():
            return "renumbering"
        return None  # re-registration in a renumbered district: no visible change
    if t == "renumbering":
        return "renumbering" if (pairs["from_bfs_nr"] != pairs["to_bfs_nr"]).any() else None
    if t == "district_rename":
        return None  # the district was renamed; nothing changed for the municipality
    return {"split": "split", "rename": "rename", "territory_exchange": "territory_change",
            "reorganisation": "territory_change"}.get(t, t)


def _continues(p) -> bool:
    """True if the pair links a predecessor whose history belongs to the successor's lineage:
    the predecessor was abolished into it, or it is the same municipality's next version."""
    if p.from_step == "29":
        return True
    if p.from_step == p.to_step and p.from_step in ("22", "23", "24", "27"):
        return True
    return p.from_step == p.to_step == "26" and p.from_bfs_nr == p.to_bfs_nr


GROUPED = ("canton_change", "district_change", "renumbering")


def _merge_same_day(evs: list[dict]) -> list[dict]:
    """One event per date and change for district/canton moves and renumberings: when several
    predecessors moved together (e.g. a cantonal district reform), their versions are listed in one
    event instead of one event each."""
    out, idx = [], {}
    for e in evs:
        if e["t"] in GROUPED:
            key = (e["d"], e["t"], str(e.get("canton")), str(e.get("district")))
            if key in idx:
                o = idx[key]
                o["from"] += [x for x in e["from"] if x not in o["from"]]
                o["to"] += [x for x in e["to"] if x not in o["to"]]
                continue
            e = {**e, "from": list(e["from"]), "to": list(e["to"])}
            idx[key] = e
        out.append(e)
    return out


def build_history(units) -> dict:
    mv = pd.read_parquet(interim_path("backbone", "municipality_version.parquet")).set_index("hist_id")
    mu = pd.read_parquet(interim_path("backbone", "mutation.parquet")).set_index("mutation_id")
    mp = pd.read_parquet(interim_path("backbone", "mutation_pair.parquet"))
    mp = mp[mp["date"] >= SINCE].copy()
    for c in ("from_step", "to_step"):
        mp[c] = mp[c].astype(str)
    mem = pd.read_parquet(interim_path("backbone", f"membership_{REFERENCE_DATE.isoformat()}.parquet"),
                          columns=["hist_id", "bfs_nr"])
    by_to = defaultdict(list)
    by_hist = defaultdict(set)
    for p in mp.itertuples(index=False):
        by_to[p.to_hist_id].append(p)
        by_hist[p.from_hist_id].add(p.mutation_id)
        by_hist[p.to_hist_id].add(p.mutation_id)
    pairs_of = {k: g for k, g in mp.groupby("mutation_id")}

    def ver(h):
        r = mv.loc[h]
        return [str(int(r["bfs_nr"])), r["name"]]

    event_cache: dict[int, dict | None] = {}

    def event(mid):
        if mid not in event_cache:
            m, g = mu.loc[mid], pairs_of[mid]
            t = _event_type(m, g, mv)
            if t is None:
                event_cache[mid] = None
            else:
                fr = list(dict.fromkeys(g["from_hist_id"]))
                to = list(dict.fromkeys(g["to_hist_id"]))
                e = {"d": m.date.date().isoformat(), "t": t,
                     "from": [ver(h) for h in fr], "to": [ver(h) for h in to]}
                if t == "canton_change":
                    e["canton"] = [mv.loc[fr[0], "canton"], mv.loc[to[0], "canton"]]
                if t in ("canton_change", "district_change"):
                    e["district"] = [_clean(mv.loc[fr[0], "district_name"]), _clean(mv.loc[to[0], "district_name"])]
                event_cache[mid] = e
        return event_cache[mid]

    gem_ids = {u["id"] for u in units if u["level"] == "gemeinde"}
    res = {}
    for r in mem.itertuples(index=False):
        uid = str(int(r.bfs_nr))
        if uid not in gem_ids:
            continue
        lineage, stack = {int(r.hist_id)}, [int(r.hist_id)]
        while stack:
            h = stack.pop()
            for p in by_to.get(h, []):
                if p.from_hist_id not in lineage and _continues(p):
                    lineage.add(p.from_hist_id)
                    stack.append(p.from_hist_id)
        mids = sorted(set().union(*(by_hist.get(h, set()) for h in lineage)),
                      key=lambda m: (mu.loc[m, "date"], m))
        evs = _merge_same_day([e for e in (event(m) for m in mids) if e is not None])
        if evs:
            res[uid] = evs
    counts = defaultdict(int)
    for evs in res.values():
        for e in evs:
            counts[e["t"]] += 1
    return {
        "note": "Events since 1960 from the BFS historized municipality register that changed this "
                "municipality or one of its predecessors (municipalities abolished into it, earlier "
                "versions of itself). from/to: [bfs_nr, name] of the versions before and after the event. "
                "Moves of several predecessors on the same day are one event. District renames and "
                "re-registrations without a visible change (same canton, district name and BFS number) "
                "are left out.",
        "types": {"merger": "municipalities merged into a new municipality",
                  "absorption": "municipalities absorbed by an existing municipality",
                  "split": "a municipality was split", "rename": "renamed",
                  "territory_change": "territory exchanged between municipalities",
                  "district_change": "moved to another district",
                  "canton_change": "moved to another canton", "renumbering": "new BFS number"},
        "source": "BFS – Historisiertes Gemeindeverzeichnis der Schweiz",
        "since": SINCE.date().isoformat(), "reference_date": REFERENCE_DATE.isoformat(),
        "n_municipalities": len(res), "n_events": dict(sorted(counts.items())),
        "units": res,
    }


# ---------------------------------------------------------------- neighbours.json

def build_neighbours(min_shared_m: float = 10.0, tol_m: float = 1.0) -> dict:
    """Units sharing a boundary: at least min_shared_m metres of one unit's outline lie within tol_m
    of the other unit (LV95). The generalized G1 polygons do not meet exactly (adjacent outlines
    are offset by micrometres), so exact boundary intersection would miss most pairs. Units touching
    only at a point are not neighbours; units facing each other across a lake are neighbours only
    if their polygons meet (municipal boundaries run through most lakes)."""
    import geopandas as gpd
    import pyogrio
    gpkg = interim_path("geo", f"units_{REFERENCE_DATE.isoformat()}.gpkg")
    out = {}
    for lvl, _ in pyogrio.list_layers(gpkg):
        g = gpd.read_file(gpkg, layer=lvl)[["id", "geometry"]]
        g["id"] = g["id"].astype(str)
        g = g.dissolve("id").reset_index()  # one row per unit
        geom = g.set_index("id")["geometry"]
        buf = gpd.GeoDataFrame({"id": g["id"]}, geometry=g.buffer(tol_m), crs=g.crs)
        sj = gpd.sjoin(g, buf, predicate="intersects")
        sj = sj[sj["id_left"] != sj["id_right"]]
        bufs = buf.set_index("id")["geometry"]
        nb = defaultdict(set)
        for a, b in zip(sj["id_left"], sj["id_right"]):
            shared = geom[a].boundary.intersection(bufs[b]).length
            if shared >= min_shared_m:
                nb[a].add(b)
                nb[b].add(a)
        key = lambda x: (len(x), x)
        out[lvl] = {u: sorted(nb.get(u, ()), key=key) for u in sorted(geom.index, key=key)}
    return {"note": f"ids of units sharing a boundary of at least {min_shared_m:g} m (BFS generalized "
                    f"boundaries G1, state {REFERENCE_DATE.isoformat()})", "levels": out}


# ---------------------------------------------------------------- reach times

REACH_METHODS = {
    "pt_station": {"en": "Timetable journey from the municipality's main station to the hub station, arriving "
                         "07:30–08:30 on a weekday (median, as in a journey planner: no waiting).",
                   "de": "Fahrplan-Reisezeit vom Hauptbahnhof der Gemeinde zum Zentrumsbahnhof, Ankunft "
                         "07:30–08:30 an einem Werktag (Median, wie im Online-Fahrplan: ohne Wartezeit).",
                   "fr": "Temps de trajet selon l'horaire, de la gare principale de la commune à la gare du pôle, "
                         "arrivée 07:30–08:30 un jour ouvrable (médiane, comme dans l'horaire en ligne : sans attente)."},
    "pt": {"en": "Door to door towards the hub, arriving 07:30–08:30: walk from where people live to the best stop "
                 "within 1.5 km, then the timetable journey (population-weighted median).",
           "de": "Tür zu Tür Richtung Zentrum, Ankunft 07:30–08:30: Fussweg vom Wohnort zur besten Haltestelle "
                 "innerhalb 1,5 km, dann die Fahrplan-Reisezeit (bevölkerungsgewichteter Median).",
           "fr": "Porte à porte vers le pôle, arrivée 07:30–08:30 : marche du domicile au meilleur arrêt à moins "
                 "de 1,5 km, puis le trajet selon l'horaire (médiane pondérée par la population)."},
    "car": {"en": "Car travel time, average weekday, from the national passenger transport model (ARE NPVM 2023).",
            "de": "Autofahrzeit, durchschnittlicher Werktag, aus dem Nationalen Personenverkehrsmodell (ARE NPVM 2023).",
            "fr": "Temps de trajet en voiture, jour ouvrable moyen, selon le modèle national du trafic voyageurs (ARE MNTP 2023)."},
}


def build_reach_times() -> dict:
    """Travel times (minutes) between every hub and every municipality, all modes, in one small file
    (docs/web_data_contract.md §4).

    Values are the reach_<mode>_<hub> metrics in latest/gemeinde/mobility_accessibility.json (the same
    values the map shows): pt = reach_pt_* (door-to-door towards the hub), pt_station = reach_ptst_*
    (main station -> hub, D31), car = reach_car_*. Reasons for gaps come from the columns' notes; the
    main station per municipality from data/interim/reach/travel_times.parquet.
    """
    src = json.loads(out_path("web", "latest", "gemeinde", "mobility_accessibility.json").read_text(encoding="utf-8"))
    idx = json.loads(out_path("reach", "index.json").read_text(encoding="utf-8"))
    out = {"units": src["units"], "hubs": [[h["slug"], h["name"]] for h in idx["hubs"]],
           "service_date": idx.get("service_date"), "pt": {}, "pt_station": {}, "car": {}, "periods": {},
           "methods": REACH_METHODS, "reasons": {"pt": {}, "pt_station": {}, "car": {}}, "late_from": {},
           "late_text": {"en": "No arrival by 08:30; median over the hour from the earliest possible arrival ({t}).",
                         "de": "Keine Ankunft bis 08:30; Median über die Stunde ab der frühestmöglichen Ankunft ({t}).",
                         "fr": "Pas d'arrivée avant 08:30 ; médiane sur l'heure suivant la première arrivée possible ({t})."}}
    for h in idx["hubs"]:
        for mode, prefix in (("pt", "reach_pt_"), ("pt_station", "reach_ptst_"), ("car", "reach_car_")):
            m = src["metrics"].get(f"{prefix}{h['slug']}")
            if m is None:
                continue
            out[mode][h["slug"]] = m["v"]
            out["periods"][mode] = m.get("period")
            notes = m.get("notes") or []
            for i, k in (m.get("n") or {}).items():
                if m["v"][int(i)] is None:
                    out["reasons"][mode].setdefault(h["slug"], {})[i] = notes[k]
                elif (t := re.search(r"no arrival by 08:30.*\((\d\d:\d\d)\)", notes[k])):
                    # value from the first hour of possible arrivals: keep only its start time
                    out["late_from"].setdefault(mode, {}).setdefault(h["slug"], {})[i] = t.group(1)
    tt = pd.read_parquet(interim_path("reach", "travel_times.parquet"))
    ms = tt[(tt["method"] == "gtfs_rcsa_mainstation") & tt["main_station"].notna()].drop_duplicates("bfs_nr")
    ms = ms.set_index(ms["bfs_nr"].astype(int).astype(str))
    out["main_station"] = [[ms.loc[u, "main_station"], int(ms.loc[u, "main_didok"]), bool(ms.loc[u, "main_inside"])]
                           if u in ms.index else None for u in src["units"]]
    out["main_station_fields"] = ["name", "didok", "inside_municipality"]
    return out


# ---------------------------------------------------------------- run

def run() -> dict:
    units = load_units()
    identity = load_identity() if cleared("wikidata_identity") else pd.DataFrame()
    cantons = load_cantons() if cleared("wikidata_cantons") else pd.DataFrame(columns=["official"])
    plz = load_plz() if cleared("swisstopo_plz") else None
    written = {
        "search": _dump(build_search(units, identity, cantons, plz), "search.json"),
        "identity": _dump(build_identity(units, identity, cantons), "identity.json"),
        "history": _dump(build_history(units), "history.json"),
        "neighbours": _dump(build_neighbours(), "neighbours.json"),
        "reach_times": _dump(build_reach_times(), "reach_times.json"),
    }
    return written


if __name__ == "__main__":
    import os
    for k, v in run().items():
        print(f"{k:12s} {os.path.getsize(v) / 1024:8.0f} KB  {v}")
