// Shareable view state in the URL hash. Full form (works within the page and in most links):
//   #v=compare&l=bezirk&m=geo_pop_density&b=share_foreign&s=pop_total&d=sym&cls=q&y=2015
//    &sp=lisa&fdr=1 (cluster map) | &sp=bi&b=<metric> (bivariate)  &embed=1 (compact iframe view)
//    &f=n:pop_total:1000:50000&f=c:kanton:ZH,BE&f=r:bern:pt:30&hub=bern&reach=pt&t=45&sel=261&tab=rank
// Every key is optional; defaults are left out. A bare single word (#compare, #density-foreigners, …)
// is accepted too: some hosts (the Claude artifact preview) keep only that form in shared links.
// Routes: 'map' (default) and 'compare'; later pages (profile, places, search, sources) add their own
// route names and read their extra keys from `params`. The regression panel (#v=regress) uses
// ry, rx, rc, rw, rse, rd, rs (documented in regmodel.ts), e.g.
//   #v=regress&ry=nrw_share_left_bloc&rx=log:tax_np_mean_taxable_income,log:geo_pop_density&rc=lang
import type { Method } from './classify';

export type ReachMode = 'off' | 'pt' | 'car';
export type Lang = 'en' | 'de' | 'fr';
const LANGS: Lang[] = ['en', 'de', 'fr'];
export type Display = 'choropleth' | 'symbols';
/** spatial map mode (map view): 'lisa' = cluster map, 'bi' = bivariate map of the shade metric against `b` */
export type SpatialMode = 'off' | 'lisa' | 'bi';
export type CatField = 'kanton' | 'sprachgebiet' | 'gemeindetyp' | 'stadt_land' | 'agglomeration' | 'grossregion';
export const CAT_FIELDS: CatField[] = ['kanton', 'sprachgebiet', 'gemeindetyp', 'stadt_land', 'agglomeration', 'grossregion'];

export type Filter =
  | { kind: 'num'; metric: string; lo: number | null; hi: number | null }
  | { kind: 'cat'; field: CatField; values: string[] }
  /** mode 'ptst' = PT station time towards the hub (D31), 'pt' = PT door to door, 'car' */
  | { kind: 'reach'; hub: string; mode: 'pt' | 'ptst' | 'car'; max: number };

export interface ViewState {
  route: string;
  level: string;
  metric: string | null;
  metricB: string | null;
  size: string | null;
  display: Display;
  cls: Method;
  year: string | null;
  filters: Filter[];
  hub: string;
  reach: ReachMode;
  t: number;
  sel: string | null;
  tab: string | null;
  /** UI language (English default) */
  lang: Lang;
  /** compare view: the scatter shows only the units matching the filters (else matches are highlighted) */
  only: boolean;
  /** public transport on the map: 'st' station time towards the hub (default), 'dd' door to door */
  ptm: 'st' | 'dd';
  /** federal vote shown by the per-vote metrics (vote id; null = the latest vote) */
  vote: string | null;
  /** yes share shown as the difference from the national result */
  vdiff: boolean;
  /** values resting on small numbers: shown, drawn lighter, or hidden (treated as gaps) */
  unstable: 'show' | 'light' | 'hide';
  /** spatial statistics: map mode ('sp'), false discovery rate for the cluster map ('fdr') */
  spatial: SpatialMode;
  fdr: boolean;
  /** compact embed mode (map, legend, attribution, link to the full view) for iframes ('embed=1') */
  embed: boolean;
  /** preset slug from a bare '#word' hash ('' = plain '#compare') */
  preset: string | null;
  /** keys this module does not know (for pages added later) */
  params: Record<string, string>;
}

