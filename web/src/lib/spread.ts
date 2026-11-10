// C1: travel-time spread over the morning (web data contract §8): P10 / median / P90 of the public-transport
// times, towards the hub and from the hub, as a journey planner shows them and including waiting.
// reach/spread.json (small: units, hubs, definitions) and reach/<hub>_spread.json (one hub, loaded on demand).
import { getOptionalJSON } from './data';

export type SpreadDir = 'to' | 'from';
export type SpreadKind = 'pt_station' | 'pt';
export type SpreadSeries = 'journey' | 'with_wait';
type Stats = Record<'p10' | 'p50' | 'p90', (number | null)[]>;
type Block = Record<SpreadKind, Record<SpreadSeries, Stats>>;

export interface SpreadIndex {
  units: string[];
  hubs: [string, string][];
  file: string;
  service_date?: string;
  /** {key: {en, de, fr}} for to, from, journey, with_wait, pt_station, pt */
  definitions: Record<string, Record<string, string>>;
}
export interface SpreadFile {
  hub: string;
  to: Block;
  from: Block;
  late_from?: Partial<Record<SpreadKind, Record<string, string>>>;
  reasons?: Partial<Record<SpreadDir, Partial<Record<SpreadKind, Record<string, string>>>>>;
}

/** One spread: the median and the 10–90 % range (minutes; null = no value / percentile undefined). */
export interface Spread {
  lo: number | null;
  mid: number | null;
  hi: number | null;
}

let indexP: Promise<SpreadIndex | null> | null = null;
let unitIndex: Map<string, number> | null = null;
export function loadSpreadIndex(): Promise<SpreadIndex | null> {
  if (!indexP) {
    indexP = getOptionalJSON<SpreadIndex>('reach/spread.json').then((ix) => {
      unitIndex = ix ? new Map(ix.units.map((u, k) => [u, k])) : null;
      return ix;
    });
    indexP.catch(() => (indexP = null));
  }
  return indexP;
}

const files = new Map<string, Promise<SpreadFile | null>>();
/** The spread file of one hub (null when this build has none). */
export function loadSpread(hub: string): Promise<SpreadFile | null> {
  let p = files.get(hub);
  if (!p) {
    p = loadSpreadIndex().then((ix) => (ix ? getOptionalJSON<SpreadFile>(`reach/${ix.file.replace('<hub>', hub)}`) : null));
    p.catch(() => files.delete(hub));
    files.set(hub, p);
  }
  return p;
}

/** Index of a municipality (BFS number) in the spread arrays, or -1. */
export function spreadIdx(ix: SpreadIndex, unit: string): number {
  if (!unitIndex || unitIndex.size !== ix.units.length) unitIndex = new Map(ix.units.map((u, k) => [u, k]));
  return unitIndex.get(unit) ?? -1;
}

/** The spread of one unit for a direction, measure and series (null: the file has no such block). */
export function spreadOf(f: SpreadFile, k: number, dir: SpreadDir, kind: SpreadKind, series: SpreadSeries): Spread | null {
  const s = f[dir]?.[kind]?.[series];
  if (!s || k < 0) return null;
  return { lo: s.p10[k] ?? null, mid: s.p50[k] ?? null, hi: s.p90[k] ?? null };
}

/** Why a unit has no median (the file's reasons), or null. */
export function spreadReason(f: SpreadFile, k: number, dir: SpreadDir, kind: SpreadKind): string | null {
  return f.reasons?.[dir]?.[kind]?.[String(k)] ?? null;
}

/** Towards the hub only: the value uses the hour from this earliest arrival ("08:55"), or null. */
export function spreadLate(f: SpreadFile, k: number, kind: SpreadKind): string | null {
  return f.late_from?.[kind]?.[String(k)] ?? null;
}

const m = (x: number) => String(Math.round(x));
/** "36 min (35–41)"; a range that does not vary is left out ("37 min"); an undefined end is "…". null = no median. */
export function fmtSpread(s: Spread | null, unit = 'min'): string | null {
  if (!s || s.mid === null) return null;
  const lo = s.lo === null ? '…' : m(s.lo);
  const hi = s.hi === null ? '…' : m(s.hi);
  const same = s.lo !== null && s.hi !== null && m(s.lo) === m(s.hi) && m(s.lo) === m(s.mid);
  return same ? `${m(s.mid)} ${unit}` : `${m(s.mid)} ${unit} (${lo}–${hi})`;
}

/** "39–62" (the range only, e.g. for the line "with waiting 39–62 min"); null when there is no median. */
export function fmtRange(s: Spread | null): string | null {
  if (!s || s.mid === null) return null;
  return `${s.lo === null ? '…' : m(s.lo)}–${s.hi === null ? '…' : m(s.hi)}`;
}

/** Definition text of a key in the UI language (English when missing). */
export function spreadDef(ix: SpreadIndex | null, key: string, lang: string): string {
  const d = ix?.definitions?.[key];
  return d ? (d[lang] ?? d.en ?? '') : '';
}
