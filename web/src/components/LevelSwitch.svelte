<script lang="ts">
  // Spatial level switch (brief 4.3): the three main levels as a segmented control, the other official
  // levels under "More". Municipality types have no geometry: listed, disabled.
  import { LEVELS } from '../lib/data';
  import { levelName, t } from '../lib/i18n.svelte';

  interface Props {
    value: string;
    onchange: (level: string) => void;
    /** levels where the current metric exists; others are dimmed (still clickable: the app asks first) */
    avail?: string[];
    /** tooltip for a dimmed level */
    naTitle?: (level: string) => string;
  }
  let { value, onchange, avail, naTitle }: Props = $props();
  const na = (id: string) => !!avail && !avail.includes(id);

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
      <button type="button" role="radio" aria-checked={value === id} class:na={na(id)} title={na(id) && naTitle ? naTitle(id) : undefined}
        onclick={() => pick(id)}>{levelName(id)}</button>
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
        <button type="button" role="menuitemradio" aria-checked={value === l.id} class:na={na(l.id)}
          title={na(l.id) && naTitle ? naTitle(l.id) : undefined} onclick={() => pick(l.id)}>{levelName(l.id)}</button>
      {/each}
      <button type="button" role="menuitemradio" aria-checked="false" disabled>{t('level.types')}</button>
      {#if avail && [...MAIN, ...more.map((l) => l.id)].some(na)}<p class="nanote">{t('ux.struck')}</p>{/if}
    </div>
  {/if}
</div>

<style>
  .lvl { position: relative; display: inline-flex; max-width: 100%; }
  /* narrow map panes (desktop 900–1100 px): the control scrolls sideways instead of covering the zoom buttons */
  .seg { max-width: 100%; overflow-x: auto; scrollbar-width: none; }
  .seg::-webkit-scrollbar { display: none; }
  .seg button { flex: none; }
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
  /* the shaded metric does not exist at this level */
  .seg button.na[aria-checked='false'], .menu button.na { color: var(--faint); text-decoration: line-through; text-decoration-thickness: 1px; }
  .menu button:disabled { color: var(--faint); cursor: default; font-style: italic; }
  .nanote { margin: 0; padding: var(--sp-2) var(--sp-3); border-top: var(--rule-row); font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text-3); max-width: 260px; }
  @media (max-width: 899px) {
    .seg button { padding: 6px 8px; font-size: 0.76rem; }
    .ml { max-width: 6.5em; }
  }
</style>
