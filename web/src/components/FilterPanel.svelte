<script lang="ts">
  // Stacked filters: numeric ranges on any metric, categorical conditions and travel time to a hub,
  // combined with AND. Each condition shows how many units pass it and how many have no value.
  import { ml, t } from '../lib/i18n.svelte';
  import MetricPicker from './MetricPicker.svelte';
  import RangeFilter from './RangeFilter.svelte';
  import { fmtNumber, fmtPeriod } from '../lib/classify';
  import type { Hub, MetricMeta } from '../lib/data';
  import { catLabel, type CatOption, type FilterEval, type MatchResult } from '../lib/filters';
  import { CAT_FIELDS, T_MAX, type CatField, type Filter } from '../lib/hash';

  interface Props {
    evals: FilterEval[];
    match: MatchResult;
    total: number;
    unitWord: string;
    level: string;
    metrics: MetricMeta[];
    hubs: Hub[];
    options: (field: CatField) => CatOption[];
    /** metric used for a new numeric condition */
    defaultMetric: string;
    defaultHub: string;
    onset: (filters: Filter[]) => void;
    /** zoom the map to the matching units (shown while filters are active) */
    onzoom?: () => void;
    /** D31 station times in this build: the reach condition offers station time and door to door */
    station?: boolean;
    /** method line of a reach measure */
    method?: (mode: 'pt' | 'ptst' | 'car', hub: string) => string;
  }
  let { evals, match, total, unitWord, level, metrics, hubs, options, defaultMetric, defaultHub, onset, onzoom, station = false, method }: Props = $props();

  const filters = $derived(evals.map((e) => e.filter));
  function update(k: number, f: Filter) {
    onset(filters.map((x, j) => (j === k ? f : x)));
  }
  function remove(k: number) {
    onset(filters.filter((_, j) => j !== k));
  }
  function add(kind: string) {
    let f: Filter;
    if (kind === 'num') f = { kind: 'num', metric: defaultMetric, lo: null, hi: null };
    else if (kind === 'reach') f = { kind: 'reach', hub: defaultHub, mode: station ? 'ptst' : 'pt', max: 30 };
    else f = { kind: 'cat', field: kind as CatField, values: [] };
    onset([...filters, f]);
  }
  function toggle(k: number, id: string) {
    const f = filters[k];
    if (f.kind !== 'cat') return;
    const values = f.values.includes(id) ? f.values.filter((v) => v !== id) : [...f.values, id];
    update(k, { ...f, values });
  }
  let search = $state<Record<number, string>>({});
  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const short = (o: CatOption[]) => o.length > 0 && o.every((x) => x.name.length <= 14);
  const nameOf = (field: CatField, id: string) => options(field).find((o) => o.id === id)?.name ?? id;
</script>

