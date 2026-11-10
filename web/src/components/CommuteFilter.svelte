<script lang="ts">
  // One commute condition (lib/commute.svelte.ts): measure, hubs, mode and the limit.
  import { t } from '../lib/i18n.svelte';
  import { fmtNumber } from '../lib/classify';
  import { COMMUTE_OPS, T_MAX, type CommuteOp } from '../lib/hash';
  import type { Hub } from '../lib/data';
  import type { FilterEval } from '../lib/filters';
  import { defaultCommute, commuteHubSlugs, nearestHubCount, reachTimesData, type CommuteFilter } from '../lib/commute.svelte';
  import RangeFilter from './RangeFilter.svelte';

  interface Props {
    e: FilterEval;
    f: CommuteFilter;
    hubs: Hub[];
    /** D31 station times in this build */
    station: boolean;
    onchange: (f: CommuteFilter) => void;
    onremove: () => void;
  }
  let { e, f, hubs, station, onchange, onremove }: Props = $props();

  /** hubs with travel times (the hub picker of the map also lists hubs that only have lines) */
  const avail = $derived.by(() => {
    const ok = new Set(commuteHubSlugs(reachTimesData()));
    return ok.size ? hubs.filter((h) => ok.has(h.slug)) : hubs;
  });
  const nameOf = (slug: string) => hubs.find((h) => h.slug === slug)?.name ?? slug;
  const multi = $derived(f.op === 'sum' || f.op === 'max' || f.op === 'any');
  const limitMax = $derived(f.op === 'sum' ? T_MAX * 2 : T_MAX);
  const nNear = $derived(nearestHubCount(reachTimesData()));

  function setOp(op: CommuteOp) {
    if (op === f.op) return;
    const d = defaultCommute(op, f.hubs.length ? f.hubs : avail.map((h) => h.slug), station);
    // keep the mode and, where the measure allows several hubs, the hubs already chosen
    const keepHubs = (op === 'sum' || op === 'max' || op === 'any') && multi ? f.hubs : d.hubs;
    onchange({ ...d, mode: op === 'diff' && f.mode === 'car' ? d.mode : f.mode, hubs: keepHubs });
  }
  function addHub(slug: string) {
    if (slug && !f.hubs.includes(slug)) onchange({ ...f, hubs: [...f.hubs, slug] });
  }
  const removeHub = (slug: string) => onchange({ ...f, hubs: f.hubs.filter((h) => h !== slug) });
  const free = $derived(avail.filter((h) => !f.hubs.includes(h.slug)));
  const missKey = $derived(f.op === 'diff' ? 'cm.noTimeDiff' : f.op === 'sum' || f.op === 'max' ? 'cm.noTimeEx' : 'cm.noTimeAny');
  const leKey = $derived(`cm.${f.op === 'sum' ? 'sumLe' : f.op === 'max' ? 'maxLe' : f.op === 'any' ? 'anyLe' : 'nearLe'}`);
</script>

