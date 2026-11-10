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
  import VintageSwitch from '../components/VintageSwitch.svelte';
  import ReachControls from '../components/ReachControls.svelte';
  import RankTable, { type RankColumn } from '../components/RankTable.svelte';
  import RankOptions from '../components/RankOptions.svelte';
  import AggregateLine from '../components/AggregateLine.svelte';
  import { commuteMeta } from '../lib/commute.svelte';
  import SizeLegend from '../components/SizeLegend.svelte';
  import YearSlider from '../components/YearSlider.svelte';
  import YearTools from '../components/YearTools.svelte';
  import SmallMultiples from '../components/SmallMultiples.svelte';
  import '../lib/i18n-mapx';
  import { changeColumn, changeMeta, defaultPeriods, periodMarks, pooledSpan, pooledValues, straddled } from '../lib/yearcmp.svelte';
  import { ciSpec, crossesClass, intervals, kindOf, rankRange, unstableEither } from '../lib/reliability';
  import { unstableIndices } from '../lib/small.svelte';
  import '../lib/i18n-r3';
  import { colon, pctSep } from '../lib/typo';
  import { RefLayer, loadRefData } from '../lib/reflayer';
  import VotePicker from '../components/VotePicker.svelte';
  import VoteResult from '../components/VoteResult.svelte';
  import SpatialPanel from '../components/SpatialPanel.svelte';
  import SpatialLegend from '../components/SpatialLegend.svelte';
  import EmbedDialog from '../components/EmbedDialog.svelte';
  import { SpatialController } from '../lib/spatial.svelte';
  import { bivariate, lisaClasses, spearman } from '../lib/spatial';
  import { bivariateColours, lisaColours, BIVARIATE, LISA_COLOURS } from '../lib/spatial-colours';
  import { viewUrl } from '../lib/embed';
  import '../lib/i18n-spatial';
  import { loadVoteFile, loadVoteIndex, voteIdOf, type VoteIndex } from '../lib/votes';
  import StatsBlock from '../components/StatsBlock.svelte';
  import { buildScale, divergeCentre, unitOf, fmtNumber, fmtPeriod, fmtTick, fmtValue, isDiverging, legendItems, sortedValues } from '../lib/classify';
  import { bareAttribution, downloadBlob, figurePNG, grabMap, slug, type LegendItem } from '../lib/export';
  import { describeFilter } from '../lib/filters';
  import { FLAG, majorityMask, precisionText } from '../lib/data';
  import type { ColumnStore } from '../lib/columns.svelte';
  import {
    availableAt, flagMarks, flagsOf, isUnstable, gapReason, precisionOf, namesOf, regionalAt, placeName, shortName, loadLevel, loadFine, loadFineLines, FINE_LEVELS, attachedFrom, levelInfo, loadCH, loadReach, loadReachIndex, loadSeries, loadUnits, seriesPeriods, unavailableReason, type Base, type Hub, type LevelData,
    type MetricMeta, type ReachFile, type UnitRow, type Column, type ColumnFile,
  } from '../lib/data';
  import { catOptions, combine, evalFilter, type MatchResult } from '../lib/filters';
  import { DEFAULT_HUB, T_MAX, type CatField, type ReachMode } from '../lib/hash';
  import { CH_BOUNDS, UnitMap, geomBounds, zoomScale, type Symbol } from '../lib/mapview';
  import { ReachOverlay } from '../lib/reach';
  import { app, replaceNext } from '../lib/state.svelte';
  import { levelName, ml, t, levelWord } from '../lib/i18n.svelte';
  import { levelsOf, requestLevel } from '../lib/levels';
  import { profileHref, sourceHref } from '../lib/nav';
  import { loadReachTimes, refOf, type ReachTimes } from '../lib/places';
  import { hasStation, kindLabel, mainStation, methodText, nearestHubOf, ptKind, reachId, reachNote, reachReason, type ReachKind } from '../lib/pt';
  import { divRamp, lighten, seqRamp, token } from '../lib/theme';
  import { fmtRange, fmtSpread, loadSpread, loadSpreadIndex, spreadDef, spreadIdx, spreadOf, type SpreadFile, type SpreadIndex, type SpreadKind } from '../lib/spread';

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
  let refLayer: RefLayer | null = null;

  const metas = $derived(base.metas);
  /** unit names in the UI language (typology units carry official names per language) */
  const names = $derived(namesOf(ld));
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
  const yearPeriods = $derived(seriesPeriods(metaRaw, ld.level));
  // change between two years (hash yc / ym): a synthetic metric with a diverging scale around 0
  const cmpWanted = $derived(app.cmpFrom !== null && !whyA && yearPeriods.length > 1 && !metaRaw.per_vote && !attachedFrom(metaRaw, ld.level));
  const cmpTo = $derived(refRaw?.col.period ?? null);
  const cmpFromRef = $derived(cmpWanted ? cols.get(ld, metaRaw.id, app.cmpFrom) : null);
  const cmpOrder = $derived(cmpTo !== null && app.cmpFrom !== null && metaRaw.periods.indexOf(app.cmpFrom) >= 0 && metaRaw.periods.indexOf(app.cmpFrom) < metaRaw.periods.indexOf(cmpTo));
  const cmpActive = $derived(
    !!cmpWanted && !!refRaw && !!cmpFromRef && !refRaw.noSeries && !cmpFromRef.noSeries && !cmpFromRef.yearMissing && cmpOrder && !vdiff,
  );
  const cmpProblem = $derived.by(() => {
    if (!cmpWanted || cmpActive) return null;
    if (cmpFromRef === undefined || refRaw === undefined) return t('yc.loading');
    if (cmpFromRef === null || cmpFromRef?.noSeries || refRaw?.noSeries) return t('yc.noSeries');
    return t('yc.invalid', { y: app.cmpFrom ?? '', to: cmpTo ?? '' });
  });
  const metaChg = $derived(cmpActive ? changeMeta(metaRaw, app.cmpMode, app.cmpFrom!, cmpTo!) : null);
  const metaA = $derived<MetricMeta>(
    metaChg ? metaChg : vdiff
      ? { ...metaRaw, id: 'vote_yes_share_diff', label_en: t('vt.diffLabelEn'), label_de: t('vt.diffLabelDe'), label_fr: t('vt.diffLabelFr'),
          unit: 'pp', unit_de: 'Pp.', unit_fr: 'pp', aggregation: 'change:vote_yes_share', direction: 'neutral', decimals: 1, headline: null }
      : metaRaw,
  );
  const refChg = $derived(cmpActive && metaChg ? { ...refRaw!, meta: metaChg, file: null, col: changeColumn(cmpFromRef!.col, refRaw!.col, app.cmpMode) } : null);
  const refDiff = $derived(
    refChg ? refChg : vdiff && refRaw && chA
      ? { ...refRaw, meta: metaA, col: { ...refRaw.col, v: refRaw.col.v.map((x) => (x === null ? null : Math.round((x - chA!.value) * 100) / 100)) } }
      : refRaw,
  );
  // small numbers (D32): units whose value rests on a small base or count (flag bits 1/2)
  // B1: the latest values carry the build's flags; a past year (series file) is judged by the metric's own rule on
  // the base and count values of that year (lib/small.svelte.ts). A change is unstable when either year is.
  const unstableIdx = $derived.by(() => {
    const to = unstableIndices(cols, ld, metaRaw, refRaw);
    if (!cmpActive || !refChg) return to;
    return unstableEither(to, unstableIndices(cols, ld, metaRaw, cmpFromRef), refChg.col.v);
  });
  // 'hide': unstable values become gaps with their reason (classes, ranks and statistics leave them out);
  // 'show' / 'light': a computed column (change, past year) gets the flag bit so the card and ranking mark it
  const refA = $derived.by(() => {
    const r = refDiff;
    if (!r || !unstableIdx.length) return r;
    if (app.unstable !== 'hide') {
      if (r.file) return r;
      const f = { ...(r.col.f ?? {}) };
      for (const i of unstableIdx) f[String(i)] = (f[String(i)] ?? 0) | FLAG.small_base;
      return { ...r, col: { ...r.col, f } };
    }
    const v = r.col.v.slice();
    const notes = [...(r.col.notes ?? []), t(cmpActive ? 'r3.hiddenChg' : 'fl.hidden', { from: app.cmpFrom ?? '', to: cmpTo ?? '' })];
    const n = { ...(r.col.n ?? {}) };
    for (const i of unstableIdx) {
      v[i] = null;
      n[String(i)] = notes.length - 1;
    }
    return { ...r, col: { ...r.col, v, n, notes } };
  });
  /** values hidden as small numbers (told apart from units without data, B2) */
  const nHidden = $derived(app.unstable === 'hide' ? unstableIdx.length : 0);
  // ------------------------------------------------------------------ spatial statistics (Moran's I, clusters, bivariate)
  let spOpen = $state(app.spatial !== 'off');
  $effect(() => {
    if (app.spatial !== 'off') spOpen = true;
  });
  const sp = new SpatialController(() => ({
    ld, values: whyA || !refA ? null : refA.col.v, enabled: spOpen || app.spatial !== 'off', lisa: app.spatial === 'lisa',
  }));
  const lisaCls = $derived(app.spatial === 'lisa' && sp.lisa && sp.lisa.p.length === ld.units.length ? lisaClasses(sp.lisa, 0.05, app.fdr) : null);
  const metaB = $derived(app.metricB ? (metas.get(app.metricB) ?? null) : null);
  const refB = $derived(app.spatial === 'bi' && metaB && metaB.id !== metaRaw.id && availableAt(metaB, ld.level) ? cols.get(ld, metaB.id, app.year) : null);
  const biRes = $derived(app.spatial === 'bi' && refA && !whyA && refB ? bivariate(refA.col.v, refB.col.v) : null);
  const biRho = $derived(biRes && refA && refB ? spearman(refA.col.v, refB.col.v) : null);
  const spatialColours = $derived(lisaCls ? lisaColours(lisaCls.code) : biRes && biRes.n > 0 ? bivariateColours(biRes.cell) : null);
  /** the spatial legend replaces the shade legend while a spatial map mode is drawn */
  const spatialMode = $derived<'lisa' | 'bi' | null>(lisaCls ? 'lisa' : biRes && biRes.n > 0 && metaB ? 'bi' : null);
  function setSpatial(m: 'off' | 'lisa' | 'bi') {
    app.spatial = m;
    // a first bivariate map needs a second metric: offer a different one that exists at this level
    if (m === 'bi' && (!app.metricB || !metas.get(app.metricB) || !availableAt(metas.get(app.metricB)!, ld.level))) {
      const alt = ['pop_total', 'geo_pop_density'].map((id) => metas.get(id)).find((x) => x && x.id !== metaRaw.id && availableAt(x, ld.level));
      app.metricB = alt?.id ?? null;
    }
  }
  /** text for one unit in the spatial mode (tooltip, card) */
  function spatialText(i: number): string | null {
    if (lisaCls && sp.lisa) {
      const c = lisaCls.code[i];
      const k = c === 1 ? 'hh' : c === 2 ? 'll' : c === 3 ? 'lh' : c === 4 ? 'hl' : c === 0 ? 'ns' : null;
      if (!k) return t('sp.lisa.none');
      return k === 'ns' ? t('sp.lisa.ns') : `${t(`sp.lisa.${k}`)} · p = ${fmtNumber(sp.lisa.p[i], 3)}`;
    }
    if (biRes && metaB) {
      const c = biRes.cell[i];
      return c < 0 ? t('lg.noData') : `${ml(metaA)}: ${t(`sp.bi.third.${c % 3}`)} · ${ml(metaB)}: ${t(`sp.bi.third.${Math.floor(c / 3)}`)}`;
    }
    return null;
  }
  /** legend rows of the spatial map for the PNG export */
  function spatialLegendItems(): LegendItem[] | null {
    if (lisaCls) {
      const c = lisaCls.counts;
      return (['hh', 'll', 'lh', 'hl', 'ns'] as const).map((k) => ({ colour: LISA_COLOURS[k], label: `${t(`sp.lisa.${k}`)} (${fmtNumber(c[k], 0)})` }));
    }
    if (biRes && metaB) {
      return [2, 1, 0].flatMap((b) => [0, 1, 2].map((a) => ({
        colour: BIVARIATE[3 * b + a], label: `${ml(metaA)}: ${t(`sp.bi.third.${a}`)} · ${ml(metaB)}: ${t(`sp.bi.third.${b}`)} (${fmtNumber(biRes.counts[3 * b + a], 0)})`,
      })));
    }
    return null;
  }

  // D21: a value published for a coarser area (labour market area, canton) attached to municipalities
  const regional = $derived(whyA ? null : regionalAt(metaRaw, ld.level));
  let regionGeo = $state.raw<{ level: string; fc: import('geojson').FeatureCollection } | null>(null);
  $effect(() => {
    const r = regional;
    if (r && regionGeo?.level !== r) loadLevel(r).then((d) => (regionGeo = { level: r, fc: d.geo })).catch(() => {});
  });
  $effect(() => {
    const fc = regional && regionGeo?.level === regional ? regionGeo.fc : null;
    void ld;
    if (mapReady) view!.setRegions(fc, fc ? regional : null);
  });
  // pooled multi-year rate of this annual metric, or the annual metric of this pooled one
  const pooledAlt = $derived(
    metaRaw.pooled ? metas.get(metaRaw.pooled.of) ?? null : (base.metrics.find((m) => m.pooled?.of === metaRaw.id && m.levels.includes(ld.level)) ?? null),
  );
  const colA = $derived(refA?.col);
  // U6: a regional value (canton rent on municipalities) is one value per region: classes, legend, histogram and
  // statistics count the regions (26 cantons), not the 2'110 municipal copies
  const regionKey = $derived.by<string[] | null | undefined>(() => {
    const r = regional;
    if (!r) return null;
    if (r === 'kanton') return ld.canton;
    if (!unitRows) return undefined;
    const out: string[] = new Array(nUnits).fill('');
    for (const row of unitRows) {
      if (row.level !== 'gemeinde') continue;
      const i = ld.index.get(row.id);
      const k = (row as unknown as Record<string, unknown>)[r];
      if (i !== undefined && typeof k === 'string') out[i] = k;
    }
    return out;
  });
  const native = $derived.by(() => {
    const key = regionKey;
    if (!key || !colA || !regional) return null;
    const first = new Map<string, number>();
    const inMask = new Map<string, number>();
    for (let i = 0; i < nUnits; i++) {
      const k = key[i];
      if (!k) continue;
      if (!first.has(k)) first.set(k, i);
      if (match.m[i]) inMask.set(k, 1);
    }
    const ks = [...first.keys()];
    const idx = ks.map((k) => first.get(k)!);
    const rowName = (k: string) => {
      const r = unitRows?.find((u) => u.level === regional && u.id === k);
      return r ? shortName(regional, placeName(regional, k, r.name)) : k;
    };
    return {
      v: idx.map((i) => colA.v[i]),
      names: ks.map(rowName),
      cantons: ks.map((k, j) => (regional === 'kanton' ? '' : ld.canton[idx[j]])),
      mask: Uint8Array.from(ks, (k) => inMask.get(k) ?? 0),
      word: levelWord(regional),
    };
  });
  const scaleA = $derived.by(() => {
    if (!colA) return null;
    const v = native?.v ?? colA.v;
    const s = sortedValues(v);
    return s.length ? buildScale(v, app.cls, isDiverging(metaA, s), seqRamp(), divRamp(), divergeCentre(metaA), fixedRef ?? undefined) : null;
  });
  /** colour of every unit (a regional scale is built on the regions, then applied to their municipalities) */
  const unitColours = $derived.by(() => {
    if (!scaleA || !colA) return null;
    if (!native) return scaleA.unitColour;
    return colA.v.map((x) => (x === null || !Number.isFinite(x) ? null : scaleA!.colourOf(x)));
  });
  // class limits fixed across years (hash fx): from all years pooled, so the slider does not re-classify
  const fixedOn = $derived(app.fixed && !cmpActive && !vdiff && !whyA && yearPeriods.length > 1);
  const pooledRef = $derived(fixedOn ? pooledValues(metaRaw, ld.level) : null);
  const fixedRef = $derived(pooledRef ?? null);
  const periodNotes = $derived(periodMarks(metaRaw));
  // U8: a vote far from 50 % (|CH - 50| > 15 points) colours almost every place the same: show it as the
  // difference from Switzerland by default (once per vote; the reader can switch back) and say why
  let vdAuto: string | null = null;
  let vdAutoOn = $state<string | null>(null);
  const lopsided = $derived(metaRaw.id === 'vote_yes_share' && !!chA && !!refRaw && chA.period === refRaw.col.period && Math.abs(chA.value - 50) > 15);
  $effect(() => {
    const id = voteShown;
    if (!id || metaRaw.id !== 'vote_yes_share' || !chA || !refRaw || chA.period !== refRaw.col.period || vdAuto === id) return;
    vdAuto = id;
    if (lopsided && !app.vdiff) {
      replaceNext();
      app.vdiff = true;
      vdAutoOn = id;
    }
  });
  const legendNotes = $derived.by(() => {
    const out: string[] = [];
    if (lopsided && chA) out.push(t(vdiff && vdAutoOn === voteShown ? 'ux.voteDiffAuto' : vdiff ? 'ux.voteOneSide' : 'ux.voteOneSide', { pct: `${fmtNumber(chA.value, 1)} %` }));
    if (cmpActive && app.cmpFrom && cmpTo) {
      const sb = straddled(metaRaw, yearPeriods, app.cmpFrom, cmpTo, periodNotes);
      if (sb.length) out.push(t('yc.straddleShort', { years: sb.map((x) => x.p).join(', ') }));
    }
    if (fixedOn) {
      if (pooledRef === undefined) out.push(t('yc.fixedWait'));
      else if (pooledRef) out.push(t('yc.fixedNote', { span: pooledSpan(metaRaw) }));
    }
    return out;
  });
  /** U11: "Change in X, 2010→2025 (percentage points)" */
  const legendTitle = $derived.by(() => {
    if (!cmpActive || !metaChg || !app.cmpFrom || !cmpTo) return null;
    const u = metaChg.unit === 'pp' ? t('ux.ppFirst') : unitOf(metaChg);
    return `${t('ux.chgTitle', { metric: ml(metaRaw), from: app.cmpFrom, to: cmpTo })}${u ? ` (${u})` : ''}`;
  });
  /** U13: sparse metrics (partial coverage): the warning goes on top of the legend, with a zoom to the data */
  const sparse = $derived.by(() => {
    if (!colA || whyA || native) return null;
    let n = 0;
    for (const x of colA.v) if (x !== null) n++;
    if (n === 0 || n >= nUnits * 0.6) return null;
    const idx: number[] = [];
    for (let i = 0; i < nUnits; i++) if (colA.v[i] !== null) idx.push(i);
    return { n, idx };
  });
  // B2: values hidden as small numbers are not "no data": the banner tells them apart and offers to show them
  const legendWarn = $derived.by(() => {
    if (!sparse) return null;
    const vars = { n: fmtNumber(sparse.n, 0), total: fmtNumber(nUnits, 0), units: word, pct: `${fmtNumber((100 * sparse.n) / nUnits, 0)}${pctSep()}%` };
    const zoom = { action: t('ux.zoomData'), onaction: () => zoomTo(sparse!.idx) };
    if (!nHidden) return { text: t('ux.sparse', vars), ...zoom };
    const g = nUnits - sparse.n - nHidden;
    return {
      text: t(g > 0 ? 'r3.sparseHidden' : 'r3.sparseHiddenOnly', { ...vars, h: fmtNumber(nHidden, 0), g: fmtNumber(g, 0) }),
      action: t('r3.showThem'), onaction: () => (app.unstable = 'show'), action2: zoom.action, onaction2: zoom.onaction,
    };
  });
  const smPooled = $derived(app.multi !== null && yearPeriods.length > 1 ? pooledValues(metaRaw, ld.level) : undefined);

  // reliability of survey and modelled values: the published 95 % interval (companion metric <id>_ci), else a badge
  const ciS = $derived(!whyA && !cmpActive && !vdiff ? ciSpec(metaRaw, metas, ld.level) : null);
  const ciRef = $derived(ciS ? cols.get(ld, ciS.meta.id, app.year) : null);
  const ivs = $derived(ciS && ciRef && refA && ciRef.col.period === refA.col.period ? intervals(refA.col.v, ciRef.col.v, ciS.relative) : null);
  const relLegend = $derived.by(() => {
    if (whyA || cmpActive || vdiff) return null;
    const k = kindOf(metaRaw.precision, !!ivs);
    if (!k) return null;
    let extra: string | null = null;
    if (ivs && scaleA) {
      let n = 0, crossing = 0;
      for (const iv of ivs) {
        if (!iv) continue;
        n++;
        if (crossesClass(scaleA, iv)) crossing++;
      }
      extra = t('rl.cross', { n: fmtNumber(n, 0), m: fmtNumber(nUnits, 0), k: fmtNumber(crossing, 0) });
    }
    return { kind: k, text: t(`rl.${k}`), extra };
  });
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
    // a column without its latest-values file is a past year, another vote, or a regional value attached
    // to municipalities (attachedFrom): only the first two have a series or vote file to read from
    const past = ref && ref.file === null && !attachedFrom(m, ld.level) ? ref.col.period : null;
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
    } else if (m.levels.includes('schweiz')) {
      loadCH(m.file).then((f) => {
        if (!live) return;
        const c = f?.metrics[m.id];
        chA = c && c.v[0] !== null ? { value: c.v[0]!, period: c.period } : null;
      });
    }
    return () => (live = false);
  });

  // national change between the two years (from the series row of Switzerland)
  let chCmp = $state.raw<{ value: number; period: string } | null>(null);
  $effect(() => {
    const on = cmpActive;
    const id = metaRaw.id;
    const a = app.cmpFrom;
    const b = cmpTo;
    const mode = app.cmpMode;
    let live = true;
    chCmp = null;
    if (!on || !a || !b) return;
    loadSeries(id).then((s) => {
      if (!s || !live) return;
      const row = s.levels.schweiz?.CH;
      const xa = row?.[s.periods.indexOf(a)];
      const xb = row?.[s.periods.indexOf(b)];
      if (xa === null || xa === undefined || xb === null || xb === undefined) return;
      const x = mode === 'abs' ? xb - xa : xa === 0 ? null : ((xb - xa) / Math.abs(xa)) * 100;
      if (x !== null) chCmp = { value: x, period: `${a}→${b}` };
    }).catch(() => {});
    return () => (live = false);
  });

  // ------------------------------------------------------------------ size (proportional symbols)
  const symbolsMode = $derived(app.display === 'symbols');
  const sizeMeta = $derived<MetricMeta | undefined>(metas.get(app.size ?? (symbolsMode ? 'pop_total' : '')));
  const whyS = $derived(sizeMeta ? unavailableReason(sizeMeta, ld.level) : null);
  const sizeRef = $derived(sizeMeta && !whyS ? cols.get(ld, sizeMeta.id, app.year) : null);
  // units.json (names, label points, regions) is loaded once symbols or categorical filters are used
  const needRows = $derived(!!sizeMeta || app.filters.some((f) => f.kind === 'cat') || app.tab === 'rank' || (!!regional && regional !== 'kanton') || (!desktop && mapReady));
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
    autoSym = null;
    if (d === 'choropleth') keepChoro = true;
    if (d === 'symbols' && !app.size) app.size = 'pop_total';
  }
  // Counts (sums) are drawn as proportional circles by default, since shading would favour large units.
  // Picking a count in the shade picker switches to circles sized by it; picking another metric switches
  // back. Choosing "Shaded" once keeps shading for counts. Links (hash) are never changed.
  let autoSym = $state<string | null>(null);
  let keepChoro = false;
  function pickShade(id: string) {
    const m = metas.get(id);
    const isCount = !!m && m.aggregation === 'sum' && !m.per_vote && availableAt(m, ld.level);
    if (autoSym && !isCount) {
      if (app.size === autoSym) app.size = null;
      app.display = 'choropleth';
      autoSym = null;
    }
    app.metric = id;
    if (isCount && !keepChoro && (app.display === 'choropleth' || autoSym)) {
      app.size = id;
      app.display = 'symbols';
      autoSym = id;
      // U7: never a silent switch: a short toast says why, with the way back
      showToast(t('ux.symToast', { metric: ml(m) }));
    }
  }
  let toast = $state<string | null>(null);
  let toastTimer: ReturnType<typeof setTimeout> | undefined;
  function showToast(text: string) {
    toast = text;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toast = null), 6000);
  }
  /** U7: circles sized by the shaded count: one circle colour, the legend shows the circles only */
  const sizeOnly = $derived(symbolsMode && !!sizeMeta && sizeMeta.id === metaA.id);
  function shadeInstead() {
    toast = null;
    keepChoro = true;
    if (app.size === autoSym) app.size = null;
    app.display = 'choropleth';
    autoSym = null;
  }

  // ------------------------------------------------------------------ filters
  const hubName = (slug: string) => hubs.find((h) => h.slug === slug)?.name ?? slug;
  const evals = $derived(
    app.filters.map((f) =>
      evalFilter(f, { ld, rows: unitRows, metas, hubName, col: (id) => cols.get(ld, id, app.year) }),
    ),
  );
  /** the stacked filter conditions alone */
  const fmatch = $derived(combine(evals, nUnits));
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
    if ((reachOn || app.filters.some((f) => f.kind === 'reach') || /_nearest_hub$/.test(metaA.id)) && !rt) loadReachTimes().then((x) => (rt = x)).catch(() => {});
  });
  const rtIndex = $derived(rt ? new Map(rt.units.map((u, k) => [u, k])) : undefined);
  const reachCol = $derived(reachRef?.col ?? null);
  const reachFile = $derived(reachOn ? reachNets[`${hub.slug}_${reachMode}`] : undefined);
  const reachedCount = $derived.by(() => {
    if (!reachCol) return null;
    let n = 0;
    for (let i = 0; i < reachCol.v.length; i++) {
      const x = reachCol.v[i];
      if (x !== null && x <= app.t && fmatch.m[i]) n++;
    }
    return n;
  });
  /** 1 = reached within the slider time (null: no travel times at this level / hub) */
  const reachMask = $derived.by(() => {
    if (!reachCol) return null;
    const m = new Uint8Array(nUnits);
    const lim = app.t;
    for (let i = 0; i < nUnits; i++) {
      const x = reachCol.v[i];
      if (x !== null && x <= lim) m[i] = 1;
    }
    return m;
  });
  /** U1: "only places within N min" makes reach a filter (match count, ranking, aggregate, statistics) */
  const reachFilter = $derived(app.ronly && reachOn && !!reachMask);
  const match = $derived.by<MatchResult>(() => {
    if (!reachFilter || !reachMask) return fmatch;
    const m = new Uint8Array(nUnits);
    let n = 0;
    for (let i = 0; i < nUnits; i++) {
      m[i] = fmatch.m[i] & reachMask[i];
      n += m[i];
    }
    return { m, n, nMissingOnly: fmatch.nMissingOnly, active: fmatch.active + 1 };
  });
  const filtered = $derived(match.active > 0);
  // car networks can be held back by the licence gate: the index lists the files of this build
  const carAvailable = $derived(carFiles ? carFiles.has(hub.slug) : reachNets[`${hub.slug}_car`] !== null);
  onMount(() => {
    loadReachIndex().then((ix) => {
      if (!ix) return;
      if (ix.hubs?.length) {
        hubs = ix.hubs;
        const known = new Set(ix.hubs.map((h) => h.slug));
        // U4: a starting point or reach condition from a link that does not exist: say so and clean the link
        const notes: string[] = [];
        if (!known.has(app.hub)) {
          const fb = known.has(DEFAULT_HUB) ? DEFAULT_HUB : ix.hubs[0].slug;
          notes.push(t('ux.badHub', { id: app.hub, hub: ix.hubs.find((h) => h.slug === fb)?.name ?? fb }));
          app.hub = fb;
        }
        const fs = app.filters.filter((f) => (f.kind !== 'reach' || known.has(f.hub)) && (f.kind !== 'commute' || f.hubs.every((h) => known.has(h))));
        if (fs.length !== app.filters.length) {
          notes.push(t('ux.badFilter', { n: app.filters.length - fs.length }));
          app.filters = fs;
        }
        if (notes.length) {
          replaceNext();
          app.notice = [app.notice, ...notes].filter(Boolean).join(' ');
        }
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
    if (app.sel !== null && !ld.index.has(app.sel)) {
      replaceNext();
      app.sel = null;
    }
  });
  function select(i: number | null) {
    choose = null;
    app.sel = i === null ? null : ld.units[i];
    if (i !== null && !desktop) sheetOpen = false;
  }
  // U16: on a phone at the national zoom a finger covers several small municipalities. A tap snaps to the
  // nearest label point among the units around it (a tap on the Zürich dot selects Zürich, not Neftenbach);
  // when two label points are about equally near, the three nearest are offered.
  let choose = $state<{ x: number; y: number; w: number; ids: number[] } | null>(null);
  const SNAP_ZOOM = 9.5;
  function tap(i: number | null, p: { x: number; y: number }) {
    if (!view || desktop || !labels || view.map.getZoom() >= SNAP_ZOOM) {
      select(i);
      return;
    }
    const near = view.unitsNear(p, 16);
    if (near.length <= 1) {
      select(i ?? near[0] ?? null);
      return;
    }
    const scored = near
      .map((k) => {
        const lp = labels![k];
        if (!lp) return { k, d: Infinity };
        const q = view!.map.project(lp as [number, number]);
        return { k, d: Math.hypot(q.x - p.x, q.y - p.y) };
      })
      .filter((x) => Number.isFinite(x.d))
      .sort((a, b) => a.d - b.d);
    if (!scored.length) {
      select(i);
      return;
    }
    const [a, b] = scored;
    if (b && a.d < 14 && b.d < 14 && b.d < a.d * 1.25) {
      choose = { x: p.x, y: p.y, w: mapEl.clientWidth, ids: scored.slice(0, 3).map((x) => x.k) };
      return;
    }
    select(a.d < 18 ? a.k : i);
  }

  // ------------------------------------------------------------------ map
  onMount(() => {
    view = new UnitMap(mapEl, base, {
      onSelect: select, onTap: tap, onHover: (i, p) => { hover = i; hoverAt = i === null ? null : p; },
      onReset: () => fit(true), resetLabel: () => t('map.reset'),
      ...(app.embed ? {} : { onFull: () => setFull(!full), fullLabel: () => t(full ? 'map.fullExit' : 'map.full'), isFull: () => full }),
      onLabels: () => (app.labels = !app.labels), labelsLabel: () => t('lb.toggle'), labelsOn: () => app.labels,
    }, { fine: { units: loadFine, lines: loadFineLines, levels: FINE_LEVELS } });
    refLayer = new RefLayer(view.map, mapEl);
    refLayer.setVisible(app.labels);
    // U17: city and lake names only once the polygons are drawn
    overlay = new ReachOverlay(view.map, mapEl);
    view.map.on('zoom', () => (zf = zoomScale(view!.map.getZoom())));
    view.map.on('movestart', (e) => {
      if ((e as { originalEvent?: unknown }).originalEvent) userMoved = true;
    });
    if (new URLSearchParams(location.search).has("debug")) Object.assign(window, { __map: view.map, __ref: refLayer });
    view.ready.then(() => {
      mapReady = true;
      fit();
      zf = zoomScale(view!.map.getZoom());
      view!.map.once('idle', () => {
        onrendered?.();
        loadRefData(base).then((d) => refLayer?.setData(d)).catch(() => {});
      });
    });
    // the map follows its box (sheet folded or opened, reach bar shown): refit while the reader has not moved it
    const ro = new ResizeObserver(() => {
      view?.map.resize();
      if (mapReady && !userMoved && !focus) fit();
    });
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
    if (desktop) return { top: 56, bottom: 24, left: 24, right: 56 };
    // phone: the level bar on top; the sheet sits below the map (it does not cover it)
    // the floating legend sits at the bottom of the map while the sheet is folded
    return { top: 52, bottom: !sheetOpen && selIdx === null ? 100 : 12, left: 10, right: 10 };
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

  const lightSet = $derived(app.unstable === 'light' && unstableIdx.length ? new Set(unstableIdx) : null);
  const colours = $derived.by(() => {
    if (!scaleA || whyA) return ld.units.map(() => null);
    const outFill = token('--muted-fill') || '#ececec';
    const one = token('--seq-3') || '#6290bb';
    const out = (spatialColours ?? (sizeOnly && colA ? colA.v.map((x) => (x === null ? null : one)) : null) ?? unitColours ?? scaleA.unitColour).slice();
    for (let i = 0; i < out.length; i++) {
      const c = out[i];
      if (c === null || c === undefined) continue;
      // D5 / U1: filtered out = one flat fill; not reached (reach shown, not filtering) = a pale tint of its class
      if (!match.m[i]) out[i] = outFill;
      else if (lightSet && lightSet.has(i)) out[i] = lighten(c, 0.62);
      else if (reachMask && !reachMask[i]) out[i] = lighten(c, 0.78);
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
  // D37: single-seat cantons whose party shares are kept apart get their own pattern
  $effect(() => {
    const mk = !whyA && colA ? majorityMask(colA, nUnits) : null;
    void ld;
    if (mapReady) view!.setMajority(mk);
  });
  $effect(() => {
    const h = hover;
    if (mapReady) view!.setHover(h);
  });
  $effect(() => {
    const f = reachFile ?? null;
    const on = reachOn;
    if (mapReady) {
      overlay!.setNetwork(f);
      refLayer!.setAvoid(on ? overlay!.hubLngLat : null);
    }
  });
  $effect(() => {
    const on = reachOn;
    if (mapReady) overlay!.setVisible(on);
  });
  $effect(() => {
    const on = app.labels;
    if (mapReady) {
      refLayer!.setVisible(on);
      view!.relabel();
    }
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
  /** D7: on desktop the right panel stays closed (the map gets the room) until a place is selected or the
   *  Ranking / Statistics tab is opened */
  const sideOpen = $derived(desktop && !app.embed && (selIdx !== null || app.tab === 'rank' || app.tab === 'stats'));
  function closeSide() {
    app.sel = null;
    app.tab = null;
  }
  function openTab(id: string) {
    // the open tab tapped again folds the sheet away
    if (sheetOpen && phoneTab === id) {
      sheetOpen = false;
      return;
    }
    app.tab = id === 'map' ? null : id;
    sheetOpen = true;
  }
  let dragY: number | null = null;
  /** the reach bar's hub button: the Map tab, scrolled to the reach controls */
  function openReach() {
    app.tab = null;
    sheetOpen = true;
    tick().then(() => document.getElementById('reach-sec')?.scrollIntoView({ block: 'start', behavior: 'smooth' }));
  }
  const rankCols = $derived.by(() => {
    const out: RankColumn[] = [];
    const seen = new Set<string>();
    const push = (key: string, tag: string, ref: { meta: MetricMeta; col: Column; file?: ColumnFile | null } | null | undefined, label?: string) => {
      if (!ref || seen.has(key)) return;
      seen.add(key);
      const f = ref.file ?? null;
      const col = ref.col;
      const marks = col.f ? (i: number) => flagMarks(f, flagsOf(f, col, i)) : undefined;
      out.push({ key, tag, meta: ref.meta, v: ref.col.v, period: ref.col.period, label, marks });
    };
    if (!whyA) {
      push(metaA.id, 'Shade', refA);
      if (nHidden && out.length) out[out.length - 1].hiddenNote = t('r3.csvHidden');
    }
    if (sizeMeta) push(sizeMeta.id, 'Size', sizeRef);
    for (const e of evals) {
      if (e.status === 'active' && e.values && e.filter.kind === 'commute') {
        const cm = commuteMeta(e.filter, hubName);
        if (!seen.has(cm.id)) {
          seen.add(cm.id);
          out.push({ key: cm.id, tag: 'Filter', meta: cm, label: e.label, v: e.values, period: cm.latest });
        }
        continue;
      }
      if (e.status !== 'active' || !e.col) continue;
      if (e.filter.kind === 'reach') push(e.col.meta.id, 'Filter', e.col, t('mv.to', { mode: kindLabel(e.filter.mode, station, true), hub: e.hubName ?? '' }));
      else push(e.col.meta.id, 'Filter', e.col);
    }
    if (reachMode === 'pt' && station) {
      if (stRef) push(stRef.meta.id, 'Reach', stRef, t('mv.to', { mode: kindLabel('ptst', true), hub: hub.name }));
      if (ddRef) push(ddRef.meta.id, 'Reach', ddRef, t('mv.to', { mode: kindLabel('pt', true, true), hub: hub.name }));
    } else if (reachRef && reachCol) push(reachRef.meta.id, 'Reach', reachRef, t('mv.to', { mode: kindLabel(reachKind, station), hub: hub.name }));
    // columns added by hand (URL: xc=)
    for (const id of app.xcols) {
      const r = cols.get(ld, id, app.year);
      if (r) push(id, 'Added', r);
    }
    return out;
  });
  // minimum population of the ranking table (URL: rmin=, rmf=1): hide smaller units, or only flag them
  const popRef = $derived(cols.get(ld, 'pop_total', app.year));
  const belowMin = $derived.by(() => {
    const s = new Set<number>();
    const pv = popRef?.col.v;
    if (!app.rmin || !pv) return s;
    for (let i = 0; i < nUnits; i++) {
      const p = pv[i];
      if (match.m[i] && p !== null && p !== undefined && p < app.rmin) s.add(i);
    }
    return s;
  });
  const rankRows = $derived.by(() => {
    const out: number[] = [];
    const hide = !!app.rmin && !app.rflag;
    for (let i = 0; i < nUnits; i++) if (match.m[i] && !(hide && belowMin.has(i))) out.push(i);
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
      const lc = refLayer?.snapshot(img.width, img.height, img.width / Math.max(1, mapEl.clientWidth));
      if (lc) layers.push(lc);
      const sLeg = spatialLegendItems();
      const legend: LegendItem[] = sLeg ?? legendItems(scaleA, metaA);
      if (!sLeg && scaleA.n < nUnits) legend.push({ colour: null, label: t('lg.noData') });
      if (lightSet) legend.push({ colour: lighten(scaleA.classColours[3] ?? '#356799', 0.62), label: t('fl.legendLight') });
      if (filtered) legend.push({ colour: token('--muted-fill') || '#ececec', label: t('ex.notMatching') });
      if (reachOn && reachMask && !reachFilter) legend.push({ colour: lighten(scaleA.classColours[2] ?? '#6290bb', 0.78), label: t('ux.notReached', { t: Math.round(app.t) }) });
      const lo = scaleA.lo, hi = scaleA.hi;
      const gradient = !sLeg && scaleA.method === 'continuous'
        ? { colours: Array.from({ length: 9 }, (_, k) => scaleA!.colourOf(lo + ((hi - lo) * k) / 8)), lo: fmtTick(lo, metaA), hi: fmtTick(hi, metaA) }
        : null;
      const src = base.sources.get(metaA.source);
      const sub = [unitOf(metaA), fmtPeriod(colA.period, true), levelName(ld.level), t(`lg.m.${app.cls}`)].filter(Boolean).join(' · ');
      const extra: string[] = [];
      if (filtered) extra.push(`${t('tab.filters')}: ${evals.map((e) => describeFilter(e, (f, id) => catOpts(f).find((o) => o.id === id)?.name ?? id)).join('; ')} (${t('mv.nMatch', { n: fmtNumber(match.n, 0), total: fmtNumber(nUnits, 0) })})`);
      if (reachOn) extra.push(`${t('rc.from')} ${hub.name}: ${kindLabel(reachKind, station, true)} ≤ ${Math.round(app.t)} min. ${methodText(reachKind, hub.name, rt, station)}`);
      const blob = await figurePNG({
        layers, scale: img.width / Math.max(1, mapEl.clientWidth), title: spatialMode === 'bi' && metaB ? t('sp.legendBi', { a: ml(metaA), b: ml(metaB) }) : spatialMode === 'lisa' ? t('sp.legendTitle', { metric: ml(metaA) }) : ml(metaA), subtitle: [sub, ...extra].join('\n'),
        legend: gradient ? [] : legend, gradient,
        credits: [
          `${t('lg.source')}: ${bareAttribution(src?.attribution || src?.publisher || metaA.source)} · ${fmtPeriod(colA.period)} · ${precisionText(metaA.precision)}`,
          `${t('ex.boundaries')} · ${t('ex.made')}`,
        ],
        link: t('ex.view', { url: location.href }),
      });
      downloadBlob(blob, `atlas-${slug(ml(metaA))}-${slug(colA.period)}.png`);
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
        return reachReason(rt, kind, hub.slug, uid, rtIndex) ?? gapReason(ref.file, ref.col, selIdx, ref.meta, ld.canton[selIdx]);
      };
      if (reachMode === 'pt' && station && ld.level === 'gemeinde') {
        // D31: station time towards the hub as the headline, door to door as the second line
        const st = stRef?.col.v[selIdx] ?? null;
        const dd = ddRef?.col.v[selIdx] ?? null;
        const x = reachKind === 'ptst' ? st : dd;
        reach = {
          label, short: label, hub: hub.name, minutes: x, within: x !== null && x <= app.t, reason: null,
          station: {
            minutes: st, from: mainStation(rt, uid, rtIndex), reason: st === null ? miss(stRef, 'ptst') : null, name: names[selIdx],
            note: st !== null ? reachNote(rt, 'ptst', hub.slug, uid, rtIndex) : null,
          },
          door: { minutes: dd, reason: dd === null ? miss(ddRef, 'pt') : null },
          active: reachKind,
          method: methodText(reachKind, hub.name, rt, true),
          spread: spreadCard(uid),
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
    // D37: the leaning ratio leaves the centre bloc out; its share is shown alongside
    if (metaA.id === 'nrw_leaning' && centreRef) {
      const cm = metas.get('nrw_share_bloc_centre');
      const x = centreRef.col.v[i] ?? centreRef.col.m?.[String(i)] ?? null;
      if (cm) extra.push({ label: ml(cm), value: x === null ? t('lg.noData') : `${fmtValue(x, cm)} (${centreRef.col.period})` });
    }
    const notes: string[] = [];
    // D39: a nearest-hub figure names its hub and says which hubs count
    if (/^reach_(ptst|pt|car)_nearest_hub$/.test(metaA.id) && ld.level === 'gemeinde') {
      // the hub's name already comes with the value's own note ("nearest hub: Luzern"); add it only when missing
      const h = nearestHubOf(rt, metaA.id, ld.units[i], rtIndex);
      const named = refA?.col.n?.[String(i)] !== undefined;
      if (h && !named) extra.push({ label: t('pt.nearestHub'), value: h });
      notes.push(t('pt.nearestSet'));
    }
    // D37 / D16: canton Jura on today's boundaries includes Moutier (voted in canton Bern until 2025)
    if (ld.level === 'kanton' && (ld.units[i] === 'JU' || ld.units[i] === 'BE') && (metaA.id.startsWith('nrw_') || metaA.id.startsWith('vote_')))
      notes.push(t(ld.units[i] === 'JU' ? 'card.juMoutier' : 'card.beMoutier'));
    const stx = spatialText(i);
    if (stx) extra.push({ label: t('sp.title'), value: stx });
    // B1: a change is flagged when either year rests on small numbers
    if (cmpActive && app.unstable !== 'hide' && unstableIdx.includes(i)) notes.push(t('r3.chgEither', { from: app.cmpFrom ?? '', to: cmpTo ?? '' }));
    // reliability of this unit's value: its 95 % interval, or the survey / modelled sentence
    let ci = null;
    let relText: string | null = null;
    if (!cmpActive && !vdiff && refA) {
      const iv = ivs?.[i] ?? null;
      if (iv && scaleA) ci = { ...iv, rank: rankRange(refA.col.v, ivs!, i, metaRaw.direction), crosses: crossesClass(scaleA, iv) };
      else {
        const k = kindOf(precisionOf(refA.file, refA.col, i, metaA), !!ivs);
        relText = ivs && refA.col.v[i] !== null ? t('rl.noCi') : k === 'survey' || k === 'modelled' ? t(`rl.${k}`) : null;
      }
    }
    return { i, reach, sub, extra, notes, ci, relText };
  });
  // C1: the morning spread of the shown hub (one file per hub, loaded while public-transport reach is on)
  let spreadIx = $state.raw<SpreadIndex | null>(null);
  let spreadF = $state.raw<SpreadFile | null>(null);
  $effect(() => {
    const on = reachOn && reachMode === 'pt' && ld.level === 'gemeinde';
    const h = hub.slug;
    let live = true;
    if (!on) return;
    loadSpreadIndex().then((x) => live && (spreadIx = x)).catch(() => {});
    loadSpread(h).then((f) => live && (spreadF = f)).catch(() => {});
    return () => (live = false);
  });
  function spreadCard(uid: string) {
    if (!spreadIx || !spreadF || spreadF.hub !== hub.slug) return null;
    const k = spreadIdx(spreadIx, uid);
    if (k < 0) return null;
    const line = (kind: SpreadKind) => {
      const out = {
        to: fmtSpread(spreadOf(spreadF!, k, 'to', kind, 'journey')),
        from: fmtSpread(spreadOf(spreadF!, k, 'from', kind, 'journey')),
        waitTo: fmtRange(spreadOf(spreadF!, k, 'to', kind, 'with_wait')),
        waitFrom: fmtRange(spreadOf(spreadF!, k, 'from', kind, 'with_wait')),
      };
      return out.to || out.from ? out : null;
    };
    return { st: line('pt_station'), dd: line('pt'), title: `${t('sp2.legend')} ${spreadDef(spreadIx, 'with_wait', app.lang)}` };
  }
  const centreRef = $derived(metaA.id === 'nrw_leaning' ? cols.get(ld, 'nrw_share_bloc_centre', app.year) : null);
  const tip = $derived.by(() => {
    if (hover === null || !hoverAt || !colA) return null;
    const fmt = (x: number | null | undefined, m: MetricMeta) => (x === null || x === undefined ? t('lg.noData') : fmtValue(x, m));
    const rows = [fmt(colA.v[hover], metaA)];
    if (sizeMeta && sizeRef && sizeMeta.id !== metaA.id) rows.push(`○ ${fmt(sizeRef.col.v[hover], sizeMeta)}`);
    const stx = spatialText(hover);
    if (stx) rows.push(stx);
    return rows;
  });
  // embed mode: attribution line and the link to the full view
  const embedCredit = $derived.by(() => {
    const ids = [metaA.source, spatialMode === 'bi' && metaB ? metaB.source : null].filter((x, k, a): x is string => !!x && a.indexOf(x) === k);
    const srcs = ids.map((id) => bareAttribution(base.sources.get(id)?.attribution || base.sources.get(id)?.publisher || id));
    return [`${t('lg.source')}: ${srcs.join('; ')}${colA ? ` · ${fmtPeriod(colA.period)}` : ''}`, t('ex.boundaries')].join(' · ');
  });
  const fullHref = $derived(app.embed ? viewUrl(false) : '');
</script>

{#snippet reachHead()}
  {#if reachOn && reachedCount !== null}
    <p class="rhead">
      {#if reachFilter}{t('ux.rankReachOn', { t: Math.round(app.t), hub: hub.name, what: kindLabel(reachKind, station, true) })}
        <button type="button" class="link" onclick={() => (app.ronly = false)}>{t('ux.showAll')}</button>
      {:else}{t('ux.rankReach', { n: fmtNumber(reachedCount, 0), t: Math.round(app.t), hub: hub.name, what: kindLabel(reachKind, station, true) })}
        <button type="button" class="link" onclick={() => (app.ronly = true)}>{t('ux.onlyThese')}</button>
      {/if}
    </p>
  {/if}
{/snippet}
{#snippet rankSnip()}
  {@render reachHead()}
  {#if rankCols.length}
    <RankOptions metrics={base.metrics} {metas} level={ld.level} xcols={app.xcols} rmin={app.rmin} rflag={app.rflag}
      hasPop={popRef !== null} nBelow={belowMin.size} unitWord={word}
      onadd={(id) => { if (!app.xcols.includes(id)) app.xcols = [...app.xcols, id]; }}
      onremove={(id) => (app.xcols = app.xcols.filter((x) => x !== id))}
      onmin={(n) => (app.rmin = n)} onflag={(f) => (app.rflag = f)} />
    <RankTable small={app.rflag && app.rmin ? belowMin : undefined} columns={rankCols} rows={rankRows} names={names} cantons={ld.canton} showCanton={ld.level === 'gemeinde' || ld.level === 'bezirk'}
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
    <StatsBlock meta={metaA} v={native?.v ?? colA.v} period={colA.period} names={native?.names ?? names} cantons={native?.cantons ?? ld.canton} ch={vdiff && chA ? { value: 0, period: chA.period } : cmpActive ? chCmp : chA} sel={null}
      source={base.sources.get(metaA.source)} unitWord={native?.word ?? word} mask={filtered ? (native?.mask ?? match.m) : null} />
  {:else}
    <p class="foot">{whyA ?? t('status.loading')}</p>
  {/if}
{/snippet}

<main class="stage" class:full={full || app.embed} class:embed={app.embed} class:sideopen={sideOpen} class:siderank={sideOpen && deskTab === 'rank'} id="main" tabindex="-1">
  <h1 class="sr-only">{t('mv.h1', { metric: ml(metaA), units: levelName(ld.level) })}</h1>
  <aside class="controls" class:open={sheetOpen} bind:this={panelEl} aria-label={t('mv.controls')}>
    {#if !desktop}
      <button type="button" class="handle" aria-expanded={sheetOpen} aria-label={sheetOpen ? t('mv.less') : t('mv.more')}
        onclick={() => (sheetOpen = !sheetOpen)} onpointerdown={(e) => (dragY = e.clientY)}
        onpointerup={(e) => { if (dragY !== null && Math.abs(e.clientY - dragY) > 24) { sheetOpen = e.clientY < dragY; e.preventDefault(); } dragY = null; }}>
        <!-- owner's choice (D29 follow-up): a chevron, since the handle is a button; up = open the sheet, down = close it -->
        <svg class="chev" class:up={!sheetOpen} viewBox="0 0 20 12" width="22" height="13" aria-hidden="true"><path d="M2 2l8 8 8-8" /></svg>
      </button>
      {#if reachOn}
        <!-- U16: reach stays at hand on a phone: Play, hub and mode, time slider -->
        <div class="rbar">
          <button type="button" class="rplay" onclick={play} aria-label={app.playing ? t('rc.pause') : t('rc.play')}>
            {#if app.playing}<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" /><rect x="9.5" y="2" width="3.5" height="12" /></svg>
            {:else}<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 2v12l10-6z" /></svg>{/if}
          </button>
          <button type="button" class="rhub" onclick={openReach} title={t('rc.from')}>
            <span class="rh">{hub.name}</span><span class="rm">{reachMode === 'car' ? t('common.car') : t('common.pt')}</span>
          </button>
          <input type="range" min="0" max={T_MAX} step="1" value={app.t} aria-label={t('rc.minutes')} style="--pct:{(100 * app.t) / T_MAX}%"
            oninput={(e) => { stop(); app.t = +e.currentTarget.value; }} />
          <output class="rt num">{Math.round(app.t)} min</output>
        </div>
      {/if}
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
        <MetricPicker metrics={base.metrics} level={ld.level} value={metaRaw.id} onpick={pickShade} />
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
        {#if regional}<p class="regn">{t('rg.note', { level: levelName(regional, false) })}</p>{/if}
        {#if pooledAlt && !whyA}
          <p class="foot pl"><button type="button" class="link" onclick={() => (app.metric = pooledAlt!.id)}>{t(metaRaw.pooled ? 'fl.annual' : 'fl.pooled', { label: ml(pooledAlt) })}</button></p>
        {/if}
        <div class="legend-wrap">
          {#if spatialMode}
            <SpatialLegend mode={spatialMode} lisa={lisaCls} counts={biRes?.counts ?? null} labelA={ml(metaA)} labelB={metaB ? ml(metaB) : ''}
              compact={!desktop && !sheetOpen} onoff={() => (app.spatial = 'off')} />
          {:else if whyA}
            <p class="why">{whyA}</p>
          {:else if sizeOnly && sizeMeta && sizeData && sizeRef}
            <SizeLegend meta={sizeMeta} period={sizeRef.col.period} vmax={sizeData.vmax} rmax={sizeData.rMax * zf} filled
              nDrawn={sizeData.syms.length} nMissing={sizeData.nMissing} nNonPositive={sizeData.nNonPositive} unitWord={word} />
          {:else if scaleA && colA}
            <Legend meta={metaA} col={native ? null : colA} v={native?.v ?? colA.v} period={colA.period} scale={scaleA} nUnits={native ? native.v.length : nUnits} unitWord={native?.word ?? word} source={base.sources.get(metaA.source)}
              mask={filtered ? (native?.mask ?? match.m) : null} title={legendTitle} warn={legendWarn}
              method={app.cls} onmethod={(m) => (app.cls = m)} compact={!desktop && !sheetOpen} axisRef={fixedRef} notes={legendNotes} rel={relLegend} nHidden={native ? 0 : nHidden} />
          {:else if colA && !scaleA}
            <p class="why">{t('mv.noValues', { p: fmtPeriod(colA.period) })}</p>
          {:else if refA === undefined}
            <p class="foot">{t('status.loading')}</p>
          {/if}
          {#if unstableIdx.length && !whyA && !spatialMode}
            <div class="ur">
              <span class="foot">{t(cmpActive ? 'r3.urChg' : 'fl.n', { n: fmtNumber(unstableIdx.length, 0) })}</span>
              <div class="seg" role="radiogroup" aria-label={t('fl.show')}>
                {#each ['show', 'light', 'hide'] as const as o}
                  <button type="button" role="radio" aria-checked={app.unstable === o} onclick={() => (app.unstable = o)}>{t(`fl.opt.${o}`)}</button>
                {/each}
              </div>
            </div>
          {/if}
          {#if scaleA && colA && !whyA}
            <div class="exrow"><button type="button" class="exb" onclick={mapPNG} disabled={pngBusy} title={t('ex.pngT')}>{pngBusy ? t('ex.pngWait') : t('ex.pngMap')}</button>
              <EmbedDialog title={spatialMode === 'bi' && metaB ? t('sp.legendBi', { a: ml(metaA), b: ml(metaB) }) : ml(metaA)} /></div>
          {/if}
          {#if autoSym && autoSym === metaRaw.id && symbolsMode && !whyA}
            <p class="hintc">{t('sym.auto', { metric: ml(metaRaw) })}
              <button type="button" class="link" onclick={shadeInstead}>{t('sym.back')}</button></p>
          {/if}
          {#if countHint}
            <p class="hintc">{t('mv.countHint', { metric: ml(metaA) })}
              <button type="button" class="link" onclick={countAsSymbols}>{t('mv.countBtn')}</button></p>
          {/if}
        </div>
        {#if yearPeriods.length > 1 && !whyA}
          <div class="yr" class:extra={!app.year}>
            <YearSlider periods={yearPeriods} value={app.year} marks={periodNotes} latest={metaRaw.latest} onchange={(y) => (app.year = y)}>
              {#if refA?.noSeries}{' · '}<span class="warn">{t('mv.noSeries')}</span>
              {:else if refA?.yearMissing}{' · '}<span class="warn">{t('mv.noYearVal', { y: refA.yearMissing })}</span>
              {:else if yearEmpty}{' · '}<span class="warn">{t('mv.noYearLevel', { y: app.year ?? '' })}</span>{/if}
            </YearSlider>
            <YearTools periods={yearPeriods} to={refRaw?.col.period ?? yearPeriods[yearPeriods.length - 1]} from={app.cmpFrom} mode={app.cmpMode} fixed={app.fixed}
              problem={cmpProblem} marks={periodNotes} onfrom={(y) => (app.cmpFrom = y)} onmode={(m) => (app.cmpMode = m)} onfixed={(v) => (app.fixed = v)}
              onmulti={() => (app.multi = defaultPeriods(yearPeriods))} />
          </div>
        {:else if app.year && !whyA}
          <p class="foot yr">{t(li.series ? 'mv.yearNoSeries' : 'mv.yearNoSeriesLevel', { y: app.year })}
            <button type="button" class="link" onclick={() => (app.year = null)}>{t('mv.backLatest')}</button></p>
        {/if}
        <VintageSwitch {base} />
      </section>

      <section class="spsec">
        <SpatialPanel {sp} bind:open={spOpen} metrics={base.metrics} {metaA} {metaB} level={ld.level} unitWord={word} {nUnits} usable={!whyA && !!refA}
          cls={lisaCls} bi={biRes} rho={biRho} biLoading={app.spatial === 'bi' && !!metaB && metaB.id !== metaRaw.id && refB === undefined} onmode={setSpatial} />
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
          onpick={(id) => { autoSym = null; app.size = id || null; }} />
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

      <section class="reach" id="reach-sec">
        <ReachControls {hubs} hub={hub.slug} mode={app.reach} t={app.t} playing={app.playing} {carAvailable} {station} ptm={app.ptm}
          onptm={(m) => (app.ptm = m)}
          only={app.ronly} ononly={ld.level === 'gemeinde' ? (v) => (app.ronly = v) : undefined}
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
          defaultHub={hub.slug} onset={(fs) => (app.filters = fs)} onzoom={match.n > 0 ? () => zoomTo(matchIdx) : undefined}>
          {#snippet extra()}
            <AggregateLine metrics={base.metrics} {metas} level={ld.level} {nUnits} mask={match.m} nMatch={match.n}
              metricId={app.agg ?? app.metric} getCol={(id) => cols.get(ld, id, app.year)} unitWord={word}
              onpick={(id) => (app.agg = id === app.metric ? null : id)} hiddenIdx={cmpActive ? [] : unstableIdx} shadeId={metaRaw.id} />
          {/snippet}
        </FilterPanel>
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
      {#if app.multi !== null}
        <SmallMultiples {base} {ld} {cols} meta={metaRaw} periods={yearPeriods} picked={app.multi} pooled={smPooled} method={app.cls}
          mask={filtered ? (match.m as Uint8Array) : null} onpick={(p) => (app.multi = p)} onclose={() => (app.multi = null)} change={cmpActive} />
      {/if}
      {#if !app.embed}
      {#if desktop && !app.embed && !sideOpen}
        <div class="sideopen seg" role="group" aria-label={t('mv.side')}>
          <button type="button" onclick={() => (app.tab = 'rank')}>{t('tab.rank')}</button>
          <button type="button" onclick={() => (app.tab = 'stats')}>{t('tab.stats')}</button>
        </div>
      {/if}
      <div class="lvlbar">
        <LevelSwitch value={ld.level} avail={levelsOf(metaA)} naTitle={(l) => t('level.na', { metric: ml(metaA), level: levelWord(l) })} onchange={(l) => { stop(); requestLevel(base, l); }} />
        <LevelNote {base} />
      </div>
      {/if}
      {#if (!desktop || app.embed) && card && refA && colA}
        <div class="card-wrap">
          <Card name={names[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
            source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} extra={card.extra} notes={card.notes} compact onclose={() => (app.sel = null)}
            profile={profileHref(refOf(ld.level, ld.units[card.i]))} profileLabel={t('card.profile')} sourceLink={sourceHref(metaA.source)} {regional}
            ci={card.ci} relText={card.relText} />
        </div>
      {/if}
      {#if choose}
        <div class="choose" role="dialog" aria-label={t('ux.nearest')} style="left:{Math.max(8, Math.min(choose.x - 110, choose.w - 228))}px; top:{choose.y + 12}px">
          <p>{t('ux.nearest')}</p>
          {#each choose.ids as k}<button type="button" onclick={() => select(k)}>{names[k]}{#if ld.canton[k] && ld.level !== 'kanton'}<span class="kt">{ld.canton[k]}</span>{/if}</button>{/each}
          <button type="button" class="cx" aria-label={t('common.close')} onclick={() => (choose = null)}>×</button>
        </div>
      {/if}
      {#if filtered && match.n === 0 && mapReady}
        <div class="zero" role="status">
          <p>{t('ux.zero')}</p>
          <button type="button" class="btn-primary" onclick={() => { app.filters = []; app.ronly = false; }}>{t('ux.clear')}</button>
        </div>
      {/if}
      {#if toast}
        <div class="toast" role="status">
          <span>{toast}</span>
          {#if autoSym}<button type="button" class="link" onclick={shadeInstead}>{t('ux.symKeep')}</button>{/if}
          <button type="button" class="tx" aria-label={t('common.dismiss')} onclick={() => (toast = null)}>×</button>
        </div>
      {/if}
      {#if (full || app.embed || (!desktop && !sheetOpen && !card)) && scaleA && colA && !whyA}
        <div class="flegend">
          {#if spatialMode}
            <div class="fl-t">{spatialMode === 'bi' && metaB ? t('sp.legendBi', { a: ml(metaA), b: ml(metaB) }) : t('sp.legendTitle', { metric: ml(metaA) })}</div>
            <SpatialLegend mode={spatialMode} lisa={lisaCls} counts={biRes?.counts ?? null} labelA={ml(metaA)} labelB={metaB ? ml(metaB) : ''} compact />
          {:else}
            <div class="fl-t">{ml(metaA)}</div>
            <Legend meta={metaA} col={native ? null : colA} v={native?.v ?? colA.v} period={colA.period} scale={scaleA} nUnits={native ? native.v.length : nUnits} unitWord={native?.word ?? word} source={base.sources.get(metaA.source)}
              mask={filtered ? (native?.mask ?? match.m) : null} title={legendTitle}
              method={app.cls} onmethod={(m) => (app.cls = m)} compact mini={app.embed || (!desktop && !full)} nHidden={native ? 0 : nHidden} />
          {/if}
        </div>
      {/if}
      {#if tip && hover !== null && hoverAt && (desktop || app.embed)}
        <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
          <strong>{names[hover]}</strong>{#if ld.canton[hover] && ld.level !== 'kanton' && !names[hover].includes('(')}&nbsp;<span class="muted">{ld.canton[hover]}</span>{/if}
          {#each tip as r}<div class="num">{r}</div>{/each}
        </div>
      {/if}
    </div>
    {#if app.embed}
      <div class="embed-foot">
        <span class="credit">{embedCredit}</span>
        <a class="open" href={fullHref} target="_blank" rel="noopener">{t('em.open')} ↗</a>
      </div>
    {/if}
  </section>

  {#if sideOpen}
    <aside class="side" aria-label={t('tab.stats')}>
      {#if !card}
        <button type="button" class="sclose" aria-label={t('common.close')} title={t('common.close')} onclick={closeSide}>
          <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.5" /></svg>
        </button>
      {/if}
      {#if card && refA && colA}
        <div class="caps lab">{t('mv.selected', { one })}</div>
        <Card name={names[card.i]} canton={ld.canton[card.i]} sub={card.sub} meta={metaA} file={refA.file} col={colA} index={card.i}
          source={base.sources.get(metaA.source)} reach={card.reach} unitWord={word} extra={card.extra} notes={card.notes} docked onclose={() => (app.sel = null)}
          profile={profileHref(refOf(ld.level, ld.units[card.i]))} profileLabel={t('card.profile')} sourceLink={sourceHref(metaA.source)} {regional}
          ci={card.ci} relText={card.relText} />
      {:else}
        <p class="foot hint">{t('mv.hint')}</p>
      {/if}
      <div class="tabs side-tabs" role="tablist" aria-label={t('mv.side')}>
        <button type="button" role="tab" aria-selected={deskTab === 'rank'} onclick={() => (app.tab = 'rank')}>{t('tab.rank')}</button>
        <button type="button" role="tab" aria-selected={deskTab === 'stats'} onclick={() => (app.tab = 'stats')}>{t('tab.stats')}</button>
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
    border: 1px solid var(--ink); padding: 6px 9px; font-size: var(--fs-small); white-space: nowrap;
  }
  .muted { color: var(--muted); }
  .choose {
    position: absolute; z-index: 8; width: 220px; background: var(--panel); border: var(--rule-edge); border-top: var(--rule-heavy); padding: 0 0 var(--sp-1);
  }
  .choose p { margin: 0; padding: var(--sp-2) 44px var(--sp-1) var(--sp-3); font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text-2); }
  .choose button:not(.cx) {
    display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: 44px; padding: 0 var(--sp-3); border: 0; border-top: var(--rule-row);
    background: none; text-align: left; font-size: var(--fs-body); font-weight: 600; cursor: pointer; color: var(--text);
  }
  .choose .kt { font-weight: 400; color: var(--text-2); font-size: var(--fs-meta); }
  .choose .cx { position: absolute; top: 0; right: 0; width: 40px; height: 40px; border: 0; background: none; font-size: var(--fs-lead); cursor: pointer; color: var(--text); }
  .zero {
    position: absolute; z-index: 6; left: 50%; top: 40%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: var(--sp-3);
    padding: var(--sp-4) var(--sp-6); background: var(--panel); border: var(--rule-edge); border-top: var(--rule-heavy); max-width: calc(100% - 32px); text-align: center;
  }
  .zero p { margin: 0; font-size: var(--fs-lead); line-height: var(--lh-lead); font-weight: 600; }
  .toast {
    position: absolute; z-index: 7; left: 50%; bottom: var(--sp-6); transform: translateX(-50%); width: max-content; max-width: min(460px, calc(100% - 24px));
    display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-2) var(--sp-1) var(--sp-2) var(--sp-3); background: var(--ink); color: var(--ink-text);
    font-size: var(--fs-small); line-height: var(--lh-small);
  }
  .toast .link { color: var(--ink-text); font-weight: 600; white-space: nowrap; }
  .toast .tx { flex: none; width: var(--ctl-h); height: var(--ctl-h); border: 0; background: none; color: var(--ink-text); cursor: pointer; font-size: var(--fs-lead); }
  .rhead { margin: 0 0 var(--sp-2); font-size: var(--fs-small); line-height: var(--lh-small); padding-left: var(--sp-2); border-left: 3px solid var(--ink); }
  .rhead .link { margin-left: var(--sp-1); }
  .lab { margin-bottom: 6px; }
  .why { margin: 0; font-size: var(--fs-small); }
  .yr { margin-top: 10px; }
  .warn { color: var(--text); }
  .link { border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: inherit; color: var(--text); }
  .row2 { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
  .row2 > .caps { flex: none; white-space: nowrap; }
  .row2 .seg button { padding: 3px 8px; font-size: var(--fs-meta); }
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
  .side { position: relative; min-width: 0; background: var(--panel); border-left: var(--rule-edge); padding: var(--sp-4) var(--gutter); overflow-y: auto; overflow-x: hidden; }
  .sclose { position: absolute; top: var(--sp-1); right: var(--sp-1); width: var(--ctl-h); height: var(--ctl-h); display: grid; place-items: center; border: 0; background: none; cursor: pointer; color: var(--text); z-index: 2; }
  .side > .lab, .side > .hint { padding-right: 36px; }
  .sideopen.seg { position: absolute; z-index: 3; top: 10px; right: 56px; }
  .sblock { margin-top: 10px; }
  .tabs { display: flex; border-bottom: 1px solid var(--ink); }
  .tabs button {
    flex: 1; padding: 6px 4px; border: 0; background: none; cursor: pointer; font-size: var(--fs-meta); font-weight: 600; color: var(--muted);
    border-bottom: 3px solid transparent; margin-bottom: -1px;
  }
  .tabs button[aria-selected='true'] { color: var(--text); border-bottom-color: var(--ink); }
  .side-tabs { margin-top: 18px; border-top: 1px solid var(--rule); }
  .badge { display: inline-grid; place-items: center; min-width: 16px; height: 16px; padding: 0 3px; background: var(--ink); color: var(--ink-text); font-size: var(--fs-cap); }
  .hint { margin: 0; }
  .card-wrap { position: absolute; z-index: 6; top: 8px; left: 8px; right: 8px; max-width: 440px; margin: 0 auto; }
  .exrow { margin: 6px 0 0; display: flex; gap: 6px; flex-wrap: wrap; }
  .vd { margin-top: 6px; }
  .regn { margin: 6px 0 0; font-size: var(--fs-meta); border-left: 3px solid var(--ink); padding-left: 6px; }
  .ur { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 4px 8px; margin-top: 6px; }
  .ur .seg button { padding: 2px 7px; font-size: var(--fs-meta); }
  .pl { margin: 4px 0 0; }
  .vd button { padding: 3px 8px; font-size: var(--fs-meta); }
  .exb { border: 1px solid var(--ink); background: var(--panel); padding: 3px 9px; cursor: pointer; font-size: var(--fs-meta); font-weight: 600; color: var(--text); }
  .exb:disabled { opacity: 0.5; cursor: progress; }
  .hintc { margin: 6px 0 0; font-size: var(--fs-meta); border-left: 3px solid var(--ink); padding-left: 6px; }
  .flegend {
    position: absolute; z-index: 4; left: 10px; bottom: 26px; width: min(340px, calc(100% - 20px)); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 8px;
  }
  .fl-t { font-weight: 700; font-size: var(--fs-small); margin-bottom: 2px; }
  .stage:focus { outline: none; }
  .spsec { padding: 10px 0; }
  .embed-foot {
    flex: none; display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 5px 10px; background: var(--panel);
    border-top: 1px solid var(--rule); font-size: var(--fs-cap); color: var(--faint); min-height: 26px;
  }
  .embed-foot .credit { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .embed-foot .open { flex: none; color: var(--text); font-weight: 700; font-size: var(--fs-meta); text-decoration: underline; text-underline-offset: 3px; padding: 4px 0; }
  /* D16: the embed legend sits top-left, clear of Genève */
  .stage.embed .flegend { top: 10px; bottom: auto; width: min(260px, calc(100% - 20px)); }
  /* full-screen map: header and panels hidden, the map fills the viewport */
  :global(html.mapfull .app > header.top) { display: none; }
  .stage.full { display: block; }
  .stage.full .controls, .stage.full .side { display: none; }
  .stage.full .pane { position: absolute; inset: 0; }
  .lvlbar { position: absolute; z-index: 3; top: 10px; left: 10px; right: 56px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px; pointer-events: none; }
  .lvlbar > :global(*) { pointer-events: auto; }

  @media (min-width: 900px) {
    .stage { display: grid; grid-template-columns: 320px minmax(0, 1fr); }
    .stage.sideopen { grid-template-columns: 320px minmax(0, 1fr) 300px; }
    .stage.siderank { grid-template-columns: 320px minmax(0, 1fr) 360px; }
    .controls { border-right: 1px solid var(--rule); min-height: 0; }
    .body { padding-top: 4px; }
  }

  @media (max-width: 899px) {
    /* phone (D7, U16): map on top, the sheet below it. Folded, the sheet is the grab handle and the tab row
       (plus the reach bar while reach is on), so the map keeps most of the screen; opening it shrinks the map. */
    .stage { display: flex; flex-direction: column; }
    .pane { order: 0; flex: 1 1 auto; min-height: 30%; }
    .controls { order: 1; flex: none; border-top: var(--rule-heavy); max-height: 64%; padding-bottom: env(safe-area-inset-bottom); }
    .controls:not(.open) .body { display: none; }
    .controls .body { min-height: 0; }
    .sheet-tabs { flex: none; padding: 0 var(--sp-3); }
    .sheet-tabs button { min-height: 44px; padding: 0 2px; }
    .handle { display: grid; place-items: center; width: 100%; height: 40px; padding: 0; border: 0; background: none; cursor: pointer; flex: none; touch-action: none; }
    .handle .chev { display: block; fill: none; stroke: var(--ink); stroke-width: 2.4; stroke-linecap: square; transition: transform 0.15s; }
    .handle .chev.up { transform: rotate(180deg); }
    @media (prefers-reduced-motion: reduce) { .handle .chev { transition: none; } }
    .rbar { flex: none; display: flex; align-items: center; gap: var(--sp-2); padding: 0 var(--sp-3) var(--sp-2); }
    .rplay { flex: none; width: 40px; height: 40px; display: grid; place-items: center; border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text); cursor: pointer; }
    .rplay svg { fill: currentColor; }
    .rhub {
      flex: 0 1 auto; min-width: 0; max-width: 40%; height: 40px; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; padding: 0 var(--sp-2);
      border: 1px solid var(--ink); background: var(--panel); color: var(--text); cursor: pointer; text-align: left;
    }
    .rh { max-width: 100%; font-size: var(--fs-small); line-height: 16px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .rm { font-size: var(--fs-cap); line-height: var(--lh-cap); color: var(--text-2); }
    .rbar input { flex: 1; min-width: 60px; }
    .rt { flex: none; min-width: 3.6em; text-align: right; font-size: var(--fs-body); font-weight: 600; }
    .body section { padding: var(--sp-3) 0; }
    .legend-wrap { margin-top: var(--sp-2); }
    /* the Map tab on a phone: shade, then reach (so it is reached without scrolling past everything), size, patterns */
    .body { display: flex; flex-direction: column; }
    .body > section.reach { order: 1; }
    .body > section.extra { order: 2; }
    .body > section.spsec { order: 3; }
    /* zoom buttons hidden on phones (pinch); the reset button stays */
    :global(.single .maplibregl-ctrl-top-right .maplibregl-ctrl-group:not(.gb-btn)) { display: none; }
    .lvlbar { top: var(--sp-2); left: var(--sp-2); }
    /* phone: the card is a short strip at the bottom of the map (expands on tap, up to the level bar) */
    .card-wrap { top: auto; bottom: 8px; right: 52px; max-height: calc(100% - 56px); display: flex; flex-direction: column; justify-content: flex-end; }
    .flegend { left: var(--sp-2); bottom: var(--sp-2); width: min(300px, calc(100% - 64px)); }
  }
</style>
