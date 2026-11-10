<script lang="ts">
  import { gapReason, partialCantons, precisionOf, PRECISION_TEXT, type Column, type ColumnFile, type MetricMeta, type Source } from '../lib/data';
  import { fmtNumber, fmtPeriod, fmtValue, rankOf } from '../lib/classify';

  interface Reach {
    label: string; // 'Public transport' | 'Car'
    short: string; // 'PT' | 'Car'
    hub: string;
    minutes: number | null;
    reason: string | null;
    within: boolean;
  }
  interface Props {
    name: string;
    canton: string;
    bfs: string;
    meta: MetricMeta;
    file: ColumnFile;
    col: Column;
    index: number;
    source: Source | undefined;
    reach: Reach | null;
    docked?: boolean;
    onclose: () => void;
  }
  let { name, canton, bfs, meta, file, col, index, source, reach, docked = false, onclose }: Props = $props();

  const value = $derived(col.v[index]);
  const rank = $derived(rankOf(col.v, index, meta.direction));
  const precision = $derived(PRECISION_TEXT[precisionOf(file, col, index, meta)] ?? precisionOf(file, col, index, meta));
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);
</script>

<div class="card" class:docked role="dialog" aria-label="{name} quick card">
  <div class="top">
    <h2>{name}</h2>
    <span class="sub">{canton} · BFS {bfs}</span>
    <button type="button" class="close" aria-label="Close" onclick={onclose}>×</button>
  </div>
  <p class="mlabel">{meta.label_en}</p>
  {#if value !== null}
    <div class="valrow">
      <span class="val">{fmtValue(value, meta)}</span>
      <span class="yr">{fmtPeriod(col.period)}</span>
      {#if rank}
        <span class="rank">
          Rank {fmtNumber(rank.rank, 0)} of {fmtNumber(rank.n, 0)} · P{Math.round(rank.pct)}<span class="long">{cov ? ' · among municipalities with data' : ''}
          <span class="muted">({meta.direction === 'lower_better' ? '1 = lowest' : '1 = highest'})</span></span>
        </span>
      {/if}
    </div>
  {:else}
    <div class="valrow">
      <span class="val nodata"><span class="hatch"></span>No data</span>
      <span class="yr">{fmtPeriod(col.period)}</span>
      <span class="rank reason">{gapReason(file, col, index, meta, canton)}</span>
    </div>
  {/if}
  <div class="foot">
    <span class="tags">
      <span class="tag">{precision}</span>
      {#if cov}<span class="tag warn">partial: {cov.length} of 26 cantons</span>{/if}
      <span class="tag src" title={source?.attribution ?? ''}>{publisher} {fmtPeriod(col.period)}</span>
    </span>
    {#if reach}
      <span class="reach">
        <span class="rl"><span class="long">{reach.label} from {reach.hub}</span><span class="short">{reach.short}</span></span>
        {#if reach.minutes !== null}
          <span class="rv" class:within={reach.within}>{fmtNumber(reach.minutes, 0)} min</span>
        {:else}
          <span class="rv muted">{reach.reason ?? 'no data'}</span>
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
  .sub { color: var(--muted); font-size: 0.78rem; flex: 1; min-width: 0; font-family: var(--font-mono); }
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
  .nodata { color: var(--muted); display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-sans); }
  .muted { color: var(--muted); }
  .foot { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 6px 10px; margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--rule); }
  .tags { display: flex; flex-wrap: wrap; gap: 0; font-size: 0.72rem; color: var(--faint); }
  .tag + .tag::before { content: '·'; margin: 0 5px; color: var(--faint); }
  .tag.warn { color: var(--text); }
  .reach { display: flex; gap: 8px; align-items: baseline; font-size: 0.82rem; }
  .rl { color: var(--muted); }
  .rv { font-weight: 700; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  .rv.within { color: var(--accent); }
  .short { display: none; }
  @media (min-width: 900px) {
    .reach { flex-basis: 100%; justify-content: space-between; }
  }
  @media (max-width: 899px) {
    .card { padding: 7px 10px 8px; }
    h2 { font-size: 0.98rem; }
    .close { width: 24px; height: 24px; }
    .mlabel { display: none; }
    .val { font-size: 1.15rem; }
    .rank { flex-basis: auto; font-size: 0.78rem; margin: 0; }
    .rank::before { content: '· '; color: var(--muted); }
    .long { display: none; }
    .short { display: inline; }
    .foot { margin-top: 5px; flex-wrap: nowrap; }
    .tags { flex-wrap: nowrap; overflow: hidden; white-space: nowrap; }
    .reach { flex: none; font-size: 0.8rem; }
  }
</style>
