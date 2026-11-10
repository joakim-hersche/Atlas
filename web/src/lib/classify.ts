// Classification (quantiles / equal interval / continuous, sequential or diverging), summary
// statistics, correlation and number formatting.
import type { MetricMeta } from './data';
import { SvelteMap } from 'svelte/reactivity';
import { app } from './state.svelte';
import { interpolate } from './theme';

export const N_CLASSES = 5;
export type Method = 'quantile' | 'equal' | 'continuous';
export const METHOD_LABEL: Record<Method, string> = { quantile: 'Quantiles', equal: 'Equal interval', continuous: 'Continuous' };

export interface Scale {
  method: Method;
  diverging: boolean;
  /** fixed classes around a meaningful midpoint (yes share: <35, 35–45, 45–50 | 50–55, 55–65, >65) */
  fixed?: boolean;
  /** midpoint of a diverging scale (0 for changes, 50 for yes shares) */
  centre: number;
  /** ascending inner class breaks (empty for continuous) */
  breaks: number[];
  /** colour per class (breaks.length + 1 entries; empty for continuous) */
  classColours: string[];
  /** number of units per class */
  counts: number[];
  /** smallest and largest value in each class (Infinity / -Infinity for an empty class) */
  classMin: number[];
  classMax: number[];
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

/** Metrics with a meaningful 50 % midpoint: vote yes share (D32), political leaning (D37). */
export const CENTRED_50 = new Set(['vote_yes_share', 'nrw_leaning']);
/** Midpoint of a diverging scale: 50 % for vote yes shares (D32) and political leaning (D37), else 0. */
export function divergeCentre(meta: { id: string }): number {
  return CENTRED_50.has(meta.id) ? 50 : 0;
}

/** Change metrics, neutral metrics with negative values and vote yes shares get a diverging scale. */
export function isDiverging(meta: MetricMeta & { aggregation?: string }, s: number[]): boolean {
  if ((meta.aggregation ?? '').startsWith('change:')) return true;
  if (CENTRED_50.has(meta.id)) return true;
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

export function buildScale(v: (number | null)[], method: Method, diverging: boolean, seq: string[], div: string[], centre = 0): Scale {
  const c0 = centre;
  const s = sortedValues(v);
  const n = s.length;
  const min = s[0];
  const max = s[n - 1];
  let breaks: number[] = [];
  let classColours: string[] = [];
  let lo = min;
  let hi = max;
  let colourOf: (x: number) => string;
  let fixed = false;

  if (method !== 'continuous' && diverging && c0 !== 0) {
    // A share with a meaningful midpoint (vote yes share: 50 %): fixed classes, the same for every vote,
    // so the colour always says which side won and by how much: three shades of orange below the
    // midpoint, three of blue above (no neutral class: 50 % is a yes/no boundary, not a category).
    fixed = true;
    breaks = [c0 - 15, c0 - 5, c0, c0 + 5, c0 + 15];
    classColours = [div[0], div[1], div[2], div[4], div[5], div[6]];
    colourOf = (x) => classColours[classIndex(x, breaks)];
  } else if (method === 'continuous') {
    if (diverging) {
      const M = Math.max(Math.abs(quantile(s, 0.02) - c0), Math.abs(quantile(s, 0.98) - c0)) || Math.max(Math.abs(min - c0), Math.abs(max - c0)) || 1;
      lo = c0 - M;
      hi = c0 + M;
      colourOf = (x) => interpolate(div, 0.5 + (x - c0) / (2 * M));
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
    if (method === 'quantile' && diverging && c0 !== 0 && min < c0 && max > c0) {
      // a scale centred on a meaningful midpoint (yes share: 50 %): three classes on each side, with
      // breaks at the terciles of the distance from the midpoint, so yes and no majorities are never mixed
      const dist = s.map((x) => Math.abs(x - c0)).sort((a, b) => a - b);
      const d1 = +quantile(dist, 1 / 3).toPrecision(3);
      const d2 = +quantile(dist, 2 / 3).toPrecision(3);
      breaks = [...new Set([c0 - d2, c0 - d1, c0, c0 + d1, c0 + d2])].filter((b) => b > min && b <= max).sort((a, b) => a - b);
    } else if (method === 'quantile') {
      // A value shared by a large block of units at either end (0 % lake share, 0 births) gets a class
      // of its own; the other units are split into quantiles. Without this the ties swallow the breaks
      // and the map collapses to one or two classes.
      let lo0 = 0;
      let hi0 = n;
      const raw: number[] = [];
      let nq = N_CLASSES;
      const block = n / N_CLASSES;
      let k0 = 0;
      while (k0 < n && s[k0] === min) k0++;
      if (k0 >= block && k0 < n) {
        raw.push(s[k0]); // first value above the tied minimum
        lo0 = k0;
        nq--;
      }
      let k1 = n;
      while (k1 > lo0 && s[k1 - 1] === max) k1--;
      if (n - k1 >= block && k1 > lo0) {
        raw.push(max);
        hi0 = k1;
        nq--;
      }
      const rest = s.slice(lo0, hi0);
      for (let k = 1; k < nq; k++) raw.push(quantile(rest, k / nq));
      if (diverging && min < c0 && max > c0) raw.push(c0);
      breaks = [...new Set(raw)].filter((b) => b > min && b <= max).sort((a, b) => a - b);
    } else if (diverging) {
      const M = Math.max(Math.abs(min - c0), Math.abs(max - c0)) || 1;
      lo = c0 - M;
      hi = c0 + M;
      breaks = [-0.6 * M, -0.2 * M, 0.2 * M, 0.6 * M].map((b) => c0 + b).filter((b) => b > min && b <= max);
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
      const M = hi - c0;
      const edges = [-Infinity, c0 - 0.6 * M, c0 - 0.2 * M, c0 + 0.2 * M, c0 + 0.6 * M, Infinity];
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
      for (let c = 0; c < nCls; c++) (upperOf(c) <= c0 && lowerOf(c) < c0 ? neg : pos).push(c);
      classColours = new Array(nCls);
      const grade = (k: number, len: number) => (len === 1 ? 2 : 1 + Math.round((k * 2) / (len - 1)));
      // neg is ascending (most negative first): the class next to 0 is the last one
      neg.forEach((c, j) => (classColours[c] = div[3 - grade(neg.length - 1 - j, neg.length)]));
      pos.forEach((c, j) => (classColours[c] = lowerOf(c) === c0 && upperOf(c) === c0 ? div[3] : div[3 + grade(j, pos.length)]));
    }
    colourOf = (x) => classColours[classIndex(x, breaks)];
  }

  const nc = Math.max(1, breaks.length + 1);
  const counts = new Array(nc).fill(0);
  const classMin = new Array(nc).fill(Infinity);
  const classMax = new Array(nc).fill(-Infinity);
  const unitColour: (string | null)[] = new Array(v.length).fill(null);
  for (let i = 0; i < v.length; i++) {
    const x = v[i];
    if (x === null || !Number.isFinite(x)) continue;
    unitColour[i] = colourOf(x);
    const c = method === 'continuous' ? 0 : classIndex(x, breaks);
    counts[c]++;
    if (x < classMin[c]) classMin[c] = x;
    if (x > classMax[c]) classMax[c] = x;
  }
  return { method, diverging, fixed, centre: c0, breaks, classColours, counts, classMin, classMax, lo, hi, min, max, n, colourOf, unitColour };
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

export interface RankInfo {
  /** 1 = highest (lowest for lower_better metrics); tied values share the best rank of their group */
  rank: number;
  /** worst rank of the tie group (= rank when the value is not tied) */
  rankTo: number;
  /** units with a value */
  n: number;
  /** other units with exactly the same value */
  tied: number;
  /** percentile of the value (0 = lowest value, 100 = highest), at the same position as `rank` */
  pct: number;
  /** percentiles of the lowest and highest position of the tie group (both = pct when not tied) */
  pctLo: number;
  pctHi: number;
}

/** Rank and percentile by one rule: a tie group takes its best position for both, and the spread of
 *  the group (rankTo, pctFrom) and its size are returned so the UI can say "tied". */
export function rankOf(v: (number | null)[], i: number, direction: MetricMeta['direction']): RankInfo | null {
  const x = v[i];
  if (x === null || x === undefined) return null;
  let above = 0, below = 0, equal = 0;
  for (const y of v) {
    if (y === null || y === undefined) continue;
    if (y > x) above++;
    else if (y < x) below++;
    else equal++;
  }
  const n = above + below + equal;
  const asc = direction === 'lower_better';
  const better = asc ? below : above;
  const rank = better + 1;
  const rankTo = better + equal;
  // value percentile of a position k (0-based from the lowest value): 100 k / (n - 1)
  const pctAt = (k: number) => (n > 1 ? (100 * k) / (n - 1) : 50);
  // the best position of the group: its top for higher-is-better ranks, its bottom for lower-is-better
  const pct = asc ? pctAt(below) : pctAt(below + equal - 1);
  return { rank, rankTo, n, tied: equal - 1, pct, pctLo: pctAt(below), pctHi: pctAt(below + equal - 1) };
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

/** Ticks for a log10 axis: powers of ten, or 1, 2, 5 × 10^k, or 1…9 × 10^k, whichever is the densest
 *  set that stays within `target`; at least two ticks (a narrow range falls back to linear ticks). */
export function logTicks(lo: number, hi: number, target = 6): number[] {
  if (!(lo > 0) || !(hi > lo)) return lo > 0 ? [lo] : [];
  const sets = [[1], [1, 2, 5], [1, 2, 3, 4, 5, 6, 7, 8, 9]];
  const gen = (ms: number[]) => {
    const out: number[] = [];
    for (let e = Math.floor(Math.log10(lo)); e <= Math.ceil(Math.log10(hi)); e++)
      for (const m of ms) {
        const t = +(m * 10 ** e).toPrecision(12);
        if (t >= lo * 0.999 && t <= hi * 1.001) out.push(t);
      }
    return out;
  };
  const cands = sets.map(gen);
  let best: number[] | null = null;
  for (const c of cands) if (c.length >= 2 && c.length <= Math.max(2, target)) best = c;
  if (best) return best;
  // too many even for powers of ten: thin them; too few even for 1…9: linear ticks inside the range
  if (cands[0].length > target) {
    const step = Math.ceil(cands[0].length / target);
    return cands[0].filter((_, k) => k % step === 0);
  }
  return niceTicks(lo, hi, 3).filter((t) => t > 0);
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
  return f.format(x).replace(/['\u2019\u00a0\u202f]/g, '\u2019').replace('-', '−');
}

/** The metric's unit in the UI language (unit_de / unit_fr when shipped; English otherwise). */
export function unitOf(meta: Pick<MetricMeta, 'unit'> & { unit_de?: string | null; unit_fr?: string | null }): string {
  if (app.lang === 'de' && meta.unit_de) return meta.unit_de;
  if (app.lang === 'fr' && meta.unit_fr) return meta.unit_fr;
  return meta.unit;
}

export function unitSuffix(meta: MetricMeta): string {
  if (!meta.unit) return '';
  const u = unitOf(meta);
  return meta.unit.startsWith('%') ? u : ` ${u}`;
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

/** Titles of federal votes by period ('2026-06-14#6870'), per language; filled from metrics.json
 *  (latest_title) and the vote index. Reactive: labels update when the index arrives. */
export const periodTitles = new SvelteMap<string, Record<string, string>>();
export function voteTitle(p: string): string | null {
  const t = periodTitles.get(p);
  if (!t) return null;
  return t[app.lang] ?? t.en ?? t.de ?? t.fr ?? Object.values(t)[0] ?? null;
}
/** '2026-06-14#6870' (vote date and vote number) -> '2026-06-14' (no internal vote number in the UI);
 *  `withTitle` appends the vote's title where there is room for it (exports). */
export function fmtPeriod(p: string, withTitle = false): string {
  const [a, b] = p.split('#');
  if (!b) return a;
  const title = withTitle ? voteTitle(p) : null;
  return title ? `${a} · ${title}` : a;
}

export function fmtR(r: number): string {
  return Number.isFinite(r) ? (r < 0 ? '−' : '') + Math.abs(r).toFixed(2) : '–';
}

/** Round to `sig` significant digits for display. */
export function fmtSig(x: number, sig = 3): string {
  if (!Number.isFinite(x)) return '–';
  if (x === 0) return '0';
  const d = Math.max(0, sig - 1 - Math.floor(Math.log10(Math.abs(x))));
  return fmtNumber(x, Math.min(d, 4));
}

export interface SlopeText {
  /** 'lin' value per step of A; 'tenfold' value per tenfold A; 'pct' % change of B per step; 'elast' elasticity */
  kind: 'lin' | 'tenfold' | 'pct' | 'elast';
  value: string;
  step: string;
}
/** The least-squares slope in words-ready parts: a power-of-ten step of A chosen so the change in B has
 *  1–3 significant digits ("+5.94 per 10'000 CHF"), on log axes per tenfold A or as % change of B. */
export function slopeParts(b: number, logX: boolean, logY: boolean, maxStep = Infinity): SlopeText | null {
  if (!Number.isFinite(b)) return null;
  const sign = (v: number) => (v > 0 ? '+' : '') + fmtSig(v);
  const stepFor = (a: number) => Math.min(maxStep, a === 0 || Math.abs(a) >= 1 ? 1 : 10 ** Math.ceil(-Math.log10(Math.abs(a))));
  if (logX && logY) return { kind: 'elast', value: fmtSig(b), step: '' };
  if (logX) return { kind: 'tenfold', value: sign(b), step: '' };
  if (logY) {
    // B multiplies by 10^(b·step) per step of A: shown as a % change
    const st = stepFor(b * Math.LN10);
    return { kind: 'pct', value: sign((10 ** (b * st) - 1) * 100), step: fmtNumber(st, 0) };
  }
  const st = stepFor(b);
  return { kind: 'lin', value: sign(b * st), step: fmtNumber(st, 0) };
}

/** Class swatches and range labels of a classed scale (as in the legend), for exports. */
export function legendItems(scale: Scale, meta: MetricMeta | { decimals: number }): { colour: string; label: string }[] {
  if (scale.method === 'continuous') return [];
  if (scale.fixed) return fixedLabels(scale, meta);
  const out = scale.classColours.map((c, k) => {
    const lo = k === 0 ? scale.min : scale.breaks[k - 1];
    const hi = k === scale.breaks.length ? scale.max : scale.breaks[k];
    const single = scale.counts[k] > 0 && scale.classMin[k] === scale.classMax[k] ? scale.classMin[k] : null;
    return { colour: c, lo, hi, single };
  });
  return out.map((c, k) => {
    const after = k > 0 && out[k - 1].single !== null && fmtTick(c.lo, meta) === fmtTick(out[k - 1].single!, meta);
    return { colour: c.colour, label: c.single !== null ? fmtTick(c.single, meta) : `${after ? '> ' : ''}${fmtTick(c.lo, meta)}–${fmtTick(c.hi, meta)}` };
  });
}

/** Labels of fixed classes: "< 35", "35–45", …, "> 65" (independent of the data range). */
export function fixedLabels(scale: Scale, meta: MetricMeta | { decimals: number }): { colour: string; label: string }[] {
  const b = scale.breaks;
  return scale.classColours.map((colour, k) => ({
    colour,
    label: k === 0 ? `< ${fmtTick(b[0], meta)}` : k === b.length ? `> ${fmtTick(b[b.length - 1], meta)}` : `${fmtTick(b[k - 1], meta)}–${fmtTick(b[k], meta)}`,
  }));
}
