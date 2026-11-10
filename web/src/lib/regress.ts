// Ordinary least squares for the regression panel (D34), with no dependencies (checked by
// web/scripts/regress-check.mjs against numpy).
//
// Method
// - Optional weights w: weighted least squares, i.e. OLS on rows multiplied by sqrt(w).
// - The design columns are scaled to unit root-mean-square before a Householder QR decomposition
//   (stable for n ≈ 2,100 and k ≤ ~40, e.g. 25 canton dummies). A column whose remaining norm after
//   the previous columns is below 1e-9 of its own norm is collinear: it is left out (NaN in the
//   result) and reported, instead of producing huge, meaningless numbers.
// - Standard errors, with B = (X'WX)⁻¹ and e the residuals, x̃ᵢ = √wᵢ xᵢ, ẽᵢ = √wᵢ eᵢ:
//   'ols'     conventional: s² B, s² = Σẽ² / (n − k); t with n − k degrees of freedom.
//   'hc1'     heteroskedasticity-robust: n/(n − k) · B (Σ x̃ᵢx̃ᵢ' ẽᵢ²) B; df n − k (Stata `vce(robust)`).
//   'cluster' cluster-robust CR1: G/(G − 1) · (n − 1)/(n − k) · B (Σ_g u_g u_g') B with
//             u_g = Σ_{i∈g} x̃ᵢ ẽᵢ; df G − 1 (Stata `regress …, vce(cluster c)`; k counts every
//             estimated parameter, fixed-effect dummies included).
// - R² = 1 − Σwe² / Σw(y − ȳ_w)²; adjusted R² = 1 − (1 − R²)(n − 1)/(n − k).
// - Standardized coefficient β = b · sd_w(x) / sd_w(y) on the estimation sample (transformed scale).

export type SeType = 'cluster' | 'hc1' | 'ols';

export interface OlsInput {
  y: ArrayLike<number>;
  /** design columns (the first is normally the intercept), each of length n */
  X: ArrayLike<number>[];
  w?: ArrayLike<number> | null;
  /** cluster id per row (any integers), required for se = 'cluster' */
  cluster?: ArrayLike<number> | null;
  se: SeType;
  /** confidence level of the intervals (default 0.95) */
  level?: number;
}

export interface OlsResult {
  n: number;
  /** estimated parameters (rank of the design) */
  k: number;
  /** degrees of freedom of the t distribution used for p-values and intervals */
  df: number;
  /** number of clusters (cluster standard errors only) */
  clusters: number | null;
  coef: number[];
  se: number[];
  t: number[];
  p: number[];
  lo: number[];
  hi: number[];
  /** standardized coefficients (NaN for the intercept) */
  beta: number[];
  /** design columns left out because they are collinear with earlier ones */
  collinear: boolean[];
  r2: number;
  r2adj: number;
  /** residual standard error, sqrt(Σwe² / (n − k)) (weighted residuals) */
  rmse: number;
  /** weighted standard deviation of the residuals (no df correction; for the map classes) */
  residSd: number;
  fitted: Float64Array;
  resid: Float64Array;
  tcrit: number;
}

export class OlsError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export function ols(inp: OlsInput): OlsResult {
  const n = inp.y.length;
  const P = inp.X.length;
  const w = inp.w ?? null;
  for (const c of inp.X) if (c.length !== n) throw new OlsError('shape', 'design columns differ in length');
  const sw = new Float64Array(n);
  let wsum = 0;
  for (let i = 0; i < n; i++) {
    const wi = w ? w[i] : 1;
    if (!(wi > 0) || !Number.isFinite(wi)) throw new OlsError('weight', 'weights must be positive');
    sw[i] = Math.sqrt(wi);
    wsum += wi;
  }

