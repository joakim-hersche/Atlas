<script lang="ts">
  import { levelName, ml, t, tiedText } from '../lib/i18n.svelte';
  import Term from './Term.svelte';
  import { glossKeyOf } from '../lib/glossary.svelte';
  import { flagTexts, flagsOf, gapReason, noteOf, partialCantons, precisionOf, precisionText, type Column, type ColumnFile, type MetricMeta, type Source } from '../lib/data';
  import { fmtNumber, fmtPeriod, fmtValue, rankOf } from '../lib/classify';

  interface Reach {
    label: string; // 'Public transport' | 'Car'
    short: string; // 'PT' | 'Car'
    hub: string;
    minutes: number | null;
    reason: string | null;
    within: boolean;
    /** D31 headline: station time towards the hub ("Winterthur → Zürich HB 22 min, from Winterthur") */
    station?: { minutes: number | null; from: string | null; reason: string | null; name: string };
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
    /** link to the place's profile page */
    profile?: string;
    profileLabel?: string;
    sourceLink?: string;
    /** D21: the value is that of a coarser area (its level) */
    regional?: string | null;
    onclose: () => void;
  }
  let { name, canton, sub, meta, file, col, index, source, reach, docked = false, unitWord = 'municipalities', extra = [], profile, profileLabel = 'Profile', sourceLink, regional = null, onclose }: Props = $props();

  const value = $derived(col.v[index]);
  const rank = $derived(rankOf(col.v, index, meta.direction));
  const precision = $derived(precisionText(precisionOf(file, col, index, meta)));
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);

  /** flags of the value (small numbers, majority election, published value, provisional) */
  const flags = $derived(value !== null ? flagTexts(file, flagsOf(file, col, index), meta) : []);
  /** provenance note of a shown value (e.g. "published canton value; …") */
  const note = $derived(value !== null ? noteOf(col, index) : null);
</script>

<div class="card" class:docked role="dialog" aria-label={name}>
  <div class="top">
    <div class="ttl"><h2>{name}</h2> <span class="sub">{sub}</span></div>
    {#if profile}<a class="prof" href={profile}>{profileLabel}&nbsp;→</a>{/if}
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
  {:else}
    <div class="valrow">
      <span class="val nodata"><span class="hatch"></span>{t('p.noData')}</span>
      <span class="yr">{fmtPeriod(col.period)}</span>
      <span class="rank reason">{gapReason(file, col, index, meta, canton)}</span>
    </div>
  {/if}
  {#each flags as f}<p class="flag">{f}{#if f.startsWith('M ')}<Term k="majority_election" />{/if}</p>{/each}
  {#if note}<p class="flag">{note}</p>{/if}
  {#each extra as x}
    <div class="extra"><span class="xl">{x.label}</span><span class="xv num">{x.value}</span></div>
  {/each}
  <div class="foot">
    <span class="tags">
      <span class="tag">{precision}</span>
      {#if cov}<span class="tag warn">{t('p.partial', { n: cov.length })}</span>{/if}
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
            <span class="rl">{t('pt.byPt')}{st.from ? `, ${t('pt.from', { st: st.from })}` : ''}</span>
          {:else}
            <span class="rv muted">{st.reason ?? t('lg.noData')}</span>
          {/if}
        </div>
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
  @media (min-width: 900px) {
    .reach { flex-basis: 100%; justify-content: space-between; }
  }
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
    .pm { display: none; }
  }
</style>
