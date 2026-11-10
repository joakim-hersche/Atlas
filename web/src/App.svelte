<script lang="ts">
  import { onMount, tick } from 'svelte';
  import Card from './components/Card.svelte';
  import Legend from './components/Legend.svelte';
  import MetricPicker from './components/MetricPicker.svelte';
  import RangeFilter from './components/RangeFilter.svelte';
  import Scatter from './components/Scatter.svelte';
  import StatsBlock from './components/StatsBlock.svelte';
  import {
    gapReason, loadCH, loadReach, loadStart, loadTheme, loadUnits, type ColumnFile, type MetricMeta, type ReachFile, type StartData,
  } from './lib/data';
  import { buildScale, fmtNumber, fmtValue, isDiverging, sortedValues, type Method } from './lib/classify';
  import { readHash, T_MAX, writeHash, type Mode, type ReachMode } from './lib/hash';
  import { CH_BOUNDS, MapView, syncCameras } from './lib/mapview';
  import { ReachOverlay } from './lib/reach';
  import { dark, divRamp, mute, seqRamp, token } from './lib/theme';

  const HUB = { slug: 'zuerich', name: 'Zürich HB' };
  const REACH_FILE = 'mobility_accessibility';
  const MIN_PER_SECOND = 30; // Play speed: 0 -> 180 min in 6 s
  const DESKTOP = '(min-width: 900px)';
  const REGION_NAMES: Record<string, string> = { '1': 'German', '2': 'French', '3': 'Italian', '4': 'Romansh' };

  interface Preset {
    slug: string;
    label: string;
    a: string;
    b: string;
    fallback?: { b: string; label: string };
  }
  const PRESETS: Preset[] = [
    { slug: 'left-income', label: 'Left bloc vs income', a: 'nrw_share_left_bloc', b: 'tax_np_mean_taxable_income',
      fallback: { b: 'nrw_share_sp', label: 'SP share vs income' } },
    { slug: 'density-foreigners', label: 'Density vs foreigners', a: 'geo_pop_density', b: 'share_foreign' },
    { slug: 'age-svp', label: 'Age vs SVP', a: 'share_age_65plus', b: 'nrw_share_svp' },
    { slug: 'heatpumps-income', label: 'Heat pumps vs income', a: 'gws_share_heatpump', b: 'tax_np_mean_taxable_income' },
  ];

  const initial = readHash();
  let data = $state.raw<StartData | null>(null);
  let loadError = $state<string | null>(null);
  let mode = $state<Mode>(initial.mode);
  let metricId = $state(initial.metric ?? 'pop_total');
  let metricB = $state<string | null>(initial.metricB);
  let method = $state<Method>(initial.cls);
  let popMin = $state<number | null>(initial.popMin);
  let popMax = $state<number | null>(initial.popMax);
  let reachMode = $state<ReachMode>(initial.reach);
  let t = $state(initial.t);
  let playing = $state(false);
  let sel = $state<number | null>(null);
  let hover = $state<number | null>(null);
  let hoverAt = $state<{ pane: 'a' | 'b'; x: number; y: number } | null>(null);
  let sheetOpen = $state(false);
  let panelH = $state(0);
  let isDark = $state(dark.matches);
  let desktop = $state(window.matchMedia(DESKTOP).matches);
  let mapReady = $state(false);
  let mapReadyB = $state(false);
  let fileA = $state.raw<ColumnFile | null>(null);
  let fileB = $state.raw<ColumnFile | null>(null);
  let chA = $state.raw<{ value: number; period: string } | null>(null);
  let mobility = $state.raw<ColumnFile | null>(null);
  let reachFiles = $state.raw<Partial<Record<'pt' | 'car', ReachFile | null>>>({});
  let reachError = $state<string | null>(null);
  let regions = $state.raw<{ idx: Int8Array; names: string[] } | null>(null);

  let mapElA: HTMLDivElement;
  let mapElB = $state<HTMLDivElement>();
  let panelEl = $state<HTMLElement>();
  let viewA: MapView | null = null;
  let viewB: MapView | null = null;
  let overlay: ReachOverlay | null = null;

  const compare = $derived(mode === 'compare');

  // ------------------------------------------------------------------ metrics and presets
  const metas = $derived(new Map((data?.metrics ?? []).map((m) => [m.id, m])));
  const metaA = $derived<MetricMeta | undefined>(metas.get(metricId) ?? metas.get('pop_total'));
  const metaB = $derived<MetricMeta | undefined>(metricB ? metas.get(metricB) : undefined);
  const presets = $derived(
    PRESETS.flatMap((p) => {
      if (!metas.size) return [];
      if (metas.has(p.a) && metas.has(p.b)) return [p];
      // left bloc not in this build yet: SP share vs income
      if (p.fallback && metas.has(p.fallback.b) && metas.has(p.b)) return [{ ...p, a: p.fallback.b, label: p.fallback.label }];
      return [];
    }),
  );
  const activePreset = $derived(presets.find((p) => p.a === metricId && p.b === metricB)?.slug ?? null);

  function applyPreset(p: Preset) {
    metricId = p.a;
    metricB = p.b;
    sel = null;
  }

  // ------------------------------------------------------------------ columns
  $effect(() => {
    const m = metaA;
    if (!data || !m) return;
    let live = true;
    loadTheme(m.file, data.core).then((f) => live && (fileA = f)).catch((e) => (loadError = String(e)));
    loadCH(m.file).then((f) => {
      if (!live) return;
      const c = f?.metrics[m.id];
      chA = c && c.v[0] !== null ? { value: c.v[0]!, period: c.period } : null;
    });
    return () => (live = false);
  });
  $effect(() => {
    const m = metaB;
    if (!data || !m || !compare) return;
    let live = true;
    loadTheme(m.file, data.core).then((f) => live && (fileB = f)).catch((e) => (loadError = String(e)));
    return () => (live = false);
  });
  const colA = $derived(metaA && fileA ? fileA.metrics[metaA.id] : undefined);
  const colB = $derived(metaB && fileB ? fileB.metrics[metaB.id] : undefined);

  const seq = $derived(seqRamp(isDark));
  const div = $derived(divRamp(isDark));
  const scaleA = $derived(colA && metaA ? buildScale(colA.v, method, isDiverging(metaA, sortedValues(colA.v)), seq, div) : null);
  const scaleB = $derived(colB && metaB ? buildScale(colB.v, method, isDiverging(metaB, sortedValues(colB.v)), seq, div) : null);
  const nUnits = $derived(data?.core.units.length ?? 0);

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
  const filtered = $derived(popMin !== null || popMax !== null);
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

  // ------------------------------------------------------------------ reach
  const reachOn = $derived(reachMode !== 'off' && !compare);
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
    const mqd = window.matchMedia(DESKTOP);
    const onDesk = () => (desktop = mqd.matches);
    mqd.addEventListener('change', onDesk);
    const t0 = performance.now();
    loadStart()
      .then((d) => {
        data = d;
        if (initial.sel) {
          const i = d.core.units.indexOf(initial.sel);
          if (i >= 0) sel = i;
        }
        // bare '#compare' or '#<preset>' from a shared link
        if (initial.preset !== null) {
          const ids = new Set(d.metrics.map((m) => m.id));
          const avail = PRESETS.map((p) =>
            ids.has(p.a) && ids.has(p.b) ? p : p.fallback && ids.has(p.fallback.b) ? { ...p, a: p.fallback.b } : null,
          ).filter((p): p is Preset => p !== null);
          const p = avail.find((x) => x.slug === initial.preset) ?? avail[0];
          if (p) applyPreset(p);
        } else if (mode === 'compare' && !metricB) metricB = defaultB(metricId);
        viewA = new MapView(mapElA, d, { onSelect: select, onHover: (i, p) => onMapHover('a', i, p) });
        overlay = new ReachOverlay(viewA.map, mapElA);
        if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __map: unknown }).__map = viewA.map;
        viewA.ready.then(() => {
          fit();
          mapReady = true;
          viewA!.map.once('idle', () => {
            (window as unknown as { __firstRender: number }).__firstRender = performance.now() - t0;
          });
        });
      })
      .catch((e) => (loadError = String(e)));
    const ro = new ResizeObserver(() => {
      viewA?.map.resize();
      viewB?.map.resize();
    });
    ro.observe(mapElA);
    return () => {
      dark.removeEventListener('change', onTheme);
      mqd.removeEventListener('change', onDesk);
      ro.disconnect();
    };
  });

  function defaultB(a: string) {
    return a === 'tax_np_mean_taxable_income' ? 'nrw_share_svp' : 'tax_np_mean_taxable_income';
  }

  function select(i: number | null) {
    sel = i;
    if (i !== null && !desktop) sheetOpen = false;
  }
  function onMapHover(pane: 'a' | 'b', i: number | null, p: { x: number; y: number } | null) {
    hover = i;
    hoverAt = i === null || !p ? null : { pane, x: p.x, y: p.y };
  }

  // second map, created the first time compare mode is shown
  let unsync: (() => void) | null = null;
  $effect(() => {
    if (!compare || !data || !mapElB || viewB) return;
    const el = mapElB;
    viewB = new MapView(el, data, { onSelect: select, onHover: (i, p) => onMapHover('b', i, p) }, { nav: false });
    const ro = new ResizeObserver(() => viewB?.map.resize());
    ro.observe(el);
    viewB.ready.then(() => {
      unsync = syncCameras(viewA!.map, viewB!.map);
      mapReadyB = true;
    });
  });
  $effect(() => () => unsync?.());

  function fit() {
    if (!viewA) return;
    const mob = !window.matchMedia(DESKTOP).matches;
    let padding: { top: number; bottom: number; left: number; right: number };
    if (compare) padding = { top: 8, bottom: 8, left: 8, right: 8 };
    else if (!mob) padding = { top: 24, bottom: 24, left: 24, right: 48 };
    else {
      const top = panelEl ? panelEl.getBoundingClientRect().top - mapElA.getBoundingClientRect().top : mapElA.clientHeight;
      padding = { top: 12, bottom: Math.max(12, mapElA.clientHeight - top + 8), left: 10, right: 10 };
    }
    viewA.map.resize();
    viewB?.map.resize();
    viewA.map.fitBounds(CH_BOUNDS, { padding, animate: false });
  }
  // refit after a layout change (mode, phone/desktop)
  $effect(() => {
    void [compare, desktop];
    if (!mapReady) return;
    tick().then(() => requestAnimationFrame(() => fit()));
  });
  $effect(() => {
    if (!mapReadyB) return;
    tick().then(() => requestAnimationFrame(() => fit()));
  });
  // phones: compact compare maps scroll with the page; panning needs two fingers
  $effect(() => {
    const coop = compare && !desktop;
    for (const v of [mapReady ? viewA : null, mapReadyB ? viewB : null]) {
      if (!v) continue;
      if (coop) v.map.cooperativeGestures.enable();
      else v.map.cooperativeGestures.disable();
    }
  });

  // language regions for the scatter plot
  $effect(() => {
    if (!compare || !data || regions) return;
    const d = data;
    loadUnits()
      .then((u) => {
        const pos = new Map(d.core.units.map((id, i) => [id, i]));
        const idx = new Int8Array(d.core.units.length).fill(-1);
        for (const r of u) {
          if (r.level !== 'gemeinde' || !r.sprachgebiet) continue;
          const i = pos.get(r.id);
          if (i !== undefined) idx[i] = Number(r.sprachgebiet) - 1;
        }
        const names = ['1', '2', '3', '4'].map((k) => REGION_NAMES[k]);
        regions = { idx, names };
      })
      .catch((e) => (loadError = String(e)));
  });

  // reach data loads on first use
  $effect(() => {
    if (!data || !reachOn) return;
    const m = reachMode as 'pt' | 'car';
    if (!mobility) loadTheme(REACH_FILE).then((f) => (mobility = f)).catch((e) => (reachError = String(e)));
    if (!(m in reachFiles)) {
      loadReach(HUB.slug, m)
        .then((f) => (reachFiles = { ...reachFiles, [m]: f }))
        .catch((e) => (reachError = String(e)));
    }
  });

  // ------------------------------------------------------------------ map updates
  const coloursA = $derived.by(() => {
    if (!scaleA) return null;
    isDark;
    const surface = token('--map-bg');
    const out = scaleA.unitColour.slice();
    if (compare) return out;
    for (let i = 0; i < out.length; i++) {
      const c = out[i];
      if (c === null) continue;
      if (!match.m[i]) out[i] = mute(c, surface, 0.88);
      else if (reachOn && reachCol) {
        const x = reachCol.v[i];
        if (!(x !== null && x <= t)) out[i] = mute(c, surface, 0.72);
      }
    }
    return out;
  });
  $effect(() => {
    if (mapReady && coloursA) viewA!.setColours(coloursA);
  });
  $effect(() => {
    if (mapReadyB && scaleB) viewB!.setColours(scaleB.unitColour);
  });
  $effect(() => {
    const s = sel;
    if (mapReady) viewA!.setSelected(s);
    if (mapReadyB) viewB!.setSelected(s);
  });
  $effect(() => {
    const h = hover;
    if (mapReady) viewA!.setHover(h);
    if (mapReadyB) viewB!.setHover(h);
  });
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
      viewA!.applyTheme();
      overlay!.draw();
    }
    if (mapReadyB) viewB!.applyTheme();
  });
  // URL hash (not while the animation runs)
  $effect(() => {
    const s = {
      mode, metric: metricId, metricB, cls: method, popMin, popMax, reach: reachMode, t,
      sel: sel === null || !data ? null : data.core.units[sel],
    };
    if (playing) return;
    const h = setTimeout(() => writeHash(s), 150);
    return () => clearTimeout(h);
  });
  $effect(() => {
    sheetOpen;
    requestAnimationFrame(() => viewA?.map.resize());
  });

  function setModeTo(m: Mode) {
    if (m === mode) return;
    stop();
    hover = null;
    hoverAt = null;
    if (m === 'compare' && !metricB) metricB = defaultB(metricId);
    mode = m;
  }

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
  function setReach(m: ReachMode) {
    stop();
    reachMode = m;
  }

  // ------------------------------------------------------------------ card and tooltip
  const card = $derived.by(() => {
    if (sel === null || !data || !metaA || !colA || !fileA || compare) return null;
    let reach = null;
    if (reachOn) {
      const label = reachMode === 'pt' ? 'Public transport' : 'Car';
      const rmeta = reachMetricId ? metas.get(reachMetricId) : undefined;
      if (reachCol && rmeta && mobility) {
        const x = reachCol.v[sel];
        reach = {
          label, short: label, hub: HUB.name, minutes: x,
          reason: x === null ? gapReason(mobility, reachCol, sel, rmeta, unitInfo.canton[sel]) : null,
          within: x !== null && x <= t,
        };
      } else {
        reach = { label, short: label, hub: HUB.name, minutes: null, reason: mobility ? 'held back in this build' : 'loading…', within: false };
      }
    }
    return { i: sel, reach };
  });
  const tipRows = $derived.by(() => {
    if (hover === null || !hoverAt || !metaA || !colA) return null;
    const rows: { k: string; v: string }[] = [];
    const fmt = (c: typeof colA, m: MetricMeta) => (c && c.v[hover!] !== null ? fmtValue(c.v[hover!]!, m) : 'no data');
    if (compare) {
      rows.push({ k: 'A', v: fmt(colA, metaA) });
      if (metaB && colB) rows.push({ k: 'B', v: fmt(colB, metaB) });
    } else rows.push({ k: '', v: fmt(colA, metaA) });
    return rows;
  });
