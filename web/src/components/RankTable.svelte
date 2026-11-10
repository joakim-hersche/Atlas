<script lang="ts">
  // Ranking table: the matching units with the shade, size and filter metrics as columns.
  // Sortable by any column (missing values always last); tapping a row selects the unit.
  import { fmtNumber, fmtPeriod } from '../lib/classify';
  import type { MetricMeta } from '../lib/data';

  export interface RankColumn {
    key: string;
    tag: string; // short role: 'Shade', 'Size', 'Filter', 'Reach'
    meta: MetricMeta;
    label?: string;
    v: (number | null)[];
    period: string;
  }
  interface Props {
    columns: RankColumn[];
    /** unit indices to list (the matching units) */
    rows: number[];
    names: string[];
    cantons: string[];
    showCanton: boolean;
    sel: number | null;
    unitWord: string;
    onselect: (i: number) => void;
  }
  let { columns, rows, names, cantons, showCanton, sel, unitWord, onselect }: Props = $props();

  const PAGE = 100;
  let sortKey = $state<string | null>(null);
  let desc = $state(true);
  let limit = $state(PAGE);

  const key = $derived(sortKey && (sortKey === 'name' || columns.some((c) => c.key === sortKey)) ? sortKey : (columns[0]?.key ?? 'name'));
  const sorted = $derived.by(() => {
    const out = rows.slice();
    if (key === 'name') {
      out.sort((a, b) => names[a].localeCompare(names[b], 'de') * (desc ? -1 : 1));
      return out;
    }
    const v = columns.find((c) => c.key === key)!.v;
    out.sort((a, b) => {
      const x = v[a];
      const y = v[b];
      if (x === null || x === undefined) return y === null || y === undefined ? 0 : 1;
      if (y === null || y === undefined) return -1;
      return desc ? y - x : x - y;
    });
    return out;
  });
  // keep the selected unit visible: show the page it is on
  const shown = $derived.by(() => {
    const p = sel === null ? -1 : sorted.indexOf(sel);
    return sorted.slice(0, Math.max(limit, p + 1));
  });
  function sortBy(k: string) {
    if (k === key) desc = !desc;
    else {
      sortKey = k;
      desc = k !== 'name';
    }
    limit = PAGE;
  }
  const fmt = (x: number | null | undefined, m: MetricMeta) => (x === null || x === undefined ? '–' : fmtNumber(x, m.decimals));
  const arrow = (k: string) => (k === key ? (desc ? ' ↓' : ' ↑') : '');
</script>

<div class="rank">
  <p class="cap"><span class="num">{fmtNumber(rows.length, 0)}</span> {unitWord}{rows.length ? ', sorted by ' + (key === 'name' ? 'name' : (columns.find((c) => c.key === key)?.label ?? columns.find((c) => c.key === key)?.meta.label_en)) : ''}. Tap a row to select it on the map.</p>
  <div class="wrap">
    <table>
      <thead>
        <tr>
          <th class="n">#</th>
          <th class="nm"><button type="button" onclick={() => sortBy('name')} aria-sort={key === 'name' ? (desc ? 'descending' : 'ascending') : 'none'}>Name{arrow('name')}</button></th>
          {#each columns as c (c.key)}
            <th class="v" title="{c.meta.label_en} ({c.meta.unit || 'value'}, {fmtPeriod(c.period)})">
              <button type="button" onclick={() => sortBy(c.key)} aria-sort={key === c.key ? (desc ? 'descending' : 'ascending') : 'none'}>
                <span class="tg">{c.tag}</span>
                <span class="lb">{c.label ?? c.meta.label_en}{arrow(c.key)}</span>
                <span class="un">{c.meta.unit || '–'}</span>
              </button>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each shown as i, k (i)}
          <tr class:sel={i === sel} onclick={() => onselect(i)}>
            <td class="n num">{k + 1}</td>
            <td class="nm"><button type="button" class="rowbtn" onclick={(e) => { e.stopPropagation(); onselect(i); }}>{names[i]}</button>{#if showCanton && cantons[i]}<span class="kt">{cantons[i]}</span>{/if}</td>
            {#each columns as c (c.key)}<td class="v num">{fmt(c.v[i], c.meta)}</td>{/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {#if shown.length < sorted.length}
    <button type="button" class="more" onclick={() => (limit += 400)}>Show {fmtNumber(Math.min(400, sorted.length - shown.length), 0)} more of {fmtNumber(sorted.length - shown.length, 0)}</button>
  {/if}
  <p class="foot">Ranks are by the sorted column among the listed {unitWord}; – = no data (always listed last).</p>
</div>

<style>
  .rank { font-size: 0.8rem; min-width: 0; }
  .cap { margin: 0 0 6px; color: var(--muted); }
  .wrap { overflow-x: auto; max-width: 100%; }
  table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
  thead th { position: sticky; top: 0; background: var(--panel); border-bottom: 2px solid var(--ink); vertical-align: bottom; padding: 0; z-index: 1; }
  th button { display: flex; flex-direction: column; width: 100%; border: 0; background: none; padding: 4px 4px 4px 0; cursor: pointer; text-align: inherit; font-weight: 700; font-size: 0.72rem; }
  th.v button { align-items: flex-end; text-align: right; padding: 4px 0 4px 6px; }
  .tg { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent); }
  .lb { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; max-width: 9em; line-height: 1.2; }
  .un { font-weight: 400; color: var(--muted); font-size: 0.68rem; }
  td { padding: 3px 0; border-bottom: 1px solid var(--border); }
  td.v { text-align: right; padding-left: 6px; white-space: nowrap; }
  td.n, th.n { width: 1%; color: var(--muted); padding-right: 6px; text-align: right; font-size: 0.72rem; }
  th.n { font-weight: 700; color: var(--text); padding: 4px 6px 4px 0; }
  td.nm { max-width: 11em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .rowbtn { border: 0; background: none; padding: 0; cursor: pointer; font-weight: 500; text-align: left; }
  .kt { color: var(--muted); font-size: 0.7rem; margin-left: 4px; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: var(--panel-2); }
  tr.sel { box-shadow: inset 3px 0 0 var(--accent); background: var(--accent-soft); }
  tr.sel .rowbtn { color: var(--accent); font-weight: 700; }
  .more { margin-top: 8px; width: 100%; padding: 6px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-weight: 500; }
  .foot { margin: 6px 0 0; }
</style>
