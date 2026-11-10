<script lang="ts">
  import { colon } from '../lib/typo';
  import '../lib/i18n-r3';
  // Regression panel (D34, option B): OLS in the browser on the units of the current level.
  // Outcome and 1–6 explanatory variables (optional log10), language-region or canton controls,
  // population weights, flagged values left out on request, the active filters as the sample.
  // Coefficient table with canton-clustered (CR1), robust (HC1) or conventional standard errors,
  // a residual map and a residual-vs-predicted plot, CSV and PNG exports. State in the hash (regmodel.ts).
  import { onMount, tick, untrack } from 'svelte';
  import LevelSwitch from '../components/LevelSwitch.svelte';
  import MetricPicker from '../components/MetricPicker.svelte';
  import ResidPlot from '../components/ResidPlot.svelte';
  import Term from '../components/Term.svelte';
  import { fmtNumber, fmtPeriod, fmtSig, unitOf } from '../lib/classify';
  import type { ColumnStore, ColView } from '../lib/columns.svelte';
  import {
    flagsOf, hasFlag, isUnstable, loadReachIndex, loadSeries, loadUnits, namesOf, regionalAt, unavailableReason,
    type Base, type Hub, type LevelData, type MetricMeta, type SeriesFile, type UnitRow,
  } from '../lib/data';
  import { bareAttribution, downloadCSV, downloadBlob, figurePNG, grabMap, slug, type Cell, type LegendItem } from '../lib/export';
  import { catOptions, combine, describeFilter, evalFilter } from '../lib/filters';
  import { levelName, levelWord, ml, t } from '../lib/i18n.svelte';
  import { CH_BOUNDS, UnitMap } from '../lib/mapview';
  import { hrefFor, profileHref } from '../lib/nav';
  import { refOf } from '../lib/places';
  import { ols, OlsError, type OlsResult, type SeType } from '../lib/regress';
  import {
    MAX_X, REG_PRESETS, effectOf, lastParams, nearestPeriod, parseSpec, rememberParams, specParams, stepFor, yearOf,
    type Control, type RegSpec, type RegVar,
  } from '../lib/regmodel';
  import { app } from '../lib/state.svelte';
  import { divRamp } from '../lib/theme';

  interface Props {
    base: Base;
    ld: LevelData;
    cols: ColumnStore;
    desktop: boolean;
    onrendered?: () => void;
  }
  let { base, ld, cols, desktop, onrendered }: Props = $props();

  const metas = $derived(base.metas);
  const names = $derived(namesOf(ld));
  const word = $derived(levelWord(ld.level));
  const N = $derived(ld.units.length);
  const REGION_NAMES = () => ['1', '2', '3', '4'].map((k) => t(`cv.r${k}`));

  // ------------------------------------------------------------------ model state (hash)
  const presets = $derived(REG_PRESETS.filter((p) => [p.spec.y, ...p.spec.xs].every((v) => metas.has(v.id))));
  const fallbackParams = () => lastParams ?? (presets[0] ? specParams(presets[0].spec) : { ry: 'pop_total' });
  // a link or the menu without a model: the last model of this session, else the first example
  $effect(() => {
    if (app.route === 'regress' && !parseSpec(app.params)) untrack(() => (app.params = { ...fallbackParams() }));
  });
  const spec = $derived<RegSpec>(parseSpec(app.params) ?? parseSpec(fallbackParams())!);
  $effect(() => {
    rememberParams(specParams(spec));
  });
  const activePreset = $derived(presets.find((p) => JSON.stringify(specParams(p.spec)) === JSON.stringify(specParams(spec)))?.slug ?? null);
  function update(patch: Partial<RegSpec>) {
    app.params = specParams({ ...spec, ...patch });
  }
  function applyPreset(slugName: string) {
    const p = presets.find((x) => x.slug === slugName);
    if (p) {
      app.params = specParams(p.spec);
      app.sel = null;
    }
  }
  const setX = (k: number, v: Partial<RegVar>) => update({ xs: spec.xs.map((x, j) => (j === k ? { ...x, ...v } : x)) });
  const removeX = (k: number) => update({ xs: spec.xs.filter((_, j) => j !== k) });
  function addX() {
    if (spec.xs.length >= MAX_X) return;
    const used = new Set([spec.y.id, ...spec.xs.map((x) => x.id)]);
    const cand = ['pop_total', 'share_foreign', 'share_age_65plus', 'tax_np_mean_taxable_income', 'geo_pop_density'].find((id) => !used.has(id) && metas.has(id));
    update({ xs: [...spec.xs, { id: cand ?? 'pop_total', log: cand === 'pop_total' }] });
  }

  // ------------------------------------------------------------------ data
  const yRef = $derived(cols.get(ld, spec.y.id, null));
  const xRefs = $derived(spec.xs.map((v) => cols.get(ld, v.id, null)));
  let unitRows = $state.raw<UnitRow[] | null>(null);
  let hubs = $state.raw<Hub[]>([]);
  let popSeries = $state.raw<SeriesFile | null | undefined>(undefined);
  $effect(() => {
    if (!unitRows && (ld.level === 'gemeinde' || app.filters.length)) loadUnits().then((u) => (unitRows = u)).catch(() => {});
    if (app.filters.some((f) => f.kind === 'reach') && !hubs.length) loadReachIndex().then((ix) => ix && (hubs = ix.hubs)).catch(() => {});
  });
  const SERIES_LEVELS = ['gemeinde', 'bezirk', 'kanton'];
  $effect(() => {
    if (spec.weights && SERIES_LEVELS.includes(ld.level) && popSeries === undefined)
      loadSeries('pop_total').then((s) => (popSeries = s)).catch(() => (popSeries = null));
  });
  const popLatest = $derived(spec.weights ? cols.get(ld, 'pop_total', null) : null);
  /** language region per unit (municipalities only): index 0..3, -1 unknown */
  const regions = $derived.by(() => {
    if (ld.level !== 'gemeinde' || !unitRows) return null;
    const idx = new Int8Array(N).fill(-1);
    for (const r of unitRows) {
      if (r.level !== 'gemeinde' || !r.sprachgebiet) continue;
      const i = ld.index.get(r.id);
      if (i !== undefined) idx[i] = Number(r.sprachgebiet) - 1;
    }
    return idx;
  });

  // filters (as in the other views)
  const hubName = (s: string) => hubs.find((h) => h.slug === s)?.name ?? s;
  const evals = $derived(app.filters.map((f) => evalFilter(f, { ld, rows: unitRows, metas, hubName, col: (id) => cols.get(ld, id, app.year) })));
  const match = $derived(combine(evals, N));
  const filtered = $derived(match.active > 0);
  const filterText = $derived(evals.map((e) => describeFilter(e, (field, id) => catOptions(field, unitRows).find((o) => o.id === id)?.name ?? id)).join(' · '));

  // ------------------------------------------------------------------ variables
  interface VarInfo {
    v: RegVar;
    meta: MetricMeta;
    ref: ColView;
    /** log10 is used */
    log: boolean;
    /** log asked for but not possible */
    logNo: string | null;
    /** values ≤ 0 left out for the log */
    nonPos: number;
    label: string;
  }
  function varInfo(v: RegVar, ref: ColView): VarInfo {
    const meta = ref.meta;
    let n = 0;
    let nonPos = 0;
    for (const x of ref.col.v) {
      if (x === null || !Number.isFinite(x)) continue;
      n++;
      if (x <= 0) nonPos++;
    }
    const logOk = n > 0 && nonPos < n && nonPos / n <= 0.1;
    const log = v.log && logOk;
    return {
      v, meta, ref, log, nonPos: log ? nonPos : 0,
      logNo: v.log && !logOk ? t('rg.logNo', { n: fmtNumber(nonPos, 0), m: fmtNumber(n, 0) }) : null,
      label: `${log ? 'log₁₀ ' : ''}${ml(meta)}`,
    };
  }
  /** per variable: info, or a reason it cannot be used (unavailable at this level), or undefined (loading) */
  const yInfo = $derived(yRef ? varInfo(spec.y, yRef) : yRef);
  const xInfos = $derived(spec.xs.map((v, k) => (xRefs[k] ? varInfo(v, xRefs[k]!) : xRefs[k])));
  const whyVar = (v: RegVar) => {
    const m = metas.get(v.id);
    return m ? unavailableReason(m, ld.level) ?? t('rg.err.unavail', { v: ml(m), units: word }) : t('f.notInBuild');
  };

  // controls and standard errors that the level allows
  const langOk = $derived(ld.level === 'gemeinde');
  const ktOk = $derived(ld.level === 'gemeinde' || ld.level === 'bezirk');
  const ctrl = $derived<Control>(spec.ctrl === 'lang' && !langOk ? 'none' : spec.ctrl === 'kt' && !ktOk ? 'none' : spec.ctrl);
  const seUsed = $derived<SeType>(spec.se === 'cluster' && !ktOk ? 'hc1' : spec.se);

  // population weights: the pop_total period nearest to the outcome's period
  const weights = $derived.by(() => {
    if (!spec.weights || !yRef) return null;
    const target = yearOf(yRef.col.period);
    const rows = popSeries?.levels[ld.level];
    if (popSeries && rows && target !== null) {
      const p = nearestPeriod(popSeries.periods, target);
      const k = p ? popSeries.periods.indexOf(p) : -1;
      if (k >= 0) return { v: ld.units.map((u) => rows[u]?.[k] ?? null), period: p! };
    }
    if (SERIES_LEVELS.includes(ld.level) && popSeries === undefined) return undefined;
    if (popLatest === undefined) return undefined;
    return popLatest ? { v: popLatest.col.v, period: popLatest.col.period } : null;
  });

  // ------------------------------------------------------------------ model
  interface TermInfo {
    kind: 'const' | 'x' | 'lang' | 'kt';
    key: string;
    label: string;
    x?: number;
  }
  type Model =
    | { status: 'loading' }
    | { status: 'error'; msg: string }
    | {
        status: 'ok';
        res: OlsResult;
        terms: TermInfo[];
        rows: number[];
        y: Float64Array;
        n: number;
        dropped: [string, number][];
        clusters: number | null;
        feRef: string | null;
        feK: number;
        flaggedSmall: number;
        within: number | null;
        flaggedMaj: number;
        xsd: number[];
        collinear: string[];
      };
  const model = $derived.by<Model>(() => {
    if (yInfo === undefined || xInfos.some((x) => x === undefined)) return { status: 'loading' };
    if (yInfo === null) return { status: 'error', msg: whyVar(spec.y) };
    const bad = spec.xs.findIndex((_, k) => xInfos[k] === null);
    if (bad >= 0) return { status: 'error', msg: whyVar(spec.xs[bad]) };
    if (!spec.xs.length) return { status: 'error', msg: t('rg.err.noX') };
    if (spec.xs.some((x) => x.id === spec.y.id)) return { status: 'error', msg: t('rg.err.same') };
    if (new Set(spec.xs.map((x) => x.id)).size < spec.xs.length) return { status: 'error', msg: t('rg.err.dup') };
    if (ctrl === 'lang' && !regions) return { status: 'loading' };
    if (spec.filtered && app.filters.length && evals.some((e) => e.status === 'loading')) return { status: 'loading' };
    if (spec.weights && weights === undefined) return { status: 'loading' };
    const xi = xInfos as VarInfo[];
    const vars = [yInfo, ...xi];
    const fileOf = (vi: VarInfo) => vi.ref.file;
    const dropOf = (vi: VarInfo, i: number) => {
      const f = flagsOf(fileOf(vi), vi.ref.col, i);
      return f !== 0 && (isUnstable(fileOf(vi), f) || hasFlag(fileOf(vi), f, 'majority_election'));
    };

    // sample, with the first reason each unit is left out
    const reasons = new Map<string, number>();
    const why = (k: string) => reasons.set(k, (reasons.get(k) ?? 0) + 1);
    const rows: number[] = [];
    let flaggedSmall = 0;
    let flaggedMaj = 0;
    const useFilter = spec.filtered && filtered;
    unit: for (let i = 0; i < N; i++) {
      if (useFilter && !match.m[i]) { why(t('rg.d.filter')); continue; }
      for (const vi of vars) {
        const x = vi.ref.col.v[i];
        if (x === null || x === undefined || !Number.isFinite(x)) {
          why(t(vi.ref.col.m?.[String(i)] !== undefined ? 'rg.d.maj' : 'rg.d.miss', { v: ml(vi.meta) }));
          continue unit;
        }
        if (spec.drop && dropOf(vi, i)) { why(t('rg.d.flag', { v: ml(vi.meta) })); continue unit; }
        if (vi.log && x <= 0) { why(t('rg.d.log', { v: ml(vi.meta) })); continue unit; }
      }
      if (ctrl === 'lang' && regions![i] < 0) { why(t('rg.d.lang')); continue; }
      if ((ctrl === 'kt' || seUsed === 'cluster') && !ld.canton[i]) { why(t('rg.d.kt')); continue; }
      if (weights && !((weights.v[i] ?? 0) > 0)) { why(t('rg.d.w')); continue; }
      for (const vi of vars) {
        const f = flagsOf(fileOf(vi), vi.ref.col, i);
        if (!f) continue;
        if (isUnstable(fileOf(vi), f)) flaggedSmall++;
        if (hasFlag(fileOf(vi), f, 'majority_election')) flaggedMaj++;
      }
      rows.push(i);
    }
    const n = rows.length;
    const tr = (vi: VarInfo, i: number) => (vi.log ? Math.log10(vi.ref.col.v[i]!) : vi.ref.col.v[i]!);
    const y = Float64Array.from(rows, (i) => tr(yInfo, i));
    const X: Float64Array[] = [new Float64Array(n).fill(1)];
    const terms: TermInfo[] = [{ kind: 'const', key: '(intercept)', label: t('rg.const') }];
    const xsd: number[] = [];
    xi.forEach((vi, k) => {
      X.push(Float64Array.from(rows, (i) => tr(vi, i)));
      terms.push({ kind: 'x', key: vi.log ? `log10(${vi.meta.id})` : vi.meta.id, label: vi.label, x: k });
      // raw standard deviation of x in the sample (for "per +step" effects)
      const raw = rows.map((i) => vi.ref.col.v[i]!);
      const m = raw.reduce((a, b) => a + b, 0) / Math.max(1, n);
      xsd.push(Math.sqrt(raw.reduce((a, b) => a + (b - m) ** 2, 0) / Math.max(1, n - 1)));
    });
    const mostFrequent = (vals: string[]) => {
      const c = new Map<string, number>();
      for (const v of vals) c.set(v, (c.get(v) ?? 0) + 1);
      return [...c.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]?.[0] ?? null;
    };
    let feRef: string | null = null;
    let feK = 0;
    if (ctrl === 'lang') {
      const codes = rows.map((i) => String(regions![i]));
      const present = [...new Set(codes)].sort();
      const ref = present.includes('0') ? '0' : mostFrequent(codes)!;
      const rn = REGION_NAMES();
      for (const c of present) {
        if (c === ref) continue;
        X.push(Float64Array.from(codes, (v) => (v === c ? 1 : 0)));
        terms.push({ kind: 'lang', key: `language_region:${Number(c) + 1}`, label: t('rg.vs', { a: rn[Number(c)], b: rn[Number(ref)] }) });
      }
      feRef = rn[Number(ref)] ?? null;
    } else if (ctrl === 'kt') {
      const kts = rows.map((i) => ld.canton[i]);
      const present = [...new Set(kts)].sort();
      const ref = mostFrequent(kts)!;
      for (const c of present) {
        if (c === ref) continue;
        X.push(Float64Array.from(kts, (v) => (v === c ? 1 : 0)));
        terms.push({ kind: 'kt', key: `canton:${c}`, label: c });
        feK++;
      }
      feRef = ref;
    }
    if (n < X.length + 1) return { status: 'error', msg: t('rg.err.few', { n: fmtNumber(n, 0), k: X.length }) };
    let clusterIds: Int32Array | null = null;
    if (seUsed === 'cluster') {
      const ids = new Map<string, number>();
      clusterIds = Int32Array.from(rows, (i) => {
        const c = ld.canton[i];
        if (!ids.has(c)) ids.set(c, ids.size);
        return ids.get(c)!;
      });
    }
    let res: OlsResult;
    try {
      res = ols({ y, X, w: weights ? Float64Array.from(rows, (i) => weights.v[i]!) : null, cluster: clusterIds, se: seUsed });
    } catch (e) {
      const code = e instanceof OlsError ? e.code : '';
      return { status: 'error', msg: code === 'clusters' ? t('rg.err.clusters') : code === 'dof' ? t('rg.err.few', { n: fmtNumber(n, 0), k: X.length }) : String(e) };
    }
    const collinear = terms.filter((tm, j) => res.collinear[j] && tm.kind !== 'kt').map((tm) => tm.label);
    // B7 (X1): with fixed effects, the within R²: the share of the differences inside cantons (or language regions)
    // that the variables explain, 1 − SSR / Σ w (y − mean of its group)²
    let within: number | null = null;
    if (ctrl === 'kt' || ctrl === 'lang') {
      const g = rows.map((i) => (ctrl === 'kt' ? ld.canton[i] : String(regions![i])));
      const wt = (r: number) => (weights ? weights.v[rows[r]]! : 1);
      const sum = new Map<string, [number, number]>();
      g.forEach((c, r) => {
        const a = sum.get(c) ?? [0, 0];
        a[0] += wt(r) * y[r];
        a[1] += wt(r);
        sum.set(c, a);
      });
      let sstW = 0, ssr = 0;
      g.forEach((c, r) => {
        const [sy, sw] = sum.get(c)!;
        sstW += wt(r) * (y[r] - sy / sw) ** 2;
        ssr += wt(r) * res.resid[r] ** 2;
      });
      within = sstW > 0 ? 1 - ssr / sstW : null;
    }
    return {
      status: 'ok', res, terms, rows, y, n, within, dropped: [...reasons.entries()].sort((a, b) => b[1] - a[1]), clusters: res.clusters, feRef, feK, flaggedSmall, flaggedMaj, xsd, collinear,
    };
  });
  const ok = $derived(model.status === 'ok' ? model : null);

  // ------------------------------------------------------------------ formatting
  function fmtCoef(x: number): string {
    if (!Number.isFinite(x)) return '–';
    const a = Math.abs(x);
    if (a === 0 || a >= 0.01) return fmtSig(x, 3);
    const e = Math.floor(Math.log10(a));
    return `${fmtNumber(x / 10 ** e, 2)}e${e < 0 ? '−' : ''}${Math.abs(e)}`;
  }
  const fmtP = (p: number) => (!Number.isFinite(p) ? '–' : p < 0.001 ? '< 0.001' : fmtNumber(p, 3));
  const signed = (v: number, sig = 2) => (v > 0 ? '+' : '') + fmtSig(v, sig);
  /** outcome unit for effects: pp for shares in %, % for a log outcome, else the unit */
  const yUnitWord = (vi: VarInfo) => (vi.log ? '%' : vi.meta.unit.startsWith('%') ? t('sc.pp') : unitOf(vi.meta));
  const xUnitWord = (m: MetricMeta) => (m.unit.startsWith('%') ? t('sc.pp') : unitOf(m));
  const words = $derived.by(() => {
    if (!ok || !yInfo) return [];
    const yi = yInfo;
    return (xInfos as VarInfo[]).map((vi, k) => {
      const j = k + 1;
      const b = ok.res.coef[j];
      if (!Number.isFinite(b)) return null;
      const step = stepFor(ok.xsd[k], vi.meta.unit.startsWith('%'));
      const e = effectOf(b, vi.log, yi.log, step);
      const lo = effectOf(ok.res.lo[j], vi.log, yi.log, step).value;
      const hi = effectOf(ok.res.hi[j], vi.log, yi.log, step).value;
      const yu = yUnitWord(yi);
      const yTxt = (v: number) => `${signed(v)}${yu === '%' ? ' %' : ` ${yu}`}`;
      const xTxt = vi.log ? `+10 % ${ml(vi.meta)}` : `+${fmtNumber(step, Math.max(0, -Math.floor(Math.log10(step))))} ${xUnitWord(vi.meta)} ${ml(vi.meta)}`.replace(/\s+/g, ' ');
      return { x: xTxt, y: `${yTxt(e.value)} ${ml(yi.meta)}`, ci: t('rg.ci95', { a: yTxt(lo), b: yTxt(hi) }) };
    });
  });
  const seLabel = (s: SeType) => t(`rg.se.${s}`);
  const ctrlText = $derived(ctrl === 'lang' ? t('rg.c.lang') : ctrl === 'kt' ? t('rg.c.kt') : '');
  const formula = $derived(
    yInfo && xInfos.every((x) => x)
      ? `${yInfo.label} ~ ${(xInfos as VarInfo[]).map((x) => x.label).join(' + ')}${ctrlText ? ` + ${ctrlText}` : ''}`
      : '',
  );
  const periodsText = $derived.by(() => {
    if (!yInfo || !xInfos.every((x) => x)) return null;
    const ps = [...new Set([yInfo, ...(xInfos as VarInfo[])].map((v) => fmtPeriod(v.ref.col.period)))];
    return ps.length > 1 ? ps.join(', ') : null;
  });
  const regionalVars = $derived(
    [yInfo, ...xInfos].filter((v): v is VarInfo => !!v && !!regionalAt(v.meta, ld.level)).map((v) => ({ label: ml(v.meta), level: levelName(regionalAt(v.meta, ld.level)!, false) })),
  );
  const partyVar = $derived([yInfo, ...xInfos].some((v) => !!v && !!v.meta.majority_cantons));
  const sourceOf = (m: MetricMeta) => base.sources.get(m.source)?.publisher.split(' (')[0] ?? m.source;

  // ------------------------------------------------------------------ residuals on the map
  /** residual and fitted value per unit (null outside the sample) */
  const perUnit = $derived.by(() => {
    if (!ok) return null;
    const resid: (number | null)[] = new Array(N).fill(null);
    const fit: (number | null)[] = new Array(N).fill(null);
    ok.rows.forEach((i, r) => {
      resid[i] = ok.res.resid[r];
      fit[i] = ok.res.fitted[r];
    });
    let s = 0;
    for (const r of ok.res.resid) s += r * r;
    const sd = Math.sqrt(s / Math.max(1, ok.n - 1)) || 1;
    return { resid, fit, sd };
  });
  const DIV = divRamp();
  const CLASS_COLOURS = [DIV[0], DIV[1], DIV[2], DIV[4], DIV[5], DIV[6]];
  const BREAKS = [-2, -1, 0, 1, 2];
  const classOf = (z: number) => {
    let c = 0;
    while (c < BREAKS.length && z >= BREAKS[c]) c++;
    return c;
  };
  const colours = $derived.by(() => {
    if (!perUnit) return ld.units.map(() => null);
    return perUnit.resid.map((r) => (r === null ? null : CLASS_COLOURS[classOf(r / perUnit.sd)]));
  });
  const classCounts = $derived.by(() => {
    const c = new Array(6).fill(0);
    if (perUnit) for (const r of perUnit.resid) if (r !== null) c[classOf(r / perUnit.sd)]++;
    return c;
  });
  /** a residual in the outcome's units (pp for shares), or as % above/below for a log outcome */
  function residText(r: number): string {
    if (!yInfo) return '';
    if (yInfo.log) return `${signed((10 ** r - 1) * 100)} %`;
    return `${signed(r, 3)} ${yUnitWord(yInfo)}`.trim();
  }
  function levelText(v: number): string {
    if (!yInfo) return '';
    const raw = yInfo.log ? 10 ** v : v;
    const d = yInfo.meta.decimals;
    return `${fmtNumber(raw, Math.abs(raw) >= 1000 ? 0 : d)}${yInfo.meta.unit.startsWith('%') ? ' %' : yInfo.meta.unit ? ` ${unitOf(yInfo.meta)}` : ''}`;
  }
  const tipLines = (i: number): string[] => {
    if (!perUnit || perUnit.resid[i] === null || !yInfo) {
      return [t('rg.notIn')];
    }
    const obs = yInfo.ref.col.v[i]!;
    return [
      `${t('rg.observed')}: ${levelText(yInfo.log ? Math.log10(obs) : obs)}`,
      `${t('rg.fitted')}: ${levelText(perUnit.fit[i]!)}`,
      `${t('rg.resid')}: ${residText(perUnit.resid[i]!)}`,
    ];
  };
  const legendLabels = $derived.by(() => {
    if (!perUnit) return [];
    const s = perUnit.sd;
    const v = (z: number) => residText(z * s);
    return [`< −2σ`, `−2σ…−1σ`, `−1σ…0`, `0…+1σ`, `+1σ…+2σ`, `> +2σ`].map((l, k) => ({ l, c: CLASS_COLOURS[k], n: classCounts[k], v: k === 0 ? `< ${v(-2)}` : k === 5 ? `> ${v(2)}` : `${v(BREAKS[k - 1])}…${v(BREAKS[k])}` }));
  });

  // ------------------------------------------------------------------ map
  let mapEl = $state<HTMLDivElement>();
  let view: UnitMap | null = null;
  let mapReady = $state(false);
  let hover = $state<number | null>(null);
  let hoverAt = $state<{ x: number; y: number } | null>(null);
  const selIdx = $derived(app.sel !== null ? (ld.index.get(app.sel) ?? null) : null);
  function select(i: number | null) {
    app.sel = i === null ? null : ld.units[i];
  }
  onMount(() => {
    view = new UnitMap(mapEl!, base, {
      onSelect: select,
      onHover: (i, p) => {
        hover = i;
        hoverAt = i === null || !p ? null : p;
      },
      onReset: () => fit(true),
      resetLabel: () => t('map.reset'),
    });
    view.ready.then(() => {
      mapReady = true;
      fit();
      view!.map.once('idle', () => onrendered?.());
    });
    const ro = new ResizeObserver(() => view?.map.resize());
    ro.observe(mapEl!);
    return () => {
      ro.disconnect();
      view?.map.remove();
    };
  });
  function fit(animate = false) {
    if (!view) return;
    view.map.resize();
    view.map.fitBounds(CH_BOUNDS, { padding: 8, animate, duration: animate ? 500 : 0 });
  }
  $effect(() => {
    void desktop;
    if (mapReady) tick().then(() => requestAnimationFrame(() => fit()));
  });
  $effect(() => {
    if (!mapReady) return;
    if (desktop) view!.map.cooperativeGestures.disable();
    else view!.map.cooperativeGestures.enable();
  });
  $effect(() => {
    void app.lang;
    if (mapReady) view!.relabel();
  });
  $effect(() => {
    const d = ld;
    if (mapReady) view!.setLevel(d);
  });
  $effect(() => {
    void ld;
    const c = colours;
    if (mapReady) view!.setColours(c);
  });
  $effect(() => {
    const s = selIdx;
    if (mapReady) view!.setSelected(s);
  });
  $effect(() => {
    const h = hover;
    if (mapReady) view!.setHover(h);
  });

  // ------------------------------------------------------------------ exports
  const stamp = () => slug(yInfo ? ml(yInfo.meta) : 'model');
  const seText = $derived(ok ? `${seLabel(seUsed)}${ok.clusters ? ` (${t('rg.clusters', { g: ok.clusters })})` : ''}` : '');
  function coefCSV() {
    if (!ok || !yInfo) return;
    const vi = (tm: TermInfo) => (tm.x !== undefined ? (xInfos as VarInfo[])[tm.x] : null);
    const rows: Cell[][] = [['term', 'label', 'coefficient', 'std_error', 'ci95_low', 'ci95_high', 'beta_standardized', 't', 'p', 'transform', 'period', 'source']];
    ok.terms.forEach((tm, j) => {
      const v = vi(tm);
      const r = ok.res;
      rows.push([tm.key, tm.label, r.coef[j], r.se[j], r.lo[j], r.hi[j], tm.kind === 'x' ? r.beta[j] : null, r.t[j], r.p[j], v ? (v.log ? 'log10' : 'none') : null, v ? v.ref.col.period : null, v ? v.meta.source : null]);
    });
    rows.push([]);
    const meta: [string, Cell][] = [
      ['outcome', `${yInfo.meta.id}${yInfo.log ? ' (log10)' : ''}`], ['outcome_period', yInfo.ref.col.period], ['outcome_source', yInfo.meta.source],
      ['level', ld.level], ['n', ok.n], ['units_at_level', N], ['r2', ok.res.r2], ['r2_adjusted', ok.res.r2adj], ['k_parameters', ok.res.k],
      ['se_type', seUsed === 'cluster' ? 'CR1 clustered by canton' : seUsed === 'hc1' ? 'HC1 robust' : 'conventional'], ['clusters', ok.clusters], ['df', ok.res.df],
      ['controls', ctrl === 'none' ? 'none' : ctrl === 'lang' ? `language region (reference ${ok.feRef})` : `canton fixed effects (reference ${ok.feRef})`],
      ['weights', weights ? `pop_total ${weights.period}` : 'none'], ['flagged_values_left_out', spec.drop ? 'yes' : 'no'],
      ['sample', spec.filtered && filtered ? `filters: ${filterText}` : 'all units'],
      ...ok.dropped.map(([k, v]) => [`left_out: ${k}`, v] as [string, Cell]),
      ['view', location.href],
    ];
    for (const [k, v] of meta) rows.push([k, v]);
    downloadCSV(rows, `atlas-regression-${stamp()}-coefficients.csv`);
  }
  function residCSV() {
    if (!ok || !yInfo || !perUnit) return;
    const rows: Cell[][] = [['id', 'name', 'canton', 'observed', 'fitted', 'residual', 'outcome_value', 'weight']];
    ok.rows.forEach((i, r) => {
      rows.push([ld.units[i], names[i], ld.canton[i] || null, ok.y[r], ok.res.fitted[r], ok.res.resid[r], yInfo!.ref.col.v[i], weights ? weights.v[i] : null]);
    });
    downloadCSV(rows, `atlas-regression-${stamp()}-residuals.csv`);
  }
  let pngBusy = $state(false);
  async function mapPNG() {
    if (!view || !ok || !yInfo || pngBusy) return;
    pngBusy = true;
    try {
      const img = await grabMap(view.map);
      const legend: LegendItem[] = legendLabels.map((x) => ({ colour: x.c, label: `${x.v} (${fmtNumber(x.n, 0)})` }));
      if (ok.n < N) legend.push({ colour: null, label: `${t('rg.notIn')} (${fmtNumber(N - ok.n, 0)})` });
      const vars = [yInfo, ...(xInfos as VarInfo[])];
      const credits = [...new Set(vars.map((v) => v.meta.source))].map((s) => {
        const src = base.sources.get(s);
        return `${t('lg.source')}${colon()}${bareAttribution(src?.attribution || src?.publisher || s)}`;
      });
      const blob = await figurePNG({
        layers: [img], scale: img.width / Math.max(1, mapEl!.clientWidth),
        title: `${t('rg.map')}: ${ml(yInfo.meta)}`,
        subtitle: [
          formula,
          `n = ${fmtNumber(ok.n, 0)} ${word} · R² = ${fmtNumber(ok.res.r2, 3)} · ${seText}${weights ? ` · ${t('rg.weights')} ${weights.period}` : ''}`,
          vars.map((v) => `${ml(v.meta)}: ${fmtPeriod(v.ref.col.period, true)}`).join(' · '),
          `${t('rg.more')} (+) / ${t('rg.less')} (−) · σ = ${residText(perUnit!.sd).replace(/^\+/, '')}`,
          spec.filtered && filtered ? `${t('tab.filters')}: ${filterText}` : '',
        ].filter(Boolean).join('\n'),
        legend,
        credits: [...credits, `${t('ex.boundaries')} · ${t('ex.made')}`],
        link: t('ex.view', { url: location.href }),
      });
      downloadBlob(blob, `atlas-regression-${stamp()}-residuals.png`);
    } finally {
      pngBusy = false;
    }
  }
  const tableTerms = $derived(ok ? ok.terms.map((tm, j) => ({ tm, j })).filter(({ tm }) => tm.kind !== 'kt') : []);
  const varOf = (tm: TermInfo) => (tm.x !== undefined ? (xInfos[tm.x] as VarInfo) : null);
