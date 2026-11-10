// Reference layer: city and lake names on the map, drawn on a canvas above it (no tile server and no glyph
// files: the site stays static). Only data that already ships is used: municipality names, label points and
// population from units.json and the gemeinde core file, and the lake outlines (with their names) of
// lakes.topojson. Labels are placed greedily by importance, so the map is never cluttered at any zoom.
import type maplibregl from 'maplibre-gl';
import type { Feature, Geometry, Position } from 'geojson';
import { loadLevel, loadUnits, type Base } from './data';
import { token } from './theme';

interface City {
  name: string;
  lng: number;
  lat: number;
  pop: number;
}
interface Lake {
  name: string;
  lng: number;
  lat: number;
  /** longer side of the lake's bounding box in degrees of longitude (a size measure) */
  span: number;
}
export interface RefData {
  cities: City[];
  lakes: Lake[];
  /** smallest place labelled at a zoom (default: towns of 2,000+ only; the older-boundaries map names every
   *  municipality when zoomed in, so a former village can be found, B5) */
  floor?: (zoom: number) => number;
}

/** Lakes with their label points (for reference layers built elsewhere, e.g. the older-boundaries map). */
export const lakesOf = (fc: { features: unknown[] }): Lake[] =>
  fc.features.map((f) => lakeOf(f as Feature<Geometry>)).filter((l): l is Lake => l !== null);

/** Interior label point of a polygon ring: the middle of the widest chord at the ring's centroid height
 *  (the centroid itself can lie on land for a bent lake). */
function labelPoint(ring: Position[]): [number, number] {
  let a = 0, cx = 0, cy = 0;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const f = ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1];
    a += f;
    cx += (ring[j][0] + ring[i][0]) * f;
    cy += (ring[j][1] + ring[i][1]) * f;
  }
  if (a === 0) return [ring[0][0], ring[0][1]];
  cx /= 3 * a;
  cy /= 3 * a;
  const xs: number[] = [];
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [x1, y1] = ring[j];
    const [x2, y2] = ring[i];
    if (y1 > cy !== y2 > cy) xs.push(x1 + ((cy - y1) / (y2 - y1)) * (x2 - x1));
  }
  xs.sort((p, q) => p - q);
  let best = -1, bx = cx;
  for (let k = 0; k + 1 < xs.length; k += 2) {
    if (xs[k + 1] - xs[k] > best) {
      best = xs[k + 1] - xs[k];
      bx = (xs[k] + xs[k + 1]) / 2;
    }
  }
  return [bx, cy];
}

function lakeOf(f: Feature<Geometry>): Lake | null {
  const name = (f.properties as { name?: string } | null)?.name;
  const g = f.geometry;
  if (!name || !g) return null;
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
  let best: Position[] | null = null, bestA = -1;
  for (const p of polys) {
    const r = p[0];
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const [x, y] of r) {
      if (x < x0) x0 = x;
      if (x > x1) x1 = x;
      if (y < y0) y0 = y;
      if (y > y1) y1 = y;
    }
    const area = (x1 - x0) * (y1 - y0);
    if (area > bestA) {
      bestA = area;
      best = r;
    }
  }
  if (!best) return null;
  const xs = best.map((p) => p[0]);
  const ys = best.map((p) => p[1]);
  const [lng, lat] = labelPoint(best);
  const w = Math.max(...xs) - Math.min(...xs);
  const h = (Math.max(...ys) - Math.min(...ys)) * 1.45; // degrees of latitude are longer than of longitude here
  return { name, lng, lat, span: Math.max(w, h) };
}

let refP: Promise<RefData> | null = null;
/** Cities (municipalities with at least 2,000 residents, by population) and lakes. */
export function loadRefData(base: Base): Promise<RefData> {
  refP ??= Promise.all([loadLevel('gemeinde'), loadUnits()]).then(([ld, rows]) => {
    const pop = ld.core.metrics.pop_total;
    const cities: City[] = [];
    if (pop) {
      for (const r of rows) {
        if (r.level !== 'gemeinde' || !r.label) continue;
        const i = ld.index.get(r.id);
        const p = i === undefined ? null : pop.v[i];
        if (p === null || p === undefined || p < 2000) continue;
        // names with a canton suffix ("Buchs (SG)") are shown without it
        cities.push({ name: r.name.replace(/\s*\([A-Z]{2}\)$/, ''), lng: r.label[0], lat: r.label[1], pop: p });
      }
      cities.sort((a, b) => b.pop - a.pop);
    }
    const lakes = base.lakes.features.map((f) => lakeOf(f as Feature<Geometry>)).filter((l): l is Lake => l !== null);
    return { cities, lakes };
  });
  refP.catch(() => (refP = null));
  return refP;
}

