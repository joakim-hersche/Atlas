<script lang="ts">
  // Aggregate of one metric over the filtered set ("French-speaking CH: 62.1 % yes"), computed by
  // the metric's own aggregation rule (lib/aggregate.ts). Shown under the match count. For metrics
  // that cannot be aggregated the reason is given instead of a figure.
  import { ml, t } from '../lib/i18n.svelte';
  import { fmtNumber, fmtPeriod, unitOf } from '../lib/classify';
  import type { ColView } from '../lib/columns.svelte';
  import type { MetricMeta } from '../lib/data';
  import { aggregate } from '../lib/aggregate';
  import MetricPicker from './MetricPicker.svelte';

  interface Props {
    metrics: MetricMeta[];
    metas: Map<string, MetricMeta>;
    level: string;
    nUnits: number;
    /** the set: 1 = matches */
    mask: Uint8Array;
    nMatch: number;
    metricId: string;
    getCol: (id: string) => ColView | null | undefined;
    unitWord: string;
    onpick: (id: string) => void;
  }
  let { metrics, metas, level, nUnits, mask, nMatch, metricId, getCol, unitWord, onpick }: Props = $props();

  const meta = $derived(metas.get(metricId));
  const own = $derived(meta ? getCol(meta.id) : null);
  const res = $derived(meta ? aggregate(meta, own, getCol, mask, nUnits) : null);
  const ruleText = $derived.by(() => {
    if (!res || res.status !== 'ok') return '';
    const labelOf = (ids: string) => ids.split(' + ').map((id) => (metas.get(id) ? ml(metas.get(id)) : id)).join(' + ');
    if (res.kind === 'sum') return t('ag.rule.sum', { units: unitWord });
    if (res.kind === 'wmean') return t('ag.rule.wmean', { w: labelOf(res.weight!) });
    return t('ag.rule.ratio', { num: labelOf(res.num!), den: labelOf(res.den!) });
  });
  const kindLabel = $derived(res?.status === 'ok' ? (res.kind === 'sum' ? t('ag.sum') : res.kind === 'ratio' ? t('ag.ratio') : t('ag.wmean', { w: ml(metas.get(res.weight!)) || res.weight! })) : '');
  const naText = $derived.by(() => {
    if (!res || res.status !== 'na') return '';
    const key = res.reason === 'noData' || res.reason === 'noParts' ? `ag.${res.reason}` : `ag.na.${res.reason}`;
    return t(key, { units: unitWord });
  });
</script>

<div class="agg" aria-live="polite">
  <div class="top">
    <span class="caps">{t('ag.metric')}</span>
    <div class="pick"><MetricPicker {metrics} {level} value={metricId} onpick={onpick} /></div>
  </div>
  {#if !meta}
    <p class="na">{t('f.notInBuild')}</p>
  {:else if res?.status === 'loading'}
    <p class="na">{t('ag.loading')}</p>
  {:else if res?.status === 'na'}
    <p class="na">{naText}</p>
  {:else if res?.status === 'ok'}
    <p class="val"><span class="big num">{fmtNumber(res.value, meta.decimals)}</span> <span class="unit">{unitOf(meta)}</span> <span class="sub">· {kindLabel}</span></p>
    <p class="note num">
      {ruleText}. {t('ag.cover', { n: fmtNumber(res.n, 0), m: fmtNumber(res.of, 0), units: unitWord })}
      · {fmtPeriod(own ? own.col.period : meta.latest)}
      {#if res.periodNote} · ({res.periodNote}){/if}
    </p>
  {/if}
</div>

<style>
  .agg { border-top: 1px solid var(--ink); margin-top: 8px; padding: 8px 0 2px; }
  .top { display: flex; align-items: center; gap: 8px; }
  .pick { flex: 1; min-width: 0; }
  .val { margin: 6px 0 0; display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 8px; }
  .big { font-size: 1.35rem; font-weight: 700; line-height: 1.1; }
  .unit { font-size: 0.8rem; }
  .sub { font-size: 0.74rem; color: var(--muted); }
  .note { margin: 2px 0 0; font-size: 0.72rem; color: var(--muted); }
  .na { margin: 6px 0 0; font-size: 0.76rem; color: var(--text); }
</style>
