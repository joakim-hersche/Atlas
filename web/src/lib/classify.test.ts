import { describe, expect, it } from 'vitest';
import { buildScale, divergeCentre, isDiverging, N_CLASSES, quantile, rankOf, sortedValues, rangeText, higherThan } from './classify';
import { divRamp, seqRamp } from './theme';
import type { MetricMeta } from './data';

const SEQ = seqRamp();
const DIV = divRamp();
const meta = (o: Partial<MetricMeta> & { id: string }) => ({ unit: '', direction: 'neutral', ...o }) as MetricMeta;

/** 1..n */
const ramp = (n: number) => Array.from({ length: n }, (_, i) => i + 1);

describe('helpers', () => {
  it('sortedValues drops gaps and sorts ascending', () => {
    expect(sortedValues([3, null, 1, NaN, 2])).toEqual([1, 2, 3]);
  });
  it('quantile interpolates linearly', () => {
    expect(quantile([1, 2, 3, 4, 5], 0)).toBe(1);
    expect(quantile([1, 2, 3, 4, 5], 0.5)).toBe(3);
    expect(quantile([0, 10], 0.25)).toBe(2.5);
    expect(quantile([], 0.5)).toBeNaN();
  });
});

describe('quantile classes', () => {
  const v = ramp(100);
  const s = buildScale(v, 'quantile', false, SEQ, DIV);
  it('makes five classes of about equal size', () => {
    expect(s.breaks).toHaveLength(N_CLASSES - 1);
    expect(s.classColours).toHaveLength(N_CLASSES);
    expect(s.counts.reduce((a, b) => a + b, 0)).toBe(100);
    for (const c of s.counts) expect(c).toBeGreaterThanOrEqual(19), expect(c).toBeLessThanOrEqual(21);
  });
  it('breaks ascend and colours run from pale to dark', () => {
    expect([...s.breaks].sort((a, b) => a - b)).toEqual(s.breaks);
    expect(s.classColours[0]).toBe(SEQ[0]);
    expect(s.classColours[N_CLASSES - 1]).toBe(SEQ[SEQ.length - 1]);
    expect(s.colourOf(1)).toBe(s.classColours[0]);
    expect(s.colourOf(100)).toBe(s.classColours[N_CLASSES - 1]);
  });
  it('gives gaps no colour and counts only real values', () => {
    const t = buildScale([1, null, 2, 3, NaN, 4, 5], 'quantile', false, SEQ, DIV);
    expect(t.n).toBe(5);
    expect(t.unitColour[1]).toBeNull();
    expect(t.unitColour[4]).toBeNull();
    expect(t.unitColour[0]).not.toBeNull();
  });
  it('a block of tied zeros gets a class of its own', () => {
    const t = buildScale([...Array(60).fill(0), ...ramp(40)], 'quantile', false, SEQ, DIV);
    expect(t.counts[0]).toBe(60);
    expect(t.min).toBe(0);
    expect(t.classMax[0]).toBe(0);
  });
  it('a constant metric collapses to one class without failing', () => {
    const t = buildScale([5, 5, 5, 5], 'quantile', false, SEQ, DIV);
    expect(t.breaks).toEqual([]);
    expect(t.counts).toEqual([4]);
  });
});

describe('equal-interval classes', () => {
  it('splits the range into five equal steps', () => {
    const s = buildScale([0, 25, 50, 75, 100], 'equal', false, SEQ, DIV);
    expect(s.breaks).toEqual([20, 40, 60, 80]);
    expect(s.counts).toEqual([1, 1, 1, 1, 1]);
    expect(s.classMin).toEqual([0, 25, 50, 75, 100]);
  });
  it('puts a value on a break into the upper class', () => {
    const s = buildScale([0, 20, 100], 'equal', false, SEQ, DIV);
    expect(s.counts[1]).toBe(1);
  });
  it('differs from quantiles on a skewed distribution', () => {
    const v = [...Array(90).fill(0).map((_, i) => i), 1000];
    const q = buildScale(v, 'quantile', false, SEQ, DIV);
    const e = buildScale(v, 'equal', false, SEQ, DIV);
    expect(e.counts[0]).toBeGreaterThan(q.counts[0]);
  });
  it('a constant metric has no breaks', () => {
    expect(buildScale([3, 3], 'equal', false, SEQ, DIV).breaks).toEqual([]);
  });
});

