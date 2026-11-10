<script lang="ts">
  // Spatial level switch (brief 4.3): the three main levels as a segmented control, the other official
  // levels under "More". Municipality types have no geometry: listed, disabled.
  import { LEVELS } from '../lib/data';
  import { levelName, t } from '../lib/i18n.svelte';

  interface Props {
    value: string;
    onchange: (level: string) => void;
  }
  let { value, onchange }: Props = $props();

  const MAIN = ['gemeinde', 'bezirk', 'kanton'];
  const more = LEVELS.filter((l) => l.geometry && !MAIN.includes(l.id));
  const inMore = $derived(!MAIN.includes(value));
  let open = $state(false);
  let root: HTMLDivElement;
  let menu = $state<HTMLDivElement>();

  function pick(id: string) {
    open = false;
    if (id !== value) onchange(id);
  }
  function toggle() {
    open = !open;
    if (open) queueMicrotask(() => (menu?.querySelector('[aria-checked="true"], button:not(:disabled)') as HTMLElement | null)?.focus());
  }
  function outside(e: PointerEvent) {
    if (open && !root.contains(e.target as Node)) open = false;
  }
  function key(e: KeyboardEvent) {
    if (!open) return;
    if (e.key === 'Escape') {
      open = false;
      (root.querySelector('.more') as HTMLElement | null)?.focus();
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      const items = [...(menu?.querySelectorAll('button:not(:disabled)') ?? [])] as HTMLElement[];
      const k = items.indexOf(document.activeElement as HTMLElement);
      items[(k + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
      e.preventDefault();
    }
  }
</script>

<svelte:window onpointerdown={outside} onkeydown={key} />

<div class="lvl" bind:this={root}>
  <div class="seg" role="radiogroup" aria-label={t('level.label')}>
    {#each MAIN as id}
      <button type="button" role="radio" aria-checked={value === id} onclick={() => pick(id)}>{levelName(id)}</button>
    {/each}
    <button type="button" class="more" aria-haspopup="menu" aria-expanded={open} aria-pressed={inMore} onclick={toggle}
      title={inMore ? levelName(value) : t('level.more')}>
      <span class="ml">{inMore ? levelName(value) : t('level.more')}</span>
      <svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>
    </button>
  </div>
  {#if open}
    <div class="menu" role="menu" bind:this={menu}>
      {#each more as l}
        <button type="button" role="menuitemradio" aria-checked={value === l.id} onclick={() => pick(l.id)}>{levelName(l.id)}</button>
      {/each}
      <button type="button" role="menuitemradio" aria-checked="false" disabled>{t('level.types')}</button>
    </div>
  {/if}
</div>

<style>
  .lvl { position: relative; display: inline-flex; max-width: 100%; }
  .seg { max-width: 100%; }
  .seg button { padding: 5px 10px; font-size: 0.8rem; font-weight: 600; }
  .more { display: inline-flex; align-items: center; gap: 4px; min-width: 0; }
  .ml { max-width: 9.5em; overflow: hidden; text-overflow: ellipsis; }
  .more svg { flex: none; }
  .menu {
    position: absolute; z-index: 30; top: calc(100% + 3px); right: 0; min-width: 210px; background: var(--panel);
    border: 1px solid var(--ink); border-top: 3px solid var(--ink); padding: 3px 0;
  }
  .menu button {
    display: block; width: 100%; text-align: left; padding: 7px 12px; border: 0; background: none; cursor: pointer; font-size: 0.84rem;
  }
  .menu button:hover:not(:disabled), .menu button:focus-visible { background: var(--panel-2); }
  .menu button[aria-checked='true'] { font-weight: 700; box-shadow: inset 3px 0 0 var(--ink); }
  .menu button:disabled { color: var(--faint); cursor: default; font-style: italic; }
  @media (max-width: 899px) {
    .seg button { padding: 6px 8px; font-size: 0.76rem; }
    .ml { max-width: 6.5em; }
  }
</style>
