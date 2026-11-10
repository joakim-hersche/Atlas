// Spatial statistics on contiguity neighbours (neighbours.json: units sharing a boundary of at least 10 m, so
// corner-only contact does not count; the profile page uses the same file): global Moran's I with a
// permutation p-value, local Moran (LISA) with conditional permutations, and 3x3 bivariate classes.
// Pure functions without DOM or framework code, so they run in a Web Worker (spatial.worker.ts) and in
// unit tests (spatial.test.ts). Random numbers come from a seeded generator: the same view always
// gives the same p-values (a shared link shows what its author saw).
//
// Conventions (as in GeoDa / spdep with style "W"):
//  - weights are row-standardised: each neighbour of a unit counts 1/(number of neighbours);
//  - units without a value are left out, and so are units left without any neighbour with a value;
//  - Moran's I: I = sum_i z_i * lag_i / sum_i z_i^2, z = value - mean, lag_i = mean of z over the neighbours of i;
//    expected value under no spatial pattern E[I] = -1/(n-1);
//  - global p-value: two-sided pseudo p-value, (1 + #{|I* - E| >= |I - E|}) / (P + 1) over P random
//    reassignments of the values to the units;
//  - LISA: I_i = (z_i / m2) * lag_i with m2 = mean of z^2; the values of the neighbours are redrawn
//    from the other units (conditional permutation, z_i held fixed); the p-value looks at the tail in
//    the direction of I_i (upper tail if I_i > 0, lower tail otherwise), (1 + #as extreme) / (P + 1).

export const DEFAULT_PERMS = 999;
export const DEFAULT_SEED = 20260101;

/** Small fast seeded generator (mulberry32): uniform in [0, 1). */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** The part of the data the statistics can use: units with a value and at least one neighbour with a value. */
export interface Prepared {
  /** original index of each kept unit */
  keep: Int32Array;
  /** value minus mean, per kept unit */
  z: Float64Array;
  /** neighbours per kept unit, as positions among the kept units */
  nb: Int32Array[];
  /** mean and sum of squared deviations */
  mean: number;
  ss: number;
  /** counts for the notes: units without a value, units with a value but no usable neighbour */
  nMissing: number;
  nIsland: number;
}

/** `neighbours[i]` = indices of the units that touch unit i (a symmetric relation). */
export function prepare(values: (number | null | undefined)[], neighbours: ArrayLike<ArrayLike<number>>): Prepared {
  const N = values.length;
  const ok = (i: number) => values[i] !== null && values[i] !== undefined && Number.isFinite(values[i] as number);
  const keepFlag = new Uint8Array(N);
  let nMissing = 0;
  let nIsland = 0;
  for (let i = 0; i < N; i++) {
    if (!ok(i)) {
      nMissing++;
      continue;
    }
    let has = false;
    const row = neighbours[i];
    if (row) for (let k = 0; k < row.length; k++) if (row[k] !== i && ok(row[k])) { has = true; break; }
    if (has) keepFlag[i] = 1;
    else nIsland++;
  }
  const pos = new Int32Array(N).fill(-1);
  const keep: number[] = [];
  for (let i = 0; i < N; i++) if (keepFlag[i]) {
    pos[i] = keep.length;
    keep.push(i);
  }
  const n = keep.length;
  let sum = 0;
  for (const i of keep) sum += values[i] as number;
  const mean = n ? sum / n : 0;
  const z = new Float64Array(n);
  let ss = 0;
  const nb: Int32Array[] = new Array(n);
  for (let p = 0; p < n; p++) {
    const i = keep[p];
    z[p] = (values[i] as number) - mean;
    ss += z[p] * z[p];
    const row = neighbours[i];
    const out: number[] = [];
    if (row) for (let k = 0; k < row.length; k++) {
      const q = pos[row[k]];
      if (q >= 0 && q !== p && !out.includes(q)) out.push(q);
    }
    nb[p] = Int32Array.from(out);
  }
  return { keep: Int32Array.from(keep), z, nb, mean, ss, nMissing, nIsland };
}

/** sum_i z_i * lag_i for the values `x` laid out on the units */
function cross(x: Float64Array, nb: Int32Array[]): number {
  let s = 0;
  for (let i = 0; i < nb.length; i++) {
    const row = nb[i];
    let l = 0;
    for (let k = 0; k < row.length; k++) l += x[row[k]];
    s += x[i] * (l / row.length);
  }
  return s;
}