describe('continuous scale', () => {
  it('has no classes and maps the 2nd to 98th percentile onto the ramp', () => {
    const s = buildScale(ramp(1000), 'continuous', false, SEQ, DIV);
    expect(s.breaks).toEqual([]);
    expect(s.lo).toBeCloseTo(quantile(ramp(1000), 0.02));
    expect(s.hi).toBeCloseTo(quantile(ramp(1000), 0.98));
    expect(s.colourOf(s.lo - 1000)).toBe(SEQ[0]);
    expect(s.colourOf(s.hi + 1000)).toBe(SEQ[SEQ.length - 1]);
  });
});

describe('diverging scales', () => {
  it('detects change metrics, vote shares and neutral metrics that cross zero', () => {
    const sNeg = [-2, -1, 3];
    expect(isDiverging(meta({ id: 'pop_change_10y', unit: '%' }), sNeg)).toBe(true);
    expect(isDiverging(meta({ id: 'x', aggregation: 'change:pop_total:10' } as never), [1, 2])).toBe(true);
    expect(isDiverging(meta({ id: 'vote_yes_share', unit: '%' }), [10, 90])).toBe(true);
    expect(isDiverging(meta({ id: 'net_migration', direction: 'neutral' }), sNeg)).toBe(true);
    expect(isDiverging(meta({ id: 'vac_rate', direction: 'lower_better' }), sNeg)).toBe(false);
    expect(isDiverging(meta({ id: 'pop_total' }), [1, 2, 3])).toBe(false);
  });
  it('the midpoint is 50 for vote yes shares and 0 otherwise', () => {
    expect(divergeCentre({ id: 'vote_yes_share' })).toBe(50);
    expect(divergeCentre({ id: 'pop_change_10y' })).toBe(0);
  });

  it('fixed classes around 50 %: three orange classes below, three blue above, the same for every vote', () => {
    const a = buildScale([5, 20, 40, 48, 52, 60, 80, 95], 'quantile', true, SEQ, DIV, 50);
    const b = buildScale([44, 49, 51, 56], 'quantile', true, SEQ, DIV, 50);
    expect(a.fixed).toBe(true);
    expect(a.breaks).toEqual([35, 45, 50, 55, 65]);
    expect(b.breaks).toEqual(a.breaks);
    expect(a.classColours).toEqual([DIV[0], DIV[1], DIV[2], DIV[4], DIV[5], DIV[6]]);
    // 50 % itself is a yes majority boundary: it goes to the blue side
    expect(a.colourOf(49.99)).toBe(DIV[2]);
    expect(a.colourOf(50)).toBe(DIV[4]);
    expect(a.colourOf(10)).toBe(DIV[0]);
    expect(a.colourOf(90)).toBe(DIV[6]);
    expect(a.counts.reduce((x, y) => x + y, 0)).toBe(8);
  });
  it('fixed classes also apply to equal-interval, but not to continuous', () => {
    expect(buildScale([10, 90], 'equal', true, SEQ, DIV, 50).fixed).toBe(true);
    expect(buildScale([10, 90], 'continuous', true, SEQ, DIV, 50).fixed).toBe(false);
  });

  it('a change around zero keeps orange below and blue above 0', () => {
    const s = buildScale([-10, -5, -1, 0, 1, 5, 10, 20], 'quantile', true, SEQ, DIV, 0);
    expect(s.fixed).toBe(false);
    expect(s.breaks).toContain(0);
    expect(s.colourOf(-10)).not.toBe(s.colourOf(20));
    expect(DIV.slice(0, 3)).toContain(s.colourOf(-10));
    expect(DIV.slice(4)).toContain(s.colourOf(20));
  });
  it('equal-interval diverging classes are symmetric around the centre', () => {
    const s = buildScale([-10, 0, 10], 'equal', true, SEQ, DIV, 0);
    expect(s.lo).toBe(-10);
    expect(s.hi).toBe(10);
    expect(s.colourOf(-10)).toBe(DIV[0]);
    expect(s.colourOf(10)).toBe(DIV[6]);
  });
  it('D3: every diverging class gets its own colour (quantile and equal interval)', () => {
    // a change map like population 2010->2025: few losses, many gains (1 class below 0, 5 above)
    const gains = [-676, -20, -3, ...ramp(400).map((x) => x * 3), ...ramp(400).map((x) => x * 40)];
    const datasets = [
      gains,
      ramp(200).map((x) => x - 20),
      ramp(200).map((x) => x - 180),
      [-10, -5, -1, 0, 1, 5, 10, 20],
      ramp(1000).map((x) => (x % 7) - 3 + x / 100),
    ];
    for (const v of datasets)
      for (const m of ['quantile', 'equal'] as const) {
        const s = buildScale(v, m, true, SEQ, DIV, 0);
        expect(new Set(s.classColours).size).toBe(s.classColours.length);
      }
    // the vote yes share (quantile around 50 %) too
    const yes = buildScale(ramp(100).map((x) => 20 + x * 0.3), 'quantile', true, SEQ, DIV, 50);
    expect(new Set(yes.classColours).size).toBe(yes.classColours.length);
  });
  it('D3: the arms run from pale next to the centre to dark at the ends', () => {
    const s = buildScale(ramp(300).map((x) => x - 30), 'quantile', true, SEQ, DIV, 0);
    const last = s.classColours.length - 1;
    expect(s.classColours[last]).toBe(DIV[6]);
    expect(s.classColours[0]).not.toBe(DIV[6]);
  });
  it('continuous diverging maps the centre to the neutral grey', () => {
    const s = buildScale([-10, -5, 0, 5, 10], 'continuous', true, SEQ, DIV, 0);
    expect(s.colourOf(0)).toBe(DIV[3]);
  });
});

