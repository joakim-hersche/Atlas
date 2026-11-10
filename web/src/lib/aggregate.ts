// Aggregate of a metric over a set of units (the filtered set), by the metric's aggregation rule
// from metrics.json (brief 4.2):
//   sum                       total of the values
//   ratio:A+B/C+D*K           (sum of A+B) / (sum of C+D) * K, recomputed from the summed parts
//   weighted_mean:W           sum(value * W) / sum(W)
//   not_aggregatable, pooled, change   no figure (stated, never averaged)
// Only units with every needed value take part; the result says how many that is.
import type { ColView } from './columns.svelte';
import type { MetricMeta } from './data';

export type AggKind = 'sum' | 'ratio' | 'wmean';

export type AggResult =
  | { status: 'loading' }
  | { status: 'na'; reason: 'notAgg' | 'pooled' | 'change' | 'unknown' | 'level' | 'noParts' | 'noData' }
  | {
      status: 'ok';
      kind: AggKind;
      value: number;
      /** units that contributed */
      n: number;
      /** units in the set */
      of: number;
      /** ids of the parts, for the rule text */
      num?: string;
      den?: string;
      weight?: string;
      /** periods of the parts when they differ from the metric's own period */
      periodNote?: string;
    };

export interface Rule {
  kind: 'sum' | 'ratio' | 'wmean' | 'notAgg' | 'pooled' | 'change' | 'unknown';
  num?: string[];
  den?: string[];
  scale?: number;
  weight?: string;
}

/** Parses `aggregation` of a metric. */
export function parseRule(a: string): Rule {
  if (a === 'sum') return { kind: 'sum' };
  if (a === 'not_aggregatable') return { kind: 'notAgg' };
  if (a.startsWith('pooled:')) return { kind: 'pooled' };
  if (a.startsWith('change:')) return { kind: 'change' };
  if (a.startsWith('weighted_mean:')) {
    const w = a.slice('weighted_mean:'.length);
    return /^[a-z0-9_]+$/i.test(w) ? { kind: 'wmean', weight: w } : { kind: 'unknown' };
  }
  if (a.startsWith('ratio:')) {
    const m = /^ratio:([a-z0-9_+]+)\/([a-z0-9_+]+?)(?:\*([0-9.]+))?$/i.exec(a);
    if (!m) return { kind: 'unknown' };
    return { kind: 'ratio', num: m[1].split('+'), den: m[2].split('+'), scale: m[3] ? Number(m[3]) : 1 };
  }
  return { kind: 'unknown' };
}

/** Columns the rule needs besides the metric itself (to ask the column store for them). */
export function partIds(meta: MetricMeta): string[] {
  const r = parseRule(meta.aggregation);
  if (r.kind === 'ratio') return [...r.num!, ...r.den!];
  if (r.kind === 'wmean') return [r.weight!];
  return [];
}

export function aggregate(
  meta: MetricMeta,
  /** the metric's own column at the current level: undefined = loading, null = not published here */
  own: ColView | null | undefined,
  getCol: (id: string) => ColView | null | undefined,
  /** 1 = unit is in the set; null = every unit */
  mask: Uint8Array | null,
  nUnits: number,
): AggResult {
  const rule = parseRule(meta.aggregation);
  if (rule.kind === 'notAgg' || rule.kind === 'pooled' || rule.kind === 'change' || rule.kind === 'unknown') {
    return { status: 'na', reason: rule.kind };
  }
  if (own === undefined) return { status: 'loading' };
  if (own === null) return { status: 'na', reason: 'level' };
  let inSet = 0;
  for (let i = 0; i < nUnits; i++) if (!mask || mask[i]) inSet++;
  if (!inSet) return { status: 'na', reason: 'noData' };

  if (rule.kind === 'sum') {
    let s = 0;
    let n = 0;
    for (let i = 0; i < nUnits; i++) {
      if (mask && !mask[i]) continue;
      const x = own.col.v[i];
      if (x === null || x === undefined) continue;
      s += x;
      n++;
    }
    return n ? { status: 'ok', kind: 'sum', value: s, n, of: inSet } : { status: 'na', reason: 'noData' };
  }

  if (rule.kind === 'wmean') {
    const w = getCol(rule.weight!);
    if (w === undefined) return { status: 'loading' };
    if (w === null) return { status: 'na', reason: 'noParts' };
    let sw = 0;
    let sx = 0;
    let n = 0;
    for (let i = 0; i < nUnits; i++) {
      if (mask && !mask[i]) continue;
      const x = own.col.v[i];
      const wi = w.col.v[i];
      if (x === null || x === undefined || wi === null || wi === undefined || !(wi > 0)) continue;
      sx += x * wi;
      sw += wi;
      n++;
    }
    if (!n) return { status: 'na', reason: 'noData' };
    const periodNote = w.col.period !== own.col.period ? `${rule.weight} ${w.col.period}` : undefined;
    return { status: 'ok', kind: 'wmean', value: sx / sw, n, of: inSet, weight: rule.weight, periodNote };
  }

  // ratio of sums
  const parts = [...rule.num!, ...rule.den!];
  const cols: ColView[] = [];
  for (const id of parts) {
    const c = getCol(id);
    if (c === undefined) return { status: 'loading' };
    if (c === null) return { status: 'na', reason: 'noParts' };
    cols.push(c);
  }
  const nn = rule.num!.length;
  let sn = 0;
  let sd = 0;
  let n = 0;
  for (let i = 0; i < nUnits; i++) {
    if (mask && !mask[i]) continue;
    let a = 0;
    let b = 0;
    let ok = true;
    for (let k = 0; k < cols.length; k++) {
      const x = cols[k].col.v[i];
      if (x === null || x === undefined) {
        ok = false;
        break;
      }
      if (k < nn) a += x;
      else b += x;
    }
    if (!ok) continue;
    sn += a;
    sd += b;
    n++;
  }
  if (!n || !(sd > 0)) return { status: 'na', reason: 'noData' };
  const odd = [...new Set(cols.filter((c) => c.col.period !== own.col.period).map((c, _k, _a) => c.col.period))];
  return {
    status: 'ok',
    kind: 'ratio',
    value: (sn / sd) * (rule.scale ?? 1),
    n,
    of: inSet,
    num: rule.num!.join(' + '),
    den: rule.den!.join(' + '),
    periodNote: odd.length ? odd.join(', ') : undefined,
  };
}
