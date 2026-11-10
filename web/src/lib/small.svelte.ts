// Small numbers for any period (B1): the latest values carry the build's flags (bits 1/2, special 64); a past
// year read from a series file is judged by the metric's own rule on the base and count values of that year
// (both shipped). Shared by the map, the years-side-by-side panels and the change map. Nothing is estimated.
import type { ColRef, LevelData, MetricMeta } from './data';
import { attachedFrom, isUnstable } from './data';
import type { ColumnStore } from './columns.svelte';
import { ruleTerms, ruleUnstable, sumColumns } from './reliability';

/** the rule a period can be judged by (pooled 3-year windows are judged on the window: latest flags only) */
export const periodRule = (meta: MetricMeta) => (meta.reliability && (meta.reliability.years ?? 1) === 1 ? meta.reliability : null);

/** Indices of the units whose value of `ref` rests on small numbers. Reactive (reads the column store);
 *  while a base or count column is loading, the shipped flags alone are returned. */
export function unstableIndices(cols: ColumnStore, ld: LevelData, meta: MetricMeta, ref: ColRef | null | undefined): number[] {
  if (!ref) return [];
  const out = new Set<number>();
  const f = ref.col.f;
  if (f) for (const k of Object.keys(f)) if (isUnstable(ref.file, f[k]) && ref.col.v[+k] !== null) out.add(+k);
  // a regional value attached to municipalities is judged at its own level (no rule on municipal bases)
  if (attachedFrom(meta, ld.level)) return [...out];
  const rule = periodRule(meta);
  if (!ref.file && rule) {
    const period = ref.col.period;
    const terms = ruleTerms(rule);
    const get = (ids: string[], mean = false) => {
      const cs = ids.map((id) => cols.get(ld, id, period));
      if (cs.some((c) => c === undefined)) return undefined;
      // a term without this period (or not at this level) cannot judge it
      if (cs.some((c) => !c || c.col.period !== period)) return null;
      const sum = sumColumns(cs.map((c) => c!.col.v));
      return mean && sum ? sum.map((x) => (x === null ? null : x / ids.length)) : sum;
    };
    const base = get(terms.base, terms.baseMean);
    const count = get(terms.count, terms.countMean);
    if (base !== undefined && count !== undefined) for (const i of ruleUnstable(ref.col.v, rule, base, count, meta.special?.max)) out.add(i);
  } else if (!ref.file && meta.special?.max !== undefined) {
    for (const i of ruleUnstable(ref.col.v, null, null, null, meta.special.max)) out.add(i);
  }
  return [...out].sort((a, b) => a - b);
}
