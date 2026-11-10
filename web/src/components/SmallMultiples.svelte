<script lang="ts">
  // Small multiples: the same metric in several years side by side, one small map per year, all with the
  // same class limits (every year pooled), so a colour means the same thing in every panel. Drawn on
  // canvases from the level's own geometry (no extra map instances), with lakes and canton outlines.
  import { onMount, tick } from 'svelte';
  import { buildScale, divergeCentre, fmtNumber, fmtPeriod, fmtTick, isDiverging, legendItems, sortedValues, type Method } from '../lib/classify';
  import type { Base, LevelData, MetricMeta } from '../lib/data';
  import type { ColumnStore } from '../lib/columns.svelte';
  import { ml, t } from '../lib/i18n.svelte';
  import '../lib/i18n-mapx';
  import { CH_BOUNDS } from '../lib/mapview';
  import { divRamp, seqRamp, token } from '../lib/theme';
  import { defaultPeriods, pooledSpan } from '../lib/yearcmp.svelte';
  import { unitOf } from '../lib/classify';
  import { unstableIndices } from '../lib/small.svelte';
  import { app } from '../lib/state.svelte';
  import '../lib/i18n-r3';

  interface Props {
    base: Base;
    ld: LevelData;
    cols: ColumnStore;
    meta: MetricMeta;
    /** all periods of the metric at this level */
    periods: string[];
    picked: string[];
    /** all years pooled (ascending): defines the shared classes; undefined while loading, null if unavailable */
    pooled: number[] | null | undefined;
    method: Method;
    /** units that match the filters (others are muted); null = no filter */
    mask: Uint8Array | null;
    onpick: (p: string[]) => void;
    onclose: () => void;
    /** the map shows a change between two years (the panels show each year's values: say so) */
    change?: boolean;
  }
  let { base, ld, cols, meta, periods, picked, pooled, method, mask, onpick, onclose, change = false }: Props = $props();

  const MAX = 9;
  const shown = $derived.by(() => {
    const ok = periods.filter((p) => picked.includes(p));
    return ok.length ? ok : defaultPeriods(periods);
  });

  // ---------------------------------------------------------------- shared scale and the panels' data
  // B2: the panels follow the map's small-number setting: hidden values are gaps, counted apart from no data
  const panels = $derived(shown.map((p) => {
    const ref = cols.get(ld, meta.id, p);
    const hid = ref && app.unstable === 'hide' ? unstableIndices(cols, ld, meta, ref) : [];
    if (!ref || !hid.length) return { p, ref, hidden: 0 };
    const v = ref.col.v.slice();
    for (const i of hid) v[i] = null;
    return { p, ref: { ...ref, col: { ...ref.col, v } }, hidden: hid.length };
  }));
  /** the pooled values, or (until they are loaded) the values of the panels that are in */
  const ref = $derived.by(() => {
    if (pooled && pooled.length) return pooled;
    const all: number[] = [];
    for (const pn of panels) if (pn.ref) for (const x of pn.ref.col.v) if (x !== null) all.push(x);
    return all.sort((a, b) => a - b);
  });
  const scale = $derived(ref.length ? buildScale(ref, method, isDiverging(meta, ref), seqRamp(), divRamp(), divergeCentre(meta), ref) : null);
  const items = $derived(scale ? legendItems(scale, meta) : []);
  const span = $derived(pooledSpan(meta));

  // ---------------------------------------------------------------- geometry as Path2D, per panel size
  const mx = (lon: number) => (lon + 180) / 360;
  const my = (lat: number) => (180 - (180 / Math.PI) * Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))) / 360;
  const [x0, y0, x1, y1] = CH_BOUNDS;
  const BX = mx(x1) - mx(x0);
  const BY = my(y0) - my(y1);
  const ASPECT = BY / BX;
  const PAD = 3;

  let gridW = $state(320);
  const cols_n = $derived(gridW >= 760 ? 3 : gridW >= 320 ? 2 : 1);
  const cw = $derived(Math.max(120, Math.floor((gridW - (cols_n - 1) * 10) / cols_n)));
  const ch = $derived(Math.round(cw * ASPECT));

  interface Paths {
    key: string;
    units: Map<number, Path2D>;
    lakes: Path2D;
    cantons: Path2D;
  }
  let paths: Paths | null = null;
  function ringPath(p: Path2D, ring: number[][], w: number, h: number) {
    const sx = (w - 2 * PAD) / BX;
    const sy = (h - 2 * PAD) / BY;
    for (let k = 0; k < ring.length; k++) {
      const x = PAD + (mx(ring[k][0]) - mx(x0)) * sx;
      const y = PAD + (my(ring[k][1]) - my(y1)) * sy;
      if (k === 0) p.moveTo(x, y);
      else p.lineTo(x, y);
    }
    p.closePath();
  }
  function geomPath(p: Path2D, g: import('geojson').Geometry | null, w: number, h: number) {
    if (!g) return;
    const polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
    for (const poly of polys) for (const r of poly) ringPath(p, r, w, h);
  }
  function build(w: number, h: number): Paths {
    const key = `${ld.level}|${w}x${h}`;
    if (paths && paths.key === key) return paths;
    const units = new Map<number, Path2D>();
    for (const f of ld.geo.features) {
      const p = new Path2D();
      geomPath(p, f.geometry, w, h);
      units.set(f.id as number, p);
    }
    const lakes = new Path2D();
    for (const f of base.lakes.features) geomPath(lakes, f.geometry, w, h);
    const cantons = new Path2D();
    for (const f of base.kanton.features) geomPath(cantons, f.geometry, w, h);
    return (paths = { key, units, lakes, cantons });
  }

  function hatchPattern(g: CanvasRenderingContext2D): CanvasPattern | string {
    const c = document.createElement('canvas');
    c.width = c.height = 8;
    const k = c.getContext('2d')!;
    k.fillStyle = token('--nodata-fill') || '#f0f0f0';
    k.fillRect(0, 0, 8, 8);
    k.strokeStyle = token('--nodata-line') || '#9a9a9a';
    k.lineWidth = 1;
    k.beginPath();
    for (let q = -1; q <= 2; q++) {
      k.moveTo(q * 4 - 1, 9);
      k.lineTo(q * 4 + 9, -1);
    }
    k.stroke();
    return g.createPattern(c, 'repeat') ?? token('--nodata-fill');
  }

  let canvases = $state<(HTMLCanvasElement | undefined)[]>([]);
  function paint(c: HTMLCanvasElement, v: (number | null)[] | null) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    c.width = Math.round(cw * dpr);
    c.height = Math.round(ch * dpr);
    c.style.width = `${cw}px`;
    c.style.height = `${ch}px`;
    const g = c.getContext('2d')!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, cw, ch);
    const P = build(cw, ch);
    const surface = token('--muted-fill') || '#ececec';
    const nodata = hatchPattern(g);
    for (const [i, path] of P.units) {
      const x = v ? v[i] : null;
      let col: string | CanvasPattern = nodata;
      if (x !== null && scale) {
        col = scale.colourOf(x);
        if (mask && !mask[i]) col = surface;
      } else if (!v) col = token('--nodata-fill') || '#f0f0f0';
      g.fillStyle = col;
      g.fill(path, 'evenodd');
      g.strokeStyle = token('--gem-line') || '#fff';
      g.lineWidth = ld.level === 'gemeinde' ? 0.25 : 0.7;
      g.stroke(path);
    }
    g.fillStyle = token('--water') || '#f1f6f9';
    g.fill(P.lakes, 'evenodd');
    g.strokeStyle = token('--water-line') || '#6f8fa6';
    g.lineWidth = 0.5;
    g.stroke(P.lakes);
    g.strokeStyle = token('--kt-line') || '#000';
    g.lineWidth = 0.6;
    g.globalAlpha = 0.85;
    g.stroke(P.cantons);
    g.globalAlpha = 1;
  }
  $effect(() => {
    void cw; void ch; void scale; void mask; void ld;
    const list = panels.map((pn) => ({ v: pn.ref ? pn.ref.col.v : null }));
    // a panel whose column is still loading is drawn blank, then again when it arrives
    list.forEach((pn, k) => {
      const c = canvases[k];
      if (c) paint(c, pn.v);
    });
  });

  // ---------------------------------------------------------------- picking years
  function toggle(p: string) {
    const cur = shown.slice();
    const k = cur.indexOf(p);
    if (k >= 0) {
      if (cur.length > 1) cur.splice(k, 1);
    } else {
      if (cur.length >= MAX) return;
      cur.push(p);
    }
    onpick(periods.filter((q) => cur.includes(q)));
  }

  // D16: focus goes to the dialog title (read first by screen readers), not to the close button
  let titleEl: HTMLHeadingElement;
  onMount(() => {
    tick().then(() => titleEl?.focus());
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && onclose();
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  });
  const nVals = (v: (number | null)[]) => sortedValues(v).length;
