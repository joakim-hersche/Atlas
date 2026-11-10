<script lang="ts">
  // Metric picker: headline metrics grouped by theme; typing searches every metric (accent- and
  // case-insensitive, German labels and ids too). Metrics that do not exist at the current level
  // (not aggregatable, or not published there) are listed but disabled, with the reason.
  import { levelName, ml, t, themeName, levelWord } from '../lib/i18n.svelte';
  import { availableAt, type MetricMeta } from '../lib/data';
  import { fmtPeriod, unitOf } from '../lib/classify';

  interface Props {
    metrics: MetricMeta[];
    value: string;
    level?: string;
    tag?: string;
    /** label of the empty choice (e.g. 'None' for size); omitted = no empty choice */
    none?: string;
    onpick: (id: string) => void;
  }
  let { metrics, value, level = 'gemeinde', tag, none, onpick }: Props = $props();
  const MAP_LEVELS = ['gemeinde', 'bezirk', 'kanton', 'grossregion', 'sprachgebiet', 'agglomeration', 'arbeitsmarktgebiet', 'stadt_land'];
  const ok = (m: MetricMeta) => availableAt(m, level);
  function why(m: MetricMeta) {
    if (m.aggregation === 'not_aggregatable') return t('mp.notAgg');
    const at = m.levels.filter((l) => MAP_LEVELS.includes(l));
    return at.length === 1 ? t('mp.only', { level: levelWord(at[0]) }) : t('mp.notFor', { level: levelWord(level) });
  }

  let open = $state(false);
  let q = $state('');
  let active = $state(0);
  let root: HTMLDivElement;
  let input = $state<HTMLInputElement>();

  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const usable = $derived(metrics.filter((m) => !m.hidden && m.levels.some((l) => MAP_LEVELS.includes(l))));
  const nAvail = $derived(usable.filter(ok).length);
  const current = $derived(metrics.find((m) => m.id === value));
  // D37: full party names in DE/FR/IT/EN (keywords) and the French label are searchable too
  const keyed = $derived(usable.map((m) => ({ m, key: norm(`${m.label_en} ${m.label_de} ${m.label_fr ?? ''} ${m.keywords ?? ''} ${m.id} ${m.theme}`) })));

  const list = $derived.by(() => {
    const words = norm(q).split(/\s+/).filter(Boolean);
    let items: MetricMeta[];
    if (!words.length) {
      items = usable.filter((m) => m.headline !== null && (ok(m) || m.levels.includes('gemeinde'))).sort((a, b) => a.headline! - b.headline!);
    } else {
      items = keyed
        .filter((k) => words.every((w) => k.key.includes(w)))
        .map((k) => k.m)
        .sort((a, b) => Number(ok(b)) - Number(ok(a)) || (a.headline ?? 1e9) - (b.headline ?? 1e9) || ml(a).localeCompare(ml(b)))
        .slice(0, 120);
    }
    // former parties (until YYYY) form their own group at the end
    const groups = new Map<string, MetricMeta[]>();
    for (const m of items) {
      const g = m.until ? `${m.theme}|former` : m.theme;
      groups.set(g, [...(groups.get(g) ?? []), m]);
    }
    return [...groups.entries()].sort((a, b) => Number(a[0].endsWith('|former')) - Number(b[0].endsWith('|former')));
  });
  const flat = $derived(list.flatMap(([, ms]) => ms).filter(ok));

  function toggle() {
    open = !open;
    if (open) {
      q = '';
      active = Math.max(0, flat.findIndex((m) => m.id === value));
      // reopen where the current choice is, instead of at the top of the list
      requestAnimationFrame(() => {
        root.querySelector('.opt[aria-selected="true"]')?.scrollIntoView({ block: 'center' });
        input?.focus({ preventScroll: true });
      });
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
    else if (e.key === 'Enter' && none && !flat.length) pick('');
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
      <span class="theme caps">{current ? themeName(current.theme) : none ? t('rc.off') : ''}</span>
      <span class="name">{current ? ml(current) : value || none || ''}</span>
    </span>
    <svg class="chev" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4" /></svg>
  </button>
  {#if open}
    <div class="pop" role="dialog" aria-label={t('mp.choose')}>
      <div class="search">
        <input bind:this={input} bind:value={q} type="search" placeholder={t('mp.search', { n: nAvail })} aria-label={t('mp.searchL')}
          oninput={() => (active = 0)} onkeydown={key} />
        <button type="button" class="x" aria-label={t('common.close')} onclick={() => (open = false)}>
          <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.5" /></svg>
        </button>
      </div>
      <div class="list" role="listbox" aria-label={t('mp.choose')}>
        {#if none && !q}
          <button type="button" role="option" class="opt" aria-selected={!value} onclick={() => pick('')}>
            <span class="ol">{none}</span>
          </button>
        {/if}
        {#if !list.length}
          <p class="empty">{t('mp.none', { q })}</p>
        {/if}
        {#each list as [theme, ms]}
          <div class="grp caps">{theme.endsWith('|former') ? `${themeName(theme.slice(0, -7))} · ${t('mp.former')}` : themeName(theme)}</div>
          {#if theme === 'Politics'}<p class="hint pol">{t('lg.ncOnly')}</p>{/if}
          {#each ms as m}
            {@const k = flat.indexOf(m)}
            {#if ok(m)}
              <button type="button" role="option" class="opt" class:active={k === active} aria-selected={m.id === value}
                title={m.description ?? undefined} onclick={() => pick(m.id)} onpointerenter={() => (active = k)}>
                <span class="ol">{ml(m)}</span>
                <span class="om">{unitOf(m) || '–'} · {fmtPeriod(m.latest)}{m.coverage.startsWith('partial:') ? ` · ${t('mp.partial')}` : ''}</span>
              </button>
            {:else}
              <div role="option" class="opt off" aria-disabled="true" aria-selected="false" title={t('mp.notFor', { level: levelWord(level) })}>
                <span class="ol">{ml(m)}</span>
                <span class="om">{why(m)}</span>
              </div>
            {/if}
          {/each}
        {/each}
        {#if !q}<p class="hint foot">{t('mp.headline', { n: nAvail })}</p>{/if}
        {#if nAvail < usable.length}
          <p class="hint foot">{t('mp.unavail', { n: usable.length - nAvail, level: levelWord(level) })}</p>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .picker { position: relative; min-width: 0; }
  .btn {
    display: flex; align-items: center; gap: 10px; width: 100%; min-height: 48px; padding: 6px 12px; text-align: left; cursor: pointer;
    background: var(--panel); border: 1px solid var(--ink);
  }
  .btn:hover, .btn[aria-expanded='true'] { box-shadow: inset 0 0 0 1px var(--ink); }
  .tag {
    flex: none; width: 20px; height: 20px; display: grid; place-items: center; font-size: 0.72rem; font-weight: 700;
    background: var(--accent); color: var(--accent-text);
  }
  .lbl { display: flex; flex-direction: column; justify-content: center; gap: 2px; min-width: 0; flex: 1; line-height: 1.2; }
  .theme { font-size: 0.62rem; }
  .name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .chev { flex: none; color: var(--text); }

  /* popover: exactly as wide as the trigger, so it never spills out of (or is clipped by) the panel */
  .pop {
    position: absolute; z-index: 30; top: calc(100% - 1px); left: 0; right: 0;
    background: var(--panel); border: 1px solid var(--ink); border-top: 3px solid var(--ink);
    display: flex; flex-direction: column; max-height: min(480px, 70vh);
  }
  .search { display: flex; align-items: center; gap: 4px; padding: 8px; border-bottom: 1px solid var(--rule); }
  .search input {
    flex: 1; min-width: 0; height: 36px; padding: 0 10px; border: 1px solid var(--ink); background: var(--panel);
    font-size: 16px; line-height: 36px; outline: none;
  }
  .search input:focus-visible { box-shadow: inset 0 0 0 1px var(--ink); outline: none; }
  .search input::-webkit-search-cancel-button { display: none; }
  .x { flex: none; display: grid; place-items: center; width: 36px; height: 36px; border: 0; background: none; cursor: pointer; color: var(--text); }
  .list { overflow-y: auto; overflow-x: hidden; padding: 0 0 8px; overscroll-behavior: contain; }
  .grp {
    position: sticky; top: 0; z-index: 1; display: flex; align-items: center; min-height: 32px; padding: 10px 12px 4px;
    font-size: 0.66rem; background: var(--panel); border-bottom: 1px solid var(--rule);
  }
  /* each row: name, then unit · period on a second line; vertically centred */
  .opt {
    display: flex; flex-direction: column; justify-content: center; gap: 2px; width: 100%; min-height: 44px; padding: 6px 12px;
    border: 0; border-bottom: 1px solid var(--border); background: none; text-align: left; cursor: pointer; color: var(--text);
  }
  .opt.active { background: var(--panel-2); }
  .opt.off { cursor: default; color: var(--faint); }
  .opt.off .om { font-style: italic; }
  .opt[aria-selected='true'] { box-shadow: inset 3px 0 0 var(--accent); }
  .opt[aria-selected='true'] .ol { color: var(--accent); font-weight: 600; }
  .ol { min-width: 0; line-height: 1.25; overflow-wrap: anywhere; }
  .om { min-width: 0; color: var(--muted); font-size: 0.72rem; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .empty { padding: 12px; color: var(--muted); margin: 0; }
  .hint { padding: 8px 12px 0; margin: 0; }
  .hint.pol { padding: 4px 12px; font-size: 0.72rem; color: var(--muted); border-bottom: 1px solid var(--border); }
  @media (min-width: 900px) {
    .search input { font-size: 0.875rem; height: 32px; line-height: 32px; }
    .x { width: 32px; height: 32px; }
  }
  @media (max-width: 899px) {
    .pop { position: fixed; z-index: 75; top: calc(env(safe-area-inset-top) + 52px); left: 8px; right: 8px; max-height: 72vh; }
  }
</style>
