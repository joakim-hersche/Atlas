// Breaks in a metric's series (change of method or definition), as the build ships them in metrics.json:
// `series_breaks` = period -> {label_en, label_de, label_fr} (also accepted: period -> text, or a list of
// periods). The marked period is the first one on the new basis. Pure helpers, no app state.

export type BreakNote = { label_en?: string; label_de?: string; label_fr?: string } | string;
export type SeriesBreaks = Record<string, BreakNote> | string[] | null | undefined;

/** The metric's `series_breaks` (typed apart from MetricMeta, which older builds lack it on). */
export function seriesBreaksOf(meta: unknown): SeriesBreaks {
  return (meta as { series_breaks?: SeriesBreaks } | null)?.series_breaks ?? null;
}

/** period -> note in the UI language (null when the build ships only the period; English as fallback) */
export function breakNotes(sb: SeriesBreaks, lang: string): Map<string, string | null> {
  const out = new Map<string, string | null>();
  if (!sb) return out;
  if (Array.isArray(sb)) {
    for (const p of sb) out.set(p, null);
    return out;
  }
  for (const [p, v] of Object.entries(sb)) {
    if (typeof v === 'string') out.set(p, v || null);
    else out.set(p, (lang === 'de' ? v.label_de : lang === 'fr' ? v.label_fr : v.label_en) || v.label_en || null);
  }
  return out;
}

/** Break periods between two periods of a metric: every marked p with from < p <= to in the order of
 *  `periods` (a comparison from..to then mixes values from both sides of p). Order of `periods` kept. */
export function breaksBetween(periods: string[], from: string | null, to: string | null, isBreak: (p: string) => boolean): string[] {
  if (!from || !to) return [];
  const a = periods.indexOf(from);
  const b = periods.indexOf(to);
  if (a < 0 || b < 0 || a >= b) return [];
  return periods.slice(a + 1, b + 1).filter(isBreak);
}

/** Position of a period on a continuous time axis (years; months as fractions), as the sparklines draw it. */
export function periodX(p: string): number {
  const y = Number(p.slice(0, 4));
  if (!/^\d{4}/.test(p) || !Number.isFinite(y)) return NaN;
  return y + (/^\d{4}-\d{2}$/.test(p) ? Number(p.slice(5, 7)) / 13 : 0);
}

/** Where to draw a break tick on a line through points at `xs` (ascending): halfway between the last point
 *  before the break and the first one on or after it. null when the break is not inside the drawn range. */
export function breakTickX(xs: number[], breakX: number): number | null {
  if (!Number.isFinite(breakX) || xs.length < 2) return null;
  let k = xs.findIndex((x) => x >= breakX);
  if (k <= 0) return null;
  return (xs[k - 1] + xs[k]) / 2;
}
