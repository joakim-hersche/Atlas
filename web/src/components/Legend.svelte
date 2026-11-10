<script lang="ts">
  // Legend as a distribution: histogram of the metric across municipalities, bars in their class
  // colour, class breaks marked, median tick, and a class row with range and count per class.
  import { partialCantons, type MetricMeta, type Source } from '../lib/data';
  import {
    axisDomain, fmtNumber, fmtPeriod, fmtTick, logTicks, METHOD_LABEL, niceTicks, quantile, sortedValues, wantsLog,
    type Method, type Scale,
  } from '../lib/classify';

  interface Props {
    meta: MetricMeta;
    v: (number | null)[];
    period: string;
    scale: Scale;
    nUnits: number;
    source: Source | undefined;
    method: Method;
    onmethod: (m: Method) => void;
    compact?: boolean;
  }
  let { meta, v, period, scale, nUnits, source, method, onmethod, compact = false }: Props = $props();

  let w = $state(300);
  const vertical = $derived(!compact && w < 300);
  const H = $derived(compact ? 34 : vertical ? 58 : 46);
  const PAD = 6;

  const s = $derived(sortedValues(v));
  const log = $derived(wantsLog(s));
  const dom = $derived(s.length ? axisDomain(s, log) : { lo: 0, hi: 1, clipLo: false, clipHi: false });
  const f = $derived(log ? Math.log10 : (x: number) => x);
  const g = $derived(log ? (x: number) => 10 ** x : (x: number) => x);
  const flo = $derived(f(dom.lo));
  const fhi = $derived(f(dom.hi) > f(dom.lo) ? f(dom.hi) : f(dom.lo) + 1);
  const W = $derived(Math.max(60, w - 2 * PAD));
  const px = (x: number) => PAD + ((Math.max(flo, Math.min(fhi, f(x))) - flo) / (fhi - flo)) * W;

  const bins = $derived.by(() => {
    const B = Math.max(12, Math.min(48, Math.round(W / 7)));
    const c = new Array(B).fill(0);
    for (const x of s) {
      const k = Math.floor(((Math.max(flo, Math.min(fhi, f(x))) - flo) / (fhi - flo)) * B);
      c[Math.min(B - 1, Math.max(0, k))]++;
    }
    const top = Math.max(1, ...c);
    return c.map((n, k) => {
      const x0 = PAD + (k / B) * W;
      const mid = g(flo + ((k + 0.5) / B) * (fhi - flo));
      return { x: x0 + 0.5, w: Math.max(1, W / B - 1), h: n ? Math.max(1.5, (n / top) * (H - 10)) : 0, fill: scale.colourOf(mid) };
    });
  });
  const median = $derived(quantile(s, 0.5));
  const ticks = $derived.by(() => {
    const t = log ? logTicks(dom.lo, dom.hi, Math.max(3, Math.round(W / 60))) : niceTicks(dom.lo, dom.hi, Math.max(3, Math.round(W / 70)));
    return t.filter((x) => x >= dom.lo && x <= dom.hi);
  });
  const strip = $derived.by(() => {
    if (scale.method === 'continuous') {
      const n = 40;
      return Array.from({ length: n }, (_, k) => ({ x: PAD + (k / n) * W, w: W / n + 0.5, fill: scale.colourOf(g(flo + ((k + 0.5) / n) * (fhi - flo))) }));
    }
    const edges = [dom.lo, ...scale.breaks.filter((b) => b > dom.lo && b < dom.hi), dom.hi];
    return edges.slice(0, -1).map((e, k) => ({ x: px(e), w: Math.max(0.5, px(edges[k + 1]) - px(e)), fill: scale.colourOf((e + edges[k + 1]) / 2) }));
  });
  const classes = $derived(
    scale.method === 'continuous'
      ? []
      : scale.classColours.map((c, k) => ({
          c,
          lo: k === 0 ? scale.min : scale.breaks[k - 1],
          hi: k === scale.breaks.length ? scale.max : scale.breaks[k],
          n: scale.counts[k],
        })),
  );
  const nGap = $derived(nUnits - scale.n);
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);
  const unitText = $derived(meta.unit || 'value');
</script>