export interface MoranResult {
  /** units used */
  n: number;
  i: number;
  /** E[I] = -1/(n-1) */
  expected: number;
  /** two-sided pseudo p-value */
  p: number;
  /** (I - mean of the permuted I) / their standard deviation */
  z: number;
  perms: number;
  nMissing: number;
  nIsland: number;
  /** mean number of neighbours */
  meanNeighbours: number;
}

/** Fisher-Yates shuffle in place */
function shuffle(a: Float64Array, rand: () => number): void {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    const t = a[i];
    a[i] = a[j];
    a[j] = t;
  }
}

export function moranI(prep: Prepared): { i: number; n: number } {
  const n = prep.z.length;
  if (n < 3 || prep.ss === 0) return { i: NaN, n };
  return { i: cross(prep.z, prep.nb) / prep.ss, n };
}

export function moranTest(prep: Prepared, perms = DEFAULT_PERMS, seed = DEFAULT_SEED): MoranResult {
  const n = prep.z.length;
  let edges = 0;
  for (const r of prep.nb) edges += r.length;
  const base = { n, perms, nMissing: prep.nMissing, nIsland: prep.nIsland, meanNeighbours: n ? edges / n : 0 };
  if (n < 3 || prep.ss === 0) return { ...base, i: NaN, expected: NaN, p: NaN, z: NaN };
  const i0 = cross(prep.z, prep.nb) / prep.ss;
  const expected = -1 / (n - 1);
  const rand = rng(seed);
  const x = Float64Array.from(prep.z);
  let extreme = 0;
  let s = 0;
  let s2 = 0;
  const d0 = Math.abs(i0 - expected);
  for (let r = 0; r < perms; r++) {
    shuffle(x, rand);
    const ip = cross(x, prep.nb) / prep.ss;
    s += ip;
    s2 += ip * ip;
    if (Math.abs(ip - expected) >= d0 - 1e-12) extreme++;
  }
  const m = s / perms;
  const sd = Math.sqrt(Math.max(0, s2 / perms - m * m));
  return { ...base, i: i0, expected, p: (extreme + 1) / (perms + 1), z: sd > 0 ? (i0 - m) / sd : NaN };
}

/** Exact permutation p-value by enumerating every ordering (for tiny examples and tests only). */
export function moranExact(prep: Prepared): number {
  const n = prep.z.length;
  const expected = -1 / (n - 1);
  const i0 = cross(prep.z, prep.nb) / prep.ss;
  const x = Float64Array.from(prep.z);
  let total = 0;
  let extreme = 0;
  const idx = Array.from({ length: n }, (_, k) => k);
  const rec = (k: number) => {
    if (k === n) {
      for (let q = 0; q < n; q++) x[q] = prep.z[idx[q]];
      total++;
      if (Math.abs(cross(x, prep.nb) / prep.ss - expected) >= Math.abs(i0 - expected) - 1e-12) extreme++;
      return;
    }
    for (let j = k; j < n; j++) {
      [idx[k], idx[j]] = [idx[j], idx[k]];
      rec(k + 1);
      [idx[k], idx[j]] = [idx[j], idx[k]];
    }
  };
  rec(0);
  return extreme / total;
}

// ------------------------------------------------------------------------------------------ LISA

/** Cluster codes per original unit. */
export const LISA = { ns: 0, hh: 1, ll: 2, lh: 3, hl: 4, missing: -1, island: -2 } as const;
export type LisaCode = (typeof LISA)[keyof typeof LISA];

export interface LisaResult {
  /** per original unit: local Moran's I (NaN where not computed) */
  i: Float64Array;
  /** per original unit: pseudo p-value (NaN where not computed) */
  p: Float64Array;
  /** per original unit: quadrant before significance: 1 HH, 2 LL, 3 LH, 4 HL; 0 where not computed */
  quad: Int8Array;
  /** per original unit: -1 no value, -2 no neighbour with a value, else 0 */
  status: Int8Array;
  perms: number;
}

