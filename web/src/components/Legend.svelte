<script lang="ts">
  import { colon } from '../lib/typo';
  // Legend as a distribution: histogram of the metric across municipalities, bars in their class
  // colour, class breaks marked, median tick, and a class row with range and count per class.
  import { ml, mdesc, t as tr } from '../lib/i18n.svelte';
  import '../lib/i18n-mapx';
  import '../lib/i18n-r3';
  import Term from './Term.svelte';
  import { sourceHref } from '../lib/nav';
  import { coverageLabel, majorityCount, partialCantons, precisionText, type Column, type MetricMeta, type Source } from '../lib/data';
  import { app } from '../lib/state.svelte';
  import {
    axisDomain, unitOf, fmtNumber, fmtPeriod, fmtTick, logTicks, METHOD_LABEL, niceTicks, quantile, sortedValues, wantsLog,
    type Method, type Scale, fixedLabels, rangeText } from '../lib/classify';

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
    /** the column shown (D37: single-seat-canton values kept apart, majority toggle) */
    col?: Column | null;
    /** values that define the axis (all years pooled, when the class limits are fixed); default: v */
    axisRef?: number[] | null;
    /** reliability notice of a survey or modelled metric (badge and sentence) */
    rel?: { kind: 'ci' | 'survey' | 'modelled'; text: string; extra?: string | null } | null;
    /** further notes under the count line (fixed class limits, change maps) */
    notes?: string[];
    /** U10: active filters (1 = matching): the histogram and the class counts show the matching units */
    mask?: Uint8Array | null;
    /** U11: a title line above the legend (change maps: what changed, between which years, in which unit) */
    title?: string | null;
    /** U13: a warning shown at the top (sparse coverage), with an optional action */
    warn?: { text: string; action?: string; onaction?: () => void; action2?: string; onaction2?: () => void } | null;
    /** B2: values hidden as small numbers (counted apart from units without data, with a way to show them) */
    nHidden?: number;
    /** B3: meaning of the two ends of a diverging scale (default: the vote and leaning maps' own) */
    sides?: { left: string; right: string } | null;
    /** level shown (J8: single-seat cantons below canton level are counted in units of that level) */
    level?: string;
    /** a small legend over the map (phone with the sheet folded, embeds): unit, the coloured axis, nothing else */
    mini?: boolean;
  }
  let { meta, v, period, scale, nUnits, source, method, onmethod, compact = false, unitWord = 'municipalities', col = null, axisRef = null, rel = null, notes = [], mask = null, title = null, warn = null, mini = false, nHidden = 0, sides = null, level = '' }: Props = $props();

  let w = $state(300);
  const vertical = $derived(!compact && w < 300);
  const H = $derived(mini ? 22 : compact ? 34 : vertical ? 58 : 46);
  const PAD = 6;

  const s = $derived(sortedValues(mask ? v.map((x, i) => (mask[i] ? x : null)) : v));
  /** units per class among the matching units (all units without a filter) */
  const counts = $derived.by(() => {
    if (!mask) return scale.counts;
    const c = new Array(scale.counts.length).fill(0);
    for (const x of s) {
      let k = 0;
      while (k < scale.breaks.length && x >= scale.breaks[k]) k++;
      c[Math.min(k, c.length - 1)]++;
    }
    return c;
  });
  // the axis stays that of all units (or all years), so filtering does not rescale it
  const sAxis = $derived(axisRef && axisRef.length ? axisRef : mask ? sortedValues(v) : s);
  const log = $derived(wantsLog(sAxis));
  const dom = $derived(sAxis.length ? axisDomain(sAxis, log) : { lo: 0, hi: 1, clipLo: false, clipHi: false });
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
          n: counts[k],
        })));
  const fixedL = $derived(scale.fixed ? fixedLabels(scale, meta) : null);
  /** D37: units of single-seat cantons kept apart (own pattern), or merged in by the toggle */
  const nMaj = $derived(col ? majorityCount(col) : 0);
  const nMajIn = $derived(col?.mIncluded ?? 0);
  const nGap = $derived(Math.max(0, nUnits - scale.n - nMaj - nHidden));
  /** D37 rule 1: the default period is not the newest one (newest incomplete): say so */
  const older = $derived(period === meta.latest && meta.latest_available && meta.latest_available !== meta.latest ? meta.latest_available : null);
  const olderWhy = $derived.by(() => {
    const ip = older ? meta.incomplete_periods?.[older] : undefined;
    if (!ip) return '';
    const l = app.lang === 'de' ? ip.label_de : app.lang === 'fr' ? ip.label_fr : null;
    return l ?? ip.label_en ?? '';
  });
  const nrw = $derived(meta.id.startsWith('nrw_'));
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);
  // U9: 'pp' spelled out in the legend (the first place a reader meets it)
  const unitText = $derived(meta.unit === 'pp' ? tr('ux.ppFirst') : unitOf(meta) || tr('fp.value'));
  const blocs = $derived(meta.id === 'nrw_leaning' || meta.id.startsWith('nrw_share_bloc_'));
