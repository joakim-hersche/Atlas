// Shareable view state in the URL hash. Full form (works within the page and in most links):
//   #v=compare&l=bezirk&m=geo_pop_density&b=share_foreign&s=pop_total&d=sym&cls=q&y=2015
//    &sp=lisa&fdr=1 (cluster map) | &sp=bi&b=<metric> (bivariate)  &embed=1 (compact iframe view)
//    &f=n:pop_total:1000:50000&f=c:kanton:ZH,BE&f=r:bern:pt:30&hub=bern&reach=pt&t=45&sel=261&tab=rank
// Year comparisons: yc=<earlier year> (change since that year, up to the slider year y), ym=p (percent instead of
// absolute), fx=1 (class limits fixed across all years), smy=2010,2015,2020 (small multiples of those periods);
// lb=0 hides the city and lake names on the map.
// Reach as a filter: ro=1 (only the places within t minutes of the hub count: match count, ranking, aggregate;
// written only while reach is on).
// Every key is optional; defaults are left out. A bare single word (#compare, #density-foreigners, …)
// is accepted too: some hosts (the Claude artifact preview) keep only that form in shared links.
// Empty conditions (f=n:<id>:: or f=c:<field>:) are left out of the link.
// Commute filters: f=m:<sum|max|any|near|diff>:<ptst|pt|car>:<hub,hub>:<lo>:<hi> (minutes; lib/commute.svelte.ts).
// Filtered aggregate: ag=<metric id> (default: the shade metric). Ranking table: xc=<metric,metric> extra columns,
// rmin=<population> minimum size, rmf=1 flag the smaller units instead of hiding them.
// Routes: 'map' (default) and 'compare'; later pages (profile, places, search, sources) add their own
// route names and read their extra keys from `params`. The regression panel (#v=regress) uses
// ry, rx, rc, rw, rse, rd, rs (documented in regmodel.ts), e.g.
//   #v=regress&ry=nrw_share_bloc_left&rx=log:tax_np_mean_taxable_income,log:geo_pop_density&rc=lang
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
  | { kind: 'reach'; hub: string; mode: 'pt' | 'ptst' | 'car'; max: number }
  /** commute over several hubs (lib/commute.svelte.ts): sum / max of the times to the chosen hubs,
   *  min over the chosen hubs ('any') or over the nearest-hub list ('near'), or PT minus car to one hub ('diff').
   *  Times in minutes; the range is lo..hi (null = open); for 'diff' mode is the PT measure. */
  | { kind: 'commute'; op: CommuteOp; mode: 'pt' | 'ptst' | 'car'; hubs: string[]; lo: number | null; hi: number | null };
export type CommuteOp = 'sum' | 'max' | 'any' | 'near' | 'diff';
export const COMMUTE_OPS: CommuteOp[] = ['sum', 'max', 'any', 'near', 'diff'];

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
  /** reach acts as a filter: only the places within `t` minutes count ('ro=1') */
  ronly: boolean;
  /** federal vote shown by the per-vote metrics (vote id; null = the latest vote) */
  vote: string | null;
  /** yes share shown as the difference from the national result */
  vdiff: boolean;
  /** D37: include single-seat (majority-election) cantons in classes, ranks and statistics */
  maj: boolean;
  /** values resting on small numbers: shown, drawn lighter, or hidden (treated as gaps) */
  unstable: 'show' | 'light' | 'hide';
  /** metric whose aggregate over the filtered set is shown next to the match count (null = the shade metric) */
  agg: string | null;
  /** extra ranking-table columns (metric ids) */
  xcols: string[];
  /** ranking table: minimum population (null = none); below it units are hidden, or only flagged when rflag */
  rmin: number | null;
  rflag: boolean;
  /** spatial statistics: map mode ('sp'), false discovery rate for the cluster map ('fdr') */
  spatial: SpatialMode;
  fdr: boolean;
  /** compact embed mode (map, legend, attribution, link to the full view) for iframes ('embed=1') */
  embed: boolean;
  /** change between two years: the earlier year ('yc'; the later one is the slider year); null = plain values */
  cmpFrom: string | null;
  /** change as an absolute difference ('a') or in percent of the earlier value ('p') */
  cmpMode: 'abs' | 'pct';
  /** class breaks fixed across all years of the metric (the slider does not re-classify) */
  fixed: boolean;
  /** small multiples: periods shown side by side (null = closed) */
  multi: string[] | null;
  /** reference layer with lake and city labels */
  labels: boolean;
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
const KNOWN = new Set(['v', 'mode', 'l', 'm', 'b', 's', 'd', 'cls', 'y', 'f', 'pop', 'hub', 'reach', 't', 'sel', 'tab', 'lang', 'only', 'ptm', 'vote', 'vd', 'ur', 'ag', 'xc', 'rmin', 'rmf', 'sp', 'fdr', 'embed', 'yc', 'ym', 'fx', 'smy', 'lb', 'mj', 'ro']);
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
  if (p[0] === 'm' && p.length === 6 && (COMMUTE_OPS as string[]).includes(p[1]) && (p[2] === 'pt' || p[2] === 'ptst' || p[2] === 'car')) {
    const hubs = p[3].split(',').filter((h) => /^[a-z0-9_]+$/i.test(h));
    return { kind: 'commute', op: p[1] as CommuteOp, mode: p[2], hubs, lo: numOrNull(p[4]), hi: numOrNull(p[5]) };
  }
  return null;
}