<div class="ch">
  <select class="sel grow" value={f.op} aria-label={t('cm.op')} onchange={(ev) => setOp(ev.currentTarget.value as CommuteOp)}>
    {#each COMMUTE_OPS as op}<option value={op}>{t(`cm.op.${op}`)}</option>{/each}
  </select>
  <button type="button" class="x" aria-label={t('fp.remove')} onclick={onremove}>×</button>
</div>

{#if f.op === 'diff'}
  <div class="rr">
    <span>{t('cm.diffOf')}</span>
    <select class="sel" value={f.hubs[0] ?? ''} aria-label={t('common.hub')} onchange={(ev) => onchange({ ...f, hubs: [ev.currentTarget.value] })}>
      {#each avail as h}<option value={h.slug}>{h.name}</option>{/each}
    </select>
    <div class="seg" role="radiogroup" aria-label={t('common.mode')}>
      {#if station}
        <button type="button" role="radio" aria-checked={f.mode === 'ptst'} title={t('pt.st')} onclick={() => onchange({ ...f, mode: 'ptst' })}>{t('pt.stS')}</button>
        <button type="button" role="radio" aria-checked={f.mode !== 'ptst'} title={t('pt.dd')} onclick={() => onchange({ ...f, mode: 'pt' })}>{t('pt.ddS')}</button>
      {:else}
        <button type="button" role="radio" aria-checked="true" onclick={() => onchange({ ...f, mode: 'pt' })}>{t('common.pt')}</button>
      {/if}
    </div>
    <span>− {t('common.car')}</span>
  </div>
{:else}
  {#if f.op === 'near'}
    <p class="cf">{t('cm.help.near', { n: nNear })}</p>
  {:else}
    <div class="chips" role="group" aria-label={t('cm.hubs')}>
      {#each f.hubs as h}
        <button type="button" class="chip" aria-pressed="true" aria-label={t('cm.removeHub', { hub: nameOf(h) })} onclick={() => removeHub(h)}>{nameOf(h)} ×</button>
      {/each}
    </div>
    <select class="sel add" value="" aria-label={t('cm.addHub')} onchange={(ev) => { const v = ev.currentTarget.value; ev.currentTarget.value = ''; addHub(v); }}>
      <option value="">{t('cm.addHub')}</option>
      {#each free as h}<option value={h.slug}>{h.name}</option>{/each}
    </select>
  {/if}
  <div class="rr mode">
    <div class="seg" role="radiogroup" aria-label={t('common.mode')}>
      {#if station}
        <button type="button" role="radio" aria-checked={f.mode === 'ptst'} title={t('pt.st')} onclick={() => onchange({ ...f, mode: 'ptst' })}>{t('pt.stS')}</button>
        <button type="button" role="radio" aria-checked={f.mode === 'pt'} title={t('pt.dd')} onclick={() => onchange({ ...f, mode: 'pt' })}>{t('pt.ddS')}</button>
      {:else}
        <button type="button" role="radio" aria-checked={f.mode !== 'car'} onclick={() => onchange({ ...f, mode: 'pt' })}>{t('common.pt')}</button>
      {/if}
      <button type="button" role="radio" aria-checked={f.mode === 'car'} onclick={() => onchange({ ...f, mode: 'car' })}>{t('common.car')}</button>
    </div>
  </div>
{/if}

{#if e.status === 'active' && f.op === 'diff' && e.domain}
  <RangeFilter label={t('cm.diffRange')} min={Math.floor(e.domain.min)} max={Math.ceil(e.domain.max)} lo={f.lo} hi={f.hi} log={false} decimals={0}
    onchange={(lo, hi) => onchange({ ...f, lo, hi })} />
{:else if f.op !== 'diff'}
  <div class="rr lim">
    <span>{t(leKey)}</span>
    <output class="num strong">{f.hi ?? limitMax} min</output>
  </div>
  <input type="range" class="rng" min="0" max={limitMax} step="5" value={Math.min(f.hi ?? limitMax, limitMax)} style="--pct:{(100 * Math.min(f.hi ?? limitMax, limitMax)) / limitMax}%" aria-label={t('cm.maxTime')}
    oninput={(ev) => onchange({ ...f, lo: null, hi: +ev.currentTarget.value })} />
{/if}
{#if e.status === 'active'}
  <p class="cf num">
    {fmtNumber(e.nPass, 0)} {t('cm.pass')}{#if e.nMissing}{' · '}<span class="hatch"></span> {fmtNumber(e.nMissing, 0)} {t(missKey)}{/if}
  </p>
{/if}
<p class="cf">{t(`cm.help.${f.op}`, { n: nNear })}</p>

<style>
  .ch { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .grow { flex: 1; min-width: 0; }
  .x { flex: none; width: 28px; height: 28px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-size: var(--fs-lead); line-height: 1; }
  .cf { margin: 4px 0 0; font-size: var(--fs-meta); color: var(--muted); }
  .chips { display: flex; flex-wrap: wrap; gap: 4px; margin: 2px 0 4px; }
  .chip { padding: 2px 7px; border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text); cursor: pointer; font-size: var(--fs-meta); font-weight: 500; }
  .rr { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .mode { margin-top: 6px; }
  .lim { margin-top: 8px; }
  .strong { font-weight: 700; }
  .rng { width: 100%; margin: var(--sp-1) 0 0; }
  .sel {
    min-width: 0; padding: 3px 24px 3px 6px; border: 1px solid var(--ink); border-radius: 0; background: var(--panel); cursor: pointer;
    -webkit-appearance: none; appearance: none; font-size: var(--fs-small); color: var(--text);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%23000' stroke-width='1.4'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 6px center; background-size: 11px;
  }
  .sel.add { width: 100%; }
  .seg button { padding: 2px 8px; font-size: var(--fs-meta); }
  @media (max-width: 899px) {
    .sel { font-size: var(--fs-input); }
  }
</style>
