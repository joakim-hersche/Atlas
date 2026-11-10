// Commute filters: measures built from travel times to several hubs (web/reach_times.json).
//   sum   sum of the times to the chosen hubs          (e.g. two workplaces in one household)
//   max   longest of the times to the chosen hubs
//   any   shortest of the times to the chosen hubs     ("within N min of any of these hubs")
//   near  shortest time to any of the nearest-hub list ("within N min of the nearest hub", D39)
//   diff  public transport minus car time to one hub
// 'near' reads the precomputed nearest-hub metric (reach_<mode>_nearest_hub), the others reach_times.json.
// All of them work on municipalities (the only level with travel times). A municipality without a
// time to a hub that the measure needs has no value and does not match (counted as missing).
// The URL form is `f=m:<op>:<mode>:<hub,hub>:<lo>:<hi>` (lib/hash.ts).
import { addStrings, t } from './i18n.svelte';
import { fmtNumber } from './classify';
import type { MetricMeta } from './data';
import type { CommuteOp, Filter } from './hash';
import { loadReachTimes, type ReachTimes } from './places';
import { DE_FILTERS, EN_FILTERS } from './i18n-filters-strings';

addStrings(EN_FILTERS, DE_FILTERS);

export type CommuteFilter = Extract<Filter, { kind: 'commute' }>;
export type CommuteMode = CommuteFilter['mode'];

// ---------------------------------------------------------------- reach_times.json, loaded on demand
let rt = $state.raw<ReachTimes | null>(null);
let started = false;
/** The travel-time file (null until loaded; reading it inside $derived re-runs once it arrives). */
export function reachTimesData(): ReachTimes | null {
  if (!started) {
    started = true;
    loadReachTimes()
      .then((x) => (rt = x))
      .catch(() => (started = false));
  }
  return rt;
}

const indexCache = new WeakMap<ReachTimes, Map<string, number>>();
function rtIndex(r: ReachTimes): Map<string, number> {
  let m = indexCache.get(r);
  if (!m) indexCache.set(r, (m = new Map(r.units.map((u, k) => [u, k]))));
  return m;
}

/** Number of hubs that count for "nearest hub" (D39: agglomeration cores with 100,000+ residents). */
export function nearestHubCount(r: ReachTimes | null): number {
  return (r as (ReachTimes & { nearest_hubs?: unknown[] }) | null)?.nearest_hubs?.length ?? 15;
}

/** Hubs with a travel-time column (all hubs but those only used for the lines or the nearest-hub rule, e.g. Baden). */
export const commuteHubSlugs = (r: ReachTimes | null): string[] => (r ? Object.keys(r.pt ?? {}).filter((h) => r.car?.[h]) : []);

/** Metric holding the time to the nearest hub (precomputed by the pipeline over the D39 hub list). */
export const nearestMetricId = (mode: CommuteMode) => `reach_${mode}_nearest_hub`;

const series = (r: ReachTimes, mode: CommuteMode) => (mode === 'car' ? r.car : mode === 'pt' ? r.pt : r.pt_station);
export const hasStationTimes = (r: ReachTimes | null) => !!r?.pt_station && Object.keys(r.pt_station).length > 0;

/** Default filter of an operation (hubs: the first two hubs of the list, or the given ones). */
export function defaultCommute(op: CommuteOp, hubs: string[], station: boolean): CommuteFilter {
  const mode: CommuteMode = station ? 'ptst' : 'pt';
  if (op === 'diff') return { kind: 'commute', op, mode, hubs: hubs.slice(0, 1), lo: null, hi: 15 };
  if (op === 'near') return { kind: 'commute', op, mode, hubs: [], lo: null, hi: 30 };
  return { kind: 'commute', op, mode, hubs: hubs.slice(0, 2), lo: null, hi: op === 'sum' ? 90 : op === 'max' ? 60 : 30 };
}

export const modeLabel = (m: CommuteMode): string => t(m === 'ptst' ? 'pt.stS' : m === 'pt' ? 'common.pt' : 'common.car');

export interface CommuteValues {
  /** per unit of the level: minutes, null = no value */
  v: (number | null)[];
  status: 'ok' | 'loading' | 'inactive';
  note: string | null;
}

