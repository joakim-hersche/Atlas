<script lang="ts">
  import type { MetricMeta } from '../lib/data';
  import { fmtNumber, fmtTick, type Classes } from '../lib/classify';

  interface Props {
    meta: MetricMeta;
    classes: Classes;
    colours: string[];
    word: string; // 'Darker' | 'Brighter'
    nUnits: number;
  }
  let { meta, classes, colours, word, nUnits }: Props = $props();

  const dirText = $derived(
    meta.direction === 'higher_better' ? 'higher is better' : meta.direction === 'lower_better' ? 'lower is better' : null,
  );
  const ticks = $derived([classes.min, ...classes.breaks, classes.max]);
  const nGap = $derived(nUnits - classes.n);
</script>

<div class="legend">
  <div class="sw" role="img" aria-label="Colour scale, {classes.classColour.length} quantile classes">
    {#each classes.classColour as c}
      <span style="background:{colours[c]}"></span>
    {/each}
  </div>
  <div class="ticks">
    {#each ticks as t, k}
      <span style="left:{(k / (ticks.length - 1)) * 100}%">{fmtTick(t, meta)}</span>
    {/each}
  </div>
  <p class="txt">
    <strong>{word} = higher</strong>{dirText ? ` · ${dirText}` : ''}
    <span class="muted">· quantiles{meta.unit ? ` · ${meta.unit}` : ''}</span>
  </p>
  {#if nGap > 0}
    <p class="gap"><span class="hatch"></span>No data: {fmtNumber(nGap, 0)} of {fmtNumber(nUnits, 0)} municipalities</p>
  {/if}
</div>

<style>
  .legend { font-size: 0.85rem; }
  .sw { display: flex; height: 12px; border-radius: 3px; overflow: hidden; margin: 0 6px; }
  .sw span { flex: 1; }
  .ticks { position: relative; height: 18px; margin: 2px 6px 0; color: var(--muted); font-variant-numeric: tabular-nums; font-size: 0.75rem; }
  .ticks span { position: absolute; transform: translateX(-50%); white-space: nowrap; }
  .ticks span:first-child { transform: none; left: -6px !important; }
  .ticks span:last-child { transform: translateX(-100%); left: calc(100% + 6px) !important; }
  .txt { margin: 4px 0 0; }
  .muted { color: var(--muted); }
  .gap { margin: 4px 0 0; color: var(--muted); display: flex; align-items: center; gap: 6px; }
  .hatch {
    display: inline-block; width: 16px; height: 12px; border-radius: 2px; border: 1px solid var(--nodata-line);
    background: repeating-linear-gradient(-45deg, var(--nodata-line) 0 1.5px, var(--nodata-fill) 1.5px 5px);
  }
</style>