export function lisa(prep: Prepared, nTotal: number, perms = DEFAULT_PERMS, seed = DEFAULT_SEED): LisaResult {
  const n = prep.z.length;
  const I = new Float64Array(nTotal).fill(NaN);
  const P = new Float64Array(nTotal).fill(NaN);
  const quad = new Int8Array(nTotal);
  const status = new Int8Array(nTotal).fill(LISA.missing);
  // units with a value that were dropped for lack of neighbours are islands
  // (the caller knows which; here every non-kept unit stays "missing" unless marked afterwards)
  if (n < 3 || prep.ss === 0) return { i: I, p: P, quad, status, perms };
  const m2 = prep.ss / n;
  const zs = new Float64Array(n);
  for (let k = 0; k < n; k++) zs[k] = prep.z[k] / Math.sqrt(m2);
  const rand = rng(seed ^ 0x9e3779b9);
  const pick = new Int32Array(64);
  for (let a = 0; a < n; a++) {
    const row = prep.nb[a];
    const deg = row.length;
    let lag = 0;
    for (let k = 0; k < deg; k++) lag += zs[row[k]];
    lag /= deg;
    const i0 = zs[a] * lag;
    let ge = 0;
    let le = 0;
    const buf = deg <= pick.length ? pick : new Int32Array(deg);
    for (let r = 0; r < perms; r++) {
      // deg distinct units other than a
      let got = 0;
      while (got < deg) {
        const c = Math.floor(rand() * n);
        if (c === a) continue;
        let dup = false;
        for (let q = 0; q < got; q++) if (buf[q] === c) { dup = true; break; }
        if (!dup) buf[got++] = c;
      }
      let l = 0;
      for (let k = 0; k < deg; k++) l += zs[buf[k]];
      const ip = (zs[a] * l) / deg;
      if (ip >= i0 - 1e-12) ge++;
      if (ip <= i0 + 1e-12) le++;
    }
    const o = prep.keep[a];
    I[o] = i0;
    P[o] = ((i0 > 0 ? ge : le) + 1) / (perms + 1);
    status[o] = 0;
    quad[o] = zs[a] >= 0 ? (lag >= 0 ? LISA.hh : LISA.hl) : lag >= 0 ? LISA.lh : LISA.ll;
  }
  return { i: I, p: P, quad, status, perms };
}

/** Benjamini-Hochberg: the largest p-value that stays significant at false discovery rate q (or 0). */
export function fdrThreshold(p: ArrayLike<number>, q = 0.05): number {
  const ps: number[] = [];
  for (let k = 0; k < p.length; k++) if (Number.isFinite(p[k])) ps.push(p[k]);
  ps.sort((a, b) => a - b);
  const m = ps.length;
  let thr = 0;
  for (let k = 0; k < m; k++) if (ps[k] <= ((k + 1) / m) * q) thr = ps[k];
  return thr;
}

export interface LisaClasses {
  /** per original unit, LISA codes */
  code: Int8Array;
  counts: { hh: number; ll: number; lh: number; hl: number; ns: number; none: number };
  /** p-value at or below which a unit counts as significant */
  threshold: number;
}

/** Significant clusters at `alpha`: uncorrected (p < alpha) or with the false discovery rate controlled at alpha. */
export function lisaClasses(res: LisaResult, alpha = 0.05, fdr = false): LisaClasses {
  const N = res.p.length;
  const code = new Int8Array(N);
  const counts = { hh: 0, ll: 0, lh: 0, hl: 0, ns: 0, none: 0 };
  const thr = fdr ? fdrThreshold(res.p, alpha) : alpha;
  for (let i = 0; i < N; i++) {
    if (res.status[i] !== 0) {
      code[i] = res.status[i];
      counts.none++;
      continue;
    }
    const sig = fdr ? res.p[i] <= thr && thr > 0 : res.p[i] < alpha;
    if (!sig) {
      code[i] = LISA.ns;
      counts.ns++;
      continue;
    }
    code[i] = res.quad[i];
    if (res.quad[i] === LISA.hh) counts.hh++;
    else if (res.quad[i] === LISA.ll) counts.ll++;
    else if (res.quad[i] === LISA.lh) counts.lh++;
    else counts.hl++;
  }
  return { code, counts, threshold: thr };
}

// ------------------------------------------------------------------------------------- bivariate

/** Value at fraction q (0..1) of the sorted non-missing values, linear interpolation. */
export function quantile(sorted: number[], q: number): number {
  if (!sorted.length) return NaN;
  const x = q * (sorted.length - 1);
  const lo = Math.floor(x);
  const hi = Math.min(sorted.length - 1, lo + 1);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (x - lo);
}

/** Cut points between the lower, middle and upper third of the values. */
export function terciles(x: (number | null | undefined)[]): [number, number] {
  const s = x.filter((v): v is number => v !== null && v !== undefined && Number.isFinite(v)).sort((a, b) => a - b);
  return [quantile(s, 1 / 3), quantile(s, 2 / 3)];
}

export const tercileOf = (v: number, cuts: [number, number]): 0 | 1 | 2 => (v <= cuts[0] ? 0 : v <= cuts[1] ? 1 : 2);

