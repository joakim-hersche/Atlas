<script lang="ts">
  // Single map: shade metric, reach, filters, quick card and statistics.
  // Desktop: controls left, map centre, card and statistics right. Phone: map with a bottom sheet.
  import { onMount, tick } from 'svelte';
  import Card from '../components/Card.svelte';
  import Legend from '../components/Legend.svelte';
  import MetricPicker from '../components/MetricPicker.svelte';
  import RangeFilter from '../components/RangeFilter.svelte';
  import StatsBlock from '../components/StatsBlock.svelte';
  import { buildScale, fmtNumber, fmtValue, isDiverging, sortedValues } from '../lib/classify';
  import type { ColumnStore } from '../lib/columns.svelte';
  import {
    gapReason, levelInfo, loadCH, loadReach, unavailableReason, type Base, type LevelData, type MetricMeta, type ReachFile,
  } from '../lib/data';
  import { T_MAX, type ReachMode } from '../lib/hash';
  import { CH_BOUNDS, UnitMap } from '../lib/mapview';
  import { ReachOverlay } from '../lib/reach';
  import { app } from '../lib/state.svelte';
  import { divRamp, mute, seqRamp, token } from '../lib/theme';

  interface Props {
    base: Base;
    ld: LevelData;
    cols: ColumnStore;
    desktop: boolean;
    onrendered?: () => void;
  }
  let { base, ld, cols, desktop, onrendered }: Props = $props();

  const HUB = { slug: 'zuerich', name: 'Zürich HB' };
  const MIN_PER_SECOND = 30; // Play speed: 0 -> 180 min in 6 s

  let mapReady = $state(false);
  let hover = $state<number | null>(null);
  let hoverAt = $state<{ x: number; y: number } | null>(null);
  let sheetOpen = $state(false);
  let chA = $state.raw<{ value: number; period: string } | null>(null);
  let reachNets = $state.raw<Record<string, ReachFile | null>>({});
  let reachError = $state<string | null>(null);
  let mapEl: HTMLDivElement;
  let panelEl = $state<HTMLElement>();
  let view: UnitMap | null = null;
  let overlay: ReachOverlay | null = null;

  const metas = $derived(base.metas);
  const li = $derived(levelInfo(ld.level));
  const word = $derived(li.label.toLowerCase());
  const nUnits = $derived(ld.units.length);

  // ------------------------------------------------------------------ shade metric
  const metaA = $derived<MetricMeta>(metas.get(app.metric) ?? metas.get('pop_total')!);
  const whyA = $derived(unavailableReason(metaA, ld.level));
  const refA = $derived(cols.get(ld, metaA.id, app.year));
  const colA = $derived(refA?.col);
  const scaleA = $derived.by(() => {
    if (!colA) return null;
    const s = sortedValues(colA.v);
    return s.length ? buildScale(colA.v, app.cls, isDiverging(metaA, s), seqRamp(), divRamp()) : null;
  });
  $effect(() => {
    const m = metaA;
    let live = true;
    chA = null;
    loadCH(m.file).then((f) => {
      if (!live) return;
      const c = f?.metrics[m.id];
      chA = c && c.v[0] !== null ? { value: c.v[0]!, period: c.period } : null;
    });
    return () => (live = false);
  });

  // ------------------------------------------------------------------ filters (population)
  const popIdx = $derived(app.filters.findIndex((f) => f.kind === 'num' && f.metric === 'pop_total'));
  const popF = $derived(popIdx >= 0 ? app.filters[popIdx] : null);
  const pop = $derived(ld.core.metrics['pop_total']?.v ?? []);
  const popRange = $derived.by(() => {
    const v = sortedValues(pop);
    return v.length ? { min: v[0], max: v[v.length - 1] } : { min: 0, max: 1 };
  });
  const popLo = $derived(popF?.kind === 'num' ? popF.lo : null);
  const popHi = $derived(popF?.kind === 'num' ? popF.hi : null);
  function setPop(lo: number | null, hi: number | null) {
    const rest = app.filters.filter((f) => !(f.kind === 'num' && f.metric === 'pop_total'));
    app.filters = lo === null && hi === null ? rest : [{ kind: 'num', metric: 'pop_total', lo, hi }, ...rest];
  }
  const filtered = $derived(popLo !== null || popHi !== null);
  const match = $derived.by(() => {
    const m = new Uint8Array(nUnits);
    let n = 0;
    for (let i = 0; i < nUnits; i++) {
      const x = pop[i];
      const ok = !filtered || (x !== null && (popLo === null || x >= popLo) && (popHi === null || x <= popHi));
      m[i] = ok ? 1 : 0;
      n += m[i];
    }
    return { m, n };
  });

  // ------------------------------------------------------------------ reach
  const reachOn = $derived(app.reach !== 'off');
  const reachMode = $derived(app.reach as 'pt' | 'car');
  const reachRef = $derived(reachOn && ld.level === 'gemeinde' ? cols.get(ld, `reach_${reachMode}_${HUB.slug}`) : null);
  const reachCol = $derived(reachRef?.col ?? null);
  const reachFile = $derived(reachOn ? reachNets[`${HUB.slug}_${reachMode}`] : undefined);
  const reachedCount = $derived.by(() => {
    if (!reachCol) return null;
    let n = 0;
    for (let i = 0; i < reachCol.v.length; i++) {
      const x = reachCol.v[i];
      if (x !== null && x <= app.t && match.m[i]) n++;
    }
    return n;
  });
  const carHeld = $derived(reachNets[`${HUB.slug}_car`] === null);
  $effect(() => {
    if (!reachOn) return;
    const key = `${HUB.slug}_${reachMode}`;
    if (key in reachNets) return;
    loadReach(HUB.slug, reachMode)
      .then((f) => (reachNets = { ...reachNets, [key]: f }))
      .catch((e) => (reachError = String(e)));
  });

  // ------------------------------------------------------------------ selection
  const selIdx = $derived(app.sel !== null ? (ld.index.get(app.sel) ?? null) : null);
  function select(i: number | null) {
    app.sel = i === null ? null : ld.units[i];
    if (i !== null && !desktop) sheetOpen = false;
  }

  // ------------------------------------------------------------------ map
  onMount(() => {
    view = new UnitMap(mapEl, base, { onSelect: select, onHover: (i, p) => { hover = i; hoverAt = i === null ? null : p; } });
    overlay = new ReachOverlay(view.map, mapEl);
    if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __map: unknown }).__map = view.map;
    view.ready.then(() => {
      mapReady = true;
      fit();
      view!.map.once('idle', () => onrendered?.());
    });
    const ro = new ResizeObserver(() => view?.map.resize());
    ro.observe(mapEl);
    return () => {
      ro.disconnect();
      stop();
      view?.map.remove();
    };
  });

  function fit() {
    if (!view) return;
    let padding: { top: number; bottom: number; left: number; right: number };
    if (desktop) padding = { top: 24, bottom: 24, left: 24, right: 48 };
    else {
      const top = panelEl ? panelEl.getBoundingClientRect().top - mapEl.getBoundingClientRect().top : mapEl.clientHeight;
      padding = { top: 12, bottom: Math.max(12, mapEl.clientHeight - top + 8), left: 10, right: 10 };
    }
    view.map.resize();
    view.map.fitBounds(CH_BOUNDS, { padding, animate: false });
  }
  $effect(() => {
    void desktop;
    if (mapReady) tick().then(() => requestAnimationFrame(() => fit()));
  });
  $effect(() => {
    sheetOpen;
    requestAnimationFrame(() => view?.map.resize());
  });

  const colours = $derived.by(() => {
    if (!scaleA || whyA) return ld.units.map(() => null);
    const surface = token('--map-bg');
    const out = scaleA.unitColour.slice();
    for (let i = 0; i < out.length; i++) {
      const c = out[i];
      if (c === null) continue;
      if (!match.m[i]) out[i] = mute(c, surface, 0.88);
      else if (reachCol) {
        const x = reachCol.v[i];
        if (!(x !== null && x <= app.t)) out[i] = mute(c, surface, 0.72);
      }
    }
    return out;
  });
  $effect(() => {
    const d = ld;
    if (mapReady) view!.setLevel(d);
  });
  $effect(() => {
    const c = colours;
    void ld;
    if (mapReady) view!.setColours(c);
  });
  $effect(() => {
    const s = selIdx;
    void ld;
    if (mapReady) view!.setSelected(s);
  });
  $effect(() => {
    const h = hover;
    if (mapReady) view!.setHover(h);
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
    const now = app.t;
    if (mapReady) overlay!.setTime(now);
  });

  // ------------------------------------------------------------------ reach animation
  let raf = 0;
  function play() {
    if (app.playing) {
      stop();
      return;
    }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      app.t = T_MAX;
      return;
    }
    if (app.t >= T_MAX) app.t = 0;
    app.playing = true;
    let last = performance.now();
    const step = (now: number) => {
      app.t = Math.min(T_MAX, app.t + ((now - last) / 1000) * MIN_PER_SECOND);
      last = now;
      if (app.t >= T_MAX) {
        stop();
        return;
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  function stop() {
    cancelAnimationFrame(raf);
    if (app.playing) app.t = Math.round(app.t);
    app.playing = false;
  }
  function setReach(m: ReachMode) {
    stop();
    app.reach = m;
  }

  // ------------------------------------------------------------------ card and tooltip
  const card = $derived.by(() => {
    if (selIdx === null || !refA || whyA) return null;
    let reach = null;
    if (reachOn) {
      const label = reachMode === 'pt' ? 'Public transport' : 'Car';
      if (reachRef && reachCol) {
        const x = reachCol.v[selIdx];
        reach = {
          label, short: label, hub: HUB.name, minutes: x,
          reason: x === null ? gapReason(reachRef.file, reachCol, selIdx, reachRef.meta, ld.canton[selIdx]) : null,
          within: x !== null && x <= app.t,
        };
      } else {
        const reason = ld.level !== 'gemeinde' ? 'per municipality only' : reachRef === null ? 'held back in this build' : 'loading…';
        reach = { label, short: label, hub: HUB.name, minutes: null, reason, within: false };
      }
    }
    const i = selIdx;
    const sub = ld.level === 'gemeinde' ? `${ld.canton[i]} · BFS ${ld.units[i]}` : ld.level === 'kanton' ? li.one : `${li.one}${ld.canton[i] ? ` · ${ld.canton[i]}` : ''}`;
    return { i, reach, sub };
  });
  const tip = $derived.by(() => {
    if (hover === null || !hoverAt || !colA) return null;
    const x = colA.v[hover];
    return x === null || x === undefined ? 'no data' : fmtValue(x, metaA);
  });
</script>

<main class="stage">
  <aside class="controls" class:open={sheetOpen} bind:this={panelEl} aria-label="Map controls">
    <button type="button" class="handle" aria-expanded={sheetOpen} onclick={() => (sheetOpen = !sheetOpen)}>
      <svg class="chev" class:up={!sheetOpen} viewBox="0 0 20 12" width="20" height="12" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
      <span class="summary">
        {(filtered ? `${fmtNumber(match.n, 0)} of ${fmtNumber(nUnits, 0)} match · ` : '') + (sheetOpen ? 'Less' : 'Statistics, filters')}
      </span>
    </button>
    <div class="body">
      <section>
        <div class="caps lab">Shade by</div>
        <MetricPicker metrics={base.metrics} level={ld.level} value={metaA.id} onpick={(id) => (app.metric = id)} />
        <div class="legend-wrap">
          {#if whyA}
            <p class="why">{whyA}</p>
          {:else if scaleA && colA}
            <Legend meta={metaA} v={colA.v} period={colA.period} scale={scaleA} {nUnits} unitWord={word} source={base.sources.get(metaA.source)}
              method={app.cls} onmethod={(m) => (app.cls = m)} compact={!desktop && !sheetOpen} />
          {:else if refA === undefined}
            <p class="foot">Loading…</p>
          {/if}
        </div>
      </section>

      <section class="reach">
        <div class="row">
          <span class="caps">Reach from {HUB.name}</span>
          <div class="seg" role="radiogroup" aria-label="Reach mode">
            <button type="button" role="radio" aria-checked={app.reach === 'off'} onclick={() => setReach('off')}>Off</button>
            <button type="button" role="radio" aria-checked={app.reach === 'pt'} onclick={() => setReach('pt')}>Public transport</button>
            <button type="button" role="radio" aria-checked={app.reach === 'car'} disabled={carHeld}
              title={carHeld ? 'Car reach is not in this build' : ''} onclick={() => setReach('car')}>Car</button>
          </div>
        </div>
        {#if reachOn}
          <div class="time">
            <button type="button" class="play" onclick={play} aria-label={app.playing ? 'Pause' : 'Play'}>
              {#if app.playing}
                <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" /><rect x="9.5" y="2" width="3.5" height="12" /></svg>
              {:else}
                <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M4 2v12l10-6z" /></svg>
              {/if}
            </button>
            <input type="range" min="0" max={T_MAX} step="1" value={app.t} aria-label="Travel time in minutes"
              oninput={(e) => { stop(); app.t = +e.currentTarget.value; }} />
            <output class="tval num">{Math.round(app.t)} min</output>
          </div>
          <p class="note">
            {#if reachError}
              Reach data could not be loaded: {reachError}
            {:else if reachFile === undefined || reachRef === undefined}
              Loading network…
            {:else if reachFile === null}
              No {reachMode === 'car' ? 'car' : 'public transport'} network in this build.
            {:else}
              {#if reachedCount !== null}<span class="num">{fmtNumber(reachedCount, 0)}</span> municipalities within {Math.round(app.t)} min{filtered ? ' (among the filtered)' : ''}; others shown desaturated.
              {:else if ld.level !== 'gemeinde'}Travel times are per municipality; the network is drawn, units are not highlighted at this level.
              {:else}Municipality times are held back in this build; only the network is drawn.{/if}
              <span class="foot detail">{reachMode === 'pt' ? `Weekday departure ${reachFile.departure ?? ''}, wait at the hub included. Own routing on the national GTFS timetable.` : 'Average weekday, ARE NPVM 2023.'}</span>
            {/if}
          </p>
        {/if}
      </section>

      <section class="extra">
        <RangeFilter label="Population filter" min={popRange.min} max={popRange.max} lo={popLo} hi={popHi} onchange={setPop}
          count={match.n} total={nUnits} />
        <p class="foot">BFS STATPOP {ld.core.metrics['pop_total']?.period ?? ''}. Non-matching {word} are muted, not hidden.</p>
      </section>

      {#if !desktop && colA && !whyA}
        <section class="extra">
          <StatsBlock meta={metaA} v={colA.v} period={colA.period} names={ld.name} cantons={ld.canton} ch={chA} sel={null}
            source={base.sources.get(metaA.source)} unitWord={word} />
        </section>
      {/if}
    </div>
  </aside>

  <section class="pane">
    <div class="mapbox">
      <div class="map" bind:this={mapEl}></div>
      {#if tip && hover !== null && hoverAt && desktop}
        <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
          <strong>{ld.name[hover]}</strong>{#if ld.canton[hover] && ld.level !== 'kanton' && !ld.name[hover].includes('(')}&nbsp;<span class="muted">{ld.canton[hover]}</span>{/if}
          <div class="num">{tip}</div>
        </div>
      {/if}
    </div>
  </section>

  {#if desktop}
    <aside class="side" aria-label="Statistics">
      {#if card && refA && colA}
        <div class="caps lab">Selected {li.one}</div>
        <Card name={ld.name[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
          source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} docked onclose={() => (app.sel = null)} />
      {:else}
        <p class="foot hint">Tap or click a {li.one} for its value, rank and percentile.</p>
      {/if}
      {#if colA && !whyA}
        <div class="sblock">
          <StatsBlock meta={metaA} v={colA.v} period={colA.period} names={ld.name} cantons={ld.canton} ch={chA} sel={null}
            source={base.sources.get(metaA.source)} unitWord={word} />
        </div>
      {/if}
    </aside>
  {/if}

  {#if !desktop && card && refA && colA}
    <div class="card-wrap">
      <Card name={ld.name[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
        source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} onclose={() => (app.sel = null)} />
    </div>
  {/if}

  {#if !mapReady}
    <div class="status" role="status">Loading map…</div>
  {/if}
</main>

<style>
  .stage { flex: 1; min-height: 0; position: relative; }
  .pane { position: relative; min-width: 0; min-height: 0; display: flex; flex-direction: column; background: var(--map-bg); }
  .mapbox { position: relative; flex: 1; min-height: 0; }
  .map { position: absolute; inset: 0; }
  .maptip {
    position: absolute; z-index: 5; pointer-events: none; transform: translate(14px, 14px); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 9px; font-size: 0.8rem; white-space: nowrap;
  }
  .muted { color: var(--muted); }
  .lab { margin-bottom: 6px; }
  .why { margin: 0; font-size: 0.8rem; }
  .status {
    position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); color: var(--muted);
    padding: 8px 14px; border: 1px solid var(--border); z-index: 40; max-width: 90vw;
  }

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

  @media (min-width: 900px) {
    .stage { display: grid; grid-template-columns: 330px minmax(0, 1fr) 290px; }
    .controls { border-right: 1px solid var(--rule); min-height: 0; }
    .body { padding-top: 4px; }
  }

  @media (max-width: 899px) {
    .pane { position: absolute; inset: 0; }
    .controls {
      position: absolute; left: 0; right: 0; bottom: 0; border-top: 2px solid var(--rule); max-height: 48%;
      padding-bottom: env(safe-area-inset-bottom);
    }
    .controls.open { max-height: 86%; }
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
  }
</style>
