<script lang="ts">
  // Year slider for metrics with a time series. null = latest. Values of past years come from the
  // series files, on the current (2026) boundaries like everything else.
  // `marks`: periods that are not comparable with their neighbours (incomplete round, break in the series),
  // drawn as small triangles under the track; the note under the slider names the one in view.
  import { t } from '../lib/i18n.svelte';
  import '../lib/i18n-mapx';
  import type { PeriodMark } from '../lib/yearcmp.svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    periods: string[];
    value: string | null;
    onchange: (year: string | null) => void;
    marks?: Map<string, PeriodMark>;
    /** the default period (null value); newer periods may exist when they are incomplete */
    latest?: string;
    /** boundary note after the range (default: harmonised to the reference state) */
    harm?: string;
    children?: Snippet;
  }
  let { periods, value, onchange, marks, latest: latestProp, harm, children }: Props = $props();

  const last = $derived(periods[periods.length - 1]);
  const latest = $derived(latestProp && periods.includes(latestProp) ? latestProp : last);
  const idx = $derived(value && periods.includes(value) ? periods.indexOf(value) : periods.indexOf(latest));
  const ticks = $derived(
    marks && periods.length > 1
      ? periods.flatMap((p, k) => (marks.has(p) ? [{ p, k, m: marks.get(p)! }] : []))
      : [],
  );
  const here = $derived(marks?.get(periods[idx]) ?? null);
  function set(k: number) {
    const p = periods[k];
    onchange(p === latest ? null : p);
  }
</script>

<div class="year">
  <span class="caps">{t('yr.year')}</span>
  <div class="rail">
    <input type="range" min="0" max={periods.length - 1} step="1" value={idx} style="--pct:{periods.length > 1 ? (100 * idx) / (periods.length - 1) : 100}%" aria-label={t('yr.year')} aria-valuetext={periods[idx] + (here ? ` (${here.text})` : '')}
      oninput={(e) => set(+e.currentTarget.value)} />
    {#each ticks as k (k.p)}
      <button type="button" class="mk" class:brk={k.m.kind === 'break'} style="left: calc(7px + (100% - 14px) * {k.k / (periods.length - 1)})"
        title="{k.p}: {k.m.text}" aria-label="{k.p}: {k.m.text}" onclick={() => set(k.k)}></button>
    {/each}
  </div>
  <output class="num yv">{periods[idx]}</output>
  <button type="button" class="latest" disabled={value === null} onclick={() => onchange(null)}>{t('yr.latest')}</button>
</div>
<p class="range foot"><span class="num">{periods[0]}–{last}</span> · {harm ?? t('yr.harm')}{#if children}{@render children()}{/if}</p>
{#if ticks.length}
  <p class="foot mkn">
    <span class="mi" class:brk={here ? here.kind === 'break' : ticks.some((k) => k.m.kind === 'break')} aria-hidden="true"></span>{here ? t('yc.markNow', { text: here.text }) : t('yc.marks')}
  </p>
{/if}

<style>
  .year { display: flex; align-items: center; gap: 8px; }
  .rail { position: relative; flex: 1; min-width: 0; }
  input { display: block; width: 100%; min-width: 0; }
  .yv { font-weight: 700; min-width: 3.2em; text-align: right; }
  .latest { padding: 2px 7px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-size: var(--fs-meta); font-weight: 500; }
  .latest:disabled { opacity: 0.45; cursor: default; }
  .range { margin: 2px 0 0; }
  /* marker: a small triangle under the track, grey = incomplete round, ink = break in the series */
  .mk {
    position: absolute; bottom: -4px; width: 14px; height: 10px; margin-left: -7px; padding: 0; border: 0; background: none; cursor: pointer;
  }
  .mk::before {
    content: ''; position: absolute; left: 3px; top: 1px; border: 4px solid transparent; border-bottom: 7px solid var(--faint); border-top: 0;
  }
  .mk.brk::before { border-bottom-color: var(--ink); }
  .mkn { margin: 2px 0 0; display: flex; align-items: center; gap: 5px; }
  .mi { flex: none; width: 0; height: 0; border: 4px solid transparent; border-bottom: 7px solid var(--faint); border-top: 0; }
  .mi.brk { border-bottom-color: var(--ink); }
</style>
