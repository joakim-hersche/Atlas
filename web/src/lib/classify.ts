// Classification (quantiles / equal interval / continuous, sequential or diverging), summary
// statistics, correlation and number formatting.
import type { MetricMeta } from './data';
import { interpolate } from './theme';

export const N_CLASSES = 5;
export type Method = 'quantile' | 'equal' | 'continuous';
export const METHOD_LABEL: Record<Method, string> = { quantile: 'Quantiles', equal: 'Equal interval', continuous: 'Continuous' };

export interface Scale {
  method: Method;
  diverging: boolean;
  /** ascending inner class breaks (empty for continuous) */
  breaks: number[];
  /** colour per class (breaks.length + 1 entries; empty for continuous) */
  classColours: string[];
  /** number of units per class */
  counts: number[];
  /** continuous domain (clamped) */
  lo: number;
  hi: number;
  min: number;
  max: number;
  n: number;
  colourOf: (x: number) => string;
  /** colour per unit, null = no value */
  unitColour: (string | null)[];
}

/** Values sorted ascending, without gaps. */
export function sortedValues(v: (number | null)[]): number[] {
  return v.filter((x): x is number => x !== null && Number.isFinite(x)).sort((a, b) => a - b);
}

/** Linear-interpolated quantile of an ascending array (p in 0..1). */
export function quantile(s: number[], p: number): number {
  if (!s.length) return NaN;
  const pos = (s.length - 1) * p;
  const lo = Math.floor(pos);
  return s[lo] + (s[Math.min(lo + 1, s.length - 1)] - s[lo]) * (pos - lo);
}

/** Change metrics and neutral metrics with negative values get a diverging scale centred on 0. */
export function isDiverging(meta: MetricMeta & { aggregation?: string }, s: number[]): boolean {
  if ((meta.aggregation ?? '').startsWith('change:')) return true;
  if (/(^|_)change(_\d+y)?$/.test(meta.id) && meta.unit.startsWith('%')) return true;
  return meta.direction === 'neutral' && s.length > 0 && s[0] < 0 && s[s.length - 1] > 0;
}

function spread(nCls: number, ramp: string[]): string[] {
  return Array.from({ length: nCls }, (_, c) =>
    ramp[nCls === 1 ? Math.floor(ramp.length / 2) : Math.round((c * (ramp.length - 1)) / (nCls - 1))],
  );
}

function classIndex(x: number, breaks: number[]): number {
  let c = 0;
  while (c < breaks.length && x >= breaks[c]) c++;
  return c;
}

