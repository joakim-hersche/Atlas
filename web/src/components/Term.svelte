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
      onclick={(e) => { e.stopPropagation(); place(); openId = open ? null : id; }}>
      <!-- D8: one info icon, outlined, 14 px -->
      <svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6.4" fill="none" stroke="currentColor" stroke-width="1.1" /><rect x="6.35" y="6" width="1.3" height="4.6" fill="currentColor" /><rect x="6.35" y="3.4" width="1.3" height="1.4" fill="currentColor" /></svg>
    </button>
    {#if open}
      <span class="pop" id={id} role="note" style="top:{pos.top}px; left:{pos.left}px"><strong>{g.term}</strong> {g.text}</span>
    {/if}
  </span>
{/if}

<style>
  .term { position: relative; display: inline-block; vertical-align: baseline; margin-left: var(--sp-1); font-family: var(--font-sans); }
  .i {
    display: inline-grid; place-items: center; width: 14px; height: 14px; padding: 0; border: 0; background: none; color: var(--text);
    cursor: pointer; vertical-align: -2px; border-radius: 50%;
  }
  .i svg { display: block; }
  /* touch screens: a 40 x 40 target around the 14 px icon, without moving the text around it */
  @media (pointer: coarse), (max-width: 899px) {
    .i { width: 40px; height: 40px; margin: -13px -13px -13px -13px; }
  }
  .i[aria-expanded='true'] svg circle { fill: var(--ink); }
  .i[aria-expanded='true'] svg rect { fill: var(--ink-text); }
  .pop {
    position: fixed; z-index: 90; width: min(280px, calc(100vw - 16px)); background: var(--panel); color: var(--text);
    border: 1px solid var(--ink); border-top: 3px solid var(--ink); padding: var(--sp-2) var(--sp-3); font-size: var(--fs-small); font-weight: 400; line-height: var(--lh-small);
    text-transform: none; letter-spacing: 0; white-space: normal; text-align: left; font-style: normal;
  }
  .pop strong { display: block; margin-bottom: 2px; }
</style>
