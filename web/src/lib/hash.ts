// Minimal shareable view state in the URL hash: #m=pop_total&pop=1000-50000&reach=pt&t=45
export type ReachMode = 'off' | 'pt' | 'car';

export interface ViewState {
  metric: string | null;
  popMin: number | null;
  popMax: number | null;
  reach: ReachMode;
  t: number;
  sel: string | null;
}

export const T_MAX = 180;

export function readHash(): ViewState {
  const q = new URLSearchParams(location.hash.replace(/^#/, ''));
  const num = (s: string | undefined) => (s && /^\d+$/.test(s) ? Number(s) : null);
  const [a, b] = (q.get('pop') ?? '').split('-');
  const reach = q.get('reach');
  const t = num(q.get('t') ?? undefined);
  return {
    metric: q.get('m'),
    popMin: num(a),
    popMax: num(b),
    reach: reach === 'pt' || reach === 'car' ? reach : 'off',
    t: t === null ? 60 : Math.min(T_MAX, t),
    sel: q.get('sel'),
  };
}

export function writeHash(s: ViewState): void {
  const q = new URLSearchParams();
  if (s.metric) q.set('m', s.metric);
  if (s.popMin !== null || s.popMax !== null) q.set('pop', `${s.popMin ?? ''}-${s.popMax ?? ''}`);
  if (s.reach !== 'off') {
    q.set('reach', s.reach);
    q.set('t', String(Math.round(s.t)));
  }
  if (s.sel) q.set('sel', s.sel);
  const h = '#' + q.toString();
  if (h !== location.hash) history.replaceState(null, '', h === '#' ? location.pathname + location.search : h);
}