/** A condition that filters nothing: a range with neither end, or a category with no value chosen. */
export function emptyFilter(f: Filter): boolean {
  return (f.kind === 'num' && f.lo === null && f.hi === null) || (f.kind === 'cat' && !f.values.length);
}

function filterKey(f: Filter): string {
  if (f.kind === 'num') return `n:${f.metric}:${f.lo ?? ''}:${f.hi ?? ''}`;
  if (f.kind === 'cat') return `c:${f.field}:${f.values.join(',')}`;
  if (f.kind === 'commute') return `m:${f.op}:${f.mode}:${f.hubs.join(',')}:${f.lo ?? ''}:${f.hi ?? ''}`;
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
    ronly: get('ro') === '1',
    vote: /^\d+$/.test(get('vote') ?? '') ? get('vote')! : null,
    vdiff: get('vd') === '1',
    maj: get('mj') === '1',
    agg: /^[a-z0-9_]+$/i.test(get('ag') ?? '') ? get('ag')! : null,
    xcols: (get('xc') ?? '').split(',').filter((x) => /^[a-z0-9_]+$/i.test(x)),
    rmin: (numOrNull(get('rmin')) ?? 0) > 0 ? numOrNull(get('rmin')) : null,
    rflag: get('rmf') === '1',
    unstable: get('ur') === 'l' ? 'light' : get('ur') === 'h' ? 'hide' : 'show',
    spatial: get('sp') === 'lisa' ? 'lisa' : get('sp') === 'bi' ? 'bi' : 'off',
    fdr: get('fdr') === '1',
    embed: get('embed') === '1',
    cmpFrom: get('yc') || null,
    cmpMode: get('ym') === 'p' ? 'pct' : 'abs',
    fixed: get('fx') === '1',
    multi: q.has('smy') ? (get('smy') ?? '').split(',').filter(Boolean) : null,
    labels: get('lb') !== '0',
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
  if (s.maj) add('mj', '1');
  if (s.route === 'map' && s.spatial !== 'off') add('sp', s.spatial);
  if (s.route === 'map' && s.spatial === 'lisa' && s.fdr) add('fdr', '1');
  if (s.unstable !== 'show') add('ur', s.unstable === 'light' ? 'l' : 'h');
  if (s.cmpFrom) {
    add('yc', s.cmpFrom);
    if (s.cmpMode === 'pct') add('ym', 'p');
  }
  if (s.fixed) add('fx', '1');
  if (s.multi) add('smy', s.multi.join(','));
  if (!s.labels) add('lb', '0');
  // U3: conditions without a range or values do nothing: they stay in the panel but not in the link
  for (const f of s.filters) if (!emptyFilter(f)) add('f', filterKey(f));
  if (s.agg) add('ag', s.agg);
  if (s.xcols.length) add('xc', s.xcols.join(','));
  if (s.rmin) add('rmin', String(Math.round(s.rmin)));
  if (s.rmin && s.rflag) add('rmf', '1');
  if (s.hub !== DEFAULT_HUB) add('hub', s.hub);
  if (s.reach !== 'off') {
    add('reach', s.reach);
    add('t', String(Math.round(s.t)));
    if (s.reach === 'pt' && s.ptm === 'dd') add('ptm', 'dd');
    if (s.ronly) add('ro', '1');
  }
  if (s.sel) add('sel', s.sel);
  if (s.tab) add('tab', s.tab);
  if (s.lang !== 'en') add('lang', s.lang);
  if (s.embed) add('embed', '1');
  if (s.route === 'compare' && s.only && s.filters.length) add('only', '1');
  for (const [k, v] of Object.entries(s.params)) add(k, v);
  return out.length ? '#' + out.map(([k, v]) => `${k}=${enc(v)}`).join('&') : '';
}

/** U2: what makes a step the Back button returns from: the page (route, unit), the level, the shaded metric and
 *  the selected unit. Sliders, years, filters and other tweaks replace the current entry. */
export function historyKey(s: { route: string; params: Record<string, string>; level: string; metric: string | null; sel: string | null }): string {
  return [routeKey(s), s.level, s.metric ?? DEFAULT_METRIC, s.sel ?? ''].join('|');
}

/** Write the state to the hash: a new history entry when historyKey changes (unless `replace`), else in place. */
export function writeHash(s: Omit<ViewState, 'preset'>, replace = false): void {
  const h = serializeHash(s);
  if (h !== location.hash && !(h === '' && location.hash === '')) {
    const url = h === '' ? location.pathname + location.search : h;
    if (!replace && historyKey(s) !== historyKey(parseHash(location.hash))) history.pushState(null, '', url);
    else history.replaceState(null, '', url);
  }
}
