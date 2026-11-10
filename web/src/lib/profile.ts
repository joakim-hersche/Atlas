// Shared logic of the profile and Compare places pages: the level data of a place, metric entries
// (value, rank in Switzerland and in the canton, percentile, gap reason, precision), the theme layout,
// and a small SVG locator ("similar places" live in similar.ts).
import type { Feature, FeatureCollection, Geometry, Position } from 'geojson';
import { rankOf, type RankInfo } from './classify';
import {
  flagMarks, flagsOf, flagTexts, gapReason, majorityValue, regionalAt, LEVELS, loadLevel, loadTheme, noteOf, partialCantons, precisionOf, type Base, type ColumnFile, type MetricMeta,
} from './data';
import { loadRows } from './places';

// ---------------------------------------------------------------- level data of a place
export interface PlaceLevel {
  level: string;
  units: string[];
  index: Map<string, number>;
  core: ColumnFile;
  name: string[];
  /** canton code per unit ('' when none) */
  canton: string[];
  /** unit indices per canton (rank within the canton) */
  byCanton: Map<string, number[]>;
  geo: FeatureCollection | null;
}

const placeLevels = new Map<string, Promise<PlaceLevel>>();
export function loadPlaceLevel(level: string): Promise<PlaceLevel> {
  let p = placeLevels.get(level);
  if (!p) {
    p = (async () => {
      const li = LEVELS.find((l) => l.id === level);
      let units: string[], core: ColumnFile, name: string[], canton: string[], geo: FeatureCollection | null = null;
      const rows = await loadRows();
      if (li?.geometry) {
        const ld = await loadLevel(level);
        ({ units, core, geo } = ld);
        name = ld.name.slice();
        canton = ld.canton.slice();
      } else {
        core = await loadTheme(level, 'core');
        units = core.units;
        name = units.map((u) => rows.get(level === 'gemeinde' ? u : `${level}:${u}`)?.name ?? u);
        canton = units.map(() => '');
      }
      // canton per unit from units.json where the geometry has none (districts)
      units.forEach((u, i) => {
        if (!canton[i]) canton[i] = (level === 'kanton' ? u : rows.get(level === 'gemeinde' ? u : `${level}:${u}`)?.kanton) ?? '';
      });
      const byCanton = new Map<string, number[]>();
      if (level === 'gemeinde' || level === 'bezirk')
        canton.forEach((c, i) => c && byCanton.set(c, [...(byCanton.get(c) ?? []), i]));
      return { level, units, index: new Map(units.map((u, i) => [u, i])), core, name, canton, byCanton, geo };
    })();
    p.catch(() => placeLevels.delete(level));
    placeLevels.set(level, p);
  }
  return p;
}

// ---------------------------------------------------------------- themes
/** Themes in the curated headline order (D24), then any others alphabetically. */
export function themeOrder(base: Base): string[] {
  const out: string[] = [];
  for (const m of base.metrics.filter((x) => x.headline !== null).sort((a, b) => a.headline! - b.headline!))
    if (!out.includes(m.theme)) out.push(m.theme);
  for (const th of [...new Set(base.metrics.map((m) => m.theme))].sort()) if (!out.includes(th)) out.push(th);
  return out;
}

export interface ThemeBlock {
  theme: string;
  /** headline metrics (shown first) */
  head: MetricMeta[];
  /** all other metrics of the theme at this level (collapsible, loaded on demand) */
  rest: MetricMeta[];
  /** theme files needed for `rest` */
  files: string[];
}
export function themeBlocks(base: Base, level: string): ThemeBlock[] {
  const at = base.metrics.filter((m) => !m.hidden && m.levels.includes(level));
  return themeOrder(base)
    .map((theme) => {
      const ms = at.filter((m) => m.theme === theme);
      const head = ms.filter((m) => m.headline !== null).sort((a, b) => a.headline! - b.headline!);
      const rest = ms.filter((m) => m.headline === null).sort((a, b) => a.label_en.localeCompare(b.label_en));
      return { theme, head, rest, files: [...new Set(rest.map((m) => m.file))] };
    })
    .filter((b) => b.head.length || b.rest.length);
}

