import { describe, expect, it } from 'vitest';
import {
  bivariate, fdrThreshold, flatten, lisa, lisaClasses, LISA, moranExact, moranI, moranTest, prepare, rng, runSpatial, spearman, terciles,
} from './spatial';

/** four units in a row: 0-1-2-3 */
const CHAIN = [[1], [0, 2], [1, 3], [2]];
/** 2x2 grid with rook contact: 0 1 / 2 3 */
const GRID2 = [[1, 2], [0, 3], [0, 3], [1, 2]];

describe("Moran's I", () => {
  it('matches the hand calculation for a chain of four (values 1..4)', () => {
    // z = -1.5 -0.5 0.5 1.5; sum z^2 = 5; sum_i z_i * lag_i = 2.0 (row-standardised); I = 2/5
    const { i, n } = moranI(prepare([1, 2, 3, 4], CHAIN));
    expect(n).toBe(4);
    expect(i).toBeCloseTo(0.4, 12);
  });

  it('is -1 for a perfect checkerboard and E[I] = -1/(n-1)', () => {
    const r = moranTest(prepare([1, 0, 0, 1], GRID2), 99, 1);
    expect(r.i).toBeCloseTo(-1, 12);
    expect(r.expected).toBeCloseTo(-1 / 3, 12);
  });

  it('is unchanged by shifting or scaling the values', () => {
    const a = moranI(prepare([1, 2, 3, 4], CHAIN)).i;
    const b = moranI(prepare([10, 20, 30, 40].map((x) => x * 7 + 100), CHAIN)).i;
    expect(b).toBeCloseTo(a, 12);
  });

  it('leaves out missing values and units without a neighbour that has a value', () => {
    // unit 3 has no value; unit 2 then keeps only neighbour 1
    const p = prepare([1, 2, 3, null], CHAIN);
    expect(p.keep.length).toBe(3);
    expect(p.nMissing).toBe(1);
    // an isolated unit with a value is reported as an island
    const q = prepare([1, 2, 3, 4, 9], [...CHAIN, []]);
    expect(q.nIsland).toBe(1);
    expect(q.keep.length).toBe(4);
  });

  it('Monte Carlo p-value agrees with the exact permutation p-value on a small example', () => {
    // 3x3 grid (rook), a smooth gradient
    const g = [[1, 3], [0, 2, 4], [1, 5], [0, 4, 6], [1, 3, 5, 7], [2, 4, 8], [3, 7], [4, 6, 8], [5, 7]];
    const vals = [1, 2, 3, 2, 3, 4, 3, 4, 5];
    const prep = prepare(vals, g);
    const exact = moranExact(prep);
    const mc = moranTest(prep, 19999, 42);
    expect(mc.i).toBeGreaterThan(0.5);
    expect(Math.abs(mc.p - exact)).toBeLessThan(0.01);
    expect(exact).toBeLessThan(0.05);
  });

  it('the same seed gives the same result; a pattern-free column gives a large p-value', () => {
    const n = 400;
    const side = 20;
    const nb: number[][] = [];
    for (let i = 0; i < n; i++) {
      const r = Math.floor(i / side), c = i % side, row: number[] = [];
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
        const rr = r + dr, cc = c + dc;
        if ((dr || dc) && rr >= 0 && rr < side && cc >= 0 && cc < side) row.push(rr * side + cc); // queen
      }
      nb.push(row);
    }
    const rand = rng(7);
    const noise = Array.from({ length: n }, () => rand());
    const a = moranTest(prepare(noise, nb), 499, 3);
    const b = moranTest(prepare(noise, nb), 499, 3);
    expect(a.p).toBe(b.p);
    expect(Math.abs(a.i)).toBeLessThan(0.15);
    expect(a.p).toBeGreaterThan(0.05);
    // a smooth surface is strongly clustered
    const smooth = Array.from({ length: n }, (_, i) => Math.floor(i / side) + (i % side));
    const s = moranTest(prepare(smooth, nb), 499, 3);
    expect(s.i).toBeGreaterThan(0.8);
    expect(s.p).toBeLessThan(0.01);
  });
});

