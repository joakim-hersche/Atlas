<script lang="ts">
  // Shell: header, data bootstrap and hash routing. Each route is a view in src/views/.
  // Routes: 'map' (single map, default) and 'compare' (two synced maps + scatter). Pages added later
  // (profile, compare places, search, sources) register here with their route name (app.route).
  import { onMount } from 'svelte';
  import CompareView from './views/CompareView.svelte';
  import MapView from './views/MapView.svelte';
  import { fmtNumber } from './lib/classify';
  import { ColumnStore } from './lib/columns.svelte';
  import { levelInfo, LEVELS, loadBase, loadLevel, type Base, type LevelData } from './lib/data';
  import { app, syncHash } from './lib/state.svelte';

  const DESKTOP = '(min-width: 900px)';

  let base = $state.raw<Base | null>(null);
  let cols = $state.raw<ColumnStore | null>(null);
  let ld = $state.raw<LevelData | null>(null);
  let loadError = $state<string | null>(null);
  let desktop = $state(window.matchMedia(DESKTOP).matches);
  const t0 = performance.now();

  // unknown level in a link: fall back to municipalities
  if (!LEVELS.some((l) => l.id === app.level && l.geometry)) app.level = 'gemeinde';

  onMount(() => {
    const mq = window.matchMedia(DESKTOP);
    const onDesk = () => (desktop = mq.matches);
    mq.addEventListener('change', onDesk);
    loadBase()
      .then((b) => {
        base = b;
        cols = new ColumnStore(b);
      })
      .catch((e) => (loadError = String(e)));
    const stopHash = syncHash();
    return () => {
      mq.removeEventListener('change', onDesk);
      stopHash();
    };
  });

  // geometry and headline values of the current level (other levels load on first use)
  $effect(() => {
    const level = app.level;
    let live = true;
    loadLevel(level)
      .then((d) => live && (ld = d))
      .catch((e) => (loadError = String(e)));
    return () => (live = false);
  });

  const route = $derived(app.route === 'compare' ? 'compare' : 'map');
  function setRoute(r: 'map' | 'compare') {
    if (r !== app.route) app.go(r, {});
  }
  const unitsText = $derived(ld ? `${fmtNumber(ld.units.length, 0)} ${levelInfo(ld.level).label.toLowerCase()}` : '2’110 municipalities');
  /** first render time, for the performance check (window.__firstRender) */
  function rendered() {
    (window as unknown as { __firstRender: number }).__firstRender ??= performance.now() - t0;
  }
</script>

<div class="app" class:compare={route === 'compare'} class:single={route === 'map'}>
  <header class="top">
    <div class="brand">
      <span class="mark" aria-hidden="true"></span>
      <strong>Gemeindebank</strong>
      <span class="sub">Switzerland · <span class="num">{unitsText}</span> · boundaries of 2026</span>
    </div>
    <div class="seg modes" role="radiogroup" aria-label="View">
      <button type="button" role="radio" aria-checked={route === 'map'} onclick={() => setRoute('map')}>Single map</button>
      <button type="button" role="radio" aria-checked={route === 'compare'} onclick={() => setRoute('compare')}>Compare</button>
    </div>
  </header>

  {#if base && cols && ld}
    {#if route === 'compare'}
      <CompareView {base} {ld} {cols} {desktop} onrendered={rendered} />
    {:else}
      <MapView {base} {ld} {cols} {desktop} onrendered={rendered} />
    {/if}
  {/if}

  {#if (!base || !ld) && !loadError}
    <div class="status" role="status">Loading map…</div>
  {/if}
  {#if loadError || cols?.error}
    <div class="status err" role="alert">Could not load data: {loadError ?? cols?.error}</div>
  {/if}
</div>

<style>
  .app { position: fixed; inset: 0; display: flex; flex-direction: column; background: var(--bg); }
  .top {
    flex: none; display: flex; align-items: center; justify-content: space-between; gap: 12px; height: 52px; padding: 0 max(16px, env(safe-area-inset-right, 0px)) 0 max(16px, env(safe-area-inset-left, 0px));
    padding-top: env(safe-area-inset-top); box-sizing: content-box; background: var(--panel); border-bottom: 3px solid var(--rule);
  }
  .brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
  .brand strong { font-weight: 700; font-size: 1.15rem; letter-spacing: -0.02em; }
  .mark { width: 18px; height: 18px; background: var(--accent); flex: none; position: relative; }
  .mark::before, .mark::after { content: ''; position: absolute; background: #fff; }
  .mark::before { left: 7.5px; top: 3.5px; width: 3px; height: 11px; }
  .mark::after { left: 3.5px; top: 7.5px; width: 11px; height: 3px; }
  .sub { color: var(--muted); font-size: 0.8rem; padding-left: 12px; border-left: 1px solid var(--rule); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .modes button { padding: 4px 12px; }
  .status {
    position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); color: var(--muted);
    padding: 8px 14px; border: 1px solid var(--border); border-radius: var(--radius); z-index: 40; max-width: 90vw;
  }
  .status.err { color: var(--text); }

  @media (max-width: 899px) {
    .top { height: 44px; border-bottom-width: 2px; }
    .brand strong { font-size: 1.02rem; }
    .mark { width: 16px; height: 16px; }
    .mark::before { left: 6.5px; top: 3px; height: 10px; }
    .mark::after { left: 3px; top: 6.5px; width: 10px; }
    .sub { display: none; }
    .modes button { padding: 3px 9px; font-size: 0.78rem; }
  }
</style>
