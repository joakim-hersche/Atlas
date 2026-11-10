// Numeric check of the in-browser OLS (src/lib/regress.ts) against an independent computation.
//   node web/scripts/regress-check.mjs            (from the repository root, Node ≥ 22.18: imports .ts directly)
// 1. A hand-checked example (y = 0.8 + 1.3 x, conventional standard error 0.1732).
// 2. A synthetic data set (n = 300, 4 regressors, 6 fixed-effect dummies, 15 clusters, weights)
//    compared with numpy (least squares by numpy.linalg.lstsq; conventional, HC1 and CR1 standard
//    errors written out in numpy; t-distribution p-values by numerical integration of the density).
//    Uses /home/user/Atlas/.venv/bin/python if present, else python3 with numpy; skipped without numpy.
// Exit code 1 when any difference exceeds the tolerance.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ols, tQuantile, tTwoSided, OlsError } from '../src/lib/regress.ts';

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const close = (name, a, b, rel = 1e-8, abs = 1e-10) => {
  const ok = Math.abs(a - b) <= abs + rel * Math.max(Math.abs(a), Math.abs(b));
  if (!ok) fails++;
  return { name, ours: a, ref: b, ok };
};
const report = (title, rows) => {
  console.log(`\n${title}`);
  let worst = 0;
  for (const r of rows) {
    // relative difference over values that are not ~0 (p-values below 1e-9 are compared absolutely)
    const d = Math.abs(r.ref) > 1e-9 ? Math.abs(r.ours - r.ref) / Math.abs(r.ref) : 0;
    worst = Math.max(worst, Number.isFinite(d) ? d : 0);
    if (!r.ok) console.log(`  FAIL ${r.name}: ours ${r.ours} reference ${r.ref}`);
  }
  console.log(`  ${rows.length} values compared, ${rows.filter((r) => r.ok).length} within tolerance, largest relative difference ${worst.toExponential(2)} (values > 1e-9)`);
};

// ------------------------------------------------------------------ 1. hand-checked example
{
  const x = [0, 1, 2, 3];
  const y = [1, 2, 3, 5];
  const r = ols({ y, X: [[1, 1, 1, 1], x], se: 'ols' });
  // b = Sxy/Sxx = 6.5/5 = 1.3, a = 2.75 − 1.3·1.5 = 0.8; SSR = 0.30, s² = 0.15, Var(b) = 0.15/5;
  // SST = 8.75, R² = 1 − 0.30/8.75; t(0.975, 2) = 4.302653
  report('1. Hand example y = a + b x (4 points, conventional SE)', [
    close('a', r.coef[0], 0.8), close('b', r.coef[1], 1.3), close('se(b)', r.se[1], Math.sqrt(0.03)),
    close('se(a)', r.se[0], Math.sqrt(0.15 * (1 / 4 + 1.5 ** 2 / 5))),
    close('R²', r.r2, 1 - 0.3 / 8.75), close('t crit df=2', r.tcrit, 4.302652729, 1e-8),
  ]);
  // collinear column: reported and left out, the rest unchanged
  const c = ols({ y, X: [[1, 1, 1, 1], x, x.map((v) => 2 * v)], se: 'ols' });
  console.log(`  duplicate column flagged collinear: ${c.collinear[2] && !c.collinear[1] ? 'yes' : 'NO'}`);
  if (!c.collinear[2] || Math.abs(c.coef[1] - 1.3) > 1e-12) fails++;
  // known t-table values
  report('   t distribution (table values)', [
    close('t(.975, 1)', tQuantile(0.05, 1), 12.70620474, 1e-8),
    close('t(.975, 10)', tQuantile(0.05, 10), 2.228138852, 1e-8),
    close('t(.975, 25)', tQuantile(0.05, 25), 2.059538553, 1e-8),
    close('t(.975, 1e6)', tQuantile(0.05, 1e6), 1.959966, 1e-6),
    close('p(|T|>2, 10)', tTwoSided(2, 10), 0.07338803, 1e-6),
  ]);
}

// ------------------------------------------------------------------ 2. synthetic data vs numpy
let seed = 12345;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const norm = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
const n = 300;
const G = 15;
const cl = Array.from({ length: n }, (_, i) => i % G);
const X = [new Array(n).fill(1)];
for (let j = 0; j < 4; j++) X.push(Array.from({ length: n }, (_, i) => norm() * (j + 1) * 1000 + cl[i] * 37 + (j === 3 ? 50000 : 0)));
for (let d = 1; d <= 6; d++) X.push(cl.map((g) => (g % 7 === d ? 1 : 0)));
const w = Array.from({ length: n }, () => Math.exp(1.5 * norm()) * 1000);
const y = Array.from({ length: n }, (_, i) => 3 + 0.002 * X[1][i] - 0.0007 * X[2][i] + 0.0001 * X[4][i] + 2 * X[6][i] + norm() * (1 + (cl[i] % 3)) + 0.8 * Math.sin(cl[i]));

const cases = [];
for (const se of ['ols', 'hc1', 'cluster'])
  for (const weighted of [false, true]) cases.push({ se, weighted, r: ols({ y, X, w: weighted ? w : null, cluster: cl, se }) });

