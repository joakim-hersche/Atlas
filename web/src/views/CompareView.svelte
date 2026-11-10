<script lang="ts">
  // Compare mode: two synced maps (metric A and B) and a scatter plot with r, ρ and weighted r.
  import { onMount, tick } from 'svelte';
  import Legend from '../components/Legend.svelte';
  import LevelSwitch from '../components/LevelSwitch.svelte';
  import LevelNote from '../components/LevelNote.svelte';
  import MetricPicker from '../components/MetricPicker.svelte';
  import Scatter from '../components/Scatter.svelte';
  import { buildScale, divergeCentre, fmtValue, isDiverging, sortedValues, type Method } from '../lib/classify';
  import type { ColumnStore } from '../lib/columns.svelte';
  import { fmtNumber } from '../lib/classify';
  import { loadReachIndex, loadUnits, namesOf, unavailableReason, type Base, type Hub, type LevelData, type MetricMeta, type UnitRow } from '../lib/data';
  import { catOptions, combine, describeFilter, evalFilter } from '../lib/filters';
  import { hrefFor } from '../lib/nav';
  import { bareAttribution } from '../lib/export';
  import { CH_BOUNDS, UnitMap, syncCameras } from '../lib/mapview';
  import { app } from '../lib/state.svelte';
  import { levelName, t, levelWord } from '../lib/i18n.svelte';
  import { switchLevel } from '../lib/levels';
  import { divRamp, mute, seqRamp, token } from '../lib/theme';

  interface Props {
    base: Base;
    ld: LevelData;
    cols: ColumnStore;
    desktop: boolean;
    onrendered?: () => void;
  }
  let { base, ld, cols, desktop, onrendered }: Props = $props();

  const REGION_NAMES = (): Record<string, string> => ({ '1': t('cv.r1'), '2': t('cv.r2'), '3': t('cv.r3'), '4': t('cv.r4') });

  interface Preset {
    slug: string;
    label: string;
    a: string;
    b: string;
    fallback?: { b: string; label: string };
  }
  const PRESETS: Preset[] = [
    { slug: 'left-income', label: 'cv.p.left', a: 'nrw_share_left_bloc', b: 'tax_np_mean_taxable_income',
      fallback: { b: 'nrw_share_sp', label: 'cv.p.sp' } },
    { slug: 'density-foreigners', label: 'cv.p.density', a: 'geo_pop_density', b: 'share_foreign' },
    { slug: 'age-svp', label: 'cv.p.age', a: 'share_age_65plus', b: 'nrw_share_svp' },
    { slug: 'heatpumps-income', label: 'cv.p.heat', a: 'gws_share_heatpump', b: 'tax_np_mean_taxable_income' },
  ];
  const metas = $derived(base.metas);
  /** unit names in the UI language */
  const names = $derived(namesOf(ld));
  const presetsOf = (m: Map<string, MetricMeta>) =>
    PRESETS.flatMap((p) => {
      if (m.has(p.a) && m.has(p.b)) return [p];
      // left bloc not in this build: SP share vs income
      if (p.fallback && m.has(p.fallback.b) && m.has(p.b)) return [{ ...p, a: p.fallback.b, label: p.fallback.label }];
      return [];
    });
  const presets = $derived(presetsOf(metas));
  const activePreset = $derived(presets.find((p) => p.a === app.metric && p.b === app.metricB)?.slug ?? null);
  function applyPreset(p: Preset) {
    app.metric = p.a;
    app.metricB = p.b;
    app.sel = null;
  }
  function defaultB(a: string) {
    return a === 'tax_np_mean_taxable_income' ? 'nrw_share_svp' : 'tax_np_mean_taxable_income';
  }
  // bare '#compare' or '#<preset>' from a shared link
  function initPreset(b: Base) {
    if (app.preset === null) return;
    const ps = presetsOf(b.metas);
    const p = ps.find((x) => x.slug === app.preset) ?? ps[0];
    app.preset = null;
    if (p) applyPreset(p);
  }
  initPreset((() => base)());
  if (!app.metricB) app.metricB = defaultB(app.metric);

  let mapReadyA = $state(false);
  let mapReadyB = $state(false);
  let hover = $state<number | null>(null);
  let hoverAt = $state<{ pane: 'a' | 'b'; x: number; y: number } | null>(null);
  let regions = $state.raw<{ idx: Int8Array; names: string[] } | null>(null);
  let unitRows = $state.raw<UnitRow[] | null>(null);
  let hubs = $state.raw<Hub[]>([]);
  let mapElA = $state<HTMLDivElement>();
  let mapElB = $state<HTMLDivElement>();
  let viewA: UnitMap | null = null;
  let viewB: UnitMap | null = null;

  const metaA = $derived<MetricMeta>(metas.get(app.metric) ?? metas.get('pop_total')!);
  const metaB = $derived<MetricMeta | undefined>(app.metricB ? metas.get(app.metricB) : undefined);
  const refA = $derived(cols.get(ld, metaA.id, app.year));
  const refB = $derived(metaB ? cols.get(ld, metaB.id, app.year) : null);
  const colA = $derived(refA?.col);
  const colB = $derived(refB?.col);
  const whyA = $derived(unavailableReason(metaA, ld.level));
  const whyB = $derived(metaB ? unavailableReason(metaB, ld.level) : null);
  const seq = seqRamp();
  const div = divRamp();
  const scaleOf = (v: (number | null)[] | undefined, m: MetricMeta | undefined, method: Method) => {
    if (!v || !m) return null;
    const s = sortedValues(v);
    return s.length ? buildScale(v, method, isDiverging(m, s), seq, div, divergeCentre(m)) : null;
  };
  const scaleA = $derived(scaleOf(colA?.v, metaA, app.cls));
  const scaleB = $derived(scaleOf(colB?.v, metaB, app.cls));
  const nUnits = $derived(ld.units.length);
  const word = $derived(levelWord(ld.level));
  const pop = $derived(ld.core.metrics['pop_total']?.v ?? ld.units.map(() => null));
  const selIdx = $derived(app.sel !== null ? (ld.index.get(app.sel) ?? null) : null);
  const blank = $derived(ld.units.map(() => null));

  // ------------------------------------------------------------------ filters (kept from the map view)
  $effect(() => {
    if (app.filters.length && !unitRows) loadUnits().then((u) => (unitRows = u)).catch(() => {});
    if (app.filters.some((f) => f.kind === 'reach') && !hubs.length) loadReachIndex().then((ix) => ix && (hubs = ix.hubs)).catch(() => {});
  });
  const hubName = (slug: string) => hubs.find((h) => h.slug === slug)?.name ?? slug;
  const evals = $derived(app.filters.map((f) => evalFilter(f, { ld, rows: unitRows, metas, hubName, col: (id) => cols.get(ld, id, app.year) })));
  const match = $derived(combine(evals, nUnits));
  const filtered = $derived(match.active > 0);
  const filterText = $derived(
    evals.map((e) => describeFilter(e, (field, id) => catOptions(field, unitRows).find((o) => o.id === id)?.name ?? id)).join(' · '),
  );
  const dimmed = (colours: (string | null)[]) => {
    if (!filtered) return colours;
    const surface = token('--map-bg');
    return colours.map((c, i) => (c && !match.m[i] ? mute(c, surface, 0.88) : c));
  };

  function select(i: number | null) {
    app.sel = i === null ? null : ld.units[i];
  }
  function onMapHover(pane: 'a' | 'b', i: number | null, p: { x: number; y: number } | null) {
    hover = i;
    hoverAt = i === null || !p ? null : { pane, x: p.x, y: p.y };
  }

  onMount(() => {
    // the reset button on either map fits Switzerland; the camera sync carries it to the other map
    const reset = { onReset: () => fit(true), resetLabel: () => t('map.reset') };
    viewA = new UnitMap(mapElA!, base, { onSelect: select, onHover: (i, p) => onMapHover('a', i, p), ...reset });
    viewB = new UnitMap(mapElB!, base, { onSelect: select, onHover: (i, p) => onMapHover('b', i, p), ...reset }, { nav: false });
    let unsync: (() => void) | null = null;
    Promise.all([viewA.ready, viewB.ready]).then(() => {
      unsync = syncCameras(viewA!.map, viewB!.map);
      mapReadyA = true;
      mapReadyB = true;
      fit();
      viewA!.map.once('idle', () => onrendered?.());
    });
    const ro = new ResizeObserver(() => {
      viewA?.map.resize();
      viewB?.map.resize();
    });
    ro.observe(mapElA!);
    ro.observe(mapElB!);
    return () => {
      unsync?.();
      ro.disconnect();
      viewA?.map.remove();
      viewB?.map.remove();
    };
  });

  function fit(animate = false) {
    if (!viewA) return;
    viewA.map.resize();
    viewB?.map.resize();
    viewA.map.fitBounds(CH_BOUNDS, { padding: { top: 8, bottom: 8, left: 8, right: 8 }, animate, duration: animate ? 500 : 0 });
  }
  $effect(() => {
    void app.lang;
    if (mapReadyA) { viewA!.relabel(); viewB!.relabel(); }
  });
  $effect(() => {
    void desktop;
    if (mapReadyA) tick().then(() => requestAnimationFrame(() => fit()));
  });
  // phones: compact compare maps scroll with the page; panning needs two fingers
  $effect(() => {
    const coop = !desktop;
    for (const v of [mapReadyA ? viewA : null, mapReadyB ? viewB : null]) {
      if (!v) continue;
      if (coop) v.map.cooperativeGestures.enable();
      else v.map.cooperativeGestures.disable();
    }
  });

  // language regions of municipalities for the scatter plot (other levels: one colour)
  $effect(() => {
    const d = ld;
    if (d.level !== 'gemeinde') {
      regions = { idx: new Int8Array(d.units.length).fill(-1), names: [] };
      return;
    }
    let live = true;
    loadUnits().then((u) => {
      if (!live) return;
      const idx = new Int8Array(d.units.length).fill(-1);
      for (const r of u) {
        if (r.level !== 'gemeinde' || !r.sprachgebiet) continue;
        const i = d.index.get(r.id);
        if (i !== undefined) idx[i] = Number(r.sprachgebiet) - 1;
      }
      regions = { idx, names: ['1', '2', '3', '4'].map((k) => REGION_NAMES()[k]) };
    });
    return () => (live = false);
  });

  $effect(() => {
    const d = ld;
    if (mapReadyA) viewA!.setLevel(d);
    if (mapReadyB) viewB!.setLevel(d);
  });
  $effect(() => {
    void ld;
    if (mapReadyA) viewA!.setColours(scaleA && !whyA ? dimmed(scaleA.unitColour) : blank);
  });
  $effect(() => {
    void ld;
    if (mapReadyB) viewB!.setColours(scaleB && !whyB ? dimmed(scaleB.unitColour) : blank);
  });
  $effect(() => {
    const s = selIdx;
    if (mapReadyA) viewA!.setSelected(s);
    if (mapReadyB) viewB!.setSelected(s);
  });
  $effect(() => {
    const h = hover;
    if (mapReadyA) viewA!.setHover(h);
    if (mapReadyB) viewB!.setHover(h);
  });

  const tipRows = $derived.by(() => {
    if (hover === null || !hoverAt) return null;
    const h = hover;
    const fmt = (v: (number | null)[] | undefined, m: MetricMeta | undefined) => (v && m && v[h] !== null && v[h] !== undefined ? fmtValue(v[h]!, m) : t('lg.noData'));
    return [{ k: 'A', v: fmt(colA?.v, metaA) }, { k: 'B', v: fmt(colB?.v, metaB) }];
  });
