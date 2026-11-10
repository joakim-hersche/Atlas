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
  const shipped = rt?.methods?.[key]?.[app.lang] ?? (app.lang === 'en' ? null : rt?.methods?.[key]?.en);
  if (shipped) return shipped;
  if (kind === 'car') return t('pt.m.car');
  if (kind === 'ptst') return t('pt.m.st', { hub });
  return t(station ? 'pt.m.dd' : 'pt.m.ddOld', { hub });
}

/** Main station name of a municipality (reach_times.json), or null. */
export function mainStation(rt: ReachTimes | null, unitId: string, index?: Map<string, number>): string | null {
  if (!rt?.main_station) return null;
  const k = index ? index.get(unitId) : rt.units.indexOf(unitId);
  if (k === undefined || k < 0) return null;
  return rt.main_station[k]?.[0] ?? null;
}

/** Why a municipality has no time for a measure (reach_times.json reasons), or null. */
export function reachReason(rt: ReachTimes | null, kind: ReachKind, unitId: string, index?: Map<string, number>): string | null {
  const key = kind === 'ptst' ? 'pt_station' : kind;
  const r = rt?.reasons?.[key];
  if (!r) return null;
  const k = index ? index.get(unitId) : rt!.units.indexOf(unitId);
  return k === undefined || k < 0 ? null : (r[String(k)] ?? null);
}

/** Label of a reach measure ('long' for headings, else short for buttons). Without station times in the
 *  build, 'pt' is plain "PT". */
export function kindLabel(kind: ReachKind, station: boolean, long = false): string {
  if (kind === 'car') return t('common.car');
  if (kind === 'ptst') return t(long ? 'pt.st' : 'pt.stS');
  return station ? t(long ? 'pt.dd' : 'pt.ddS') : t(long ? 'rc.pt' : 'common.pt');
}
