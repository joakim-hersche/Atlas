// Public-transport travel times (D31): the headline is the timetable time from the municipality's main
// station towards the hub ("Winterthur → Zürich HB 22 min by train, from Winterthur station"); the second
// line is door to door, also towards the hub. Builds without the station metrics (before the D31 data)
// keep the earlier door-to-door figure, measured from the hub outwards, with its own method text.
import type { MetricMeta } from './data';
import { app } from './state.svelte';
import { t } from './i18n.svelte';
import type { ReachTimes } from './places';

/** 'ptst' station time, 'pt' door to door, 'car' */
export type ReachKind = 'ptst' | 'pt' | 'car';

export const reachId = (kind: ReachKind, hub: string) => `reach_${kind}_${hub}`;

/** true when this build has the D31 station times */
export const hasStation = (metas: Map<string, MetricMeta>) => metas.has('reach_ptst_nearest_hub') || [...metas.keys()].some((k) => k.startsWith('reach_ptst_'));

/** The measure used on the map for public transport: station time when available and chosen. */
export function ptKind(metas: Map<string, MetricMeta>): 'ptst' | 'pt' {
  return app.ptm === 'dd' || !hasStation(metas) ? 'pt' : 'ptst';
}

/** One-line method text: the pipeline's text in the UI language when shipped, else ours. */
export function methodText(kind: ReachKind, hub: string, rt: ReachTimes | null, station: boolean): string {
  const key = kind === 'ptst' ? 'pt_station' : kind;
  // the pipeline's text in the UI language; otherwise our own translation (not the English text)
  const shipped = rt?.methods?.[key]?.[app.lang];
  if (shipped) return shipped;
  if (kind === 'car') return t('pt.m.car');
  if (kind === 'ptst') return t('pt.m.st', { hub });
  return t(station ? 'pt.m.dd' : 'pt.m.ddOld', { hub });
}

/** Main station of a municipality (reach_times.json): its name, and whether it lies outside the
 *  municipality (no stop inside: the nearest one is used). null when unknown. */
export function mainStation(rt: ReachTimes | null, unitId: string, index?: Map<string, number>): { name: string; outside: boolean; mode: string | null } | null {
  if (!rt?.main_station) return null;
  const k = index ? index.get(unitId) : rt.units.indexOf(unitId);
  if (k === undefined || k < 0) return null;
  const s = rt.main_station[k];
  if (!s) return null;
  // a stop that is not a rail station is named with its mode: "Weggis, Dorfplatz (bus)"
  const mode = s[3] && s[3] !== 'rail' ? (rt.mode_text?.[s[3]]?.[app.lang] ?? s[3]) : null;
  return { name: mode ? `${s[0]} (${mode})` : s[0], outside: s[2] === false, mode };
}

/** Name of the nearest hub (D39 set) for a nearest-hub metric id, or null. */
export function nearestHubOf(rt: ReachTimes | null, metricId: string, unitId: string, index?: Map<string, number>): string | null {
  const m = /^reach_(ptst|pt|car)_nearest_hub$/.exec(metricId);
  if (!m || !rt?.nearest) return null;
  const key = m[1] === 'ptst' ? 'pt_station' : m[1];
  const k = index ? index.get(unitId) : rt.units.indexOf(unitId);
  return k === undefined || k < 0 ? null : (rt.nearest[key]?.[k] ?? null);
}

/** The rule for which hubs count as "nearest hub", in the UI language. */
export const nearestRule = (rt: ReachTimes | null): string | null => rt?.nearest_rule?.[app.lang] ?? rt?.nearest_rule?.en ?? null;

/** How a municipality's time to a hub was obtained, when it is special (reach_times.json notes), or null. */
export function reachNote(rt: ReachTimes | null, kind: ReachKind, hub: string, unitId: string, index?: Map<string, number>): string | null {
  const key = kind === 'ptst' ? 'pt_station' : kind;
  const n = rt?.notes?.[key]?.[hub];
  if (!n) return null;
  const k = index ? index.get(unitId) : rt!.units.indexOf(unitId);
  return k === undefined || k < 0 ? null : (n[String(k)] ?? null);
}

/** Why a municipality has no time for a measure (reach_times.json reasons), or null. */
export function reachReason(rt: ReachTimes | null, kind: ReachKind, hub: string, unitId: string, index?: Map<string, number>): string | null {
  const k = index ? index.get(unitId) : rt?.units.indexOf(unitId);
  if (!rt || k === undefined || k < 0) return null;
  return reasonAt(rt, kind === 'ptst' ? 'pt_station' : kind, hub, k);
}

/** reasons[key][hub][idx] (per hub); older builds wrote reasons[key][idx]. */
export function reasonAt(rt: ReachTimes, key: string, hub: string, k: number): string | null {
  const r = rt.reasons?.[key];
  if (!r) return null;
  const h = r[hub];
  if (h && typeof h === 'object') return h[String(k)] ?? null;
  const flat = r[String(k)];
  return typeof flat === 'string' ? flat : null;
}

/** Label of a reach measure ('long' for headings, else short for buttons). Without station times in the
 *  build, 'pt' is plain "PT". */
export function kindLabel(kind: ReachKind, station: boolean, long = false): string {
  if (kind === 'car') return t('common.car');
  if (kind === 'ptst') return t(long ? 'pt.st' : 'pt.stS');
  return station ? t(long ? 'pt.dd' : 'pt.ddS') : t(long ? 'rc.pt' : 'common.pt');
}
