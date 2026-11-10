// "Similar places" (profile page): nearest units by weighted z-scores of a set of metrics, the reasons
// behind each match (per-metric share of the distance), and an optional "near" restriction by distance
// (km between label points) or travel time to a hub.
//
// Method, kept deliberately simple so it can be explained in one sentence:
//   z      = (value - mean) / standard deviation over all units of the level that have a value
//            (log10 of the value first for skewed metrics),
//   d(a,b) = sqrt( sum_k w_k (z_ka - z_kb)^2 / sum_k w_k ) over the metrics both places have,
//   share  = w_k (z_ka - z_kb)^2 / (d^2 * sum_k w_k): how much one metric adds to the distance.
// With all weights 1 this is the root mean square of the z-score differences, the behaviour before
// weights existed. Mahalanobis distance or PCA would remove the double counting of correlated metrics, but
// with missing values, 60+ candidate metrics and no per-metric reading of the result they are harder to
// explain; instead the editor names strongly correlated pairs so the reader can lower their weights.
import type { ColumnFile, MetricMeta, UnitRow } from './data';
import type { PlaceLevel } from './profile';
import type { ReachTimes } from './places';
import { refOf } from './places';

export interface SimMetric {
  id: string;
  /** weight, 0.5 steps from 0.5 to 3 */
  w: number;
  /** compare on a log10 scale (skewed metrics: density, jobs, income) */
  log: boolean;
}

/** Headline metrics of the default "similar places" vector (all in the core file, national coverage).
 *  Skewed ones are compared on a log scale. */
export const SIMILAR_METRICS: { id: string; log?: boolean }[] = [
  { id: 'geo_pop_density', log: true },
  { id: 'pop_change_10y' },
  { id: 'share_age_65plus' },
  { id: 'share_foreign' },
  { id: 'hh_avg_size' },
  { id: 'ent_jobs_per_1000', log: true },
  { id: 'tax_np_mean_taxable_income', log: true },
  { id: 'edu_share_tertiary' },
  { id: 'nrw_share_bloc_left' },
  { id: 'area_share_settlement' },
  { id: 'geo_elev_mean' },
];
export const DEFAULT_SIM: SimMetric[] = SIMILAR_METRICS.map((m) => ({ id: m.id, w: 1, log: !!m.log }));

export const W_MIN = 0.5;
export const W_MAX = 3;
export const W_STEP = 0.5;
export const MAX_SIM_METRICS = 30;

// ---------------------------------------------------------------- spec in the URL
/** 'id:w' or 'id:w:l' (log scale), comma separated. */
export function serializeSim(spec: SimMetric[]): string {
  return spec.map((m) => `${m.id}:${+m.w.toFixed(1)}${m.log ? ':l' : ''}`).join(',');
}
export const isDefaultSim = (spec: SimMetric[]) => serializeSim(spec) === serializeSim(DEFAULT_SIM);

export function parseSim(s: string | undefined): SimMetric[] | null {
  if (!s) return null;
  const out: SimMetric[] = [];
  for (const part of s.split(',')) {
    const p = part.split(':');
    if (!/^[a-z0-9_]+$/i.test(p[0] ?? '') || out.some((m) => m.id === p[0])) continue;
    const w = Number(p[1]);
    out.push({
      id: p[0],
      w: Number.isFinite(w) ? Math.max(W_MIN, Math.min(W_MAX, Math.round(w / W_STEP) * W_STEP)) : 1,
      log: p[2] === 'l',
    });
    if (out.length >= MAX_SIM_METRICS) break;
  }
  return out.length >= 2 ? out : null;
}

// ---------------------------------------------------------------- z-score columns
const zCache = new WeakMap<object, { lin?: Float64Array | null; log?: Float64Array | null }>();
/** z-scores of a column (NaN where missing; on a log scale non-positive values count as missing).
 *  null when fewer than 3 values or no spread. Cached per column. */
export function zColumn(v: (number | null)[], log: boolean): Float64Array | null {
  let c = zCache.get(v);
  if (!c) zCache.set(v, (c = {}));
  const key = log ? 'log' : 'lin';
  if (key in c) return c[key] ?? null;
  const x = new Float64Array(v.length);
  let n = 0, sum = 0;
  for (let i = 0; i < v.length; i++) {
    const a = v[i];
    const y = a === null || a === undefined ? NaN : log ? (a > 0 ? Math.log10(a) : NaN) : a;
    x[i] = y;
    if (Number.isFinite(y)) {
      n++;
      sum += y;
    }
  }
  let z: Float64Array | null = null;
  if (n >= 3) {
    const mu = sum / n;
    let ss = 0;
    for (const y of x) if (Number.isFinite(y)) ss += (y - mu) ** 2;
    const sd = Math.sqrt(ss / n);
    if (sd > 0) {
      z = x;
      for (let i = 0; i < z.length; i++) z[i] = (z[i] - mu) / sd;
    }
  }
  c[key] = z;
  return z;
}

