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
  <div class="vin" role="radiogroup" aria-label={tv('vin.label')} aria-busy={busy}>
    <span class="caps lab" aria-hidden="true">{tv('vin.label')}</span>
    <div class="seg">
      <button type="button" role="radio" aria-checked={cur === null} title={tv('vin.refT', { date: fmtDate(ix.reference) })}
        onclick={() => pick(null)}>{tv('vin.ref', { y: refYear })}</button>
      {#each ix.vintages as v}
        <button type="button" role="radio" aria-checked={cur === v.id} title={tv('vin.oldT', { date: fmtDate(v.date) })}
          onclick={() => pick(v.id)}>{v.id}</button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .vin { display: inline-flex; align-items: center; gap: 6px; background: var(--panel); border: 1px solid var(--ink); padding: 0 0 0 6px; max-width: 100%; }
  .vin[aria-busy='true'] { cursor: progress; }
  .lab { font-size: 0.66rem; }
  .seg { border: 0; border-left: 1px solid var(--ink); }
  .seg button { padding: 3px 8px; font-size: 0.74rem; font-weight: 600; }
  @media (max-width: 899px) {
    .seg button { padding: 4px 7px; font-size: 0.72rem; }
  }
</style>
