<script lang="ts">
  // Ranking table: the matching units with the shade, size and filter metrics as columns.
  // Sortable by any column (missing values always last); tapping a row selects the unit.
  import { ml, t } from '../lib/i18n.svelte';
  import { fmtNumber, fmtPeriod, unitOf } from '../lib/classify';
  import type { MetricMeta } from '../lib/data';
  import { copyText, downloadCSV, slug, toTSV, type Cell } from '../lib/export';

  export interface RankColumn {
    key: string;
    tag: string; // short role: 'Shade', 'Size', 'Filter', 'Reach'
    meta: MetricMeta;
    label?: string;
    v: (number | null)[];
    period: string;
    /** flag markers of a unit's value (△ small numbers, M, °, p), when the column has flags */
    marks?: (i: number) => string;
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
    /** zoom the map to the listed units */
    onzoom?: () => void;
    /** unit ids (export) */
    ids?: string[];
    /** source name of a metric's source id (export) */
    sourceName?: (sourceId: string) => string;
    /** units to flag as below the minimum population (marked ▽ and drawn lighter) */
    small?: Set<number>;
  }
  let { columns, rows, names, cantons, showCanton, sel, unitWord, onselect, onzoom, ids, sourceName, small }: Props = $props();

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
  /** rank by the sorted column: equal values share the best rank ('=' marks a tie); by name: the row number */
  const rankNo = $derived.by(() => {
    const out = new Map<number, { r: number; tie: boolean }>();
    if (key === 'name') {
      sorted.forEach((i, k) => out.set(i, { r: k + 1, tie: false }));
      return out;
    }
    const v = columns.find((c) => c.key === key)!.v;
    let r = 0;
    for (let k = 0; k < sorted.length; k++) {
      const x = v[sorted[k]];
      if (x === null || x === undefined) break;
      if (k === 0 || x !== v[sorted[k - 1]]) r = k + 1;
      const tie = (k > 0 && v[sorted[k - 1]] === x) || (k + 1 < sorted.length && v[sorted[k + 1]] === x);
      out.set(sorted[k], { r, tie });
    }
    return out;
  });
  // ------------------------------------------------------------------ export (D32)
  /** all listed rows in the current order: id, name, canton, then value, period and source per column */
  function table(): Cell[][] {
    const head: Cell[] = ['id', t('rt.name'), t('cat.kanton')];
    for (const c of columns) {
      const lb = c.label ?? ml(c.meta);
      head.push(c.meta.unit ? `${lb} [${unitOf(c.meta)}]` : lb, `${lb} – ${t('ex.period')}`, `${lb} – ${t('ex.source')}`);
      if (c.marks) head.push(`${lb} – ${t('ex.flags')}`);
    }
    const out: Cell[][] = [head];
    for (const i of sorted) {
      const r: Cell[] = [ids?.[i] ?? '', names[i], cantons[i] || ''];
      for (const c of columns) {
        r.push(c.v[i] ?? null, c.period, sourceName ? sourceName(c.meta.source) : c.meta.source);
        if (c.marks) r.push(c.marks(i));
      }
      out.push(r);
    }
    return out;
  }
  let copied = $state<string | null>(null);
  function csv() {
    const k = columns.find((c) => c.key === key);
    downloadCSV(table(), `gemeindebank-${slug(k ? (k.label ?? ml(k.meta)) : 'ranking')}.csv`);
  }
  async function copy() {
    const ok = await copyText(toTSV(table()));
    copied = ok ? t('ex.copied', { n: fmtNumber(sorted.length, 0) }) : t('ex.copyFail');
    setTimeout(() => (copied = null), 2500);
  }
  const fmt = (x: number | null | undefined, m: MetricMeta) => (x === null || x === undefined ? '–' : fmtNumber(x, m.decimals));
  const arrow = (k: string) => (k === key ? (desc ? ' ↓' : ' ↑') : '');
</script>

