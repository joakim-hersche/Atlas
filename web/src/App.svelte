<script lang="ts">
  import { onMount } from 'svelte';
  import Card from './components/Card.svelte';
  import Legend from './components/Legend.svelte';
  import RangeFilter from './components/RangeFilter.svelte';
  import { gapReason, loadReach, loadStart, loadTheme, type ColumnFile, type MetricMeta, type ReachFile, type StartData } from './lib/data';
  import { fmtNumber, quantileClasses } from './lib/classify';
  import { readHash, T_MAX, writeHash, type ReachMode } from './lib/hash';
  import { CH_BOUNDS, MapView } from './lib/mapview';
  import { ReachOverlay } from './lib/reach';
  import { dark, ramp, rampWord } from './lib/theme';

  const HUB = { slug: 'zuerich', name: 'Zürich HB' };
  const REACH_FILE = 'mobility_accessibility';
  const MIN_PER_SECOND = 30; // Play speed: 0 -> 180 min in 6 s
  const DESKTOP = '(min-width: 900px)';

  const initial = readHash();
  let data = $state.raw<StartData | null>(null);
  let loadError = $state<string | null>(null);
  let metricId = $state(initial.metric ?? 'pop_total');
  let popMin = $state<number | null>(initial.popMin);
  let popMax = $state<number | null>(initial.popMax);
  let reachMode = $state<ReachMode>(initial.reach);
  let t = $state(initial.t);
  let playing = $state(false);
  let sel = $state<number | null>(null);
  let sheetOpen = $state(false);
  let panelH = $state(0);
  let isDark = $state(dark.matches);
  let mapReady = $state(false);
  let metricFile = $state.raw<ColumnFile | null>(null);
  let mobility = $state.raw<ColumnFile | null>(null);
  let reachFiles = $state.raw<Partial<Record<'pt' | 'car', ReachFile | null>>>({});
  let reachError = $state<string | null>(null);

  let mapEl: HTMLDivElement;
  let panelEl: HTMLElement;
  let view: MapView | null = null;
  let overlay: ReachOverlay | null = null;

  // ------------------------------------------------------------------ derived data
  const metas = $derived(new Map((data?.metrics ?? []).map((m) => [m.id, m])));
  const meta = $derived<MetricMeta | undefined>(metas.get(metricId) ?? metas.get('pop_total'));
  const col = $derived(meta && metricFile ? metricFile.metrics[meta.id] : undefined);
  const colours = $derived(ramp(isDark));
  const word = $derived(rampWord(isDark));
  const classes = $derived(col ? quantileClasses(col.v) : null);
  const nUnits = $derived(data?.core.units.length ?? 0);

  // headline metrics (D24), grouped by theme in headline order
  const groups = $derived.by(() => {
    const hl = (data?.metrics ?? []).filter((m) => m.headline !== null && !m.hidden).sort((a, b) => a.headline! - b.headline!);
    const out = new Map<string, MetricMeta[]>();
    for (const m of hl) out.set(m.theme, [...(out.get(m.theme) ?? []), m]);
    if (meta && !hl.some((m) => m.id === meta.id)) out.set('Other', [meta]);
    return [...out.entries()];
  });

  // unit names and cantons by core index
  const unitInfo = $derived.by(() => {
    if (!data) return { name: [] as string[], canton: [] as string[] };
    const byId = new Map(data.gemeinde.features.map((f) => [String(f.properties.id), f.properties]));
    return {
      name: data.core.units.map((u) => byId.get(u)?.name ?? u),
      canton: data.core.units.map((u) => byId.get(u)?.canton ?? ''),
    };
  });

  const pop = $derived(data ? data.core.metrics['pop_total'].v : []);
  const popRange = $derived.by(() => {
    const v = pop.filter((x): x is number => x !== null);
    return v.length ? { min: Math.min(...v), max: Math.max(...v) } : { min: 0, max: 1 };
  });
  const match = $derived.by(() => {
    const m = new Uint8Array(pop.length);
    let n = 0;
    for (let i = 0; i < pop.length; i++) {
      const x = pop[i];
      const ok = (popMin === null || (x !== null && x >= popMin)) && (popMax === null || (x !== null && x <= popMax));
      m[i] = ok ? 1 : 0;
      n += m[i];
    }
    return { m, n };
  });

  const reachOn = $derived(reachMode !== 'off');
  const reachMetricId = $derived(reachOn ? `reach_${reachMode}_${HUB.slug}` : null);
  const reachCol = $derived(reachMetricId && mobility ? mobility.metrics[reachMetricId] ?? null : null);
  const reachFile = $derived(reachOn ? reachFiles[reachMode as 'pt' | 'car'] : undefined);
  const reachedCount = $derived.by(() => {
    if (!reachCol) return null;
    let n = 0;
    for (let i = 0; i < reachCol.v.length; i++) {
      const x = reachCol.v[i];
      if (x !== null && x <= t && match.m[i]) n++;
    }
    return n;
  });
  const carHeld = $derived(reachFiles.car === null);

  // ------------------------------------------------------------------ loading
  onMount(() => {
    const onTheme = () => (isDark = dark.matches);
    dark.addEventListener('change', onTheme);
    const t0 = performance.now();
    loadStart()
      .then((d) => {
        data = d;
        if (initial.sel) {
          const i = d.core.units.indexOf(initial.sel);
          if (i >= 0) sel = i;
        }
        view = new MapView(mapEl, d, (i) => {
          sel = i;
          if (i !== null && !window.matchMedia(DESKTOP).matches) sheetOpen = false;
        });
        overlay = new ReachOverlay(view.map, mapEl);
        // ?debug exposes the map object for automated checks
        if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __map: unknown }).__map = view.map;
        view.ready.then(() => {
          fit();
          mapReady = true;
          view!.map.once('idle', () => {
            (window as unknown as { __firstRender: number }).__firstRender = performance.now() - t0;
          });
        });
      })
      .catch((e) => (loadError = String(e)));
    const ro = new ResizeObserver(() => fit());
    ro.observe(document.body);
    return () => {
      dark.removeEventListener('change', onTheme);
      ro.disconnect();
    };
  });

  function fit() {
    if (!view || !panelEl) return;
    const desktop = window.matchMedia(DESKTOP).matches;
    const r = panelEl.getBoundingClientRect();
    const padding = desktop
      ? { top: 24, bottom: 24, left: r.right + 16, right: 64 }
      : { top: 16, bottom: Math.min(window.innerHeight * 0.55, window.innerHeight - r.top + 8), left: 12, right: 12 };
    view.map.fitBounds(CH_BOUNDS, { padding, animate: false });
  }

  // metric column: core file or the theme file holding it (D23)
  $effect(() => {
    if (!data || !meta) return;
    const file = meta.file;
    if (file === 'core') {
      metricFile = data.core;
      return;
    }
    let live = true;
    loadTheme(file).then((f) => live && (metricFile = f)).catch((e) => (loadError = String(e)));
    return () => (live = false);
  });

  // reach data loads on first use
  $effect(() => {
    if (!data || !reachOn) return;
    const mode = reachMode as 'pt' | 'car';
    if (!mobility) loadTheme(REACH_FILE).then((f) => (mobility = f)).catch((e) => (reachError = String(e)));
    if (!(mode in reachFiles)) {
      loadReach(HUB.slug, mode)
        .then((f) => (reachFiles = { ...reachFiles, [mode]: f }))
        .catch((e) => (reachError = String(e)));
    }
  });

  // ------------------------------------------------------------------ map updates
  $effect(() => {
    if (mapReady && classes) view!.setColours(classes.colour);
  });
  $effect(() => {
    if (!mapReady) return;
    const dim = new Float32Array(match.m.length);
    for (let i = 0; i < dim.length; i++) {
      if (!match.m[i]) dim[i] = 0.82;
      else if (reachOn && reachCol) {
        const x = reachCol.v[i];
        dim[i] = x !== null && x <= t ? 0 : 0.62;
      }
    }
    view!.setDim(dim);
  });
  $effect(() => {
    if (mapReady) view!.setSelected(sel);
  });
  // read the dependencies before the readiness check so the effects re-run on change
  $effect(() => {
    const f = reachFile ?? null;
    if (mapReady) overlay!.setNetwork(f);
  });
  $effect(() => {
    const on = reachOn;
    if (mapReady) overlay!.setVisible(on);
  });
  $effect(() => {
    const now = t;
    if (mapReady) overlay!.setTime(now);
  });
  $effect(() => {
    isDark;
    if (mapReady) {
      view!.applyTheme();
      overlay!.draw();
    }
  });
  // URL hash (not while the animation runs)
  $effect(() => {
    const s = { metric: metricId, popMin, popMax, reach: reachMode, t, sel: sel === null || !data ? null : data.core.units[sel] };
    if (playing) return;
    const h = setTimeout(() => writeHash(s), 150);
    return () => clearTimeout(h);
  });
  // shrinking the sheet changes the visible map area
  $effect(() => {
    sheetOpen;
    requestAnimationFrame(() => view?.map.resize());
  });

  // ------------------------------------------------------------------ reach animation
  let raf = 0;
  function play() {
    if (playing) {
      stop();
      return;
    }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      t = T_MAX;
      return;
    }
    if (t >= T_MAX) t = 0;
    playing = true;
    let last = performance.now();
    const step = (now: number) => {
      t = Math.min(T_MAX, t + ((now - last) / 1000) * MIN_PER_SECOND);
      last = now;
      if (t >= T_MAX) {
        stop();
        return;
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  function stop() {
    cancelAnimationFrame(raf);
    playing = false;
    t = Math.round(t);
  }
  function setMode(m: ReachMode) {
    stop();
    reachMode = m;
  }

  // ------------------------------------------------------------------ card
  const card = $derived.by(() => {
    if (sel === null || !data || !meta || !col || !metricFile) return null;
    let reach = null;
    if (reachOn) {
      const label = reachMode === 'pt' ? 'Public transport' : 'Car';
      const short = reachMode === 'pt' ? 'Public transport' : 'Car';
      const rmeta = reachMetricId ? metas.get(reachMetricId) : undefined;
      if (reachCol && rmeta && mobility) {
        const x = reachCol.v[sel];
        reach = {
          label, short, hub: HUB.name, minutes: x,
          reason: x === null ? gapReason(mobility, reachCol, sel, rmeta, unitInfo.canton[sel]) : null,
          within: x !== null && x <= t,
        };
      } else {
        reach = { label, short, hub: HUB.name, minutes: null, reason: mobility ? 'held back in this build' : 'loading…', within: false };
      }
    }
    return { i: sel, reach };
  });
</script>

<div class="app" style="--sheet:{panelH}px">
  <div class="map" bind:this={mapEl}></div>

  {#if !mapReady && !loadError}
    <div class="status" role="status">Loading map…</div>
  {/if}
  {#if loadError}
    <div class="status err" role="alert">Could not load data: {loadError}</div>
  {/if}

  {#if card && meta && col && metricFile && data}
    <div class="card-wrap">
      <Card
        name={unitInfo.name[card.i]} canton={unitInfo.canton[card.i]} bfs={data.core.units[card.i]}
        {meta} file={metricFile} {col} index={card.i} source={data.sources.get(meta.source)}
        reach={card.reach} onclose={() => (sel = null)} />
    </div>
  {/if}

  <aside class="panel" class:open={sheetOpen} bind:this={panelEl} bind:offsetHeight={panelH} aria-label="Map controls">
    <button type="button" class="handle" aria-expanded={sheetOpen} onclick={() => (sheetOpen = !sheetOpen)}>
      <span class="grip" aria-hidden="true"></span>
      <span class="brand">Gemeindebank</span>
      <span class="summary">
        {(popMin !== null || popMax !== null ? `${fmtNumber(match.n, 0)} of ${fmtNumber(nUnits, 0)} match · ` : '') + (sheetOpen ? 'Less' : 'More filters')}
      </span>
    </button>
    <div class="body">
      <section>
        <label class="field">
          <span class="flabel">Shade by</span>
          <select bind:value={metricId} disabled={!data}>
            {#each groups as [theme, list]}
              <optgroup label={theme}>
                {#each list as m}<option value={m.id}>{m.label_en}</option>{/each}
              </optgroup>
            {/each}
          </select>
        </label>
        {#if meta && classes && col}
          <Legend {meta} {classes} {colours} {word} {nUnits} />
        {/if}
      </section>

      <section class="reach">
        <div class="row">
          <span class="flabel">Reach<span class="hubname">&nbsp;from {HUB.name}</span></span>
          <div class="seg" role="radiogroup" aria-label="Reach mode">
            <button type="button" role="radio" aria-checked={reachMode === 'off'} onclick={() => setMode('off')}>Off</button>
            <button type="button" role="radio" aria-checked={reachMode === 'pt'} onclick={() => setMode('pt')}>Public transport</button>
            <button type="button" role="radio" aria-checked={reachMode === 'car'} disabled={carHeld}
              title={carHeld ? 'Car reach is not in this build' : ''} onclick={() => setMode('car')}>Car</button>
          </div>
        </div>
        {#if reachOn}
          <div class="time">
            <button type="button" class="play" onclick={play} aria-label={playing ? 'Pause' : 'Play'}>
              {#if playing}
                <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" rx="1" /><rect x="9.5" y="2" width="3.5" height="12" rx="1" /></svg>
              {:else}
                <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M4 2.5v11a.7.7 0 0 0 1.06.6l9-5.5a.7.7 0 0 0 0-1.2l-9-5.5A.7.7 0 0 0 4 2.5z" /></svg>
              {/if}
            </button>
            <input type="range" min="0" max={T_MAX} step="1" value={t} aria-label="Travel time in minutes"
              oninput={(e) => { stop(); t = +e.currentTarget.value; }} />
            <output class="tval">{Math.round(t)} min</output>
          </div>
          <p class="note">
            {#if reachError}
              Reach data could not be loaded: {reachError}
            {:else if reachFile === undefined || !mobility}
              Loading network…
            {:else if reachFile === null}
              No {reachMode === 'car' ? 'car' : 'public transport'} network in this build.
            {:else}
              {#if reachedCount !== null}<strong>{fmtNumber(reachedCount, 0)}</strong> municipalities within {Math.round(t)} min of {HUB.name}{popMin !== null || popMax !== null ? ' (among the filtered)' : ''}.
              {:else}Municipality times are held back in this build; only the network is drawn.{/if}
              <span class="muted detail">{reachMode === 'pt' ? `Weekday departure ${reachFile.departure ?? ''}, wait at the hub included.` : 'Average weekday (ARE NPVM 2023).'}</span>
            {/if}
          </p>
        {/if}
      </section>

      <section class="extra">
        <RangeFilter label="Population" min={popRange.min} max={popRange.max} bind:lo={popMin} bind:hi={popMax}
          count={match.n} total={nUnits} />
        {#if data}<p class="note muted">{data.core.metrics['pop_total'].period} · BFS STATPOP. Non-matching municipalities are dimmed.</p>{/if}
      </section>
    </div>
  </aside>
</div>

<style>
  .app { position: fixed; inset: 0; }
  .map { position: absolute; inset: 0; }
  .status {
    position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); color: var(--muted);
    padding: 10px 16px; border-radius: 10px; box-shadow: var(--shadow); z-index: 5; max-width: 90vw;
  }
  .status.err { color: var(--reach-line); }

  .card-wrap { position: absolute; z-index: 6; top: max(8px, env(safe-area-inset-top)); left: 8px; right: 8px; max-width: 440px; margin: 0 auto; }

  .panel {
    position: absolute; z-index: 4; left: 0; right: 0; bottom: 0; background: var(--panel); border-top: 1px solid var(--border);
    border-radius: var(--radius) var(--radius) 0 0; box-shadow: var(--shadow); max-height: 46vh; display: flex; flex-direction: column;
    padding-bottom: env(safe-area-inset-bottom);
  }
  .panel.open { max-height: 82vh; }
  .handle {
    display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 4px 8px; padding: 6px 16px 6px; border: 0; background: none;
    text-align: left; cursor: pointer; flex: none;
  }
  .grip { grid-column: 1 / -1; justify-self: center; width: 38px; height: 5px; border-radius: 3px; background: var(--border); }
  .brand { font-weight: 700; letter-spacing: 0.01em; }
  .summary { color: var(--muted); font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .body { overflow-y: auto; padding: 0 16px 12px; overscroll-behavior: contain; }
  section { padding: 8px 0; }
  section + section { border-top: 1px solid var(--border); }
  .extra { display: none; }
  .panel.open .extra { display: block; }

  .field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
  .flabel { font-size: 0.8rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
  select {
    width: 100%; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--border); background: var(--panel-2); font-size: 16px;
  }
  .row { display: flex; flex-direction: column; gap: 6px; }
  .seg { display: flex; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: var(--panel-2); }
  .seg button { flex: 1; padding: 7px 6px; border: 0; background: none; cursor: pointer; font-size: 0.9rem; white-space: nowrap; }
  .seg button + button { border-left: 1px solid var(--border); }
  .seg button[aria-checked='true'] { background: var(--accent); color: var(--accent-text); font-weight: 600; }
  .seg button:disabled { opacity: 0.45; cursor: not-allowed; }
  .time { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
  .time input { flex: 1; accent-color: var(--reach-line); min-width: 0; height: 28px; }
  .play {
    width: 40px; height: 40px; border-radius: 50%; border: 0; background: var(--reach-line); color: #fff; display: grid; place-items: center;
    cursor: pointer; flex: none;
  }
  .play svg { fill: currentColor; }
  .tval { font-variant-numeric: tabular-nums; font-weight: 650; min-width: 4.2em; text-align: right; }
  .note { margin: 6px 0 0; font-size: 0.85rem; }
  .muted { color: var(--muted); }

  @media (max-width: 899px) {
    :global(.maplibregl-ctrl-top-right) { display: none; }
    .handle { padding: 4px 16px 2px; }
    .brand { font-size: 0.95rem; }
    section { padding: 6px 0; }
    .field { flex-direction: row; align-items: center; gap: 10px; margin-bottom: 6px; }
    .field .flabel { flex: none; }
    .field select { flex: 1; min-width: 0; padding: 6px 8px; }
    .row { flex-direction: row; align-items: center; gap: 10px; }
    .row .flabel { flex: none; }
    .hubname { display: none; }
    .row .seg { flex: 1; min-width: 0; }
    .seg button { padding: 6px 4px; font-size: 0.85rem; }
    .time { margin-top: 6px; }
    .panel:not(.open) .detail { display: none; }
  }
  @media (min-width: 900px) {
    .panel {
      top: 16px; left: 16px; bottom: auto; right: auto; width: 360px; max-height: calc(100% - 32px); border-radius: var(--radius);
      border: 1px solid var(--border);
    }
    .panel.open { max-height: calc(100% - 32px); }
    .handle { cursor: default; pointer-events: none; padding-top: 12px; }
    .grip, .summary { display: none; }
    .extra { display: block; }
    .card-wrap { left: auto; right: 56px; top: 16px; width: 340px; margin: 0; }
  }
</style>