<div class="filters">
  <div class="summary" aria-live="polite">
    {#if match.active}
      <span class="num">{t('fp.match', { n: fmtNumber(match.n, 0), total: fmtNumber(total, 0), units: unitWord })}</span>
      {#if match.active > 1}{t('fp.all', { n: match.active })}{/if}
      {#if match.nMissingOnly}<span class="miss">· <span class="hatch"></span> <span class="num">{fmtNumber(match.nMissingOnly, 0)}</span> {t('fp.excluded')}</span>{/if}
    {:else}
      {t('fp.none', { n: fmtNumber(total, 0), units: unitWord })}
    {/if}
    {#if filters.length}
      <span class="acts">
        {#if match.active && onzoom}<button type="button" class="link" onclick={onzoom}>{t('fp.zoom')}</button>{/if}
        <button type="button" class="link" onclick={() => onset([])}>{t('fp.clear')}</button>
      </span>
    {/if}
  </div>

  {#each evals as e, k (k)}
    {@const f = e.filter}
    <div class="cond" class:inactive={e.status === 'inactive'}>
      {#if f.kind === 'num'}
        <div class="ch">
          <div class="grow"><MetricPicker {metrics} {level} value={f.metric} onpick={(id) => update(k, { kind: 'num', metric: id, lo: null, hi: null })} /></div>
          <button type="button" class="x" aria-label={t('fp.remove')} onclick={() => remove(k)}>×</button>
        </div>
        {#if e.status === 'active' && e.domain && e.col}
          <RangeFilter label={ml(e.col.meta)} hideLabel min={e.domain.min} max={e.domain.max} lo={f.lo} hi={f.hi}
            log={e.domain.log} decimals={e.col.meta.decimals} onchange={(lo, hi) => update(k, { ...f, lo, hi })} />
          <p class="cf num">
            {e.col.meta.unit || t('fp.value')} · {fmtPeriod(e.col.col.period)} · {fmtNumber(e.nPass, 0)} {t('fp.pass')}{#if e.nMissing}{' · '}<span class="hatch"></span> {fmtNumber(e.nMissing, 0)} {t('fp.noDataEx')}{/if}
          </p>
        {/if}
      {:else if f.kind === 'cat'}
        {@const opts = options(f.field)}
        <div class="ch">
          <span class="caps grow">{catLabel(f.field)}</span>
          <button type="button" class="x" aria-label={t('fp.remove')} onclick={() => remove(k)}>×</button>
        </div>
        {#if short(opts)}
          <div class="chips" role="group" aria-label={catLabel(f.field)}>
            {#each opts as o}
              <button type="button" class="chip" aria-pressed={f.values.includes(o.id)} onclick={() => toggle(k, o.id)}>{o.name}</button>
            {/each}
          </div>
        {:else if opts.length}
          {#if f.values.length}
            <div class="chips">
              {#each f.values as id}<button type="button" class="chip" aria-pressed="true" title="Remove" onclick={() => toggle(k, id)}>{nameOf(f.field, id)} ×</button>{/each}
            </div>
          {/if}
          {#if opts.length > 12}
            <input type="search" class="find" placeholder={t('fp.search', { n: opts.length })} aria-label={t('fp.search', { n: catLabel(f.field) })}
              value={search[k] ?? ''} oninput={(ev) => (search = { ...search, [k]: ev.currentTarget.value })} />
          {/if}
          <div class="list" role="group" aria-label={catLabel(f.field)}>
            {#each opts.filter((o) => !search[k] || norm(o.name).includes(norm(search[k]))) as o}
              <label class="opt"><input type="checkbox" checked={f.values.includes(o.id)} onchange={() => toggle(k, o.id)} /> <span>{o.name}</span></label>
            {/each}
          </div>
        {/if}
        {#if e.status === 'active'}<p class="cf num">{fmtNumber(e.nPass, 0)} pass</p>{/if}
      {:else}
        <div class="ch">
          <span class="caps grow">{t('fp.travel')}</span>
          <button type="button" class="x" aria-label={t('fp.remove')} onclick={() => remove(k)}>×</button>
        </div>
        <div class="rr">
          <span>{t('fp.within')}</span>
          <output class="num strong">{f.max} min</output>
          <span>{t('fp.of')}</span>
          <select class="sel" value={f.hub} aria-label={t('common.hub')} onchange={(ev) => update(k, { ...f, hub: ev.currentTarget.value })}>
            {#each hubs as h}<option value={h.slug}>{h.name}</option>{/each}
          </select>
          <div class="seg" role="radiogroup" aria-label={t('common.mode')}>
            {#if station}
              <button type="button" role="radio" aria-checked={f.mode === 'ptst'} title={t('pt.st')} onclick={() => update(k, { ...f, mode: 'ptst' })}>{t('pt.stS')}</button>
              <button type="button" role="radio" aria-checked={f.mode === 'pt'} title={t('pt.dd')} onclick={() => update(k, { ...f, mode: 'pt' })}>{t('pt.ddS')}</button>
            {:else}
              <button type="button" role="radio" aria-checked={f.mode === 'pt' || f.mode === 'ptst'} onclick={() => update(k, { ...f, mode: 'pt' })}>{t('common.pt')}</button>
            {/if}
            <button type="button" role="radio" aria-checked={f.mode === 'car'} onclick={() => update(k, { ...f, mode: 'car' })}>{t('common.car')}</button>
          </div>
        </div>
        <input type="range" class="rng" min="0" max={T_MAX} step="5" value={f.max} aria-label={t('fp.maxTime')}
          oninput={(ev) => update(k, { ...f, max: +ev.currentTarget.value })} />
        {#if e.status === 'active'}
          <p class="cf num">
            {fmtNumber(e.nPass, 0)} {t('fp.pass')}{#if e.nMissing}{' · '}<span class="hatch"></span> {fmtNumber(e.nMissing, 0)} {t('fp.noTimeEx')}{/if}
          </p>
        {/if}
        {#if method}<p class="cf">{method(f.mode, e.hubName ?? f.hub)}</p>{/if}
      {/if}
      {#if e.note}<p class="cf note">{e.note}</p>{/if}
    </div>
  {/each}

  <label class="add">
    <span class="caps">{t('fp.add')}</span>
    <select class="sel" value="" onchange={(ev) => { const v = ev.currentTarget.value; ev.currentTarget.value = ''; if (v) add(v); }}>
      <option value="">{t('fp.choose')}</option>
      <option value="num">{t('fp.range')}</option>
      {#each CAT_FIELDS as fld}<option value={fld}>{catLabel(fld)}</option>{/each}
      <option value="reach">{t('fp.reach')}</option>
    </select>
  </label>
  <p class="foot">{t('fp.foot', { units: unitWord })}</p>
</div>

<style>
  .filters { font-size: 0.82rem; }
  .summary { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 6px; margin-bottom: 8px; }
  .miss { color: var(--text); }
  .acts { margin-left: auto; display: inline-flex; gap: 10px; }
  .link { border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: 0.78rem; }
  .cond { border-top: 1px solid var(--ink); padding: 8px 0 10px; }
  .cond.inactive .ch, .cond.inactive .chips, .cond.inactive .list { opacity: 0.6; }
  .ch { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .grow { flex: 1; min-width: 0; }
  .x { flex: none; width: 28px; height: 28px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-size: 1.05rem; line-height: 1; }
  .cf { margin: 4px 0 0; font-size: 0.74rem; color: var(--muted); }
  .note { color: var(--text); }
  .chips { display: flex; flex-wrap: wrap; gap: 4px; margin: 2px 0 2px; }
  .chip { padding: 2px 7px; border: 1px solid var(--ink); background: none; cursor: pointer; font-size: 0.76rem; font-weight: 500; }
  .chip[aria-pressed='true'] { background: var(--ink); color: var(--ink-text); }
  .find { width: 100%; margin: 4px 0; padding: 5px 8px; border: 1px solid var(--ink); font-size: 16px; background: var(--panel); border-radius: 0; }
  .list { max-height: 150px; overflow-y: auto; border: 1px solid var(--border); padding: 2px 6px; overscroll-behavior: contain; }
  .opt { display: flex; gap: 6px; align-items: baseline; padding: 2px 0; cursor: pointer; }
  .opt input { accent-color: var(--ink); margin: 0; flex: none; }
  .rr { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .strong { font-weight: 700; }
  .rng { width: 100%; accent-color: var(--ink); margin: 6px 0 0; }
  .sel {
    min-width: 0; padding: 3px 24px 3px 6px; border: 1px solid var(--ink); border-radius: 0; background: var(--panel); cursor: pointer;
    -webkit-appearance: none; appearance: none; font-size: 0.82rem;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%23000' stroke-width='1.4'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 6px center; background-size: 11px;
  }
  .seg button { padding: 2px 8px; font-size: 0.76rem; }
  .add { display: flex; align-items: center; justify-content: space-between; gap: 8px; border-top: 1px solid var(--ink); padding-top: 10px; }
  .add .sel { flex: 1; max-width: 220px; }
  .foot { margin: 8px 0 0; }
  @media (max-width: 899px) {
    .sel, .find { font-size: 16px; }
  }
</style>
