<script lang="ts">
  // Boundaries switch (docs/older_boundaries.md): the harmonised reference state or an older
  // municipality state. Hidden when the build has no older vintages (no vintages.json).
  import type { Base } from '../lib/data';
  import { currentVintage, loadVintageIndex, switchVintage, type VintageIndex } from '../lib/vintage';
  import { fmtDate, tv } from '../lib/vintage-strings.svelte';

  interface Props {
    base: Base;
  }
  let { base }: Props = $props();

  let ix = $state.raw<VintageIndex | null>(null);
  $effect(() => {
    loadVintageIndex().then((x) => (ix = x));
  });
  const cur = $derived(currentVintage());
  const refYear = $derived(ix ? ix.reference.slice(0, 4) : '');
  let busy = $state(false);
  async function pick(id: string | null) {
    if (busy || id === cur) return;
    busy = true;
    try {
      await switchVintage(base, id);
    } finally {
      busy = false;
    }
  }
</script>

{#if ix && ix.vintages.length}
  <!-- a quiet line in the panel (owner: the boundaries choice must not sit front and centre on the map) -->
  <div class="vin foot" role="radiogroup" aria-label={tv('vin.label')} aria-busy={busy}>
    <span class="lab">{tv('vin.label')}:</span>
    <button type="button" class="opt" role="radio" aria-checked={cur === null} title={tv('vin.refT', { date: fmtDate(ix.reference) })}
      onclick={() => pick(null)}>{tv('vin.ref', { y: refYear })}</button>
    {#each ix.vintages as v}
      <span class="sep" aria-hidden="true">·</span>
      <button type="button" class="opt" role="radio" aria-checked={cur === v.id} title={tv('vin.oldT', { date: fmtDate(v.date) })}
        onclick={() => pick(v.id)}>{v.id}</button>
    {/each}
  </div>
{/if}

<style>
  .vin { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 6px; margin: 8px 0 0; }
  .vin[aria-busy='true'] { cursor: progress; }
  .lab { color: var(--muted); }
  .sep { color: var(--muted); }
  .opt { border: 0; background: none; padding: 0; min-height: 0; font: inherit; color: var(--text); text-decoration: underline; text-underline-offset: 2px; cursor: pointer; }
  .opt[aria-checked='true'] { text-decoration: none; font-weight: 600; color: var(--ink); cursor: default; }
  /* touch: a 40 px target around the short text, without changing the line's look */
  @media (pointer: coarse) { .opt { min-height: 40px; min-width: 40px; margin: -12px 0; } }
</style>
