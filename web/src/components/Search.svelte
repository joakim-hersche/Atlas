<script lang="ts" module>
  import { addStrings } from '../lib/i18n.svelte';
  addStrings(
    {
      'search.placeholder': 'Place, canton or postal code',
      'search.open': 'Search places',
      'search.label': 'Search places',
      'search.none': 'Nothing found for “{q}”.',
      'search.loading': 'Loading the place index…',
      'search.also': 'also',
      'search.addresses': '{p}% of addresses',
      'search.hint': 'Names in any language, postal codes, BFS numbers',
      'search.error': 'The place index could not be loaded.',
    },
    {
      'search.placeholder': 'Ort, Kanton oder PLZ',
      'search.open': 'Orte suchen',
      'search.label': 'Orte suchen',
      'search.none': 'Nichts gefunden für «{q}».',
      'search.loading': 'Ortsverzeichnis wird geladen…',
      'search.also': 'auch',
      'search.addresses': '{p} % der Adressen',
      'search.hint': 'Namen in jeder Sprache, Postleitzahlen, BFS-Nummern',
      'search.error': 'Das Ortsverzeichnis konnte nicht geladen werden.',
    },
  );
  let uid = 0;
</script>

<script lang="ts">
  // Place search (brief 6.1): any municipality, district, canton, other level or postal code, accent-
  // and language-insensitive. The index (search.json) loads on first focus. Keyboard: arrows, Enter, Esc.
  import { fmtNumber } from '../lib/classify';
  import { peekLevel } from '../lib/data';
  import { levelName, t } from '../lib/i18n.svelte';
  import { loadSearch, norm, search, type SearchHit, type SearchIndex } from '../lib/places';
  import { vintageFind } from '../lib/vintage-strings.svelte';
  import '../lib/i18n-r3';

  interface Props {
    /** the hit is passed too (a former name selects the old unit on the older-boundaries map) */
    onpick: (ref: string, hit?: SearchHit) => void;
    /** 'header': on phones an icon that opens a full-width field; 'inline': always a field */
    variant?: 'header' | 'inline';
    /** phone layout of the header variant */
    collapsed?: boolean;
    placeholder?: string;
    /** references not offered (already chosen) */
    exclude?: string[];
    disabled?: boolean;
  }
  let { onpick, variant = 'inline', collapsed = false, placeholder, exclude = [], disabled = false }: Props = $props();

  const id = `srch-${++uid}`;
  let ix = $state.raw<SearchIndex | null>(null);
  let failed = $state(false);
  let pop = $state.raw<Map<string, number> | undefined>(undefined);
  let q = $state('');
  let open = $state(false);
  let expanded = $state(false); // phone header: field shown
  let active = $state(0);
  let input = $state<HTMLInputElement>();
  let root: HTMLDivElement;

  function ensure() {
    if (ix || failed) return;
    loadSearch().then((x) => (ix = x)).catch(() => (failed = true));
    // population ranks equal matches when the municipalities' values are already in memory
    peekLevel('gemeinde')?.then((ld) => {
      const v = ld.core.metrics.pop_total?.v;
      if (v) pop = new Map(ld.units.map((u, i) => [u, v[i] ?? 0]));
    });
  }
  // B5 (R1): on the older-boundaries map, the municipalities of that state are searched too (former villages
  // such as Obstalden), listed first; picking one selects it on that map (ref "vin:<BFS number>")
  const local = $derived(variant === 'header' && vintageFind.units?.length ? vintageFind.units : null);
  const localHits = $derived.by<SearchHit[]>(() => {
    const nq = norm(q);
    if (!local || !nq) return [];
    const out: SearchHit[] = [];
    for (const u of local) {
      const k = norm(u.name);
      if (k.startsWith(nq) || k.split(' ').some((w) => w.startsWith(nq))) out.push({ ref: `vin:${u.id}`, name: u.name, level: 'gemeinde', kanton: u.kanton, vintage: vintageFind.label ?? '' });
      if (out.length >= 5) break;
    }
    return out;
  });
  const hits = $derived<SearchHit[]>(ix && q.trim() ? [...localHits, ...search(ix, q, 12, pop).filter((h) => !exclude.includes(h.ref))] : localHits);
  $effect(() => {
    void hits;
    active = 0;
  });

  function pick(h: SearchHit | undefined) {
    if (!h) return;
    onpick(h.ref, h);
    q = '';
    open = false;
    expanded = false;
    input?.blur();
  }
  function close() {
    open = false;
    if (expanded) {
      expanded = false;
      q = '';
    }
  }
  function key(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      open = true;
      active = Math.min(hits.length - 1, active + 1);
      e.preventDefault();
      scrollActive();
    } else if (e.key === 'ArrowUp') {
      active = Math.max(0, active - 1);
      e.preventDefault();
      scrollActive();
    } else if (e.key === 'Enter') {
      pick(hits[active]);
      e.preventDefault();
    } else if (e.key === 'Escape') {
      if (q && !expanded) q = '';
      else close();
      e.preventDefault();
    }
  }
  function scrollActive() {
    queueMicrotask(() => root.querySelector('.hit.active')?.scrollIntoView({ block: 'nearest' }));
  }
  function expand() {
    expanded = true;
    ensure();
    queueMicrotask(() => input?.focus());
  }
  function outside(e: PointerEvent) {
    if ((open || expanded) && !root.contains(e.target as Node)) close();
  }
  /** U14: the type as a legible chip, the canton next to it */
  const typeOf = (h: SearchHit) => {
    if (h.vintage) return h.vintage;
    const lv = levelName(h.level, false);
    return lv.charAt(0).toUpperCase() + lv.slice(1);
  };
  const showField = $derived(variant === 'inline' || !collapsed || expanded);
