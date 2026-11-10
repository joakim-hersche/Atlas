<script lang="ts" module>
  let openId = $state<string | null>(null);
  let uid = 0;
</script>

<script lang="ts">
  // ⓘ next to a word of jargon: tap or click shows a plain-language explanation from the glossary.
  // Renders nothing when the glossary has no entry (or the build ships no glossary).
  import { onMount } from 'svelte';
  import { gloss, loadGlossary } from '../lib/glossary.svelte';
  import { t } from '../lib/i18n.svelte';

  interface Props {
    /** glossary key (pipeline/i18n/glossary.yaml) */
    k: string | null;
  }
  let { k }: Props = $props();
  const id = `gl-${++uid}`;
  onMount(loadGlossary);
  const g = $derived(k ? gloss(k) : null);
  const open = $derived(openId === id);
  let root = $state<HTMLSpanElement>();
  /** open toward the left when the ⓘ sits in the right half of the screen */
  let flip = $state(false);
  function outside(e: PointerEvent) {
    if (open && root && !root.contains(e.target as Node)) openId = null;
  }
</script>

<svelte:window onpointerdown={outside} onkeydown={(e) => open && e.key === 'Escape' && (openId = null)} />

{#if g}
  <span class="term" bind:this={root}>
    <button type="button" class="i" aria-expanded={open} aria-controls={id} aria-label="{t('gl.more')}: {g.term}"
      onclick={(e) => { e.stopPropagation(); flip = (root?.getBoundingClientRect().left ?? 0) > window.innerWidth / 2; openId = open ? null : id; }}>i</button>
    {#if open}
      <span class="pop" class:flip id={id} role="note"><strong>{g.term}</strong> {g.text}</span>
    {/if}
  </span>
{/if}

<style>
  .term { position: relative; display: inline-block; vertical-align: baseline; margin-left: 3px; font-family: var(--font-sans); }
  .i {
    width: 14px; height: 14px; padding: 0; border: 1px solid var(--ink); border-radius: 50%; background: var(--panel); color: var(--text);
    font: italic 700 9px/12px Georgia, 'Times New Roman', serif; cursor: pointer; text-align: center; vertical-align: 1px;
  }
  .i[aria-expanded='true'] { background: var(--ink); color: var(--ink-text); }
  .pop {
    position: absolute; z-index: 80; top: calc(100% + 4px); left: -8px; width: min(280px, 80vw); background: var(--panel); color: var(--text);
    border: 1px solid var(--ink); border-top: 3px solid var(--ink); padding: 7px 9px; font-size: 0.78rem; font-weight: 400; line-height: 1.4;
    text-transform: none; letter-spacing: 0; white-space: normal; text-align: left; font-style: normal;
  }
  .pop.flip { left: auto; right: -8px; }
  .pop strong { display: block; margin-bottom: 2px; }
</style>
