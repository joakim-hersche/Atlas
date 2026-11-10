// Comparing years on the map: change between two years as a metric, class limits fixed across all years
// (pooled values), and markers for periods that are not comparable with their neighbours.
// Everything is computed from the series files that already ship; nothing is estimated.
import { SvelteMap } from 'svelte/reactivity';
import { breakNotes, breaksBetween, seriesBreaksOf } from './breaks';
import { loadSeries, type Column, type MetricMeta } from './data';
import { ml, t } from './i18n.svelte';
import { app } from './state.svelte';
import './i18n-mapx';

// ---------------------------------------------------------------- pooled values (fixed class limits)
const pooled = new SvelteMap<string, number[] | null>();
const pending = new Set<string>();

/** All values of a metric at one level, all periods pooled, ascending: the distribution that defines the
 *  class limits when they are fixed across years. Periods the build marks as incomplete (a newer survey
 *  round with a fraction of the units) are left out, so the limits come from comparable rounds only.
 *  undefined = loading, null = no series file (then the current year's own classes are kept). */
export function pooledValues(meta: MetricMeta, level: string): number[] | null | undefined {
  const key = `${level}|${meta.id}`;
  const hit = pooled.get(key);
  if (hit !== undefined || pooled.has(key)) return hit;
  if (!pending.has(key)) {
    pending.add(key);
    loadSeries(meta.id)
      .then((s) => {
        pending.delete(key);
        const rows = s?.levels[level];
        if (!s || !rows) {
          pooled.set(key, null);
          return;
        }
        const skip = new Set(Object.keys(meta.incomplete_periods ?? {}));
        const keep = s.periods.map((p) => !skip.has(p));
        const out: number[] = [];
        for (const r of Object.values(rows)) {
          for (let k = 0; k < r.length; k++) {
            const x = r[k];
            if (keep[k] && x !== null && Number.isFinite(x)) out.push(x);
          }
        }
        out.sort((a, b) => a - b);
        pooled.set(key, out.length ? out : null);
      })
      .catch(() => {
        pending.delete(key);
        pooled.set(key, null);
      });
  }
  return undefined;
}

/** First and last period that went into the pooled values (for the legend note). */
export function pooledSpan(meta: MetricMeta): string {
  const skip = new Set(Object.keys(meta.incomplete_periods ?? {}));
  const ps = meta.periods.filter((p) => !skip.has(p));
  return ps.length ? `${ps[0]}–${ps[ps.length - 1]}` : '';
}

// ---------------------------------------------------------------- change between two years
export type ChangeMode = 'abs' | 'pct';

/** The metric describing a change between two periods (a synthetic metric: diverging scale around 0,
 *  no better/worse direction). `abs` is in the metric's unit (percentage points for a share), `pct` in
 *  percent of the earlier value. */
export function changeMeta(meta: MetricMeta, mode: ChangeMode, from: string, to: string): MetricMeta {
  const isPct = meta.unit.startsWith('%');
  const label = t(mode === 'abs' ? 'yc.labelAbs' : 'yc.labelPct', { metric: ml(meta), from, to });
  const common = { ...meta, id: `${meta.id}__chg_${mode}`, label_en: label, label_de: label, label_fr: label, direction: 'neutral' as const,
    aggregation: `change:${meta.id}`, headline: null, description: null, latest_title: null, per_vote: false, pooled: null };
  if (mode === 'pct') return { ...common, unit: '%', unit_de: '%', unit_fr: '%', decimals: 1 };
  if (isPct) return { ...common, unit: 'pp', unit_de: 'Pp.', unit_fr: 'pp', decimals: Math.max(1, meta.decimals) };
  return { ...common, decimals: meta.decimals };
}

/** Values of the change between two columns of the same level. A unit without a value in either period has
 *  none; a percent change needs a non-zero earlier value. */
export function changeValues(from: (number | null)[], to: (number | null)[], mode: ChangeMode): (number | null)[] {
  return to.map((x, i) => {
    const a = from[i];
    if (x === null || x === undefined || a === null || a === undefined) return null;
    if (mode === 'abs') return round(x - a, 6);
    return a === 0 ? null : round(((x - a) / Math.abs(a)) * 100, 4);
  });
}
const round = (x: number, d: number) => Math.round(x * 10 ** d) / 10 ** d;

export function changeColumn(from: Column, to: Column, mode: ChangeMode): Column {
  return { period: `${from.period}→${to.period}`, v: changeValues(from.v, to.v, mode) };
}

// ---------------------------------------------------------------- series-break markers
export interface PeriodMark {
  kind: 'incomplete' | 'break';
  text: string;
}

/** Periods of a metric that are not comparable with their neighbours, from what the build ships:
 *  `incomplete_periods` (a newer round with only part of the units) and, when a build ships them,
 *  `series_breaks` (period -> note, or a list of periods, for changes of method or definition). */
export function periodMarks(meta: MetricMeta): Map<string, PeriodMark> {
  const out = new Map<string, PeriodMark>();
  for (const [p, ip] of Object.entries(meta.incomplete_periods ?? {})) {
    const lang = app.lang;
    const label = lang === 'de' ? ip.label_de : lang === 'fr' ? ip.label_fr : null;
    out.set(p, { kind: 'incomplete', text: label ?? ip.label_en ?? t('yc.incomplete') });
  }
  for (const [p, txt] of breakNotes(seriesBreaksOf(meta), app.lang)) {
    const prev = out.get(p);
    // a break and an incomplete round on the same period: the break is what matters for comparisons
    out.set(p, { kind: 'break', text: prev ? `${txt ?? t('yc.break')} · ${prev.text}` : (txt ?? t('yc.break')) });
  }
  return out;
}

/** Breaks in the series that a comparison from..to straddles (periods on the new basis, oldest first). */
export function straddled(meta: MetricMeta, periods: string[], from: string | null, to: string | null, marks = periodMarks(meta)): { p: string; text: string }[] {
  return breaksBetween(periods, from, to, (p) => marks.get(p)?.kind === 'break').map((p) => ({ p, text: marks.get(p)!.text }));
}

// ---------------------------------------------------------------- small multiples
/** About six evenly spaced periods, the first and the last included. */
export function defaultPeriods(ps: string[]): string[] {
  if (ps.length <= 6) return ps.slice();
  return Array.from({ length: 6 }, (_, k) => ps[Math.round((k * (ps.length - 1)) / 5)]);
}
