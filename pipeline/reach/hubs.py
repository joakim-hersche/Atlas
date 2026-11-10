"""The 20 reach hubs (decision D9) and their main station in the GTFS feed.

Each hub is its main rail station, identified by didok number (= GTFS stops.didok of the parent
station; GTFS station id 'Parentch:1:sloid:<didok - 8500000>'). Nearby tram/bus stops are reached
from it over the 400 m footpaths, so they are not listed as extra sources.
"""
from __future__ import annotations

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
]
SLUGS = [h[0] for h in HUBS]
