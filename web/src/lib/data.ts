// Data loading and the column format written by pipeline/build/web.py.
import { feature } from 'topojson-client';
import { levelName, t, levelWord } from './i18n.svelte';
import type { Topology, GeometryCollection } from 'topojson-specification';
import type { FeatureCollection, Geometry } from 'geojson';

export type Direction = 'higher_better' | 'lower_better' | 'neutral';

export interface MetricMeta {
  id: string;
  theme: string;
  label_en: string;
  label_de: string;
  unit: string;
  decimals: number;
  direction: Direction;
  aggregation: string;
  precision: string;
  coverage: string; // 'national' | 'partial:AG,BE,...'
  source: string;
  description: string | null;
  levels: string[];
  periods: string[];
  n_periods: number;
  per_vote?: boolean;
  latest: string;
  headline: number | null;
  hidden: boolean;
  file: string;
}

export interface Column {
  period: string;
  v: (number | null)[];
  s?: Record<string, number>; // unit index -> status code (only for gaps)
  p?: Record<string, number>; // unit index -> precision code (when it differs per unit)
}

export interface ColumnFile {
  level: string;
  units: string[];
  metrics: Record<string, Column>;
  status_codes: Record<string, number>;
  precision_codes: Record<string, number>;
}

export interface Source {
  source_id: string;
  title: string;
  publisher: string;
  url: string;
  attribution: string;
}

export type Segment = [number, number, number, number[]]; // t_start, t_end, kind, flat lon/lat

export interface ReachFile {
  hub: string;
  name: string;
  mode: 'pt' | 'car';
  unit: string;
  departure?: string;
  service_date?: string;
  note?: string;
  kinds: Record<string, string>;
  segments: Segment[];
}

export interface GemeindeProps {
  id: number;
  name: string;
  canton: string;
  district: number;
}

const BASE = './data/';

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

