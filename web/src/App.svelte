<script lang="ts">
  // Shell: header (search, navigation, language), data bootstrap and hash routing. Each route is a view
  // in src/views/: 'map' (default), 'compare' (Compare metrics: two synced maps + scatter), 'profile'
  // (one place, #v=profile&id=261 or id=kanton:ZH), 'places' (Compare places, #v=places&ids=261,351),
  // 'regress' (regression panel, D34; keys in lib/regmodel.ts) and 'sources' (#v=sources&src=<source_id>).
  import { onMount, untrack } from 'svelte';
  import MapView from './views/MapView.svelte';
  import SourcesView from './views/SourcesView.svelte';
  import Search from './components/Search.svelte';
  import ShareButton from './components/ShareButton.svelte';
  import Locator from './components/Locator.svelte';
  import { initRadioGroups } from './lib/a11y';
  import { fmtNumber } from './lib/classify';
  import { ColumnStore } from './lib/columns.svelte';
  import { LEVELS, loadBase, loadLevel, unitCounts, type Base, type LevelData } from './lib/data';
  import { loadFrench, t, levelWord } from './lib/i18n.svelte';
  import { hrefFor } from './lib/nav';
  import { app, syncHash } from './lib/state.svelte';
  import { sanitizeState } from './lib/sanitize';
  import { viewUrl } from './lib/embed';
  import './lib/i18n-spatial';
  import './lib/i18n-ux';

  // pages other than the map load on first use (code splitting: the first load carries the map only)
  let compareP: Promise<typeof import('./views/CompareView.svelte')> | undefined;
  let profileP: Promise<typeof import('./views/ProfileView.svelte')> | undefined;
  let placesP: Promise<typeof import('./views/PlacesView.svelte')> | undefined;
  let regressP: Promise<typeof import('./views/RegressView.svelte')> | undefined;
  const compareMod = () => (compareP ??= import('./views/CompareView.svelte'));
  const profileMod = () => (profileP ??= import('./views/ProfileView.svelte'));
  const placesMod = () => (placesP ??= import('./views/PlacesView.svelte'));
  const regressMod = () => (regressP ??= import('./views/RegressView.svelte'));

  const DESKTOP = '(min-width: 900px)';
  const MAP_ROUTES = ['map', 'compare', 'regress'];
  const PAGES = ['profile', 'places', 'sources'];

  let base = $state.raw<Base | null>(null);
  let cols = $state.raw<ColumnStore | null>(null);
  let ld = $state.raw<LevelData | null>(null);
  let loadError = $state<string | null>(null);
  let desktop = $state(window.matchMedia(DESKTOP).matches);
  let menuOpen = $state(false);
  let menuEl = $state<HTMLDivElement>();
  const t0 = performance.now();

  // unknown level in a link: fall back to municipalities
  if (!LEVELS.some((l) => l.id === app.level && l.geometry)) {
    app.notice = t('ux.badLevel', { id: app.level });
    app.level = 'gemeinde';
  }

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
    const stopRadios = initRadioGroups();
    return () => {
      mq.removeEventListener('change', onDesk);
      stopHash();
      stopRadios();
    };
  });

  // state from a link that the app cannot use is replaced by what is shown (the hash follows)
  $effect(() => {
    void app.loads;
    const b = base;
    if (b) untrack(() => sanitizeState(b));
  });

  const route = $derived(PAGES.includes(app.route) || app.route === 'compare' || app.route === 'regress' ? app.route : 'map');
  const isMap = $derived(MAP_ROUTES.includes(route));

  // geometry and headline values of the map level (only the map views need it; other levels on first use)
  $effect(() => {
    if (!isMap) return;
    const level = app.level;
    let live = true;
    loadLevel(level)
      .then((d) => live && (ld = d))
      .catch((e) => (loadError = String(e)));
    return () => (live = false);
  });

  $effect(() => {
    document.documentElement.lang = app.lang;
    if (app.lang === 'fr') loadFrench();
  });

  const NAV = ['map', 'compare', 'regress', 'places'] as const;
  const navLabel = (r: string) => t(`nav.${r}`);
  /** real links (open in a new tab, middle-click, shareable); the rest of the view state is kept */
  const navHref = (r: string) =>
    r === 'places' && app.route === 'profile' && app.params.id ? hrefFor('places', { ids: app.params.id }) : hrefFor(r);
  /** a search result opens the place's profile */
  function openPlace(ref: string) {
    app.go('profile', { id: ref });
  }
  function outsideMenu(e: PointerEvent) {
    if (menuOpen && menuEl && !menuEl.contains(e.target as Node)) menuOpen = false;
  }
  function skipToMain(e: MouseEvent) {
    e.preventDefault();
    const m = document.getElementById('main');
    m?.focus();
    m?.scrollIntoView?.({ block: 'start' });
  }
  // header: the real number of units, formatted like every other number (never hard-coded)
  const gemCount = $derived(unitCounts.get('gemeinde') ?? null);
  const unitsText = $derived(
    ld && isMap ? `${fmtNumber(ld.units.length, 0)} ${levelWord(ld.level)}` : gemCount !== null ? `${fmtNumber(gemCount, 0)} ${levelWord('gemeinde')}` : '',
  );
  // U18: a profile belongs to the place pages (Compare places)
  const current = $derived(route === 'profile' ? 'places' : route);
  /** first render time, for the performance check (window.__firstRender) */
  function rendered() {
    (window as unknown as { __firstRender: number }).__firstRender ??= performance.now() - t0;
  }