describe('LISA', () => {
  it('local values average to the global I (row-standardised weights)', () => {
    const prep = prepare([1, 2, 3, 4], CHAIN);
    const r = lisa(prep, 4, 99, 5);
    const mean = Array.from(r.i).reduce((s, x) => s + x, 0) / 4;
    expect(mean).toBeCloseTo(0.4, 12);
  });

  it('assigns the four quadrants', () => {
    // two high units next to each other, two low units next to each other
    const r = lisa(prepare([10, 9, 1, 0], CHAIN), 4, 99, 5);
    expect(Array.from(r.quad)).toEqual([LISA.hh, LISA.hh, LISA.ll, LISA.ll]);
    // a lone high unit among lows is a high-low outlier, a lone low among highs a low-high outlier
    const star = [[1, 2, 3, 4], [0], [0], [0], [0]];
    expect(Array.from(lisa(prepare([9, 0, 0, 1, 1], star), 5, 99, 5).quad)[0]).toBe(LISA.hl);
    expect(Array.from(lisa(prepare([0, 9, 9, 8, 9], star), 5, 99, 5).quad)[0]).toBe(LISA.lh);
  });

  it('finds a planted cluster and not noise (999 permutations)', () => {
    const side = 16, n = side * side;
    const nb: number[][] = [];
    for (let i = 0; i < n; i++) {
      const r = Math.floor(i / side), c = i % side, row: number[] = [];
      for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [-1, 1], [1, -1], [1, 1]]) {
        const rr = r + dr, cc = c + dc;
        if (rr >= 0 && rr < side && cc >= 0 && cc < side) row.push(rr * side + cc);
      }
      nb.push(row);
    }
    const rand = rng(11);
    const v = Array.from({ length: n }, (_, i) => {
      const r = Math.floor(i / side), c = i % side;
      return (r < 5 && c < 5 ? 10 : 0) + rand();
    });
    const res = lisa(prepare(v, nb), n, 999, 9);
    const cl = lisaClasses(res, 0.05, false);
    // centre of the planted block: high-high
    expect(cl.code[2 * side + 2]).toBe(LISA.hh);
    // far corner: not a high-high cluster
    expect(cl.code[(side - 1) * side + (side - 1)]).not.toBe(LISA.hh);
    expect(cl.counts.hh).toBeGreaterThan(10);
    expect(cl.counts.hh).toBeLessThan(40);
    // correcting for the number of tests can only remove clusters
    const f = lisaClasses(res, 0.05, true);
    expect(f.counts.hh + f.counts.ll + f.counts.lh + f.counts.hl).toBeLessThanOrEqual(cl.counts.hh + cl.counts.ll + cl.counts.lh + cl.counts.hl);
  });

  it('marks missing units and islands', () => {
    const vals = [1, 2, 3, 4, 5, null];
    const r = runSpatial({ id: 1, values: vals, ...flatten([...CHAIN, [], [0]]), perms: 99, seed: 1, withLisa: true });
    expect(r.lisa!.status[4]).toBe(LISA.island);
    expect(r.lisa!.status[5]).toBe(LISA.missing);
    expect(r.lisa!.status[0]).toBe(0);
  });
});

describe('false discovery rate', () => {
  it('Benjamini-Hochberg threshold', () => {
    // m = 5, q = 0.05: p(k) <= k/5 * 0.05 -> 0.001 <= 0.01 ok, 0.012 <= 0.02 ok, 0.04 <= 0.03 no, ...
    expect(fdrThreshold([0.04, 0.001, 0.5, 0.012, 0.9], 0.05)).toBeCloseTo(0.012, 12);
    expect(fdrThreshold([0.2, 0.5], 0.05)).toBe(0);
  });
});

describe('bivariate classes', () => {
  it('splits both columns into thirds and counts the cells', () => {
    const a = [1, 2, 3, 4, 5, 6, 7, 8, 9];
    const b = [9, 8, 7, 6, 5, 4, 3, 2, 1];
    const r = bivariate(a, b);
    expect(r.n).toBe(9);
    expect(terciles(a)).toEqual([1 + 8 / 3, 1 + 16 / 3]);
    // a low and b high -> A class 0, B class 2 -> cell 6
    expect(r.cell[0]).toBe(6);
    expect(r.cell[8]).toBe(2);
    expect(r.counts.reduce((s, x) => s + x, 0)).toBe(9);
  });
  it('leaves out units missing either value', () => {
    const r = bivariate([1, 2, null, 4], [1, null, 3, 4]);
    expect(Array.from(r.cell).filter((c) => c >= 0).length).toBe(2);
    expect(r.cell[1]).toBe(-1);
  });
  it('Spearman correlation', () => {
    expect(spearman([1, 2, 3, 4], [10, 20, 30, 40])).toBeCloseTo(1, 12);
    expect(spearman([1, 2, 3, 4], [4, 3, 2, 1])).toBeCloseTo(-1, 12);
  });
});
