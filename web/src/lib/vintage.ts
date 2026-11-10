// Older boundary vintages (docs/older_boundaries.md): the municipality map of a past municipality
// state with the values that exist on that state (pipeline/build/vintages.py). Everything is loaded on
// first use; the harmonised map does not load any of it (only the small index, for the switch).
// URL: #v=vintage&vin=2000&m=<metric>&y=<period>&sel=<BFS number on that state>
import { feature, mesh } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
import type { Feature, FeatureCollection, MultiLineString } from 'geojson';
import { getOptionalJSON, type Base, type Column, type ColumnFile, type MetricMeta, type Source } from './data';
import { app } from './state.svelte';

export interface VintageMetric {
  periods: string[];
  /** theme file of the vintage that holds the metric */
  file: string;
  source: string;
  /** 'native': published on that state; 'forward': from an older state, carried forward by ATLAS */
  provenance: 'native' | 'forward';
  note: string;
  /** municipalities whose newest value is a boundary estimate (split population-weighted) */
  n_estimate: number;
}

export interface VintageInfo {
  id: string;
  date: string;
  label_en: string;
  label_de: string;
  label_fr: string;
  n_units: number;
  geometry: { path: string; gzip_bytes: number };
  units: { path: string; gzip_bytes: number };
  files: Record<string, { path: string; gzip_bytes: number }>;
  metrics: Record<string, VintageMetric>;
}

export interface VintageIndex {
  reference: string;
  generated: string;
  vintages: VintageInfo[];
  sources: Record<string, Source & { license?: string; vintage?: string }>;
}

export interface VintageUnit {
  id: string;
  hist_id: number;
  name: string;
  kanton: string;
  bezirk: string | null;
  label: [number, number] | null;
  /** municipalities of the reference state it is part of: [BFS number, name, share of its residents,
   *  number of municipalities of this state that form it] */
  to: [string, string, number, number][];
}

export interface VintageColumn extends Column {
  /** Switzerland: counts summed over the state's municipalities, shares from the summed counts */
  ch?: number | null;
}

export interface VintageValues {
  vintage: string;
  units: string[];
  metrics: Record<string, VintageColumn[]>;
  status_codes: Record<string, number>;
  precision_codes: Record<string, number>;
}

export interface VintageData {
  info: VintageInfo;
  units: VintageUnit[];
  index: Map<string, number>;
  /** municipalities, feature id = unit index */
  geo: FeatureCollection;
  lakes: FeatureCollection;
  /** canton borders of that state (mesh between municipalities of different cantons, plus the outline) */
  cantons: FeatureCollection;
}

const memo = new Map<string, Promise<unknown>>();
function once<T>(key: string, load: () => Promise<T>): Promise<T> {
  let p = memo.get(key) as Promise<T> | undefined;
  if (!p) {
    p = load();
    p.catch(() => memo.delete(key));
    memo.set(key, p);
  }
  return p;
}

/** The index of older vintages, or null when this build has none (the switch then stays hidden). */
export const loadVintageIndex = () => once('index', () => getOptionalJSON<VintageIndex>('web/vintages.json').catch(() => null));

async function need<T>(path: string): Promise<T> {
  const x = await getOptionalJSON<T>(path);
  if (x === null) throw new Error(`${path}: not found`);
  return x;
}

/** Geometry and units of one vintage. */
export function loadVintage(info: VintageInfo): Promise<VintageData> {
  return once(`v:${info.id}`, async () => {
    const [topo, uf] = await Promise.all([need<Topology>(info.geometry.path), need<{ units: VintageUnit[] }>(info.units.path)]);
    const units = uf.units;
    const index = new Map(units.map((u, i) => [u.id, i]));
    const obj = topo.objects.gemeinde as GeometryCollection<{ id: string; canton: string }>;
    const fc = feature(topo, obj) as unknown as FeatureCollection;
    const features: Feature[] = [];
    for (const f of fc.features) {
      const i = index.get(String((f.properties as { id: string }).id));
      if (i === undefined) continue;
      f.id = i;
      features.push(f);
    }
    const lakes = topo.objects.lakes
      ? (feature(topo, topo.objects.lakes as GeometryCollection) as unknown as FeatureCollection)
      : { type: 'FeatureCollection' as const, features: [] };
    const kt = (g: { properties?: unknown }) => (g.properties as { canton?: string } | undefined)?.canton;
    const borders = mesh(topo, obj, (a, b) => a === b || kt(a) !== kt(b)) as MultiLineString;
    const cantons: FeatureCollection = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: borders }] };
    return { info, units, index, geo: { type: 'FeatureCollection', features }, lakes, cantons };
  });
}