/** Like getJSON, but a missing file (404) resolves to null instead of failing. */
export async function getOptionalJSON<T>(path: string): Promise<T | null> {
  const r = await fetch(BASE + path);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

/** Cache a promise per key; a failed load is forgotten so it can be retried. */
function cached<T>(store: Map<string, Promise<T>>, key: string, load: () => Promise<T>): Promise<T> {
  let p = store.get(key);
  if (!p) {
    p = load();
    p.catch(() => store.delete(key));
    store.set(key, p);
  }
  return p;
}

function topo<P>(t: Topology, name: string): FeatureCollection<Geometry, P> {
  return feature(t, t.objects[name] as GeometryCollection) as unknown as FeatureCollection<Geometry, P>;
}

// ---------------------------------------------------------------- spatial levels (brief 4.3)
export interface LevelInfo {
  id: string;
  label: string; // English, plural (UI)
  one: string; // English, singular
  de: string; // official German term
  geometry: boolean;
  series: boolean; // time series files cover this level (pipeline/build/web.py SERIES_LEVELS)
}
export const LEVELS: LevelInfo[] = [
  { id: 'gemeinde', label: 'Municipalities', one: 'municipality', de: 'Gemeinde', geometry: true, series: true },
  { id: 'bezirk', label: 'Districts', one: 'district', de: 'Bezirk', geometry: true, series: true },
  { id: 'kanton', label: 'Cantons', one: 'canton', de: 'Kanton', geometry: true, series: true },
  { id: 'grossregion', label: 'Major regions', one: 'major region', de: 'Grossregion', geometry: true, series: false },
  { id: 'sprachgebiet', label: 'Language regions', one: 'language region', de: 'Sprachgebiet', geometry: true, series: false },
  { id: 'agglomeration', label: 'Agglomerations', one: 'agglomeration', de: 'Agglomeration', geometry: true, series: false },
  { id: 'arbeitsmarktgebiet', label: 'Labour market areas', one: 'labour market area', de: 'Arbeitsmarktgebiet', geometry: true, series: false },
  { id: 'stadt_land', label: 'Urban / rural', one: 'urban/rural type', de: 'Stadt/Land', geometry: true, series: false },
];
export const levelInfo = (id: string): LevelInfo => LEVELS.find((l) => l.id === id) ?? LEVELS[0];

export interface LevelData {
  level: string;
  /** unit ids in the order of the level's column files */
  units: string[];
  index: Map<string, number>;
  /** features with id = unit index (MapLibre feature-state needs numeric ids) */
  geo: FeatureCollection;
  core: ColumnFile;
  name: string[];
  /** canton code per unit ('' when the unit spans cantons or has none) */
  canton: string[];
}

export interface Base {
  metrics: MetricMeta[];
  metas: Map<string, MetricMeta>;
  sources: Map<string, Source>;
  kanton: FeatureCollection;
  lakes: FeatureCollection;
}

const geoFiles = new Map<string, Promise<Topology>>();
const loadTopo = (name: string) => cached(geoFiles, name, () => getJSON<Topology>(`geo/${name}.topojson`));

let baseP: Promise<Base> | null = null;
/** Metric catalog, sources, canton outlines and lakes: loaded once at start. */
export function loadBase(): Promise<Base> {
  if (!baseP) {
    baseP = Promise.all([
      getJSON<MetricMeta[]>('web/metrics.json'),
      getJSON<Source[]>('web/sources.json'),
      loadTopo('kanton'),
      loadTopo('lakes'),
    ]).then(([metrics, sources, k, l]) => ({
      metrics,
      metas: new Map(metrics.map((m) => [m.id, m])),
      sources: new Map(sources.map((s) => [s.source_id, s])),
      kanton: topo(k, 'kanton'),
      lakes: topo(l, 'lakes'),
    }));
    baseP.catch(() => (baseP = null));
  }
  return baseP;
}

const levelFiles = new Map<string, Promise<LevelData>>();
/** The level's data if it is loaded or loading, without starting a download. */
export const peekLevel = (level: string): Promise<LevelData> | undefined => levelFiles.get(level);
/** Geometry and headline values of one level (gemeinde at start; the others on first use). */
export function loadLevel(level: string): Promise<LevelData> {
  return cached(levelFiles, level, async () => {
    const needNames = level !== 'gemeinde';
    const [t, core, units] = await Promise.all([
      loadTopo(level),
      loadTheme(level, 'core'),
      needNames ? loadUnits() : Promise.resolve(null),
    ]);
    const fc = topo<{ id: string | number; name?: string; canton?: string }>(t, level);
    const index = new Map(core.units.map((u, i) => [u, i]));
    const name = core.units.slice();
    const canton = core.units.map(() => '');
    if (units) {
      for (const r of units) {
        if (r.level !== level) continue;
        const i = index.get(r.id);
        if (i === undefined) continue;
        name[i] = r.name;
        canton[i] = r.kanton ?? '';
      }
    }
    if (level === 'kanton') core.units.forEach((u, i) => (canton[i] = u));
    const features = [];
    for (const f of fc.features) {
      const i = index.get(String(f.properties.id));
      if (i === undefined) continue;
      f.id = i;
      if (!units) {
        name[i] = f.properties.name ?? name[i];
        canton[i] = f.properties.canton ?? '';
      }
      features.push(f);
    }
    return { level, units: core.units, index, geo: { type: 'FeatureCollection', features } as FeatureCollection, core, name, canton };
  });
}

const themeFiles = new Map<string, Promise<ColumnFile>>();
/** Theme files (D23) of a level are fetched on first use and kept. */
export function loadTheme(level: string, file: string, core?: ColumnFile): Promise<ColumnFile> {
  if (file === 'core' && core) return Promise.resolve(core);
  return cached(themeFiles, `${level}/${file}`, () => getJSON<ColumnFile>(`web/latest/${level}/${file}.json`));
}

/** Switzerland as a whole (level 'schweiz'); not every theme has a national file. */
const chFiles = new Map<string, Promise<ColumnFile | null>>();
export function loadCH(file: string): Promise<ColumnFile | null> {
  return cached(chFiles, file, () => getOptionalJSON<ColumnFile>(`web/latest/schweiz/${file}.json`).catch(() => null));
}

export interface SeriesFile {
  metric: string;
  periods: string[];
  levels: Record<string, Record<string, (number | null)[]>>;
}
const seriesFiles = new Map<string, Promise<SeriesFile | null>>();
/** All periods of one metric for municipalities, districts, cantons and Switzerland (on demand). */
export function loadSeries(metric: string): Promise<SeriesFile | null> {
  return cached(seriesFiles, metric, () => getOptionalJSON<SeriesFile>(`web/series/${metric}.json`));
}

export interface UnitRow {
  id: string;
  level: string;
  name: string;
  kanton?: string | null;
  bezirk?: string;
  label?: [number, number] | null;
  grossregion?: string;
  sprachgebiet?: string;
  agglomeration?: string;
  arbeitsmarktgebiet?: string;
  stadt_land?: string;
  gemeindetyp?: string;
  n_gemeinden?: number;
}
let unitsP: Promise<UnitRow[]> | null = null;
/** All units of all levels: names, label points, parent regions of each municipality. */
export function loadUnits(): Promise<UnitRow[]> {
  if (!unitsP) {
    unitsP = getJSON<UnitRow[]>('web/units.json');
    unitsP.catch(() => (unitsP = null));
  }
  return unitsP;
}

export interface Hub {
  slug: string;
  name: string;
}
export interface ReachIndex {
  hubs: Hub[];
  files: { hub: string; mode: 'pt' | 'car'; file: string; gzip_bytes?: number }[];
  service_date?: string;
}
let reachIndexP: Promise<ReachIndex | null> | null = null;
export function loadReachIndex(): Promise<ReachIndex | null> {
  if (!reachIndexP) {
    reachIndexP = getOptionalJSON<ReachIndex>('reach/index.json');
    reachIndexP.catch(() => (reachIndexP = null));
  }
  return reachIndexP;
}

const reachFiles = new Map<string, Promise<ReachFile | null>>();
export function loadReach(hub: string, mode: 'pt' | 'car'): Promise<ReachFile | null> {
  return cached(reachFiles, `${hub}_${mode}`, () => getOptionalJSON<ReachFile>(`reach/${hub}_${mode}.json`));
}

// ---------------------------------------------------------------- gap reasons (D21)
const STATUS = ['no_data', 'suppressed', 'not_published', 'not_covered', 'not_applicable'];
const statusText = (k: string) => t(`gap.${k}`);

const PRECISIONS = ['exact', 'survey', 'modelled', 'boundary_estimate'];
/** Precision tag in the UI language (exact / survey / modelled / boundary estimate). */
export const precisionText = (p: string): string => (PRECISIONS.includes(p) ? t(`prec.${p}`) : p);

export function partialCantons(meta: MetricMeta): string[] | null {
  return meta.coverage.startsWith('partial:') ? meta.coverage.slice(8).split(',') : null;
}

/** Reason a value is missing, from the status code, falling back to the coverage list.
 *  `file` is null for a column built from a series file (no status codes there). */
export function gapReason(file: ColumnFile | null, col: Column, i: number, meta: MetricMeta, canton: string): string {
  if (!file) return statusText('no_data');
  const code = col.s?.[String(i)];
  if (code !== undefined) {
    const name = Object.keys(file.status_codes).find((k) => file.status_codes[k] === code);
    if (name && STATUS.includes(name)) return statusText(name);
  }
  const cov = partialCantons(meta);
  if (cov && !cov.includes(canton)) return statusText('not_covered');
  return statusText('no_data');
}

export function precisionOf(file: ColumnFile | null, col: Column, i: number, meta: MetricMeta): string {
  const code = file ? col.p?.[String(i)] : undefined;
  if (file && code !== undefined) {
    const name = Object.keys(file.precision_codes).find((k) => file.precision_codes[k] === code);
    if (name) return name;
  }
  return meta.precision;
}

/** One metric's values at one level for one period, ready for the map, filters and tables. */
export interface ColRef {
  meta: MetricMeta;
  level: string;
  col: Column;
  /** the latest-values file (status and precision codes), or null for a column built from a series */
  file: ColumnFile | null;
}

const lvlLabel = (id: string) => levelWord(id);

/** Why a metric cannot be shown at a level (one line), or null when it can. */
export function unavailableReason(meta: MetricMeta, level: string): string | null {
  if (meta.levels.includes(level)) return null;
  const where = meta.levels.filter((l) => l !== 'schweiz' && l !== 'gemeindetyp').map(lvlLabel);
  const list = where.length ? where.join(', ') : t('why.chOnly');
  if (meta.aggregation === 'not_aggregatable')
    return t('why.notAgg', { level: lvlLabel(level), list });
  return t('why.notPub', { level: lvlLabel(level), list });
}

/** Periods of a metric that the year slider can show at a level (series files exist for some levels only). */
export function seriesPeriods(meta: MetricMeta, level: string): string[] {
  const li = LEVELS.find((l) => l.id === level);
  if (!li?.series || meta.per_vote || meta.periods.length < 2 || !meta.levels.includes(level)) return [];
  return meta.periods;
}
