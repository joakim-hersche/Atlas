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
    onclose: () => void;
  }
  let { name, canton, bfs, meta, file, col, index, source, reach, onclose }: Props = $props();

  const value = $derived(col.v[index]);
  const rank = $derived(rankOf(col.v, index, meta.direction));
  const precision = $derived(PRECISION_TEXT[precisionOf(file, col, index, meta)] ?? precisionOf(file, col, index, meta));
  const cov = $derived(partialCantons(meta));
  const publisher = $derived(source ? source.publisher.split(' (')[0] : meta.source);
</script>

<div class="card" role="dialog" aria-label="{name} quick card">
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
          Rank {fmtNumber(rank.rank, 0)} of {fmtNumber(rank.n, 0)}<span class="long">{cov ? ' municipalities with data' : ' in Switzerland'}
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
      <span class="tag src" title={source?.attribution ?? ''}>{publisher}</span>
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
    background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow);
    padding: 12px 14px; width: 100%;
  }
  .top { display: flex; align-items: baseline; gap: 8px; }
  h2 { margin: 0; font-size: 1.15rem; line-height: 1.2; }
  .sub { color: var(--muted); font-size: 0.85rem; flex: 1; min-width: 0; }
  .close {
    border: 0; background: var(--panel-2); width: 30px; height: 30px; border-radius: 50%; font-size: 1.2rem; line-height: 1;
    cursor: pointer; flex: none; align-self: start;
  }
  .mlabel { margin: 4px 0 0; color: var(--muted); font-size: 0.85rem; }
  .valrow { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 6px; margin-top: 1px; }
  .val { font-size: 1.25rem; font-weight: 650; font-variant-numeric: tabular-nums; }
  .yr { font-size: 0.8rem; color: var(--muted); }
  .rank { flex-basis: 100%; font-size: 0.88rem; margin-top: 2px; }
  .reason { color: var(--text); }
  .nodata { color: var(--muted); display: inline-flex; align-items: center; gap: 6px; }
  .muted { color: var(--muted); }
  .foot { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 6px 10px; margin-top: 8px; }
  .tags { display: flex; flex-wrap: wrap; gap: 4px; }
  .tag { font-size: 0.72rem; padding: 2px 7px; border-radius: 999px; background: var(--panel-2); border: 1px solid var(--border); color: var(--muted); }
  .tag.warn { color: var(--text); border-color: var(--nodata-line); }
  .reach { display: flex; gap: 8px; align-items: baseline; font-size: 0.9rem; }
  .rl { color: var(--muted); }
  .rv { font-weight: 650; font-variant-numeric: tabular-nums; }
  .rv.within { color: var(--reach-line); }
  .short { display: none; }
  @media (min-width: 900px) {
    .reach { flex-basis: 100%; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 8px; }
  }
  @media (max-width: 899px) {
    .card { padding: 8px 12px 9px; }
    h2 { font-size: 1.02rem; }
    .sub { font-size: 0.8rem; }
    .close { width: 26px; height: 26px; font-size: 1.05rem; }
    .mlabel { display: none; }
    .val { font-size: 1.05rem; }
    .rank { flex-basis: auto; font-size: 0.82rem; margin: 0; }
    .rank::before { content: '· '; color: var(--muted); }
    .long { display: none; }
    .short { display: inline; }
    .foot { margin-top: 5px; flex-wrap: nowrap; }
    .tags { flex-wrap: nowrap; overflow: hidden; }
    .reach { flex: none; font-size: 0.85rem; }
  }
  .hatch {
    display: inline-block; width: 18px; height: 14px; border-radius: 2px; border: 1px solid var(--nodata-line);
    background: repeating-linear-gradient(-45deg, var(--nodata-line) 0 1.5px, var(--nodata-fill) 1.5px 5px);
  }
</style>
