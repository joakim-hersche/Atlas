// Export (D32): CSV of a table, TSV to the clipboard, PNG of the map or a chart with a source line and the
// link to the view. Downloads use a Blob and a temporary <a download> click (works on iPhone Safari).
import type maplibregl from 'maplibre-gl';
import { token } from './theme';

export type Cell = string | number | null | undefined;

/** Start a download of a Blob under a file name. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

/** File-name-safe slug: 'Population density' -> 'population-density'. */
export function slug(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'export';
}

/** Plain machine-readable number: full precision of the data, '.' decimals, no grouping. */
const plain = (c: Cell) => (c === null || c === undefined ? '' : typeof c === 'number' ? (Number.isFinite(c) ? String(c) : '') : c);

/** RFC 4180 CSV (comma, quotes doubled, CRLF). */
export function toCSV(rows: Cell[][]): string {
  const q = (c: Cell) => {
    const s = plain(c);
    return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return rows.map((r) => r.map(q).join(',')).join('\r\n') + '\r\n';
}

/** CSV download, UTF-8 with a byte-order mark so Excel reads umlauts and accents correctly. */
export function downloadCSV(rows: Cell[][], filename: string): void {
  downloadBlob(new Blob(['﻿' + toCSV(rows)], { type: 'text/csv;charset=utf-8' }), filename);
}

/** Tab-separated text (pastes into a spreadsheet as cells). */
export function toTSV(rows: Cell[][]): string {
  return rows.map((r) => r.map((c) => plain(c).replace(/[\t\r\n]+/g, ' ')).join('\t')).join('\n');
}

/** Copy text to the clipboard; falls back to a hidden textarea where the async API is missing. */
export async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* fall through */
  }
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.setAttribute('readonly', '');
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  }
  ta.remove();
  return ok;
}

/** Attribution text without a leading "Source:" / "Quelle:" (the export adds its own label). */
export const bareAttribution = (s: string) => s.replace(/^\s*(source|sources|quelle|quellen)\s*:\s*/i, '');

// ---------------------------------------------------------------- PNG
/** A copy of the map's WebGL canvas, taken right after a frame is drawn (no preserveDrawingBuffer needed). */
export function grabMap(map: maplibregl.Map): Promise<HTMLCanvasElement> {
  return new Promise((resolve) => {
    map.once('render', () => {
      const c = map.getCanvas();
      const out = document.createElement('canvas');
      out.width = c.width;
      out.height = c.height;
      out.getContext('2d')!.drawImage(c, 0, 0);
      resolve(out);
    });
    map.triggerRepaint();
  });
}

export interface LegendItem {
  colour: string | null; // null = hatched "no data"
  label: string;
  /** pattern of a null colour: the no-data hatch (default) or the dots of single-seat cantons (D37) */
  pattern?: 'hatch' | 'dots';
}

export interface Figure {
  /** images drawn on top of each other (the map, then the reach overlay), all the same pixel size */
  layers: HTMLCanvasElement[];
  /** device pixels per CSS pixel of the layers */
  scale: number;
  title: string;
  subtitle: string;
  legend: LegendItem[];
  /** a gradient instead of class swatches (continuous scales): colours from low to high, end labels */
  gradient?: { colours: string[]; lo: string; hi: string } | null;
  /** B3: what the two ends of a diverging scale mean ("← No", "Yes →"), drawn under the swatches */
  sides?: { left: string; right: string; leftColour?: string; rightColour?: string } | null;
  /** B3: patterns and notes explained under the legend (one line each) */
  notes?: string[];
  /** source and credit lines */
  credits: string[];
  /** link to the view (printed in full) */
  link: string;
}

function dots(g: CanvasRenderingContext2D, x: number, y: number, w: number, h: number) {
  g.save();
  g.fillStyle = token('--surface-2') || '#f4f4f4';
  g.fillRect(x, y, w, h);
  g.fillStyle = '#9a9a9a';
  for (let yy = y + 2; yy < y + h; yy += 4) for (let xx = x + 2; xx < x + w; xx += 4) g.fillRect(xx - 0.75, yy - 0.75, 1.5, 1.5);
  g.strokeStyle = token('--nodata-line') || '#9a9a9a';
  g.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  g.restore();
}

function hatch(g: CanvasRenderingContext2D, x: number, y: number, w: number, h: number) {
  g.save();
  g.fillStyle = token('--nodata-fill') || '#f0f0f0';
  g.fillRect(x, y, w, h);
  g.beginPath();
  g.rect(x, y, w, h);
  g.clip();
  g.strokeStyle = token('--nodata-line') || '#9a9a9a';
  g.lineWidth = 1;
  for (let k = -h; k < w; k += 4) {
    g.moveTo(x + k, y + h);
    g.lineTo(x + k + h, y);
  }
  g.stroke();
  g.restore();
}

/** Wrap text into lines that fit `max` px. */
function wrap(g: CanvasRenderingContext2D, text: string, max: number): string[] {
  const out: string[] = [];
  let line = '';
  for (const w of text.split(/\s+/)) {
    const next = line ? `${line} ${w}` : w;
    if (g.measureText(next).width > max && line) {
      out.push(line);
      line = w;
    } else line = next;
  }
  if (line) out.push(line);
  return out;
}

