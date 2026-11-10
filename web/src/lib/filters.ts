// Stacked filters (brief 6.1): any number of conditions, combined with AND.
// A unit with no value for a filtered metric does not match; those are counted separately so the
// UI can say how many were excluded for missing data (D21: gaps are shown, never hidden).
import type { ColView } from './columns.svelte';
import { type LevelData, type MetricMeta, type UnitRow } from './data';
import { emptyFilter, type CatField, type Filter } from './hash';
import { fmtNumber, rangeText, sortedValues, wantsLog } from './classify';
import { ml, t, levelWord, unitName } from './i18n.svelte';
import { commuteLabel, commuteValues, describeCommute, nearestMetricId, reachTimesData, type CommuteValues } from './commute.svelte';

/** Label of a categorical filter field in the UI language. */
export const catLabel = (f: CatField): string => t(`cat.${f}`);

export interface CatOption {
  id: string;
  name: string;
}

export interface FilterEval {
  filter: Filter;
  /** active: filters the map; loading: data not there yet (no effect); inactive: cannot apply here */
  status: 'active' | 'loading' | 'inactive';
  note: string | null;
  /** 1 = passes (only when active) */
  pass: Uint8Array | null;
  /** 1 = no value for this condition's metric (counted as not passing) */
  miss: Uint8Array | null;
  nPass: number;
  nMissing: number;
  /** numeric conditions: the column and the slider domain */
  col?: ColView;
  domain?: { min: number; max: number; log: boolean };
  /** reach conditions: hub name */
  hubName?: string;
  /** commute conditions: the measure per unit (minutes) and its label, for the ranking table */
  values?: (number | null)[];
  label?: string;
  /** commute conditions: one-line description (hub names resolved) */
  desc?: string;
}

export interface FilterContext {
  ld: LevelData;
  rows: UnitRow[] | null;
  metas: Map<string, MetricMeta>;
  hubName: (slug: string) => string;
  /** reactive column lookup (ColumnStore.get bound to the level and year) */
  col: (id: string) => ColView | null | undefined;
}

/** Value of a categorical field per unit of the current level, or null when it does not apply. */
export function catValues(field: CatField, ld: LevelData, rows: UnitRow[] | null): (string | undefined)[] | null {
  if (ld.level === field) return ld.units.slice();
  if (field === 'kanton' && ld.level !== 'gemeinde') {
    return ld.canton.some(Boolean) ? ld.canton.map((c) => c || undefined) : null;
  }
  if (ld.level !== 'gemeinde' || !rows) return null;
  const out: (string | undefined)[] = new Array(ld.units.length);
  for (const r of rows) {
    if (r.level !== 'gemeinde') continue;
    const i = ld.index.get(r.id);
    if (i === undefined) continue;
    const v = field === 'kanton' ? r.kanton : r[field];
    out[i] = v ?? undefined;
  }
  return out;
}

/** Options of a categorical field (from units.json), sorted for display. */
export function catOptions(field: CatField, rows: UnitRow[] | null): CatOption[] {
  if (!rows) return [];
  const out = rows.filter((r) => r.level === field).map((r) => ({ id: r.id, name: unitName(r) }));
  if (field === 'agglomeration') out.sort((a, b) => a.name.localeCompare(b.name, 'de'));
  else out.sort((a, b) => (field === 'kanton' ? a.id.localeCompare(b.id) : Number(a.id) - Number(b.id)));
  return out;
}

