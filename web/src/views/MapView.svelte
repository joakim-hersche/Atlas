<script lang="ts">
  // Single map: shade metric, reach, filters, quick card and statistics.
  // Desktop: controls left, map centre, card and statistics right. Phone: map with a bottom sheet.
  import { onMount, tick } from 'svelte';
  import Card from '../components/Card.svelte';
  import Legend from '../components/Legend.svelte';
  import MetricPicker from '../components/MetricPicker.svelte';
  import FilterPanel from '../components/FilterPanel.svelte';
  import LevelSwitch from '../components/LevelSwitch.svelte';
  import LevelNote from '../components/LevelNote.svelte';
  import ReachControls from '../components/ReachControls.svelte';
  import RankTable, { type RankColumn } from '../components/RankTable.svelte';
  import SizeLegend from '../components/SizeLegend.svelte';
  import YearSlider from '../components/YearSlider.svelte';
  import VotePicker from '../components/VotePicker.svelte';
  import VoteResult from '../components/VoteResult.svelte';
  import { loadVoteFile, loadVoteIndex, voteIdOf, type VoteIndex } from '../lib/votes';
  import StatsBlock from '../components/StatsBlock.svelte';
  import { buildScale, divergeCentre, fmtNumber, fmtPeriod, fmtTick, fmtValue, isDiverging, legendItems, sortedValues } from '../lib/classify';
  import { bareAttribution, downloadBlob, figurePNG, grabMap, slug, type LegendItem } from '../lib/export';
  import { describeFilter } from '../lib/filters';
  import { precisionText } from '../lib/data';
  import type { ColumnStore } from '../lib/columns.svelte';
  import {
    gapReason, levelInfo, loadCH, loadReach, loadReachIndex, loadSeries, loadUnits, seriesPeriods, unavailableReason, type Base, type Hub, type LevelData,
    type MetricMeta, type ReachFile, type UnitRow,
  } from '../lib/data';
  import { catOptions, combine, evalFilter } from '../lib/filters';
  import { T_MAX, type CatField, type ReachMode } from '../lib/hash';
  import { CH_BOUNDS, UnitMap, geomBounds, zoomScale, type Symbol } from '../lib/mapview';
  import { ReachOverlay } from '../lib/reach';
  import { app } from '../lib/state.svelte';
  import { levelName, ml, t, levelWord } from '../lib/i18n.svelte';
  import { switchLevel } from '../lib/levels';
  import { profileHref, sourceHref } from '../lib/nav';
  import { loadReachTimes, refOf, type ReachTimes } from '../lib/places';
  import { hasStation, kindLabel, mainStation, methodText, ptKind, reachId, reachReason, type ReachKind } from '../lib/pt';
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
  /** map fills the viewport (header, panels hidden); not in the hash */
  let full = $state(false);
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
  const word = $derived(levelWord(ld.level));
  const one = $derived(levelName(ld.level, false));
    const nUnits = $derived(ld.units.length);

  // ------------------------------------------------------------------ shade metric
  const metaRaw = $derived<MetricMeta>(metas.get(app.metric) ?? metas.get('pop_total')!);
  const whyA = $derived(unavailableReason(metaRaw, ld.level));
  const refRaw = $derived(cols.get(ld, metaRaw.id, app.year));

  // federal votes (D32): any vote from the index; yes share optionally as the difference from Switzerland
  let voteIx = $state.raw<VoteIndex | null>(null);
  $effect(() => {
    // only builds whose metrics.json announces the vote index have one (no request otherwise)
    if (metaRaw.per_vote && metaRaw.vote_index && !voteIx) loadVoteIndex().then((ix) => (voteIx = ix));
  });
  const voteShown = $derived(refRaw && metaRaw.per_vote ? voteIdOf(refRaw.col.period) : null);
  const voteEntry = $derived(voteIx && voteShown ? (voteIx.votes.find((v) => v.id === voteShown) ?? null) : null);
  const vdiff = $derived(app.vdiff && metaRaw.id === 'vote_yes_share' && !!chA && !!refRaw);
  const metaA = $derived<MetricMeta>(
    vdiff
      ? { ...metaRaw, id: 'vote_yes_share_diff', label_en: t('vt.diffLabelEn'), label_de: t('vt.diffLabelDe'), label_fr: t('vt.diffLabelFr'),
          unit: 'pp', unit_de: 'Pp.', unit_fr: 'pp', aggregation: 'change:vote_yes_share', direction: 'neutral', decimals: 1, headline: null }
      : metaRaw,
  );
  const refA = $derived(
    vdiff && refRaw && chA
      ? { ...refRaw, meta: metaA, col: { ...refRaw.col, v: refRaw.col.v.map((x) => (x === null ? null : Math.round((x - chA!.value) * 100) / 100)) } }
      : refRaw,
  );
  const colA = $derived(refA?.col);
  const scaleA = $derived.by(() => {
    if (!colA) return null;
    const s = sortedValues(colA.v);
    return s.length ? buildScale(colA.v, app.cls, isDiverging(metaA, s), seqRamp(), divRamp(), divergeCentre(metaA)) : null;
  });
  const yearPeriods = $derived(seriesPeriods(metaRaw, ld.level));
  /** a count (sum) as a choropleth favours large units: suggest circles */
  const countHint = $derived(metaA.aggregation === 'sum' && app.display === 'choropleth' && app.size !== metaA.id && !whyA);
  function countAsSymbols() {
    app.size = metaA.id;
    app.display = 'symbols';
  }
  const yearEmpty = $derived(!!colA && refA?.file === null && !colA.v.some((x) => x !== null));
  // national value: latest file, the series row of Switzerland for a past year, or the chosen vote
  $effect(() => {
    const m = metaRaw;
    const ref = refRaw;
    const past = ref && ref.file === null ? ref.col.period : null;
    let live = true;
    chA = null;
    if (past && m.per_vote) {
      const id = voteIdOf(past);
      loadVoteIndex().then((ix) => {
        const e = ix?.votes.find((v) => v.id === id);
        if (!e || !live) return;
        const known = m.id === 'vote_yes_share' ? e.yes_pct : m.id === 'vote_turnout' ? e.turnout_pct : null;
        if (known !== null && known !== undefined) {
          chA = { value: known, period: past };
          return;
        }
        loadVoteFile(e.file).then((f) => {
          const row = f?.levels.schweiz?.[m.id];
          const x = row ? (row.CH ?? Object.values(row)[0]) : null;
          if (live) chA = x !== null && x !== undefined ? { value: x, period: past } : null;
        });
      });
    } else if (past) {
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
  /** D31: station times in this build; the PT measure on the map (station time or door to door) */
  const station = $derived(hasStation(metas));
  const reachKind = $derived<ReachKind>(reachMode === 'car' ? 'car' : ptKind(metas));
  const reachRef = $derived(reachOn && ld.level === 'gemeinde' ? cols.get(ld, reachId(reachKind, hub.slug)) : null);
  // both PT measures for the card and the ranking (station headline + door to door)
  const stRef = $derived(reachOn && reachMode === 'pt' && station && ld.level === 'gemeinde' ? cols.get(ld, reachId('ptst', hub.slug)) : null);
  const ddRef = $derived(reachOn && reachMode === 'pt' && station && ld.level === 'gemeinde' ? cols.get(ld, reachId('pt', hub.slug)) : null);
  // reach_times.json: main station names, method texts and reasons for missing times (D31)
  let rt = $state.raw<ReachTimes | null>(null);
  $effect(() => {
    if ((reachOn || app.filters.some((f) => f.kind === 'reach')) && !rt) loadReachTimes().then((x) => (rt = x)).catch(() => {});
  });
  const rtIndex = $derived(rt ? new Map(rt.units.map((u, k) => [u, k])) : undefined);
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
      if (ix.hubs?.length) {
        hubs = ix.hubs;
        const known = new Set(ix.hubs.map((h) => h.slug));
        if (!known.has(app.hub)) app.hub = ix.hubs[0].slug;
        const fs = app.filters.filter((f) => f.kind !== 'reach' || known.has(f.hub));
        if (fs.length !== app.filters.length) app.filters = fs;
      }
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
  // a selection or hub from a link that does not exist here is dropped (the hash follows)
  $effect(() => {
    if (app.sel !== null && !ld.index.has(app.sel)) app.sel = null;
  });
  function select(i: number | null) {
    app.sel = i === null ? null : ld.units[i];
    if (i !== null && !desktop) sheetOpen = false;
  }

  // ------------------------------------------------------------------ map
  onMount(() => {
    view = new UnitMap(mapEl, base, {
      onSelect: select, onHover: (i, p) => { hover = i; hoverAt = i === null ? null : p; },
      onReset: () => fit(true), resetLabel: () => t('map.reset'),
      onFull: () => setFull(!full), fullLabel: () => t(full ? 'map.fullExit' : 'map.full'), isFull: () => full,
    });
    overlay = new ReachOverlay(view.map, mapEl);
    view.map.on('zoom', () => (zf = zoomScale(view!.map.getZoom())));
    view.map.on('movestart', (e) => {
      if ((e as { originalEvent?: unknown }).originalEvent) userMoved = true;
    });
    if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __map: unknown }).__map = view.map;
    view.ready.then(() => {
      mapReady = true;
      fit();
      zf = zoomScale(view!.map.getZoom());
      view!.map.once('idle', () => onrendered?.());
    });
    const ro = new ResizeObserver(() => view?.map.resize());
    ro.observe(mapEl);
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && full && setFull(false);
    window.addEventListener('keydown', esc);
    return () => {
      ro.disconnect();
      stop();
      window.removeEventListener('keydown', esc);
      document.documentElement.classList.remove('mapfull');
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
    padding = mapPadding();
    view.map.resize();
    const f = focus && selIdx !== null ? ld.geo.features.find((x) => x.id === selIdx) : undefined;
    if (f) {
      view.map.resize();
      view.fitGeometry(f.geometry, padding);
      return;
    }
    view.map.fitBounds(CH_BOUNDS, { padding, animate, duration: animate ? 500 : 0 });
    userMoved = false;
  }
  function mapPadding() {
    if (desktop) return { top: 24, bottom: 24, left: 24, right: 48 };
    // phone: the level bar on top; the sheet sits below the map (it does not cover it)
    return { top: 46, bottom: 12, left: 10, right: 10 };
  }
  /** the user panned or zoomed since the last fit: then a resize keeps their view */
  let userMoved = false;
  /** Zoom to a set of units (matches, a ranking row). */
  const boxes = $derived(ld.geo.features.map((f) => geomBounds(f.geometry)));
  function zoomTo(idx: number[], maxZoom = 10.5) {
    if (!view || !idx.length) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const byId = new Map(ld.geo.features.map((f, k) => [f.id as number, k]));
    for (const i of idx) {
      const k = byId.get(i);
      const b = k === undefined ? null : boxes[k];
      if (!b) continue;
      x0 = Math.min(x0, b[0]); y0 = Math.min(y0, b[1]); x1 = Math.max(x1, b[2]); y1 = Math.max(y1, b[3]);
    }
    if (!Number.isFinite(x0)) return;
    if (!desktop) sheetOpen = false;
    tick().then(() => {
      view!.map.resize();
      view!.fitBox([x0, y0, x1, y1], mapPadding(), { animate: true, maxZoom });
    });
  }
  const matchIdx = $derived.by(() => {
    const out: number[] = [];
    for (let i = 0; i < nUnits; i++) if (match.m[i]) out.push(i);
    return out;
  });
  function setFull(v: boolean) {
    full = v;
    document.documentElement.classList.toggle('mapfull', v);
    if (v) sheetOpen = false;
    tick().then(() => requestAnimationFrame(() => {
      view?.relabel();
      if (!userMoved) fit();
      else view?.map.resize();
    }));
  }
  $effect(() => {
    void app.lang;
    if (mapReady) view!.relabel();
  });
  $effect(() => {
    void desktop;
    if (mapReady) tick().then(() => requestAnimationFrame(() => fit()));
  });
  $effect(() => {
    void sheetOpen;
    requestAnimationFrame(() => {
      view?.map.resize();
      if (mapReady && !desktop && !userMoved && !focus) fit();
    });
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
    // phones: the sheet folds away so the growing network stays in view
    if (!desktop) sheetOpen = false;
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
    { id: 'map', label: 'tab.map' },
    { id: 'filters', label: 'tab.filters' },
    { id: 'rank', label: 'tab.rank' },
    { id: 'stats', label: 'tab.stats' },
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
      if (e.filter.kind === 'reach') push(e.col.meta.id, 'Filter', e.col, t('mv.to', { mode: kindLabel(e.filter.mode, station, true), hub: e.hubName ?? '' }));
      else push(e.col.meta.id, 'Filter', e.col);
    }
    if (reachMode === 'pt' && station) {
      if (stRef) push(stRef.meta.id, 'Reach', stRef, t('mv.to', { mode: kindLabel('ptst', true), hub: hub.name }));
      if (ddRef) push(ddRef.meta.id, 'Reach', ddRef, t('mv.to', { mode: kindLabel('pt', true, true), hub: hub.name }));
    } else if (reachRef && reachCol) push(reachRef.meta.id, 'Reach', reachRef, t('mv.to', { mode: kindLabel(reachKind, station), hub: hub.name }));
    return out;
  });
  const rankRows = $derived.by(() => {
    const out: number[] = [];
    for (let i = 0; i < nUnits; i++) if (match.m[i]) out.push(i);
    return out;
  });
  function selectFromList(i: number) {
    select(i);
    zoomTo([i], ld.level === 'gemeinde' ? 9.5 : 8.5);
  }

  // ------------------------------------------------------------------ PNG export (D32)
  let pngBusy = $state(false);
  async function mapPNG() {
    if (!view || !scaleA || !colA || pngBusy) return;
    pngBusy = true;
    try {
      const img = await grabMap(view.map);
      const layers = [img];
      const rc = reachOn ? (mapEl.querySelector('canvas.reach-canvas') as HTMLCanvasElement | null) : null;
      if (rc) layers.push(rc);
      const legend: LegendItem[] = legendItems(scaleA, metaA);
      if (scaleA.n < nUnits) legend.push({ colour: null, label: t('lg.noData') });
      if (filtered) legend.push({ colour: mute(scaleA.classColours[2] ?? '#6290bb', token('--map-bg'), 0.88), label: t('ex.notMatching') });
      const lo = scaleA.lo, hi = scaleA.hi;
      const gradient = scaleA.method === 'continuous'
        ? { colours: Array.from({ length: 9 }, (_, k) => scaleA!.colourOf(lo + ((hi - lo) * k) / 8)), lo: fmtTick(lo, metaA), hi: fmtTick(hi, metaA) }
        : null;
      const src = base.sources.get(metaA.source);
      const sub = [metaA.unit, fmtPeriod(colA.period), levelName(ld.level), t(`lg.m.${app.cls}`)].filter(Boolean).join(' · ');
      const extra: string[] = [];
      if (filtered) extra.push(`${t('tab.filters')}: ${evals.map((e) => describeFilter(e, (f, id) => catOpts(f).find((o) => o.id === id)?.name ?? id)).join('; ')} (${t('mv.nMatch', { n: fmtNumber(match.n, 0), total: fmtNumber(nUnits, 0) })})`);
      if (reachOn) extra.push(`${t('rc.from')} ${hub.name}: ${kindLabel(reachKind, station, true)} ≤ ${Math.round(app.t)} min. ${methodText(reachKind, hub.name, rt, station)}`);
      const blob = await figurePNG({
        layers, scale: img.width / Math.max(1, mapEl.clientWidth), title: ml(metaA), subtitle: [sub, ...extra].join('\n'),
        legend: gradient ? [] : legend, gradient,
        credits: [
          `${t('lg.source')}: ${bareAttribution(src?.attribution || src?.publisher || metaA.source)} · ${fmtPeriod(colA.period)} · ${precisionText(metaA.precision)}`,
          `${t('ex.boundaries')} · ${t('ex.made')}`,
        ],
        link: t('ex.view', { url: location.href }),
      });
      downloadBlob(blob, `gemeindebank-${slug(ml(metaA))}-${slug(colA.period)}.png`);
    } finally {
      pngBusy = false;
    }
  }

  // ------------------------------------------------------------------ card and tooltip
  const card = $derived.by(() => {
    if (selIdx === null || !refA || whyA) return null;
    let reach = null;
    if (reachOn) {
      const label = reachMode === 'pt' ? t('rc.pt') : t('common.car');
      const uid = ld.units[selIdx];
      const miss = (ref: typeof reachRef, kind: ReachKind) => {
        if (!ref) return ref === undefined ? t('status.loading') : t('mv.heldBack');
        return reachReason(rt, kind, uid, rtIndex) ?? gapReason(ref.file, ref.col, selIdx, ref.meta, ld.canton[selIdx]);
      };
      if (reachMode === 'pt' && station && ld.level === 'gemeinde') {
        // D31: station time towards the hub as the headline, door to door as the second line
        const st = stRef?.col.v[selIdx] ?? null;
        const dd = ddRef?.col.v[selIdx] ?? null;
        const x = reachKind === 'ptst' ? st : dd;
        reach = {
          label, short: label, hub: hub.name, minutes: x, within: x !== null && x <= app.t, reason: null,
          station: { minutes: st, from: mainStation(rt, uid, rtIndex), reason: st === null ? miss(stRef, 'ptst') : null, name: ld.name[selIdx] },
          door: { minutes: dd, reason: dd === null ? miss(ddRef, 'pt') : null },
          active: reachKind,
          method: methodText(reachKind, hub.name, rt, true),
        };
      } else if (reachRef && reachCol) {
        const x = reachCol.v[selIdx];
        reach = {
          label, short: label, hub: hub.name, minutes: x,
          reason: x === null ? miss(reachRef, reachKind) : null,
          within: x !== null && x <= app.t,
          // before the D31 data, public transport is measured from the hub outwards
          outward: reachMode === 'pt',
        };
      } else {
        const reason = ld.level !== 'gemeinde' ? t('mv.perGem') : reachRef === null ? t('mv.heldBack') : t('status.loading');
        reach = { label, short: label, hub: hub.name, minutes: null, reason, within: false };
      }
    }
    const i = selIdx;
    const sub = ld.level === 'gemeinde' ? `${ld.canton[i]} · BFS ${ld.units[i]}` : ld.level === 'kanton' ? one : `${one}${ld.canton[i] ? ` · ${ld.canton[i]}` : ''}`;
    const extra = [];
    if (sizeMeta && sizeRef && sizeMeta.id !== metaA.id) {
      const x = sizeRef.col.v[i];
      extra.push({ label: `${t('mv.size')}: ${ml(sizeMeta)}`, value: x === null ? t('lg.noData') : `${fmtValue(x, sizeMeta)} (${sizeRef.col.period})` });
    }
    return { i, reach, sub, extra };
  });
  const tip = $derived.by(() => {
    if (hover === null || !hoverAt || !colA) return null;
    const fmt = (x: number | null | undefined, m: MetricMeta) => (x === null || x === undefined ? t('lg.noData') : fmtValue(x, m));
    const rows = [fmt(colA.v[hover], metaA)];
    if (sizeMeta && sizeRef && sizeMeta.id !== metaA.id) rows.push(`○ ${fmt(sizeRef.col.v[hover], sizeMeta)}`);
    return rows;
  });
</script>

{#snippet rankSnip()}
  {#if rankCols.length}
    <RankTable columns={rankCols} rows={rankRows} names={ld.name} cantons={ld.canton} showCanton={ld.level === 'gemeinde' || ld.level === 'bezirk'}
      sel={selIdx} unitWord={filtered ? t('mv.matching', { units: word }) : word} onselect={selectFromList} ids={ld.units}
      sourceName={(id) => base.sources.get(id)?.publisher.split(' (')[0] ?? id}
      onzoom={filtered && match.n > 0 ? () => zoomTo(matchIdx) : undefined} />
  {:else}
    <p class="foot">{whyA ?? t('status.loading')}</p>
  {/if}
{/snippet}
{#snippet statsSnip()}
  {#if voteIx && voteEntry && !whyA}<VoteResult index={voteIx} entry={voteEntry} />{/if}
  {#if colA && !whyA}
    <StatsBlock meta={metaA} v={colA.v} period={colA.period} names={ld.name} cantons={ld.canton} ch={vdiff && chA ? { value: 0, period: chA.period } : chA} sel={null}
      source={base.sources.get(metaA.source)} unitWord={word} mask={filtered ? match.m : null} />
  {:else}
    <p class="foot">{whyA ?? t('status.loading')}</p>
  {/if}
{/snippet}

<main class="stage" class:full id="main" tabindex="-1">
  <h1 class="sr-only">{t('mv.h1', { metric: ml(metaA), units: levelName(ld.level) })}</h1>
  <aside class="controls" class:open={sheetOpen} bind:this={panelEl} aria-label={t('mv.controls')}>
    <button type="button" class="handle" aria-expanded={sheetOpen} onclick={() => (sheetOpen = !sheetOpen)}>
      <svg class="chev" class:up={!sheetOpen} viewBox="0 0 20 12" width="20" height="12" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
      <span class="summary">
        {(filtered ? `${t('mv.nMatch', { n: fmtNumber(match.n, 0), total: fmtNumber(nUnits, 0) })} · ` : '') + (sheetOpen ? t('mv.less') : t('mv.more'))}
      </span>
    </button>
    {#if !desktop}
      <div class="tabs sheet-tabs" role="tablist" aria-label={t('mv.panel')}>
        {#each PHONE_TABS as tb}
          <button type="button" role="tab" aria-selected={phoneTab === tb.id} onclick={() => openTab(tb.id)}>
            {t(tb.label)}{#if tb.id === 'filters' && app.filters.length}&nbsp;<span class="badge num">{app.filters.length}</span>{/if}
          </button>
        {/each}
      </div>
    {/if}
    <div class="body">
      {#if desktop || phoneTab === 'map'}
      <section>
        <div class="row2 lab">
          <span class="caps">{t('mv.shade')}</span>
        </div>
        <MetricPicker metrics={base.metrics} level={ld.level} value={metaRaw.id} onpick={(id) => (app.metric = id)} />
        {#if metaRaw.per_vote && voteIx && voteShown}
          <VotePicker index={voteIx} value={voteShown} onpick={(id) => (app.vote = voteIdOf(metaRaw.latest) === id ? null : id)} />
        {/if}
        {#if metaRaw.id === 'vote_yes_share' && !whyA}
          <div class="seg vd" role="radiogroup" aria-label={t('vt.view')}>
            <button type="button" role="radio" aria-checked={!app.vdiff} onclick={() => (app.vdiff = false)}>{t('vt.share')}</button>
            <button type="button" role="radio" aria-checked={app.vdiff} disabled={!chA} title={chA ? '' : t('st.noCH')} onclick={() => (app.vdiff = true)}>{t('vt.diff')}</button>
          </div>
        {/if}
        {#if refRaw?.voteMissing}<p class="foot">{t('vt.missing')}</p>{/if}
        <div class="legend-wrap">
          {#if whyA}
            <p class="why">{whyA}</p>
          {:else if scaleA && colA}
            <Legend meta={metaA} v={colA.v} period={colA.period} scale={scaleA} {nUnits} unitWord={word} source={base.sources.get(metaA.source)}
              method={app.cls} onmethod={(m) => (app.cls = m)} compact={!desktop && !sheetOpen} />
          {:else if colA && !scaleA}
            <p class="why">No values for {colA.period} at this level.</p>
          {:else if refA === undefined}
            <p class="foot">{t('status.loading')}</p>
          {/if}
          {#if scaleA && colA && !whyA}
            <p class="exrow"><button type="button" class="exb" onclick={mapPNG} disabled={pngBusy} title={t('ex.pngT')}>{pngBusy ? t('ex.pngWait') : t('ex.pngMap')}</button></p>
          {/if}
          {#if countHint}
            <p class="hintc">{t('mv.countHint', { metric: ml(metaA) })}
              <button type="button" class="link" onclick={countAsSymbols}>{t('mv.countBtn')}</button></p>
          {/if}
        </div>
        {#if yearPeriods.length > 1 && !whyA}
          <div class="yr" class:extra={!app.year}>
            <YearSlider periods={yearPeriods} value={app.year} onchange={(y) => (app.year = y)}>
              {#if refA?.noSeries}{' · '}<span class="warn">{t('mv.noSeries')}</span>
              {:else if refA?.yearMissing}{' · '}<span class="warn">{t('mv.noYearVal', { y: refA.yearMissing })}</span>
              {:else if yearEmpty}{' · '}<span class="warn">{t('mv.noYearLevel', { y: app.year ?? '' })}</span>{/if}
            </YearSlider>
          </div>
        {:else if app.year && !whyA}
          <p class="foot yr">{t(li.series ? 'mv.yearNoSeries' : 'mv.yearNoSeriesLevel', { y: app.year })}
            <button type="button" class="link" onclick={() => (app.year = null)}>{t('mv.backLatest')}</button></p>
        {/if}
      </section>

      <section class="extra">
        <div class="row2">
          <span class="caps">{t('mv.sizeBy')}</span>
          <div class="seg" role="radiogroup" aria-label={t('mv.mapType')}>
            <button type="button" role="radio" aria-checked={!symbolsMode} onclick={() => setDisplay('choropleth')}>{t('mv.choro')}</button>
            <button type="button" role="radio" aria-checked={symbolsMode} onclick={() => setDisplay('symbols')}>{t('mv.symbols')}</button>
          </div>
        </div>
        <MetricPicker metrics={base.metrics} level={ld.level} value={sizeMeta?.id ?? ''} none={symbolsMode ? undefined : t('mv.none')}
          onpick={(id) => (app.size = id || null)} />
        {#if whyS}
          <p class="why sp">{whyS}</p>
        {:else if sizeMeta && sizeData && sizeRef}
          <div class="sp">
            <SizeLegend meta={sizeMeta} period={sizeRef.col.period} vmax={sizeData.vmax} rmax={sizeData.rMax * zf} filled={symbolsMode}
              nDrawn={sizeData.syms.length} nMissing={sizeData.nMissing} nNonPositive={sizeData.nNonPositive} unitWord={word} />
          </div>
        {:else if sizeMeta}
          <p class="foot sp">{t('status.loading')}</p>
        {/if}
        <p class="foot sp">
          {#if symbolsMode}{t('mv.symHint')}
          {:else if sizeMeta}{t('mv.ringHint')}
          {:else}{t('mv.sizeHint')}{/if}
        </p>
      </section>

      <section class="reach">
        <ReachControls {hubs} hub={hub.slug} mode={app.reach} t={app.t} playing={app.playing} {carAvailable} {station} ptm={app.ptm}
          onptm={(m) => (app.ptm = m)}
          onhub={(slug) => { stop(); app.hub = slug; }} onmode={setReach} ont={(v) => { stop(); app.t = v; }} onplay={play}>
          {#if reachError}
            {t('mv.reachErr', { e: reachError })}
          {:else if reachFile === undefined || reachRef === undefined}
            {t('mv.loadingNet')}
          {:else if reachFile === null}
            {t(reachMode === 'car' ? 'mv.noCarNet' : 'mv.noPtNet', { hub: hub.name })}
          {:else}
            {#if reachedCount !== null}{t(filtered ? 'pt.reachedF' : 'pt.reached', { n: fmtNumber(reachedCount, 0), t: Math.round(app.t), what: kindLabel(reachKind, station, true) })}
            {:else if ld.level !== 'gemeinde'}{t('mv.reachLevel')}
            {:else}{t('mv.reachHeld')}{/if}
            <span class="foot detail">{methodText(reachKind, hub.name, rt, station)} {t('pt.lines', { hub: hub.name })}</span>
          {/if}
        </ReachControls>
      </section>

      {/if}
      {#if desktop || phoneTab === 'filters'}
      <section>
        <div class="caps lab">{t('tab.filters')}</div>
        <FilterPanel {evals} {match} total={nUnits} unitWord={word} level={ld.level} metrics={base.metrics} {hubs}
          {station} method={(mode, h) => methodText(mode, h, rt, station)}
          options={catOpts} defaultMetric={app.filters.some((f) => f.kind === 'num' && f.metric === metaRaw.id) ? 'pop_total' : metaRaw.id}
          defaultHub={hub.slug} onset={(fs) => (app.filters = fs)} onzoom={match.n > 0 ? () => zoomTo(matchIdx) : undefined} />
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
        <LevelNote />
      </div>
      {#if !desktop && card && refA && colA}
        <div class="card-wrap">
          <Card name={ld.name[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
            source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} extra={card.extra} onclose={() => (app.sel = null)}
            profile={profileHref(refOf(ld.level, ld.units[card.i]))} profileLabel={t('card.profile')} sourceLink={sourceHref(metaA.source)} />
        </div>
      {/if}
      {#if full && scaleA && colA && !whyA}
        <div class="flegend">
          <div class="fl-t">{ml(metaA)}</div>
          <Legend meta={metaA} v={colA.v} period={colA.period} scale={scaleA} {nUnits} unitWord={word} source={base.sources.get(metaA.source)}
            method={app.cls} onmethod={(m) => (app.cls = m)} compact />
        </div>
      {/if}
      {#if tip && hover !== null && hoverAt && desktop}
        <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
          <strong>{ld.name[hover]}</strong>{#if ld.canton[hover] && ld.level !== 'kanton' && !ld.name[hover].includes('(')}&nbsp;<span class="muted">{ld.canton[hover]}</span>{/if}
          {#each tip as r}<div class="num">{r}</div>{/each}
        </div>
      {/if}
    </div>
  </section>

  {#if desktop}
    <aside class="side" aria-label={t('tab.stats')}>
      {#if card && refA && colA}
        <div class="caps lab">{t('mv.selected', { one })}</div>
        <Card name={ld.name[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
          source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} extra={card.extra} docked onclose={() => (app.sel = null)}
          profile={profileHref(refOf(ld.level, ld.units[card.i]))} profileLabel={t('card.profile')} sourceLink={sourceHref(metaA.source)} />
      {:else}
        <p class="foot hint">{t('mv.hint')}</p>
      {/if}
      <div class="tabs side-tabs" role="tablist" aria-label={t('mv.side')}>
        <button type="button" role="tab" aria-selected={deskTab === 'rank'} onclick={() => (app.tab = 'rank')}>{t('tab.rank')}</button>
        <button type="button" role="tab" aria-selected={deskTab === 'stats'} onclick={() => (app.tab = null)}>{t('tab.stats')}</button>
      </div>
      <div class="sblock">
        {#if deskTab === 'rank'}{@render rankSnip()}{:else}{@render statsSnip()}{/if}
      </div>
    </aside>
  {/if}


  {#if !mapReady}
    <div class="status" role="status">{t('status.loadingMap')}</div>
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
  .exrow { margin: 6px 0 0; }
  .vd { margin-top: 6px; }
  .vd button { padding: 3px 8px; font-size: 0.74rem; }
  .exb { border: 1px solid var(--ink); background: var(--panel); padding: 3px 9px; cursor: pointer; font-size: 0.74rem; font-weight: 600; color: var(--text); }
  .exb:disabled { opacity: 0.5; cursor: progress; }
  .hintc { margin: 6px 0 0; font-size: 0.76rem; border-left: 3px solid var(--accent); padding-left: 6px; }
  .flegend {
    position: absolute; z-index: 4; left: 10px; bottom: 26px; width: min(340px, calc(100% - 20px)); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 8px;
  }
  .fl-t { font-weight: 700; font-size: 0.8rem; margin-bottom: 2px; }
  .stage:focus { outline: none; }
  /* full-screen map: header and panels hidden, the map fills the viewport */
  :global(html.mapfull .app > header.top) { display: none; }
  .stage.full { display: block; }
  .stage.full .controls, .stage.full .side { display: none; }
  .stage.full .pane { position: absolute; inset: 0; }
  .lvlbar { position: absolute; z-index: 3; top: 10px; left: 10px; right: 56px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px; pointer-events: none; }
  .lvlbar > :global(*) { pointer-events: auto; }

  @media (min-width: 900px) {
    .stage { display: grid; grid-template-columns: 330px minmax(0, 1fr) 320px; }
    .controls { border-right: 1px solid var(--rule); min-height: 0; }
    .body { padding-top: 4px; }
  }

  @media (max-width: 899px) {
    /* phone: map on top, the sheet below it (it never covers the map); opening the sheet shrinks the map */
    .stage { display: flex; flex-direction: column; }
    .pane { order: 0; flex: 1 1 auto; min-height: 38%; }
    .controls {
      order: 1; flex: none; border-top: 2px solid var(--rule); max-height: 46%;
      padding-bottom: env(safe-area-inset-bottom);
    }
    .controls.open { max-height: 62%; }
    .controls .body { min-height: 0; }
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
    :global(.single .maplibregl-ctrl-top-right .maplibregl-ctrl-group:not(.gb-btn)) { display: none; }
    .lvlbar { top: 8px; left: 8px; }
    .card-wrap { top: 48px; }
  }
</style>
