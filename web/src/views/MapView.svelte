<script lang="ts">
  // Single map: shade metric, reach, filters, quick card and statistics.
  // Desktop: controls left, map centre, card and statistics right. Phone: map with a bottom sheet.
  import { onMount, tick } from 'svelte';
  import Card from '../components/Card.svelte';
  import Legend from '../components/Legend.svelte';
  import MetricPicker from '../components/MetricPicker.svelte';
  import FilterPanel from '../components/FilterPanel.svelte';
  import LevelSwitch from '../components/LevelSwitch.svelte';
  import ReachControls from '../components/ReachControls.svelte';
  import RankTable, { type RankColumn } from '../components/RankTable.svelte';
  import SizeLegend from '../components/SizeLegend.svelte';
  import YearSlider from '../components/YearSlider.svelte';
  import StatsBlock from '../components/StatsBlock.svelte';
  import { buildScale, fmtNumber, fmtValue, isDiverging, sortedValues } from '../lib/classify';
  import type { ColumnStore } from '../lib/columns.svelte';
  import {
    gapReason, levelInfo, loadCH, loadReach, loadReachIndex, loadSeries, loadUnits, seriesPeriods, unavailableReason, type Base, type Hub, type LevelData,
    type MetricMeta, type ReachFile, type UnitRow,
  } from '../lib/data';
  import { catOptions, combine, evalFilter } from '../lib/filters';
  import { T_MAX, type CatField, type ReachMode } from '../lib/hash';
  import { CH_BOUNDS, UnitMap, zoomScale, type Symbol } from '../lib/mapview';
  import { ReachOverlay } from '../lib/reach';
  import { app } from '../lib/state.svelte';
  import { t } from '../lib/i18n.svelte';
  import { currentLevelNote, switchLevel } from '../lib/levels';
  import { profileHref, sourceHref } from '../lib/nav';
  import { refOf } from '../lib/places';
  import { divRamp, mute, seqRamp, token } from '../lib/theme';

  interface Props {
    base: Base;
    ld: LevelData;
    cols: ColumnStore;
    desktop: boolean;
    onrendered?: () => void;
  }
  let { base, ld, cols, desktop, onrendered }: Props = $props();

  const MIN_PER_SECOND = 30; // Play speed: 0 -> 180 min in 6 s
  /** radius in px of the largest value at the reference zoom, per level */
  const R_MAX: Record<string, number> = {
    gemeinde: 22, bezirk: 24, kanton: 30, grossregion: 36, sprachgebiet: 36, agglomeration: 26, arbeitsmarktgebiet: 24, stadt_land: 36,
  };

  let mapReady = $state(false);
  let hover = $state<number | null>(null);
  let hoverAt = $state<{ x: number; y: number } | null>(null);
  let sheetOpen = $state(false);
  let chA = $state.raw<{ value: number; period: string } | null>(null);
  let reachNets = $state.raw<Record<string, ReachFile | null>>({});
  let reachError = $state<string | null>(null);
  let hubs = $state.raw<Hub[]>([{ slug: 'zuerich', name: 'Zürich HB' }]);
  let carFiles = $state.raw<Set<string> | null>(null);
  let unitRows = $state.raw<UnitRow[] | null>(null);
  let zf = $state(1);
  let mapEl: HTMLDivElement;
  let panelEl = $state<HTMLElement>();
  let view: UnitMap | null = null;
  let overlay: ReachOverlay | null = null;

  const metas = $derived(base.metas);
  const li = $derived(levelInfo(ld.level));
  const word = $derived(li.label.toLowerCase());
  const aOne = $derived(`${/^[aeiou]/.test(li.one) ? 'an' : 'a'} ${li.one}`);
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
  const yearPeriods = $derived(seriesPeriods(metaA, ld.level));
  const yearEmpty = $derived(!!colA && refA?.file === null && !colA.v.some((x) => x !== null));
  // national value: latest file, or the series row of Switzerland for a past year
  $effect(() => {
    const m = metaA;
    const past = refA && refA.file === null ? refA.col.period : null;
    let live = true;
    chA = null;
    if (past) {
      loadSeries(m.id).then((s) => {
        const k = s ? s.periods.indexOf(past) : -1;
        const x = k >= 0 ? s!.levels.schweiz?.CH?.[k] : null;
        if (live) chA = x !== null && x !== undefined ? { value: x, period: past } : null;
      }).catch(() => {});
    } else {
      loadCH(m.file).then((f) => {
        if (!live) return;
        const c = f?.metrics[m.id];
        chA = c && c.v[0] !== null ? { value: c.v[0]!, period: c.period } : null;
      });
    }
    return () => (live = false);
  });

  // ------------------------------------------------------------------ size (proportional symbols)
  const symbolsMode = $derived(app.display === 'symbols');
  const sizeMeta = $derived<MetricMeta | undefined>(metas.get(app.size ?? (symbolsMode ? 'pop_total' : '')));
  const whyS = $derived(sizeMeta ? unavailableReason(sizeMeta, ld.level) : null);
  const sizeRef = $derived(sizeMeta && !whyS ? cols.get(ld, sizeMeta.id, app.year) : null);
  // units.json (names, label points, regions) is loaded once symbols or categorical filters are used
  const needRows = $derived(!!sizeMeta || app.filters.some((f) => f.kind === 'cat') || app.tab === 'rank');
  $effect(() => {
    if (needRows && !unitRows) loadUnits().then((u) => (unitRows = u));
  });
  const labels = $derived.by(() => {
    if (!unitRows) return null;
    const out: ([number, number] | null)[] = new Array(nUnits).fill(null);
    for (const r of unitRows) {
      if (r.level !== ld.level || !r.label) continue;
      const i = ld.index.get(r.id);
      if (i !== undefined) out[i] = r.label;
    }
    return out;
  });
  const sizeData = $derived.by(() => {
    if (!sizeRef || !labels) return null;
    const v = sizeRef.col.v;
    let vmax = 0, nMissing = 0, nNonPositive = 0;
    for (const x of v) {
      if (x === null) nMissing++;
      else if (x <= 0) nNonPositive++;
      else if (x > vmax) vmax = x;
    }
    if (!(vmax > 0)) return null;
    const rMax = R_MAX[ld.level] ?? 24;
    const syms: Symbol[] = [];
    for (let i = 0; i < v.length; i++) {
      const x = v[i];
      const p = labels[i];
      if (x !== null && x > 0 && p) syms.push({ i, lngLat: p, r: rMax * Math.sqrt(x / vmax) });
    }
    return { syms, vmax, rMax, nMissing, nNonPositive };
  });
  function setDisplay(d: 'choropleth' | 'symbols') {
    app.display = d;
    if (d === 'symbols' && !app.size) app.size = 'pop_total';
  }

  // ------------------------------------------------------------------ filters
  const hubName = (slug: string) => hubs.find((h) => h.slug === slug)?.name ?? slug;
  const evals = $derived(
    app.filters.map((f) =>
      evalFilter(f, { ld, rows: unitRows, metas, hubName, col: (id) => cols.get(ld, id, app.year) }),
    ),
  );
  const match = $derived(combine(evals, nUnits));
  const filtered = $derived(match.active > 0);
  const catOpts = (field: CatField) => catOptions(field, unitRows);

  // ------------------------------------------------------------------ reach
  const reachOn = $derived(app.reach !== 'off');
  const reachMode = $derived(app.reach as 'pt' | 'car');
  const hub = $derived(hubs.find((h) => h.slug === app.hub) ?? hubs[0]);
  const reachRef = $derived(reachOn && ld.level === 'gemeinde' ? cols.get(ld, `reach_${reachMode}_${hub.slug}`) : null);
  const reachCol = $derived(reachRef?.col ?? null);
  const reachFile = $derived(reachOn ? reachNets[`${hub.slug}_${reachMode}`] : undefined);
  const reachedCount = $derived.by(() => {
    if (!reachCol) return null;
    let n = 0;
    for (let i = 0; i < reachCol.v.length; i++) {
      const x = reachCol.v[i];
      if (x !== null && x <= app.t && match.m[i]) n++;
    }
    return n;
  });
  // car networks can be held back by the licence gate: the index lists the files of this build
  const carAvailable = $derived(carFiles ? carFiles.has(hub.slug) : reachNets[`${hub.slug}_car`] !== null);
  onMount(() => {
    loadReachIndex().then((ix) => {
      if (!ix) return;
      if (ix.hubs?.length) hubs = ix.hubs;
      carFiles = new Set(ix.files.filter((f) => f.mode === 'car').map((f) => f.hub));
    });
  });
  // the network of the chosen hub and mode, loaded on demand (one file per hub and mode)
  $effect(() => {
    if (!reachOn) return;
    const slug = hub.slug;
    const mode = reachMode;
    const key = `${slug}_${mode}`;
    if (key in reachNets) return;
    reachError = null;
    loadReach(slug, mode)
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
    view = new UnitMap(mapEl, base, {
      onSelect: select, onHover: (i, p) => { hover = i; hoverAt = i === null ? null : p; },
      onReset: () => fit(true), resetLabel: () => t('map.reset'),
    });
    overlay = new ReachOverlay(view.map, mapEl);
    view.map.on('zoom', () => (zf = zoomScale(view!.map.getZoom())));
    if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __map: unknown }).__map = view.map;
    view.ready.then(() => {
      mapReady = true;
      fit();
      zf = zoomScale(view!.map.getZoom());
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

  // 'show on map' from a profile: the first fits frame the selected place instead of all of Switzerland
  let focus = app.focusSel;
  app.focusSel = false;
  function fit(animate = false) {
    if (!view) return;
    if (animate) focus = false;
    let padding: { top: number; bottom: number; left: number; right: number };
    if (desktop) padding = { top: 24, bottom: 24, left: 24, right: 48 };
    else {
      const top = panelEl ? panelEl.getBoundingClientRect().top - mapEl.getBoundingClientRect().top : mapEl.clientHeight;
      padding = { top: 46, bottom: Math.max(12, mapEl.clientHeight - top + 8), left: 10, right: 10 };
    }
    view.map.resize();
    const f = focus && selIdx !== null ? ld.geo.features.find((x) => x.id === selIdx) : undefined;
    if (f) {
      view.map.resize();
      view.fitGeometry(f.geometry, padding);
      return;
    }
    view.map.fitBounds(CH_BOUNDS, { padding, animate, duration: animate ? 500 : 0 });
  }
  $effect(() => {
    void app.lang;
    if (mapReady) view!.relabel();
  });
  const levelNote = $derived(currentLevelNote());
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
    const d = app.display;
    if (mapReady) view!.setDisplay(d);
  });
  $effect(() => {
    const sd = sizeData;
    const style = symbolsMode ? 'filled' : 'hollow';
    void ld;
    if (mapReady) view!.setSymbols(sd ? sd.syms : null, style);
  });
  $effect(() => {
    const c = colours;
    const m = match.m;
    void ld;
    if (mapReady) view!.setColours(c, filtered ? m.map((x) => 1 - x) as Uint8Array : undefined);
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

  // ------------------------------------------------------------------ tabs and ranking
  const PHONE_TABS = [
    { id: 'map', label: 'Map' },
    { id: 'filters', label: 'Filters' },
    { id: 'rank', label: 'Ranking' },
    { id: 'stats', label: 'Statistics' },
  ];
  const phoneTab = $derived(PHONE_TABS.some((t) => t.id === app.tab) ? app.tab! : 'map');
  const deskTab = $derived(app.tab === 'rank' ? 'rank' : 'stats');
  function openTab(id: string) {
    app.tab = id === 'map' ? null : id;
    sheetOpen = true;
  }
  const rankCols = $derived.by(() => {
    const out: RankColumn[] = [];
    const seen = new Set<string>();
    const push = (key: string, tag: string, ref: { meta: MetricMeta; col: { v: (number | null)[]; period: string } } | null | undefined, label?: string) => {
      if (!ref || seen.has(key)) return;
      seen.add(key);
      out.push({ key, tag, meta: ref.meta, v: ref.col.v, period: ref.col.period, label });
    };
    if (!whyA) push(metaA.id, 'Shade', refA);
    if (sizeMeta) push(sizeMeta.id, 'Size', sizeRef);
    for (const e of evals) {
      if (e.status !== 'active' || !e.col) continue;
      if (e.filter.kind === 'reach') push(e.col.meta.id, 'Filter', e.col, `${e.filter.mode === 'pt' ? 'PT' : 'Car'} to ${e.hubName}`);
      else push(e.col.meta.id, 'Filter', e.col);
    }
    if (reachRef && reachCol) push(reachRef.meta.id, 'Reach', reachRef, `${reachMode === 'pt' ? 'PT' : 'Car'} to ${hub.name}`);
    return out;
  });
  const rankRows = $derived.by(() => {
    const out: number[] = [];
    for (let i = 0; i < nUnits; i++) if (match.m[i]) out.push(i);
    return out;
  });
  function selectFromList(i: number) {
    select(i);
    const p = labels?.[i];
    if (p && view) view.reveal(p);
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
          label, short: label, hub: hub.name, minutes: x,
          reason: x === null ? gapReason(reachRef.file, reachCol, selIdx, reachRef.meta, ld.canton[selIdx]) : null,
          within: x !== null && x <= app.t,
        };
      } else {
        const reason = ld.level !== 'gemeinde' ? 'per municipality only' : reachRef === null ? 'held back in this build' : 'loading…';
        reach = { label, short: label, hub: hub.name, minutes: null, reason, within: false };
      }
    }
    const i = selIdx;
    const sub = ld.level === 'gemeinde' ? `${ld.canton[i]} · BFS ${ld.units[i]}` : ld.level === 'kanton' ? li.one : `${li.one}${ld.canton[i] ? ` · ${ld.canton[i]}` : ''}`;
    const extra = [];
    if (sizeMeta && sizeRef && sizeMeta.id !== metaA.id) {
      const x = sizeRef.col.v[i];
      extra.push({ label: `Size: ${sizeMeta.label_en}`, value: x === null ? 'no data' : `${fmtValue(x, sizeMeta)} (${sizeRef.col.period})` });
    }
    return { i, reach, sub, extra };
  });
  const tip = $derived.by(() => {
    if (hover === null || !hoverAt || !colA) return null;
    const fmt = (x: number | null | undefined, m: MetricMeta) => (x === null || x === undefined ? 'no data' : fmtValue(x, m));
    const rows = [fmt(colA.v[hover], metaA)];
    if (sizeMeta && sizeRef && sizeMeta.id !== metaA.id) rows.push(`○ ${fmt(sizeRef.col.v[hover], sizeMeta)}`);
    return rows;
  });