export interface BivariateResult {
  /** per unit: 3 * classB + classA (0..8), or -1 when either value is missing */
  cell: Int8Array;
  cutsA: [number, number];
  cutsB: [number, number];
  /** units per cell (index as in `cell`) */
  counts: number[];
  /** units with both values */
  n: number;
}

export function bivariate(a: (number | null | undefined)[], b: (number | null | undefined)[]): BivariateResult {
  const N = a.length;
  const ok = (x: number | null | undefined): x is number => x !== null && x !== undefined && Number.isFinite(x);
  // class breaks from the units that have both values, so the nine cells share one population
  const both = (v: (number | null | undefined)[]) => v.map((x, i) => (ok(x) && ok(b[i]) && ok(a[i]) ? x : null));
  const cutsA = terciles(both(a));
  const cutsB = terciles(both(b));
  const cell = new Int8Array(N).fill(-1);
  const counts = new Array<number>(9).fill(0);
  let n = 0;
  for (let i = 0; i < N; i++) {
    const x = a[i];
    const y = b[i];
    if (!ok(x) || !ok(y)) continue;
    const c = 3 * tercileOf(y, cutsB) + tercileOf(x, cutsA);
    cell[i] = c;
    counts[c]++;
    n++;
  }
  return { cell, cutsA, cutsB, counts, n };
}

/** Spearman rank correlation of two columns (ties get average ranks), over units with both values. */
export function spearman(a: (number | null | undefined)[], b: (number | null | undefined)[]): number {
  const idx: number[] = [];
  for (let i = 0; i < a.length; i++) if (Number.isFinite(a[i] as number) && Number.isFinite(b[i] as number) && a[i] !== null && b[i] !== null) idx.push(i);
  const n = idx.length;
  if (n < 3) return NaN;
  const rank = (v: (number | null | undefined)[]) => {
    const o = idx.slice().sort((p, q) => (v[p] as number) - (v[q] as number));
    const r = new Float64Array(a.length);
    for (let s = 0; s < n; ) {
      let e = s;
      while (e + 1 < n && v[o[e + 1]] === v[o[s]]) e++;
      for (let k = s; k <= e; k++) r[o[k]] = (s + e) / 2;
      s = e + 1;
    }
    return r;
  };
  const ra = rank(a);
  const rb = rank(b);
  let ma = 0, mb = 0;
  for (const i of idx) { ma += ra[i]; mb += rb[i]; }
  ma /= n; mb /= n;
  let sab = 0, saa = 0, sbb = 0;
  for (const i of idx) {
    sab += (ra[i] - ma) * (rb[i] - mb);
    saa += (ra[i] - ma) ** 2;
    sbb += (rb[i] - mb) ** 2;
  }
  return saa > 0 && sbb > 0 ? sab / Math.sqrt(saa * sbb) : NaN;
}

// ------------------------------------------------------------------------------- worker protocol

export interface SpatialRequest {
  id: number;
  values: (number | null)[];
  /** neighbours per unit index (compressed: offsets + flat list) */
  off: Int32Array;
  list: Int32Array;
  perms: number;
  seed: number;
  /** also run the LISA (costs about the same again) */
  withLisa: boolean;
}
export interface SpatialResponse {
  id: number;
  moran: MoranResult;
  lisa: LisaResult | null;
  error?: string;
}

/** The whole job: used by the worker and as the fallback on the main thread. */
export function runSpatial(req: SpatialRequest): SpatialResponse {
  const N = req.values.length;
  const nb: number[][] = new Array(N);
  for (let i = 0; i < N; i++) nb[i] = Array.from(req.list.subarray(req.off[i], req.off[i + 1]));
  const prep = prepare(req.values, nb);
  const moran = moranTest(prep, req.perms, req.seed);
  let l: LisaResult | null = null;
  if (req.withLisa) {
    l = lisa(prep, N, req.perms, req.seed);
    // units with a value but without a usable neighbour: marked as islands
    for (let i = 0; i < N; i++) {
      const v = req.values[i];
      if (l.status[i] === LISA.missing && v !== null && v !== undefined && Number.isFinite(v)) l.status[i] = LISA.island;
    }
  }
  return { id: req.id, moran, lisa: l };
}

/** Flatten neighbour lists into offsets + list (cheap to send to a worker). */
export function flatten(nb: number[][]): { off: Int32Array; list: Int32Array } {
  const off = new Int32Array(nb.length + 1);
  let t = 0;
  for (let i = 0; i < nb.length; i++) {
    off[i] = t;
    t += nb[i].length;
  }
  off[nb.length] = t;
  const list = new Int32Array(t);
  let k = 0;
  for (const r of nb) for (const j of r) list[k++] = j;
  return { off, list };
}