// ---------------------------------------------------------------- metric entries
export type Rank = RankInfo;
export interface Entry {
  meta: MetricMeta;
  value: number | null;
  period: string;
  rank: Rank | null;
  /** rank within the canton (municipalities and districts) */
  rankKt: Rank | null;
  precision: string;
  /** reason for a missing value (D21) */
  gap: string | null;
  partial: string[] | null;
  /** D21: the value is that of a coarser area (its level), or null */
  regional: string | null;
  /** flag markers (△ M ° p) and their sentences; provenance note of a shown value */
  marks: string;
  flags: string[];
  note: string | null;
}

/** One metric for unit i of a level, from a latest-values file. null = the file has no column. */
export function entryOf(pl: PlaceLevel, file: ColumnFile, meta: MetricMeta, i: number): Entry | null {
  const col = file.metrics[meta.id];
  if (!col) return null;
  // D37: a single-seat canton's party share is shown with its flag, but not ranked
  const maj = col.v[i] === null || col.v[i] === undefined ? majorityValue(col, i) : null;
  const value = col.v[i] ?? maj;
  const n = col.v.length;
  let rank: Rank | null = null;
  let rankKt: Rank | null = null;
  if (value !== null && maj === null && n > 1) {
    rank = rankOf(col.v, i, meta.direction);
    const grp = pl.byCanton.get(pl.canton[i]);
    if (grp && grp.length > 1) {
      const sub = grp.map((k) => col.v[k] ?? null);
      rankKt = rankOf(sub, grp.indexOf(i), meta.direction);
    }
  }
  return {
    meta, value, period: col.period, rank, rankKt,
    precision: precisionOf(file, col, i, meta),
    gap: value === null ? gapReason(file, col, i, meta, pl.canton[i]) : null,
    partial: partialCantons(meta),
    regional: regionalAt(meta, pl.level),
    marks: value !== null ? flagMarks(file, flagsOf(file, col, i)) : '',
    flags: value !== null ? flagTexts(file, flagsOf(file, col, i), meta) : [],
    note: value !== null && maj === null ? noteOf(col, i) : null,
  };
}

// ---------------------------------------------------------------- locator (SVG)
const LON0 = 5.956, LAT1 = 47.808, KX = Math.cos((46.8 * Math.PI) / 180);
export const LOC_W = 300;
const SCALE = LOC_W / ((10.492 - LON0) * KX);
export const LOC_H = Math.round((LAT1 - 45.818) * SCALE);
export const project = (p: Position): [number, number] => [(p[0] - LON0) * KX * SCALE, (LAT1 - p[1]) * SCALE];

function ringPath(ring: Position[], minStep: number): string {
  let out = '';
  let lx = NaN, ly = NaN;
  for (let k = 0; k < ring.length; k++) {
    const [x, y] = project(ring[k]);
    if (k > 0 && k < ring.length - 1 && Math.abs(x - lx) < minStep && Math.abs(y - ly) < minStep) continue;
    out += (k ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
    lx = x;
    ly = y;
  }
  return out + 'Z';
}
export function geomPath(g: Geometry | null, minStep = 0.6): string {
  if (!g) return '';
  if (g.type === 'Polygon') return g.coordinates.map((r) => ringPath(r, minStep)).join('');
  if (g.type === 'MultiPolygon') return g.coordinates.map((p) => p.map((r) => ringPath(r, minStep)).join('')).join('');
  return '';
}
const pathCache = new WeakMap<FeatureCollection, string>();
export function collectionPath(fc: FeatureCollection): string {
  let s = pathCache.get(fc);
  if (s === undefined) {
    s = fc.features.map((f: Feature) => geomPath(f.geometry)).join('');
    pathCache.set(fc, s);
  }
  return s;
}
/** Bounding box in locator pixels. */
export function geomBox(g: Geometry | null): [number, number, number, number] | null {
  if (!g || (g.type !== 'Polygon' && g.type !== 'MultiPolygon')) return null;
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of polys)
    for (const r of p)
      for (const pt of r) {
        const [x, y] = project(pt);
        x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
      }
  return [x0, y0, x1, y1];
}
