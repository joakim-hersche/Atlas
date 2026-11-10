<script lang="ts">
  // "Spatial patterns" section of the map controls: global Moran's I of the shaded metric, and the map modes
  // Values / Clusters (LISA) / Two metrics (bivariate). The statistics come from the SpatialController
  // (Web Worker); this component only shows them and sets app.spatial, app.fdr and app.metricB.
  import MetricPicker from './MetricPicker.svelte';
  import Term from './Term.svelte';
  import { fmtNumber, fmtTick } from '../lib/classify';
  import type { MetricMeta } from '../lib/data';
  import { ml, t } from '../lib/i18n.svelte';
  import '../lib/i18n-spatial';
  import type { SpatialController } from '../lib/spatial.svelte';
  import type { BivariateResult, LisaClasses } from '../lib/spatial';
  import { app } from '../lib/state.svelte';

  interface Props {
    sp: SpatialController;
    open: boolean;
    metrics: MetricMeta[];
    metaA: MetricMeta;
    metaB: MetricMeta | null;
    level: string;
    /** plural unit word ('municipalities') */
    unitWord: string;
    nUnits: number;
    /** the shaded metric has values at this level */
    usable: boolean;
    cls: LisaClasses | null;
    bi: BivariateResult | null;
    rho: number | null;
    /** second metric is still loading */
    biLoading: boolean;
    onmode: (m: 'off' | 'lisa' | 'bi') => void;
  }
  let { sp, open = $bindable(), metrics, metaA, metaB, level, unitWord, nUnits, usable, cls, bi, rho, biLoading, onmode }: Props = $props();

  const M = $derived(sp.moran);
  const fmtP = (p: number) => (p <= 1 / (sp.perms + 1) + 1e-9 ? `≤ ${fmtNumber(1 / (sp.perms + 1), 3)}` : `= ${fmtNumber(p, 3)}`);
  const verdict = $derived.by(() => {
    if (!M || !Number.isFinite(M.i) || !Number.isFinite(M.p)) return null;
    if (M.p < 0.05 && M.i > M.expected) return 'pos';
    if (M.p < 0.05 && M.i < M.expected) return 'neg';
    return 'none';
  });
  const MODES = ['off', 'lisa', 'bi'] as const;
  const falseAlarms = $derived(cls ? Math.round(0.05 * (nUnits - cls.counts.none)) : 0);
</script>