interface Placed {
  text: string;
  x: number;
  y: number;
  kind: 'city' | 'lake';
  size: number;
  align: 'left' | 'right' | 'center';
  /** gap between the point and the text (px) */
  gap: number;
  /** draw the city's own dot (not where the reach hub dot sits) */
  dot: boolean;
}

/** Smallest city shown at a zoom level (the placement then thins the rest out by collisions). */
function minPop(z: number): number {
  // D7: only places of 50,000+ at the initial (national) zoom
  return z < 7 ? 50000 : z < 8 ? 28000 : z < 8.8 ? 13000 : z < 9.6 ? 6500 : z < 10.5 ? 3500 : 2000;
}
// D7 / D1: city labels 11 px / 600 at least (13 and 12 px for the largest cities when there is room)
const citySize = (pop: number, narrow: boolean) => (narrow ? 11 : pop >= 100000 ? 13 : pop >= 30000 ? 12 : 11);
const cityWeight = (size: number) => (size >= 12 ? 650 : 600);
/** D16: label halo 2.5 px (the stroke straddles the glyph outline, so twice that) */
const HALO = 5;

export class RefLayer {
  private canvas: HTMLCanvasElement;
  private g: CanvasRenderingContext2D;
  private data: RefData | null = null;
  private visible = true;
  private placed: Placed[] = [];
  private widths = new Map<string, number>();
  private avoid: [number, number] | null = null;

  constructor(private map: maplibregl.Map, parent: HTMLElement) {
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'ref-canvas';
    this.canvas.setAttribute('aria-hidden', 'true');
    parent.appendChild(this.canvas);
    this.g = this.canvas.getContext('2d')!;
    map.on('render', () => this.draw());
    map.on('resize', () => this.draw());
  }

  setData(d: RefData | null) {
    this.data = d;
    this.draw();
  }
  /** D16: a point whose own marker is drawn elsewhere (the reach hub): a city label there moves clear of it */
  setAvoid(p: [number, number] | null) {
    this.avoid = p;
    this.draw();
  }
  setVisible(v: boolean) {
    this.visible = v;
    this.draw();
  }

  private font(kind: 'city' | 'lake', size: number) {
    return `${kind === 'lake' ? 'italic 500' : cityWeight(size)} ${size}px ${token('--font-sans') || 'sans-serif'}`;
  }
  private width(g: CanvasRenderingContext2D, text: string, font: string): number {
    const k = font + '|' + text;
    let w = this.widths.get(k);
    if (w === undefined) {
      g.font = font;
      w = g.measureText(text).width;
      this.widths.set(k, w);
    }
    return w;
  }