</script>

{#snippet varRow(v: RegVar, info: VarInfo | null | undefined, tag: string, onpick: (id: string) => void, onlog: (b: boolean) => void, onremove: (() => void) | null)}
  <div class="vrow">
    <div class="vpick"><MetricPicker metrics={base.metrics} level={ld.level} value={v.id} {tag} {onpick} /></div>
    <label class="lg" title={t('rg.logT')}><input type="checkbox" checked={v.log} onchange={(e) => onlog(e.currentTarget.checked)} /> log</label>
    {#if onremove}<button type="button" class="rm" aria-label={t('rg.remove', { v: info ? ml(info.meta) : v.id })} onclick={onremove}>×</button>{/if}
  </div>
  {#if info === null}<p class="vnote">{whyVar(v)}</p>
  {:else if info?.logNo}<p class="vnote">{info.logNo}</p>
  {:else if info && info.nonPos > 0}<p class="vnote">{t('rg.logDrop', { n: fmtNumber(info.nonPos, 0) })}</p>{/if}
{/snippet}

<nav class="presets" aria-label={t('cv.examplesL')}>
  <LevelSwitch value={ld.level} onchange={(l) => { app.levelNote = null; app.setLevel(l); }} />
  <span class="caps">{t('pl.try')}</span>
  {#each presets as p}
    <button type="button" class="chip" aria-pressed={activePreset === p.slug} onclick={() => applyPreset(p.slug)}>{t(p.label)}</button>
  {/each}
</nav>
{#if app.filters.length}
  <div class="fbar" role="status">
    <span class="caps">{t('tab.filters')}</span>
    <span class="ftx">{#if filtered}<strong class="num">{t('fp.match', { n: fmtNumber(match.n, 0), total: fmtNumber(N, 0), units: word })}</strong>{' · '}{/if}{filterText}</span>
    <label class="chk"><input type="checkbox" checked={spec.filtered} onchange={(e) => update({ filtered: e.currentTarget.checked })} /> {t('rg.useFilters')}</label>
    <a href={hrefFor('map', {}, { tab: 'filters' })} class="fedit">{t('cv.editFilters')}</a>
  </div>
{/if}

<main class="stage" id="main" tabindex="-1">
  <h1 class="sr-only">{t('nav.regress')}</h1>
  <div class="left">
    <section class="spec" aria-label={t('rg.model')}>
      <div class="caps">{t('rg.outcome')}</div>
      {@render varRow(spec.y, yInfo, 'Y', (id) => update({ y: { ...spec.y, id } }), (b) => update({ y: { ...spec.y, log: b } }), null)}
      <div class="caps sp">{t('rg.xs')}</div>
      {#each spec.xs as v, k (k)}
        {@render varRow(v, xInfos[k], `X${k + 1}`, (id) => setX(k, { id }), (b) => setX(k, { log: b }), () => removeX(k))}
      {/each}
      {#if spec.xs.length < MAX_X}<button type="button" class="add" onclick={addX}>{t('rg.add')}</button>{/if}

      <div class="caps sp">{t('rg.controls')}<Term k="fixed_effects" /></div>
      <div class="seg" role="radiogroup" aria-label={t('rg.controls')}>
        <button type="button" role="radio" aria-checked={ctrl === 'none'} onclick={() => update({ ctrl: 'none' })}>{t('rg.c.none')}</button>
        <button type="button" role="radio" aria-checked={ctrl === 'lang'} disabled={!langOk} onclick={() => update({ ctrl: 'lang' })}>{t('rg.c.lang')}</button>
        <button type="button" role="radio" aria-checked={ctrl === 'kt'} disabled={!ktOk} onclick={() => update({ ctrl: 'kt' })}>{t('rg.c.ktS')}</button>
      </div>
      {#if !langOk || !ktOk}<p class="vnote">{!ktOk ? t('rg.c.ktOnly') : t('rg.c.langOnly')}</p>{/if}

      <div class="caps sp">{t('rg.options')}</div>
      <label class="chk"><input type="checkbox" checked={spec.weights} onchange={(e) => update({ weights: e.currentTarget.checked })} /> {t('rg.weights')}</label>
      {#if spec.weights && weights && yRef}<p class="vnote">{t('rg.weightsT', { p: fmtPeriod(weights.period), y: fmtPeriod(yRef.col.period) })}</p>{/if}
      <label class="chk"><input type="checkbox" checked={spec.drop} onchange={(e) => update({ drop: e.currentTarget.checked })} /> {t('rg.drop')}</label>
      {#if ok && ok.flaggedSmall && !spec.drop && app.unstable === 'hide'}<p class="hint r3">{t('r3.rgShown')} ({fmtNumber(ok.flaggedSmall, 0)} △)</p>{/if}

      <div class="caps sp">{t('rg.se')}<Term k="clustered_se" /></div>
      <div class="seg" role="radiogroup" aria-label={t('rg.se')}>
        <button type="button" role="radio" aria-checked={seUsed === 'cluster'} disabled={!ktOk} onclick={() => update({ se: 'cluster' })}>{t('rg.se.clusterS')}</button>
        <button type="button" role="radio" aria-checked={seUsed === 'hc1'} onclick={() => update({ se: 'hc1' })}>HC1</button>
        <button type="button" role="radio" aria-checked={seUsed === 'ols'} onclick={() => update({ se: 'ols' })}>{t('rg.se.olsS')}</button>
      </div>
      <p class="vnote">{spec.se === 'cluster' && !ktOk ? t('rg.se.fallback', { units: word }) : t(`rg.se.note.${seUsed}`)}</p>
    </section>

    <section class="res" aria-live="polite">
      <div class="caps">{t('rg.results')}</div>
      {#if model.status === 'loading'}
        <p class="muted">{t('status.loading')}</p>
      {:else if model.status === 'error'}
        <p class="err">{t('rg.err', { e: model.msg })}</p>
      {:else if ok && yInfo}
        <p class="formula">{formula}</p>
        <div class="fit num">
          <span><b>n</b> {fmtNumber(ok.n, 0)}</span>
          <span><b>{weights ? t('r3.r2w') : 'R²'}</b><Term k="r_squared" /> {fmtNumber(ok.res.r2, 3)}</span>
          <span><b>{t('rg.r2adj')}</b> {fmtNumber(ok.res.r2adj, 3)}</span>
          {#if ok.within !== null}<span title={t('r3.r2withinT')}><b>{t('r3.r2within')}</b> {fmtNumber(ok.within, 3)}</span>{/if}
          <span class="sel">{seText}</span>
        </div>
        <!-- B7 (X1, X9): what R² measures here (weighted or not, one variable or several) and what the SE choice changes -->
        <p class="plain">{t(spec.xs.length === 1 && ctrl === 'none' ? 'r3.r2Plain1' : 'ux.r2Plain', { p: fmtNumber(Math.max(0, ok.res.r2) * 100, 0), y: ml(yInfo.meta), units: word, x: ok.terms.find((tm) => tm.kind === 'x')?.label ?? '' })}{weights ? ` ${t('r3.r2wNote')}` : ''}{ok.within !== null ? ` ${t('r3.withinNote', { p: fmtNumber(Math.max(0, ok.within) * 100, 0), g: ctrl === 'kt' ? t('r3.inCantons') : t('r3.inRegions') })}` : ''}</p>
        <p class="plain se">{t('r3.seNote')}</p>
        <div class="tw">
          <table class="coef">
            <thead>
              <tr>
                <th class="vh">{t('rg.var')}</th>
                <th>{t('rg.coef')}<Term k="coefficient" /></th>
                <th>{t('rg.seh')}</th>
                <th>{t('rg.ci')}<Term k="confidence_interval" /></th>
                <th>β<Term k="standardized_coefficient" /></th>
                <th class="tc">t</th>
                <th>p</th>
              </tr>
            </thead>
            <tbody>
              {#each tableTerms as { tm, j } (tm.key)}
                {@const r = ok.res}
                {@const vi = varOf(tm)}
                <tr class:const={tm.kind === 'const'} class:dummy={tm.kind === 'lang'}>
                  <th class="vh">
                    {tm.label}
                    {#if vi}<span class="vp">{fmtPeriod(vi.ref.col.period)} · {sourceOf(vi.meta)}</span>{/if}
                  </th>
                  {#if r.collinear[j]}
                    <td colspan={desktop ? 6 : 5} class="muted">{t('rg.dropCol')}</td>
                  {:else}
                    <td class="num b">{fmtCoef(r.coef[j])}</td>
                    <td class="num">{fmtCoef(r.se[j])}</td>
                    <td class="num ci">{fmtCoef(r.lo[j])} … {fmtCoef(r.hi[j])}</td>
                    <td class="num">{tm.kind === 'x' ? fmtNumber(r.beta[j], 2) : ''}</td>
                    <td class="num tc">{fmtNumber(r.t[j], 2)}</td>
                    <td class="num" class:sig={r.p[j] < 0.05}>{fmtP(r.p[j])}</td>
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        <p class="foot">
          {t('rg.outcomeLine', { y: ml(yInfo.meta), p: fmtPeriod(yInfo.ref.col.period), s: sourceOf(yInfo.meta) })}{yInfo.log ? ` ${t('rg.logY')}` : ''}
          {ctrl === 'lang' && ok.feRef ? ` ${t('rg.langRef', { ref: ok.feRef })}` : ''}
          {ctrl === 'kt' ? ` ${t('rg.fe', { k: ok.feK, ref: ok.feRef ?? '' })}` : ''}
          {weights ? ` ${t('rg.weightsUsed', { p: fmtPeriod(weights.period) })}` : ''}
          {t('rg.dfLine', { df: ok.res.df })}
        </p>
        {#if ok.clusters !== null && ok.clusters < 10}<p class="warnl">{t('rg.fewClusters', { g: ok.clusters })}</p>{/if}
        {#if ok.collinear.length}<p class="warnl">{t('rg.collinear', { v: ok.collinear.join(', ') })}</p>{/if}

        <!-- X9: "other variables held constant" only when there are others (variables or fixed effects) -->
        <div class="caps sp">{t(spec.xs.length === 1 && ctrl === 'none' ? 'r3.words1' : 'rg.words')}</div>
        <ul class="words">
          {#each words as w}
            {#if w}<li><span class="wx">{w.x}</span> → <strong class="num">{w.y}</strong> <span class="muted">({w.ci})</span></li>{/if}
          {/each}
        </ul>

        <div class="caps sp">{t('rg.sample')}</div>
        <p class="drop">{t('rg.used', { n: fmtNumber(ok.n, 0), m: fmtNumber(N, 0), units: word })}</p>
        {#if ok.dropped.length}
          <ul class="dropl">
            {#each ok.dropped as [k, v]}<li><span class="num">{fmtNumber(v, 0)}</span> {k}</li>{/each}
          </ul>
          <p class="foot">{t('rg.firstReason')}</p>
        {/if}

        <div class="exrow">
          <button type="button" class="exb" onclick={coefCSV}>{t('rg.csvCoef')}</button>
          <button type="button" class="exb" onclick={residCSV}>{t('rg.csvRes')}</button>
          <button type="button" class="exb" onclick={mapPNG} disabled={pngBusy}>{pngBusy ? t('ex.pngWait') : t('ex.pngMap')}</button>
        </div>
      {/if}

      <div class="cav">
        <div class="caps">{t('rg.cav')}</div>
        <ul>
          <li>{t('rg.cav.cause')}</li>
          <li>{t('rg.cav.eco')}</li>
          <li>{t('rg.cav.spatial')}</li>
          <li>{t('rg.cav.small')}{ok && !spec.drop && ok.flaggedSmall ? ` ${t('rg.cav.smallN', { n: fmtNumber(ok.flaggedSmall, 0) })}` : ''}</li>
          {#if periodsText}<li>{t('rg.cav.years', { list: periodsText })}</li>{/if}
          {#if partyVar}<li>{t('rg.cav.maj')}{ok && !spec.drop && ok.flaggedMaj ? ` ${t('rg.cav.majN', { n: fmtNumber(ok.flaggedMaj, 0) })}` : ''}
            {app.maj ? t('rg.majIn') : t('rg.majOut')}
            <button type="button" class="majt" onclick={() => (app.maj = !app.maj)}>{app.maj ? t('lg.majExclude') : t('lg.majInclude')}</button></li>{/if}
          {#each regionalVars as r}<li>{t('rg.cav.reg', { v: r.label, level: r.level })}</li>{/each}
        </ul>
      </div>
    </section>
  </div>

  <section class="viz">
    <div class="vhead">
      <span class="caps">{t('rg.map')}<Term k="residual" /></span>
    </div>
    <div class="mapbox">
      <div class="map" bind:this={mapEl}></div>
      {#if hover !== null && hoverAt && desktop}
        <div class="maptip" style="left:{hoverAt.x}px; top:{hoverAt.y}px">
          <strong>{names[hover]}</strong>{#if ld.canton[hover] && ld.level !== 'kanton' && !names[hover].includes('(')}&nbsp;<span class="muted">{ld.canton[hover]}</span>{/if}
          {#each tipLines(hover) as l}<div class="num">{l}</div>{/each}
        </div>
      {/if}
    </div>
    {#if ok && perUnit}
      <div class="rleg">
        <div class="ends"><span>← {t('rg.less')}</span><span>{t('rg.more')} →</span></div>
        <div class="sw">
          {#each legendLabels as x}<span class="cell" title={x.v}><i style="background:{x.c}"></i><span class="cl">{x.l}</span><span class="num cn">{fmtNumber(x.n, 0)}</span></span>{/each}
        </div>
        <p class="foot">
          {t('rg.sigma', { s: residText(perUnit.sd).replace(/^\+/, '') })}{weights ? ` ${t('r3.sigmaUnw')}` : ''}
          {#if ok.n < N}<span class="nd"><span class="hatch"></span> {t('rg.notIn')} ({fmtNumber(N - ok.n, 0)})</span>{/if}
        </p>
      </div>
    {/if}
    {#if selIdx !== null}
      <div class="selbox">
        <div class="st"><strong>{names[selIdx]}</strong>{#if ld.canton[selIdx] && ld.level !== 'kanton'}&nbsp;<span class="muted">{ld.canton[selIdx]}</span>{/if}
          <a class="prof" href={profileHref(refOf(ld.level, ld.units[selIdx]))}>{t('card.profile')}&nbsp;→</a>
          <button type="button" class="close" aria-label={t('common.close')} onclick={() => (app.sel = null)}>×</button>
        </div>
        <div class="num sl">{tipLines(selIdx).join(' · ')}</div>
      </div>
    {/if}
    {#if ok && yInfo && perUnit}
      <div class="caps sp">{t('rg.scatter')}</div>
      <ResidPlot idx={ok.rows} fitted={ok.res.fitted} resid={ok.res.resid} region={regions} regionNames={REGION_NAMES()} {names} cantons={ld.canton}
        xTitle={`${t('rg.fitted')}${yInfo.log ? ' (log₁₀)' : ''}`} yTitle={`${t('rg.resid')}${yInfo.log ? ' (log₁₀)' : ''}`} decimals={yInfo.log ? 2 : yInfo.meta.decimals}
        {tipLines} {hover} sel={selIdx} onhover={(i) => (hover = i)} onselect={select} />
      <p class="foot">{t('rg.scatterNote')}</p>
    {/if}
  </section>
</main>

<style>
  .plain { margin: var(--sp-2) 0 0; font-size: var(--fs-small); line-height: var(--lh-small); }
  .plain.se { color: var(--text-2); font-size: var(--fs-meta); line-height: var(--lh-meta); }
  .presets {
    flex: none; display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: var(--panel); border-bottom: 1px solid var(--rule);
    overflow-x: auto; scrollbar-width: none;
  }
  .presets .caps { margin: 0 4px 0 8px; flex: none; }
  .chip {
    flex: none; min-height: var(--ctl-h); padding: 0 var(--sp-3); border: 1px solid var(--ink); background: none; cursor: pointer; font-size: var(--fs-body); font-weight: 500; white-space: nowrap; color: var(--text);
  }
  .chip:hover { background: var(--surface-2); }
  .chip[aria-pressed='true'] { background: var(--ink); border-color: var(--ink); color: var(--ink-text); }
  .fbar {
    flex: none; display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; padding: 5px 16px; font-size: var(--fs-meta);
    border-bottom: 1px solid var(--rule); background: var(--panel);
  }
  .ftx { flex: 1 1 240px; min-width: 0; }
  .fedit { color: var(--text); font-size: var(--fs-meta); }

  .stage { flex: 1; min-height: 0; position: relative; background: var(--panel); }
  .stage:focus { outline: none; }
  section { min-width: 0; }
  .spec, .res { padding: 12px 16px 14px; }
  .res { border-top: 1px solid var(--rule); }
  .viz { padding: 12px 16px 16px; display: flex; flex-direction: column; }
  .viz > * { flex: none; }
  .sp { margin-top: 14px; }
  .caps { margin-bottom: 5px; }
  .vrow { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
  .vpick { flex: 1; min-width: 0; }
  .lg { flex: none; display: inline-flex; align-items: center; gap: 3px; font-size: var(--fs-small); cursor: pointer; }
  .lg input, .chk input { accent-color: var(--ink); margin: 0; }
  .rm { flex: none; width: 26px; height: 26px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-size: var(--fs-body); line-height: 1; color: var(--text); }
  .vnote { margin: -1px 0 6px; font-size: var(--fs-meta); border-left: 3px solid var(--ink); padding-left: 6px; color: var(--text); }
  .add { border: 1px solid var(--ink); background: none; min-height: var(--ctl-h); padding: 0 var(--sp-3); cursor: pointer; font-size: var(--fs-body); font-weight: 500; color: var(--text); }
  .seg { flex-wrap: wrap; margin-bottom: 4px; }
  .seg button { padding: 4px 9px; font-size: var(--fs-meta); }
  .chk { display: flex; align-items: flex-start; gap: 6px; font-size: var(--fs-small); margin: 4px 0; cursor: pointer; }
  .chk input { margin-top: 2px; }
  .hint.r3 { margin: 2px 0 6px 20px; font-size: var(--fs-meta); line-height: var(--lh-meta); color: var(--text-2); }
  .fbar .chk { margin: 0; }
  .muted { color: var(--muted); }
  .err { margin: 0; border-left: 3px solid var(--ink); padding-left: 8px; font-size: var(--fs-small); }
  .formula { margin: 0 0 6px; font-weight: 700; font-size: var(--fs-body); line-height: 1.3; }
  .fit { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: var(--fs-small); padding: 6px 0; border-top: 3px solid var(--rule); border-bottom: 1px solid var(--rule); }
  .fit b { font-weight: 600; color: var(--muted); margin-right: 3px; }
  .fit .sel { color: var(--muted); font-family: var(--font-sans); }
  .tw { overflow-x: auto; margin-top: 2px; }
  table.coef { width: 100%; border-collapse: collapse; font-size: var(--fs-small); }
  .coef th, .coef td { padding: 5px 4px; text-align: right; white-space: nowrap; vertical-align: top; }
  .coef thead th { font-weight: 700; font-size: var(--fs-meta); border-bottom: 1px solid var(--rule); }
  .coef tbody tr + tr { border-top: 1px solid var(--border); }
  .coef .vh { text-align: left; white-space: normal; font-weight: 600; min-width: 130px; }
  .coef thead .vh { font-weight: 700; }
  .vp { display: block; font-weight: 400; font-size: var(--fs-cap); color: var(--faint); }
  .coef .b { font-weight: 700; }
  .coef .ci { color: var(--muted); }
  .coef .sig { font-weight: 700; }
  .coef tr.const th, .coef tr.const td { color: var(--muted); font-weight: 400; }
  .coef tr.dummy th { font-weight: 500; }
  .warnl { margin: 6px 0 0; font-size: var(--fs-meta); border-left: 3px solid var(--ink); padding-left: 6px; }
  .words { margin: 0; padding: 0; list-style: none; font-size: var(--fs-small); }
  .words li { padding: 3px 0; line-height: 1.35; }
  .words li + li { border-top: 1px solid var(--border); }
  .drop { margin: 0 0 4px; font-size: var(--fs-small); }
  .dropl { margin: 0; padding: 0 0 0 2px; list-style: none; font-size: var(--fs-small); }
  .dropl .num { display: inline-block; min-width: 3.2em; text-align: right; margin-right: 6px; font-weight: 600; }
  .exrow { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
  .exb { border: 1px solid var(--ink); background: var(--panel); padding: 4px 9px; cursor: pointer; font-size: var(--fs-meta); font-weight: 600; color: var(--text); }
  .exb:disabled { opacity: 0.5; cursor: progress; }
  .cav { margin-top: 16px; padding-top: 8px; border-top: 3px solid var(--rule); }
  .cav ul { margin: 0; padding-left: 16px; font-size: var(--fs-meta); color: var(--text); line-height: 1.4; }
  .cav li + li { margin-top: 3px; }

  .vhead { display: flex; align-items: center; justify-content: space-between; }
  .mapbox { position: relative; flex: none; height: 420px; border: 1px solid var(--rule); background: var(--map-bg); }
  .map { position: absolute; inset: 0; }
  .maptip {
    position: absolute; z-index: 5; pointer-events: none; transform: translate(14px, 14px); background: var(--panel);
    border: 1px solid var(--ink); padding: 6px 9px; font-size: var(--fs-small); white-space: nowrap;
  }
  .rleg { margin-top: 6px; }
  .ends { display: flex; justify-content: space-between; font-size: var(--fs-meta); font-weight: 600; }
  .sw { display: grid; grid-template-columns: repeat(6, 1fr); gap: 2px; margin-top: 3px; }
  .cell { display: flex; flex-direction: column; align-items: center; font-size: var(--fs-cap); }
  .cell i { display: block; width: 100%; height: 10px; }
  .cl { margin-top: 2px; white-space: nowrap; }
  .cn { color: var(--muted); }
  .rleg .foot { margin: 4px 0 0; display: flex; flex-wrap: wrap; gap: 4px 12px; }
  .nd { display: inline-flex; align-items: center; gap: 4px; }
  .selbox { margin-top: 8px; padding: 6px 8px; border: 1px solid var(--ink); border-top: 3px solid var(--ink); font-size: var(--fs-small); }
  .st { display: flex; align-items: center; gap: 6px; }
  .st strong { font-size: var(--fs-body); }
  .prof { margin-left: auto; font-size: var(--fs-meta); font-weight: 700; color: var(--ink-text); background: var(--ink); padding: 3px 8px; text-decoration: none; white-space: nowrap; }
  .close { border: 1px solid var(--ink); background: none; width: 24px; height: 24px; cursor: pointer; color: var(--text); }
  .sl { margin-top: 3px; }

  @media (min-width: 900px) {
    .stage { display: grid; grid-template-columns: minmax(360px, 1fr) minmax(0, 1fr); }
    .left { overflow-y: auto; border-right: 1px solid var(--rule); min-height: 0; }
    .viz { overflow-y: auto; min-height: 0; }
    .mapbox { height: min(52vh, 480px); }
  }
  @media (min-width: 1280px) {
    .stage { grid-template-columns: 330px minmax(0, 1.05fr) minmax(0, 1fr); }
    .left { display: contents; }
    .spec { overflow-y: auto; border-right: 1px solid var(--rule); min-height: 0; }
    .res { overflow-y: auto; border-top: 0; border-right: 1px solid var(--rule); min-height: 0; }
  }
  @media (max-width: 899px) {
    /* U16: the example chips wrap instead of running off the screen */
    .presets { padding: var(--sp-2) var(--gutter); flex-wrap: wrap; overflow: visible; row-gap: var(--sp-2); }
    .presets .caps { margin-left: 0; }
    .stage { overflow-y: auto; -webkit-overflow-scrolling: touch; }
    .viz { border-top: 1px solid var(--rule); padding-bottom: calc(16px + env(safe-area-inset-bottom)); }
    .mapbox { height: 300px; }
    .coef { font-size: var(--fs-meta); }
    .coef th, .coef td { padding: 5px 3px; }
    .coef .vh { min-width: 0; }
    .coef .ci { white-space: normal; min-width: 4.5em; }
    .coef .tc { display: none; }
    :global(.regress .maplibregl-ctrl-top-right .maplibregl-ctrl-group:not(.gb-btn)) { display: none; }
  }
  .majt { border: 0; background: none; padding: 0; text-decoration: underline; cursor: pointer; font-size: inherit; color: var(--text); }
</style>
