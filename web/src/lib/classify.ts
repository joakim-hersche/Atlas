// Quantile classes, ranks and number formatting.
import type { MetricMeta } from './data';

export const N_CLASSES = 5;

export interface Classes {
  breaks: number[]; // ascending unique inner breaks
  min: number;
  max: number;
  n: number; // units with a value
  /** colour index 0..N_CLASSES-1 per unit, -1 = no value */
  colour: Int8Array;
  /** colour index per class (fewer classes when many values tie) */
  classColour: number[];
}

export function quantileClasses(v: (number | null)[]): Classes {
  const vals = v.filter((x): x is number => x !== null && Number.isFinite(x)).sort((a, b) => a - b);
  const colour = new Int8Array(v.length).fill(-1);
  if (!vals.length) return { breaks: [], min: NaN, max: NaN, n: 0, colour, classColour: [] };
  const raw: number[] = [];
  for (let k = 1; k < N_CLASSES; k++) {
    const pos = (vals.length - 1) * (k / N_CLASSES);
    const lo = Math.floor(pos);
    raw.push(vals[lo] + (vals[Math.min(lo + 1, vals.length - 1)] - vals[lo]) * (pos - lo));
  }
  const min = vals[0];
  const max = vals[vals.length - 1];
  const breaks = [...new Set(raw)].filter((b) => b > min && b <= max);
  const nCls = breaks.length + 1;
  const classColour = Array.from({ length: nCls }, (_, c) =>
    nCls === 1 ? Math.floor(N_CLASSES / 2) : Math.round((c * (N_CLASSES - 1)) / (nCls - 1)),
  );
  for (let i = 0; i < v.length; i++) {
    const x = v[i];
    if (x === null || !Number.isFinite(x)) continue;
    let c = 0;
    while (c < breaks.length && x >= breaks[c]) c++;
    colour[i] = classColour[c];
  }
  return { breaks, min, max, n: vals.length, colour, classColour };
}

/** Rank 1 = highest (or lowest for lower_better metrics); ties share the better rank. */
export function rankOf(v: (number | null)[], i: number, direction: MetricMeta['direction']): { rank: number; n: number } | null {
  const x = v[i];
  if (x === null) return null;
  let better = 0;
  let n = 0;
  const asc = direction === 'lower_better';
  for (const y of v) {
    if (y === null) continue;
    n++;
    if (asc ? y < x : y > x) better++;
  }
  return { rank: better + 1, n };
}

const fmtCache = new Map<number, Intl.NumberFormat>();
export function fmtNumber(x: number, decimals: number): string {
  const d = Math.max(0, Math.min(decimals, 4));
  let f = fmtCache.get(d);
  if (!f) {
    f = new Intl.NumberFormat('de-CH', { minimumFractionDigits: d, maximumFractionDigits: d });
    fmtCache.set(d, f);
  }
  return f.format(x);
}

export function fmtValue(x: number, meta: MetricMeta): string {
  const n = fmtNumber(x, meta.decimals);
  if (!meta.unit) return n;
  return meta.unit.startsWith('%') ? `${n}${meta.unit}` : `${n} ${meta.unit}`;
}

/** Shorter number for legend ticks: keeps the metric's decimals but abbreviates large values. */
export function fmtTick(x: number, meta: MetricMeta): string {
  const a = Math.abs(x);
  if (a >= 1e6) return `${fmtNumber(x / 1e6, 1)}M`;
  if (a >= 1e4) return `${fmtNumber(x / 1e3, 0)}k`;
  return fmtNumber(x, meta.decimals);
}

/** '2026-06-14#6870' (vote date and vote number) -> '2026-06-14, vote no. 6870' */
export function fmtPeriod(p: string): string {
  const [a, b] = p.split('#');
  return b ? `${a}, vote no. ${b}` : a;
}
