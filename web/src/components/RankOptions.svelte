<script lang="ts">
  // Options above the ranking table: add any metric as a column, and a minimum population
  // (smaller municipalities are hidden, or only flagged). All of it lives in the URL (lib/hash.ts).
  import { ml, t } from '../lib/i18n.svelte';
  import { fmtNumber } from '../lib/classify';
  import type { MetricMeta } from '../lib/data';
  import MetricPicker from './MetricPicker.svelte';

  interface Props {
    metrics: MetricMeta[];
    metas: Map<string, MetricMeta>;
    level: string;
    xcols: string[];
    rmin: number | null;
    rflag: boolean;
    /** population is published at this level */
    hasPop: boolean;
    /** units below the minimum (hidden or flagged) */
    nBelow: number;
    unitWord: string;
    onadd: (id: string) => void;
    onremove: (id: string) => void;
    onmin: (n: number | null) => void;
    onflag: (flag: boolean) => void;
  }
  let { metrics, metas, level, xcols, rmin, rflag, hasPop, nBelow, unitWord, onadd, onremove, onmin, onflag }: Props = $props();

  function setMin(raw: string) {
    const n = Number(raw.replace(/['’\s]/g, ''));
    onmin(raw.trim() !== '' && Number.isFinite(n) && n > 0 ? Math.round(n) : null);
  }
</script>

<div class="ropt">
  <div class="add"><MetricPicker {metrics} {level} tag="+" value={t('rx.add')} onpick={(id) => id && onadd(id)} /></div>
  {#if xcols.length}
    <div class="chips" role="group" aria-label={t('rt.tag.Added')}>
      {#each xcols as id (id)}
        {@const m = metas.get(id)}
        <button type="button" class="chip" aria-label={t('rx.remove', { metric: m ? ml(m) : id })} onclick={() => onremove(id)}>{m ? ml(m) : id} ×</button>
      {/each}
    </div>
  {/if}
  <div class="min">
    <label class="lab" for="rx-min">{t('rx.min')}</label>
    <input id="rx-min" class="num" type="text" inputmode="numeric" autocomplete="off" placeholder={t('rx.minPh')} disabled={!hasPop}
      value={rmin ?? ''} onchange={(ev) => setMin(ev.currentTarget.value)} onkeydown={(ev) => { if (ev.key === 'Enter') setMin(ev.currentTarget.value); }} />
    <div class="seg" role="radiogroup" aria-label={t('rx.min')}>
      <button type="button" role="radio" aria-checked={!rflag} disabled={!hasPop} onclick={() => onflag(false)}>{t('rx.hide')}</button>
      <button type="button" role="radio" aria-checked={rflag} disabled={!hasPop} onclick={() => onflag(true)}>{t('rx.flag')}</button>
    </div>
    {#if rmin}<button type="button" class="link" onclick={() => onmin(null)}>{t('rx.clear')}</button>{/if}
  </div>
  {#if !hasPop}
    <p class="note">{t('rx.noPop')}</p>
  {:else if rmin && nBelow}
    <p class="note num">{t(rflag ? 'rx.flagged' : 'rx.hidden', { n: fmtNumber(nBelow, 0), units: unitWord, min: fmtNumber(rmin, 0) })}</p>
  {/if}
</div>

<style>
  .ropt { margin: 0 0 10px; }
  .chips { display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0 0; }
  .chip { padding: 2px 7px; border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text); cursor: pointer; font-size: 0.74rem; font-weight: 500; }
  .min { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; margin-top: 8px; }
  .lab { font-size: 0.76rem; font-weight: 600; }
  input { width: 6.5em; padding: 4px 6px; border: 1px solid var(--ink); border-radius: 0; background: var(--panel); font-size: 16px; text-align: right; color: var(--text); }
  input:disabled { opacity: 0.5; }
  .seg button { padding: 2px 8px; font-size: 0.76rem; }
  .link { border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: 0.76rem; color: var(--text); }
  .note { margin: 4px 0 0; font-size: 0.74rem; color: var(--muted); }
  @media (min-width: 900px) { input { font-size: 0.82rem; } }
</style>