<div class="rank">
  <p class="cap">{#if onzoom}<button type="button" class="zoom" onclick={onzoom}>{t('fp.zoom')}</button>{/if}<span class="num">{fmtNumber(rows.length, 0)}</span> {unitWord}{rows.length ? t('rt.sorted', { by: key === 'name' ? t('rt.nameL') : (columns.find((c) => c.key === key)?.label ?? ml(columns.find((c) => c.key === key)?.meta)) }) : ''}. {t('rt.tap')}</p>
  <div class="wrap">
    <table>
      <thead>
        <tr>
          <th class="n">#</th>
          <th class="nm" aria-sort={key === 'name' ? (desc ? 'descending' : 'ascending') : 'none'}><button type="button" onclick={() => sortBy('name')}>{t('rt.name')}{arrow('name')}</button></th>
          {#each columns as c (c.key)}
            <th class="v" title="{ml(c.meta)} ({unitOf(c.meta) || t('fp.value')}, {fmtPeriod(c.period)})" aria-sort={key === c.key ? (desc ? 'descending' : 'ascending') : 'none'}>
              <button type="button" onclick={() => sortBy(c.key)}>
                <span class="tg">{t(`rt.tag.${c.tag}`)}</span>
                <span class="lb">{c.label ?? ml(c.meta)}{arrow(c.key)}</span>
                <span class="un">{unitOf(c.meta) || '–'}</span>
              </button>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each shown as i (i)}
          {@const rn = rankNo.get(i)}
          <tr class:sel={i === sel} class:small={small?.has(i)} onclick={() => onselect(i)}>
            <td class="n num" title={rn?.tie ? t('rt.tie') : undefined}>{rn ? `${rn.tie ? '=' : ''}${rn.r}` : '–'}</td>
            <td class="nm"><button type="button" class="rowbtn" onclick={(e) => { e.stopPropagation(); onselect(i); }}>{names[i]}</button>{#if small?.has(i)}<span class="sm" title={t('rx.small')} aria-label={t('rx.small')}>▽</span>{/if}{#if showCanton && cantons[i]}<span class="kt">{cantons[i]}</span>{/if}</td>
            {#each columns as c (c.key)}<td class="v num">{fmt(c.v[i], c.meta)}{#if c.marks}{@const mk = c.marks(i)}{#if mk}<sup class="fl" title={t('fl.key')}>{mk}</sup>{/if}{/if}</td>{/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {#if shown.length < sorted.length}
    <button type="button" class="more" onclick={() => (limit += 400)}>{t('rt.more', { n: fmtNumber(Math.min(400, sorted.length - shown.length), 0), of: fmtNumber(sorted.length - shown.length, 0) })}</button>
  {/if}
  <div class="ex">
    <button type="button" onclick={csv} title={t('ex.csvT')}>{t('ex.csv')}</button>
    <button type="button" onclick={copy} title={t('ex.copyT')}>{t('ex.copy')}</button>
    {#if copied}<span class="ok" role="status">{copied}</span>{/if}
  </div>
  <p class="foot">{t('rt.foot', { units: unitWord })} {t('ex.note', { n: fmtNumber(rows.length, 0) })}{#if columns.some((c) => c.marks)}{' '}{t('fl.key')}{/if}</p>
</div>

<style>
  .rank { font-size: var(--fs-small); min-width: 0; }
  .cap { margin: 0 0 6px; color: var(--muted); }
  .zoom { float: right; margin-left: 8px; border: 1px solid var(--ink); background: var(--panel); padding: 1px 7px; font-size: var(--fs-meta); font-weight: 600; cursor: pointer; color: var(--text); }
  .wrap { overflow-x: auto; max-width: 100%; }
  table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
  thead th { text-align: left; position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--ink); vertical-align: bottom; padding: 0; z-index: 1; }
  th button { display: flex; flex-direction: column; width: 100%; border: 0; background: none; padding: 4px 4px 4px 0; cursor: pointer; text-align: inherit; font-weight: 700; font-size: var(--fs-meta); }
  th.v button { align-items: flex-end; text-align: right; padding: 4px 0 4px 6px; }
  .tg { font-size: var(--fs-cap); text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-2); }
  .lb { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; max-width: 9em; line-height: 1.2; }
  .un { font-weight: 400; color: var(--muted); font-size: var(--fs-cap); }
  td { padding: 3px 0; border-bottom: 1px solid var(--border); }
  td.v { text-align: right; padding-left: 6px; white-space: nowrap; }
  td.n, th.n { width: 1%; color: var(--muted); padding-right: 6px; text-align: right; font-size: var(--fs-meta); }
  th.n { font-weight: 700; color: var(--text); padding: 4px 6px 4px 0; }
  td.nm { max-width: 13em; line-height: 1.25; overflow-wrap: break-word; word-break: normal; hyphens: manual; }
  .rowbtn { border: 0; background: none; padding: 0; cursor: pointer; font-weight: 500; text-align: left; }
  .kt { color: var(--muted); font-size: var(--fs-cap); margin-left: 4px; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: var(--panel-2); }
  tr.small td { color: var(--muted); }
  .sm { color: var(--text); font-size: var(--fs-cap); margin-left: 4px; }
  tr.sel { box-shadow: inset 3px 0 0 var(--ink); background: var(--surface-2); }
  tr.sel .rowbtn { color: var(--text); font-weight: 700; }
  .more { margin-top: 8px; width: 100%; padding: 6px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-weight: 500; }
  .foot { margin: 6px 0 0; }
  .ex { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 8px; }
  .ex button { border: 1px solid var(--ink); background: var(--panel); padding: 4px 10px; cursor: pointer; font-size: var(--fs-meta); font-weight: 600; color: var(--text); }
  .ok { font-size: var(--fs-meta); color: var(--text); }
  .fl { font-size: var(--fs-cap); color: var(--text); margin-left: 1px; font-family: var(--font-sans); }
</style>
