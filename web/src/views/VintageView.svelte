<script lang="ts">
  import { pubName } from '../lib/texts.svelte';
  // Older boundaries (docs/older_boundaries.md): the municipality map of a past municipality state,
  // shaded only by metrics that exist on that state (native, or carried forward from an older state).
  // URL: #v=vintage&vin=2000&m=vz_lang_fr_share&y=1970&sel=<BFS number on that state>&cls=…
  // Desktop: controls left, map centre, card and statistics right. Phone: map on top, panel below.
  import { onMount, tick } from 'svelte';
  import Card from '../components/Card.svelte';
  import Legend from '../components/Legend.svelte';
  import MetricPicker from '../components/MetricPicker.svelte';
  import StatsBlock from '../components/StatsBlock.svelte';
  import YearSlider from '../components/YearSlider.svelte';
  import VintageSwitch from '../components/VintageSwitch.svelte';
  import { buildScale, divergeCentre, fmtNumber, fmtPeriod, fmtValue, isDiverging, sortedValues } from '../lib/classify';
  import { unitCounts, type Base, type LevelData, type MetricMeta, type Source } from '../lib/data';
  import { levelName, ml, t, levelWord } from '../lib/i18n.svelte';
  import { CH_BOUNDS, UnitMap } from '../lib/mapview';
  import { profileHref, sourceHref } from '../lib/nav';
  import { refOf } from '../lib/places';
  import { app } from '../lib/state.svelte';
  import { divRamp, seqRamp } from '../lib/theme';
  import {
    loadVintage, loadVintageIndex, loadVintageValues, switchVintage, vintageColumn, vintageLabel, vintageMeta, VINTAGE_FALLBACK, predecessorOf,
    type VintageData, type VintageIndex, type VintageValues,
  } from '../lib/vintage';
  import { fmtDate, tv, vintageFind } from '../lib/vintage-strings.svelte';
  import { RefLayer, lakesOf, type RefData } from '../lib/reflayer';
  import { loadHistory, norm, type HistoryFile } from '../lib/places';
  import '../lib/i18n-r3';
  import type maplibregl from 'maplibre-gl';
  import type { FeatureCollection } from 'geojson';

  interface Props {
    base: Base;
    desktop: boolean;
    onrendered?: () => void;
  }
  let { base, desktop, onrendered }: Props = $props();

  let ix = $state.raw<VintageIndex | null>(null);
  let ixMissing = $state(false);
  let data = $state.raw<VintageData | null>(null);
  let vals = $state.raw<{ key: string; v: VintageValues } | null>(null);
  let err = $state<string | null>(null);
  let mapReady = $state(false);
  let hover = $state<number | null>(null);
  let hoverAt = $state<{ x: number; y: number } | null>(null);
  let mapEl: HTMLDivElement;
  let view: UnitMap | null = null;
  let refLayer: RefLayer | null = null;

  onMount(() => {
    loadVintageIndex().then((x) => {
      ix = x;
      ixMissing = !x || !x.vintages.length;
    });
  });
  const info = $derived(ix?.vintages.find((v) => v.id === app.params.vin) ?? null);
  // unknown vintage in a link: the newest older vintage (the hash follows)
  $effect(() => {
    if (ix && ix.vintages.length && !info) app.params = { ...app.params, vin: ix.vintages[0].id };
  });
  $effect(() => {
    const i = info;
    if (!i) return;
    let live = true;
    loadVintage(i).then((d) => live && (data = d)).catch((e) => (err = String(e)));
    return () => (live = false);
  });
  const shown = $derived(data && info && data.info.id === info.id ? data : null);
  const vin = $derived(info?.id ?? '');
  const refYear = $derived(ix ? ix.reference.slice(0, 4) : '');

  // ------------------------------------------------------------------ metric
  const metaRaw = $derived(base.metas.get(app.metric));
  const vm = $derived(info?.metrics[app.metric] ?? null);
  const meta = $derived<MetricMeta | null>(vm && metaRaw ? vintageMeta(metaRaw, vm) : null);
  /** metrics of this vintage, adapted for the picker */
  const pickable = $derived(
    info ? base.metrics.filter((m) => info.metrics[m.id]).map((m) => vintageMeta(m, info.metrics[m.id])) : [],
  );
  /** a metric to offer when the shaded one does not exist on this state: same theme first */
  const fallback = $derived.by(() => {
    if (vm || !pickable.length) return null;
    const heads = pickable.filter((m) => m.headline !== null && m.headline < 1000).sort((a, b) => a.headline! - b.headline!);
    return heads.find((m) => m.theme === metaRaw?.theme) ?? heads[0] ?? pickable[0];
  });
  $effect(() => {
    const i = info;
    const m = vm;
    if (!i || !m) return;
    const key = `${i.id}:${m.file}`;
    if (vals?.key === key) return;
    let live = true;
    loadVintageValues(i, m.file).then((v) => live && (vals = { key, v })).catch((e) => (err = String(e)));
    return () => (live = false);
  });
  const ref = $derived(
    meta && vm && info && vals?.key === `${info.id}:${vm.file}` ? vintageColumn(vals.v, meta.id, app.year) : null,
  );
  const col = $derived(ref?.col ?? null);
  const yearMissing = $derived(!!app.year && !!vm && !vm.periods.includes(app.year));
  const source = $derived<Source | undefined>(vm && ix ? (ix.sources[vm.source] as Source | undefined) : undefined);
  const geoSource = $derived(ix?.sources.bfs_hist_boundaries);
  /** sources page entry when the harmonised build lists the source, else the publisher's page */
  const srcLink = $derived(vm ? (base.sources.has(vm.source) ? sourceHref(vm.source) : source?.url || undefined) : undefined);
  const aligned = $derived(!!shown && !!ref && ref.file.units.length === shown.units.length);
  const scale = $derived.by(() => {
    if (!col || !meta || !aligned) return null;
    const s = sortedValues(col.v);
    return s.length ? buildScale(col.v, app.cls, isDiverging(meta, s), seqRamp(), divRamp(), divergeCentre(meta)) : null;
  });
  const names = $derived(shown ? shown.units.map((u) => u.name) : []);
  const cantons = $derived(shown ? shown.units.map((u) => u.kanton) : []);
  const nUnits = $derived(shown?.units.length ?? 0);
  const word = $derived(levelWord('gemeinde'));

  // ------------------------------------------------------------------ selection
  const selIdx = $derived(shown && app.sel !== null ? (shown.index.get(app.sel) ?? null) : null);
  $effect(() => {
    if (shown && app.sel !== null && !shown.index.has(app.sel)) app.sel = null;
  });
  function select(i: number | null) {
    app.sel = i === null || !shown ? null : shown.units[i].id;
  }
  const card = $derived.by(() => {
    if (selIdx === null || !shown || !ref || !meta) return null;
    const u = shown.units[selIdx];
    const pct = (w: number) => fmtNumber(Math.round(w * 1000) / 10, w >= 0.999 ? 0 : 1);
    // where the municipality is today: one row per current municipality (short values: the card keeps
    // label and value on one line)
    const extra: { label: string; value: string }[] = [];
    const notes: string[] = [];
    if (u.to.length === 1) {
      const [id, name, , parts] = u.to[0];
      if (parts > 1) {
        // B5 (R15): one sentence, "Today part of Glarus Nord, which was formed in 2011 from 8 municipalities"
        const ev = joinEvent(u.id, id);
        const year = ev ? ev.d.slice(0, 4) : null;
        const key = ev?.t === 'absorption' ? 'r3.vinJoined' : year ? 'r3.vinFormed' : 'r3.vinFormedNoYear';
        notes.push(t(key, { name: `${name} (${id})`, year: year ?? '', n: parts, y: vin }));
      } else extra.push({ label: tv('vin.todayOne'), value: `${name} (${id})` });
    } else {
      u.to.forEach((x, k) => extra.push({ label: k === 0 ? tv('vin.today') : '', value: `${x[1]} · ${tv('vin.share', { p: pct(x[2]) })}` }));
    }
    const main = u.to[0];
    return {
      i: selIdx, u, extra, notes,
      sub: `${u.kanton} · BFS ${u.id} · ${vin}`,
      profile: main ? profileHref(refOf('gemeinde', main[0])) : undefined,
      profileLabel: main ? tv('vin.profile') : undefined,
    };
  });
  // boundary history (mergers and their dates) for the card wording
  let hist = $state.raw<HistoryFile | null>(null);
  $effect(() => {
    if (selIdx !== null && !hist) loadHistory().then((h) => (hist = h)).catch(() => {});
  });
  /** the event after this state that took the old municipality `old` into today's `current` */
  function joinEvent(old: string, current: string) {
    const evs = hist?.units?.[current];
    if (!evs || !info) return null;
    return evs.find((e) => e.d > info.date && (e.t === 'merger' || e.t === 'absorption') && e.from.some((f) => f[0] === old)) ?? null;
  }
  const tip = $derived(hover !== null && shown && col && meta ? (col.v[hover] === null ? t('lg.noData') : fmtValue(col.v[hover]!, meta)) : null);

  // ------------------------------------------------------------------ map
  function asLevel(d: VintageData): LevelData {
    const units = d.units.map((u) => u.id);
    return {
      level: 'gemeinde', units, index: d.index, geo: d.geo, name: d.units.map((u) => u.name), canton: d.units.map((u) => u.kanton),
      core: { level: 'gemeinde', units, metrics: {}, status_codes: {}, precision_codes: {} },
    };
  }
  const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] };
  onMount(() => {
    view = new UnitMap(mapEl, base, {
      onSelect: select, onHover: (i, p) => { hover = i; hoverAt = i === null ? null : p; },
      onReset: () => fit(true), resetLabel: () => t('map.reset'),
      onLabels: () => (app.labels = !app.labels), labelsLabel: () => t('lb.toggle'), labelsOn: () => app.labels,
    });
    // B5 (R1): place names of that state and lake names, as on the harmonised map
    refLayer = new RefLayer(view.map, mapEl);
    refLayer.setVisible(app.labels);
    view.ready.then(() => {
      mapReady = true;
      fit();
      view!.map.once('idle', () => onrendered?.());
    });
    const ro = new ResizeObserver(() => view?.map.resize());
    ro.observe(mapEl);
    return () => {
      ro.disconnect();
      view?.map.remove();
    };
  });
  /** B5 (R14): a link with a selection opens zoomed to it (once per selection from a link or the search) */
  let focusSel = $state(app.sel !== null);
  $effect(() => {
    const i = selIdx;
    const d = shown;
    if (mapReady && focusSel && i !== null && d) tick().then(() => requestAnimationFrame(() => fit(true)));
  });
  /** the selection's outline, when a link or the search asked to zoom to it */
  function focusTarget() {
    if (!focusSel || selIdx === null || !shown) return null;
    return shown.geo.features.find((x) => x.id === selIdx) ?? null;
  }
  // the header search lists the municipalities of this state while it is shown
  $effect(() => {
    const d = shown;
    vintageFind.units = d ? d.units.map((u) => ({ id: u.id, name: u.name, kanton: u.kanton })) : null;
    vintageFind.label = d ? t('r3.vinUnit', { y: d.info.id }) : null;
  });
  onMount(() => () => {
    vintageFind.units = null;
    vintageFind.label = null;
  });
  // the header search on this route: a former name or a current municipality selects the old unit
  $effect(() => {
    const q = vintageFind.q;
    const d = shown;
    if (!q || !d) return;
    vintageFind.q = null;
    let id: string | null = q.bfs && d.index.has(q.bfs) ? q.bfs : null;
    if (!id && q.name) id = d.units.find((u) => norm(u.name) === norm(q.name!))?.id ?? null;
    if (!id && q.current) id = predecessorOf(d.units, q.current);
    if (id) {
      app.sel = id;
      focusSel = true;
    }
  });
  // reference labels: every municipality of that state (towns at the national zoom, all names zoomed in)
  let popVals = $state.raw<{ key: string; v: VintageValues } | null>(null);
  const popId = $derived(info ? (VINTAGE_FALLBACK.slice(0, 2).find((id) => info!.metrics[id]) ?? null) : null);
  $effect(() => {
    const i = info;
    const id = popId;
    if (!i || !id) return;
    const key = `${i.id}:${id}`;
    if (popVals?.key === key) return;
    loadVintageValues(i, i.metrics[id].file).then((v) => (popVals = { key, v })).catch(() => {});
  });
  const refData = $derived.by<RefData | null>(() => {
    const d = shown;
    if (!d) return null;
    const pc = popVals && popId && popVals.key === `${d.info.id}:${popId}` ? vintageColumn(popVals.v, popId, null) : null;
    const pos = pc ? new Map(pc.file.units.map((u, k) => [u, pc.col.v[k] ?? 0])) : null;
    const cities = d.units
      .filter((u) => u.label)
      .map((u) => ({ name: u.name.replace(/\s*\([A-Z]{2}\)$/, ''), lng: u.label![0], lat: u.label![1], pop: pos?.get(u.id) ?? 0 }))
      .sort((a, b) => b.pop - a.pop);
    // as on the harmonised map up to zoom 10.5; deeper, every municipality (the placement still avoids overlaps)
    const floor = (z: number) => (z < 7 ? 50000 : z < 8 ? 28000 : z < 8.8 ? 13000 : z < 9.6 ? 4000 : z < 10.3 ? 1000 : 0);
    return { cities, lakes: lakesOf(base.lakes), floor };
  });
  $effect(() => {
    const r = refData;
    if (mapReady) refLayer?.setData(r);
  });
  $effect(() => {
    const on = app.labels;
    if (mapReady) {
      refLayer?.setVisible(on);
      view?.relabel();
    }
  });
  function fit(animate = false) {
    if (!view) return;
    const f = focusTarget();
    if (f) {
      focusSel = false;
      view.map.resize();
      view.fitGeometry(f.geometry, desktop ? { top: 40, bottom: 40, left: 40, right: 60 } : { top: 30, bottom: 90, left: 20, right: 44 }, { animate, maxZoom: 11 });
      return;
    }
    const padding = desktop ? { top: 24, bottom: 24, left: 24, right: 48 } : { top: 46, bottom: 12, left: 10, right: 10 };
    view.map.resize();
    view.map.fitBounds(CH_BOUNDS, { padding, animate, duration: animate ? 500 : 0 });
  }
  let drawn = '';
  $effect(() => {
    const d = shown;
    if (!mapReady || !d || drawn === d.info.id) return;
    // the shared map class skips a level it already shows: clear it first when the state changes
    if (drawn) view!.setLevel({ ...asLevel(d), level: 'vintage-clear', units: [], geo: EMPTY });
    view!.setLevel(asLevel(d));
    (view!.map.getSource('kt') as maplibregl.GeoJSONSource | undefined)?.setData(d.cantons);
    (view!.map.getSource('lakes') as maplibregl.GeoJSONSource | undefined)?.setData(d.lakes);
    drawn = d.info.id;
  });
  $effect(() => {
    const c = scale && aligned ? scale.unitColour : shown ? shown.units.map(() => null) : null;
    void drawn;
    if (mapReady && c && shown && drawn === shown.info.id) view!.setColours(c);
  });
  $effect(() => {
    const s = selIdx;
    void drawn;
    if (mapReady) view!.setSelected(s);
  });
  $effect(() => {
    const h = hover;
    if (mapReady) view!.setHover(h);
  });
  $effect(() => {
    void desktop;
    if (mapReady) tick().then(() => requestAnimationFrame(() => fit()));
  });

  const provText = $derived(vm ? (vm.provenance === 'forward' ? tv('vin.forward') : tv('vin.native')) : '');
