"""Reach hubs (decisions D9, D39) and their main station in the GTFS feed.

Each hub is its main rail station, identified by didok number (= GTFS stops.didok of the parent
station; GTFS station id 'Parentch:1:sloid:<didok - 8500000>'). Nearby tram/bus stops are reached
from it over the 400 m footpaths, so they are not listed as extra sources.

HUBS        every starting point of the reach picker: the 20 approved stations (D9) plus Baden (D39).
NEAREST_HUBS the hub set of the "travel time to the nearest hub" metrics (D39): the main station of the
            core city of every BFS agglomeration (Agglomerationen 2020, backbone column AGGL2020) with at
            least 100,000 residents in the latest STATPOP year. Derived from the data by
            `nearest_hubs()` and checked against the 15 hubs the owner approved; each qualifying
            agglomeration is mapped to its hub station explicitly in AGGLO_HUB (the agglomeration code is
            the BFS number of its core municipality).
"""
from __future__ import annotations

import pandas as pd

HUBS = [  # slug, display name, didok
    ("zuerich", "Zürich HB", 8503000),
    ("bern", "Bern", 8507000),
    ("basel", "Basel SBB", 8500010),
    ("geneve", "Genève", 8501008),
    ("lausanne", "Lausanne", 8501120),
    ("luzern", "Luzern", 8505000),
    ("stgallen", "St. Gallen", 8506302),
    ("winterthur", "Winterthur", 8506000),
    ("lugano", "Lugano", 8505300),
    ("bellinzona", "Bellinzona", 8505213),
    ("chur", "Chur", 8509000),
    ("biel", "Biel/Bienne", 8504300),
    ("fribourg", "Fribourg/Freiburg", 8504100),
    ("sion", "Sion", 8501506),
    ("zug", "Zug", 8502204),
    ("aarau", "Aarau", 8502113),
    ("olten", "Olten", 8500218),
    ("schaffhausen", "Schaffhausen", 8503424),
    ("neuchatel", "Neuchâtel", 8504221),
    ("thun", "Thun", 8507100),
    ("baden", "Baden", 8503504),    # D39: core city of the agglomeration Baden – Brugg (Baden SBB)
]
SLUGS = [h[0] for h in HUBS]
NAMES = {h[0]: h[1] for h in HUBS}

MIN_AGGLO_POP = 100_000
# agglomeration (AGGL2020 code = BFS number of the core municipality) -> hub station; only the
# agglomerations that reach MIN_AGGLO_POP need an entry (the check below fails on a missing one)
AGGLO_HUB = {
    261: "zuerich",       # Zürich
    6621: "geneve",       # Genève (CH)
    2701: "basel",        # Basel (CH)
    5586: "lausanne",     # Lausanne
    351: "bern",          # Bern
    1061: "luzern",       # Luzern
    3203: "stgallen",     # St. Gallen
    5192: "lugano",       # Lugano (CH)
    230: "winterthur",    # Winterthur
    1711: "zug",          # Zug
    4021: "baden",        # Baden – Brugg
    4001: "aarau",        # Aarau
    6458: "neuchatel",    # Neuchâtel
    371: "biel",          # Biel/Bienne
    2581: "olten",        # Olten – Zofingen
}
# the 15 hubs approved by the owner (D39), in descending agglomeration population (STATPOP 2025)
NEAREST_HUBS_EXPECTED = ["zuerich", "geneve", "basel", "lausanne", "bern", "luzern", "stgallen", "lugano",
                         "winterthur", "zug", "baden", "aarau", "neuchatel", "biel", "olten"]
NEAREST_RULE = {
    "en": "Hubs = main station of the core city of every agglomeration (BFS 2020 definition) with at least "
          "100,000 residents (STATPOP {year}): {hubs}.",
    "de": "Zentren = Hauptbahnhof der Kernstadt jeder Agglomeration (BFS-Definition 2020) mit mindestens "
          "100 000 Einwohnerinnen und Einwohnern (STATPOP {year}): {hubs}.",
    "fr": "Pôles = gare principale de la ville-centre de chaque agglomération (définition OFS 2020) d'au moins "
          "100 000 habitants (STATPOP {year}) : {hubs}.",
}


def agglomeration_population() -> pd.DataFrame:
    """Residents per agglomeration (AGGL2020, reference state): latest STATPOP year of pop_total at
    municipality level (data/interim/observation/bfs_statpop.parquet) summed over the backbone
    membership. Columns: agglomeration (int), agglomeration_name, pop, year."""
    from pipeline.common import REFERENCE_DATE, interim_path
    obs = pd.read_parquet(interim_path("observation", "bfs_statpop.parquet"),
                          columns=["unit_id", "level", "metric_id", "period", "value", "status"])
    obs = obs[(obs.metric_id == "pop_total") & (obs.level == "gemeinde") & (obs.status == "ok")]
    year = max(obs.period, key=lambda p: int(str(p)[:4]))
    obs = obs[obs.period == year]
    mem = pd.read_parquet(interim_path("backbone", f"membership_{REFERENCE_DATE.isoformat()}.parquet"),
                          columns=["bfs_nr", "agglomeration", "agglomeration_name"])
    if len(obs) != len(mem):
        raise ValueError(f"STATPOP {year}: {len(obs)} municipalities with pop_total, membership has {len(mem)}")
    m = mem.assign(unit_id=mem.bfs_nr.astype(int).astype(str)).merge(obs[["unit_id", "value"]], on="unit_id")
    m = m.dropna(subset=["agglomeration"])
    a = m.groupby(["agglomeration", "agglomeration_name"], as_index=False)["value"].sum()
    a = a.rename(columns={"value": "pop"}).astype({"agglomeration": int})
    a["year"] = str(year)
    return a.sort_values("pop", ascending=False, ignore_index=True)


def nearest_hubs(check: bool = True) -> tuple[list[str], pd.DataFrame]:
    """The hub set for the nearest-hub metrics, derived from the data (rule in the module docstring).
    Returns (slugs in descending agglomeration population, the qualifying agglomerations with their hub)."""
    a = agglomeration_population()
    q = a[a["pop"] >= MIN_AGGLO_POP].copy()
    unmapped = q[~q.agglomeration.isin(AGGLO_HUB)]
    if len(unmapped):
        raise ValueError(f"agglomerations >= {MIN_AGGLO_POP} residents without a hub station: "
                         f"{unmapped[['agglomeration', 'agglomeration_name', 'pop']].to_dict('records')}")
    q["hub"] = q.agglomeration.map(AGGLO_HUB)
    slugs = q.hub.tolist()
    if check and slugs != NEAREST_HUBS_EXPECTED:
        raise ValueError(f"nearest-hub set changed (D39 lists {NEAREST_HUBS_EXPECTED}); derived from "
                         f"STATPOP {q.year.iloc[0]}: {slugs}. Review with the owner before updating.")
    missing = set(slugs) - set(SLUGS)
    if missing:
        raise ValueError(f"nearest hubs not in HUBS: {sorted(missing)}")
    return slugs, q


def nearest_rule_text(lang: str, year: str, slugs: list[str] | None = None) -> str:
    slugs = slugs or NEAREST_HUBS_EXPECTED
    return NEAREST_RULE[lang].format(year=year, hubs=", ".join(NAMES[s] for s in slugs))
