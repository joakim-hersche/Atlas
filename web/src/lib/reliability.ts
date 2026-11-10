// Reliability of survey and modelled values.
// Only what the build ships is used: where a metric has a companion metric `<id>_ci` (the half-width of its
// published 95 % confidence interval; Structural Survey shares and counts, rents), the interval, the range
// of plausible ranks and the classes it touches are shown. Every other survey or modelled value gets a
// plain badge saying that no interval is published. Nothing is estimated here.
import type { MetricMeta } from './data';
import type { Scale } from './classify';

export type Kind = 'ci' | 'survey' | 'modelled';

export interface CiSpec {
  /** the companion metric holding the half-width */
  meta: MetricMeta;
  /** half-width as % of the estimate (counts) rather than in the metric's own unit */
  relative: boolean;
}

/** The confidence-interval companion of a metric at a level, or null. Companion ids end in `_ci`. */
export function ciSpec(meta: MetricMeta, metas: Map<string, MetricMeta>, level: string): CiSpec | null {
  if (meta.id.endsWith('_ci')) return null;
  const c = metas.get(`${meta.id}_ci`);
  if (!c || !c.levels.includes(level) || !c.unit.startsWith('±')) return null;
  // '± %' = relative to the estimate; '± pp', '± CHF' … = in absolute units
  const relative = c.unit.replace('±', '').trim() === '%';
  return { meta: c, relative };
}

export interface Interval {
  lo: number;
  hi: number;
  half: number;
}

/** Interval of every unit from the values and the half-widths (null where either is missing). */
export function intervals(v: (number | null)[], ci: (number | null)[], relative: boolean): (Interval | null)[] {
  return v.map((x, i) => {
    const h = ci[i];
    if (x === null || x === undefined || h === null || h === undefined || !Number.isFinite(h)) return null;
    const half = relative ? (Math.abs(x) * h) / 100 : h;
    return { lo: x - half, hi: x + half, half };
  });
}

export interface RankRange {
  /** best rank still possible, worst rank still possible, units ranked */
  from: number;
  to: number;
  n: number;
}

/** Range of ranks a unit could hold if every value lay anywhere in its interval (units without an interval
 *  count as exact). Rank 1 = highest value, or the lowest for lower-is-better metrics, as in the ranking.
 *  A unit is surely ahead of another only when their intervals do not overlap, so the range is wide on
 *  purpose: it is the set of ranks the data cannot rule out. */
export function rankRange(v: (number | null)[], iv: (Interval | null)[], i: number, direction: MetricMeta['direction']): RankRange | null {
  const x = v[i];
  if (x === null || x === undefined) return null;
  const me = iv[i] ?? { lo: x, hi: x, half: 0 };
  const low = direction === 'lower_better';
  let ahead = 0; // surely better than me
  let behind = 0; // surely worse than me
  let n = 0;
  for (let j = 0; j < v.length; j++) {
    const y = v[j];
    if (y === null || y === undefined) continue;
    n++;
    if (j === i) continue;
    const o = iv[j] ?? { lo: y, hi: y, half: 0 };
    if (low) {
      if (o.hi < me.lo) ahead++;
      else if (o.lo > me.hi) behind++;
    } else {
      if (o.lo > me.hi) ahead++;
      else if (o.hi < me.lo) behind++;
    }
  }
  return { from: ahead + 1, to: n - behind, n };
}

/** The interval reaches into more than one class of the scale (the unit's colour could be another one). */
export function crossesClass(scale: Scale, iv: Interval): boolean {
  if (scale.method === 'continuous' || !scale.breaks.length) return false;
  return scale.colourOf(iv.lo) !== scale.colourOf(iv.hi);
}

/** Kind of reliability notice a metric needs: a published interval, or the survey / modelled badge. */
export function kindOf(precision: string, hasCi: boolean): Kind | null {
  if (hasCi) return 'ci';
  if (precision === 'survey') return 'survey';
  if (precision === 'modelled') return 'modelled';
  return null;
}