<div class="sp">
  <button type="button" class="head" aria-expanded={open} onclick={() => (open = !open)}>
    <span class="caps">{t('sp.title')}</span>
    <svg class="chev" class:up={open} viewBox="0 0 20 12" width="14" height="9" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
  </button>

  {#if open}
    {#if !usable}
      <p class="foot">{t('sp.noVals')}</p>
    {:else}
      <p class="foot intro">{t('sp.intro', { units: unitWord, metric: ml(metaA) })} <Term k="contiguity" /></p>

      <div class="moran" aria-live="polite">
        <div class="mh"><span class="mt">{t('sp.moran')}</span><Term k="morans_i" /></div>
        {#if sp.noNeighbours}
          <p class="foot">{t('sp.noNb')}</p>
        {:else if sp.error}
          <p class="foot">{t('sp.error', { e: sp.error })}</p>
        {:else if M && verdict}
          <p class="big num">{t('sp.moranVal', { i: fmtNumber(M.i, 3), e: fmtNumber(M.expected, 4), p: fmtP(M.p) })} <Term k="permutation_p" /></p>
          <p class="plain">{t(`sp.moran.${verdict}`, { units: unitWord })}</p>
          <p class="foot">{t('sp.moranFine', { n: fmtNumber(M.n, 0), units: unitWord, k: fmtNumber(M.perms, 0), m: fmtNumber(M.meanNeighbours, 1) })}</p>
          {#if M.nMissing + M.nIsland > 0}<p class="foot">{t('sp.left', { a: fmtNumber(M.nMissing, 0), b: fmtNumber(M.nIsland, 0) })}</p>{/if}
          {#if M.n < 30}<p class="foot">{t('sp.small', { n: fmtNumber(M.n, 0), units: unitWord })}</p>{/if}
          {#if sp.busy}<p class="foot">{t('sp.computing')}</p>{/if}
        {:else if sp.busy || !M}
          <p class="foot">{t('sp.computing')}</p>
        {:else}
          <p class="foot">{t('sp.noVals')}</p>
        {/if}
      </div>

      <div class="modes">
        <span class="caps">{t('sp.mode')}</span>
        <div class="seg" role="radiogroup" aria-label={t('sp.mode')}>
          {#each MODES as m}
            <button type="button" role="radio" aria-checked={app.spatial === m} onclick={() => onmode(m)}>{t(`sp.mode.${m}`)}</button>
          {/each}
        </div>
      </div>

      {#if app.spatial === 'lisa'}
        <p class="plain">{t('sp.lisa.what')} <Term k="lisa" /></p>
        <label class="fdr">
          <input type="checkbox" checked={app.fdr} onchange={(e) => (app.fdr = e.currentTarget.checked)} />
          <span>{t('sp.fdr')} <Term k="fdr" /></span>
        </label>
        {#if sp.busy && !cls}
          <p class="foot">{t('sp.computing')}</p>
        {:else if cls}
          <p class="foot">{t('sp.lisa.rule', { k: fmtNumber(sp.perms, 0) })}</p>
          <p class="foot warn">{app.fdr ? t('sp.lisa.fdr') : t('sp.lisa.raw', { n: fmtNumber(nUnits - cls.counts.none, 0), f: fmtNumber(falseAlarms, 0) })}</p>
        {/if}
      {:else if app.spatial === 'bi'}
        <p class="plain">{t('sp.bi.what')} <Term k="bivariate_map" /></p>
        <div class="b2">
          <span class="caps">{t('sp.bi.second')}</span>
          <MetricPicker {metrics} {level} value={metaB?.id ?? ''} none={t('sp.bi.pick')} onpick={(id) => (app.metricB = id || null)} />
        </div>
        {#if metaB && metaB.id === metaA.id}
          <p class="foot warn">{t('sp.bi.same')}</p>
        {:else if biLoading}
          <p class="foot">{t('sp.computing')}</p>
        {:else if bi && metaB}
          <p class="foot">{t('sp.bi.n', { n: fmtNumber(bi.n, 0), units: unitWord })}
            {#if rho !== null && Number.isFinite(rho)}{t('sp.bi.rho', { r: fmtNumber(rho, 2) })}{/if}</p>
          <p class="foot">{t('sp.bi.cuts', { m: ml(metaA), c1: fmtTick(bi.cutsA[0], metaA), c2: fmtTick(bi.cutsA[1], metaA) })}
            {t('sp.bi.cuts', { m: ml(metaB), c1: fmtTick(bi.cutsB[0], metaB), c2: fmtTick(bi.cutsB[1], metaB) })}</p>
        {/if}
      {/if}
    {/if}
  {/if}
</div>

<style>
  .head { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 0; border: 0; background: none; cursor: pointer; color: var(--text); }
  .chev { fill: none; stroke: var(--ink); stroke-width: 2.5; stroke-linecap: square; transition: transform 0.15s; }
  .chev.up { transform: rotate(180deg); }
  @media (prefers-reduced-motion: reduce) { .chev { transition: none; } }
  .foot { margin: 6px 0 0; }
  .intro { margin-top: 8px; }
  .moran { margin-top: 8px; border-left: 3px solid var(--ink); padding-left: 8px; }
  .mh { display: flex; align-items: center; gap: 2px; }
  .mt { font-weight: 700; font-size: var(--fs-small); }
  .big { margin: 2px 0 0; font-weight: 600; font-size: var(--fs-small); }
  .plain { margin: 6px 0 0; font-size: var(--fs-small); line-height: 1.4; }
  .modes { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
  .modes .seg button { padding: 3px 8px; font-size: var(--fs-meta); }
  .fdr { display: flex; align-items: flex-start; gap: 6px; margin-top: 8px; font-size: var(--fs-meta); cursor: pointer; }
  .fdr input { margin: 2px 0 0; accent-color: var(--ink); }
  .warn { color: var(--text); border-left: 3px solid var(--ink); padding-left: 6px; }
  .b2 { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
</style>
