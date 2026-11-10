<script lang="ts">
  // Year slider for metrics with a time series. null = latest. Values of past years come from the
  // series files, on the current (2026) boundaries like everything else.
  import type { Snippet } from 'svelte';

  interface Props {
    periods: string[];
    value: string | null;
    onchange: (year: string | null) => void;
    children?: Snippet;
  }
  let { periods, value, onchange, children }: Props = $props();

  const latest = $derived(periods[periods.length - 1]);
  const idx = $derived(value && periods.includes(value) ? periods.indexOf(value) : periods.length - 1);
  function set(k: number) {
    const p = periods[k];
    onchange(p === latest ? null : p);
  }
</script>

<div class="year">
  <span class="caps">Year</span>
  <input type="range" min="0" max={periods.length - 1} step="1" value={idx} aria-label="Year" aria-valuetext={periods[idx]}
    oninput={(e) => set(+e.currentTarget.value)} />
  <output class="num yv">{periods[idx]}</output>
  <button type="button" class="latest" disabled={value === null} onclick={() => onchange(null)}>Latest</button>
</div>
<p class="range foot"><span class="num">{periods[0]}–{latest}</span> · harmonized to the 2026 boundaries{#if children}{@render children()}{/if}</p>

<style>
  .year { display: flex; align-items: center; gap: 8px; }
  input { flex: 1; min-width: 0; accent-color: var(--ink); height: 24px; }
  .yv { font-weight: 700; min-width: 3.2em; text-align: right; }
  .latest { padding: 2px 7px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-size: 0.74rem; font-weight: 500; }
  .latest:disabled { opacity: 0.45; cursor: default; }
  .range { margin: 2px 0 0; }
</style>
