"""Map curation (decision D38): which metric × level maps the app offers, from pipeline/curation.yaml.

The rule (audit round 2, docs/audit_round2.md) runs on the shipped default-period values, after the
aggregation fixes (M1), so a map is not hidden for a gap the build can close:
  SHOW  the metric covers >= 80 % of the level's units and >= 80 % of its population
  NOTE  >= 25 % of units, >= 50 % of population and >= 20 units (shown, labelled as partial)
  HIDE  otherwise; levels with fewer than 20 units are shown only when every unit has a value
A unit counts as covered when it has a value (ok), a single-seat canton's value (majority_election) or
a defined 'does not apply' (not_applicable, e.g. a party that did not stand).
The file's explicit decisions (with reasons) override the rule: whole metrics (duplicates, technical
denominators, confidence intervals), single metric × level cells, and whole levels.

Enforcement in metrics.json (pipeline.build.web), using the mechanisms the frontend already reads:
  hidden: true                 metric never offered (picker, profiles, sources list); levels kept
  levels                       a hidden level is removed, so the picker, level switch and tables skip it
  unavailable_levels[level]    the reason (one clause, no closing full stop), shown where the level is not offered
  profile_levels               all levels with values (profiles keep hidden-from-map values, labelled)
  curation {level: {v, why}}   the verdict per level ('show' | 'note' | 'hide') and its reason
featured.json lists the featured story maps; each must be shown or noted at its level.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

PATH = Path(__file__).resolve().parents[1] / "curation.yaml"
NEVER_CURATED = ("schweiz",)   # one unit: never a map, but the Swiss reference value stays


def load(path: Path = PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def rule_verdict(n: int, n_units: int, pop_share: float, rule: dict) -> tuple[str, str]:
    """(verdict, reason) of the generic coverage rule for one metric × level."""
    show, note = rule.get("show") or {}, rule.get("note") or {}
    small = int(rule.get("small_level_units", 20))
    us = n / n_units if n_units else 0.0
    cov = f"{n:,} of {n_units:,} units, {100 * pop_share:.0f} % of residents"
    if n == 0:
        return "hide", "no values at this level"
    if n_units < small:
        if n == n_units:
            return "show", f"complete ({cov})"
        return "hide", f"fewer than {small} units: shown only when every unit has a value ({cov})"
    if us >= float(show.get("min_unit_share", 0.8)) and pop_share >= float(show.get("min_pop_share", 0.8)):
        return "show", cov
    if (us >= float(note.get("min_unit_share", 0.25)) and pop_share >= float(note.get("min_pop_share", 0.5))
            and n >= int(note.get("min_units", 20))):
        return "note", f"partial coverage: {cov}"
    return "hide", f"too little coverage for a map: {cov}"


def _match(mid: str, keys) -> dict | None:
    """Explicit entry for a metric: exact id first, then the first matching pattern ('re:<regex>')."""
    if mid in keys:
        return keys[mid]
    for k, v in keys.items():
        if str(k).startswith("re:") and re.fullmatch(str(k)[3:], mid):
            return v
    return None


def decide(mid: str, level: str, n: int, n_units: int, pop_share: float, cfg: dict) -> tuple[str, str, str]:
    """(verdict, reason, basis) for one metric × level; basis 'file' (explicit decision) or 'rule'."""
    v, why = rule_verdict(n, n_units, pop_share, cfg.get("rule") or {})
    m = _match(mid, cfg.get("metrics") or {}) or {}
    if m.get("hide"):
        return "hidden", m.get("reason", "hidden"), "file"
    if m.get("maps") is False:
        return "hide", m.get("reason", "not offered as a map"), "file"
    lv = (m.get("levels") or {}).get(level)
    if lv is not None:
        if isinstance(lv, str):
            lv = {"v": lv}
        return lv.get("v", v), lv.get("reason", m.get("reason", why)), "file"
    only = m.get("only_levels")
    if only is not None and level not in only:
        return "hide", m.get("reason", f"offered only at: {', '.join(only)}"), "file"
    lvl_rule = (cfg.get("levels") or {}).get(level) or {}
    if lvl_rule.get("hide") and not any(re.fullmatch(p, mid) for p in lvl_rule.get("except", [])):
        return "hide", lvl_rule.get("reason", "level not offered as a map"), "file"
    if v != "hide" and m.get("note"):
        return "note", m["note"], "file"
    return v, why, "rule"


def clean_reason(why: str) -> str:
    """A curation reason as one clause: whitespace collapsed (YAML folding) and no closing full stop."""
    return re.sub(r"\s+", " ", str(why)).strip().rstrip(".").strip()


def apply(entry: dict, verdicts: dict, levels_with_values: list[str]) -> dict:
    """Enforce one metric's verdicts {level: (verdict, reason, basis)} on its metrics.json entry."""
    entry["profile_levels"] = list(levels_with_values)
    if any(v[0] == "hidden" for v in verdicts.values()):
        entry["hidden"] = True
    cur = {}
    keep = []
    unav = dict(entry.get("unavailable_levels") or {})
    for lvl in levels_with_values:
        v = verdicts.get(lvl)
        if v is None:
            keep.append(lvl)
            continue
        verdict, why, _ = v
        cur[lvl] = {"v": "hide" if verdict == "hidden" else verdict, "why": clean_reason(why)}
        # a hidden metric keeps its levels: the app never offers it, but companions (e.g. the
        # confidence interval `<id>_ci` of a survey share) are looked up through them
        if verdict == "hide":
            # the app shows "Not available here: <reason>." (review round 3, C5: no repeated phrase and no
            # double full stop), so the reason is the plain why without its own closing full stop
            unav[lvl] = clean_reason(why)
        else:
            keep.append(lvl)
    entry["levels"] = keep
    entry["unavailable_levels"] = unav or None
    entry["curation"] = cur or None
    return entry


def featured(cfg: dict, catalog: list[dict]) -> list[dict]:
    """Featured story maps (journalist's list), each checked against the curated catalog."""
    by = {e["id"]: e for e in catalog}
    out = []
    for f in cfg.get("featured") or []:
        e = by.get(f["metric"])
        ok = bool(e) and not e.get("hidden") and f["level"] in (e.get("levels") or [])
        if not ok and f["level"] == "gemeinde" and e and not e.get("hidden"):
            # a regional value attached to municipalities (native level offered)
            ok = e.get("native_level") in (e.get("levels") or []) and e.get("native_level") != "gemeinde"
        out.append({**f, "available": ok, "label_en": e["label_en"] if e else None,
                    "label_de": e["label_de"] if e else None})
    return out