  /** Decide which labels fit (greedy by importance) and remember them for drawing and export. */
  private place(g: CanvasRenderingContext2D, W: number, H: number) {
    this.placed = [];
    const d = this.data;
    if (!d || !this.visible) return;
    const m = this.map;
    const z = m.getZoom();
    // pixels per degree of longitude at this zoom
    const ppd = (512 * 2 ** z) / 360;
    const boxes: [number, number, number, number][] = [];
    const free = (b: [number, number, number, number]) => {
      if (b[0] < 2 || b[1] < 2 || b[2] > W - 2 || b[3] > H - 2) return false;
      for (const o of boxes) if (b[0] < o[2] + 3 && b[2] > o[0] - 3 && b[1] < o[3] + 2 && b[3] > o[1] - 2) return false;
      return true;
    };
    // lakes first when large enough for their name, then cities by population, then the other lakes
    const floor = d.floor ? d.floor(z) : minPop(z);
    const av = this.avoid ? m.project(this.avoid) : null;
    // the hub dot (radius 5.5) is an obstacle for every other label
    if (av) boxes.push([av.x - 6, av.y - 6, av.x + 6, av.y + 6]);
    type Cand = { kind: 'city'; c: City } | { kind: 'lake'; l: Lake };
    const cands: Cand[] = [];
    for (const c of d.cities) {
      if (c.pop < floor) break;
      cands.push({ kind: 'city', c });
    }
    for (const l of d.lakes) cands.push({ kind: 'lake', l });
    const score = (c: Cand) => (c.kind === 'city' ? c.c.pop : 22000 + c.l.span * 40000);
    cands.sort((a, b) => score(b) - score(a));
    for (const cd of cands) {
      if (cd.kind === 'city') {
        const c = cd.c;
        const p = m.project([c.lng, c.lat]);
        if (p.x < -20 || p.y < -20 || p.x > W + 20 || p.y > H + 20) continue;
        const size = citySize(c.pop, W < 600);
        const w = this.width(g, c.name, this.font('city', size));
        // next to the reach hub dot (radius 5.5): no own dot, the text set further out
        const onHub = !!av && Math.hypot(av.x - p.x, av.y - p.y) < 24;
        const gap = onHub ? 13 : 5;
        const cx = onHub ? av!.x : p.x;
        const cy = onHub ? av!.y : p.y;
        let align: Placed['align'] = 'left';
        // the box covers the city's own dot, but not the hub dot (an obstacle of its own)
        const dot = onHub ? -gap + 2 : 3.5;
        let box: [number, number, number, number] = [cx - dot, cy - size / 2 - 1, cx + gap + w, cy + size / 2 + 1];
        if (!free(box)) {
          align = 'right';
          box = [cx - gap - w, cy - size / 2 - 1, cx + dot, cy + size / 2 + 1];
          if (!free(box)) continue;
        }
        boxes.push(box);
        this.placed.push({ text: c.name, x: cx, y: cy, kind: 'city', size, align, gap, dot: !onHub });
      } else {
        const l = cd.l;
        // a lake is named once it is long enough on screen to carry a name
        if (l.span * ppd < 46) continue;
        const p = m.project([l.lng, l.lat]);
        const size = l.span * ppd > 130 ? 12 : 11;
        const w = this.width(g, l.name, this.font('lake', size));
        const box: [number, number, number, number] = [p.x - w / 2, p.y - size / 2 - 1, p.x + w / 2, p.y + size / 2 + 1];
        if (!free(box)) continue;
        boxes.push(box);
        this.placed.push({ text: l.name, x: p.x, y: p.y, kind: 'lake', size, align: 'center', gap: 0, dot: false });
      }
    }
  }

  private paint(g: CanvasRenderingContext2D, scale: number) {
    g.setTransform(scale, 0, 0, scale, 0, 0);
    g.textBaseline = 'middle';
    g.lineJoin = 'round';
    const ink = token('--ink') || '#000';
    const lake = token('--lake-label') || '#3d6079';
    const halo = token('--panel') || '#fff';
    for (const p of this.placed) {
      const font = this.font(p.kind, p.size);
      g.font = font;
      g.textAlign = p.align === 'center' ? 'center' : p.align === 'left' ? 'left' : 'right';
      const tx = p.align === 'left' ? p.x + p.gap : p.align === 'right' ? p.x - p.gap : p.x;
      g.lineWidth = HALO;
      g.strokeStyle = halo;
      g.strokeText(p.text, tx, p.y);
      g.fillStyle = p.kind === 'lake' ? lake : ink;
      g.fillText(p.text, tx, p.y);
      if (p.kind === 'city' && p.dot) {
        g.beginPath();
        g.arc(p.x, p.y, 2.3, 0, Math.PI * 2);
        g.fillStyle = halo;
        g.fill();
        g.beginPath();
        g.arc(p.x, p.y, 1.6, 0, Math.PI * 2);
        g.fillStyle = ink;
        g.fill();
      }
    }
  }

  draw() {
    const el = this.map.getContainer();
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const w = el.clientWidth;
    const h = el.clientHeight;
    if (this.canvas.width !== Math.round(w * dpr) || this.canvas.height !== Math.round(h * dpr)) {
      this.canvas.width = Math.round(w * dpr);
      this.canvas.height = Math.round(h * dpr);
      this.canvas.style.width = `${w}px`;
      this.canvas.style.height = `${h}px`;
    }
    const g = this.g;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.place(g, w, h);
    this.paint(g, dpr);
  }

  /** The labels as drawn now, on a transparent canvas of the map's export size (for the PNG export). */
  snapshot(width: number, height: number, scale: number): HTMLCanvasElement | null {
    if (!this.visible || !this.placed.length) return null;
    const c = document.createElement('canvas');
    c.width = width;
    c.height = height;
    this.paint(c.getContext('2d')!, scale);
    return c;
  }
}
