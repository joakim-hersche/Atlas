// Colours and labels for the spatial map modes: the cluster map (LISA) and the bivariate 3x3 map.
//
// Bivariate (D6): Joshua Stevens' blue-pink 3x3 scheme. The shade metric runs along the horizontal axis
// (#e8e8e8 -> #5ac8c8, teal-blue), the second metric up the vertical axis (#e8e8e8 -> #be64ac, pink); the
// corner where both are high is #3b4994. Rows bottom to top as in his legend.
//
// LISA: dark red for high-high (D4: #b2182b, not the brand red), blue for low-low, pale red / pale blue for the
// outliers, light grey for places without a significant pattern.

/** cell index = 3 * (third of the second metric) + (third of the shade metric) */
export const BIVARIATE = [
  '#e8e8e8', '#ace4e4', '#5ac8c8', // second metric low:  shade low, mid, high
  '#dfb0d6', '#a5add3', '#5698b9', // second metric mid
  '#be64ac', '#8c62aa', '#3b4994', // second metric high
];

export const LISA_COLOURS = {
  hh: '#b2182b',
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
