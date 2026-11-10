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
  /** fixed position of the popover (escapes scrolling panels that would clip it) */
  let pos = $state({ top: 0, left: 0 });
  function place() {
    const r = root!.getBoundingClientRect();
    const w = Math.min(280, window.innerWidth - 16);
    pos = { top: Math.min(r.bottom + 4, window.innerHeight - 140), left: Math.max(8, Math.min(r.left - 8, window.innerWidth - w - 8)) };
  }
  function outside(e: PointerEvent) {
    if (open && root && !root.contains(e.target as Node)) openId = null;
  }
</script>

<svelte:window onscroll={() => (openId = null)} onresize={() => (openId = null)} onpointerdown={outside} onkeydown={(e) => open && e.key === 'Escape' && (openId = null)} />

{#if g}
  <span class="term" bind:this={root}>
    <button type="button" class="i" aria-expanded={open} aria-controls={id} aria-label="{t('gl.more')}: {g.term}"
      onclick={(e) => { e.stopPropagation(); place(); openId = open ? null : id; }}>i</button>
    {#if open}
      <span class="pop" id={id} role="note" style="top:{pos.top}px; left:{pos.left}px"><strong>{g.term}</strong> {g.text}</span>
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
    position: fixed; z-index: 90; width: min(280px, calc(100vw - 16px)); background: var(--panel); color: var(--text);
    border: 1px solid var(--ink); border-top: 3px solid var(--ink); padding: 7px 9px; font-size: 0.78rem; font-weight: 400; line-height: 1.4;
    text-transform: none; letter-spacing: 0; white-space: normal; text-align: left; font-style: normal;
  }
  .pop strong { display: block; margin-bottom: 2px; }
</style>