describe('rankOf', () => {
  it('ranks the highest value first for higher_better and neutral metrics', () => {
    const r = rankOf([10, 30, 20, null], 1, 'higher_better');
    expect(r).toMatchObject({ rank: 1, n: 3, tied: 0 });
  });
  it('ranks the lowest value first for lower_better metrics', () => {
    const r = rankOf([10, 30, 20, null], 0, 'lower_better');
    expect(r).toMatchObject({ rank: 1, n: 3, tied: 0 });
  });
  it('tied values share the best rank and report the tie', () => {
    const r = rankOf([5, 9, 9, 1], 1, 'higher_better')!;
    expect(r).toMatchObject({ rank: 1, rankTo: 2, tied: 1, n: 4 });
  });
  it('has no rank for a unit without a value', () => {
    expect(rankOf([10, null], 1, 'higher_better')).toBeNull();
  });
});

describe('class range labels', () => {
  it('keep negative bounds apart from the dash', () => {
    expect(rangeText('10', '20')).toBe('10–20');
    expect(rangeText('−14.5', '−6.5')).toBe('−14.5\u2009–\u2009−6.5');
    expect(rangeText('−1.1', '0')).toBe('−1.1\u2009–\u20090');
  });
});

describe('tie wording (D5)', () => {
  it('"higher than" counts only strictly lower values: a zero tied with many is not higher than them', () => {
    const v = [0, 0, 0, 0, 0, 5, 10, 20, 30, 40];
    const r = rankOf(v, 0, 'higher_better')!;
    expect(higherThan(r)).toBe(0);
    expect(r.tied).toBe(4);
    const top = rankOf(v, 9, 'higher_better')!;
    expect(Math.round(higherThan(top))).toBe(100);
  });
});