export const T_MAX = 180;
export const DEFAULT_HUB = 'zuerich';
export const DEFAULT_LEVEL = 'gemeinde';
/** default shade: a density, never a count as a choropleth (cartographic rule; review round 1) */
export const DEFAULT_METRIC = 'geo_pop_density';
const CLS: Record<string, Method> = { q: 'quantile', e: 'equal', c: 'continuous' };
const CLS_KEY: Record<Method, string> = { quantile: 'q', equal: 'e', continuous: 'c' };
const KNOWN = new Set(['v', 'mode', 'l', 'm', 'b', 's', 'd', 'cls', 'y', 'f', 'pop', 'hub', 'reach', 't', 'sel', 'tab', 'lang', 'only', 'ptm', 'vote', 'vd', 'ur', 'sp', 'fdr', 'embed']);
/** bare words that name a route rather than a compare preset */
const ROUTE_WORDS = new Set(['map', 'single', 'compare']);

const numOrNull = (s: string | undefined) => (s !== undefined && s !== '' && Number.isFinite(Number(s)) ? Number(s) : null);

function parseFilter(raw: string): Filter | null {
  const p = raw.split(':');
  if (p[0] === 'n' && p.length === 4 && /^[a-z0-9_]+$/i.test(p[1])) {
    const lo = numOrNull(p[2]);
    const hi = numOrNull(p[3]);
    return { kind: 'num', metric: p[1], lo, hi };
  }
  if (p[0] === 'c' && p.length === 3 && (CAT_FIELDS as string[]).includes(p[1])) {
    return { kind: 'cat', field: p[1] as CatField, values: p[2] ? p[2].split(',').filter(Boolean) : [] };
  }
  if (p[0] === 'r' && p.length === 4 && (p[2] === 'pt' || p[2] === 'ptst' || p[2] === 'car')) {
    const max = numOrNull(p[3]);
    return { kind: 'reach', hub: p[1], mode: p[2], max: max === null ? 30 : Math.max(0, Math.min(T_MAX, max)) };
  }
  return null;
}

function filterKey(f: Filter): string {
  if (f.kind === 'num') return `n:${f.metric}:${f.lo ?? ''}:${f.hi ?? ''}`;
  if (f.kind === 'cat') return `c:${f.field}:${f.values.join(',')}`;
  return `r:${f.hub}:${f.mode}:${Math.round(f.max)}`;
}

