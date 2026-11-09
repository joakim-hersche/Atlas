"""Generic client for the BFS SDMX platform (.Stat Suite, NSI Web Service).

Base: https://disseminate.stats.swiss/rest
  GET /dataflow/all                                         catalogue (SDMX-ML)
  GET /dataflow/<agency>/<DF>/<ver>?references=all          dataflow + DSD + codelists
  GET /availableconstraint/<agency>,<DF>,<ver>/all/all/all  codes actually present per dimension
  GET /data/<agency>,<DF>,<ver>/<key>?startPeriod=&endPeriod=
      Accept: application/vnd.sdmx.data+csv;version=1.0.0   -> CSV with codes
The key has one position per dimension (TIME_PERIOD excluded) in DSD order, '.'-separated;
an empty position is a wildcard and '+' means OR. A wrong number of positions gives HTTP 422,
a query without matches HTTP 404 (NoRecordsFound).

Geo codes (codelists CL_*KT_BEZ_GDE_SNAP_<year>): Gemeinde = plain BFS number, canton = its
abbreviation, district = 'B_<nr>', Switzerland = '8100'; flows may add NUTS-2 regions ('CH01')
and unknown ('_U'). All downloads are cached through pipeline.common.fetch under
data/raw/bfs_sdmx/<date>/; versions are pinned by the callers.

Licence: every flow links to a statistik.admin.ch asset with termsOfUse OPEN-BY.
"""
from __future__ import annotations

import hashlib
import io
import re
import time
import xml.etree.ElementTree as ET
from functools import lru_cache

import pandas as pd

from pipeline.common import fetch, latest_snapshot

SOURCE = "bfs_sdmx"
BASE = "https://disseminate.stats.swiss/rest"
CSV_ACCEPT = "application/vnd.sdmx.data+csv;version=1.0.0"
NS = {
    "m": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}
CANTONS = {"ZH", "BE", "LU", "UR", "SZ", "OW", "NW", "GL", "ZG", "FR", "SO", "BS", "BL", "SH", "AR",
           "AI", "SG", "GR", "AG", "TG", "TI", "VD", "VS", "NE", "GE", "JU"}
SWITZERLAND = "8100"
_last_call = [0.0]


def _pace():
    wait = 1.0 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.time()


def _flow_ref(agency: str, flow: str, version: str) -> str:
    return f"{agency},{flow},{version}"


def _get(url: str, filename: str, headers: dict | None = None, params: dict | None = None):
    if latest_snapshot(SOURCE, filename) is None:
        _pace()
    return fetch(url, SOURCE, filename, headers=headers, params=params)


@lru_cache(maxsize=None)
def structure(agency: str, flow: str, version: str) -> dict:
    """Dimensions (in key order) with their codelist codes and labels.

    Returns {"dimensions": [dim_id, ...], "codes": {dim_id: {code: label_en}}, "names": {...}}.
    """
    p = _get(f"{BASE}/dataflow/{agency}/{flow}/{version}", f"{flow}_{version}.structure.xml",
             params={"references": "all"})
    root = ET.parse(p).getroot()
    lists = {}
    for cl in root.iter(f"{{{NS['s']}}}Codelist"):
        codes = {}
        for code in cl.findall("s:Code", NS):
            names = {n.get("{http://www.w3.org/XML/1998/namespace}lang"): n.text
                     for n in code.findall("c:Name", NS)}
            codes[code.get("id")] = names.get("en") or names.get("de") or next(iter(names.values()), "")
        lists[(cl.get("agencyID"), cl.get("id"), cl.get("version"))] = codes
    dims, codes = [], {}
    dsd = root.find(".//s:DataStructure", NS)
    for d in dsd.find(".//s:DimensionList", NS):
        tag = d.tag.split("}")[1]
        if tag == "TimeDimension":
            continue
        did = d.get("id")
        dims.append((int(d.get("position", len(dims) + 1)), did))
        ref = d.find(".//s:Enumeration/Ref", NS)
        if ref is not None:
            codes[did] = lists.get((ref.get("agencyID"), ref.get("id"), ref.get("version")), {})
    dims = [x for _, x in sorted(dims)]
    return {"dimensions": dims, "codes": codes}


