<script lang="ts">
  import { levelName, ml, t, tiedText } from '../lib/i18n.svelte';
  import Term from './Term.svelte';
  import { glossKeyOf } from '../lib/glossary.svelte';
  import { coverageLabel, majorityValue, flagTexts, flagsOf, gapReason, noteOf, partialCantons, precisionOf, precisionText, type Column, type ColumnFile, type MetricMeta, type Source } from '../lib/data';
  import { fmtNumber, fmtPeriod, fmtValue, rankOf } from '../lib/classify';

  interface Reach {
    label: string; // 'Public transport' | 'Car'
    short: string; // 'PT' | 'Car'
    hub: string;
    minutes: number | null;
    reason: string | null;
    within: boolean;
    /** D31 headline: station time towards the hub ("Winterthur → Zürich HB 22 min, from Winterthur") */
    station?: { minutes: number | null; from: { name: string; outside: boolean } | null; reason: string | null; name: string; note?: string | null };
    /** D31 second line: door to door towards the hub */
    door?: { minutes: number | null; reason: string | null };
    /** measure used on the map ('ptst' | 'pt') */
    active?: string;
    /** one-line method of the active measure */
    method?: string;
    /** before the D31 data: public transport measured from the hub outwards */
    outward?: boolean;
  }
  interface Extra {
    label: string;
    value: string;
  }
  interface Props {
    name: string;
    /** canton code, used for the coverage gap reason */
    canton: string;
    /** line next to the name, e.g. 'ZH · BFS 261' */
    sub: string;
    meta: MetricMeta;
    file: ColumnFile | null;
    col: Column;
    index: number;
    source: Source | undefined;
    reach: Reach | null;
    docked?: boolean;
    unitWord?: string;
    /** further rows, e.g. the size metric */
    extra?: Extra[];
    /** further one-line notes (e.g. canton boundaries) */
    notes?: string[];
    /** link to the place's profile page */
    profile?: string;
    profileLabel?: string;
    sourceLink?: string;
    /** D21: the value is that of a coarser area (its level) */
    regional?: string | null;
    /** phone: a two-line strip (name, value, rank, travel time) that expands on tap, so the map stays visible */
    compact?: boolean;
    onclose: () => void;
  }
  let { name, canton, sub, meta, file, col, index, source, reach, docked = false, unitWord = 'municipalities', extra = [], notes = [], profile, profileLabel = 'Profile', sourceLink, regional = null, compact = false, onclose }: Props = $props();
  /** compact strip opened to the full card (kept while other places are selected) */
  let expanded = $state(false);

  const value = $derived(col.v[index]);
  /** D37: a single-seat canton's value, kept apart from classes and ranks (shown here, labelled) */
  const majVal = $derived(value === null ? majorityValue(col, index) : null);
  const rank = $derived(rankOf(col.v, index, meta.direction));
  const precision = $derived(precisionText(precisionOf(file, col, index, meta)));
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);

  /** flags of the value (small numbers, majority election, published value, provisional) */
  const flags = $derived(value !== null || majVal !== null ? flagTexts(file, flagsOf(file, col, index), meta) : []);
  /** provenance note of a shown value (e.g. "published canton value; …") */
  const note = $derived(value !== null ? noteOf(col, index) : null);
  /** strip: the travel time in one line ("Winterthur → Zürich HB 20 min") */
  const reachLine = $derived.by(() => {
    if (!reach) return null;
    const st = reach.station;
    const m = st ? st.minutes : reach.minutes;
    const time = m !== null ? `${fmtNumber(m, 0)} min` : t('lg.noData');
    return { text: `${reach.short} → ${reach.hub}`, time, within: m !== null && reach.within };
  });
</script>