export function parseHash(hash: string): ViewState {
  const raw = hash.replace(/^#/, '');
  const word = /^[a-z][a-z0-9-]*$/i.test(raw) ? raw.toLowerCase() : null;
  const q = new URLSearchParams(word ? '' : raw);
  const get = (k: string) => q.get(k) ?? undefined;
  const reach = get('reach');
  const t = numOrNull(get('t'));
  let route = get('v') ?? (get('mode') === 'compare' ? 'compare' : 'map');
  if (route === 'single') route = 'map';
  let preset: string | null = null;
  if (word !== null) {
    if (word === 'compare') { route = 'compare'; preset = ''; }
    else if (word === 'map' || word === 'single') route = 'map';
    else if (!ROUTE_WORDS.has(word)) { route = 'compare'; preset = word; }
  }
  const filters = q.getAll('f').map(parseFilter).filter((f): f is Filter => f !== null);
  // old links: pop=min-max
  const pop = get('pop');
  if (pop) {
    const [a, b] = pop.split('-');
    const lo = numOrNull(a);
    const hi = numOrNull(b);
    if (lo !== null || hi !== null) filters.unshift({ kind: 'num', metric: 'pop_total', lo, hi });
  }
  const params: Record<string, string> = {};
  for (const [k, v] of q) if (!KNOWN.has(k)) params[k] = v;
  return {
    route,
    level: get('l') ?? DEFAULT_LEVEL,
    metric: get('m') ?? null,
    metricB: get('b') ?? null,
    size: get('s') ?? null,
    display: get('d') === 'sym' ? 'symbols' : 'choropleth',
    cls: CLS[get('cls') ?? ''] ?? 'quantile',
    year: get('y') ?? null,
    filters,
    hub: get('hub') ?? DEFAULT_HUB,
    reach: reach === 'pt' || reach === 'car' ? reach : 'off',
    t: t === null ? 60 : Math.max(0, Math.min(T_MAX, t)),
    sel: get('sel') ?? null,
    tab: get('tab') ?? null,
    // an embedded frame does not read or write the visitor's stored language: English unless the link says otherwise
    lang: LANGS.includes(get('lang') as Lang) ? (get('lang') as Lang) : get('embed') === '1' ? 'en' : storedLang(),
    only: get('only') === '1',
    ptm: get('ptm') === 'dd' ? 'dd' : 'st',
    vote: /^\d+$/.test(get('vote') ?? '') ? get('vote')! : null,
    vdiff: get('vd') === '1',
    unstable: get('ur') === 'l' ? 'light' : get('ur') === 'h' ? 'hide' : 'show',
    spatial: get('sp') === 'lisa' ? 'lisa' : get('sp') === 'bi' ? 'bi' : 'off',
    fdr: get('fdr') === '1',
    embed: get('embed') === '1',
    preset,
    params,
  };
}

/** Language chosen earlier on this device (localStorage can throw or be empty: then English). */
export function storedLang(): Lang {
  try {
    const l = localStorage.getItem('gb-lang') as Lang | null;
    return l && LANGS.includes(l) ? l : 'en';
  } catch {
    return 'en';
  }
}
export function storeLang(l: Lang): void {
  try {
    localStorage.setItem('gb-lang', l);
  } catch {
    /* private mode or blocked storage: the hash still carries it */
  }
}

/** Route and the page's own keys: a change of these is a new history entry (Back returns). */
export function routeKey(s: { route: string; params: Record<string, string> }): string {
  return [s.route, s.params.id ?? '', s.params.ids ?? ''].join('|');
}

export function readHash(): ViewState {
  return parseHash(location.hash);
}

// keep ':' ',' readable in the fragment (both are allowed there unescaped)
const enc = (s: string) => encodeURIComponent(s).replace(/%3A/gi, ':').replace(/%2C/gi, ',');

export function serializeHash(s: Omit<ViewState, 'preset'>): string {
  const out: [string, string][] = [];
  const add = (k: string, v: string) => out.push([k, v]);
  if (s.route !== 'map') add('v', s.route);
  if (s.level !== DEFAULT_LEVEL) add('l', s.level);
  if (s.metric) add('m', s.metric);
  const bivariate = s.route === 'map' && s.spatial === 'bi';
  if ((s.route === 'compare' || bivariate) && s.metricB) add('b', s.metricB);
  if (s.size) add('s', s.size);
  if (s.display === 'symbols') add('d', 'sym');
  if (s.cls !== 'quantile') add('cls', CLS_KEY[s.cls]);
  if (s.year) add('y', s.year);
  if (s.vote) add('vote', s.vote);
  if (s.vdiff) add('vd', '1');
  if (s.route === 'map' && s.spatial !== 'off') add('sp', s.spatial);
  if (s.route === 'map' && s.spatial === 'lisa' && s.fdr) add('fdr', '1');
  if (s.unstable !== 'show') add('ur', s.unstable === 'light' ? 'l' : 'h');
  for (const f of s.filters) add('f', filterKey(f));
  if (s.hub !== DEFAULT_HUB) add('hub', s.hub);
  if (s.reach !== 'off') {
    add('reach', s.reach);
    add('t', String(Math.round(s.t)));
    if (s.reach === 'pt' && s.ptm === 'dd') add('ptm', 'dd');
  }
  if (s.sel) add('sel', s.sel);
  if (s.tab) add('tab', s.tab);
  if (s.lang !== 'en') add('lang', s.lang);
  if (s.embed) add('embed', '1');
  if (s.route === 'compare' && s.only && s.filters.length) add('only', '1');
  for (const [k, v] of Object.entries(s.params)) add(k, v);
  return out.length ? '#' + out.map(([k, v]) => `${k}=${enc(v)}`).join('&') : '';
}

export function writeHash(s: Omit<ViewState, 'preset'>): void {
  const h = serializeHash(s);
  if (h !== location.hash && !(h === '' && location.hash === '')) {
    const url = h === '' ? location.pathname + location.search : h;
    // a new page (route or unit) gets its own history entry; view tweaks replace the current one
    if (routeKey(s) !== routeKey(parseHash(location.hash))) history.pushState(null, '', url);
    else history.replaceState(null, '', url);
  }
}
