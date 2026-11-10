<script lang="ts">
  // Legend of the spatial map modes. Cluster map: the five classes with their counts. Bivariate map: the
  // 3x3 colour grid with one axis per metric (shade metric along, second metric up), counts in the titles.
  import Term from './Term.svelte';
  import { fmtNumber } from '../lib/classify';
  import { t } from '../lib/i18n.svelte';
  import '../lib/i18n-spatial';
  import { BIVARIATE, LISA_COLOURS } from '../lib/spatial-colours';
  import type { LisaClasses } from '../lib/spatial';

  interface Props {
    mode: 'lisa' | 'bi';
    lisa?: LisaClasses | null;
    /** bivariate: units per cell (index 3 * third of B + third of A) and the metric labels */
    counts?: number[] | null;
    labelA?: string;
    labelB?: string;
    compact?: boolean;
    /** "back to values" link */
    onoff?: () => void;
  }
  let { mode, lisa = null, counts = null, labelA = '', labelB = '', compact = false, onoff }: Props = $props();

  const ROWS = [
    { k: 'hh', c: LISA_COLOURS.hh },
    { k: 'll', c: LISA_COLOURS.ll },
    { k: 'lh', c: LISA_COLOURS.lh },
    { k: 'hl', c: LISA_COLOURS.hl },
    { k: 'ns', c: LISA_COLOURS.ns },
  ] as const;
  const third = (k: number) => t(`sp.bi.third.${k}`);
  /** grid rows from the top: second metric high, mid, low */
  const cells = [2, 1, 0].flatMap((b) => [0, 1, 2].map((a) => ({ a, b, i: 3 * b + a })));
  const title = (c: { a: number; b: number; i: number }) =>
    `${labelA}: ${third(c.a)} · ${labelB}: ${third(c.b)}${counts ? ` · ${fmtNumber(counts[c.i], 0)}` : ''}`;
</script>

<div class="sl" class:compact>
  {#if mode === 'lisa'}
    <ul class="cl" aria-label={t('sp.mode.lisa')}>
      {#each ROWS as r}
        <li>
          <span class="sw" style="background:{r.c}"></span>
          <span class="lab">{t(`sp.lisa.${r.k}`)}</span>
          {#if lisa && !compact}<span class="cn num">{fmtNumber(lisa.counts[r.k], 0)}</span>{/if}
        </li>
      {/each}
      {#if lisa && lisa.counts.none && !compact}
        <li><span class="sw none"></span><span class="lab">{t('sp.lisa.none')}</span><span class="cn num">{fmtNumber(lisa.counts.none, 0)}</span></li>
      {/if}
    </ul>
  {:else}
    <div class="bv">
      <div class="grid" role="img" aria-label={t('sp.legendBi', { a: labelA, b: labelB })}>
        {#each cells as c}
          <span class="cell" style="background:{BIVARIATE[c.i]}" title={title(c)}></span>
        {/each}
      </div>
      <div class="ax">
        <p><span class="chip" style="background:{BIVARIATE[2]}"></span>{t('sp.bi.axisX', { m: labelA })}</p>
        <p><span class="chip" style="background:{BIVARIATE[6]}"></span>{t('sp.bi.axisY', { m: labelB })}</p>
      </div>
    </div>
  {/if}
  {#if !compact}
    <p class="note"><Term k={mode === 'lisa' ? 'lisa' : 'bivariate_map'} /></p>
  {/if}
  {#if onoff}<button type="button" class="link" onclick={onoff}>{t('sp.off')}</button>{/if}
</div>

<style>
  .sl { font-size: 0.76rem; }
  .cl { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr; gap: 3px; }
  .cl li { display: flex; align-items: center; gap: 7px; }
  .sw { width: 14px; height: 14px; flex: none; border: 1px solid rgba(0, 0, 0, 0.25); }
  .sw.none { background: repeating-linear-gradient(45deg, #fff, #fff 2px, #cfcfcf 2px, #cfcfcf 3px); }
  .lab { flex: 1; min-width: 0; }
  .cn { color: var(--faint); }
  .compact .cl { grid-template-columns: 1fr 1fr; gap: 1px 10px; font-size: 0.7rem; }
  .compact .sw { width: 10px; height: 10px; }
  .bv { display: flex; align-items: flex-start; gap: 10px; }
  .ax { min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: space-between; align-self: stretch; }
  .ax p { margin: 0 0 6px; font-weight: 600; line-height: 1.3; overflow-wrap: anywhere; }
  .chip { display: inline-block; width: 9px; height: 9px; margin-right: 5px; border: 1px solid rgba(0, 0, 0, 0.25); vertical-align: baseline; }
  .grid { display: grid; grid-template-columns: repeat(3, 28px); grid-auto-rows: 28px; gap: 1px; background: #fff; border: 1px solid var(--ink); }
  .compact .grid { grid-template-columns: repeat(3, 16px); grid-auto-rows: 16px; }
  .cell { display: block; }
  .note { margin: 4px 0 0; }
  .link { border: 0; background: none; padding: 0; margin-top: 4px; text-decoration: underline; cursor: pointer; font-size: inherit; color: var(--text); }
</style>