</script>

{#snippet langSwitch()}
  <div class="seg lang" role="radiogroup" aria-label={t('nav.lang')}>
    <button type="button" role="radio" aria-checked={app.lang === 'en'} lang="en" title="English" onclick={() => (app.lang = 'en')}>EN</button>
    <button type="button" role="radio" aria-checked={app.lang === 'de'} lang="de" title="Deutsch" onclick={() => (app.lang = 'de')}>DE</button>
    <button type="button" role="radio" aria-checked={app.lang === 'fr'} lang="fr" title="Français" onclick={() => (app.lang = 'fr')}>FR</button>
  </div>
{/snippet}

<svelte:window onpointerdown={outsideMenu} onkeydown={(e) => e.key === 'Escape' && (menuOpen = false)} />

<div class="app" class:embed={app.embed} class:compare={route === 'compare'} class:regress={route === 'regress'} class:single={route === 'map'} class:page={!isMap}>
  {#if !app.embed}
  <a class="skip" href="#main" onclick={skipToMain}>{t('nav.skip')}</a>
  <header class="top">
    <a class="brand" href={hrefFor('map')} title="ATLAS — {t('nav.map')}">
      <span class="mark" aria-hidden="true"></span>
      <strong>ATLAS</strong>
      <span class="sub">{unitsText ? t('brand.sub', { units: unitsText }) : t('brand.subNo')}</span>
    </a>
    <div class="right">
      <Search variant="header" collapsed={!desktop} onpick={openPlace} />
      {#if desktop}
        <nav class="seg modes" aria-label={t('nav.view')}>
          {#each NAV as r}
            <a href={navHref(r)} aria-current={current === r ? 'page' : undefined}>{navLabel(r)}</a>
          {/each}
        </nav>
        <a class="plain" href={navHref('sources')} aria-current={current === 'sources' ? 'page' : undefined}>{t('nav.sources')}</a>
        <ShareButton />
        {@render langSwitch()}
      {:else}
        <ShareButton variant="icon" />
        <div class="menu" bind:this={menuEl}>
          <button type="button" class="menubtn" aria-haspopup="true" aria-expanded={menuOpen} onclick={() => (menuOpen = !menuOpen)}>
            <span>{current ? navLabel(current) : t('nav.menu')}</span>
            <svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" /></svg>
          </button>
          {#if menuOpen}
            <nav class="drop" aria-label={t('nav.view')}>
              {#each [...NAV, 'sources'] as r}
                <a href={navHref(r)} aria-current={current === r ? 'page' : undefined} onclick={() => (menuOpen = false)}>{navLabel(r)}</a>
              {/each}
              <div class="dlang">{@render langSwitch()}</div>
            </nav>
          {/if}
        </div>
      {/if}
    </div>
  </header>
  {/if}

  {#if app.notice && !app.embed}
    <div class="notice" role="status">
      <span>{app.notice}</span>
      <button type="button" aria-label={t('common.dismiss')} onclick={() => (app.notice = null)}>
        <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.5" /></svg>
      </button>
    </div>
  {/if}

  {#if base && cols}
    {#if route === 'profile'}
      {#await profileMod() then M}<M.default {base} {desktop} />{/await}
    {:else if route === 'places'}
      {#await placesMod() then M}<M.default {base} {desktop} />{/await}
    {:else if route === 'sources'}
      <SourcesView {base} />
    {:else if ld}
      {#if route === 'compare'}
        {#await compareMod() then M}<M.default {base} {ld} {cols} {desktop} onrendered={rendered} />{/await}
      {:else if route === 'regress'}
        {#await regressMod() then M}<M.default {base} {ld} {cols} {desktop} onrendered={rendered} />{/await}
      {:else}
        <MapView {base} {ld} {cols} {desktop} onrendered={rendered} />
      {/if}
    {/if}
  {/if}

  {#if app.embed && !isMap}
    <a class="embed-open" href={viewUrl(false)} target="_blank" rel="noopener">{t('em.open')} ↗</a>
  {/if}

  {#if (!base || (isMap && !ld)) && !loadError}
    <!-- U17: Switzerland's outline (the canton file comes first) and a progress line while the map data loads -->
    <div class="loading" role="status">
      {#if base && isMap}<div class="lshape"><Locator kanton={base.kanton} lakes={base.lakes} shapes={[]} label={t('ux.loadingData')} /></div>{/if}
      <p>{isMap ? (base ? t('ux.loadingData') : t('status.loadingMap')) : t('status.loading')}</p>
      <span class="bar" aria-hidden="true"><i></i></span>
    </div>
  {/if}
  {#if loadError || cols?.error}
    <div class="status err" role="alert">{t('status.error', { e: loadError ?? cols?.error ?? '' })}</div>
  {/if}
</div>

<style>
  .app { position: fixed; inset: 0; display: flex; flex-direction: column; background: var(--bg); }
  .top {
    position: relative; z-index: 50;
    flex: none; display: flex; align-items: center; justify-content: space-between; gap: 12px; height: 52px; padding: 0 max(16px, env(safe-area-inset-right, 0px)) 0 max(16px, env(safe-area-inset-left, 0px));
    padding-top: env(safe-area-inset-top); box-sizing: content-box; background: var(--panel); border-bottom: 3px solid var(--rule);
  }
  .brand { display: flex; align-items: center; gap: 12px; min-width: 0; border: 0; background: none; padding: 0; cursor: pointer; text-align: left; color: var(--text); text-decoration: none; }
  .skip {
    position: absolute; left: 8px; top: -60px; z-index: 100; background: var(--ink); color: var(--ink-text); padding: 0 12px; min-height: 40px; display: flex; align-items: center; font-weight: 600;
    text-decoration: none;
  }
  .skip:focus { top: 8px; }
  .brand strong { font-weight: 700; font-size: var(--fs-lead); letter-spacing: 0.08em; }
  .mark { width: 18px; height: 18px; background: var(--accent); flex: none; position: relative; }
  .mark::before, .mark::after { content: ''; position: absolute; background: #fff; }
  .mark::before { left: 7.5px; top: 3.5px; width: 3px; height: 11px; }
  .mark::after { left: 3.5px; top: 7.5px; width: 11px; height: 3px; }
  .sub { color: var(--muted); font-size: var(--fs-small); padding-left: 12px; border-left: 1px solid var(--rule); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .right { display: flex; align-items: center; gap: 10px; flex: none; }
  .modes a { padding: 5px 12px; }
  .plain {
    border: 1px solid transparent; background: none; padding: 5px 8px; cursor: pointer; font-size: var(--fs-small); font-weight: 500;
    text-decoration: underline; text-underline-offset: 3px; color: var(--text);
  }
  .plain[aria-current='page'] { background: var(--ink); color: var(--ink-text); text-decoration: none; }
  .menu { position: relative; }
  .lang button { padding: 5px 8px; font-size: var(--fs-meta); }
  .dlang { padding: 8px 14px 6px; border-top: 1px solid var(--border); margin-top: 3px; }
  .drop .dlang .lang button { display: inline-block; width: auto; padding: 6px 14px; font-size: var(--fs-small); }
  .drop .dlang .lang button[aria-checked='true'] { background: var(--ink); color: var(--ink-text); }
  .menubtn {
    display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 10px; border: 1px solid var(--ink); background: var(--panel);
    font-size: var(--fs-small); font-weight: 600; cursor: pointer; white-space: nowrap;
  }
  .drop {
    position: absolute; right: 0; top: calc(100% + 3px); min-width: 200px; background: var(--panel); border: 1px solid var(--ink);
    border-top: 3px solid var(--ink); padding: 3px 0; z-index: 70;
  }
  .drop > a { display: block; width: 100%; text-align: left; padding: 10px 14px; border: 0; background: none; font-size: var(--fs-body); cursor: pointer; color: var(--text); text-decoration: none; }
  .drop > a[aria-current='page'] { font-weight: 700; box-shadow: inset 3px 0 0 var(--ink); }
  .status {
    position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); color: var(--muted);
    padding: 8px 14px; border: 1px solid var(--border); border-radius: var(--radius); z-index: 40; max-width: 90vw;
  }
  .status.err { color: var(--text); }
  .loading {
    position: absolute; inset: 52px 0 0; z-index: 40; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--sp-3);
    background: var(--bg); pointer-events: none; padding: var(--sp-4);
  }
  .loading p { margin: 0; font-size: var(--fs-small); line-height: var(--lh-small); color: var(--text-2); }
  .lshape { width: min(520px, 86vw); opacity: 0.55; }
  .bar { position: relative; display: block; width: 160px; height: 2px; background: var(--border); overflow: hidden; }
  .bar i { position: absolute; top: 0; bottom: 0; width: 40%; background: var(--ink); animation: slide 1.1s ease-in-out infinite; }
  @keyframes slide { from { left: -40%; } to { left: 100%; } }
  @media (prefers-reduced-motion: reduce) { .bar i { animation: none; left: 0; width: 100%; } }
  .notice {
    flex: none; display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-1) var(--sp-1) var(--sp-1) var(--gutter);
    border-bottom: var(--rule-edge); background: var(--surface-2); font-size: var(--fs-small); line-height: var(--lh-small); position: relative; z-index: 45;
  }
  .notice span { flex: 1; min-width: 0; }
  .notice button { flex: none; width: var(--ctl-h); height: var(--ctl-h); display: grid; place-items: center; border: 0; background: none; cursor: pointer; color: var(--text); }
  .embed-open {
    position: absolute; right: 8px; bottom: 8px; z-index: 60; background: var(--panel); color: var(--text); border: 1px solid var(--ink);
    padding: 5px 10px; font-size: var(--fs-meta); font-weight: 700; text-decoration: none;
  }

  @media (max-width: 1279px) {
    .sub { display: none; }
  }
  @media (max-width: 899px) {
    .top { height: 44px;  gap: 8px; }
    .brand strong { font-size: var(--fs-body); }
    .mark { width: 16px; height: 16px; }
    .mark::before { left: 6.5px; top: 3px; height: 10px; }
    .mark::after { left: 3px; top: 6.5px; width: 10px; }
    .right { gap: 6px; }
  }
</style>