</script>

<svelte:window onpointerdown={outside} />

<div class="search" class:header={variant === 'header'} class:phone={variant === 'header' && collapsed} class:expanded bind:this={root}>
  {#if !showField}
    <button type="button" class="icon" aria-label={t('search.open')} title={t('search.open')} onclick={expand}>
      <svg viewBox="0 0 20 20" width="19" height="19" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="2" /><path d="M12.6 12.6 17 17" stroke="currentColor" stroke-width="2.2" stroke-linecap="square" /></svg>
    </button>
  {:else}
    <div class="field">
      <svg class="mag" viewBox="0 0 20 20" width="15" height="15" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="2" /><path d="M12.6 12.6 17 17" stroke="currentColor" stroke-width="2.2" stroke-linecap="square" /></svg>
      <input bind:this={input} bind:value={q} type="search" {disabled} autocomplete="off" spellcheck="false"
        placeholder={placeholder ?? t('search.placeholder')} aria-label={t('search.label')}
        role="combobox" aria-expanded={open && !!q.trim()} aria-controls="{id}-list" aria-autocomplete="list"
        aria-activedescendant={open && hits[active] ? `${id}-${active}` : undefined}
        onfocus={() => { ensure(); open = true; }} oninput={() => (open = true)} onkeydown={key} />
      {#if expanded}
        <button type="button" class="x" aria-label={t('common.close')} onclick={close}>×</button>
      {/if}
    </div>
    {#if open && q.trim()}
      <div class="pop" id="{id}-list" role="listbox" aria-label={t('search.label')}>
        {#if failed}
          <p class="msg">{t('search.error')}</p>
        {:else if !ix && !localHits.length}
          <p class="msg">{t('search.loading')}</p>
        {:else if !hits.length}
          <p class="msg">{t('search.none', { q: q.trim() })}</p>
        {:else}
          {#each hits as h, k (h.ref + (h.plz?.code ?? '') + (h.bfs ? 'b' : ''))}
            <button type="button" role="option" id="{id}-{k}" class="hit" class:active={k === active} aria-selected={k === active}
              tabindex="-1" onpointerenter={() => (active = k)} onclick={() => pick(h)}>
              <span class="hn">
                {#if h.plz}<span class="code num">{h.plz.code}</span>{/if}
                {#if h.bfs}<span class="code num">BFS {h.ref}</span>{/if}
                <strong>{h.name}</strong>
                {#if h.via}<span class="via">{t('search.also')}: {h.via}</span>{/if}
                {#if h.former}<span class="via">{t('r3.formerly')}: {h.former.name}{h.former.until ? ` (${t('r3.until', { y: h.former.until.slice(0, 4) })})` : ''}</span>{/if}
                {#if h.plz && h.plz.locality !== h.name}<span class="via">{h.plz.locality}</span>{/if}
              </span>
              <span class="hs">
                <span class="chip">{typeOf(h)}</span>{#if h.kanton && h.level !== 'kanton'}<span class="kt">{h.kanton}</span>{/if}
                {#if h.plz && h.plz.share < 100}<span class="num">{t('search.addresses', { p: h.plz.share < 0.05 ? '< 0.1' : fmtNumber(h.plz.share, h.plz.share < 1 ? 1 : 0) })}</span>{/if}
              </span>
            </button>
          {/each}
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .search { position: relative; min-width: 0; }
  .field { position: relative; display: flex; align-items: center; }
  .mag { position: absolute; left: 8px; color: var(--text); pointer-events: none; }
  input {
    width: 100%; min-width: 0; padding: 6px 8px 6px 29px; border: 1px solid var(--ink); border-radius: 0; background: var(--panel);
    font-size: var(--fs-small); -webkit-appearance: none; appearance: none;
  }
  input::-webkit-search-cancel-button { display: none; }
  .header { width: 280px; }
  @media (max-width: 1199px) { .header { width: 190px; } }
  .icon {
    width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid var(--ink); background: var(--panel); cursor: pointer;
    color: var(--text); padding: 0;
  }
  .x { flex: none; border: 0; background: none; width: 40px; height: 36px; font-size: var(--fs-stat); cursor: pointer; color: var(--text); }
  .pop {
    position: absolute; z-index: 60; top: calc(100% + 3px); left: 0; right: 0; min-width: 320px; max-height: min(420px, 70vh); overflow-y: auto;
    background: var(--panel); border: 1px solid var(--ink); border-top: 3px solid var(--ink); overscroll-behavior: contain;
  }
  .header .pop { left: auto; right: 0; width: 360px; }
  .hit {
    display: flex; flex-direction: column; align-items: flex-start; gap: 1px; width: 100%; padding: 6px 10px; border: 0;
    border-bottom: 1px solid var(--border); background: none; text-align: left; cursor: pointer;
  }
  .hit.active { background: var(--panel-2); box-shadow: inset 3px 0 0 var(--ink); }
  .hn { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 8px; }
  .hn strong { font-weight: 700; }
  .code { font-weight: 700; background: var(--ink); color: var(--ink-text); padding: 0 4px; font-size: var(--fs-meta); }
  .via { color: var(--muted); font-size: var(--fs-meta); }
  .hs { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-1) var(--sp-2); color: var(--text-2); font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .chip { border: 1px solid var(--ink); padding: 0 var(--sp-1); color: var(--text); font-weight: 600; }
  .kt { font-weight: 600; color: var(--text); }
  .msg { margin: 0; padding: 10px; color: var(--muted); font-size: var(--fs-small); }

  /* phone header: icon, then a full-width field over the header */
  .phone { width: auto; position: static; }
  .phone.expanded .field {
    position: absolute; z-index: 61; inset: 0; background: var(--panel); padding: 0 4px 0 12px; border-bottom: 1px solid var(--rule);
  }
  .phone.expanded .mag { left: 20px; }
  .phone input { font-size: var(--fs-input); padding: 7px 8px 7px 30px; }
  .phone .pop { position: absolute; top: 100%; left: 0; right: 0; width: auto; min-width: 0; max-height: 72vh; border-left: 0; border-right: 0; }
  @media (max-width: 899px) {
    .search:not(.header) input { font-size: var(--fs-input); }
    .pop { min-width: 0; }
  }
</style>
