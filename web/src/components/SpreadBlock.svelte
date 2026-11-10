<script lang="ts">
  // C1: the morning spread of the public-transport times between a municipality and one hub, both directions:
  // "36 min (35–41)" (median, 10–90 % of the morning's connections) for the station time and door to door, with
  // the range including waiting on a second line. Definitions come from reach/spread.json.
  import { t } from '../lib/i18n.svelte';
  import '../lib/i18n-ux';
  import { app } from '../lib/state.svelte';
  import {
    fmtRange, fmtSpread, loadSpread, loadSpreadIndex, spreadDef, spreadIdx, spreadLate, spreadOf, spreadReason,
    type SpreadDir, type SpreadFile, type SpreadIndex, type SpreadKind,
  } from '../lib/spread';

  interface Props {
    unit: string;
    hub: string;
    hubName: string;
    /** the build has station times (D31): show both measures; else door to door only */
    station?: boolean;
  }
  let { unit, hub, hubName, station = true }: Props = $props();

  let ix = $state.raw<SpreadIndex | null | undefined>(undefined);
  let f = $state.raw<SpreadFile | null | undefined>(undefined);
  loadSpreadIndex().then((x) => (ix = x)).catch(() => (ix = null));
  $effect(() => {
    const h = hub;
    let live = true;
    f = undefined;
    loadSpread(h).then((x) => live && (f = x)).catch(() => live && (f = null));
    return () => (live = false);
  });
  const k = $derived(ix ? spreadIdx(ix, unit) : -1);
  const kinds = $derived<SpreadKind[]>(station ? ['pt_station', 'pt'] : ['pt']);
  const DIRS: SpreadDir[] = ['to', 'from'];
  const def = (key: string) => spreadDef(ix ?? null, key, app.lang);
  function cell(dir: SpreadDir, kind: SpreadKind) {
    if (!f || k < 0) return null;
    const j = spreadOf(f, k, dir, kind, 'journey');
    const w = spreadOf(f, k, dir, kind, 'with_wait');
    return {
      main: fmtSpread(j),
      wait: fmtRange(w),
      why: j?.mid === null || j === null ? spreadReason(f, k, dir, kind) : null,
      late: dir === 'to' ? spreadLate(f, k, kind) : null,
    };
  }
</script>

{#if ix && f && k >= 0}
  <div class="spread">
    <table>
      <thead>
        <tr>
          <th></th>
          {#each DIRS as d}<th class="n" title={def(d)}>{t(d === 'to' ? 'sp2.toHub' : 'sp2.fromHub', { hub: hubName })}</th>{/each}
        </tr>
      </thead>
      <tbody>
        {#each kinds as kind}
          <tr>
            <th scope="row" title={def(kind)}>{t(kind === 'pt_station' ? 'p.reachSt' : 'p.reachDoor')}</th>
            {#each DIRS as d}
              {@const c = cell(d, kind)}
              <td class="n">
                {#if c?.main}
                  <span class="v">{c.main}{#if c.late}<sup title={t('sp2.late', { t: c.late })}>*</sup>{/if}</span>
                  {#if c.wait}<span class="w" title={def('with_wait')}>{t('sp2.waitL', { a: c.wait.split('–')[0], b: c.wait.split('–')[1] })}</span>{/if}
                {:else}
                  <span class="none" title={c?.why ?? undefined}>{t('sp2.none')}</span>
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
    <p class="foot">{t('sp2.legend')}</p>
    {#if DIRS.some((d) => kinds.some((kd) => cell(d, kd)?.late))}
      <p class="foot">* {t('sp2.late', { t: kinds.map((kd) => cell('to', kd)?.late).find(Boolean) ?? '' })}</p>
    {/if}
    {#each DIRS as d}
      {#each kinds as kd}
        {@const c = cell(d, kd)}
        {#if c && !c.main && c.why}<p class="foot">{t(d === 'to' ? 'sp2.toHub' : 'sp2.fromHub', { hub: hubName })}: {c.why}</p>{/if}
      {/each}
    {/each}
    <details class="how">
      <summary>{t('sp2.how')}</summary>
      <ul>
        {#each ['to', 'from', 'journey', 'with_wait', ...kinds] as key}{#if def(key)}<li>{def(key)}</li>{/if}{/each}
      </ul>
    </details>
  </div>
{:else if ix === null || f === null}
  <p class="foot">{t('sp2.notBuilt')}</p>
{:else if ix && f && k < 0}
  <p class="foot">{t('sp2.none')}</p>
{:else}
  <p class="foot">…</p>
{/if}

<style>
  .spread { padding: var(--sp-2) 0 var(--sp-1); }
  table { width: 100%; border-collapse: collapse; font-size: var(--fs-small); line-height: var(--lh-small); }
  th { text-align: left; font-weight: 600; font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text-2); padding: 0 var(--sp-2) var(--sp-1) 0; vertical-align: bottom; }
  td, tbody th { padding: var(--sp-1) var(--sp-2) var(--sp-1) 0; border-top: var(--rule-row); vertical-align: top; }
  .n { text-align: right; padding-right: 0; }
  .v { display: block; font-weight: 700; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .w { display: block; font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text-3); font-variant-numeric: tabular-nums; }
  td + td { padding-left: var(--sp-3); }
  .none { color: var(--text-3); }
  .foot { margin: var(--sp-1) 0 0; }
  .how { margin-top: var(--sp-1); font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .how summary { cursor: pointer; font-weight: 600; }
  .how ul { margin: var(--sp-1) 0 0; padding-left: var(--sp-4); color: var(--text-2); }
  .how li + li { margin-top: var(--sp-1); }
</style>
