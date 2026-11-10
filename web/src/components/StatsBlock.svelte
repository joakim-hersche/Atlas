<script lang="ts">
  import { pubName } from '../lib/texts.svelte';
  // Summary statistics of the shaded metric across municipalities, plus the selected unit.
  import { t, tiedText } from '../lib/i18n.svelte';
  import Term from './Term.svelte';
  import { sourceHref } from '../lib/nav';
  import { coverageLabel, partialCantons, precisionText, type MetricMeta, type Source } from '../lib/data';
  import { fmtNumber, fmtPeriod, mean, quantile, rankOf, sortedValues, unitOf, higherThan } from '../lib/classify';

  interface Props {
    meta: MetricMeta;
    v: (number | null)[];
    period: string;
    names: string[];
    cantons: string[];
    ch: { value: number; period: string } | null;
    sel: number | null;
    source: Source | undefined;
    unitWord?: string;
    /** active filters: 1 = matching unit (statistics are computed over the matches only) */
    mask?: Uint8Array | null;
  }
  let { meta, v, period, names, cantons, ch, sel, source, unitWord = 'municipalities', mask = null }: Props = $props();

  const nIn = $derived(mask ? mask.reduce((a, b) => a + b, 0) : v.length);
  const s = $derived(sortedValues(mask ? v.map((x, i) => (mask[i] ? x : null)) : v));
  const ext = $derived.by(() => {
    let lo = -1, hi = -1;
    for (let i = 0; i < v.length; i++) {
      const x = v[i];
      if (x === null || (mask && !mask[i])) continue;
      if (lo < 0 || x < v[lo]!) lo = i;
      if (hi < 0 || x > v[hi]!) hi = i;
    }
    return { lo, hi };
  });
  const rank = $derived(sel === null ? null : rankOf(v, sel, meta.direction));
  const cov = $derived(partialCantons(meta));
  const f = (x: number) => fmtNumber(x, meta.decimals);
  const publisher = $derived(source ? pubName(source.publisher) : meta.source);
</script>

<div class="stats">
  <div class="caps">{t(mask ? 'st.distF' : 'st.dist', { units: unitWord })}</div>
  <div class="unit">{unitOf(meta) || t('fp.value')} · {fmtPeriod(period)}</div>
  {#if mask}<p class="filt">{t('st.filtered', { n: fmtNumber(nIn, 0), total: fmtNumber(v.length, 0), units: unitWord })}</p>{/if}
  {#if s.length}
    <table>
      <tbody>
        <tr><th>{t('st.n')}</th><td class="num">{fmtNumber(s.length, 0)} <span class="muted">{t('st.of', { n: fmtNumber(nIn, 0) })}</span></td></tr>
        <tr><th>{t('st.mean')} <span class="muted">({t('st.unweighted')})</span></th><td class="num">{f(mean(s))}</td></tr>
        <tr><th>{t('st.median')}<Term k="median" /></th><td class="num">{f(quantile(s, 0.5))}</td></tr>
        <tr><th title={t('ux.p10T')}>{t('ux.p10Plain', { units: unitWord })}<Term k="p10_p90" /></th><td class="num">{f(quantile(s, 0.1))}</td></tr>
        <tr><th title={t('ux.p90T')}>{t('ux.p90Plain', { units: unitWord })}</th><td class="num">{f(quantile(s, 0.9))}</td></tr>
        <tr><th>Min</th><td class="num">{f(s[0])}<span class="who">{names[ext.lo]}{names[ext.lo]?.includes('(') || !cantons[ext.lo] || cantons[ext.lo] === names[ext.lo] ? '' : ` ${cantons[ext.lo]}`}</span></td></tr>
        <tr><th>Max</th><td class="num">{f(s[s.length - 1])}<span class="who">{names[ext.hi]}{names[ext.hi]?.includes('(') || !cantons[ext.hi] || cantons[ext.hi] === names[ext.hi] ? '' : ` ${cantons[ext.hi]}`}</span></td></tr>
        <tr><th>{t('st.ch')}{#if mask}<span class="who">{t('st.chAll')}</span>{/if}</th><td class="num">{ch ? f(ch.value) : '–'}{#if ch && ch.period !== period}<span class="who">{fmtPeriod(ch.period)}</span>{/if}</td></tr>
      </tbody>
    </table>
    <p class="foot">
      <a href={sourceHref(meta.source)}>{publisher}</a> · {fmtPeriod(period)} · {precisionText(meta.precision)}{cov ? ` · ${coverageLabel(meta)}` : ''}{ch ? '' : ` · ${t('st.noCH')}`}
    </p>
  {:else if mask}
    <p class="muted">{t('st.noMatch')}</p>
  {/if}

  {#if sel !== null}
    <div class="selblock">
      <div class="caps">{t('st.selected')}</div>
      <div class="sname"><strong>{names[sel]}</strong> <span class="muted">{cantons[sel]}</span></div>
      {#if v[sel] !== null && rank}
        <table>
          <tbody>
            <tr><th>{t('st.value')}</th><td class="num strong">{f(v[sel]!)}</td></tr>
            <tr><th>{t('st.rank')}</th><td class="num">{fmtNumber(rank.rank, 0)} <span class="muted">{t('st.of', { n: fmtNumber(rank.n, 0) })}{tiedText(rank, true)}, {meta.direction === 'lower_better' ? t('card.oneLowest') : t('card.oneHighest')}</span></td></tr>
            <tr><th>{t('st.pct')}<Term k="percentile" /></th><td class="num" title="P{fmtNumber(Math.round(higherThan(rank)), 0)}">{t('ux.pctPlain', { p: fmtNumber(Math.round(higherThan(rank)), 0), units: unitWord })}</td></tr>
          </tbody>
        </table>
        <div class="pbar" aria-hidden="true">{#if rank.tied > 0}<i style="left:{rank.pctLo}%; width:{rank.pctHi - rank.pctLo}%"></i>{/if}<span style="left:{rank.pct}%"></span></div>
      {:else}
        <p class="muted">{t('st.noValue')}</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .stats { font-size: var(--fs-small); }
  .unit { font-size: var(--fs-meta); color: var(--muted); margin-top: 2px; }
  table { width: 100%; border-collapse: collapse; margin-top: 4px; }
  th { text-align: left; font-weight: 400; color: var(--text-2); padding: var(--sp-1) var(--sp-2) var(--sp-1) 0; vertical-align: top; }
  td { text-align: right; padding: var(--sp-1) 0; white-space: nowrap; }
  tr + tr { border-top: 1px solid var(--border); }
  .who { display: block; font-family: var(--font-sans); font-size: var(--fs-meta); color: var(--faint); }
  .muted { color: var(--muted); }
  .strong { font-weight: 700; font-size: var(--fs-body); }
  .foot { margin: 6px 0 0; }
  .filt { margin: 4px 0 0; font-size: var(--fs-meta); border-left: 3px solid var(--ink); padding-left: 6px; }
  .selblock { margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--rule); }
  .sname { margin: 3px 0 0; font-size: var(--fs-body); }
  .pbar { position: relative; height: 6px; margin: 8px 0 2px; background: var(--border); }
  .pbar i { position: absolute; top: 0; height: 6px; background: var(--surface-2); border: 1px solid var(--ink); border-width: 0 1px; }
  .pbar span { position: absolute; top: -3px; width: 3px; height: 12px; background: var(--ink); transform: translateX(-1.5px); }
  .foot a { color: inherit; }
</style>