export function buildScale(v: (number | null)[], method: Method, diverging: boolean, seq: string[], div: string[]): Scale {
  const s = sortedValues(v);
  const n = s.length;
  const min = s[0];
  const max = s[n - 1];
  let breaks: number[] = [];
  let classColours: string[] = [];
  let lo = min;
  let hi = max;
  let colourOf: (x: number) => string;

  if (method === 'continuous') {
    if (diverging) {
      const M = Math.max(Math.abs(quantile(s, 0.02)), Math.abs(quantile(s, 0.98))) || Math.max(Math.abs(min), Math.abs(max)) || 1;
      lo = -M;
      hi = M;
      colourOf = (x) => interpolate(div, 0.5 + x / (2 * M));
    } else {
      lo = quantile(s, 0.02);
      hi = quantile(s, 0.98);
      if (!(hi > lo)) {
        lo = min;
        hi = max > min ? max : min + 1;
      }
      colourOf = (x) => interpolate(seq, (x - lo) / (hi - lo));
    }
  } else {
    if (method === 'quantile') {
      const raw: number[] = [];
      for (let k = 1; k < N_CLASSES; k++) raw.push(quantile(s, k / N_CLASSES));
      if (diverging && min < 0 && max > 0) raw.push(0);
      breaks = [...new Set(raw)].filter((b) => b > min && b <= max).sort((a, b) => a - b);
    } else if (diverging) {
      const M = Math.max(Math.abs(min), Math.abs(max)) || 1;
      lo = -M;
      hi = M;
      breaks = [-0.6 * M, -0.2 * M, 0.2 * M, 0.6 * M].filter((b) => b > min && b <= max);
    } else {
      const w = (max - min) / N_CLASSES;
      breaks = w > 0 ? Array.from({ length: N_CLASSES - 1 }, (_, k) => min + w * (k + 1)) : [];
    }
    const nCls = breaks.length + 1;
    if (!diverging) {
      classColours = spread(nCls, seq);
    } else if (method === 'equal') {
      // fixed symmetric classes: strong –, moderate –, around 0, moderate +, strong +
      const idx = [0, 1, 3, 5, 6];
      const M = hi;
      const edges = [-Infinity, -0.6 * M, -0.2 * M, 0.2 * M, 0.6 * M, Infinity];
      classColours = Array.from({ length: nCls }, (_, c) => {
        const a = c === 0 ? min : breaks[c - 1];
        return div[idx[Math.min(4, classIndex(a, edges.slice(1, 5)))]];
      });
    } else {
      // classes below 0 take the orange arm, above 0 the blue arm, graded outward from 0
      const lowerOf = (c: number) => (c === 0 ? min : breaks[c - 1]);
      const upperOf = (c: number) => (c === nCls - 1 ? max : breaks[c]);
      const neg: number[] = [];
      const pos: number[] = [];
      for (let c = 0; c < nCls; c++) (upperOf(c) <= 0 && lowerOf(c) < 0 ? neg : pos).push(c);
      classColours = new Array(nCls);
      const grade = (k: number, len: number) => (len === 1 ? 2 : 1 + Math.round((k * 2) / (len - 1)));
      // neg is ascending (most negative first): the class next to 0 is the last one
      neg.forEach((c, j) => (classColours[c] = div[3 - grade(neg.length - 1 - j, neg.length)]));
      pos.forEach((c, j) => (classColours[c] = lowerOf(c) === 0 && upperOf(c) === 0 ? div[3] : div[3 + grade(j, pos.length)]));
    }
    colourOf = (x) => classColours[classIndex(x, breaks)];
  }

  const counts = new Array(Math.max(1, breaks.length + 1)).fill(0);
  const unitColour: (string | null)[] = new Array(v.length).fill(null);
  for (let i = 0; i < v.length; i++) {
    const x = v[i];
    if (x === null || !Number.isFinite(x)) continue;
    unitColour[i] = colourOf(x);
    counts[method === 'continuous' ? 0 : classIndex(x, breaks)]++;
  }
  return { method, diverging, breaks, classColours, counts, lo, hi, min, max, n, colourOf, unitColour };
}

// ---------------------------------------------------------------- distribution axis
/** Heavily right-skewed positive metrics (population, density) are shown on a log axis. */
export function wantsLog(s: number[]): boolean {
  if (!s.length || s[0] <= 0) return false;
  return quantile(s, 0.98) / quantile(s, 0.5) > 6;
}

/** Axis domain: min..max, unless a tail is far out; then P1/P99 and the tail is folded into the end bin. */
export function axisDomain(s: number[], log: boolean): { lo: number; hi: number; clipLo: boolean; clipHi: boolean } {
  const f = log ? Math.log10 : (x: number) => x;
  const g = log ? (x: number) => 10 ** x : (x: number) => x;
  const min = f(s[0]);
  const max = f(s[s.length - 1]);
  const p1 = f(quantile(s, 0.01));
  const p99 = f(quantile(s, 0.99));
  const iqr = p99 - p1 || 1;
  const clipLo = p1 - min > 0.3 * iqr;
  const clipHi = max - p99 > 0.3 * iqr;
  return { lo: g(clipLo ? p1 : min), hi: g(clipHi ? p99 : max), clipLo, clipHi };
}

// ---------------------------------------------------------------- statistics
export function mean(s: number[]): number {
  let t = 0;
  for (const x of s) t += x;
  return t / s.length;
}

export function ranks(x: number[]): Float64Array {
  const idx = Array.from(x.keys()).sort((a, b) => x[a] - x[b]);
  const r = new Float64Array(x.length);
  for (let k = 0; k < idx.length; ) {
    let j = k;
    while (j + 1 < idx.length && x[idx[j + 1]] === x[idx[k]]) j++;
    const avg = (k + j) / 2 + 1;
    for (let q = k; q <= j; q++) r[idx[q]] = avg;
    k = j + 1;
  }
  return r;
}

export interface Fit {
  r: number;
  slope: number;
  intercept: number;
}

