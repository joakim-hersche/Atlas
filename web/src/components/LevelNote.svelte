<script lang="ts">
  // One-line note after a level switch replaced a metric that does not exist at the new level,
  // with "switch back" (previous level and metrics) and dismiss.
  import { t } from '../lib/i18n.svelte';
  import { confirmAsk, currentAsk, currentLevelNote, levelsOf, switchBack } from '../lib/levels';
  import { levelName, levelWord, ml } from '../lib/i18n.svelte';
  import type { Base } from '../lib/data';
  import { app } from '../lib/state.svelte';

  interface Props {
    /** 'float': over the map; 'bar': a full-width line */
    variant?: 'float' | 'bar';
    base?: Base;
  }
  let { variant = 'float', base }: Props = $props();
  const text = $derived(currentLevelNote());
  const ask = $derived(currentAsk());
  const askMeta = $derived(ask && base ? base.metas.get(ask.metric) : undefined);
  const fbMeta = $derived(ask?.fallback && base ? base.metas.get(ask.fallback) : undefined);
</script>

{#if ask && askMeta}
  <p class="lnote ask {variant}" role="status">
    <span class="tx">{t('level.ask', { metric: ml(askMeta), level: levelWord(ask.level),
      levels: levelsOf(askMeta).map((l) => levelName(l)).join(', ') || '–' })}</span>
    {#if fbMeta && base}
      <button type="button" class="back" onclick={() => confirmAsk(base)}>{t('level.go', { level: levelName(ask.level), fallback: ml(fbMeta) })}</button>
    {/if}
    <button type="button" class="stay" onclick={() => (app.levelAsk = null)}>{t('level.stay')}</button>
  </p>
{:else if text}
  <p class="lnote {variant}" role="status">
    <span class="tx">{text}</span>
    <button type="button" class="back" onclick={switchBack}>{t('level.back')}</button>
    <button type="button" class="lx" aria-label={t('common.dismiss')} onclick={() => (app.levelNote = null)}>×</button>
  </p>
{/if}

<style>
  .lnote { margin: 0; display: flex; align-items: center; gap: 6px; font-size: 0.76rem; background: var(--panel); }
  .float { max-width: 440px; border: 1px solid var(--ink); padding: 3px 3px 3px 8px; }
  .bar { flex: none; padding: 5px 8px 5px 16px; font-size: 0.78rem; border-bottom: 1px solid var(--rule); }
  .tx { flex: 1; min-width: 0; }
  .back { flex: none; border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text); padding: 2px 8px; cursor: pointer; font-size: 0.74rem; font-weight: 600; white-space: nowrap; }
  .stay { flex: none; border: 1px solid var(--ink); background: var(--panel); color: var(--text); padding: 2px 8px; cursor: pointer; font-size: 0.74rem; font-weight: 600; white-space: nowrap; }
  .ask { flex-wrap: wrap; row-gap: 4px; }
  .lx { flex: none; border: 0; background: none; cursor: pointer; font-size: 1rem; line-height: 1; padding: 0 4px; color: var(--text); }
</style>
