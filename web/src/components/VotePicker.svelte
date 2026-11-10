<script lang="ts">
  // Vote picker (D32): any federal vote, searchable by title (all languages) and date, newest first.
  // Each entry shows the national yes share and the official outcome where known.
  import { fmtNumber } from '../lib/classify';
  import { t } from '../lib/i18n.svelte';
  import { norm } from '../lib/places';
  import { app } from '../lib/state.svelte';
  import type { VoteEntry, VoteIndex } from '../lib/votes';

  interface Props {
    index: VoteIndex;
    /** vote id shown (the latest when the picker value is null) */
    value: string;
    onpick: (id: string) => void;
  }
  let { index, value, onpick }: Props = $props();

  let open = $state(false);
  let q = $state('');
  let active = $state(0);
  let root: HTMLDivElement;
  let input = $state<HTMLInputElement>();

  const titleOf = (v: VoteEntry) => v.title[app.lang] ?? v.title.en ?? v.title.de ?? v.title.fr ?? Object.values(v.title)[0] ?? '';
  const votes = $derived(index.votes.slice().sort((a, b) => b.date.localeCompare(a.date) || Number(b.id) - Number(a.id)));
  const keyed = $derived(votes.map((v) => ({ v, key: norm(`${v.date} ${v.date.slice(0, 4)} ${Object.values(v.title).join(' ')}`) })));
  const list = $derived.by(() => {
    const words = norm(q).split(' ').filter(Boolean);
    const hits = words.length ? keyed.filter((k) => words.every((w) => k.key.includes(w))).map((k) => k.v) : votes;
    return hits.slice(0, 200);
  });
  const current = $derived(index.votes.find((v) => v.id === value) ?? null);

  function toggle() {
    open = !open;
    if (open) {
      q = '';
      active = Math.max(0, list.findIndex((v) => v.id === value));
      queueMicrotask(() => {
        input?.focus();
        root.querySelector('.opt[aria-selected="true"]')?.scrollIntoView({ block: 'nearest' });
      });
    }
  }
  function pick(v: VoteEntry | undefined) {
    if (!v) return;
    open = false;
    onpick(v.id);
  }
  function key(e: KeyboardEvent) {
    if (e.key === 'Escape') open = false;
    else if (e.key === 'ArrowDown') { active = Math.min(list.length - 1, active + 1); e.preventDefault(); scroll(); }
    else if (e.key === 'ArrowUp') { active = Math.max(0, active - 1); e.preventDefault(); scroll(); }
    else if (e.key === 'Enter') pick(list[active]);
  }
  function scroll() {
    queueMicrotask(() => root.querySelector('.opt.active')?.scrollIntoView({ block: 'nearest' }));
  }
  function outside(e: PointerEvent) {
    if (open && !root.contains(e.target as Node)) open = false;
  }
  const outcome = (v: VoteEntry) => (v.accepted === true ? t('vt.accepted') : v.accepted === false ? t('vt.rejected') : null);
</script>

<svelte:window onpointerdown={outside} />

<div class="vp" bind:this={root}>
  <button type="button" class="btn" aria-haspopup="listbox" aria-expanded={open} onclick={toggle}>
    <span class="lbl">
      <span class="caps">{t('vt.vote')} · {current?.date ?? ''}{current?.provisional ? ` · ${t('vt.prov')}` : ''}</span>
      <span class="ttl">{current ? titleOf(current) : value}</span>
    </span>
    <svg class="chev" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4" /></svg>
  </button>
  {#if open}
    <div class="pop" role="dialog" aria-label={t('vt.choose')}>
      <div class="search">
        <input bind:this={input} bind:value={q} type="search" placeholder={t('vt.search', { n: fmtNumber(index.votes.length, 0) })}
          aria-label={t('vt.searchL')} oninput={() => (active = 0)} onkeydown={key} />
        <button type="button" class="x" aria-label={t('common.close')} onclick={() => (open = false)}>×</button>
      </div>
      <div class="list" role="listbox" aria-label={t('vt.choose')}>
        {#if !list.length}<p class="empty">{t('vt.none', { q })}</p>{/if}
        {#each list as v, k (v.id)}
          {@const oc = outcome(v)}
          <button type="button" role="option" class="opt" class:active={k === active} aria-selected={v.id === value}
            onclick={() => pick(v)} onpointerenter={() => (active = k)}>
            <span class="od num">{v.date}</span>
            <span class="ot">{titleOf(v)}</span>
            <span class="om num">
              {v.yes_pct !== null ? `${fmtNumber(v.yes_pct, 1)}% ${t('vt.yes')}` : '–'}{#if oc}{' · '}<span class:acc={v.accepted}>{oc}</span>{/if}{#if v.provisional}{' · '}{t('vt.prov')}{/if}
            </span>
          </button>
        {/each}
        <p class="hint foot">{t('vt.hint', { n: fmtNumber(index.votes.length, 0) })}</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .vp { position: relative; min-width: 0; margin-top: 6px; }
  .btn { display: flex; align-items: center; gap: 8px; width: 100%; padding: 5px 8px; text-align: left; cursor: pointer; background: var(--panel); border: 1px solid var(--ink); }
  .lbl { display: flex; flex-direction: column; min-width: 0; flex: 1; line-height: 1.25; }
  .caps { font-size: 0.62rem; }
  .ttl { font-weight: 600; font-size: 0.84rem; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .chev { flex: none; }
  .pop {
    position: absolute; z-index: 30; top: calc(100% + 4px); left: 0; width: max(100%, 420px); max-width: calc(100vw - 16px);
    background: var(--panel); border: 1px solid var(--ink); border-top: 3px solid var(--ink); display: flex; flex-direction: column; max-height: min(480px, 72vh);
  }
  .search { display: flex; gap: 4px; padding: 6px; border-bottom: 1px solid var(--border); }
  .search input { flex: 1; min-width: 0; padding: 6px 8px; border: 1px solid var(--ink); background: var(--panel); font-size: 16px; border-radius: 0; }
  .x { border: 0; background: none; width: 32px; font-size: 1.2rem; cursor: pointer; color: var(--text); }
  .list { overflow-y: auto; overscroll-behavior: contain; padding-bottom: 6px; }
  .opt { display: grid; grid-template-columns: 6.2em minmax(0, 1fr); gap: 0 8px; width: 100%; padding: 6px 10px; border: 0; border-bottom: 1px solid var(--border); background: none; text-align: left; cursor: pointer; }
  .opt.active { background: var(--panel-2); }
  .opt[aria-selected='true'] { box-shadow: inset 3px 0 0 var(--accent); }
  .od { font-size: 0.74rem; color: var(--muted); grid-row: span 2; padding-top: 1px; }
  .ot { font-size: 0.82rem; font-weight: 500; line-height: 1.25; }
  .om { font-size: 0.72rem; color: var(--muted); }
  .acc { color: var(--text); font-weight: 600; }
  .empty { padding: 10px; margin: 0; color: var(--muted); }
  .hint { padding: 8px 10px 0; margin: 0; }
  @media (max-width: 899px) {
    .pop { position: fixed; top: max(8px, env(safe-area-inset-top)); left: 8px; right: 8px; width: auto; max-width: none; max-height: 76vh; }
  }
</style>