/** (Weighted) Pearson correlation and least-squares line y = a + b x. */
export function pearson(x: ArrayLike<number>, y: ArrayLike<number>, w?: ArrayLike<number>): Fit {
  let sw = 0, mx = 0, my = 0;
  for (let i = 0; i < x.length; i++) {
    const wi = w ? w[i] : 1;
    sw += wi;
    mx += wi * x[i];
    my += wi * y[i];
  }
  mx /= sw;
  my /= sw;
  let sxx = 0, syy = 0, sxy = 0;
  for (let i = 0; i < x.length; i++) {
    const wi = w ? w[i] : 1;
    const dx = x[i] - mx;
    const dy = y[i] - my;
    sxx += wi * dx * dx;
    syy += wi * dy * dy;
    sxy += wi * dx * dy;
  }
  const slope = sxx > 0 ? sxy / sxx : NaN;
  return { r: sxx > 0 && syy > 0 ? sxy / Math.sqrt(sxx * syy) : NaN, slope, intercept: my - slope * mx };
}

export function spearman(x: number[], y: number[]): number {
  return pearson(ranks(x), ranks(y)).r;
}

/** Rank 1 = highest (or lowest for lower_better metrics); ties share the better rank. */
export function rankOf(v: (number | null)[], i: number, direction: MetricMeta['direction']): { rank: number; n: number; pct: number } | null {
  const x = v[i];
  if (x === null) return null;
  let better = 0, below = 0, equal = 0, n = 0;
  const asc = direction === 'lower_better';
  for (const y of v) {
    if (y === null) continue;
    n++;
    if (asc ? y < x : y > x) better++;
    if (y < x) below++;
    else if (y === x) equal++;
  }
  return { rank: better + 1, n, pct: (100 * (below + 0.5 * equal)) / n };
}

// ---------------------------------------------------------------- ticks
export function niceStep(span: number, target: number): number {
  const raw = span / Math.max(1, target);
  const p = 10 ** Math.floor(Math.log10(raw));
  const m = raw / p;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
}

export function niceTicks(lo: number, hi: number, target = 5): number[] {
  if (!(hi > lo)) return [lo];
  const st = niceStep(hi - lo, target);
  const out: number[] = [];
  for (let t = Math.ceil(lo / st) * st; t <= hi + st * 1e-9; t += st) out.push(Math.abs(t) < st * 1e-9 ? 0 : +t.toPrecision(12));
  return out;
}

/** Ticks for a log10 axis: 1, 2, 5 × powers of ten inside [lo, hi] (thinned when crowded). */
export function logTicks(lo: number, hi: number, target = 6): number[] {
  const out: number[] = [];
  for (let e = Math.floor(Math.log10(lo)); e <= Math.ceil(Math.log10(hi)); e++)
    for (const m of [1, 2, 5]) {
      const t = m * 10 ** e;
      if (t >= lo * 0.999 && t <= hi * 1.001) out.push(t);
    }
  if (out.length > target) return out.filter((t) => Math.abs(Math.log10(t) - Math.round(Math.log10(t))) < 1e-9);
  return out;
}

// ---------------------------------------------------------------- formatting
const fmtCache = new Map<number, Intl.NumberFormat>();
export function fmtNumber(x: number, decimals: number): string {
  const d = Math.max(0, Math.min(decimals, 4));
  let f = fmtCache.get(d);
  if (!f) {
    f = new Intl.NumberFormat('de-CH', { minimumFractionDigits: d, maximumFractionDigits: d });
    fmtCache.set(d, f);
  }
  return f.format(x).replace('-', '−');
}

export function unitSuffix(meta: MetricMeta): string {
  if (!meta.unit) return '';
  return meta.unit.startsWith('%') ? meta.unit : ` ${meta.unit}`;
}

export function fmtValue(x: number, meta: MetricMeta): string {
  return fmtNumber(x, meta.decimals) + unitSuffix(meta);
}

/** Short axis/legend label: abbreviates large values, otherwise the metric's decimals (at most 1 extra). */
export function fmtTick(x: number, meta: MetricMeta | { decimals: number }): string {
  const a = Math.abs(x);
  if (a >= 1e6) return `${fmtNumber(x / 1e6, a >= 1e7 ? 0 : 1)}M`;
  if (a >= 1e4) return `${fmtNumber(x / 1e3, 0)}k`;
  if (a >= 1000) return fmtNumber(x, 0);
  const d = Math.max(meta.decimals, 0);
  const r = +x.toFixed(d);
  return fmtNumber(r, Number.isInteger(r) ? 0 : d);
}

/** '2026-06-14#6870' (vote date and vote number) -> '2026-06-14, vote no. 6870' */
export function fmtPeriod(p: string): string {
  const [a, b] = p.split('#');
  return b ? `${a}, vote no. ${b}` : a;
}

export function fmtR(r: number): string {
  return Number.isFinite(r) ? (r < 0 ? '−' : '') + Math.abs(r).toFixed(2) : '–';
}
