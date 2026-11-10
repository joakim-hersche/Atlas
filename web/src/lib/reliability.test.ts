import { describe, expect, it } from 'vitest';
import { ruleTerms, ruleUnstable, sumColumns, unstableEither } from './reliability';

describe('small numbers for any period (B1)', () => {
  const rule = { base: 'pop_total', count: null, min_base: 100, min_count: null, years: 1 };

  it('flags values whose base is below the minimum, never units without a value', () => {
    const v = [10, 20, null, 30];
    const base = [50, 150, 10, 99];
    expect(ruleUnstable(v, rule, base, null)).toEqual([0, 3]);
  });

  it('reads the count too, and the special cap', () => {
    const r = { base: null, count: 'births', min_base: null, min_count: 20 };
    expect(ruleUnstable([1, 2, 3], r, null, [5, 25, null])).toEqual([0]);
    expect(ruleUnstable([900, 1200, null], null, null, null, 1000)).toEqual([1]);
  });

  it('a base without a value cannot judge the unit', () => {
    expect(ruleUnstable([1, 2], rule, [null, 500], null)).toEqual([]);
  });

  it('sums a base given as several metrics (yes + no votes)', () => {
    expect(ruleTerms({ base: ['vote_yes', 'vote_no'], count: null })).toEqual({ base: ['vote_yes', 'vote_no'], count: [] });
    expect(ruleTerms({ base: 'vote_yes+vote_no', count: 'births' })).toEqual({ base: ['vote_yes', 'vote_no'], count: ['births'] });
    expect(sumColumns([[40, 10, null], [50, 200, 3]])).toEqual([90, 210, null]);
    expect(sumColumns([])).toBeNull();
  });

  it('a change is unstable when either year is, among units with a change value', () => {
    expect(unstableEither([3, 1], [1, 5, 7], [0, 1, 2, 3, 4, 5, null, 7])).toEqual([1, 3, 5, 7]);
    expect(unstableEither([2], [], [1, 2, null])).toEqual([]);
  });
});
