<script lang="ts">
  // Summary statistics of the shaded metric across municipalities, plus the selected unit.
  import { partialCantons, type MetricMeta, type Source } from '../lib/data';
  import { fmtNumber, fmtPeriod, mean, quantile, rankOf, sortedValues } from '../lib/classify';

  interface Props {
    meta: MetricMeta;
    v: (number | null)[];
    period: string;
    names: string[];
    cantons: string[];
    ch: { value: number; period: string } | null;
    sel: number | null;
    source: Source | undefined;
  }
  let { meta, v, period, names, cantons, ch, sel, source }: Props = $props();

  const s = $derived(sortedValues(v));
  const ext = $derived.by(() => {
    let lo = -1, hi = -1;
    for (let i = 0; i < v.length; i++) {
      const x = v[i];
      if (x === null) continue;
      if (lo < 0 || x < v[lo]!) lo = i;
      if (hi < 0 || x > v[hi]!) hi = i;
    }
    return { lo, hi };
  });
  const rank = $derived(sel === null ? null : rankOf(v, sel, meta.direction));
  const cov = $derived(partialCantons(meta));
  const f = (x: number) => fmtNumber(x, meta.decimals);
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);
</script>

<div class="stats">
  <div class="caps">Distribution across municipalities</div>
  <div class="unit">{meta.unit || 'value'} · {fmtPeriod(period)}</div>
  {#if s.length}
    <table>
      <tbody>
        <tr><th>n with data</th><td class="num">{fmtNumber(s.length, 0)} <span class="muted">of {fmtNumber(v.length, 0)}</span></td></tr>
        <tr><th>Mean <span class="muted">(unweighted)</span></th><td class="num">{f(mean(s))}</td></tr>
        <tr><th>Median</th><td class="num">{f(quantile(s, 0.5))}</td></tr>
        <tr><th>P10 / P90</th><td class="num">{f(quantile(s, 0.1))} / {f(quantile(s, 0.9))}</td></tr>
        <tr><th>Min</th><td class="num">{f(s[0])}<span class="who">{names[ext.lo]}{names[ext.lo]?.includes('(') ? '' : ` ${cantons[ext.lo]}`}</span></td></tr>
        <tr><th>Max</th><td class="num">{f(s[s.length - 1])}<span class="who">{names[ext.hi]}{names[ext.hi]?.includes('(') ? '' : ` ${cantons[ext.hi]}`}</span></td></tr>
        <tr><th>Switzerland</th><td class="num">{ch ? f(ch.value) : '–'}{#if ch && ch.period !== period}<span class="who">{fmtPeriod(ch.period)}</span>{/if}</td></tr>
      </tbody>
    </table>
    <p class="foot">
      {publisher} · {fmtPeriod(period)} · {meta.precision}{cov ? ` · partial: ${cov.length} of 26 cantons` : ''}{ch ? '' : ' · no national value published'}
    </p>
  {/if}

  {#if sel !== null}
    <div class="selblock">
      <div class="caps">Selected</div>
      <div class="sname"><strong>{names[sel]}</strong> <span class="muted">{cantons[sel]}</span></div>
      {#if v[sel] !== null && rank}
        <table>
          <tbody>
            <tr><th>Value</th><td class="num strong">{f(v[sel]!)}</td></tr>
            <tr><th>Rank</th><td class="num">{fmtNumber(rank.rank, 0)} <span class="muted">of {fmtNumber(rank.n, 0)}{meta.direction === 'lower_better' ? ', 1 = lowest' : ', 1 = highest'}</span></td></tr>
            <tr><th>Percentile</th><td class="num">P{fmtNumber(Math.round(rank.pct), 0)}</td></tr>
          </tbody>
        </table>
        <div class="pbar" aria-hidden="true"><span style="left:{rank.pct}%"></span></div>
      {:else}
        <p class="muted">No value for this municipality.</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .stats { font-size: 0.82rem; }
  .unit { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }
  table { width: 100%; border-collapse: collapse; margin-top: 4px; }
  th { text-align: left; font-weight: 400; color: var(--muted); padding: 4px 8px 4px 0; vertical-align: top; white-space: nowrap; }
  td { text-align: right; padding: 4px 0; }
  tr + tr { border-top: 1px solid var(--border); }
  .who { display: block; font-family: var(--font-sans); font-size: 0.72rem; color: var(--faint); }
  .muted { color: var(--muted); }
  .strong { font-weight: 500; font-size: 0.95rem; }
  .foot { margin: 6px 0 0; }
  .selblock { margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--border-strong); }
  .sname { margin: 3px 0 0; font-size: 0.95rem; }
  .pbar { position: relative; height: 6px; margin: 8px 0 2px; background: linear-gradient(to right, var(--border), var(--border-strong)); }
  .pbar span { position: absolute; top: -3px; width: 2px; height: 12px; background: var(--text); transform: translateX(-1px); }
</style>