const py = [join(here, '..', '..', '.venv', 'bin', 'python'), 'python3'].find((p) => p === 'python3' || existsSync(p));
const dir = mkdtempSync(join(tmpdir(), 'regress-check-'));
writeFileSync(join(dir, 'data.json'), JSON.stringify({ y, X, w, cl }));
const code = String.raw`
import json, sys, math
import numpy as np
d = json.load(open(sys.argv[1]))
y = np.array(d['y']); X = np.array(d['X']).T; w0 = np.array(d['w']); cl = np.array(d['cl'])
def tpdf(x, df):
    return math.exp(math.lgamma((df+1)/2) - math.lgamma(df/2)) / math.sqrt(df*math.pi) * (1 + x*x/df) ** (-(df+1)/2)
def p_two(t, df):
    # 1 - 2 * integral_0^|t| of the density (composite Simpson, 200001 points)
    t = abs(t); m = 200000; h = t / m
    xs = np.linspace(0, t, m + 1)
    f = np.exp(math.lgamma((df+1)/2) - math.lgamma(df/2)) / math.sqrt(df*math.pi) * (1 + xs*xs/df) ** (-(df+1)/2)
    s = f[0] + f[-1] + 4 * f[1:-1:2].sum() + 2 * f[2:-1:2].sum()
    return 1 - 2 * s * h / 3
def tcrit(df):
    lo, hi = 0.0, 20.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if p_two(mid, df) > 0.05: lo = mid
        else: hi = mid
    return (lo + hi) / 2
out = {}
for se in ['ols', 'hc1', 'cluster']:
    for weighted in [False, True]:
        w = w0 if weighted else np.ones_like(y)
        sw = np.sqrt(w)
        Xw = X * sw[:, None]; yw = y * sw
        b = np.linalg.lstsq(Xw, yw, rcond=None)[0]
        n, k = X.shape
        e = y - X @ b; ew = e * sw
        Binv = np.linalg.inv(Xw.T @ Xw)
        if se == 'ols':
            V = Binv * (ew @ ew) / (n - k); df = n - k
        elif se == 'hc1':
            S = Xw * ew[:, None]
            V = Binv @ (S.T @ S) @ Binv * n / (n - k); df = n - k
        else:
            S = Xw * ew[:, None]
            gs = np.unique(cl); G = len(gs)
            U = np.array([S[cl == g].sum(axis=0) for g in gs])
            V = Binv @ (U.T @ U) @ Binv * (G / (G - 1)) * ((n - 1) / (n - k)); df = G - 1
        s = np.sqrt(np.diag(V))
        ybar = (w * y).sum() / w.sum()
        r2 = 1 - (w * e * e).sum() / (w * (y - ybar) ** 2).sum()
        sd = lambda v: math.sqrt((w * (v - (w * v).sum() / w.sum()) ** 2).sum() / w.sum())
        beta = [b[j] * sd(X[:, j]) / sd(y) if j > 0 else None for j in range(k)]
        tt = b / s
        out[f'{se}-{int(weighted)}'] = dict(b=b.tolist(), se=s.tolist(), t=tt.tolist(), p=[p_two(v, df) for v in tt[:5]],
            tcrit=tcrit(df), r2=r2, r2adj=1 - (1 - r2) * (n - 1) / (n - k), beta=beta, df=df, fitted=(X @ b)[:20].tolist())
print(json.dumps(out))
`;
const res = spawnSync(py, ['-c', code, join(dir, 'data.json')], { encoding: 'utf8' });
if (res.status !== 0) {
  console.log(`\n2. numpy comparison skipped (${py}: ${res.stderr.trim().split('\n').pop()})`);
} else {
  const ref = JSON.parse(res.stdout);
  console.log(`\n2. Synthetic data, n = ${n}, k = ${X.length} (intercept, 4 regressors, 6 dummies), ${G} clusters; reference: numpy ${py}`);
  for (const c of cases) {
    const R = ref[`${c.se}-${Number(c.weighted)}`];
    const rows = [];
    X.forEach((_, j) => {
      rows.push(close(`b${j}`, c.r.coef[j], R.b[j], 1e-9));
      rows.push(close(`se${j}`, c.r.se[j], R.se[j], 1e-9));
      rows.push(close(`t${j}`, c.r.t[j], R.t[j], 1e-9));
      if (j > 0) rows.push(close(`beta${j}`, c.r.beta[j], R.beta[j], 1e-9));
    });
    for (let j = 0; j < 5; j++) rows.push(close(`p${j}`, c.r.p[j], R.p[j], 1e-6, 1e-9));
    rows.push(close('t crit', c.r.tcrit, R.tcrit, 1e-7));
    rows.push(close('R²', c.r.r2, R.r2, 1e-10), close('adj R²', c.r.r2adj, R.r2adj, 1e-10), close('df', c.r.df, R.df, 0, 0));
    for (let i = 0; i < 20; i++) rows.push(close(`fitted${i}`, c.r.fitted[i], R.fitted[i], 1e-10));
    report(`   SE ${c.se}${c.weighted ? ', weighted' : ''} (df ${c.r.df})`, rows);
  }
  const c = cases.find((x) => x.se === 'cluster' && x.weighted).r;
  console.log(`   example (CR1, weighted): b1 = ${c.coef[1].toPrecision(8)}, se = ${c.se[1].toPrecision(8)}, p = ${c.p[1].toPrecision(4)}, R² = ${c.r2.toFixed(6)}`);
}
try {
  ols({ y: [1, 2], X: [[1, 1], [0, 1]], se: 'ols' });
  fails++;
} catch (e) {
  console.log(`\n3. too few units: refused (${e instanceof OlsError ? e.code : e})`);
}
console.log(fails ? `\n${fails} FAILED` : '\nAll checks passed.');
process.exit(fails ? 1 : 0);