</script>

<div class="legend" class:compact class:mini>
  {#if warn}
    <p class="warnbar">{warn.text}{#if warn.action && warn.onaction}{' '}<button type="button" class="link" onclick={warn.onaction}>{warn.action}</button>{/if}{#if warn.action2 && warn.onaction2}{' · '}<button type="button" class="link" onclick={warn.onaction2}>{warn.action2}</button>{/if}</p>
  {/if}
  {#if title}<p class="ltitle">{title}</p>{/if}
  <div class="head">
    <span class="unit">{unitText}<span class="per">{' · '}{fmtPeriod(period)}{log ? ` · ${tr('lg.log')}` : ''}</span></span>
    {#if !mini && !scale.fixed}
      <span class="mterm"><Term k={method === 'quantile' ? 'quantile' : method === 'equal' ? 'equal_intervals' : 'continuous'} /></span>
      <div class="seg" role="radiogroup" aria-label={tr('lg.class')}>
        {#each ['quantile', 'equal', 'continuous'] as const as m}
          <button type="button" role="radio" aria-checked={method === m} title={tr(`lg.m.${m}`)} onclick={() => onmethod(m)}>
            {tr(`lg.s.${m}`)}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <div class="plot" bind:clientWidth={w}>
    <svg width={w} height={H + 24} role="img" aria-label={`${ml(meta)} · n = ${fmtNumber(scale.n, 0)} ${unitWord}`}>
      {#each bins as b}
        {#if b.h}<rect x={b.x} y={H - b.h} width={b.w} height={b.h} fill={b.fill} />{/if}
      {/each}
      <line x1={PAD} x2={PAD + W} y1={H + 0.5} y2={H + 0.5} class="base" />
      {#each strip as r}<rect x={r.x} y={H + 2} width={r.w} height="6" fill={r.fill} />{/each}
      {#if scale.diverging && dom.lo < scale.centre && dom.hi > scale.centre}<line x1={px(scale.centre)} x2={px(scale.centre)} y1="0" y2={H + 7} class="zero" />{/if}
      {#if Number.isFinite(median) && !mini}
        <line x1={px(median) + 0.5} x2={px(median) + 0.5} y1="2" y2={H} class="md" />
        <text x={px(median) + (px(median) > PAD + W - 80 ? -4 : 4)} y="9" class="mdl" text-anchor={px(median) > PAD + W - 80 ? 'end' : 'start'}>{tr('lg.median')} {fmtTick(median, meta)}</text>
      {/if}
      {#each ticks as t}
        <line x1={px(t)} x2={px(t)} y1={H + 8} y2={H + 11} class="tk" />
        <text x={px(t)} y={H + 22} class="tl" text-anchor="middle">{fmtTick(t, meta)}</text>
      {/each}
    </svg>
  </div>

  {#if sides}
    <div class="sides"><span>← {sides.left}</span><span>{sides.right} →</span></div>
  {:else if scale.fixed && meta.id === 'vote_yes_share'}
    <div class="sides"><span>← {tr('lg.no')}</span><span>{tr('lg.yes')} →</span></div>
  {:else if scale.fixed && meta.id === 'nrw_leaning'}
    <div class="sides"><span>← {tr('lg.leftLean')}</span><span>{tr('lg.rightLean')} →</span></div>
  {/if}
  {#if !mini}
  {#if classes.length && !compact}
    <div class="classes" class:vertical style="grid-template-columns: repeat({vertical ? 1 : classes.length}, 1fr)">
      {#each classes as c, k}
        <div class="cls">
          <span class="sw" style="background:{c.c}"></span>
          <span class="rng num">{fixedL ? fixedL[k].label : c.single !== null ? fmtTick(c.single, meta) : `${c.after ? '> ' : ''}${rangeText(fmtTick(c.lo, meta), fmtTick(c.hi, meta))}`}</span>
          <span class="cn num">{fmtNumber(c.n, 0)}</span>
        </div>
      {/each}
    </div>
  {/if}

  <p class="meta">
    {#if mask}<span class="num">{tr('ux.nMatching', { n: fmtNumber(s.length, 0) })}</span>{' · '}{/if}<span class="num">{tr('r3.nUnits', { n: fmtNumber(scale.n, 0), units: unitWord })}</span>
    {#if nGap > 0}<span> · <span class="hatch"></span> <span class="num">{fmtNumber(nGap, 0)}</span> {tr('lg.noData')}</span>{/if}
    {#if nHidden > 0}<span> · <span class="hatch"></span> {tr('r3.hiddenN', { n: fmtNumber(nHidden, 0) })}
      <button type="button" class="link" onclick={() => (app.unstable = 'show')}>{tr('r3.showThem')}</button></span>{/if}
    {#if nMaj > 0}<span class="majl"> · <span class="majp"></span> {#if level && level !== 'kanton'}{tr('r3.majUnits', { n: fmtNumber(nMaj, 0), units: unitWord })}{:else}<span class="num">{fmtNumber(nMaj, 0)}</span> {tr('lg.maj')}{/if}<Term k="majority_election" />
      <button type="button" class="link" onclick={() => (app.maj = true)}>{tr('lg.majInclude')}</button></span>
    {:else if nMajIn > 0}<span class="majl"> · {tr('lg.majIncluded', { n: fmtNumber(nMajIn, 0) })}
      <button type="button" class="link" onclick={() => (app.maj = false)}>{tr('lg.majExclude')}</button></span>{/if}
    {#if scale.method === 'continuous'}<span> · {tr('lg.clamped')}</span>{/if}
    {#if dom.clipLo || dom.clipHi}<span> · {tr('lg.clipped')}<Term k="axis_clipped" /></span>{/if}
    {#if scale.diverging}<span> · {tr('lg.centredOn', { c: fmtTick(scale.centre, meta) + (meta.unit.startsWith('%') ? '%' : '') })}</span>{/if}
  </p>
  {#if older}<p class="older">{tr('lg.older', { p: fmtPeriod(period), n: fmtPeriod(older) })}{olderWhy ? ` (${olderWhy})` : ''}</p>{/if}
  {#if meta.id === 'nrw_leaning'}<p class="dnote">{tr('lg.leanNote')}</p>{/if}
  {#if blocs && !compact}<p class="dnote">{tr('ux.blocs')}</p>{/if}
  {#if !compact && mdesc(meta)}
    <details class="def"><summary>ⓘ {tr('lg.definition')}</summary><p>{mdesc(meta)}</p></details>
  {/if}
  {#if nrw && !compact}<p class="dnote">{tr('lg.ncOnly')}</p>{/if}
  {#each notes as n}<p class="meta nt">{n}</p>{/each}
  {#if rel}
    <p class="rel"><span class="rb rb-{rel.kind}">{tr(`rl.b.${rel.kind}`)}</span> {rel.text}{#if rel.extra}{' '}<span class="rx">{rel.extra}</span>{/if}</p>
  {/if}
  <p class="foot">
    {tr('lg.source')}{colon()}<a href={sourceHref(meta.source)}>{publisher}</a> · {fmtPeriod(period)} · {precisionText(meta.precision)}{cov ? '' : ` · ${tr('lg.national')}`}
    {#if cov}<span class="partial"> · {coverageLabel(meta)}</span>{/if}
  </p>
  {/if}
</div>

<style>
  .legend { font-size: var(--fs-small); line-height: var(--lh-small); min-width: 0; }
  .ltitle { margin: 0 0 var(--sp-1); font-size: var(--fs-body); line-height: var(--lh-body); font-weight: 600; }
  .warnbar { margin: 0 0 var(--sp-2); padding-left: var(--sp-2); border-left: 3px solid var(--ink); font-size: var(--fs-small); line-height: var(--lh-small); }
  .warnbar .link { border: 0; background: none; padding: 0; text-decoration: underline; text-underline-offset: 2px; cursor: pointer; font: inherit; font-weight: 600; color: var(--text); }
  .head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: var(--sp-1) var(--sp-2); margin-bottom: var(--sp-1); }
  .unit { color: var(--text); font-weight: 600; min-width: 0; flex: 1 1 120px; }
  .seg { flex: none; }
  .mterm { margin-left: auto; }
  .per { color: var(--text-2); font-weight: 400; }
  .seg button { min-height: var(--ctl-h-sm); padding: 0 var(--sp-2); font-size: var(--fs-meta); }
  .plot { width: 100%; }
  svg { display: block; overflow: visible; }
  .base { stroke: var(--ink); stroke-width: 1; }
  .zero { stroke: var(--ink); stroke-width: 1; }
  .md { stroke: var(--ink); stroke-width: 1; }
  .mdl { font: 600 var(--fs-cap) var(--font-sans); fill: var(--text); paint-order: stroke; stroke: var(--panel); stroke-width: 3px; stroke-linejoin: round; }
  .tk { stroke: var(--plot-axis); }
  .tl { font: var(--fs-cap) var(--font-sans); font-variant-numeric: tabular-nums; fill: var(--text); }
  .classes { display: grid; gap: 0 var(--sp-1); margin-top: var(--sp-1); }
  .sides { display: flex; justify-content: space-between; margin-top: var(--sp-1); font-size: var(--fs-meta); font-weight: 600; }
  .sides span:first-child { color: var(--div-n3); }
  .sides span:last-child { color: var(--div-p3); }
  .cls { display: flex; flex-direction: column; min-width: 0; }
  .sw { height: 6px; margin-bottom: 2px; }
  .rng { font-size: var(--fs-cap); color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }
  .cn { font-size: var(--fs-cap); color: var(--text); font-variant-numeric: tabular-nums; }
  .meta { margin: var(--sp-1) 0 0; color: var(--text-2); font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .foot { margin: 2px 0 0; }
  .majp { display: inline-block; width: 12px; height: 9px; vertical-align: -1px; border: 1px solid var(--nodata-line);
    background: radial-gradient(circle, #9a9a9a 1px, transparent 1.3px) 0 0 / 5px 5px, var(--surface-2); }
  .meta .link { margin-left: var(--sp-1); border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: inherit; color: var(--text); }
  .majl .link { margin-left: var(--sp-1); border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: inherit; color: var(--text); }
  .older { margin: var(--sp-1) 0 0; font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text); border-left: 3px solid var(--ink); padding-left: var(--sp-2); }
  .dnote { margin: var(--sp-1) 0 0; font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text-2); }
  .def { margin: var(--sp-1) 0 0; font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .def summary { cursor: pointer; color: var(--text); font-weight: 600; }
  .def p { margin: var(--sp-1) 0 0; color: var(--text); font-size: var(--fs-small); line-height: var(--lh-small); }
  .nt { margin-top: var(--sp-1); }
  .rel { margin: var(--sp-1) 0 0; font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .rb { display: inline-block; padding: 0 var(--sp-1); border: 1px solid var(--ink); font-size: var(--fs-cap); font-weight: 600; white-space: nowrap; vertical-align: 1px; }
  .rb-ci { background: var(--ink); color: var(--ink-text); }
  .rx { color: var(--text-2); }
  .partial { color: var(--text); }
  .foot a { color: inherit; }
  .compact .head { margin-bottom: 2px; }
  .mini .head { margin-bottom: 0; }
  .mini .unit { font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .classes.vertical { gap: 0; margin-top: var(--sp-2); }
  .vertical .cls { flex-direction: row; align-items: center; gap: var(--sp-2); min-height: 24px; border-bottom: var(--rule-row); }
  .vertical .sw { width: 14px; height: 10px; margin: 0; flex: none; }
  .vertical .rng { flex: 1; font-size: var(--fs-meta); color: var(--text); }
  .vertical .cn { color: var(--text-2); font-size: var(--fs-meta); }
</style>