/** Values of one theme file of a vintage (all periods). */
export const loadVintageValues = (info: VintageInfo, file: string) =>
  once(`f:${info.id}:${file}`, () => need<VintageValues>(info.files[file].path));

/** One metric's column for a period, as a ColumnFile + Column pair the shared components understand. */
export function vintageColumn(vals: VintageValues, metric: string, period: string | null): { file: ColumnFile; col: VintageColumn } | null {
  const cols = vals.metrics[metric];
  if (!cols?.length) return null;
  const col = (period && cols.find((c) => c.period === period)) || cols[cols.length - 1];
  const file: ColumnFile = { level: 'gemeinde', units: vals.units, metrics: { [metric]: col }, status_codes: vals.status_codes, precision_codes: vals.precision_codes };
  return { file, col };
}

/** Metric metadata of the harmonised catalog, adapted to the vintage (periods, source; national
 *  coverage on that state). */
export function vintageMeta(meta: MetricMeta, vm: VintageMetric): MetricMeta {
  return {
    ...meta, periods: vm.periods, n_periods: vm.periods.length, latest: vm.periods[vm.periods.length - 1], latest_available: undefined,
    levels: ['gemeinde'], source: vm.source, coverage: 'national', coverage_detail: null, incomplete_periods: null, unavailable_levels: null,
    reliability: null, pooled: null, majority_cantons: null, native_level: 'gemeinde',
    // every metric of a vintage is listed in the picker (the list is short)
    headline: meta.headline ?? 1000,
  };
}

/** Vintage label in the UI language. */
export function vintageLabel(v: VintageInfo, lang: string): string {
  return lang === 'de' ? v.label_de : lang === 'fr' ? v.label_fr : v.label_en;
}

/** Old -> current: the current municipality that holds most of the old one's residents. */
export function mainSuccessor(u: VintageUnit | undefined): string | null {
  return u?.to.length ? u.to[0][0] : null;
}

/** Current -> old: the old unit that contributes the whole of itself (weight 1) to the current
 *  municipality, preferring the one with the same BFS number, else the one with the largest share. */
export function predecessorOf(units: VintageUnit[], current: string): string | null {
  let best: VintageUnit | null = null;
  let bw = -1;
  for (const u of units) {
    const hit = u.to.find((t) => t[0] === current);
    if (!hit) continue;
    const w = hit[2] + (u.id === current ? 1 : 0);
    if (w > bw) {
      bw = w;
      best = u;
    }
  }
  return best?.id ?? null;
}

// ---------------------------------------------------------------- switching (view state)

/** The vintage shown now (null = the harmonised reference state). */
export const currentVintage = (): string | null => (app.route === 'vintage' ? (app.params.vin ?? null) : null);

/** Switch between the harmonised map (target null) and an older vintage. The shade metric is kept
 *  (the vintage view says so when it has no values there); the selected municipality follows: an old
 *  municipality goes to the current one holding most of its residents, a current one to its main
 *  predecessor. */
export async function switchVintage(base: Base, target: string | null): Promise<void> {
  const ix = await loadVintageIndex();
  if (!ix) return;
  const from = currentVintage();
  if (target === from) return;
  let cur: string | null = null;
  const fi = from ? ix.vintages.find((v) => v.id === from) : undefined;
  if (fi && app.sel) {
    const d = await loadVintage(fi);
    const i = d.index.get(app.sel);
    cur = i === undefined ? null : mainSuccessor(d.units[i]);
  } else if (!from && app.level === 'gemeinde') cur = app.sel;
  if (target === null) {
    const meta = base.metas.get(app.metric);
    app.go('map', {});
    app.level = 'gemeinde';
    app.sel = cur;
    if (app.year && !meta?.periods.includes(app.year)) app.year = null;
    return;
  }
  const ti = ix.vintages.find((v) => v.id === target);
  if (!ti) return;
  let sel: string | null = null;
  if (cur) sel = predecessorOf((await loadVintage(ti)).units, cur);
  app.go('vintage', { vin: target });
  app.level = 'gemeinde';
  app.sel = sel;
  const vm = ti.metrics[app.metric];
  if (app.year && !vm?.periods.includes(app.year)) app.year = null;
}
