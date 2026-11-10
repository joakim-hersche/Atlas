// Shareable view state in the URL hash:
//   #mode=compare&m=geo_pop_density&b=share_foreign&cls=q&pop=1000-50000&reach=pt&t=45&sel=261
// A bare single word (#compare, #density-foreigners, …) is accepted too: some hosts pass only that.
import type { Method } from './classify';

export type ReachMode = 'off' | 'pt' | 'car';
export type Mode = 'single' | 'compare';

export interface ViewState {
  mode: Mode;
  metric: string | null;
  metricB: string | null;
  cls: Method;
  popMin: number | null;
  popMax: number | null;
  reach: ReachMode;
  t: number;
  sel: string | null;
  /** preset slug from a bare '#word' hash */
  preset: string | null;
}

export const T_MAX = 180;
const CLS: Record<string, Method> = { q: 'quantile', e: 'equal', c: 'continuous' };
const CLS_KEY: Record<Method, string> = { quantile: 'q', equal: 'e', continuous: 'c' };

export function readHash(): ViewState {
  const raw = location.hash.replace(/^#/, '');
  const word = /^[a-z][a-z0-9-]*$/i.test(raw) ? raw.toLowerCase() : null;
  const q = new URLSearchParams(word ? '' : raw);
  const num = (s: string | undefined) => (s && /^\d+$/.test(s) ? Number(s) : null);
  const [a, b] = (q.get('pop') ?? '').split('-');
  const reach = q.get('reach');
  const t = num(q.get('t') ?? undefined);
  const mode: Mode = q.get('mode') === 'compare' || (word !== null && word !== 'single') ? 'compare' : 'single';
  return {
    mode,
    metric: q.get('m'),
    metricB: q.get('b'),
    cls: CLS[q.get('cls') ?? ''] ?? 'quantile',
    popMin: num(a),
    popMax: num(b),
    reach: reach === 'pt' || reach === 'car' ? reach : 'off',
    t: t === null ? 60 : Math.min(T_MAX, t),
    sel: q.get('sel'),
    preset: word && word !== 'single' && word !== 'compare' ? word : word === 'compare' ? '' : null,
  };
}

export function writeHash(s: Omit<ViewState, 'preset'>): void {
  const q = new URLSearchParams();
  if (s.mode === 'compare') q.set('mode', 'compare');
  if (s.metric) q.set('m', s.metric);
  if (s.mode === 'compare' && s.metricB) q.set('b', s.metricB);
  if (s.cls !== 'quantile') q.set('cls', CLS_KEY[s.cls]);
  if (s.popMin !== null || s.popMax !== null) q.set('pop', `${s.popMin ?? ''}-${s.popMax ?? ''}`);
  if (s.mode === 'single' && s.reach !== 'off') {
    q.set('reach', s.reach);
    q.set('t', String(Math.round(s.t)));
  }
  if (s.sel) q.set('sel', s.sel);
  const h = '#' + q.toString();
  if (h !== location.hash) history.replaceState(null, '', h === '#' ? location.pathname + location.search : h);
}
