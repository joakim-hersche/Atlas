"""Build the Wikidata identity lookup of the current municipalities (identity.csv next to this file).

    uv run python -m pipeline.sources.wikidata_identity.fetch

1. SPARQL (query.wikidata.org): items with P31 = Q70208 (municipality of Switzerland) and no P576
   (dissolved), with their P771 (Swiss municipality code), labels de/fr/it/rm/en, P856 (official
   website), P94 (coat of arms image) and the sitelink count; a second query lists their Wikipedia
   articles (wikiGroup "wikipedia").
2. Join to the reference-state municipalities on the BFS number. P771 statements with an end time
   (pq:P582) are ignored when a current statement exists. Municipalities whose item carries no P771
   are matched on the exact German label among unmatched current-municipality items (match = label).
   Several truthy P94/P856 values: the first in sort order is used, the others are kept in *_alt.
3. Coat-of-arms licences from the Commons API (extmetadata LicenseShortName, AttributionRequired),
   50 titles per request, paced; images are not downloaded.
All responses are cached through pipeline.common.fetch (data/raw/wikidata_identity/...).
Data: Wikidata, CC0 1.0. Coat-of-arms files: licence per file as recorded.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
from pathlib import Path

import pandas as pd

from pipeline.common import REFERENCE_DATE, fetch, interim_path

SOURCE = "wikidata_identity"
SPARQL = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/w/api.php"
OUT = Path(__file__).with_name("identity.csv")
LANGS = ["de", "fr", "it", "rm", "en"]
WIKIS = ["de", "fr", "it", "en"]

Q_ITEMS = """
SELECT ?item ?code ?end ?de ?fr ?it ?rm ?en ?web ?coa ?sl WHERE {
  ?item wdt:P31 wd:Q70208 .
  FILTER NOT EXISTS { ?item wdt:P576 ?dissolved }
  OPTIONAL { ?item p:P771 ?st . ?st ps:P771 ?code . OPTIONAL { ?st pq:P582 ?end } }
  OPTIONAL { ?item rdfs:label ?de FILTER(LANG(?de) = "de") }
  OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
  OPTIONAL { ?item rdfs:label ?it FILTER(LANG(?it) = "it") }
  OPTIONAL { ?item rdfs:label ?rm FILTER(LANG(?rm) = "rm") }
  OPTIONAL { ?item rdfs:label ?en FILTER(LANG(?en) = "en") }
  OPTIONAL { ?item wdt:P856 ?web }
  OPTIONAL { ?item wdt:P94 ?coa }
  ?item wikibase:sitelinks ?sl .
}"""

Q_WIKIPEDIA = """
SELECT ?item ?article ?wiki WHERE {
  hint:Query hint:optimizer "None" .
  ?item wdt:P31 wd:Q70208 .
  FILTER NOT EXISTS { ?item wdt:P576 ?dissolved }
  ?article schema:about ?item .
  ?article schema:isPartOf ?wiki .
  ?wiki wikibase:wikiGroup "wikipedia" .
}"""


def _sparql(query: str, name: str) -> pd.DataFrame:
    name = f"{name}_{hashlib.sha1(query.encode()).hexdigest()[:8]}.json"  # new query -> new cache file
    p = fetch(SPARQL, SOURCE, name, params={"query": query, "format": "json"},
              headers={"Accept": "application/sparql-results+json"})
    res = json.loads(Path(p).read_text(encoding="utf-8"))
    rows = [{k: v["value"] for k, v in b.items()} for b in res["results"]["bindings"]]
    df = pd.DataFrame(rows, columns=res["head"]["vars"])
    df["qid"] = df["item"].str.rsplit("/", n=1).str[1]
    return df


def _first(s: pd.Series):
    v = sorted(set(s.dropna()))
    return v[0] if v else None


def _alts(s: pd.Series):
    v = sorted(set(s.dropna()))
    return " | ".join(v[1:]) if len(v) > 1 else None


def _items() -> pd.DataFrame:
    d = _sparql(Q_ITEMS, "sparql_items")
    d["code"] = pd.to_numeric(d["code"], errors="coerce")
    d["coa_file"] = d["coa"].map(lambda u: urllib.parse.unquote(u.rsplit("/", 1)[1]) if isinstance(u, str) else None)
    per_item = d.groupby("qid").agg(
        **{f"label_{l}": (l, _first) for l in LANGS},
        website=("web", _first), website_alt=("web", _alts),
        coat_of_arms_file=("coa_file", _first), coat_of_arms_alt=("coa_file", _alts),
        sitelinks_total=("sl", "first"))
    codes = d[d["code"].notna()][["qid", "code", "end"]].drop_duplicates()
    # current codes first; ended statements only where an item has nothing else
    codes["ended"] = codes["end"].notna()
    return per_item, codes


def _wikipedia() -> pd.DataFrame:
    w = _sparql(Q_WIKIPEDIA, "sparql_wikipedia")
    w["lang"] = w["wiki"].str.extract(r"https://([^.]+)\.wikipedia\.org/", expand=False)
    n = w.groupby("qid")["wiki"].nunique().rename("wikipedia_editions")
    links = w[w["lang"].isin(WIKIS)].pivot_table(index="qid", columns="lang", values="article", aggfunc="first")
    links = links.reindex(columns=WIKIS).add_prefix("wikipedia_")
    return pd.concat([n, links], axis=1)


def _commons_licences(files: list[str], pause: float = 6.0) -> pd.DataFrame:
    rows = []
    files = sorted(set(f for f in files if f))
    for i in range(0, len(files), 50):
        batch = files[i:i + 50]
        titles = "|".join(f"File:{f}" for f in batch)
        key = hashlib.sha1(titles.encode()).hexdigest()[:12]
        params = {"action": "query", "titles": titles, "prop": "imageinfo", "iiprop": "extmetadata",
                  "iiextmetadatafilter": "LicenseShortName|AttributionRequired|License|Artist",
                  "format": "json", "formatversion": "2"}
        for attempt in range(4):
            try:
                p = fetch(COMMONS, SOURCE, f"commons_extmetadata_{key}.json", params=params)
                break
            except RuntimeError:  # repeated HTTP 429: back off and try again
                time.sleep(60 * (attempt + 1))
        else:
            raise RuntimeError("Commons API keeps refusing (429)")
        if Path(p).stat().st_mtime > time.time() - 30:  # fresh download: be gentle
            time.sleep(pause)
        res = json.loads(Path(p).read_text(encoding="utf-8"))
        norm = {n["to"]: n["from"] for n in res.get("query", {}).get("normalized", [])}
        for page in res.get("query", {}).get("pages", []):
            title = norm.get(page["title"], page["title"])
            meta = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
            rows.append({"coat_of_arms_file": title.split(":", 1)[1],
                         "license_short_name": meta.get("LicenseShortName", {}).get("value"),
                         "license": meta.get("License", {}).get("value"),
                         "attribution_required": meta.get("AttributionRequired", {}).get("value"),
                         "commons_missing": bool(page.get("missing"))})
    out = pd.DataFrame(rows)
    # titles come back normalised (underscores -> spaces); match on the normalised form
    out["key"] = out["coat_of_arms_file"].str.replace("_", " ")
    return out.drop(columns="coat_of_arms_file").drop_duplicates("key")


def build(write: bool = True) -> pd.DataFrame:
    ref = pd.read_parquet(interim_path("backbone", f"membership_{REFERENCE_DATE.isoformat()}.parquet"),
                          columns=["bfs_nr", "name", "kanton"])
    per_item, codes = _items()
    cur = codes[~codes["ended"]]
    m = ref.merge(cur[["qid", "code"]], left_on="bfs_nr", right_on="code", how="left")
    m["match"] = m["qid"].notna().map({True: "P771", False: None})
    miss = m["qid"].isna()
    if miss.any():  # ended codes
        old = codes[codes["ended"]].drop_duplicates("code").set_index("code")["qid"]
        m.loc[miss, "qid"] = m.loc[miss, "bfs_nr"].map(old)
        m.loc[miss & m["qid"].notna(), "match"] = "P771_ended"
    miss = m["qid"].isna()
    if miss.any():  # items without any P771: exact German label, unique, not used yet
        used = set(m["qid"].dropna())
        free = per_item[~per_item.index.isin(used) & ~per_item.index.isin(codes["qid"])]
        by_label = free.reset_index().groupby("label_de")["qid"].agg(list)
        for i in m.index[miss]:
            hit = by_label.get(m.at[i, "name"])
            if hit and len(hit) == 1:
                m.at[i, "qid"], m.at[i, "match"] = hit[0], "label_de"
    if m["bfs_nr"].duplicated().any():
        dup = m[m["bfs_nr"].duplicated(keep=False)]
        raise ValueError(f"BFS numbers matched to several items: {dup[['bfs_nr', 'qid']].values.tolist()}")
    m = m.drop(columns="code").merge(per_item, left_on="qid", right_index=True, how="left")
    m = m.merge(_wikipedia(), left_on="qid", right_index=True, how="left")
    lic = _commons_licences(m["coat_of_arms_file"].dropna().tolist())
    m["key"] = m["coat_of_arms_file"].str.replace("_", " ")
    m = m.merge(lic, on="key", how="left").drop(columns="key")
    m["wikipedia_editions"] = m["wikipedia_editions"].fillna(0).where(m["qid"].notna()).astype("Int64")
    m["sitelinks_total"] = pd.to_numeric(m["sitelinks_total"]).astype("Int64")
    cols = ["bfs_nr", "name", "kanton", "qid", "match", *[f"label_{l}" for l in LANGS], "website",
            "website_alt", "coat_of_arms_file", "coat_of_arms_alt", "license_short_name",
            "attribution_required", "license", "commons_missing", *[f"wikipedia_{w}" for w in WIKIS],
            "wikipedia_editions", "sitelinks_total"]
    m = m[cols].sort_values("bfs_nr")
    if write:
        m.to_csv(OUT, index=False)
    return m


if __name__ == "__main__":
    df = build()
    print(len(df), "rows ->", OUT)
    print(df["match"].value_counts(dropna=False).to_dict())
    print(df["license_short_name"].value_counts(dropna=False).head(10).to_dict())
