"""Crosswalk from any municipality version (histId) to the municipality state at a target date.

Topology comes from the official mutation list: every mutation links initial versions to terminal
versions. Where an initial version has a single successor, the weight is 1 (renames, renumbering,
reassignments, mergers). Where it has several successors (splits, territory exchanges), the weights
are the share of the version's population that ends up in each successor, measured with the BFS
population hectare grid on the historized boundaries (see weights.py). Weights are chained through
successive mutations until the target date is reached.

Output: crosswalk.parquet with one row per (from_hist_id, to_hist_id) and
  weight          share of the source version's population (or area) mapped to the target
  weight_source   'identity' | 'single_successor' | method label of the split weights
  n_steps         number of mutations chained
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

import pandas as pd

from pipeline.common import REFERENCE_DATE, interim_path


def load_backbone() -> tuple[pd.DataFrame, pd.DataFrame]:
    mv = pd.read_parquet(interim_path("backbone", "municipality_version.parquet"))
    pair = pd.read_parquet(interim_path("backbone", "mutation_pair.parquet"))
    return mv, pair


def versions_at(mv: pd.DataFrame, date: dt.date, municipalities_only: bool = True) -> pd.DataFrame:
    """Municipality versions valid on a date (valid_from <= date <= valid_to or open)."""
    d = pd.Timestamp(date)
    sel = (mv["valid_from"] <= d) & (mv["valid_to"].isna() | (mv["valid_to"] >= d))
    if municipalities_only:
        sel &= mv["entry_mode"] == "11"
    return mv[sel]


def split_pairs(pair: pd.DataFrame) -> pd.DataFrame:
    """(mutation, from_hist_id) groups with more than one successor: these need weights."""
    n = pair.groupby(["mutation_id", "from_hist_id"])["to_hist_id"].transform("nunique")
    return pair[n > 1]


def build_crosswalk(mv: pd.DataFrame, pair: pd.DataFrame, split_weights: pd.DataFrame,
                    target_date: dt.date = REFERENCE_DATE) -> pd.DataFrame:
    """Chain mutations forward from every version to the versions valid on target_date.

    split_weights: columns mutation_id, from_hist_id, to_hist_id, weight, weight_source
    (one set of weights per split group, summing to 1 per (mutation_id, from_hist_id)).
    """
    target = pd.Timestamp(target_date)
    # successors of each version, by the mutation that abolished/changed it
    succ: dict[int, list[tuple[int, float, str]]] = defaultdict(list)
    sw = {(r.mutation_id, r.from_hist_id, r.to_hist_id): (r.weight, r.weight_source)
          for r in split_weights.itertuples()}
    pair = pair[pair["date"] <= target]
    groups = pair.groupby(["mutation_id", "from_hist_id"])
    for (mid, fh), g in groups:
        tos = sorted(set(g["to_hist_id"]))
        if len(tos) == 1:
            if tos[0] != fh:
                succ[fh].append((tos[0], 1.0, "single_successor"))
            continue
        for th in tos:
            w, src = sw.get((mid, fh, th), (None, None))
            if w is None:
                raise KeyError(f"missing split weight for mutation {mid}: {fh} -> {th}")
            succ[fh].append((th, w, src))

    valid_target = set(versions_at(mv, target_date, municipalities_only=False)["hist_id"].astype(int))

    memo: dict[int, dict[int, tuple[float, set, int]]] = {}

    def resolve(h: int, depth: int = 0) -> dict[int, tuple[float, set, int]]:
        if h in memo:
            return memo[h]
        if depth > 200:
            raise RecursionError(f"mutation chain too long at {h}")
        if h in valid_target or h not in succ:
            res = {h: (1.0, set(), 0)}
        else:
            res = {}
            for th, w, src in succ[h]:
                for t, (w2, srcs, n) in resolve(th, depth + 1).items():
                    w0, s0, n0 = res.get(t, (0.0, set(), 0))
                    res[t] = (w0 + w * w2, s0 | srcs | {src}, max(n0, n + 1))
        memo[h] = res
        return res

    rows = []
    for h in mv["hist_id"].astype(int):
        for t, (w, srcs, n) in resolve(h).items():
            if t not in valid_target:
                continue  # dead end: e.g. territory leaving Switzerland; logged by validation
            if n == 0:
                src = "identity"
            elif srcs <= {"single_successor"}:
                src = "single_successor"
            else:
                src = "+".join(sorted(s for s in srcs if s != "single_successor"))
            rows.append((h, t, w, src, n))
    cw = pd.DataFrame(rows, columns=["from_hist_id", "to_hist_id", "weight", "weight_source", "n_steps"])
    tgt = mv.set_index("hist_id")[["bfs_nr", "name", "canton"]]
    cw = cw.join(tgt.rename(columns=lambda c: "to_" + c), on="to_hist_id")
    cw = cw.join(tgt.rename(columns=lambda c: "from_" + c), on="from_hist_id")
    cw["target_date"] = target
    return cw


def map_bfs_at_date(mv: pd.DataFrame, bfs_nr: pd.Series, date: dt.date) -> pd.Series:
    """Resolve BFS numbers valid on a date to histIds (NaN where no version is valid)."""
    v = versions_at(mv, date, municipalities_only=False)
    lookup = v.drop_duplicates("bfs_nr").set_index("bfs_nr")["hist_id"]
    return bfs_nr.map(lookup)