</script>

<div class="sm" role="dialog" aria-label={t('sm.title')}>
  <header>
    <div class="hd">
      <h2 tabindex="-1" bind:this={titleEl}>{t('sm.title')}</h2>
      <p class="mt">{ml(meta)} <span class="un">· {unitOf(meta)}</span></p>
      {#if change}<p class="mt chg">{t('r3.smNote')}</p>{/if}
    </div>
    <button type="button" class="x" aria-label={t('sm.close')} title={t('sm.close')} onclick={onclose}>×</button>
  </header>

  {#if !periods.length}
    <p class="foot pad">{t('sm.level')}</p>
  {:else}
    <div class="chips" role="group" aria-label={t('sm.years')}>
      {#each periods as p}
        <button type="button" class="chip num" aria-pressed={shown.includes(p)} disabled={!shown.includes(p) && shown.length >= MAX} onclick={() => toggle(p)}>{p}</button>
      {/each}
    </div>
    {#if shown.length >= MAX}<p class="foot pad0">{t('sm.max', { n: MAX })}</p>{/if}

    <div class="grid" bind:clientWidth={gridW} style="grid-template-columns: repeat({cols_n}, minmax(0, 1fr))">
      {#each panels as pn, k (pn.p)}
        <figure>
          <figcaption><strong class="num">{fmtPeriod(pn.p)}</strong>
            {#if pn.ref}<span class="foot num">n = {fmtNumber(nVals(pn.ref.col.v), 0)}{pn.hidden ? ` · ${t('r3.smHidden', { h: fmtNumber(pn.hidden, 0) })}` : ''}</span>{:else if pn.ref === undefined}<span class="foot">{t('sm.loading')}</span>{/if}
          </figcaption>
          <div class="cv" role="img" aria-label={t('sm.canvas', { metric: ml(meta), year: pn.p })}>
            <canvas bind:this={canvases[k]} aria-hidden="true"></canvas>
            {#if pn.ref === null || (pn.ref && !nVals(pn.ref.col.v))}<span class="nov foot">{t('sm.noVal')}</span>{/if}
          </div>
        </figure>
      {/each}
    </div>

    <div class="key">
      {#if scale && scale.method === 'continuous'}
        <div class="grad" style="background: linear-gradient(to right, {Array.from({ length: 9 }, (_, q) => scale.colourOf(scale.lo + ((scale.hi - scale.lo) * q) / 8)).join(',')})"></div>
        <div class="ends num"><span>{fmtTick(scale.lo, meta)}</span><span>{fmtTick(scale.hi, meta)}</span></div>
      {:else}
        <div class="cls" style="grid-template-columns: repeat({Math.max(1, items.length)}, 1fr)">
          {#each items as it}
            <div class="c"><span class="sw" style="background:{it.colour}"></span><span class="rng num">{it.label}</span></div>
          {/each}
        </div>
      {/if}
      <p class="foot">
        {pooled === undefined ? t('yc.fixedWait') : pooled === null ? '' : t('sm.note', { span })}
      </p>
    </div>
  {/if}
</div>

<style>
  .sm {
    position: absolute; inset: 0; z-index: 8; background: var(--panel); overflow-y: auto; padding: 12px 14px 16px;
    display: flex; flex-direction: column; gap: 10px; overscroll-behavior: contain;
  }
  @media (max-width: 899px) { .sm { position: fixed; z-index: 60; padding-bottom: calc(16px + env(safe-area-inset-bottom)); } }
  header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; border-bottom: 1px solid var(--ink); padding-bottom: 8px; }
  h2 { margin: 0; font-size: var(--fs-lead); }
  .mt { margin: 2px 0 0; font-size: var(--fs-small); font-weight: 600; }
  .mt.chg { font-weight: 400; color: var(--text-2); font-size: var(--fs-meta); }
  .un { font-weight: 400; color: var(--muted); }
  h2:focus { outline: none; }
  .x { flex: none; width: var(--ctl-h); height: var(--ctl-h); border: 1px solid var(--ink); background: var(--panel); font-size: var(--fs-stat); line-height: 1; cursor: pointer; }
  .x:hover { background: var(--panel-2); }
  /* D16: the years as one joined segment row that scrolls sideways */
  .chips { display: flex; flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; border: 1px solid var(--ink); align-self: flex-start; max-width: 100%; }
  .chips::-webkit-scrollbar { display: none; }
  .chip { flex: none; min-height: var(--ctl-h-sm); padding: 0 var(--sp-3); border: 0; background: var(--panel); font-size: var(--fs-small); cursor: pointer; font-variant-numeric: tabular-nums; }
  .chip + .chip { border-left: 1px solid var(--ink); }
  .chip[aria-pressed='true'] { background: var(--ink); color: var(--ink-text); }
  .chip:disabled { opacity: 0.4; cursor: not-allowed; }
  .grid { display: grid; gap: 12px 10px; }
  figure { margin: 0; min-width: 0; }
  figcaption { display: flex; align-items: baseline; justify-content: space-between; gap: 6px; margin-bottom: 2px; font-size: var(--fs-small); }
  .cv { position: relative; background: var(--map-bg); border: 1px solid var(--border); }
  canvas { display: block; }
  .nov { position: absolute; inset: 0; display: grid; place-items: center; background: color-mix(in srgb, var(--panel) 70%, transparent); }
  .key { border-top: 1px solid var(--rule); padding-top: 8px; }
  .cls { display: grid; gap: 3px; }
  .c { display: flex; flex-direction: column; min-width: 0; }
  .sw { height: 6px; margin-bottom: 2px; }
  .rng { font-size: var(--fs-cap); color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .grad { height: 8px; }
  .ends { display: flex; justify-content: space-between; font-size: var(--fs-cap); color: var(--muted); }
  .key p { margin: 5px 0 0; }
  .pad { padding: 8px 0; }
  .pad0 { margin: -4px 0 0; }
</style>
