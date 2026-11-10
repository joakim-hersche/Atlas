// Data loading and the column format written by pipeline/build/web.py.
import { feature } from 'topojson-client';
import { SvelteMap } from 'svelte/reactivity';
import { t, levelWord } from './i18n.svelte';
import { periodTitles } from './classify';
import { app } from './state.svelte';
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
  // ---- web data contract, round 1 (docs/web_data_contract.md); all optional: older builds lack them
  label_fr?: string | null;
  unit_de?: string | null;
  unit_fr?: string | null;
  /** newest period with any value (latest = default period with near-complete coverage) */
  latest_available?: string;
  incomplete_periods?: Record<string, { n: number; of: number; level: string; label_en?: string; label_de?: string; label_fr?: string }> | null;
  coverage_meta?: string;
  coverage_detail?: { level: string; period: string; n: number; of: number; n_cantons: number } | null;
  /** level -> reason (English) why the metric has no values there */
  unavailable_levels?: Record<string, string> | null;
  /** small-number rule (flag bits 1/2) */
  reliability?: { count: string | null; base: string | null; min_count: number; min_base: number; rule_en?: string; rule_de?: string; rule_fr?: string } | null;
  /** pooled multi-year rate of an annual metric */
  pooled?: { of: string; years: number } | null;
  /** NRW: cantons with a majority election per election year (flag bit 4) */
  majority_cantons?: Record<string, string[]> | null;
  /** per-vote metrics: path of the vote index */
  vote_index?: string | null;
  /** per-vote metrics: title of the latest vote */
  latest_title?: Record<string, string> | null;
}

export interface Column {
  period: string;
  v: (number | null)[];
  s?: Record<string, number>; // unit index -> status code (only for gaps)
  p?: Record<string, number>; // unit index -> precision code (when it differs per unit)
  f?: Record<string, number>; // unit index -> flag bitmask (flag_bits of the file)
  n?: Record<string, number>; // unit index -> index into notes (gap reason or provenance)
  notes?: string[];
}

export interface ColumnFile {
  level: string;
  units: string[];
  metrics: Record<string, Column>;
  status_codes: Record<string, number>;
  precision_codes: Record<string, number>;
  /** flag name -> bit (small_base 1, small_count 2, majority_election 4, published_value 8, provisional 16) */
  flag_bits?: Record<string, number>;
}

export interface Source {
  source_id: string;
  title: string;
  publisher: string;
  url: string;
  attribution: string;
  /** ISO date of the newest download */
  fetched?: string | null;
  /** plain status wording (e.g. "held back: licence not yet confirmed") */
  status_text?: string | null;
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
    ]).then(([metrics, sources, k, l]) => {
      // titles of the latest federal vote (per-vote metrics), for period labels
      for (const m of metrics) if (m.per_vote && m.latest_title) periodTitles.set(m.latest, m.latest_title);
      return {
      metrics,
      metas: new Map(metrics.map((m) => [m.id, m])),
      sources: new Map(sources.map((s) => [s.source_id, s])),
      kanton: topo(k, 'kanton'),
      lakes: topo(l, 'lakes'),
    };
    });
    baseP.catch(() => (baseP = null));
  }
  return baseP;
}

const levelFiles = new Map<string, Promise<LevelData>>();
/** number of units per level, for every level loaded so far (reactive: the header shows the real count) */
export const unitCounts = new SvelteMap<string, number>();
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
    unitCounts.set(level, core.units.length);
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
  /** official BFS names of typology units per language (de, fr, it, en); `name` is German */
  names?: Record<string, string>;
}
let unitsP: Promise<UnitRow[]> | null = null;
/** official names per language of typology units ('sprachgebiet:2' -> {de, fr, it, en}) */
const unitNames = new Map<string, Record<string, string>>();
/** A unit's name in the UI language where the source gives one (typology units), else `fallback`. */
export function placeName(level: string, id: string, fallback: string): string {
  const n = unitNames.get(`${level}:${id}`);
  return (n && n[app.lang]) || fallback;
}
/** Names of a level's units in the UI language (reactive on the language when read in a $derived). */
export function namesOf(ld: LevelData): string[] {
  if (ld.level === 'gemeinde' || !unitNames.size) return ld.name;
  return ld.units.map((u, i) => placeName(ld.level, u, ld.name[i]));
}
/** All units of all levels: names, label points, parent regions of each municipality. */
export function loadUnits(): Promise<UnitRow[]> {
  if (!unitsP) {
    unitsP = getJSON<UnitRow[]>('web/units.json').then((u) => {
      for (const r of u) if (r.names) unitNames.set(`${r.level}:${r.id}`, r.names);
      return u;
    });
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
  const note = noteOf(col, i);
  if (note) return note;
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

/** The column's note for unit i (the real reason for a gap, or the provenance of a fallback value). */
export function noteOf(col: Column, i: number): string | null {
  const k = col.n?.[String(i)];
  return k !== undefined && col.notes?.[k] ? col.notes[k] : null;
}

export const FLAG = { small_base: 1, small_count: 2, majority_election: 4, published_value: 8, provisional: 16 } as const;
export type FlagName = keyof typeof FLAG;
/** Flag bitmask of unit i (0 = none). Bits follow the file's flag_bits, else the contract defaults. */
export function flagsOf(file: ColumnFile | null, col: Column, i: number): number {
  return col.f?.[String(i)] ?? 0;
}
export function hasFlag(file: ColumnFile | null, flags: number, name: FlagName): boolean {
  const bit = file?.flag_bits?.[name] ?? FLAG[name];
  return (flags & bit) !== 0;
}

/** Unstable small-number value (base or count below the metric's reliability rule). */
export const isUnstable = (file: ColumnFile | null, flags: number) =>
  flags !== 0 && (hasFlag(file, flags, 'small_base') || hasFlag(file, flags, 'small_count'));

/** Short markers of a unit's flags, for tables and cards: △ small numbers, M majority election,
 *  ° published value used, p provisional. */
export function flagMarks(file: ColumnFile | null, flags: number): string {
  if (!flags) return '';
  let out = '';
  if (isUnstable(file, flags)) out += '△';
  if (hasFlag(file, flags, 'majority_election')) out += 'M';
  if (hasFlag(file, flags, 'published_value')) out += '°';
  if (hasFlag(file, flags, 'provisional')) out += 'p';
  return out;
}

/** Full sentences for a unit's flags (card, profile), in the UI language. */
export function flagTexts(file: ColumnFile | null, flags: number, meta: MetricMeta): string[] {
  if (!flags) return [];
  const out: string[] = [];
  if (isUnstable(file, flags)) {
    const r = meta.reliability;
    const lang: string = app.lang;
    const rule = r ? ((lang === 'de' ? r.rule_de : lang === 'fr' ? r.rule_fr : null) ?? r.rule_en ?? null) : null;
    out.push(`△ ${t('fl.small')}${rule ? ` (${rule})` : ''}`);
  }
  if (hasFlag(file, flags, 'majority_election')) out.push(`M ${t('fl.majority')}`);
  if (hasFlag(file, flags, 'published_value')) out.push(`° ${t('fl.published')}`);
  if (hasFlag(file, flags, 'provisional')) out.push(`p ${t('fl.provisional')}`);
  return out;
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
  const real = meta.unavailable_levels?.[level];
  const where = meta.levels.filter((l) => l !== 'schweiz' && l !== 'gemeindetyp').map(lvlLabel);
  const list = where.length ? where.join(', ') : t('why.chOnly');
  if (real) return t('why.real', { reason: real, list });
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