export function evalFilter(f: Filter, cx: FilterContext): FilterEval {
  const n = cx.ld.units.length;
  const word = levelWord(cx.ld.level);
  const base = { filter: f, pass: null, miss: null, nPass: n, nMissing: 0 };
  if (f.kind === 'cat') {
    const vals = catValues(f.field, cx.ld, cx.rows);
    if (!vals) {
      if (cx.ld.level === 'gemeinde' && !cx.rows) return { ...base, status: 'loading', note: t('f.loading') };
      return { ...base, status: 'inactive', note: t(f.field === 'kanton' ? 'f.catOnlyKt' : 'f.catOnlyGem', { units: word }) };
    }
    if (!f.values.length) return { ...base, status: 'inactive', note: t('f.chooseValues') };
    const want = new Set(f.values);
    const pass = new Uint8Array(n);
    let nPass = 0;
    for (let i = 0; i < n; i++) {
      const v = vals[i];
      if (v !== undefined && want.has(v)) {
        pass[i] = 1;
        nPass++;
      }
    }
    return { ...base, status: 'active', note: null, pass, nPass };
  }

  if (f.kind === 'commute') {
    if (cx.ld.level !== 'gemeinde') return { ...base, status: 'inactive', note: t('f.reachGem', { units: word }) };
    let cv: CommuteValues;
    if (f.op === 'near') {
      // the nearest-hub time is a metric column (D39 hub list), not recomputed here
      const id = nearestMetricId(f.mode);
      if (!cx.metas.has(id)) return { ...base, status: 'inactive', note: t('cm.notBuild') };
      const c = cx.col(id);
      if (c === undefined) return { ...base, status: 'loading', note: t('f.loading') };
      if (c === null) return { ...base, status: 'inactive', note: t('f.notPub', { units: word }) };
      cv = { v: c.col.v, status: 'ok', note: null };
    } else cv = commuteValues(f, cx.ld.units, reachTimesData());
    if (cv.status !== 'ok') return { ...base, status: cv.status, note: cv.note };
    const pass = new Uint8Array(n);
    const miss = new Uint8Array(n);
    let nPass = 0;
    let nMissing = 0;
    for (let i = 0; i < n; i++) {
      const x = cv.v[i];
      if (x === null || x === undefined) {
        miss[i] = 1;
        nMissing++;
      } else if ((f.lo === null || x >= f.lo) && (f.hi === null || x <= f.hi)) {
        pass[i] = 1;
        nPass++;
      }
    }
    const s = sortedValues(cv.v);
    const domain = s.length ? { min: s[0], max: s[s.length - 1], log: false } : undefined;
    return { filter: f, status: 'active', note: null, pass, miss, nPass, nMissing, domain, values: cv.v, label: commuteLabel(f, cx.hubName), desc: describeCommute(f, cx.hubName) };
  }

  let id: string;
  let lo: number | null;
  let hi: number | null;
  let hubName: string | undefined;
  if (f.kind === 'reach') {
    hubName = cx.hubName(f.hub);
    if (cx.ld.level !== 'gemeinde') return { ...base, status: 'inactive', note: t('f.reachGem', { units: word }), hubName };
    id = `reach_${f.mode}_${f.hub}`;
    lo = null;
    hi = f.max;
  } else {
    id = f.metric;
    lo = f.lo;
    hi = f.hi;
  }
  const meta = cx.metas.get(id);
  if (!meta) return { ...base, status: 'inactive', note: t('f.notInBuild'), hubName };
  const c = cx.col(id);
  if (c === undefined) return { ...base, status: 'loading', note: t('f.loading'), hubName };
  if (c === null) {
    const note = t(meta.aggregation === 'not_aggregatable' ? 'f.notAgg' : 'f.notPub', { units: word });
    return { ...base, status: 'inactive', note, hubName };
  }
  const v = c.col.v;
  const pass = new Uint8Array(n);
  const miss = new Uint8Array(n);
  let nPass = 0;
  let nMissing = 0;
  for (let i = 0; i < n; i++) {
    const x = v[i];
    if (x === null || x === undefined) {
      miss[i] = 1;
      nMissing++;
    } else if ((lo === null || x >= lo) && (hi === null || x <= hi)) {
      pass[i] = 1;
      nPass++;
    }
  }
  const s = sortedValues(v);
  const domain = s.length ? { min: s[0], max: s[s.length - 1], log: wantsLog(s) } : undefined;
  return { filter: f, status: 'active', note: null, pass, miss, nPass, nMissing, col: c, domain, hubName };
}

export interface MatchResult {
  /** 1 = matches all active conditions */
  m: Uint8Array;
  n: number;
  /** units excluded only because a filtered metric has no value */
  nMissingOnly: number;
  active: number;
}

export function combine(evals: FilterEval[], n: number): MatchResult {
  const m = new Uint8Array(n).fill(1);
  // a range with neither end set filters nothing (it would only drop the units without a value)
  const act = evals.filter((e) => e.status === 'active' && e.pass && !emptyFilter(e.filter));
  let count = 0;
  let nMissingOnly = 0;
  for (let i = 0; i < n; i++) {
    let ok = true;
    let missing = false;
    let other = false;
    for (const e of act) {
      if (e.pass![i]) continue;
      ok = false;
      if (e.miss?.[i]) missing = true;
      else other = true;
    }
    m[i] = ok ? 1 : 0;
    if (ok) count++;
    else if (missing && !other) nMissingOnly++;
  }
  return { m, n: count, nMissingOnly, active: act.length };
}

/** One short line per condition ("Population 1'000–5'000", "Canton: ZH, BE", "≤ 30 min to Bern, PT"). */
export function describeFilter(e: FilterEval, nameOf: (field: CatField, id: string) => string): string {
  const f = e.filter;
  if (f.kind === 'cat') return `${catLabel(f.field)}: ${f.values.map((v) => nameOf(f.field, v)).join(', ') || '–'}`;
  if (f.kind === 'commute') return e.desc ?? f.op;
  if (f.kind === 'reach') return t('f.reachDesc', { max: f.max, hub: e.hubName ?? f.hub, mode: t(f.mode === 'ptst' ? 'pt.stS' : f.mode === 'pt' ? 'common.pt' : 'common.car') });
  const m = e.col?.meta;
  const d = m?.decimals ?? 0;
  const lo = f.lo === null ? '' : fmtNumber(f.lo, d);
  const hi = f.hi === null ? '' : fmtNumber(f.hi, d);
  const rng = f.lo !== null && f.hi !== null ? rangeText(lo, hi) : f.lo !== null ? `≥ ${lo}` : f.hi !== null ? `≤ ${hi}` : t('f.any');
  return `${m ? ml(m) : f.metric} ${rng}`;
}
