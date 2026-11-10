<script lang="ts">
  // Metric picker: headline metrics grouped by theme; typing searches every metric available
  // at municipality level (accent- and case-insensitive, German labels and ids too).
  import type { MetricMeta } from '../lib/data';

  interface Props {
    metrics: MetricMeta[];
    value: string;
    tag?: string;
    onpick: (id: string) => void;
  }
  let { metrics, value, tag, onpick }: Props = $props();

  let open = $state(false);
  let q = $state('');
  let active = $state(0);
  let root: HTMLDivElement;
  let input = $state<HTMLInputElement>();

  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const usable = $derived(metrics.filter((m) => !m.hidden && m.levels.includes('gemeinde')));
  const current = $derived(metrics.find((m) => m.id === value));
  const keyed = $derived(usable.map((m) => ({ m, key: norm(`${m.label_en} ${m.label_de} ${m.id} ${m.theme}`) })));

  const list = $derived.by(() => {
    const words = norm(q).split(/\s+/).filter(Boolean);
    let items: MetricMeta[];
    if (!words.length) {
      items = usable.filter((m) => m.headline !== null).sort((a, b) => a.headline! - b.headline!);
    } else {
      items = keyed
        .filter((k) => words.every((w) => k.key.includes(w)))
        .map((k) => k.m)
        .sort((a, b) => (a.headline ?? 1e9) - (b.headline ?? 1e9) || a.label_en.localeCompare(b.label_en))
        .slice(0, 120);
    }
    const groups = new Map<string, MetricMeta[]>();
    for (const m of items) groups.set(m.theme, [...(groups.get(m.theme) ?? []), m]);
    return [...groups.entries()];
  });
  const flat = $derived(list.flatMap(([, ms]) => ms));

  function toggle() {
    open = !open;
    if (open) {
      q = '';
      active = Math.max(0, flat.findIndex((m) => m.id === value));
      queueMicrotask(() => input?.focus());
    }
  }
  function pick(id: string) {
    open = false;
    onpick(id);
  }
  function key(e: KeyboardEvent) {
    if (e.key === 'Escape') open = false;
    else if (e.key === 'ArrowDown') { active = Math.min(flat.length - 1, active + 1); e.preventDefault(); scrollActive(); }
    else if (e.key === 'ArrowUp') { active = Math.max(0, active - 1); e.preventDefault(); scrollActive(); }
    else if (e.key === 'Enter' && flat[active]) pick(flat[active].id);
  }
  function scrollActive() {
    queueMicrotask(() => root.querySelector('.opt.active')?.scrollIntoView({ block: 'nearest' }));
  }
  function outside(e: PointerEvent) {
    if (open && !root.contains(e.target as Node)) open = false;
  }
</script>

<svelte:window onpointerdown={outside} />

<div class="picker" bind:this={root}>
  <button type="button" class="btn" aria-haspopup="listbox" aria-expanded={open} onclick={toggle}>
    {#if tag}<span class="tag">{tag}</span>{/if}
    <span class="lbl">
      <span class="theme caps">{current?.theme ?? ''}</span>
      <span class="name">{current?.label_en ?? value}</span>
    </span>
    <svg class="chev" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4" /></svg>
  </button>
  {#if open}
    <div class="pop" role="dialog" aria-label="Choose a metric">
      <div class="search">
        <input bind:this={input} bind:value={q} type="search" placeholder="Search {usable.length} metrics" aria-label="Search metrics"
          oninput={() => (active = 0)} onkeydown={key} />
        <button type="button" class="x" aria-label="Close" onclick={() => (open = false)}>×</button>
      </div>
      <div class="list" role="listbox" aria-label="Metrics">
        {#if !flat.length}
          <p class="empty">No metric matches “{q}”.</p>
        {/if}
        {#each list as [theme, ms]}
          <div class="grp caps">{theme}</div>
          {#each ms as m}
            {@const k = flat.indexOf(m)}
            <button type="button" role="option" class="opt" class:active={k === active} aria-selected={m.id === value}
              onclick={() => pick(m.id)} onpointerenter={() => (active = k)}>
              <span class="ol">{m.label_en}</span>
              <span class="om">{m.unit || '–'} · {m.latest}{m.coverage.startsWith('partial:') ? ' · partial' : ''}</span>
            </button>
          {/each}
        {/each}
        {#if !q}<p class="hint foot">Headline metrics shown. Type to search all {usable.length}.</p>{/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .picker { position: relative; min-width: 0; }
  .btn {
    display: flex; align-items: center; gap: 8px; width: 100%; padding: 5px 8px; text-align: left; cursor: pointer;
    background: var(--panel); border: 1px solid var(--border-strong); border-radius: var(--radius);
  }
  .btn:hover { border-color: var(--accent); }
  .tag {
    flex: none; font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500; width: 18px; height: 18px; display: grid;
    place-items: center; border-radius: 2px; background: var(--text); color: var(--panel);
  }
  .lbl { display: flex; flex-direction: column; min-width: 0; flex: 1; line-height: 1.2; }
  .theme { font-size: 0.62rem; }
  .name { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .chev { flex: none; color: var(--muted); }
  .pop {
    position: absolute; z-index: 30; top: calc(100% + 4px); left: 0; width: max(100%, 360px); max-width: calc(100vw - 16px);
    background: var(--panel); border: 1px solid var(--border-strong); border-radius: var(--radius); box-shadow: var(--shadow);
    display: flex; flex-direction: column; max-height: min(460px, 70vh);
  }
  .search { display: flex; gap: 4px; padding: 6px; border-bottom: 1px solid var(--border); }
  .search input {
    flex: 1; min-width: 0; padding: 6px 8px; border: 1px solid var(--border-strong); border-radius: var(--radius);
    background: var(--panel-2); font-size: 16px;
  }
  .x { border: 0; background: none; width: 32px; font-size: 1.2rem; cursor: pointer; color: var(--muted); }
  .list { overflow-y: auto; padding: 2px 0 6px; overscroll-behavior: contain; }
  .grp { padding: 10px 10px 3px; font-size: 0.64rem; position: sticky; top: 0; background: var(--panel); }
  .opt {
    display: flex; justify-content: space-between; gap: 10px; width: 100%; padding: 5px 10px; border: 0; background: none;
    text-align: left; cursor: pointer; align-items: baseline;
  }
  .opt.active { background: var(--accent-soft); }
  .opt[aria-selected='true'] .ol { color: var(--accent); font-weight: 500; }
  .opt[aria-selected='true'] { box-shadow: inset 2px 0 0 var(--accent); }
  .ol { min-width: 0; }
  .om { flex: none; color: var(--faint); font-size: 0.72rem; font-family: var(--font-mono); max-width: 45%; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .empty { padding: 10px; color: var(--muted); margin: 0; }
  .hint { padding: 8px 10px 0; margin: 0; }
  @media (max-width: 899px) {
    .pop { position: fixed; top: max(8px, env(safe-area-inset-top)); left: 8px; right: 8px; width: auto; max-width: none; max-height: 72vh; }
  }
</style>
