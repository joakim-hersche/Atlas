// Data loading and the column format written by pipeline/build/web.py.
import { feature } from 'topojson-client';
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
  precision: string;
  coverage: string; // 'national' | 'partial:AG,BE,...'
  source: string;
  description: string | null;
  levels: string[];
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

function topo<P>(t: Topology, name: string): FeatureCollection<Geometry, P> {
  return feature(t, t.objects[name] as GeometryCollection) as unknown as FeatureCollection<Geometry, P>;
}

export interface StartData {
  gemeinde: FeatureCollection<Geometry, GemeindeProps>;
  kanton: FeatureCollection;
  lakes: FeatureCollection;
  metrics: MetricMeta[];
  sources: Map<string, Source>;
  core: ColumnFile;
}

export async function loadStart(): Promise<StartData> {
  const [g, k, l, metrics, sources, core] = await Promise.all([
    getJSON<Topology>('geo/gemeinde.topojson'),
    getJSON<Topology>('geo/kanton.topojson'),
    getJSON<Topology>('geo/lakes.topojson'),
    getJSON<MetricMeta[]>('web/metrics.json'),
    getJSON<Source[]>('web/sources.json'),
    getJSON<ColumnFile>('web/latest/gemeinde/core.json'),
  ]);
  const gemeinde = topo<GemeindeProps>(g, 'gemeinde');
  // numeric feature ids (BFS numbers) let MapLibre address each unit with feature-state
  for (const f of gemeinde.features) f.id = Number(f.properties.id);
  return {
    gemeinde,
    kanton: topo(k, 'kanton'),
    lakes: topo(l, 'lakes'),
    metrics,
    sources: new Map(sources.map((s) => [s.source_id, s])),
    core,
  };
}

const themeFiles = new Map<string, Promise<ColumnFile>>();
/** Theme files (D23) are fetched on first use and kept. */
export function loadTheme(file: string): Promise<ColumnFile> {
  let p = themeFiles.get(file);
  if (!p) {
    p = getJSON<ColumnFile>(`web/latest/gemeinde/${file}.json`);
    p.catch(() => themeFiles.delete(file));
    themeFiles.set(file, p);
  }
  return p;
}

export function loadReach(hub: string, mode: 'pt' | 'car'): Promise<ReachFile | null> {
  return getOptionalJSON<ReachFile>(`reach/${hub}_${mode}.json`);
}

// ---------------------------------------------------------------- gap reasons (D21)
const STATUS_TEXT: Record<string, string> = {
  no_data: 'no data for this year',
  suppressed: 'suppressed (small numbers)',
  not_published: 'not published at this level',
  not_covered: 'not covered by this canton',
  not_applicable: 'not applicable',
};

export const PRECISION_TEXT: Record<string, string> = {
  exact: 'exact',
  survey: 'survey',
  modelled: 'modelled',
  boundary_estimate: 'boundary estimate',
};

export function partialCantons(meta: MetricMeta): string[] | null {
  return meta.coverage.startsWith('partial:') ? meta.coverage.slice(8).split(',') : null;
}

/** Reason a value is missing, from the status code, falling back to the coverage list. */
export function gapReason(file: ColumnFile, col: Column, i: number, meta: MetricMeta, canton: string): string {
  const code = col.s?.[String(i)];
  if (code !== undefined) {
    const name = Object.keys(file.status_codes).find((k) => file.status_codes[k] === code);
    if (name && STATUS_TEXT[name]) return STATUS_TEXT[name];
  }
  const cov = partialCantons(meta);
  if (cov && !cov.includes(canton)) return STATUS_TEXT.not_covered;
  return STATUS_TEXT.no_data;
}

export function precisionOf(file: ColumnFile, col: Column, i: number, meta: MetricMeta): string {
  const code = col.p?.[String(i)];
  if (code !== undefined) {
    const name = Object.keys(file.precision_codes).find((k) => file.precision_codes[k] === code);
    if (name) return name;
  }
  return meta.precision;
}
