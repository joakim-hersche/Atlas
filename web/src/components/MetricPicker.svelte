<script lang="ts">
  // Metric picker: headline metrics grouped by theme; typing searches every metric (accent- and
  // case-insensitive, German labels and ids too). Metrics that do not exist at the current level
  // (not aggregatable, or not published there) are listed but disabled, with the reason.
  import { levelName, mdesc, ml, t, themeName, levelWord, themeWords } from '../lib/i18n.svelte';
  import { availableAt, type MetricMeta } from '../lib/data';
  import { fmtPeriod, unitOf } from '../lib/classify';
  import { metricKey, rankMetrics, suggestMetrics } from '../lib/metricsearch';
  import { app } from '../lib/state.svelte';

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

  const usable = $derived(metrics.filter((m) => !m.hidden && m.levels.some((l) => MAP_LEVELS.includes(l))));
  const nAvail = $derived(usable.filter(ok).length);
  const current = $derived(metrics.find((m) => m.id === value));
  // U5: word starts only, the label in the UI language ranked first; D37 party names (keywords) searchable too
  // F13: theme names in every language are search words too ("Lärm" or "Umwelt" in the English UI)
  const keys = $derived(usable.map((m) => metricKey(m, themeWords(m.theme))));
  const SEARCH = '\u0000search';
  const ranked = $derived(q.trim() ? rankMetrics(keys, q, { lang: app.lang, ok }) : []);
  const sugg = $derived(q.trim() && !ranked.length ? suggestMetrics(keys, q, { lang: app.lang, ok }) : null);

  const list = $derived.by(() => {
    // a search is one list in rank order (Enter takes the first); the theme is named on each row
    if (q.trim()) return ranked.length ? [[SEARCH, ranked] as [string, MetricMeta[]]] : [];
    const items = usable.filter((m) => m.headline !== null && (ok(m) || m.levels.includes('gemeinde'))).sort((a, b) => a.headline! - b.headline!);
    // former parties (until YYYY) form their own group at the end
    const groups = new Map<string, MetricMeta[]>();
    for (const m of items) {
      const g = m.until ? `${m.theme}|former` : m.theme;
      groups.set(g, [...(groups.get(g) ?? []), m]);
    }
    return [...groups.entries()].sort((a, b) => Number(a[0].endsWith('|former')) - Number(b[0].endsWith('|former')));
  });
  const flat = $derived(list.flatMap(([, ms]) => ms).filter(ok));

  // U12: on desktop the list is a popover over the map (fixed position), not clipped by the scrolling panel
  let btnEl = $state<HTMLButtonElement>();
  let popStyle = $state('');
  function place() {
    if (!btnEl || !window.matchMedia('(min-width: 900px)').matches) {
      popStyle = '';
      return;
    }
    const r = btnEl.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const w = Math.min(Math.max(r.width, 400), vw - 16);
    const left = Math.max(8, Math.min(r.left, vw - w - 8));
    const below = vh - r.bottom - 12;
    const above = r.top - 12;
    if (below < 360 && above > below) popStyle = `position:fixed;left:${left}px;width:${w}px;bottom:${vh - r.top - 1}px;top:auto;max-height:${Math.min(560, above)}px`;
    else popStyle = `position:fixed;left:${left}px;width:${w}px;top:${r.bottom - 1}px;max-height:${Math.min(560, below)}px`;
  }
  function onScroll(e: Event) {
    if (open && !(e.target instanceof Node && root.contains(e.target))) place();
  }
  function toggle() {
    open = !open;
    if (open) {
      place();
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

<svelte:window onpointerdown={outside} onresize={() => open && place()} onscrollcapture={onScroll} />

<div class="picker" bind:this={root}>
  <button type="button" class="btn" bind:this={btnEl} aria-haspopup="listbox" aria-expanded={open} onclick={toggle}>
    {#if tag}<span class="tag">{tag}</span>{/if}
    <span class="lbl">
      <span class="theme caps">{current ? themeName(current.theme) : none ? t('rc.off') : ''}</span>
      <span class="name">{current ? ml(current) : value || none || ''}</span>
    </span>
    <svg class="chev" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4" /></svg>
  </button>
  {#if open}
    <div class="pop" role="dialog" aria-label={t('mp.choose')} style={popStyle}>
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
        {#if !list.length && sugg}
          <p class="empty">{sugg.kind === 'partial' ? t('ux.partial') : sugg.items.length ? t('ux.suggest', { q }) : t('mp.none', { q })}</p>
          {#each sugg.items.filter(ok) as m}
            <button type="button" role="option" class="opt" aria-selected={m.id === value} onclick={() => pick(m.id)}>
              <span class="ol">{ml(m)}</span>
              <span class="om">{themeName(m.theme)} · {unitOf(m) || '–'} · {fmtPeriod(m.latest)}</span>
            </button>
          {/each}
        {/if}
        {#each list as [theme, ms]}
          {#if theme !== SEARCH}
            <div class="grp caps">{theme.endsWith('|former') ? `${themeName(theme.slice(0, -7))} · ${t('mp.former')}` : themeName(theme)}</div>
            {#if theme === 'Politics'}<p class="hint pol">{t('lg.ncOnly')}</p>{/if}
          {/if}
          {#each ms as m}
            {@const k = flat.indexOf(m)}
            {#if ok(m)}
              <button type="button" role="option" class="opt" class:active={k === active} aria-selected={m.id === value}
                title={mdesc(m) ?? undefined} onclick={() => pick(m.id)} onpointerenter={() => (active = k)}>
                <span class="ol">{ml(m)}</span>
                <span class="om">{theme === SEARCH ? `${themeName(m.theme)} · ` : ''}{unitOf(m) || '–'} · {fmtPeriod(m.latest)}{m.coverage.startsWith('partial:') ? ` · ${t('mp.partial')}` : ''}</span>
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
    flex: none; width: 20px; height: 20px; display: grid; place-items: center; font-size: var(--fs-meta); font-weight: 700;
    background: var(--ink); color: var(--ink-text);
  }
  .lbl { display: flex; flex-direction: column; justify-content: center; gap: 2px; min-width: 0; flex: 1; line-height: 1.2; }
  .theme { font-size: var(--fs-cap); }
  .name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .chev { flex: none; color: var(--text); }

  /* popover: exactly as wide as the trigger, so it never spills out of (or is clipped by) the panel */
  .pop {
    position: absolute; z-index: 60; top: calc(100% - 1px); left: 0; right: 0;
    background: var(--panel); border: 1px solid var(--ink); border-top: 3px solid var(--ink);
    display: flex; flex-direction: column; max-height: min(480px, 70vh);
  }
  .search { display: flex; align-items: center; gap: 4px; padding: 8px; border-bottom: 1px solid var(--rule); }
  .search input {
    flex: 1; min-width: 0; height: 36px; padding: 0 10px; border: 1px solid var(--ink); background: var(--panel);
    font-size: var(--fs-input); line-height: 36px; outline: none;
  }
  .search input:focus-visible { box-shadow: inset 0 0 0 1px var(--ink); outline: none; }
  .search input::-webkit-search-cancel-button { display: none; }
  .x { flex: none; display: grid; place-items: center; width: 36px; height: 36px; border: 0; background: none; cursor: pointer; color: var(--text); }
  .list { overflow-y: auto; overflow-x: hidden; padding: 0 0 8px; overscroll-behavior: contain; }
  .grp {
    position: sticky; top: 0; z-index: 1; display: flex; align-items: center; min-height: 32px; padding: 10px 12px 4px;
    font-size: var(--fs-cap); background: var(--panel); border-bottom: 1px solid var(--rule);
  }
  /* each row: name, then unit · period on a second line; vertically centred */
  .opt {
    display: flex; flex-direction: column; justify-content: center; gap: 2px; width: 100%; min-height: 44px; padding: 6px 12px;
    border: 0; border-bottom: 1px solid var(--border); background: none; text-align: left; cursor: pointer; color: var(--text);
  }
  .opt.active { background: var(--panel-2); }
  .opt.off { cursor: default; color: var(--faint); }
  .opt.off .om { font-style: italic; }
  .opt[aria-selected='true'] { box-shadow: inset 3px 0 0 var(--ink); }
  .opt[aria-selected='true'] .ol { color: var(--text); font-weight: 700; }
  .ol { min-width: 0; line-height: 1.25; overflow-wrap: anywhere; }
  .om { min-width: 0; color: var(--muted); font-size: var(--fs-meta); line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .empty { padding: 12px; color: var(--muted); margin: 0; }
  .hint { padding: 8px 12px 0; margin: 0; }
  .hint.pol { padding: 4px 12px; font-size: var(--fs-meta); color: var(--muted); border-bottom: 1px solid var(--border); }
  @media (min-width: 900px) {
    .search input { font-size: var(--fs-small); height: 32px; line-height: 32px; }
    .x { width: 32px; height: 32px; }
  }
  @media (max-width: 899px) {
    /* B4 (R4): on a phone the list is a modal sheet over the page; a scrim shows that it covers the tabs */
    .pop { position: fixed; z-index: 75; top: calc(env(safe-area-inset-top) + 52px); left: 8px; right: 8px; max-height: 72vh; box-shadow: 0 0 0 100vmax rgba(0, 0, 0, 0.32); }
  }
</style>