<div class="legend" class:compact>
  <div class="head">
    <span class="unit">{unitText}<span class="per">&nbsp;· {fmtPeriod(period)}{log ? ' · log scale' : ''}</span></span>
    <div class="seg" role="radiogroup" aria-label="Classification">
      {#each ['quantile', 'equal', 'continuous'] as const as m}
        <button type="button" role="radio" aria-checked={method === m} title={METHOD_LABEL[m]} onclick={() => onmethod(m)}>
          {m === 'quantile' ? 'Quantile' : m === 'equal' ? 'Equal' : 'Cont.'}
        </button>
      {/each}
    </div>
  </div>

  <div class="plot" bind:clientWidth={w}>
    <svg width={w} height={H + 22} role="img" aria-label="Distribution of {meta.label_en} across {fmtNumber(scale.n, 0)} municipalities">
      {#each bins as b}
        {#if b.h}<rect x={b.x} y={H - b.h} width={b.w} height={b.h} fill={b.fill} />{/if}
      {/each}
      <line x1={PAD} x2={PAD + W} y1={H + 0.5} y2={H + 0.5} class="base" />
      {#each strip as r}<rect x={r.x} y={H + 2} width={r.w} height="5" fill={r.fill} />{/each}
      {#if scale.method !== 'continuous'}
        {#each scale.breaks as b}
          {#if b > dom.lo && b < dom.hi}<line x1={px(b)} x2={px(b)} y1="4" y2={H + 7} class="brk" />{/if}
        {/each}
      {/if}
      {#if scale.diverging && dom.lo < 0 && dom.hi > 0}<line x1={px(0)} x2={px(0)} y1="0" y2={H + 7} class="zero" />{/if}
      {#if Number.isFinite(median)}
        <path d="M{px(median) - 3.5},0 h7 l-3.5,4.5 z" class="md" />
        <text x={Math.min(PAD + W - 2, Math.max(PAD + 2, px(median) + 6))} y="7" class="mdl" text-anchor={px(median) > PAD + W - 70 ? 'end' : 'start'}
          dx={px(median) > PAD + W - 70 ? -12 : 0}>median {fmtTick(median, meta)}</text>
      {/if}
      {#each ticks as t}
        <line x1={px(t)} x2={px(t)} y1={H + 7} y2={H + 10} class="tk" />
        <text x={px(t)} y={H + 20} class="tl" text-anchor="middle">{fmtTick(t, meta)}</text>
      {/each}
    </svg>
  </div>

  {#if classes.length && !compact}
    <div class="classes" class:vertical style="grid-template-columns: repeat({vertical ? 1 : classes.length}, 1fr)">
      {#each classes as c}
        <div class="cls">
          <span class="sw" style="background:{c.c}"></span>
          <span class="rng num">{fmtTick(c.lo, meta)}–{fmtTick(c.hi, meta)}</span>
          <span class="cn num">{fmtNumber(c.n, 0)}</span>
        </div>
      {/each}
    </div>
  {/if}

  <p class="meta">
    <span class="num">n = {fmtNumber(scale.n, 0)}</span>
    {#if nGap > 0}<span> · <span class="hatch"></span> <span class="num">{fmtNumber(nGap, 0)}</span> no data</span>{/if}
    {#if scale.method === 'continuous'}<span> · scale clamped at P2/P98</span>{/if}
    {#if dom.clipLo || dom.clipHi}<span> · axis clipped at P1/P99</span>{/if}
    {#if scale.diverging}<span> · centred on 0</span>{/if}
  </p>
  <p class="foot">
    Source: {publisher} · {fmtPeriod(period)} · {meta.precision}{cov ? '' : ' · national'}
    {#if cov}<span class="partial"> · partial: {cov.length} of 26 cantons</span>{/if}
  </p>
</div>

<style>
  .legend { font-size: 0.8rem; min-width: 0; }
  .head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 4px 8px; margin-bottom: 4px; }
  .unit { color: var(--text); font-weight: 500; min-width: 0; flex: 1 1 120px; }
  .seg { flex: none; margin-left: auto; }
  .per { color: var(--muted); font-weight: 400; }
  .seg button { padding: 2px 7px; font-size: 0.72rem; }
  .plot { width: 100%; }
  svg { display: block; overflow: visible; }
  .base { stroke: var(--border-strong); stroke-width: 1; }
  .brk { stroke: var(--text); stroke-width: 0.75; stroke-dasharray: 2 2; opacity: 0.55; }
  .zero { stroke: var(--text); stroke-width: 1; }
  .md { fill: var(--text); }
  .mdl { font: 500 10px var(--font-mono); fill: var(--text); paint-order: stroke; stroke: var(--panel); stroke-width: 3px; stroke-linejoin: round; }
  .tk { stroke: var(--plot-axis); }
  .tl { font: 10px var(--font-mono); fill: var(--muted); }
  .classes { display: grid; gap: 0 3px; margin-top: 2px; }
  .cls { display: flex; flex-direction: column; min-width: 0; }
  .sw { height: 4px; margin-bottom: 2px; }
  .rng { font-size: 0.66rem; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .cn { font-size: 0.7rem; color: var(--text); }
  .meta { margin: 5px 0 0; color: var(--muted); font-size: 0.74rem; }
  .foot { margin: 2px 0 0; }
  .partial { color: var(--text); }
  .compact .head { margin-bottom: 2px; }
  .classes.vertical { gap: 0; margin-top: 6px; }
  .vertical .cls { flex-direction: row; align-items: center; gap: 8px; padding: 2px 0; border-bottom: 1px solid var(--border); }
  .vertical .sw { width: 14px; height: 10px; margin: 0; flex: none; }
  .vertical .rng { flex: 1; font-size: 0.72rem; color: var(--text); }
  .vertical .cn { color: var(--muted); }
</style>