  // scaled, weighted design columns
  const A: Float64Array[] = [];
  const scale: number[] = [];
  for (let j = 0; j < P; j++) {
    const src = inp.X[j];
    const col = new Float64Array(n);
    let ss = 0;
    for (let i = 0; i < n; i++) {
      const v = src[i] * sw[i];
      if (!Number.isFinite(v)) throw new OlsError('nan', 'design contains a missing value');
      col[i] = v;
      ss += v * v;
    }
    const s = Math.sqrt(ss / n) || 1;
    for (let i = 0; i < n; i++) col[i] /= s;
    A.push(col);
    scale.push(s);
  }
  const yt = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    yt[i] = inp.y[i] * sw[i];
    if (!Number.isFinite(yt[i])) throw new OlsError('nan', 'outcome contains a missing value');
  }

  // Householder QR, column by column, skipping collinear columns
  const vs: Float64Array[] = [];
  const taus: number[] = [];
  const Rcols: Float64Array[] = []; // accepted column c: R[0..c]
  const acc: number[] = []; // design index of accepted column c
  const collinear = new Array<boolean>(P).fill(false);
  const applyAll = (x: Float64Array, upto: number) => {
    for (let r = 0; r < upto; r++) {
      const v = vs[r];
      let d = 0;
      for (let i = r; i < n; i++) d += v[i - r] * x[i];
      d *= taus[r];
      if (d !== 0) for (let i = r; i < n; i++) x[i] -= d * v[i - r];
    }
  };
  for (let j = 0; j < P; j++) {
    const r = acc.length;
    const col = Float64Array.from(A[j]);
    applyAll(col, r);
    let nrm = 0;
    for (let i = r; i < n; i++) nrm += col[i] * col[i];
    nrm = Math.sqrt(nrm);
    if (r >= n || nrm <= 1e-9 * Math.sqrt(n)) {
      collinear[j] = true;
      continue;
    }
    const alpha = col[r] > 0 ? -nrm : nrm;
    const v = new Float64Array(n - r);
    for (let i = r; i < n; i++) v[i - r] = col[i];
    v[0] -= alpha;
    let vv = 0;
    for (let i = 0; i < v.length; i++) vv += v[i] * v[i];
    const R = new Float64Array(r + 1);
    for (let i = 0; i < r; i++) R[i] = col[i];
    R[r] = alpha;
    vs.push(v);
    taus.push(vv > 0 ? 2 / vv : 0);
    Rcols.push(R);
    acc.push(j);
  }
  const k = acc.length;
  if (n - k < 1) throw new OlsError('dof', 'too few units for the number of parameters');

  // Q'y and back substitution R b = (Q'y)[0..k)
  const qty = Float64Array.from(yt);
  applyAll(qty, k);
  const R = (i: number, c: number) => (i <= c ? Rcols[c][i] : 0);
  const bs = new Float64Array(k);
  for (let i = k - 1; i >= 0; i--) {
    let s = qty[i];
    for (let c = i + 1; c < k; c++) s -= R(i, c) * bs[c];
    bs[i] = s / R(i, i);
  }
  // R⁻¹ (upper triangular), B = R⁻¹ R⁻ᵀ = (A'A)⁻¹ in the scaled space
  const Ri: Float64Array[] = Array.from({ length: k }, () => new Float64Array(k)); // Ri[i][c]
  for (let c = 0; c < k; c++) {
    Ri[c][c] = 1 / R(c, c);
    for (let i = c - 1; i >= 0; i--) {
      let s = 0;
      for (let m = i + 1; m <= c; m++) s += R(i, m) * Ri[m][c];
      Ri[i][c] = -s / R(i, i);
    }
  }
  const B: Float64Array[] = Array.from({ length: k }, () => new Float64Array(k));
  for (let a = 0; a < k; a++)
    for (let b = a; b < k; b++) {
      let s = 0;
      for (let m = Math.max(a, b); m < k; m++) s += Ri[a][m] * Ri[b][m];
      B[a][b] = s;
      B[b][a] = s;
    }

  // coefficients on the original scale, fitted values and residuals
  const coefAcc = acc.map((j, c) => bs[c] / scale[j]);
  const fitted = new Float64Array(n);
  const resid = new Float64Array(n);
  let ssr = 0;
  let ybar = 0;
  for (let i = 0; i < n; i++) ybar += (w ? w[i] : 1) * inp.y[i];
  ybar /= wsum;
  let sst = 0;
  for (let i = 0; i < n; i++) {
    let f = 0;
    for (let c = 0; c < k; c++) f += inp.X[acc[c]][i] * coefAcc[c];
    fitted[i] = f;
    resid[i] = inp.y[i] - f;
    const wi = w ? w[i] : 1;
    ssr += wi * resid[i] * resid[i];
    sst += wi * (inp.y[i] - ybar) ** 2;
  }

  // variance of the scaled coefficients
  let V: Float64Array[];
  let df: number;
  let clusters: number | null = null;
  const sandwich = (M: Float64Array[], f: number) => {
    const BM: Float64Array[] = Array.from({ length: k }, () => new Float64Array(k));
    for (let a = 0; a < k; a++)
      for (let b = 0; b < k; b++) {
        let s = 0;
        for (let m = 0; m < k; m++) s += B[a][m] * M[m][b];
        BM[a][b] = s;
      }
    const out: Float64Array[] = Array.from({ length: k }, () => new Float64Array(k));
    for (let a = 0; a < k; a++)
      for (let b = 0; b < k; b++) {
        let s = 0;
        for (let m = 0; m < k; m++) s += BM[a][m] * B[m][b];
        out[a][b] = s * f;
      }
    return out;
  };
  const scoreRow = (i: number, g: Float64Array) => {
    const e = sw[i] * resid[i];
    for (let c = 0; c < k; c++) g[c] = A[acc[c]][i] * e;
  };
  if (inp.se === 'ols') {
    const s2 = ssr / (n - k);
    V = B.map((row) => row.map((x) => x * s2));
    df = n - k;
  } else if (inp.se === 'hc1') {
    const M: Float64Array[] = Array.from({ length: k }, () => new Float64Array(k));
    const g = new Float64Array(k);
    for (let i = 0; i < n; i++) {
      scoreRow(i, g);
      for (let a = 0; a < k; a++) for (let b = 0; b < k; b++) M[a][b] += g[a] * g[b];
    }
    V = sandwich(M, n / (n - k));
    df = n - k;
  } else {
    const cl = inp.cluster;
    if (!cl || cl.length !== n) throw new OlsError('cluster', 'cluster ids missing');
    const sums = new Map<number, Float64Array>();
    const g = new Float64Array(k);
    for (let i = 0; i < n; i++) {
      scoreRow(i, g);
      let u = sums.get(cl[i]);
      if (!u) sums.set(cl[i], (u = new Float64Array(k)));
      for (let a = 0; a < k; a++) u[a] += g[a];
    }
    const G = sums.size;
    if (G < 2) throw new OlsError('clusters', 'clustered standard errors need at least two clusters');
    const M: Float64Array[] = Array.from({ length: k }, () => new Float64Array(k));
    for (const u of sums.values()) for (let a = 0; a < k; a++) for (let b = 0; b < k; b++) M[a][b] += u[a] * u[b];
    V = sandwich(M, (G / (G - 1)) * ((n - 1) / (n - k)));
    df = G - 1;
    clusters = G;
  }

  const level = inp.level ?? 0.95;
  const tcrit = tQuantile(1 - level, df);
  // weighted standard deviations (sample of the regression), for standardized coefficients
  const wsd = (x: ArrayLike<number>) => {
    let m = 0;
    for (let i = 0; i < n; i++) m += (w ? w[i] : 1) * x[i];
    m /= wsum;
    let s = 0;
    for (let i = 0; i < n; i++) s += (w ? w[i] : 1) * (x[i] - m) ** 2;
    return Math.sqrt(s / wsum);
  };
  const sdY = wsd(inp.y);
  const nanArr = () => new Array<number>(P).fill(NaN);
  const coef = nanArr(), se = nanArr(), t = nanArr(), p = nanArr(), lo = nanArr(), hi = nanArr(), beta = nanArr();
  acc.forEach((j, c) => {
    const b = coefAcc[c];
    const s = Math.sqrt(Math.max(0, V[c][c])) / scale[j];
    coef[j] = b;
    se[j] = s;
    t[j] = b / s;
    p[j] = tTwoSided(b / s, df);
    lo[j] = b - tcrit * s;
    hi[j] = b + tcrit * s;
    const sx = wsd(inp.X[j]);
    beta[j] = sx > 0 && sdY > 0 ? (b * sx) / sdY : NaN;
  });
  const r2 = sst > 0 ? 1 - ssr / sst : NaN;
  let rs = 0;
  let rm = 0;
  for (let i = 0; i < n; i++) rm += (w ? w[i] : 1) * resid[i];
  rm /= wsum;
  for (let i = 0; i < n; i++) rs += (w ? w[i] : 1) * (resid[i] - rm) ** 2;
  return {
    n, k, df, clusters, coef, se, t, p, lo, hi, beta, collinear,
    r2, r2adj: 1 - ((1 - r2) * (n - 1)) / (n - k), rmse: Math.sqrt(ssr / (n - k)), residSd: Math.sqrt(rs / wsum),
    fitted, resid, tcrit,
  };
}

