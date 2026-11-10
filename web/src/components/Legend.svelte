<script lang="ts">
  // Legend as a distribution: histogram of the metric across municipalities, bars in their class
  // colour, class breaks marked, median tick, and a class row with range and count per class.
  import { ml, t as tr } from '../lib/i18n.svelte';
  import Term from './Term.svelte';
  import { sourceHref } from '../lib/nav';
  import { partialCantons, precisionText, type MetricMeta, type Source } from '../lib/data';
  import {
    axisDomain, unitOf, fmtNumber, fmtPeriod, fmtTick, logTicks, METHOD_LABEL, niceTicks, quantile, sortedValues, wantsLog,
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
    unitWord?: string;
  }
  let { meta, v, period, scale, nUnits, source, method, onmethod, compact = false, unitWord = 'municipalities' }: Props = $props();

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
  const classes = $derived.by(() => {
    const out = rawClasses();
    // the class right after a single-value class starts just above that value: "> 0–6", not "0–6"
    return out.map((c, k) => ({ ...c, after: k > 0 && out[k - 1].single !== null && fmtTick(c.lo, meta) === fmtTick(out[k - 1].single!, meta) }));
  });
  const rawClasses = () => (
    scale.method === 'continuous'
      ? []
      : scale.classColours.map((c, k) => ({
          c,
          lo: k === 0 ? scale.min : scale.breaks[k - 1],
          hi: k === scale.breaks.length ? scale.max : scale.breaks[k],
          /** a class holding one value only (a block of ties, e.g. 0) is labelled with that value */
          single: scale.counts[k] > 0 && scale.classMin[k] === scale.classMax[k] ? scale.classMin[k] : null,
          n: scale.counts[k],
        })));
  const nGap = $derived(nUnits - scale.n);
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);
  const unitText = $derived(unitOf(meta) || tr('fp.value'));
</script>

<div class="legend" class:compact>
  <div class="head">
    <span class="unit">{unitText}<span class="per">&nbsp;· {fmtPeriod(period)}{log ? ` · ${tr('lg.log')}` : ''}</span></span>
    <span class="mterm"><Term k={method === 'quantile' ? 'quantile' : method === 'equal' ? 'equal_intervals' : 'continuous'} /></span>
    <div class="seg" role="radiogroup" aria-label={tr('lg.class')}>
      {#each ['quantile', 'equal', 'continuous'] as const as m}
        <button type="button" role="radio" aria-checked={method === m} title={tr(`lg.m.${m}`)} onclick={() => onmethod(m)}>
          {tr(`lg.s.${m}`)}
        </button>
      {/each}
    </div>
  </div>

  <div class="plot" bind:clientWidth={w}>
    <svg width={w} height={H + 22} role="img" aria-label={`${ml(meta)} · n = ${fmtNumber(scale.n, 0)} ${unitWord}`}>
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
      {#if scale.diverging && dom.lo < scale.centre && dom.hi > scale.centre}<line x1={px(scale.centre)} x2={px(scale.centre)} y1="0" y2={H + 7} class="zero" />{/if}
      {#if Number.isFinite(median)}
        <path d="M{px(median) - 3.5},0 h7 l-3.5,4.5 z" class="md" />
        <text x={Math.min(PAD + W - 2, Math.max(PAD + 2, px(median) + 6))} y="7" class="mdl" text-anchor={px(median) > PAD + W - 70 ? 'end' : 'start'}
          dx={px(median) > PAD + W - 70 ? -12 : 0}>{tr('lg.median')} {fmtTick(median, meta)}</text>
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
          <span class="rng num">{c.single !== null ? fmtTick(c.single, meta) : `${c.after ? '> ' : ''}${fmtTick(c.lo, meta)}–${fmtTick(c.hi, meta)}`}</span>
          <span class="cn num">{fmtNumber(c.n, 0)}</span>
        </div>
      {/each}
    </div>
  {/if}

  <p class="meta">
    <span class="num">n = {fmtNumber(scale.n, 0)}</span>
    {#if nGap > 0}<span> · <span class="hatch"></span> <span class="num">{fmtNumber(nGap, 0)}</span> {tr('lg.noData')}</span>{/if}
    {#if scale.method === 'continuous'}<span> · {tr('lg.clamped')}</span>{/if}
    {#if dom.clipLo || dom.clipHi}<span> · {tr('lg.clipped')}<Term k="axis_clipped" /></span>{/if}
    {#if scale.diverging}<span> · {tr('lg.centredOn', { c: fmtTick(scale.centre, meta) + (meta.unit.startsWith('%') ? '%' : '') })}</span>{/if}
  </p>
  <p class="foot">
    {tr('lg.source')}: <a href={sourceHref(meta.source)}>{publisher}</a> · {fmtPeriod(period)} · {precisionText(meta.precision)}{cov ? '' : ` · ${tr('lg.national')}`}
    {#if cov}<span class="partial"> · {tr('p.partial', { n: cov.length })}</span>{/if}
  </p>
</div>

<style>
  .legend { font-size: 0.8rem; min-width: 0; }
  .head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 4px 8px; margin-bottom: 4px; }
  .unit { color: var(--text); font-weight: 600; min-width: 0; flex: 1 1 120px; }
  .seg { flex: none; }
  .mterm { margin-left: auto; }
  .per { color: var(--muted); font-weight: 400; }
  .seg button { padding: 2px 7px; font-size: 0.72rem; }
  .plot { width: 100%; }
  svg { display: block; overflow: visible; }
  .base { stroke: var(--ink); stroke-width: 1; }
  .brk { stroke: var(--text); stroke-width: 0.75; stroke-dasharray: 2 2; opacity: 0.7; }
  .zero { stroke: var(--text); stroke-width: 1; }
  .md { fill: var(--text); }
  .mdl { font: 700 10px var(--font-mono); fill: var(--text); paint-order: stroke; stroke: var(--panel); stroke-width: 3px; stroke-linejoin: round; }
  .tk { stroke: var(--plot-axis); }
  .tl { font: 10px var(--font-mono); fill: var(--text); }
  .classes { display: grid; gap: 0 3px; margin-top: 2px; }
  .cls { display: flex; flex-direction: column; min-width: 0; }
  .sw { height: 4px; margin-bottom: 2px; }
  .rng { font-size: 0.68rem; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .cn { font-size: 0.7rem; color: var(--text); }
  .meta { margin: 5px 0 0; color: var(--muted); font-size: 0.74rem; }
  .foot { margin: 2px 0 0; }
  .partial { color: var(--text); }
  .foot a { color: inherit; }
  .compact .head { margin-bottom: 2px; }
  .classes.vertical { gap: 0; margin-top: 6px; }
  .vertical .cls { flex-direction: row; align-items: center; gap: 8px; padding: 2px 0; border-bottom: 1px solid var(--border); }
  .vertical .sw { width: 14px; height: 10px; margin: 0; flex: none; }
  .vertical .rng { flex: 1; font-size: 0.72rem; color: var(--text); }
  .vertical .cn { color: var(--muted); }
</style>
