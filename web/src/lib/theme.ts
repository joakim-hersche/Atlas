// Colour tokens shared by CSS and the map. CSS owns the values (app.css); the map reads them.
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

// Viridis samples (perceptually uniform, readable with colour-vision deficiency).
// Light mode: low = light yellow, high = dark purple ("darker = higher").
// Dark mode: the ramp is flipped so that high stands out from the dark background ("brighter = higher").
const VIRIDIS_LIGHT = ['#fde725', '#5ec962', '#21918c', '#3b528b', '#440154'];
const VIRIDIS_DARK = ['#3e2f78', '#335f8c', '#21918c', '#4ac16d', '#fde725'];

export function ramp(isDark = dark.matches): string[] {
  return isDark ? VIRIDIS_DARK : VIRIDIS_LIGHT;
}

export function rampWord(isDark = dark.matches): string {
  return isDark ? 'Brighter' : 'Darker';
}
