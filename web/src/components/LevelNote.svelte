<script lang="ts">
  // One-line note after a level switch replaced a metric that does not exist at the new level,
  // with "switch back" (previous level and metrics) and dismiss.
  import { t } from '../lib/i18n.svelte';
  import { currentLevelNote, switchBack } from '../lib/levels';
  import { app } from '../lib/state.svelte';

  interface Props {
    /** 'float': over the map; 'bar': a full-width line */
    variant?: 'float' | 'bar';
  }
  let { variant = 'float' }: Props = $props();
  const text = $derived(currentLevelNote());
</script>

{#if text}
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
  .lx { flex: none; border: 0; background: none; cursor: pointer; font-size: 1rem; line-height: 1; padding: 0 4px; color: var(--text); }
</style>