/** The measure's value per unit of the level (ids), for the units that have travel times. */
export function commuteValues(f: CommuteFilter, ids: string[], r: ReachTimes | null): CommuteValues {
  const none = (status: 'loading' | 'inactive', note: string | null): CommuteValues => ({ v: [], status, note });
  if (f.op === 'near') return none('inactive', null); // 'near' reads the nearest-hub metric column (filters.ts)
  if (!r) return none('loading', t('f.loading'));
  if (f.mode !== 'car' && !(f.mode === 'pt' ? r.pt : r.pt_station)) return none('inactive', t('cm.notBuild'));
  const known = new Set(commuteHubSlugs(r));
  const hubs = f.hubs;
  if (!hubs.length) return none('inactive', t(f.op === 'diff' ? 'cm.pickHub' : 'cm.pickHubs'));
  if (hubs.some((h) => !known.has(h))) return none('inactive', t('cm.unknownHub'));
  const idx = rtIndex(r);
  const main = series(r, f.mode) ?? {};
  const out: (number | null)[] = new Array(ids.length).fill(null);
  for (let i = 0; i < ids.length; i++) {
    const k = idx.get(ids[i]);
    if (k === undefined) continue;
    if (f.op === 'diff') {
      const a = main[hubs[0]]?.[k];
      const b = r.car[hubs[0]]?.[k];
      if (typeof a === 'number' && typeof b === 'number') out[i] = a - b;
      continue;
    }
    let sum = 0;
    let max = -Infinity;
    let min = Infinity;
    let miss = false;
    for (const h of hubs) {
      const x = main[h]?.[k];
      if (typeof x !== 'number') miss = true;
      else {
        sum += x;
        if (x > max) max = x;
        if (x < min) min = x;
      }
    }
    if (f.op === 'sum') out[i] = miss ? null : sum;
    else if (f.op === 'max') out[i] = miss ? null : max;
    else out[i] = min === Infinity ? null : min; // any / near: the best of the available times
  }
  return { v: out, status: 'ok', note: null };
}

const hubsText = (f: CommuteFilter, hubName: (slug: string) => string) => f.hubs.map(hubName).join(' + ') || '–';

/** Label of the measure ("Sum of times to Bern + Zürich HB, PT station"). */
export function commuteLabel(f: CommuteFilter, hubName: (slug: string) => string): string {
  return t(`cm.col.${f.op}`, { hubs: hubsText(f, hubName), mode: modeLabel(f.mode), hub: f.hubs[0] ? hubName(f.hubs[0]) : '–' });
}

/** One-line description of the condition for the exports and the filter summary. */
export function describeCommute(f: CommuteFilter, hubName: (slug: string) => string): string {
  const lo = f.lo === null ? '' : fmtNumber(f.lo, 0);
  const hi = f.hi === null ? '' : fmtNumber(f.hi, 0);
  const rng = f.lo !== null && f.hi !== null ? `${lo}–${hi} min` : f.lo !== null ? `≥ ${lo} min` : f.hi !== null ? `≤ ${hi} min` : t('f.any');
  return t(`cm.desc.${f.op}`, { hubs: hubsText(f, hubName), mode: modeLabel(f.mode), hub: f.hubs[0] ? hubName(f.hubs[0]) : '–', rng });
}

/** A metric description of the measure, so the ranking table can show it as a column. */
export function commuteMeta(f: CommuteFilter, hubName: (slug: string) => string): MetricMeta {
  const label = commuteLabel(f, hubName);
  return {
    id: `commute_${f.op}_${f.mode}_${f.hubs.join('_')}`,
    theme: 'Mobility & accessibility',
    label_en: label, label_de: label, label_fr: label,
    unit: 'min', unit_de: 'Min.', unit_fr: 'min',
    decimals: 0,
    direction: 'lower_better',
    aggregation: 'not_aggregatable',
    precision: 'modelled',
    coverage: 'national',
    source: 'reach_times',
    description: null,
    levels: ['gemeinde'],
    periods: [], n_periods: 1, latest: r2026(), headline: null, hidden: true, file: '',
  } as MetricMeta;
}
const r2026 = () => rt?.periods?.[rt?.pt_station ? 'pt_station' : 'pt'] ?? '';
