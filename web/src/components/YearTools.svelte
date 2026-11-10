<script lang="ts">
  // Under the year slider: values or change between two years (absolute / percent), class limits fixed
  // across years, and the small-multiples button. State lives in the URL hash through the parent.
  import { t } from '../lib/i18n.svelte';
  import '../lib/i18n-mapx';
  import type { ChangeMode } from '../lib/yearcmp.svelte';

  interface Props {
    /** all periods of the metric at this level, oldest first */
    periods: string[];
    /** the period on show (the later year of a comparison) */
    to: string;
    from: string | null;
    mode: ChangeMode;
    fixed: boolean;
    /** a problem with the comparison (earlier year not usable, series missing, still loading) */
    problem: string | null;
    onfrom: (y: string | null) => void;
    onmode: (m: ChangeMode) => void;
    onfixed: (v: boolean) => void;
    onmulti: () => void;
  }
  let { periods, to, from, mode, fixed, problem, onfrom, onmode, onfixed, onmulti }: Props = $props();

  const earlier = $derived(periods.slice(0, Math.max(0, periods.indexOf(to))));
  const changing = $derived(from !== null);
  function startChange() {
    if (earlier.length) onfrom(earlier[0]);
  }
</script>

<div class="yt">
  <div class="line">
    <div class="seg" role="radiogroup" aria-label={t('yc.view')}>
      <button type="button" role="radio" aria-checked={!changing} onclick={() => onfrom(null)}>{t('yc.values')}</button>
      <button type="button" role="radio" aria-checked={changing} disabled={!earlier.length && !changing} title={earlier.length ? '' : t('yc.none')} onclick={() => (changing ? null : startChange())}>{t('yc.change')}</button>
    </div>
    <button type="button" class="multi" onclick={onmulti}>{t('yc.multi')}</button>
  </div>
  {#if changing}
    <div class="line">
      <label class="since"><span class="caps">{t('yc.from')}</span>
        <select value={from} onchange={(e) => onfrom(e.currentTarget.value)} aria-label={t('yc.from')}>
          {#if from && !earlier.includes(from)}<option value={from}>{from}</option>{/if}
          {#each earlier as p}<option value={p}>{p}</option>{/each}
        </select>
      </label>
      <span class="foot">→ <span class="num">{to}</span></span>
      <div class="seg" role="radiogroup" aria-label={t('yc.change')}>
        <button type="button" role="radio" aria-checked={mode === 'abs'} onclick={() => onmode('abs')}>{t('yc.abs')}</button>
        <button type="button" role="radio" aria-checked={mode === 'pct'} onclick={() => onmode('pct')}>{t('yc.pct')}</button>
      </div>
    </div>
    <p class="foot">{problem ?? t('yc.note', { from: from ?? '', to })}{#if !problem && mode === 'pct'}{' '}{t('yc.notePct')}{/if}</p>
  {/if}
  <label class="fx" class:off={changing} title={changing ? t('ux.fixedOffWhy') : t('yc.fixedT')}>
    <input type="checkbox" checked={fixed && !changing} disabled={changing} onchange={(e) => onfixed(e.currentTarget.checked)} />
    <span>{t('yc.fixed')}</span>
  </label>
  {#if changing}<p class="foot">{t('ux.fixedOffWhy')}</p>{/if}
</div>

<style>
  .yt { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
  .line { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px 8px; }
  .seg button { padding: 3px 9px; font-size: 0.76rem; }
  .multi { border: 1px solid var(--ink); background: var(--panel); padding: 3px 9px; cursor: pointer; font-size: 0.76rem; font-weight: 600; color: var(--text); }
  .multi:hover { background: var(--panel-2); }
  .since { display: flex; align-items: center; gap: 6px; }
  select { border: 1px solid var(--ink); background: var(--panel); padding: 2px 4px; font-size: 0.8rem; border-radius: 0; }
  .fx { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; cursor: pointer; }
  .fx input { accent-color: var(--ink); margin: 0; width: 15px; height: 15px; }
  .fx.off { opacity: 0.5; cursor: default; }
  p.foot { margin: 0; }
</style>
