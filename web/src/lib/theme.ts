// Colour tokens shared by CSS and the map. CSS owns the UI values (app.css); the map reads them.
// The site is light only (decision D29: white Swiss style).
export function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// ---------------------------------------------------------------- data colour scales
// Sequential: one steel-blue hue, monotone in lightness (checked with the dataviz validator): low = pale, high = dark.
const SEQ = ['#d3e0ec', '#9dbad5', '#6290bb', '#356799', '#173f68'];
// Diverging: orange (negative) – grey (0) – blue (positive), 3 steps per arm (the same values as the --div-* tokens
// in app.css; D10: the dark 'no' end is #b5602a, lighter than before, so it reads as a colour, not as black).
const DIV = ['#b5602a', '#e0965f', '#f3cfae', '#e6e8eb', '#b3c8dc', '#6290bb', '#244f7c'];
// Language regions (BFS Sprachgebiete 1–4) in scatter and residual plots (D15): German dark grey, French teal,
// Italian ochre, Romansh violet; always labelled in the legend.
const REGION = ['#3d3d3d', '#1f8a8a', '#d9a21b', '#8a63b8'];

export const seqRamp = () => SEQ;
export const divRamp = () => DIV;
export const regionColours = () => REGION;

// ---------------------------------------------------------------- colour helpers
type RGB = [number, number, number];
export function hexToRgb(h: string): RGB {
  const s = h.replace('#', '');
  const n = parseInt(s.length === 3 ? s.replace(/./g, (c) => c + c) : s, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
export function rgbToHex([r, g, b]: RGB): string {
  return '#' + [r, g, b].map((x) => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, '0')).join('');
}

/** Linear interpolation through a list of hex stops, t in 0..1. */
export function interpolate(stops: string[], t: number): string {
  const x = Math.max(0, Math.min(1, t)) * (stops.length - 1);
  const k = Math.min(stops.length - 2, Math.floor(x));
  const f = x - k;
  const a = hexToRgb(stops[k]);
  const b = hexToRgb(stops[k + 1]);
  return rgbToHex([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]);
}

/** Tint a colour toward white, keeping its hue (unstable small-number values drawn lighter). */
export function lighten(hex: string, amount: number): string {
  const [r, g, b] = hexToRgb(hex);
  return rgbToHex([r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount]);
}

/** Desaturate a colour and pull it toward the map surface (for filtered-out or unreached units). */
export function mute(hex: string, surface: string, amount: number): string {
  const [r, g, b] = hexToRgb(hex);
  const [sr, sg, sb] = hexToRgb(surface);
  const y = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const k = amount;
  // grey with the same luminance, then blended toward the surface
  const gr = y + (r - y) * (1 - k);
  const gg = y + (g - y) * (1 - k);
  const gb = y + (b - y) * (1 - k);
  const s = 0.55 * k;
  return rgbToHex([gr + (sr - gr) * s, gg + (sg - gg) * s, gb + (sb - gb) * s]);
}
