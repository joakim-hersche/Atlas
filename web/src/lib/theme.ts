// Colour tokens shared by CSS and the map. CSS owns the UI values (app.css); the map reads them.
// Dark when the host sets data-theme="dark", or when no explicit theme is set and the OS is dark.
const mq = window.matchMedia('(prefers-color-scheme: dark)');
const root = document.documentElement;
const listeners = new Map<() => void, MutationObserver>();
export const dark = {
  get matches(): boolean {
    const t = root.getAttribute('data-theme');
    return t === 'dark' || (t !== 'light' && mq.matches);
  },
  addEventListener(_type: 'change', cb: () => void) {
    mq.addEventListener('change', cb);
    const mo = new MutationObserver(cb);
    mo.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    listeners.set(cb, mo);
  },
  removeEventListener(_type: 'change', cb: () => void) {
    mq.removeEventListener('change', cb);
    listeners.get(cb)?.disconnect();
    listeners.delete(cb);
  },
};

export function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// ---------------------------------------------------------------- data colour scales
// Sequential: one steel-blue hue, monotone in lightness (checked with the dataviz validator).
// Light: low = pale, high = dark. Dark: low recedes into the dark surface, high is bright.
const SEQ_LIGHT = ['#d3e0ec', '#9dbad5', '#6290bb', '#356799', '#173f68'];
const SEQ_DARK = ['#21364c', '#2f5880', '#4a7fb0', '#80aad3', '#c6dbee'];

// Diverging: orange (negative) – grey (0) – blue (positive), 3 steps per arm.
const DIV_LIGHT = ['#a4541f', '#d98a55', '#f0c9a8', '#e3e5e8', '#b3c8dc', '#6290bb', '#244f7c'];
const DIV_DARK = ['#f0a46c', '#b06a3a', '#5e4332', '#33383e', '#2f4a66', '#4f80b2', '#a6c6e6'];

// Language regions (BFS Sprachgebiete 1–4): fixed order, validated all-pairs for CVD;
// Romansh (few municipalities) takes a neutral grey and is always labelled in the legend.
const REGION_LIGHT = ['#2a78d6', '#eb6834', '#1baf7a', '#6b7079'];
const REGION_DARK = ['#3987e5', '#d95926', '#199e70', '#b9bec5'];

export const seqRamp = (isDark = dark.matches) => (isDark ? SEQ_DARK : SEQ_LIGHT);
export const divRamp = (isDark = dark.matches) => (isDark ? DIV_DARK : DIV_LIGHT);
export const regionColours = (isDark = dark.matches) => (isDark ? REGION_DARK : REGION_LIGHT);

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