</script>

<main class="stage" id="main" tabindex="-1">
  <h1 class="sr-only">{info ? tv('vin.title', { date: fmtDate(info.date) }) : tv('vin.label')}</h1>
  <aside class="controls" aria-label={t('mv.controls')}>
    <div class="body">
      <section>
        <div class="caps lab">{info ? vintageLabel(info, app.lang) : tv('vin.label')}</div>
        {#if info}
          <p class="foot cnt">{tv('vin.count', { n: fmtNumber(info.n_units, 0), m: fmtNumber(unitCounts.get('gemeinde') ?? 2110, 0) })}</p>
        {/if}
        <div class="row2 lab"><span class="caps">{t('mv.shade')}</span></div>
        {#if info}
          <!-- a metric without values on this state stays named on the button (no level: not in the list) -->
          <MetricPicker metrics={vm || !metaRaw ? pickable : [...pickable, { ...metaRaw, levels: [] }]} level="gemeinde" value={app.metric}
            onpick={(id) => (app.metric = id)} />
        {/if}
        <div class="legend-wrap">
          {#if info && !vm && metaRaw}
            <p class="why" role="status">{tv('vin.na', { metric: ml(metaRaw), y: vin })}</p>
            <p class="acts">
              <button type="button" class="act" onclick={() => switchVintage(base, null)}>{tv('vin.toRef', { y: refYear })}</button>
              {#if fallback}<button type="button" class="act alt" onclick={() => (app.metric = fallback!.id)}>{tv('vin.try', { metric: ml(fallback) })}</button>{/if}
            </p>
            <p class="foot">{tv('vin.nAvail', { n: pickable.length })}</p>
          {:else if scale && col && meta}
            <Legend {meta} v={col.v} period={col.period} {scale} {nUnits} unitWord={word} {source}
              method={app.cls} onmethod={(m) => (app.cls = m)} compact={!desktop} />
          {:else if err}
            <p class="why">{t('status.error', { e: err })}</p>
          {:else}
            <p class="foot">{t('status.loading')}</p>
          {/if}
        </div>
        {#if vm && meta && vm.periods.length > 1}
          <div class="yr">
            <YearSlider periods={vm.periods} value={yearMissing ? null : app.year} onchange={(y) => (app.year = y)} harm={info ? tv('vin.yrHarm', { date: fmtDate(info.date) }) : undefined}>
              {#if yearMissing}{' · '}<span class="warn">{tv('vin.noYear', { y: app.year ?? '' })}</span>{/if}
            </YearSlider>
          </div>
        {:else if yearMissing && col}
          <p class="foot yr">{tv('vin.noYear', { y: app.year ?? '' })} · {fmtPeriod(col.period)}</p>
        {/if}
        <VintageSwitch {base} />
        {#if app.filters.length}<p class="foot fnote">{t('r3.vinFilters', { n: app.filters.length })}</p>{/if}
        {#if vm}
          <p class="prov">{provText}{#if vm.provenance === 'forward' && vm.n_estimate}{' '}{tv('vin.nEst', { n: fmtNumber(vm.n_estimate, 0) })}{/if}
            {#if source}<a href={srcLink}>{pubName(source.publisher)}</a>{/if}</p>
        {/if}
      </section>
      <section>
        <p class="foot">{info ? tv('vin.geo', { date: fmtDate(info.date) }) : ''}{geoSource ? ` · ${geoSource.license?.split(' – ')[0] ?? ''}` : ''}</p>
      </section>
    </div>
  </aside>

  <section class="pane">
    <div class="mapbox">
      <div class="map" bind:this={mapEl}></div>
      {#if !desktop && card && ref && meta}
        <div class="card-wrap">
          <Card name={card.u.name} canton={card.u.kanton} sub={card.sub} {meta} file={ref.file} col={ref.col} index={card.i}
            {source} reach={null} unitWord={word} extra={card.extra} notes={card.notes} compact onclose={() => (app.sel = null)}
            profile={card.profile} profileLabel={card.profileLabel} sourceLink={srcLink} />
        </div>
      {/if}
      {#if tip !== null && hover !== null && hoverAt && desktop}
        <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
          <strong>{names[hover]}</strong>&nbsp;<span class="muted">{cantons[hover]}</span>
          <div class="num">{tip}</div>
        </div>
      {/if}
      {#if ixMissing}
        <div class="status" role="status">{tv('vin.none')} <button type="button" class="act" onclick={() => app.go('map', {})}>{t('nav.map')}</button></div>
      {:else if !shown && info}
        <div class="status" role="status">{tv('vin.loading', { y: info.id })}</div>
      {/if}
    </div>
  </section>

  {#if desktop}
    <aside class="side" aria-label={t('tab.stats')}>
      {#if card && ref && meta}
        <div class="caps lab">{t('mv.selected', { one: levelName('gemeinde', false) })}</div>
        <Card name={card.u.name} canton={card.u.kanton} sub={card.sub} {meta} file={ref.file} col={ref.col} index={card.i}
          {source} reach={null} unitWord={word} extra={card.extra} notes={card.notes} docked onclose={() => (app.sel = null)}
          profile={card.profile} profileLabel={card.profileLabel} sourceLink={srcLink} />
      {:else}
        <p class="foot hint">{tv('vin.hint')}</p>
      {/if}
      {#if col && meta && aligned}
        <div class="sblock">
          <StatsBlock {meta} v={col.v} period={col.period} {names} {cantons} ch={col.ch !== undefined && col.ch !== null ? { value: col.ch, period: col.period } : null}
            sel={null} {source} unitWord={word} />
        </div>
      {/if}
    </aside>
  {/if}
</main>

<style>
  .stage { flex: 1; min-height: 0; position: relative; }
  .stage:focus { outline: none; }
  .pane { position: relative; min-width: 0; min-height: 0; display: flex; flex-direction: column; background: var(--map-bg); }
  .mapbox { position: relative; flex: 1; min-height: 0; }
  .map { position: absolute; inset: 0; }
  .controls { display: flex; flex-direction: column; background: var(--panel); z-index: 4; min-height: 0; }
  .body { overflow-y: auto; padding: 0 16px 14px; overscroll-behavior: contain; }
  .body section { padding: 14px 0; }
  .body section + section { border-top: 1px solid var(--rule); }
  .lab { margin-bottom: 6px; }
  .row2 { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 10px; }
  .cnt { margin: 0 0 4px; }
  .legend-wrap { margin-top: 10px; }
  .why { margin: 0; font-size: 0.8rem; border-left: 3px solid var(--accent); padding-left: 8px; }
  .acts { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 4px; }
  .act { border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text); padding: 4px 9px; cursor: pointer; font-size: 0.76rem; font-weight: 600; }
  .act.alt { background: var(--panel); color: var(--text); }
  .yr { margin-top: 10px; }
  .warn { color: var(--text); }
  .fnote { margin: 8px 0 0; border-left: 3px solid var(--ink); padding-left: 6px; color: var(--text); }
  .prov { margin: 10px 0 0; font-size: 0.74rem; color: var(--muted); line-height: 1.4; }
  .prov a { color: var(--text); }
  .side { background: var(--panel); border-left: 1px solid var(--rule); padding: 14px 16px; overflow-y: auto; }
  .sblock { margin-top: 18px; border-top: 1px solid var(--rule); padding-top: 10px; }
  .hint { margin: 0; }
  .muted { color: var(--muted); }
  .maptip {
    position: absolute; z-index: 5; pointer-events: none; transform: translate(14px, 14px); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 9px; font-size: 0.8rem; white-space: nowrap;
  }
  .card-wrap { position: absolute; z-index: 6; left: 8px; right: 34px; bottom: 8px; max-width: 440px; margin: 0 auto; max-height: calc(100% - 52px); display: flex; flex-direction: column; justify-content: flex-end; }
  .status {
    position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); background: var(--panel); color: var(--muted);
    padding: 8px 14px; border: 1px solid var(--border); z-index: 40; max-width: 90vw;
  }
  @media (min-width: 900px) {
    .stage { display: grid; grid-template-columns: 330px minmax(0, 1fr) 320px; }
    .controls { border-right: 1px solid var(--rule); }
    .body { padding-top: 4px; }
  }
  @media (max-width: 899px) {
    .stage { display: flex; flex-direction: column; }
    .pane { order: 0; flex: 1 1 auto; min-height: 50%; }
    .controls { order: 1; flex: none; border-top: 2px solid var(--rule); max-height: 44%; padding-bottom: env(safe-area-inset-bottom); }
    .body section { padding: 9px 0; }
  }
</style>