{#if compact && !expanded}
  <div class="card strip" role="dialog" aria-label={name}>
    <button type="button" class="sbtn" aria-expanded="false" title={t('card.expand')} onclick={() => (expanded = true)}>
      <span class="l1"><strong>{name}</strong> <span class="sub">{sub}</span></span>
      <span class="l2 num">
        {#if value !== null}
          <span class="sval">{fmtValue(value, meta)}</span>
          <span class="yr">{fmtPeriod(col.period)}</span>
          {#if rank}<span class="srank">· {t('card.rank', { r: fmtNumber(rank.rank, 0), n: fmtNumber(rank.n, 0) })}</span>{/if}
          {#if flags.length}<span class="smark">{flags.map((f) => f.split(' ')[0]).join('')}</span>{/if}
        {:else if majVal !== null}
          <span class="sval">{fmtValue(majVal, meta)}</span>
          <span class="yr">{fmtPeriod(col.period)}</span>
          <span class="smark">M</span> <span class="srank">{t('card.majShort')}</span>
        {:else}
          <span class="nodata"><span class="hatch"></span>{t('p.noData')}</span>
        {/if}
      </span>
      {#if reachLine}<span class="l3"><span class="rl">{reachLine.text}</span> <span class="rv" class:within={reachLine.within}>{reachLine.time}</span></span>{/if}
      <svg class="chev" viewBox="0 0 20 12" width="16" height="10" aria-hidden="true"><path d="M2 10l8-8 8 8" /></svg>
    </button>
    <div class="sside">
      <button type="button" class="close" aria-label={t('common.close')} onclick={onclose}>×</button>
      {#if profile}<a class="prof" href={profile}>{profileLabel}&nbsp;→</a>{/if}
    </div>
  </div>
{:else}
<div class="card" class:docked class:compact role="dialog" aria-label={name}>
  <div class="top">
    <div class="ttl"><h2>{name}</h2> <span class="sub">{sub}</span></div>
    {#if profile}<a class="prof" href={profile}>{profileLabel}&nbsp;→</a>{/if}
    {#if compact}
      <button type="button" class="close" aria-expanded="true" aria-label={t('card.collapse')} title={t('card.collapse')} onclick={() => (expanded = false)}>
        <svg class="chev" viewBox="0 0 20 12" width="12" height="8" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
      </button>
    {/if}
    <button type="button" class="close" aria-label={t('common.close')} onclick={onclose}>×</button>
  </div>
  <p class="mlabel">{ml(meta)}<Term k={glossKeyOf(meta)} /></p>
  {#if value !== null}
    <div class="valrow">
      <span class="val">{fmtValue(value, meta)}</span>
      <span class="yr">{fmtPeriod(col.period)}</span>
      {#if rank}
        <span class="rank">
          {t('card.rank', { r: fmtNumber(rank.rank, 0), n: fmtNumber(rank.n, 0) })}{tiedText(rank)} · P{Math.round(rank.pct)}<Term k="percentile" /><span class="long">{cov ? ` · ${t('card.amongData', { units: unitWord })}` : ''}
          <span class="muted">({meta.direction === 'lower_better' ? t('card.oneLowest') : t('card.oneHighest')})</span></span>
        </span>
      {/if}
    </div>
  {:else if majVal !== null}
    <div class="valrow">
      <span class="val">{fmtValue(majVal, meta)}</span>
      <span class="yr">{fmtPeriod(col.period)}</span>
      <span class="rank reason">{t('card.majNoRank')}</span>
    </div>
  {:else}
    <div class="valrow">
      <span class="val nodata"><span class="hatch"></span>{t('p.noData')}</span>
      <span class="yr">{fmtPeriod(col.period)}</span>
      <span class="rank reason">{gapReason(file, col, index, meta, canton)}</span>
    </div>
  {/if}
  {#each flags as f}<p class="flag">{f}{#if f.startsWith('M ')}<Term k="majority_election" />{/if}</p>{/each}
  {#if note}<p class="flag">{note}</p>{/if}
  {#each notes as nt}<p class="flag">{nt}</p>{/each}
  {#each extra as x}
    <div class="extra"><span class="xl">{x.label}</span><span class="xv num">{x.value}</span></div>
  {/each}
  <div class="foot">
    <span class="tags">
      <span class="tag">{precision}</span>
      {#if cov}<span class="tag warn">{coverageLabel(meta)}</span>{/if}
      {#if regional}<span class="tag warn">{t('rg.tag', { level: levelName(regional, false) })}</span>{/if}
      {#if sourceLink}<a class="tag src" href={sourceLink} title={source?.attribution ?? ''}>{publisher} {fmtPeriod(col.period)}</a>
      {:else}<span class="tag src" title={source?.attribution ?? ''}>{publisher} {fmtPeriod(col.period)}</span>{/if}
    </span>
    {#if reach?.station}
      {@const st = reach.station}
      <div class="pt">
        <div class="ptl">
          <span class="rl">{st.name} → {reach.hub}</span>
          {#if st.minutes !== null}
            <span class="rv" class:within={reach.within && reach.active === 'ptst'}>{fmtNumber(st.minutes, 0)} min</span>
            <span class="rl">{t('pt.byPt')}{st.from ? `, ${t(st.from.outside ? 'pt.fromOut' : 'pt.from', { st: st.from.name })}` : ''}</span>
          {:else}
            <span class="rv muted">{st.reason ?? t('lg.noData')}</span>
          {/if}
        </div>
        {#if st.note}<p class="pm nt">{st.note}</p>{/if}
        {#if reach.door}
          <div class="ptl sub2">
            <span class="rl">{t('pt.door')}</span>
            {#if reach.door.minutes !== null}
              <span class="rv" class:within={reach.within && reach.active === 'pt'}>{fmtNumber(reach.door.minutes, 0)} min</span>
            {:else}
              <span class="rv muted">{reach.door.reason ?? t('lg.noData')}</span>
            {/if}
          </div>
        {/if}
        {#if reach.method}<p class="pm">{reach.method}</p>{/if}
      </div>
    {:else if reach}
      <span class="reach">
        <span class="rl"><span class="long">{t(reach.outward ? 'card.fromHub' : 'card.toHub', { mode: reach.label, hub: reach.hub })}</span><span class="short">{reach.short}</span></span>
        {#if reach.minutes !== null}
          <span class="rv" class:within={reach.within}>{fmtNumber(reach.minutes, 0)} min</span>
        {:else}
          <span class="rv muted">{reach.reason ?? t('lg.noData')}</span>
        {/if}
      </span>
    {/if}
  </div>
</div>
{/if}

<style>
  .card {
    background: var(--panel); border: 1px solid var(--ink); border-top: 3px solid var(--ink);
    padding: 10px 12px; width: 100%;
  }
  .card.docked { box-shadow: none; border: 0; padding: 0; background: none; }
  .top { display: flex; align-items: baseline; gap: 8px; }
  h2 { margin: 0; font-size: 1.1rem; line-height: 1.2; font-weight: 700; letter-spacing: -0.01em; }
  .ttl { flex: 1; min-width: 0; display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 8px; }
  h2 { display: inline; }
  .sub { color: var(--muted); font-size: 0.78rem; font-family: var(--font-mono); white-space: nowrap; }
  .prof {
    flex: none; align-self: start; font-size: 0.78rem; font-weight: 700; color: var(--ink-text); background: var(--ink); padding: 4px 8px;
    text-decoration: none; white-space: nowrap;
  }
  a.tag { color: var(--faint); }
  .close {
    border: 1px solid var(--ink); background: none; width: 26px; height: 26px; font-size: 1.05rem; line-height: 1;
    cursor: pointer; flex: none; align-self: start; color: var(--text);
  }
  .mlabel { margin: 8px 0 0; color: var(--text); font-weight: 700; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; }
  .valrow { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 8px; margin-top: 1px; }
  .val { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  .yr { font-size: 0.75rem; color: var(--muted); font-family: var(--font-mono); }
  .rank { flex-basis: 100%; font-size: 0.8rem; margin-top: 2px; font-variant-numeric: tabular-nums; }
  .reason { color: var(--text); }
  .flag { margin: 3px 0 0; font-size: 0.76rem; color: var(--text); border-left: 3px solid var(--accent); padding-left: 6px; line-height: 1.3; }
  .nodata { color: var(--muted); display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-sans); }
  .muted { color: var(--muted); }
  .extra { display: flex; justify-content: space-between; gap: 10px; font-size: 0.8rem; margin-top: 4px; }
  .xl { color: var(--muted); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .xv { font-weight: 600; flex: none; }
  .foot { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 6px 10px; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--rule); }
  .tags { display: flex; flex-wrap: wrap; gap: 0; font-size: 0.72rem; color: var(--faint); }
  .tag + .tag::before { content: '·'; margin: 0 5px; color: var(--faint); display: inline-block; }
  .tag.warn { color: var(--text); }
  .reach { display: flex; gap: 8px; align-items: baseline; font-size: 0.82rem; }
  .rl { color: var(--muted); }
  .rv { font-weight: 700; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  .rv.within { color: var(--accent); }
  .short { display: none; }
  .pt { flex-basis: 100%; font-size: 0.82rem; }
  .ptl { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 8px; }
  .ptl .rv { font-size: 1rem; }
  .sub2 .rv { font-size: 0.86rem; }
  .pm { margin: 2px 0 0; font-size: 0.7rem; color: var(--faint); line-height: 1.3; }
  .pm.nt { color: var(--text); }
  @media (min-width: 900px) {
    .reach { flex-basis: 100%; justify-content: space-between; }
  }
  /* phone strip: two or three short lines; the whole strip opens the full card */
  .strip { display: flex; align-items: stretch; gap: 8px; padding: 6px 8px 6px 10px; }
  .sbtn {
    flex: 1; min-width: 0; display: grid; grid-template-columns: minmax(0, 1fr) auto; column-gap: 8px; align-items: baseline;
    border: 0; background: none; padding: 0; text-align: left; cursor: pointer; color: var(--text);
  }
  .sbtn > span { grid-column: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sbtn .chev { grid-column: 2; grid-row: 1 / span 3; align-self: center; }
  .l1 strong { font-size: 0.95rem; font-weight: 700; letter-spacing: -0.01em; }
  .sbtn > .l2 { font-size: 0.8rem; margin-top: 1px; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.3; }
  .sval { font-weight: 700; font-size: 0.95rem; }
  .srank { color: var(--text); }
  .smark { margin-left: 4px; color: var(--accent); font-weight: 700; }
  .l3 { font-size: 0.78rem; margin-top: 1px; }
  .l3 .rv { font-size: 0.8rem; }
  .sside { flex: none; display: flex; flex-direction: column; align-items: flex-end; justify-content: space-between; gap: 4px; }
  .chev { fill: none; stroke: var(--ink); stroke-width: 2.5; stroke-linecap: square; }
  .close .chev { display: block; margin: auto; }
  .compact { max-height: 100%; min-height: 0; flex: 0 1 auto; overflow-y: auto; overscroll-behavior: contain; }
  @media (max-width: 899px) {
    .card { padding: 7px 10px 8px; }
    h2 { font-size: 0.98rem; }
    .prof {
    flex: none; align-self: start; font-size: 0.78rem; font-weight: 700; color: var(--ink-text); background: var(--ink); padding: 4px 8px;
    text-decoration: none; white-space: nowrap;
  }
  a.tag { color: var(--faint); }
  .close { width: 24px; height: 24px; }
    .mlabel { display: none; }
    .val { font-size: 1.15rem; }
    .rank { flex-basis: auto; font-size: 0.78rem; margin: 0; }
    .rank::before { content: '· '; color: var(--muted); }
    .long { display: none; }
    .short { display: inline; }
    .foot { margin-top: 5px; flex-wrap: nowrap; }
    .foot:has(.pt) { flex-wrap: wrap; }
    .tags { flex-wrap: nowrap; overflow: hidden; white-space: nowrap; }
    .reach { flex: none; font-size: 0.8rem; }
    .pt { font-size: 0.78rem; }
    .pm:not(.nt) { display: none; }
  }
</style>