</script>

{#snippet rankSnip()}
  {#if rankCols.length}
    <RankTable columns={rankCols} rows={rankRows} names={ld.name} cantons={ld.canton} showCanton={ld.level === 'gemeinde' || ld.level === 'bezirk'}
      sel={selIdx} unitWord={filtered ? `matching ${word}` : word} onselect={selectFromList} />
  {:else}
    <p class="foot">{whyA ?? 'Loading…'}</p>
  {/if}
{/snippet}
{#snippet statsSnip()}
  {#if colA && !whyA}
    <StatsBlock meta={metaA} v={colA.v} period={colA.period} names={ld.name} cantons={ld.canton} ch={chA} sel={null}
      source={base.sources.get(metaA.source)} unitWord={word} />
  {:else}
    <p class="foot">{whyA ?? 'Loading…'}</p>
  {/if}
{/snippet}

<main class="stage">
  <aside class="controls" class:open={sheetOpen} bind:this={panelEl} aria-label="Map controls">
    <button type="button" class="handle" aria-expanded={sheetOpen} onclick={() => (sheetOpen = !sheetOpen)}>
      <svg class="chev" class:up={!sheetOpen} viewBox="0 0 20 12" width="20" height="12" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
      <span class="summary">
        {(filtered ? `${fmtNumber(match.n, 0)} of ${fmtNumber(nUnits, 0)} match · ` : '') + (sheetOpen ? 'Less' : 'More')}
      </span>
    </button>
    {#if !desktop}
      <div class="tabs sheet-tabs" role="tablist" aria-label="Panel">
        {#each PHONE_TABS as tb}
          <button type="button" role="tab" aria-selected={phoneTab === tb.id} onclick={() => openTab(tb.id)}>
            {tb.label}{#if tb.id === 'filters' && app.filters.length}&nbsp;<span class="badge num">{app.filters.length}</span>{/if}
          </button>
        {/each}
      </div>
    {/if}
    <div class="body">
      {#if desktop || phoneTab === 'map'}
      <section>
        <div class="row2 lab">
          <span class="caps">Shade by</span>
        </div>
        <MetricPicker metrics={base.metrics} level={ld.level} value={metaA.id} onpick={(id) => (app.metric = id)} />
        <div class="legend-wrap">
          {#if whyA}
            <p class="why">{whyA}</p>
          {:else if scaleA && colA}
            <Legend meta={metaA} v={colA.v} period={colA.period} scale={scaleA} {nUnits} unitWord={word} source={base.sources.get(metaA.source)}
              method={app.cls} onmethod={(m) => (app.cls = m)} compact={!desktop && !sheetOpen} />
          {:else if colA && !scaleA}
            <p class="why">No values for {colA.period} at this level.</p>
          {:else if refA === undefined}
            <p class="foot">Loading…</p>
          {/if}
        </div>
        {#if yearPeriods.length > 1 && !whyA}
          <div class="yr" class:extra={!app.year}>
            <YearSlider periods={yearPeriods} value={app.year} onchange={(y) => (app.year = y)}>
              {#if refA?.noSeries}{' · '}<span class="warn">no time series for this metric in this build; latest shown</span>
              {:else if refA?.yearMissing}{' · '}<span class="warn">no {refA.yearMissing} value; latest shown</span>
              {:else if yearEmpty}{' · '}<span class="warn">no value for {app.year} at this level</span>{/if}
            </YearSlider>
          </div>
        {:else if app.year && !whyA}
          <p class="foot yr">Year {app.year}: this metric has no time series {li.series ? '' : 'at this level '}— latest shown.
            <button type="button" class="link" onclick={() => (app.year = null)}>Back to latest</button></p>
        {/if}
      </section>

      <section class="extra">
        <div class="row2">
          <span class="caps">Size by</span>
          <div class="seg" role="radiogroup" aria-label="Map type">
            <button type="button" role="radio" aria-checked={!symbolsMode} onclick={() => setDisplay('choropleth')}>Choropleth</button>
            <button type="button" role="radio" aria-checked={symbolsMode} onclick={() => setDisplay('symbols')}>Symbols</button>
          </div>
        </div>
        <MetricPicker metrics={base.metrics} level={ld.level} value={sizeMeta?.id ?? ''} none={symbolsMode ? undefined : 'None'}
          onpick={(id) => (app.size = id || null)} />
        {#if whyS}
          <p class="why sp">{whyS}</p>
        {:else if sizeMeta && sizeData && sizeRef}
          <div class="sp">
            <SizeLegend meta={sizeMeta} period={sizeRef.col.period} vmax={sizeData.vmax} rmax={sizeData.rMax * zf} filled={symbolsMode}
              nDrawn={sizeData.syms.length} nMissing={sizeData.nMissing} nNonPositive={sizeData.nNonPositive} unitWord={word} />
          </div>
        {:else if sizeMeta}
          <p class="foot sp">Loading…</p>
        {/if}
        <p class="foot sp">
          {#if symbolsMode}Circles at each {li.one}'s label point take the shade colour; the polygons are grey.
          {:else if sizeMeta}Rings over the shaded map. “Symbols” draws filled circles in the shade colour instead.
          {:else}Optional: a second metric as circle size.{/if}
        </p>
      </section>

      <section class="reach">
        <ReachControls {hubs} hub={hub.slug} mode={app.reach} t={app.t} playing={app.playing} {carAvailable}
          onhub={(slug) => { stop(); app.hub = slug; }} onmode={setReach} ont={(v) => { stop(); app.t = v; }} onplay={play}>
          {#if reachError}
            Reach data could not be loaded: {reachError}
          {:else if reachFile === undefined || reachRef === undefined}
            Loading network…
          {:else if reachFile === null}
            No {reachMode === 'car' ? 'car' : 'public transport'} network for {hub.name} in this build.
          {:else}
            {#if reachedCount !== null}<span class="num">{fmtNumber(reachedCount, 0)}</span> municipalities within {Math.round(app.t)} min{filtered ? ' (among the filtered)' : ''}; others shown desaturated.
            {:else if ld.level !== 'gemeinde'}Travel times are per municipality: the network is drawn, units are not highlighted at this level.
            {:else}Municipality times are held back in this build; only the network is drawn.{/if}
            <span class="foot detail">{reachMode === 'pt' ? `Weekday departure ${reachFile.departure ?? ''} from ${hub.name}, wait at the hub included. Own routing on the national GTFS timetable.` : 'Average weekday, ARE NPVM 2023.'}</span>
          {/if}
        </ReachControls>
      </section>

      {/if}
      {#if desktop || phoneTab === 'filters'}
      <section>
        <div class="caps lab">Filters</div>
        <FilterPanel {evals} {match} total={nUnits} unitWord={word} level={ld.level} metrics={base.metrics} {hubs}
          options={catOpts} defaultMetric={app.filters.some((f) => f.kind === 'num' && f.metric === metaA.id) ? 'pop_total' : metaA.id}
          defaultHub={hub.slug} onset={(fs) => (app.filters = fs)} />
      </section>

      {/if}
      {#if !desktop && phoneTab === 'rank'}
        <section>{@render rankSnip()}</section>
      {/if}
      {#if !desktop && phoneTab === 'stats'}
        <section>{@render statsSnip()}</section>
      {/if}
    </div>
  </aside>

  <section class="pane">
    <div class="mapbox">
      <div class="map" bind:this={mapEl}></div>
      <div class="lvlbar">
        <LevelSwitch value={ld.level} onchange={(l) => { stop(); switchLevel(base, l); }} />
        {#if levelNote}
          <p class="lnote" role="status">{levelNote}
            <button type="button" class="lx" aria-label={t('common.dismiss')} onclick={() => (app.levelNote = null)}>×</button></p>
        {/if}
      </div>
      {#if tip && hover !== null && hoverAt && desktop}
        <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
          <strong>{ld.name[hover]}</strong>{#if ld.canton[hover] && ld.level !== 'kanton' && !ld.name[hover].includes('(')}&nbsp;<span class="muted">{ld.canton[hover]}</span>{/if}
          {#each tip as r}<div class="num">{r}</div>{/each}
        </div>
      {/if}
    </div>
  </section>

  {#if desktop}
    <aside class="side" aria-label="Statistics">
      {#if card && refA && colA}
        <div class="caps lab">Selected {li.one}</div>
        <Card name={ld.name[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
          source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} extra={card.extra} docked onclose={() => (app.sel = null)}
          profile={profileHref(refOf(ld.level, ld.units[card.i]))} profileLabel={t('card.profile')} sourceLink={sourceHref(metaA.source)} />
      {:else}
        <p class="foot hint">Tap or click {aOne} for its value, rank and percentile.</p>
      {/if}
      <div class="tabs side-tabs" role="tablist" aria-label="Side panel">
        <button type="button" role="tab" aria-selected={deskTab === 'rank'} onclick={() => (app.tab = 'rank')}>Ranking</button>
        <button type="button" role="tab" aria-selected={deskTab === 'stats'} onclick={() => (app.tab = null)}>Statistics</button>
      </div>
      <div class="sblock">
        {#if deskTab === 'rank'}{@render rankSnip()}{:else}{@render statsSnip()}{/if}
      </div>
    </aside>
  {/if}

  {#if !desktop && card && refA && colA}
    <div class="card-wrap">
      <Card name={ld.name[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
        source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} extra={card.extra} onclose={() => (app.sel = null)}
        profile={profileHref(refOf(ld.level, ld.units[card.i]))} profileLabel={t('card.profile')} sourceLink={sourceHref(metaA.source)} />
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
  .yr { margin-top: 10px; }
  .warn { color: var(--text); }
  .link { border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: inherit; color: var(--text); }
  .row2 { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
  .row2 > .caps { flex: none; white-space: nowrap; }
  .row2 .seg button { padding: 3px 8px; font-size: 0.76rem; }
  .sp { margin-top: 8px; }
  p.sp { margin-bottom: 0; }
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
  .reach .detail { display: block; margin-top: 3px; }
  .side { background: var(--panel); border-left: 1px solid var(--rule); padding: 14px 16px; overflow-y: auto; }
  .sblock { margin-top: 10px; }
  .tabs { display: flex; border-bottom: 1px solid var(--ink); }
  .tabs button {
    flex: 1; padding: 6px 4px; border: 0; background: none; cursor: pointer; font-size: 0.78rem; font-weight: 600; color: var(--muted);
    border-bottom: 3px solid transparent; margin-bottom: -1px;
  }
  .tabs button[aria-selected='true'] { color: var(--text); border-bottom-color: var(--ink); }
  .side-tabs { margin-top: 18px; border-top: 1px solid var(--rule); }
  .badge { display: inline-grid; place-items: center; min-width: 16px; height: 16px; padding: 0 3px; background: var(--ink); color: var(--ink-text); font-size: 0.66rem; }
  .hint { margin: 0; }
  .card-wrap { position: absolute; z-index: 6; top: 8px; left: 8px; right: 8px; max-width: 440px; margin: 0 auto; }
  .lvlbar { position: absolute; z-index: 3; top: 10px; left: 10px; right: 56px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px; pointer-events: none; }
  .lvlbar > :global(*) { pointer-events: auto; }
  .lnote {
    margin: 0; max-width: 420px; background: var(--panel); border: 1px solid var(--ink); padding: 4px 4px 4px 8px; font-size: 0.76rem;
    display: flex; align-items: flex-start; gap: 6px;
  }
  .lx { border: 0; background: none; cursor: pointer; font-size: 1rem; line-height: 1; padding: 0 4px; color: var(--text); }

  @media (min-width: 900px) {
    .stage { display: grid; grid-template-columns: 330px minmax(0, 1fr) 320px; }
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
    .sheet-tabs { flex: none; padding: 0 12px; }
    .sheet-tabs button { padding: 5px 2px 6px; }
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
    .controls:not(.open) .detail { display: none; }
    /* zoom buttons hidden on phones (pinch); the reset button stays */
    :global(.single .maplibregl-ctrl-top-right .maplibregl-ctrl-group:not(.gb-reset)) { display: none; }
    .lvlbar { top: 8px; left: 8px; }
    .card-wrap { top: 48px; }
  }
</style>