/** Compose a figure (title, image, legend, sources, link) into a PNG Blob. */
export async function figurePNG(f: Figure): Promise<Blob> {
  const s = f.scale;
  const W = f.layers[0].width;
  const pad = 16 * s;
  const sans = getComputedStyle(document.documentElement).getPropertyValue('--font-sans') || 'sans-serif';
  const measure = document.createElement('canvas').getContext('2d')!;
  const font = (wt: number, px: number) => `${wt} ${px * s}px ${sans}`;

  // layout pass: heights of the text blocks
  measure.font = font(700, 18);
  const titleLines = wrap(measure, f.title, W - 2 * pad);
  measure.font = font(400, 12);
  const subLines = f.subtitle ? f.subtitle.split('\n').flatMap((p) => wrap(measure, p, W - 2 * pad)) : [];
  measure.font = font(400, 11);
  const legendRows: { items: LegendItem[] }[] = [];
  {
    let row: LegendItem[] = [];
    let x = 0;
    for (const it of f.legend) {
      const w = 14 * s + 6 * s + measure.measureText(it.label).width + 14 * s;
      if (x + w > W - 2 * pad && row.length) {
        legendRows.push({ items: row });
        row = [];
        x = 0;
      }
      row.push(it);
      x += w;
    }
    if (row.length) legendRows.push({ items: row });
  }
  measure.font = font(400, 10.5);
  const noteLines = (f.notes ?? []).flatMap((n) => wrap(measure, n, W - 2 * pad));
  const creditLines = [...f.credits.flatMap((c) => wrap(measure, c, W - 2 * pad)), ...wrap(measure, f.link, W - 2 * pad)];
  const lh = (px: number) => px * 1.35 * s;
  const head = pad + titleLines.length * lh(18) + subLines.length * lh(12) + 8 * s;
  const legH = (f.gradient ? 30 * s : 0) + legendRows.length * lh(11) + (legendRows.length ? 6 * s : 0) + 8 * s + (f.sides ? lh(11) + 2 * s : 0);
  const foot = legH + (noteLines.length ? noteLines.length * lh(10.5) + 4 * s : 0) + creditLines.length * lh(10.5) + pad;
  const H = head + f.layers[0].height + foot;

  const c = document.createElement('canvas');
  c.width = W;
  c.height = Math.ceil(H);
  const g = c.getContext('2d')!;
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, W, H);
  g.fillStyle = '#000000';
  g.textBaseline = 'top';
  let y = pad;
  g.font = font(700, 18);
  for (const l of titleLines) {
    g.fillText(l, pad, y);
    y += lh(18);
  }
  g.font = font(400, 12);
  g.fillStyle = '#3d3d3d';
  for (const l of subLines) {
    g.fillText(l, pad, y);
    y += lh(12);
  }
  // heavy rule under the title (Swiss style)
  g.fillStyle = '#000000';
  g.fillRect(pad, head - 4 * s, W - 2 * pad, 2 * s);
  for (const layer of f.layers) g.drawImage(layer, 0, head, W, f.layers[0].height);
  y = head + f.layers[0].height + 8 * s;
  g.fillRect(pad, y - 4 * s, W - 2 * pad, 1 * s);
  // legend
  g.font = font(400, 11);
  if (f.gradient) {
    const gw = Math.min(260 * s, W - 2 * pad);
    const grad = g.createLinearGradient(pad, 0, pad + gw, 0);
    f.gradient.colours.forEach((col, k) => grad.addColorStop(k / Math.max(1, f.gradient!.colours.length - 1), col));
    g.fillStyle = grad;
    g.fillRect(pad, y, gw, 10 * s);
    g.fillStyle = '#000000';
    g.fillText(f.gradient.lo, pad, y + 13 * s);
    g.textAlign = 'right';
    g.fillText(f.gradient.hi, pad + gw, y + 13 * s);
    g.textAlign = 'left';
    y += 30 * s;
  }
  {
    for (const r of legendRows) {
      let x = pad;
      for (const it of r.items) {
        if (it.colour) {
          g.fillStyle = it.colour;
          g.fillRect(x, y + 1 * s, 14 * s, 10 * s);
        } else if (it.pattern === 'dots') dots(g, x, y + 1 * s, 14 * s, 10 * s);
        else hatch(g, x, y + 1 * s, 14 * s, 10 * s);
        g.fillStyle = '#000000';
        g.fillText(it.label, x + 20 * s, y);
        x += 20 * s + g.measureText(it.label).width + 14 * s;
      }
      y += lh(11);
    }
    y += legendRows.length ? 6 * s : 0;
  }
  // the meaning of the two ends of a diverging scale
  if (f.sides) {
    g.font = font(600, 11);
    g.fillStyle = f.sides.leftColour || '#000000';
    g.fillText(`← ${f.sides.left}`, pad, y);
    g.textAlign = 'right';
    g.fillStyle = f.sides.rightColour || '#000000';
    g.fillText(`${f.sides.right} →`, W - pad, y);
    g.textAlign = 'left';
    y += lh(11) + 2 * s;
  }
  if (noteLines.length) {
    g.font = font(400, 10.5);
    g.fillStyle = '#000000';
    for (const l of noteLines) {
      g.fillText(l, pad, y);
      y += lh(10.5);
    }
    y += 4 * s;
  }
  // sources and the link to the view
  g.font = font(400, 10.5);
  g.fillStyle = '#3d3d3d';
  for (const l of creditLines) {
    g.fillText(l, pad, y);
    y += lh(10.5);
  }
  return new Promise((resolve, reject) => c.toBlob((b) => (b ? resolve(b) : reject(new Error('PNG export failed'))), 'image/png'));
}
