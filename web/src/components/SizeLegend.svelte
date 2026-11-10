<script lang="ts">
  // Legend for proportional symbols: three nested reference circles (area proportional to the value)
  // at the current zoom, plus counts of units without a circle.
  import { t } from '../lib/i18n.svelte';
  import type { MetricMeta } from '../lib/data';
  import { fmtNumber, fmtPeriod, fmtTick, unitOf } from '../lib/classify';

  interface Props {
    meta: MetricMeta;
    period: string;
    vmax: number;
    /** radius of vmax in px at the current zoom */
    rmax: number;
    filled: boolean;
    nDrawn: number;
    nMissing: number;
    nNonPositive: number;
    unitWord: string;
  }
  let { meta, period, vmax, rmax, filled, nDrawn, nMissing, nNonPositive, unitWord }: Props = $props();

  /** round down to one significant digit (440'935 -> 400'000) */
  function floor1(x: number): number {
    if (!(x > 0)) return 0;
    const p = 10 ** Math.floor(Math.log10(x));
    return Math.floor(x / p) * p;
  }
  const refs = $derived.by(() => {
    const a = floor1(vmax);
    const out = [a, floor1(vmax / 6), floor1(vmax / 40)].filter((v, k, all) => v > 0 && all.indexOf(v) === k);
    return out.map((v) => ({ v, r: rmax * Math.sqrt(v / vmax) }));
  });
  const R = $derived(Math.max(6, refs[0]?.r ?? 6));
  const H = $derived(Math.max(2 * R + 8, 3 * 11 + 6));
  // label baselines at the circle tops, pushed apart to at least 11 px
  const ly = $derived.by(() => {
    const out: number[] = [];
    for (const c of refs) {
      const y = H - 2 - 2 * c.r + 3.5;
      out.push(out.length ? Math.max(y, out[out.length - 1] + 11) : y);
    }
    return out;
  });
  const W = $derived(2 * R + 96);
</script>

<div class="size">
  <div class="head"><span class="unit">{unitOf(meta) || t('fp.value')}</span><span class="per">&nbsp;· {fmtPeriod(period)} · {t('sz.area')}</span></div>
  <svg width={W} height={H} role="img" aria-label="{t('sz.aria')}: {refs.map((r) => fmtTick(r.v, meta)).join(', ')} {unitOf(meta)}">
    {#each refs as c, k}
      {@const cy = H - 2 - c.r}
      <circle cx={R + 1} {cy} r={Math.max(0.8, c.r)} class:filled class="c" />
      <polyline points="{R + 1},{H - 2 - 2 * c.r} {2 * R + 8},{H - 2 - 2 * c.r} {2 * R + 14},{ly[k] - 3.5}" class="ld" />
      <text x={2 * R + 18} y={ly[k]} class="tl">{fmtTick(c.v, meta)}</text>
    {/each}
  </svg>
  <p class="meta">
    {t('sz.drawn', { n: fmtNumber(nDrawn, 0), units: unitWord })}
    {#if nMissing}· {t('sz.nodata', { n: fmtNumber(nMissing, 0) })}{/if}
    {#if nNonPositive}· {t('sz.nonpos', { n: fmtNumber(nNonPositive, 0) })}{/if}
  </p>
</div>

<style>
  .size { font-size: var(--fs-small); }
  .head { margin-bottom: 4px; }
  .unit { font-weight: 600; }
  .per { color: var(--muted); }
  svg { display: block; overflow: visible; }
  .c { fill: none; stroke: var(--ink); stroke-width: 1; }
  .c.filled { fill: var(--panel-2); stroke: var(--ink); }
  .ld { fill: none; stroke: var(--ink); stroke-width: 0.6; stroke-dasharray: 2 2; }
  .tl { font: var(--fs-cap) var(--font-mono); fill: var(--text); }
  .meta { margin: 4px 0 0; color: var(--muted); font-size: var(--fs-meta); }
</style>
