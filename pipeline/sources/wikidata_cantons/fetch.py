"""Canton (and country) names in de/fr/it/rm/en from Wikidata (cantons.csv next to this file).

    python -m pipeline.sources.wikidata_cantons.fetch

SPARQL (query.wikidata.org): items with P31 = Q23058 (canton of Switzerland) and their P300
(ISO 3166-2 code, CH-XX), labels de/fr/it/rm/en. The labels carry a "Kanton"/"canton de" prefix
in most languages; `short_<lang>` is the label with that prefix removed (a fixed list of prefixes,
below), e.g. "Kanton Genf" -> "Genf", "Canton of Geneva" -> "Geneva". The response is cached
through pipeline.common.fetch (data/raw/wikidata_cantons/...). Data: Wikidata, CC0 1.0.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from pipeline.common import fetch

SOURCE = "wikidata_cantons"
SPARQL = "https://query.wikidata.org/sparql"
OUT = Path(__file__).with_name("cantons.csv")
LANGS = ["de", "fr", "it", "rm", "en"]

QUERY = """
SELECT ?item ?iso ?de ?fr ?it ?rm ?en WHERE {
  ?item wdt:P31 wd:Q23058 ; wdt:P300 ?iso .
  OPTIONAL { ?item rdfs:label ?de FILTER(LANG(?de) = "de") }
  OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
  OPTIONAL { ?item rdfs:label ?it FILTER(LANG(?it) = "it") }
  OPTIONAL { ?item rdfs:label ?rm FILTER(LANG(?rm) = "rm") }
  OPTIONAL { ?item rdfs:label ?en FILTER(LANG(?en) = "en") }
}"""

# Switzerland itself (Q39), for the national unit in search
QUERY_CH = """
SELECT ?item ?de ?fr ?it ?rm ?en WHERE {
  VALUES ?item { wd:Q39 }
  OPTIONAL { ?item rdfs:label ?de FILTER(LANG(?de) = "de") }
  OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
  OPTIONAL { ?item rdfs:label ?it FILTER(LANG(?it) = "it") }
  OPTIONAL { ?item rdfs:label ?rm FILTER(LANG(?rm) = "rm") }
  OPTIONAL { ?item rdfs:label ?en FILTER(LANG(?en) = "en") }
}"""

PREFIX = re.compile(r"^(Kanton|Canton of the|Canton of|canton de la|canton des|canton du|canton de|canton d'|"
                    r"cantone|canton|Chantun)\s*", re.I)


def short(label: str | None) -> str | None:
    if not isinstance(label, str):
        return None
    return PREFIX.sub("", label).strip() or label


def _sparql(query: str, name: str) -> pd.DataFrame:
    name = f"{name}_{hashlib.sha1(query.encode()).hexdigest()[:8]}.json"  # new query -> new cache file
    p = fetch(SPARQL, SOURCE, name, params={"query": query, "format": "json"},
              headers={"Accept": "application/sparql-results+json"})
    res = json.loads(Path(p).read_text(encoding="utf-8"))
    rows = [{k: v["value"] for k, v in b.items()} for b in res["results"]["bindings"]]
    return pd.DataFrame(rows, columns=res["head"]["vars"])


def build(write: bool = True) -> pd.DataFrame:
    """26 canton rows (kanton = ISO code suffix) plus one row kanton = 'CH' for Switzerland."""
    d = _sparql(QUERY, "sparql_cantons")
    d = d[d["iso"].str.fullmatch(r"CH-[A-Z]{2}")].copy()
    d["kanton"] = d["iso"].str[3:]
    d["qid"] = d["item"].str.rsplit("/", n=1).str[1]
    d = d.sort_values("qid").drop_duplicates("kanton")
    for lang in LANGS:
        d[f"short_{lang}"] = d[lang].map(short)
    if len(d) != 26:
        raise ValueError(f"expected 26 cantons from Wikidata, got {len(d)}")
    ch = _sparql(QUERY_CH, "sparql_switzerland").head(1).assign(kanton="CH", qid="Q39")
    for lang in LANGS:
        ch[f"short_{lang}"] = ch[lang]
    d = pd.concat([d, ch[d.columns.intersection(ch.columns)]], ignore_index=True)
    d = d.rename(columns={lang: f"label_{lang}" for lang in LANGS})
    d = d[["kanton", "qid", *[f"label_{l}" for l in LANGS], *[f"short_{l}" for l in LANGS]]].sort_values("kanton")
    if write:
        d.to_csv(OUT, index=False)
    return d


if __name__ == "__main__":
    print(build().to_string())