/** Skewed, strictly positive metric: a log scale compares it more sensibly (suggested when adding). */
export function looksSkewed(v: (number | null)[]): boolean {
  const xs = v.filter((a): a is number => a !== null && a !== undefined);
  if (xs.length < 30 || xs.some((a) => a <= 0)) return false;
  const mu = xs.reduce((a, b) => a + b, 0) / xs.length;
  const sd = Math.sqrt(xs.reduce((a, b) => a + (b - mu) ** 2, 0) / xs.length);
  if (!(sd > 0)) return false;
  const sk = xs.reduce((a, b) => a + ((b - mu) / sd) ** 3, 0) / xs.length;
  return sk > 2;
}

/** The latest-values column of a metric from the loaded theme files of the level. */
export function columnOf(pl: PlaceLevel, files: Record<string, ColumnFile>, id: string) {
  const c = pl.core.metrics[id];
  if (c) return c;
  for (const f of Object.values(files)) if (f.metrics[id]) return f.metrics[id];
  return null;
}

// ---------------------------------------------------------------- similarity
export interface SimPart {
  id: string;
  w: number;
  /** values before any log transform */
  xi: number;
  xj: number;
  /** |z difference| in standard deviations */
  dz: number;
  /** share of the squared distance (sums to 1 over the metrics; 0 when the places are identical) */
  share: number;
}
export interface Similar {
  i: number;
  /** weighted root mean squared z difference over the metrics both places have */
  d: number;
  n: number;
  parts: SimPart[];
}
export interface SimResult {
  /** metrics of the vector that the place has a value for, and that were usable */
  used: string[];
  /** metrics of the spec without values for this place or without a column (file not loaded) */
  skipped: string[];
  list: Similar[];
  /** candidates left after `allow` */
  pool: number;
}

/** Nearest units by weighted z-scores (missing values skipped; at least 70% of the metrics shared).
 *  `allow` restricts the candidates (e.g. to those near a hub). */
export function similarPlaces(
  pl: PlaceLevel, i: number,
  opts: { spec?: SimMetric[]; files?: Record<string, ColumnFile>; allow?: (j: number) => boolean; k?: number } = {},
): SimResult {
  const spec = opts.spec ?? DEFAULT_SIM;
  const k = opts.k ?? 6;
  const cols: { id: string; w: number; z: Float64Array; v: (number | null)[] }[] = [];
  const used: string[] = [];
  const skipped: string[] = [];
  for (const m of spec) {
    const c = columnOf(pl, opts.files ?? {}, m.id);
    const z = c ? zColumn(c.v, m.log) : null;
    if (!c || !z || !Number.isFinite(z[i])) {
      skipped.push(m.id);
      continue;
    }
    cols.push({ id: m.id, w: m.w, z, v: c.v });
    used.push(m.id);
  }
  const need = Math.ceil(0.7 * cols.length);
  const found: { j: number; d: number; n: number }[] = [];
  let pool = 0;
  if (cols.length >= 2) {
    for (let j = 0; j < pl.units.length; j++) {
      if (j === i || (opts.allow && !opts.allow(j))) continue;
      pool++;
      let s = 0, ws = 0, n = 0;
      for (const c of cols) {
        const b = c.z[j];
        if (!Number.isFinite(b)) continue;
        s += c.w * (c.z[i] - b) ** 2;
        ws += c.w;
        n++;
      }
      if (n >= need && n > 0) found.push({ j, d: Math.sqrt(s / ws), n });
    }
    found.sort((a, b) => a.d - b.d);
  }
  const list = found.slice(0, k).map(({ j, d, n }) => {
    const raw: { id: string; w: number; xi: number; xj: number; dz: number; t: number }[] = [];
    let tot = 0;
    for (const c of cols) {
      const b = c.z[j];
      if (!Number.isFinite(b)) continue;
      const dz = Math.abs(c.z[i] - b);
      const t = c.w * dz * dz;
      tot += t;
      raw.push({ id: c.id, w: c.w, xi: c.v[i] as number, xj: c.v[j] as number, dz, t });
    }
    const parts = raw.map((r) => ({ id: r.id, w: r.w, xi: r.xi, xj: r.xj, dz: r.dz, share: tot > 0 ? r.t / tot : 0 }));
    return { i: j, d, n, parts };
  });
  return { used, skipped, list, pool };
}