@lru_cache(maxsize=None)
def availability(agency: str, flow: str, version: str) -> dict:
    """Codes actually present per dimension, plus 'TIME_PERIOD' (start, end) and 'obs_count'."""
    p = _get(f"{BASE}/availableconstraint/{_flow_ref(agency, flow, version)}/all/all/all",
             f"{flow}_{version}.availability.xml")
    root = ET.parse(p).getroot()
    out: dict = {}
    for kv in root.iter(f"{{{NS['c']}}}KeyValue"):
        vals = [v.text for v in kv.findall("c:Value", NS)]
        tr = kv.find("c:TimeRange", NS)
        if tr is not None:
            st, en = tr.find("c:StartPeriod", NS), tr.find("c:EndPeriod", NS)
            vals = (st.text if st is not None else None, en.text if en is not None else None)
        out[kv.get("id")] = vals
    for a in root.iter(f"{{{NS['c']}}}Annotation"):
        if a.get("id") == "obs_count":
            out["obs_count"] = int(a.findtext("c:AnnotationTitle", namespaces=NS))
    return out


def key(agency: str, flow: str, version: str, select: dict[str, str | list[str] | None]) -> str:
    """Build a data key from {dimension: code | [codes] | None (wildcard)}."""
    dims = structure(agency, flow, version)["dimensions"]
    unknown = set(select) - set(dims)
    if unknown:
        raise KeyError(f"{flow}: unknown dimensions {unknown}; has {dims}")
    parts = []
    for d in dims:
        v = select.get(d)
        parts.append("" if v is None else (v if isinstance(v, str) else "+".join(v)))
    return ".".join(parts)


def data(agency: str, flow: str, version: str, select: dict[str, str | list[str] | None],
         start: str | int | None = None, end: str | int | None = None) -> pd.DataFrame:
    """Download (cached) and parse observations as strings (value column OBS_VALUE -> float 'value')."""
    k = key(agency, flow, version, select)
    params = {}
    if start is not None:
        params["startPeriod"] = str(start)
    if end is not None:
        params["endPeriod"] = str(end)
    h = hashlib.sha1(f"{k}|{sorted(params.items())}".encode()).hexdigest()[:12]
    p = _get(f"{BASE}/data/{_flow_ref(agency, flow, version)}/{k}", f"{flow}_{version}.{h}.csv",
             headers={"Accept": CSV_ACCEPT}, params=params or None)
    df = pd.read_csv(io.BytesIO(p.read_bytes()), dtype=str, keep_default_na=False)
    df["value"] = pd.to_numeric(df["OBS_VALUE"].replace("", None), errors="coerce")
    return df


def data_chunked(agency: str, flow: str, version: str, select: dict, years: list[int],
                 chunk: int = 4) -> pd.DataFrame:
    """data() split into year ranges (keeps single responses small)."""
    parts = []
    for i in range(0, len(years), chunk):
        ys = years[i:i + chunk]
        parts.append(data(agency, flow, version, select, start=ys[0], end=ys[-1]))
    return pd.concat(parts, ignore_index=True)


def geo_level(code: str) -> str | None:
    """Level of a geo code: gemeinde | bezirk | kanton | schweiz | None (other, e.g. NUTS, unknown)."""
    c = str(code)
    if c == SWITZERLAND:
        return "schweiz"
    if c in CANTONS:
        return "kanton"
    if re.fullmatch(r"B_\d+", c):
        return "bezirk"
    if re.fullmatch(r"\d{1,4}", c) and 0 < int(c) < 9000:
        return "gemeinde"
    return None


def native_unit(code: str, level: str) -> str:
    """Unit id convention of the observation table for published higher levels."""
    if level == "schweiz":
        return "CH"
    if level == "bezirk":
        return str(int(code[2:]))
    return code
