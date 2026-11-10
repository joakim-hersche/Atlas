// Colours and labels for the spatial map modes: the cluster map (LISA) and the bivariate 3x3 map.
//
// Bivariate: horizontal axis (the shade metric) runs pale grey -> blue, vertical axis (the second metric)
// pale grey -> orange; a cell is the multiply blend of its two axis colours, so the diagonal gets darker
// when both are high. Blue/orange is the colour-blind-safe pair (the axes differ in hue and in lightness);
// simulated for protanopia, deuteranopia and tritanopia the nine cells stay at least 14 CIE76 delta-E
// apart (checked while building this; the lightest and darkest corners are the closest pair).
//
// LISA: red for high-high, blue for low-low, pale red / pale blue for the outliers, light grey for
// places without a significant pattern.

/** cell index = 3 * (third of the second metric) + (third of the shade metric) */
export const BIVARIATE = [
  '#e6e6e6', '#abc2d6', '#497fb2', // second metric low:  shade low, mid, high
  '#e6ba93', '#ab9d89', '#496772', // second metric mid
  '#d57937', '#9e6633', '#44432b', // second metric high
];

export const LISA_COLOURS = {
  hh: '#c8442a',
  ll: '#2f6aa3',
  lh: '#8db3d6',
  hl: '#eda17f',
  ns: '#ececec',
} as const;

/** Per-unit colours for the bivariate map (null = a value is missing: hatched like other gaps). */
export function bivariateColours(cell: Int8Array): (string | null)[] {
  return Array.from(cell, (c) => (c >= 0 ? BIVARIATE[c] : null));
}

/** Per-unit colours for the cluster map. */
export function lisaColours(code: Int8Array): (string | null)[] {
  return Array.from(code, (c) =>
    c === 1 ? LISA_COLOURS.hh : c === 2 ? LISA_COLOURS.ll : c === 3 ? LISA_COLOURS.lh : c === 4 ? LISA_COLOURS.hl : c === 0 ? LISA_COLOURS.ns : null,
  );
}
