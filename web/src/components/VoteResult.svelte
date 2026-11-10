<script lang="ts">
  // Result of one federal vote (D32): national yes share and turnout, the official outcome where known,
  // the cantons' count (Ständemehr: half cantons count ½) and every canton's yes share around 50 %.
  import { fmtDate, fmtNumber, voteTitle } from '../lib/classify';
  import { t } from '../lib/i18n.svelte';
  import { app } from '../lib/state.svelte';
  import { standText, type VoteEntry, type VoteIndex } from '../lib/votes';

  interface Props {
    index: VoteIndex;
    entry: VoteEntry;
  }
  let { index, entry }: Props = $props();

  const title = $derived(entry.title[app.lang] ?? entry.title.en ?? entry.title.de ?? Object.values(entry.title)[0] ?? voteTitle(entry.period) ?? t('vt.untitled'));
  const rows = $derived(
    index.cantons
      .map((kt, k) => ({ kt, v: entry.canton_yes_pct[k] ?? null, half: index.half_cantons.includes(kt) }))
      .sort((a, b) => (b.v ?? -1) - (a.v ?? -1)),
  );
  const outcome = $derived(entry.accepted === true ? t('vt.accepted') : entry.accepted === false ? t('vt.rejected') : null);
</script>

<section class="vr" aria-label={t('vt.result')}>
  <div class="caps">{t('vt.result')}</div>
  <p class="tt">{title}</p>
  <p class="dt">{fmtDate(entry.date)}{#if entry.provisional}{' · '}<strong>{t('vt.provL')}</strong>{/if}</p>
  <table class="nat">
    <tbody>
      <tr><th>{t('vt.ch')}</th><td class="num strong">{entry.yes_pct !== null ? `${fmtNumber(entry.yes_pct, 1)}% ${t('vt.yes')}` : '–'}</td></tr>
      {#if entry.turnout_pct !== null}<tr><th>{t('vt.turnout')}</th><td class="num">{fmtNumber(entry.turnout_pct, 1)}%</td></tr>{/if}
      {#if entry.cantons_yes !== null}
        <tr><th>{t('vt.cantons')}</th><td class="num">{standText(entry.cantons_yes)} : {standText(entry.cantons_no)}
          <span class="muted">{t('vt.of', { n: entry.cantons_total ?? '' })}</span></td></tr>
      {/if}
      {#if outcome}<tr><th>{t('vt.outcome')}</th><td class="strong">{outcome}</td></tr>{/if}
    </tbody>
  </table>
  <div class="kts" role="list">
    {#each rows as r (r.kt)}
      <div class="kt" role="listitem">
        <span class="kc">{r.kt}{r.half ? '½' : ''}</span>
        <span class="bar" aria-hidden="true">
          {#if r.v !== null}<i class:yes={r.v > 50} style="width:{Math.max(0, Math.min(100, r.v))}%"></i>{/if}<b></b>
        </span>
        <span class="kv num">{r.v !== null ? fmtNumber(r.v, 1) : '–'}</span>
      </div>
    {/each}
  </div>
  <p class="foot">{t('vt.note')}</p>
</section>

<style>
  .vr { font-size: 0.8rem; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid var(--rule); }
  .tt { margin: 3px 0 0; font-weight: 700; font-size: 0.9rem; line-height: 1.3; }
  .dt { margin: 1px 0 4px; color: var(--muted); font-size: 0.76rem; }
  .nat { width: 100%; border-collapse: collapse; }
  .nat th { text-align: left; font-weight: 400; color: var(--muted); padding: 3px 8px 3px 0; }
  .nat td { text-align: right; padding: 3px 0; }
  .nat tr + tr { border-top: 1px solid var(--border); }
  .strong { font-weight: 700; }
  .muted { color: var(--muted); }
  .kts { display: grid; grid-template-columns: 1fr 1fr; gap: 1px 14px; margin-top: 8px; }
  .kt { display: grid; grid-template-columns: 2.4em minmax(0, 1fr) 2.8em; align-items: center; gap: 4px; }
  .kc { font-weight: 600; font-size: 0.74rem; }
  .bar { position: relative; height: 8px; background: var(--panel-2); }
  .bar i { position: absolute; left: 0; top: 0; bottom: 0; background: #d98a55; }
  .bar i.yes { background: #6290bb; }
  .bar b { position: absolute; left: 50%; top: -2px; bottom: -2px; width: 1px; background: var(--ink); }
  .kv { text-align: right; font-size: 0.74rem; }
  .foot { margin: 6px 0 0; }
</style>