</script>

<nav class="presets" aria-label={t('cv.examplesL')}>
  <LevelSwitch value={ld.level} onchange={(l) => switchLevel(base, l)} />
  <span class="caps">{t('pl.try')}</span>
  {#each presets as p}
    <button type="button" class="chip" aria-pressed={activePreset === p.slug} onclick={() => applyPreset(p)}>{t(p.label)}</button>
  {/each}
</nav>

<LevelNote variant="bar" />
{#if app.filters.length}
  <div class="fbar" role="status">
    <span class="caps">{t('tab.filters')}</span>
    <span class="ftx">{#if filtered}<strong class="num">{t('fp.match', { n: fmtNumber(match.n, 0), total: fmtNumber(nUnits, 0), units: word })}</strong>{' · '}{/if}{filterText}</span>
    <span class="seg" role="radiogroup" aria-label={t('cv.scatterMode')}>
      <button type="button" role="radio" aria-checked={!app.only} onclick={() => (app.only = false)}>{t('cv.highlight')}</button>
      <button type="button" role="radio" aria-checked={app.only} onclick={() => (app.only = true)}>{t('cv.only')}</button>
    </span>
    <a href={hrefFor('map', {}, { tab: 'filters' })} class="fedit">{t('cv.editFilters')}</a>
  </div>
{/if}

<main class="stage" id="main" tabindex="-1">
  <h1 class="sr-only">{t('nav.compare')}</h1>
  {#each [{ pane: 'a' as const, tag: 'A', meta: metaA, col: colA, scale: scaleA, why: whyA, ref: refA },
          { pane: 'b' as const, tag: 'B', meta: metaB, col: colB, scale: scaleB, why: whyB, ref: refB }] as P (P.pane)}
    <section class="pane" class:pa={P.pane === 'a'} class:pb={P.pane === 'b'}>
      <div class="phead">
        <MetricPicker metrics={base.metrics} level={ld.level} value={P.meta?.id ?? ''} tag={P.tag}
          onpick={(id) => (P.pane === 'a' ? (app.metric = id) : (app.metricB = id))} />
      </div>
      <div class="pbody">
        <div class="mapbox">
          {#if P.pane === 'a'}<div class="map" bind:this={mapElA}></div>{:else}<div class="map" bind:this={mapElB}></div>{/if}
          {#if hoverAt?.pane === P.pane && tipRows && hover !== null && desktop}
            <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
              <strong>{names[hover]}</strong>{#if ld.canton[hover] && ld.level !== 'kanton' && !names[hover].includes('(')}&nbsp;<span class="muted">{ld.canton[hover]}</span>{/if}
              {#each tipRows as r}<div class="num"><span class="k">{r.k}</span>{r.v}</div>{/each}
            </div>
          {/if}
        </div>
        <div class="plegend">
          {#if P.why}
            <p class="why">{P.why}</p>
          {:else if P.meta && P.scale && P.col}
            <Legend meta={P.meta} v={P.col.v} period={P.col.period} scale={P.scale} {nUnits} unitWord={word}
              source={base.sources.get(P.meta.source)} method={app.cls} onmethod={(m) => (app.cls = m)} />
            {#if P.ref?.yearMissing}<p class="foot">{t('cv.noYear', { y: P.ref.yearMissing })}</p>{/if}
          {:else if P.ref === undefined}
            <p class="muted">{t('status.loading')}</p>
          {/if}
        </div>
      </div>
    </section>
  {/each}

  <section class="pane ps">
    {#if metaB && colA && colB && regions && !whyA && !whyB}
      <Scatter xMeta={metaA} yMeta={metaB} x={colA.v} y={colB.v} xPeriod={colA.period} yPeriod={colB.period}
        region={regions.idx} regionNames={regions.names} {pop} names={names} cantons={ld.canton}
        hover={hover} sel={selIdx} unitWord={word} mask={filtered ? match.m : null} only={app.only}
        credits={[metaA, metaB].map((m, k) => `${k ? 'B' : 'A'} – ${t('lg.source')}: ${bareAttribution(base.sources.get(m.source)?.attribution || base.sources.get(m.source)?.publisher || m.source)}`)}
        note={[levelName(ld.level), filtered ? `${t('tab.filters')}: ${filterText} (${t('mv.nMatch', { n: fmtNumber(match.n, 0), total: fmtNumber(nUnits, 0) })})` : ''].filter(Boolean).join(' · ')} unitOne={levelName(ld.level, false)} onhover={(i) => { hover = i; hoverAt = null; }} onselect={select} />
    {:else if whyA || whyB}
      <p class="muted loading">{t('cv.needBoth')}</p>
    {:else}
      <p class="muted loading">{t('status.loading')}</p>
    {/if}
  </section>
</main>

<style>
  .presets {
    flex: none; display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: var(--panel); border-bottom: 1px solid var(--rule);
    overflow-x: auto; scrollbar-width: none;
  }
  .presets .caps { margin: 0 4px 0 8px; flex: none; }
  .chip {
    flex: none; padding: 4px 10px; border: 1px solid var(--ink); background: none; cursor: pointer;
    font-size: 0.8rem; font-weight: 500; white-space: nowrap;
  }
  .chip:hover { color: var(--accent); border-color: var(--accent); }
  .chip[aria-pressed='true'] { background: var(--ink); border-color: var(--ink); color: var(--ink-text); }

  .stage { flex: 1; min-height: 0; position: relative; }
  .fbar {
    flex: none; display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; padding: 5px 16px; font-size: 0.78rem;
    border-bottom: 1px solid var(--rule); background: var(--panel);
  }
  .ftx { flex: 1 1 240px; min-width: 0; }
  .fbar .seg button { padding: 2px 8px; font-size: 0.74rem; }
  .fedit { color: var(--text); font-size: 0.76rem; }
  .pane { position: relative; min-width: 0; min-height: 0; display: flex; flex-direction: column; background: var(--panel); }
  .phead { flex: none; padding: 8px; border-bottom: 1px solid var(--rule); }
  .pbody { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .mapbox { position: relative; flex: 1; min-height: 0; }
  .map { position: absolute; inset: 0; }
  .plegend { flex: none; padding: 10px 12px; border-top: 1px solid var(--rule); }
  .why { margin: 0; font-size: 0.8rem; }
  .maptip {
    position: absolute; z-index: 5; pointer-events: none; transform: translate(14px, 14px); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 9px; font-size: 0.8rem; white-space: nowrap;
  }
  .k { display: inline-block; width: 1.3em; color: var(--muted); font-weight: 500; }
  .muted { color: var(--muted); }
  .loading { padding: 16px; }

  @media (min-width: 900px) {
    .stage {
      display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); grid-template-rows: minmax(340px, 1.35fr) minmax(300px, 1fr);
      gap: 1px; background: var(--rule); overflow-y: auto;
    }
    .pane { container-type: inline-size; }
    .ps { grid-column: 1 / -1; padding: 10px 14px 12px; }
    @container (min-width: 620px) {
      .pbody { flex-direction: row; }
      .plegend { width: 250px; border-top: 0; border-left: 1px solid var(--rule); overflow-y: auto; }
    }
  }
  @media (max-width: 899px) {
    .presets { padding: 6px 16px; }
    .stage { overflow-y: auto; -webkit-overflow-scrolling: touch; }
    .pane { border-bottom: 1px solid var(--rule); }
    .mapbox { flex: none; height: 250px; }
    .plegend { padding: 6px 10px 8px; }
    .ps { padding: 10px 10px calc(16px + env(safe-area-inset-bottom)); }
    :global(.compare .maplibregl-ctrl-top-right .maplibregl-ctrl-group:not(.gb-btn)) { display: none; }
  }
</style>