/** Pairs of the metrics in use that move together (Pearson r of the z-scores over units with both
 *  values), |r| >= thr: they count about twice in the distance. Strongest first. */
export function correlatedPairs(
  pl: PlaceLevel, spec: SimMetric[], files: Record<string, ColumnFile>, thr = 0.8,
): { a: string; b: string; r: number }[] {
  const zs: { id: string; z: Float64Array }[] = [];
  for (const m of spec) {
    const c = columnOf(pl, files, m.id);
    const z = c ? zColumn(c.v, m.log) : null;
    if (z) zs.push({ id: m.id, z });
  }
  const out: { a: string; b: string; r: number }[] = [];
  for (let p = 0; p < zs.length; p++)
    for (let q = p + 1; q < zs.length; q++) {
      const x = zs[p].z, y = zs[q].z;
      let n = 0, sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0;
      for (let j = 0; j < x.length; j++) {
        const a = x[j], b = y[j];
        if (!Number.isFinite(a) || !Number.isFinite(b)) continue;
        n++; sx += a; sy += b; sxx += a * a; syy += b * b; sxy += a * b;
      }
      if (n < 30) continue;
      const den = Math.sqrt((sxx - (sx * sx) / n) * (syy - (sy * sy) / n));
      if (!(den > 0)) continue;
      const r = (sxy - (sx * sy) / n) / den;
      if (Math.abs(r) >= thr) out.push({ a: zs[p].id, b: zs[q].id, r });
    }
  return out.sort((u, v) => Math.abs(v.r) - Math.abs(u.r));
}

/** Metrics offered in the editor: national coverage, a value per unit at the level, no per-vote series. */
export function simCandidates(metrics: MetricMeta[], level: string): MetricMeta[] {
  return metrics.filter((m) => !m.hidden && !m.per_vote && m.coverage === 'national' && m.levels.includes(level));
}

// ---------------------------------------------------------------- "near" restriction
export type NearMode = 'km' | 'pt' | 'car';
/** anchor: 'self' (the profile's place), 'p-<id>' (another place of the level), 'h-<hub slug>' (a hub) */
export interface Near {
  anchor: string;
  mode: NearMode;
  n: number;
}
export const NEAR_MAX = { km: 200, pt: 180, car: 180 } as const;

export const serializeNear = (n: Near) => `${n.anchor}:${n.mode}:${Math.round(n.n)}`;
export function parseNear(s: string | undefined): Near | null {
  if (!s) return null;
  const p = s.split(':');
  if (p.length !== 3 || !/^(self|[ph]-[A-Za-z0-9_.-]+)$/.test(p[0])) return null;
  const mode = p[1];
  const n = Number(p[2]);
  if ((mode !== 'km' && mode !== 'pt' && mode !== 'car') || !Number.isFinite(n) || n <= 0) return null;
  if (p[0].startsWith('h-') === (mode === 'km')) return null; // hubs take minutes, places kilometres
  return { anchor: p[0], mode, n: Math.min(n, NEAR_MAX[mode]) };
}

const R_KM = 6371;
export function haversineKm(a: [number, number], b: [number, number]): number {
  const rad = Math.PI / 180;
  const dLat = (b[1] - a[1]) * rad, dLon = (b[0] - a[0]) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * R_KM * Math.asin(Math.sqrt(h));
}

/** Distance (km) or travel time (min) of every unit of the level to the anchor; null per unit where there is
 *  none, and null overall while the needed data is not loaded. */
export function nearDistances(
  pl: PlaceLevel, idx: number, near: Near, rows: Map<string, UnitRow> | null, reach: ReachTimes | null,
): (number | null)[] | null {
  if (near.mode === 'km') {
    if (!rows) return null;
    const at = (id: string): [number, number] | null => rows.get(refOf(pl.level, id))?.label ?? null;
    const from = at(near.anchor === 'self' ? pl.units[idx] : near.anchor.slice(2));
    if (!from) return null;
    return pl.units.map((u) => {
      const p = at(u);
      return p ? haversineKm(from, p) : null;
    });
  }
  if (!reach || pl.level !== 'gemeinde') return null;
  const slug = near.anchor.slice(2);
  const arr = near.mode === 'car' ? reach.car[slug] : (reach.pt_station?.[slug] ?? reach.pt[slug]);
  if (!arr) return null;
  const k = new Map(reach.units.map((u, q) => [u, q]));
  return pl.units.map((u) => {
    const q = k.get(u);
    return q === undefined ? null : (arr[q] ?? null);
  });
}
