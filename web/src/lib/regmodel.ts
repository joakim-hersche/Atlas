// Regression panel (D34): model state in the URL hash, presets, sample building and readable effects.
// The estimation itself is in regress.ts.
//
// Hash keys of the route #v=regress (all optional; defaults left out):
//   ry=<metric id>            outcome; 'log:<id>' for log10 of the outcome
//   rx=<id>,log:<id>,…        1–6 explanatory variables, each optionally log10
//   rc=lang | kt              controls: language region dummies (BFS Sprachgebiet) or canton fixed effects
//   rw=pop                    population weights (pop_total of the year nearest to the outcome's period)
//   rse=hc1 | ols             standard errors (default: clustered by canton, CR1)
//   rd=1                      leave out values flagged △ (small numbers) or M (majority election)
//   rs=f                      sample = units matching the active filters (default: all units)
// The level is the app's `l` key; the selected unit is `sel`.
import type { SeType } from './regress';

export interface RegVar {
  id: string;
  log: boolean;
}
export type Control = 'none' | 'lang' | 'kt';
export interface RegSpec {
  y: RegVar;
  xs: RegVar[];
  ctrl: Control;
  weights: boolean;
  se: SeType;
  drop: boolean;
  filtered: boolean;
}
export const MAX_X = 6;
export const REG_KEYS = ['ry', 'rx', 'rc', 'rw', 'rse', 'rd', 'rs'];

const parseVar = (s: string): RegVar | null => {
  const log = s.startsWith('log:');
  const id = log ? s.slice(4) : s;
  return /^[a-z0-9_]+$/i.test(id) ? { id, log } : null;
};
const varKey = (v: RegVar) => (v.log ? `log:${v.id}` : v.id);

export function parseSpec(p: Record<string, string>): RegSpec | null {
  const y = p.ry ? parseVar(p.ry) : null;
  if (!y) return null;
  const xs = (p.rx ?? '').split(',').filter(Boolean).map(parseVar).filter((v): v is RegVar => v !== null).slice(0, MAX_X);
  return {
    y,
    xs,
    ctrl: p.rc === 'lang' || p.rc === 'kt' ? p.rc : 'none',
    weights: p.rw === 'pop',
    se: p.rse === 'hc1' || p.rse === 'ols' ? p.rse : 'cluster',
    drop: p.rd === '1',
    filtered: p.rs === 'f',
  };
}

export function specParams(s: RegSpec): Record<string, string> {
  const out: Record<string, string> = { ry: varKey(s.y) };
  if (s.xs.length) out.rx = s.xs.map(varKey).join(',');
  if (s.ctrl !== 'none') out.rc = s.ctrl;
  if (s.weights) out.rw = 'pop';
  if (s.se !== 'cluster') out.rse = s.se;
  if (s.drop) out.rd = '1';
  if (s.filtered) out.rs = 'f';
  return out;
}

export interface RegPreset {
  slug: string;
  label: string;
  spec: RegSpec;
}
const base = { weights: false, se: 'cluster' as SeType, drop: false, filtered: false };
export const REG_PRESETS: RegPreset[] = [
  {
    slug: 'left', label: 'rg.p.left',
    spec: { ...base, y: { id: 'nrw_share_left_bloc', log: false }, xs: [{ id: 'tax_np_mean_taxable_income', log: true }, { id: 'geo_pop_density', log: true }], ctrl: 'lang' },
  },
  {
    slug: 'svp', label: 'rg.p.svp',
    spec: { ...base, y: { id: 'nrw_share_svp', log: false }, xs: [{ id: 'geo_pop_density', log: true }, { id: 'share_foreign', log: false }, { id: 'tax_np_mean_taxable_income', log: true }], ctrl: 'none' },
  },
  {
    slug: 'turnout', label: 'rg.p.turnout',
    spec: { ...base, y: { id: 'nrw_turnout', log: false }, xs: [{ id: 'tax_np_mean_taxable_income', log: true }, { id: 'share_age_65plus', log: false }], ctrl: 'none' },
  },
];

/** The last model shown in this session (restored when the panel is opened again from the menu). */
export let lastParams: Record<string, string> | null = null;
export const rememberParams = (p: Record<string, string>) => (lastParams = p);

/** Middle year of a period label: '2023' → 2023, '2023-2025' → 2024, '2013/18' → 2015 (rounded down),
 *  '2026-06-14#6870' → 2026. null when there is no year. */
export function yearOf(period: string): number | null {
  const m = period.match(/(\d{4})(?:(?:-|–)(\d{4})|\/(\d{2}))?/);
  if (!m) return null;
  const a = Number(m[1]);
  if (m[2] && !period.includes('#') && /^\d{4}-\d{4}$/.test(period)) return Math.floor((a + Number(m[2])) / 2);
  if (m[3]) return Math.floor((a + Math.floor(a / 100) * 100 + Number(m[3])) / 2);
  return a;
}

/** Period of a list nearest to a year (ties: the later one). */
export function nearestPeriod(periods: string[], year: number): string | null {
  let best: string | null = null;
  let bd = Infinity;
  for (const p of periods) {
    const y = yearOf(p);
    if (y === null) continue;
    const d = Math.abs(y - year);
    if (d < bd || (d === bd && best !== null && (yearOf(best) ?? 0) < y)) {
      bd = d;
      best = p;
    }
  }
  return best;
}

/** A readable step of x for "per +step" effects: a power of ten at or below the standard deviation
 *  (income sd 20'000 → 10'000; density sd 1'500 → 1'000), at most 10 for shares in %. */
export function stepFor(sd: number, isShare: boolean): number {
  if (!(sd > 0)) return 1;
  const s = 10 ** Math.floor(Math.log10(sd));
  return isShare ? Math.min(10, s) : s;
}

/** Effect of x on y in the outcome's units, for a coefficient b on the model scale.
 *  kind 'abs': change of y in its unit; 'pct': % change of y (log outcome).
 *  xStep: 'pct10' = +10 % of x (log x), else a number (+step in x's unit). */
export function effectOf(b: number, xLog: boolean, yLog: boolean, step: number): { value: number; kind: 'abs' | 'pct' } {
  const dx = xLog ? Math.log10(1.1) : step; // change of the regressor on the model scale
  const d = b * dx;
  return yLog ? { value: (10 ** d - 1) * 100, kind: 'pct' } : { value: d, kind: 'abs' };
}