</script>

<div class="app" class:compare class:single={!compare} style="--sheet:{panelH}px">
  <header class="top">
    <div class="brand">
      <span class="mark" aria-hidden="true"></span>
      <strong>Gemeindebank</strong>
      <span class="sub">Swiss municipalities · <span class="num">{fmtNumber(nUnits || 2110, 0)}</span> units · boundaries of 2026</span>
    </div>
    <div class="seg modes" role="radiogroup" aria-label="View">
      <button type="button" role="radio" aria-checked={!compare} onclick={() => setModeTo('single')}>Single map</button>
      <button type="button" role="radio" aria-checked={compare} onclick={() => setModeTo('compare')}>Compare</button>
    </div>
  </header>

  {#if compare}
    <nav class="presets" aria-label="Example comparisons">
      <span class="caps">Examples</span>
      {#each presets as p}
        <button type="button" class="chip" aria-pressed={activePreset === p.slug} onclick={() => applyPreset(p)}>{p.label}</button>
      {/each}
    </nav>
  {/if}

  <main class="stage">
    {#if !compare}
      <aside class="controls" class:open={sheetOpen} bind:this={panelEl} bind:offsetHeight={panelH} aria-label="Map controls">
        <button type="button" class="handle" aria-expanded={sheetOpen} onclick={() => (sheetOpen = !sheetOpen)}>
          <svg class="chev" class:up={!sheetOpen} viewBox="0 0 20 12" width="20" height="12" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
          <span class="summary">
            {(filtered ? `${fmtNumber(match.n, 0)} of ${fmtNumber(nUnits, 0)} match · ` : '') + (sheetOpen ? 'Less' : 'Statistics, filters')}
          </span>
        </button>
        <div class="body">
          <section>
            <div class="caps lab">Shade by</div>
            {#if data}<MetricPicker metrics={data.metrics} value={metricId} onpick={(id) => (metricId = id)} />{/if}
            {#if metaA && scaleA && colA}
              <div class="legend-wrap">
                <Legend meta={metaA} v={colA.v} period={colA.period} scale={scaleA} {nUnits} source={data?.sources.get(metaA.source)}
                  {method} onmethod={(m) => (method = m)} compact={!desktop && !sheetOpen} />
              </div>
            {/if}
          </section>

          <section class="reach">
            <div class="row">
              <span class="caps">Reach from {HUB.name}</span>
              <div class="seg" role="radiogroup" aria-label="Reach mode">
                <button type="button" role="radio" aria-checked={reachMode === 'off'} onclick={() => setReach('off')}>Off</button>
                <button type="button" role="radio" aria-checked={reachMode === 'pt'} onclick={() => setReach('pt')}>Public transport</button>
                <button type="button" role="radio" aria-checked={reachMode === 'car'} disabled={carHeld}
                  title={carHeld ? 'Car reach is not in this build' : ''} onclick={() => setReach('car')}>Car</button>
              </div>
            </div>
            {#if reachOn}
              <div class="time">
                <button type="button" class="play" onclick={play} aria-label={playing ? 'Pause' : 'Play'}>
                  {#if playing}
                    <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" /><rect x="9.5" y="2" width="3.5" height="12" /></svg>
                  {:else}
                    <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M4 2v12l10-6z" /></svg>
                  {/if}
                </button>
                <input type="range" min="0" max={T_MAX} step="1" value={t} aria-label="Travel time in minutes"
                  oninput={(e) => { stop(); t = +e.currentTarget.value; }} />
                <output class="tval num">{Math.round(t)} min</output>
              </div>
              <p class="note">
                {#if reachError}
                  Reach data could not be loaded: {reachError}
                {:else if reachFile === undefined || !mobility}
                  Loading network…
                {:else if reachFile === null}
                  No {reachMode === 'car' ? 'car' : 'public transport'} network in this build.
                {:else}
                  {#if reachedCount !== null}<span class="num">{fmtNumber(reachedCount, 0)}</span> municipalities within {Math.round(t)} min{filtered ? ' (among the filtered)' : ''}; others shown desaturated.
                  {:else}Municipality times are held back in this build; only the network is drawn.{/if}
                  <span class="foot detail">{reachMode === 'pt' ? `Weekday departure ${reachFile.departure ?? ''}, wait at the hub included. Own routing on the national GTFS timetable.` : 'Average weekday, ARE NPVM 2023.'}</span>
                {/if}
              </p>
            {/if}
          </section>

          <section class="extra">
            <RangeFilter label="Population filter" min={popRange.min} max={popRange.max} bind:lo={popMin} bind:hi={popMax}
              count={match.n} total={nUnits} />
            {#if data}<p class="foot">BFS STATPOP {data.core.metrics['pop_total'].period}. Non-matching municipalities are muted, not hidden.</p>{/if}
          </section>

          {#if !desktop && metaA && colA}
            <section class="extra">
              <StatsBlock meta={metaA} v={colA.v} period={colA.period} names={unitInfo.name} cantons={unitInfo.canton} ch={chA} sel={null}
                source={data?.sources.get(metaA.source)} />
            </section>
          {/if}
        </div>
      </aside>
    {/if}

    <section class="pane pa">
      {#if compare && data}
        <div class="phead">
          <MetricPicker metrics={data.metrics} value={metricId} tag="A" onpick={(id) => (metricId = id)} />
        </div>
      {/if}
      <div class="pbody">
        <div class="mapbox">
          <div class="map" bind:this={mapElA}></div>
          {#if hoverAt?.pane === 'a' && tipRows && hover !== null && desktop}
            <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
              <strong>{unitInfo.name[hover]}</strong>{#if !unitInfo.name[hover].includes('(')}&nbsp;<span class="muted">{unitInfo.canton[hover]}</span>{/if}
              {#each tipRows as r}<div class="num">{#if r.k}<span class="k">{r.k}</span>{/if}{r.v}</div>{/each}
            </div>
          {/if}
        </div>
        {#if compare && metaA && scaleA && colA}
          <div class="plegend">
            <Legend meta={metaA} v={colA.v} period={colA.period} scale={scaleA} {nUnits} source={data?.sources.get(metaA.source)}
              {method} onmethod={(m) => (method = m)} />
          </div>
        {/if}
      </div>
    </section>

    <section class="pane pb" hidden={!compare}>
      {#if data}
        <div class="phead">
          <MetricPicker metrics={data.metrics} value={metricB ?? ''} tag="B" onpick={(id) => (metricB = id)} />
        </div>
      {/if}
      <div class="pbody">
        <div class="mapbox">
          <div class="map" bind:this={mapElB}></div>
          {#if hoverAt?.pane === 'b' && tipRows && hover !== null && desktop}
            <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
              <strong>{unitInfo.name[hover]}</strong>{#if !unitInfo.name[hover].includes('(')}&nbsp;<span class="muted">{unitInfo.canton[hover]}</span>{/if}
              {#each tipRows as r}<div class="num">{#if r.k}<span class="k">{r.k}</span>{/if}{r.v}</div>{/each}
            </div>
          {/if}
        </div>
        {#if compare && metaB && scaleB && colB}
          <div class="plegend">
            <Legend meta={metaB} v={colB.v} period={colB.period} scale={scaleB} {nUnits} source={data?.sources.get(metaB.source)}
              {method} onmethod={(m) => (method = m)} />
          </div>
        {/if}
      </div>
    </section>

    {#if compare}
      <section class="pane ps">
        {#if metaA && metaB && colA && colB && regions}
          <Scatter xMeta={metaA} yMeta={metaB} x={colA.v} y={colB.v} xPeriod={colA.period} yPeriod={colB.period}
            region={regions.idx} regionNames={regions.names} {pop} names={unitInfo.name} cantons={unitInfo.canton}
            {hover} {sel} {isDark} onhover={(i) => { hover = i; hoverAt = null; }} onselect={(i) => (sel = i)} />
        {:else}
          <p class="muted loading">Loading…</p>
        {/if}
      </section>
    {/if}

    {#if !compare && desktop}
      <aside class="side" aria-label="Statistics">
        {#if card && metaA && colA && fileA && data}
          <div class="caps lab">Selected municipality</div>
          <Card name={unitInfo.name[card.i]} canton={unitInfo.canton[card.i]} bfs={data.core.units[card.i]}
            meta={metaA} file={fileA} col={colA} index={card.i} source={data.sources.get(metaA.source)}
            reach={card.reach} docked onclose={() => (sel = null)} />
        {:else}
          <p class="foot hint">Tap or click a municipality for its value, rank and percentile.</p>
        {/if}
        {#if metaA && colA}
          <div class="sblock">
            <StatsBlock meta={metaA} v={colA.v} period={colA.period} names={unitInfo.name} cantons={unitInfo.canton} ch={chA} sel={null}
              source={data?.sources.get(metaA.source)} />
          </div>
        {/if}
      </aside>
    {/if}

    {#if !compare && !desktop && card && metaA && colA && fileA && data}
      <div class="card-wrap">
        <Card name={unitInfo.name[card.i]} canton={unitInfo.canton[card.i]} bfs={data.core.units[card.i]}
          meta={metaA} file={fileA} col={colA} index={card.i} source={data.sources.get(metaA.source)}
          reach={card.reach} onclose={() => (sel = null)} />
      </div>
    {/if}

    {#if !mapReady && !loadError}
      <div class="status" role="status">Loading map…</div>
    {/if}
    {#if loadError}
      <div class="status err" role="alert">Could not load data: {loadError}</div>
    {/if}
  </main>
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
  .presets {
    flex: none; display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: var(--panel); border-bottom: 1px solid var(--rule);
    overflow-x: auto; scrollbar-width: none;
  }
  .presets .caps { margin-right: 4px; flex: none; }
  .chip {
    flex: none; padding: 4px 10px; border: 1px solid var(--ink); background: none; cursor: pointer;
    font-size: 0.8rem; font-weight: 500; white-space: nowrap;
  }
  .chip:hover { color: var(--accent); border-color: var(--accent); }
  .chip[aria-pressed='true'] { background: var(--ink); border-color: var(--ink); color: var(--ink-text); }

  .stage { flex: 1; min-height: 0; position: relative; }
  .pane { position: relative; min-width: 0; min-height: 0; display: flex; flex-direction: column; background: var(--panel); }
  .pane[hidden] { display: none; }
  .phead { flex: none; padding: 8px; border-bottom: 1px solid var(--rule); }
  .pbody { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .mapbox { position: relative; flex: 1; min-height: 0; }
  .map { position: absolute; inset: 0; }
  .plegend { flex: none; padding: 10px 12px; border-top: 1px solid var(--rule); }
  .maptip {
    position: absolute; z-index: 5; pointer-events: none; transform: translate(14px, 14px); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 9px; font-size: 0.8rem; white-space: nowrap;
  }
  .k { display: inline-block; width: 1.3em; color: var(--muted); font-weight: 500; }
  .muted { color: var(--muted); }
  .loading { padding: 16px; }
  .lab { margin-bottom: 6px; }

  .status {
    position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); color: var(--muted);
    padding: 8px 14px; border: 1px solid var(--border); border-radius: var(--radius); z-index: 40; max-width: 90vw;
  }
  .status.err { color: var(--text); }

  /* controls (single mode) */
  .controls { display: flex; flex-direction: column; background: var(--panel); z-index: 4; }
  .handle { display: none; }
  .body { overflow-y: auto; padding: 0 16px 14px; overscroll-behavior: contain; }
  section { min-width: 0; }
  .body section { padding: 14px 0; }
  .body section + section { border-top: 1px solid var(--rule); }
  .legend-wrap { margin-top: 10px; }
  .row { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; }
  .time { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
  .time input { flex: 1; accent-color: var(--ink); min-width: 0; height: 24px; }
  .play {
    width: 28px; height: 28px; border-radius: var(--radius); border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text);
    display: grid; place-items: center; cursor: pointer; flex: none;
  }
  .play svg { fill: currentColor; }
  .tval { min-width: 4.2em; text-align: right; }
  .note { margin: 6px 0 0; font-size: 0.8rem; }
  .note .foot { display: block; margin-top: 3px; }
  .side { background: var(--panel); border-left: 1px solid var(--rule); padding: 14px 16px; overflow-y: auto; }
  .sblock { margin-top: 18px; padding-top: 12px; border-top: 1px solid var(--rule); }
  .hint { margin: 0; }
  .card-wrap { position: absolute; z-index: 6; top: 8px; left: 8px; right: 8px; max-width: 440px; margin: 0 auto; }

  /* ---------------- desktop / tablet */
  @media (min-width: 900px) {
    .single .stage { display: grid; grid-template-columns: 330px minmax(0, 1fr) 290px; }
    .single .controls { border-right: 1px solid var(--rule); min-height: 0; }
    .single .body { padding-top: 4px; }
    .single .pa { background: var(--map-bg); }

    .compare .stage {
      display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); grid-template-rows: minmax(340px, 1.35fr) minmax(300px, 1fr);
      gap: 1px; background: var(--rule); overflow-y: auto;
    }
    .compare .pane { container-type: inline-size; }
    .compare .ps { grid-column: 1 / -1; padding: 10px 14px 12px; }
    @container (min-width: 620px) {
      .pbody { flex-direction: row; }
      .plegend { width: 250px; border-top: 0; border-left: 1px solid var(--rule); overflow-y: auto; }
    }
  }

  /* ---------------- phone */
  @media (max-width: 899px) {
    .top { height: 44px; border-bottom-width: 2px; }
    .brand strong { font-size: 1.02rem; }
    .mark { width: 16px; height: 16px; }
    .mark::before { left: 6.5px; top: 3px; height: 10px; }
    .mark::after { left: 3px; top: 6.5px; width: 10px; }
    .sub { display: none; }
    .modes button { padding: 3px 9px; font-size: 0.78rem; }
    .presets { padding: 6px 16px; }

    .single .pa { position: absolute; inset: 0; }
    .single .controls {
      position: absolute; left: 0; right: 0; bottom: 0; border-top: 2px solid var(--rule); max-height: 48%;
      padding-bottom: env(safe-area-inset-bottom);
    }
    .single .controls.open { max-height: 86%; }
    .handle {
      display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 5px 14px 2px; border: 0; background: none; cursor: pointer; flex: none;
    }
    .chev { fill: none; stroke: var(--ink); stroke-width: 2.5; stroke-linecap: square; transition: transform 0.15s; }
    .chev.up { transform: rotate(180deg); }
    @media (prefers-reduced-motion: reduce) { .chev { transition: none; } }
    .summary { color: var(--text); font-weight: 500; font-size: 0.76rem; font-variant-numeric: tabular-nums; }
    .body section { padding: 9px 0; }
    .legend-wrap { margin-top: 6px; }
    .extra { display: none; }
    .controls.open .extra { display: block; }
    .row { flex-direction: row; align-items: center; justify-content: space-between; gap: 8px; }
    .reach .seg button { padding: 4px 7px; }
    .controls:not(.open) .detail { display: none; }
    :global(.single .maplibregl-ctrl-top-right) { display: none; }

    .compare .stage { overflow-y: auto; -webkit-overflow-scrolling: touch; }
    .compare .pane { border-bottom: 1px solid var(--rule); }
    .compare .mapbox { flex: none; height: 250px; }
    .compare .plegend { padding: 6px 10px 8px; }
    .compare .ps { padding: 10px 10px calc(16px + env(safe-area-inset-bottom)); }
    :global(.compare .maplibregl-ctrl-top-right) { display: none; }
  }
</style>