// ---------------------------------------------------------------- Student t distribution
function lnGamma(x: number): number {
  // Lanczos approximation (g = 7, n = 9), accurate to ~1e-15 for x > 0
  const c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
    12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lnGamma(1 - x);
  x -= 1;
  let a = c[0];
  const t = x + 7.5;
  for (let i = 1; i < 9; i++) a += c[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

/** Continued fraction of the incomplete beta function (modified Lentz). */
function betacf(x: number, a: number, b: number): number {
  const FPMIN = 1e-300;
  const qab = a + b, qap = a + 1, qam = a - 1;
  let c = 1;
  let d = 1 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= 300; m++) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < 1e-15) break;
  }
  return h;
}

/** Regularized incomplete beta function I_x(a, b). */
export function incBeta(x: number, a: number, b: number): number {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const bt = Math.exp(lnGamma(a + b) - lnGamma(a) - lnGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? (bt * betacf(x, a, b)) / a : 1 - (bt * betacf(1 - x, b, a)) / b;
}

/** Two-sided p-value P(|T| ≥ |t|) of Student's t with df degrees of freedom. */
export function tTwoSided(t: number, df: number): number {
  if (!Number.isFinite(t)) return Number.isNaN(t) ? NaN : 0;
  return incBeta(df / (df + t * t), df / 2, 0.5);
}

/** t such that P(|T| ≥ t) = alpha (two-sided critical value), by bisection. */
export function tQuantile(alpha: number, df: number): number {
  let lo = 0;
  let hi = 1;
  while (tTwoSided(hi, df) > alpha && hi < 1e7) hi *= 2;
  for (let it = 0; it < 200; it++) {
    const mid = (lo + hi) / 2;
    if (tTwoSided(mid, df) > alpha) lo = mid;
    else hi = mid;
    if (hi - lo < 1e-12 * hi) break;
  }
  return (lo + hi) / 2;
}
