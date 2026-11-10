<script lang="ts">
  // Scatter plot of metric A (x) against metric B (y) for every municipality with data in both,
  // drawn on a canvas: points by language region, optional population size, least-squares line,
  // and n, Pearson r, Spearman rho and population-weighted Pearson r.
  import { ml, t as tr } from '../lib/i18n.svelte';
  import type { MetricMeta } from '../lib/data';
  import {
    fmtNumber, fmtPeriod, fmtR, fmtTick, fmtValue, logTicks, niceTicks, pearson, sortedValues, spearman, wantsLog,
  } from '../lib/classify';
  import { regionColours, token } from '../lib/theme';

  interface Props {
    xMeta: MetricMeta;
    yMeta: MetricMeta;
    x: (number | null)[];
    y: (number | null)[];
    xPeriod: string;
    yPeriod: string;
    region: Int8Array;
    regionNames: string[];
    pop: (number | null)[];
    names: string[];
    cantons: string[];
    hover: number | null;
    sel: number | null;
    isDark: boolean;
    onhover: (i: number | null) => void;
    onselect: (i: number | null) => void;
    unitWord?: string;
    unitOne?: string;
  }
  let {
    xMeta, yMeta, x, y, xPeriod, yPeriod, region, regionNames, pop, names, cantons, hover, sel, isDark, onhover, onselect,
    unitWord = 'municipalities', unitOne = 'municipality',
  }: Props = $props();

  let sizeByPop = $state(false);
  let logX = $state(false);
  let logY = $state(false);
  let w = $state(600);
  let h = $state(320);
  let canvas: HTMLCanvasElement;
  let tip = $state<{ i: number; left: number; top: number } | null>(null);

  // default to a log axis for heavily skewed positive metrics; reset when the metric changes
  $effect(() => {
    logX = wantsLog(sortedValues(x));
  });
  $effect(() => {
    logY = wantsLog(sortedValues(y));
  });

  const pts = $derived.by(() => {
    const idx: number[] = [];
    const px: number[] = [];
    const py: number[] = [];
    const pw: number[] = [];
    for (let i = 0; i < x.length; i++) {
      const a = x[i];
      const b = y[i];
      if (a === null || b === null || !Number.isFinite(a) || !Number.isFinite(b)) continue;
      if ((logX && a <= 0) || (logY && b <= 0)) continue;
      idx.push(i);
      px.push(logX ? Math.log10(a) : a);
      py.push(logY ? Math.log10(b) : b);
      pw.push(pop[i] ?? 0);
    }
    return { idx, px, py, pw };
  });
  const both = $derived.by(() => {
    let n = 0;
    for (let i = 0; i < x.length; i++) if (x[i] !== null && y[i] !== null) n++;
    return n;
  });
  const stats = $derived.by(() => {
    const { px, py, pw } = pts;
    if (px.length < 3) return null;
    return { n: px.length, fit: pearson(px, py), rho: spearman(px, py), rw: pearson(px, py, pw).r };
  });

  const M = { l: 50, r: 12, t: 22, b: 30 };
  function domain(v: number[], log: boolean) {
    let lo = Infinity, hi = -Infinity;
    for (const t of v) {
      if (t < lo) lo = t;
      if (t > hi) hi = t;
    }
    if (!(hi > lo)) { lo -= 1; hi += 1; }
    const pad = (hi - lo) * 0.03;
    lo -= pad;
    hi += pad;
    if (!log && lo < 0 && Math.min(...v) >= 0) lo = 0; // non-negative metrics start at 0 at most
    return { lo, hi };
  }
  const dx = $derived(pts.px.length ? domain(pts.px, logX) : { lo: 0, hi: 1 });
  const dy = $derived(pts.py.length ? domain(pts.py, logY) : { lo: 0, hi: 1 });
  const sx = (t: number) => M.l + ((t - dx.lo) / (dx.hi - dx.lo)) * (w - M.l - M.r);
  const sy = (t: number) => h - M.b - ((t - dy.lo) / (dy.hi - dy.lo)) * (h - M.t - M.b);
  const maxPop = $derived(Math.max(1, ...pts.pw));
  const radius = (k: number) => (sizeByPop ? 1.6 + 11 * Math.sqrt(pts.pw[k] / maxPop) : w < 500 ? 2.2 : 2.6);
  let screen: Float32Array = new Float32Array(0);

  function ticksFor(d: { lo: number; hi: number }, log: boolean, target: number) {
    if (!log) return niceTicks(d.lo, d.hi, target).map((t) => ({ v: t, label: t }));
    return logTicks(10 ** d.lo, 10 ** d.hi, target).map((t) => ({ v: Math.log10(t), label: t }));
  }

  function draw() {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const g = canvas.getContext('2d')!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    const grid = token('--plot-grid');
    const axis = token('--plot-axis');
    const muted = token('--muted');
    const text = token('--text');
    const surface = token('--panel');
    const mono = getComputedStyle(document.documentElement).getPropertyValue('--font-mono');
    const cols = regionColours(isDark);

    // grid and ticks
    g.font = `10px ${mono}`;
    g.lineWidth = 1;
    const xt = ticksFor(dx, logX, Math.max(3, Math.round((w - M.l - M.r) / 90)));
    const yt = ticksFor(dy, logY, Math.max(3, Math.round((h - M.t - M.b) / 50)));
    g.strokeStyle = grid;
    g.fillStyle = muted;
    g.textAlign = 'center';
    g.textBaseline = 'top';
    for (const t of xt) {
      const X = Math.round(sx(t.v)) + 0.5;
      g.beginPath(); g.moveTo(X, M.t); g.lineTo(X, h - M.b); g.stroke();
      g.fillText(fmtTick(t.label, xMeta), X, h - M.b + 5);
    }
    g.textAlign = 'right';
    g.textBaseline = 'middle';
    for (const t of yt) {
      const Y = Math.round(sy(t.v)) + 0.5;
      g.beginPath(); g.moveTo(M.l, Y); g.lineTo(w - M.r, Y); g.stroke();
      g.fillText(fmtTick(t.label, yMeta), M.l - 6, Y);
    }
    g.strokeStyle = axis;
    g.beginPath(); g.moveTo(M.l, h - M.b + 0.5); g.lineTo(w - M.r, h - M.b + 0.5); g.stroke();
    g.beginPath(); g.moveTo(M.l - 0.5, M.t); g.lineTo(M.l - 0.5, h - M.b); g.stroke();
    // zero lines for diverging metrics
    g.strokeStyle = muted;
    if (!logX && dx.lo < 0 && dx.hi > 0) { const X = Math.round(sx(0)) + 0.5; g.beginPath(); g.moveTo(X, M.t); g.lineTo(X, h - M.b); g.stroke(); }
    if (!logY && dy.lo < 0 && dy.hi > 0) { const Y = Math.round(sy(0)) + 0.5; g.beginPath(); g.moveTo(M.l, Y); g.lineTo(w - M.r, Y); g.stroke(); }

    // axis titles
    g.fillStyle = text;
    g.font = `500 11px ${getComputedStyle(document.documentElement).getPropertyValue('--font-sans')}`;
    g.textAlign = 'left';
    g.textBaseline = 'alphabetic';
    g.fillText(`↑ ${ml(yMeta)}${yMeta.unit ? ` (${yMeta.unit})` : ''}${logY ? ', log' : ''}`, 4, 12, w - 8);
    g.textAlign = 'right';
    g.fillText(`${ml(xMeta)}${xMeta.unit ? ` (${xMeta.unit})` : ''}${logX ? ', log' : ''} →`, w - M.r, h - 2, w - M.l);

    // points, largest first so small ones stay visible
    const { idx, px, py } = pts;
    const order = Array.from(idx.keys());
    if (sizeByPop) order.sort((a, b) => pts.pw[b] - pts.pw[a]);
    screen = new Float32Array(idx.length * 3);
    g.lineWidth = 0.6;
    g.strokeStyle = surface;
    for (const k of order) {
      const X = sx(px[k]);
      const Y = sy(py[k]);
      const r = radius(k);
      screen[3 * k] = X;
      screen[3 * k + 1] = Y;
      screen[3 * k + 2] = r;
      const reg = region[idx[k]];
      g.globalAlpha = sizeByPop ? 0.62 : 0.78;
      g.fillStyle = reg >= 0 ? cols[reg] : muted;
      g.beginPath();
      g.arc(X, Y, r, 0, Math.PI * 2);
      g.fill();
      g.globalAlpha = 1;
      if (r > 2.5) g.stroke();
    }

    // least-squares line over the x range
    if (stats && Number.isFinite(stats.fit.slope)) {
      const x0 = Math.min(...px);
      const x1 = Math.max(...px);
      g.save();
      g.beginPath();
      g.rect(M.l, M.t, w - M.l - M.r, h - M.t - M.b);
      g.clip();
      g.strokeStyle = surface;
      g.lineWidth = 3.5;
      g.beginPath();
      g.moveTo(sx(x0), sy(stats.fit.intercept + stats.fit.slope * x0));
      g.lineTo(sx(x1), sy(stats.fit.intercept + stats.fit.slope * x1));
      g.stroke();
      g.strokeStyle = text;
      g.lineWidth = 1.5;
      g.stroke();
      g.restore();
    }

    // highlighted municipality (hover from any view, or selection)
    for (const i of [sel, hover]) {
      if (i === null) continue;
      const k = idx.indexOf(i);
      if (k < 0) continue;
      const X = screen[3 * k];
      const Y = screen[3 * k + 1];
      const r = Math.max(4.5, screen[3 * k + 2] + 2);
      g.lineWidth = 3.5;
      g.strokeStyle = surface;
      g.beginPath(); g.arc(X, Y, r, 0, Math.PI * 2); g.stroke();
      g.lineWidth = 1.8;
      g.strokeStyle = token('--sel-line');
      g.stroke();
    }
  }

  $effect(() => {
    // redraw on any input change
    void [pts, w, h, sizeByPop, hover, sel, isDark, stats, xMeta, yMeta];
    draw();
  });

  function nearest(e: PointerEvent): number | null {
    const r = canvas.getBoundingClientRect();
    const X = e.clientX - r.left;
    const Y = e.clientY - r.top;
    let best = -1;
    let bd = Infinity;
    for (let k = 0; k < pts.idx.length; k++) {
      const d = Math.hypot(screen[3 * k] - X, screen[3 * k + 1] - Y) - screen[3 * k + 2];
      if (d < bd) { bd = d; best = k; }
    }
    return best >= 0 && bd < (e.pointerType === 'touch' ? 14 : 8) ? best : null;
  }
  function move(e: PointerEvent) {
    const k = nearest(e);
    if (k === null) {
      tip = null;
      onhover(null);
      return;
    }
    tip = { i: pts.idx[k], left: screen[3 * k], top: screen[3 * k + 1] };
    onhover(pts.idx[k]);
  }
  function leave() {
    tip = null;
    onhover(null);
  }
  function click(e: PointerEvent) {
    const k = nearest(e);
    onselect(k === null ? null : pts.idx[k]);
    if (k !== null) tip = { i: pts.idx[k], left: screen[3 * k], top: screen[3 * k + 1] };
  }

  const regionCount = $derived.by(() => {
    const c = [0, 0, 0, 0];
    for (const i of pts.idx) if (region[i] >= 0) c[region[i]]++;
    return c;
  });
  const cols = $derived(regionColours(isDark));
  const focus = $derived(sel ?? hover);
  const fmt = (v: number | null, m: MetricMeta) => (v === null ? 'no data' : fmtValue(v, m));
</script>

<div class="scatter">
  <div class="plotcol">
    <div class="bar">
      <span class="caps">A × B · {tr('sc.each', { one: unitOne })}</span>
      <span class="opts">
        <label><input type="checkbox" bind:checked={sizeByPop} /> {tr('sc.sizePop')}</label>
        <label><input type="checkbox" bind:checked={logX} /> log x</label>
        <label><input type="checkbox" bind:checked={logY} /> log y</label>
      </span>
    </div>
    <div class="plot" bind:clientWidth={w} bind:clientHeight={h}>
      <canvas bind:this={canvas} style="width:{w}px;height:{h}px" onpointermove={move} onpointerleave={leave} onpointerdown={click}
        aria-label={tr('sc.aria', { y: ml(yMeta), x: ml(xMeta) })}></canvas>
      {#if tip}
        <div class="tip" style="left:{tip.left}px; top:{tip.top}px" class:flip={tip.left > w * 0.6}>
          <strong>{names[tip.i]}</strong>{#if !names[tip.i].includes('(')}&nbsp;<span class="muted">{cantons[tip.i]}</span>{/if}
          <div class="num"><span class="k">A</span> {fmt(x[tip.i], xMeta)}</div>
          <div class="num"><span class="k">B</span> {fmt(y[tip.i], yMeta)}</div>
        </div>
      {/if}
    </div>
    <div class="regions" aria-label={tr('p.lang')}>
      {#each regionNames as name, k}
        <span><i style="background:{cols[k]}"></i>{name} <span class="num muted">{fmtNumber(regionCount[k], 0)}</span></span>
      {/each}
      <span class="muted">— {tr('sc.ols')}</span>
    </div>
  </div>

  <div class="stats">
    <div class="caps">{tr('sc.assoc')}</div>
    {#if stats}
      <table>
        <tbody>
          <tr><th>n</th><td class="num">{fmtNumber(stats.n, 0)}</td></tr>
          <tr><th>Pearson r</th><td class="num strong">{fmtR(stats.fit.r)}</td></tr>
          <tr><th>Spearman <i class="gr">ρ</i></th><td class="num strong">{fmtR(stats.rho)}</td></tr>
          <tr><th>{tr('sc.rw')}</th><td class="num">{fmtR(stats.rw)}</td></tr>
          <tr><th>{tr('sc.slope')}</th><td class="num">{Number.isFinite(stats.fit.slope) ? fmtNumber(stats.fit.slope, Math.abs(stats.fit.slope) < 0.01 ? 5 : Math.abs(stats.fit.slope) < 1 ? 3 : 2) : '–'}</td></tr>
        </tbody>
      </table>
      <p class="foot">
        {logX || logY ? `${tr('sc.on', { what: [logX ? 'log₁₀ A' : '', logY ? 'log₁₀ B' : ''].filter(Boolean).join(tr('sc.and')) })} ` : ''}{tr('sc.weights')}
        {both - stats.n > 0 ? tr('sc.nonpos', { n: fmtNumber(both - stats.n, 0) }) : ''}
        {tr('sc.across', { units: unitWord })}
      </p>
    {:else}
      <p class="muted">{tr('sc.few', { units: unitWord })}</p>
    {/if}
    <div class="sel">
      {#if focus !== null}
        <div class="caps">{sel !== null ? tr('st.selected') : tr('sc.hover')}</div>
        <div class="sname"><strong>{names[focus]}</strong>{#if !names[focus].includes('(')}&nbsp;<span class="muted">{cantons[focus]}</span>{/if}</div>
        <div class="num"><span class="k">A</span> {fmt(x[focus], xMeta)} <span class="muted">{fmtPeriod(xPeriod)}</span></div>
        <div class="num"><span class="k">B</span> {fmt(y[focus], yMeta)} <span class="muted">{fmtPeriod(yPeriod)}</span></div>
      {:else}
        <p class="foot">{tr('sc.hint')}</p>
      {/if}
    </div>
  </div>
</div>

<style>
  .scatter { display: grid; grid-template-columns: minmax(0, 1fr) 240px; gap: 0 18px; height: 100%; min-height: 0; }
  .plotcol { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
  .bar { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px; }
  .opts { display: flex; gap: 12px; font-size: 0.78rem; color: var(--text); }
  .opts label { display: inline-flex; align-items: center; gap: 4px; cursor: pointer; white-space: nowrap; }
  .opts input { accent-color: var(--ink); margin: 0; }
  .plot { position: relative; flex: 1; min-height: 220px; }
  canvas { position: absolute; inset: 0; touch-action: pan-y; cursor: crosshair; }
  .tip {
    position: absolute; transform: translate(12px, -50%); pointer-events: none; background: var(--panel); border: 1px solid var(--ink);
    padding: 6px 9px; font-size: 0.8rem; white-space: nowrap; z-index: 2;
  }
  .tip.flip { transform: translate(calc(-100% - 12px), -50%); }
  .k { display: inline-block; width: 1.3em; color: var(--muted); font-weight: 500; }
  .regions { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 0.76rem; margin-top: 4px; }
  .regions i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
  .muted { color: var(--muted); }
  .stats { border-left: 1px solid var(--rule); padding-left: 16px; min-width: 0; overflow-y: auto; }
  table { width: 100%; border-collapse: collapse; margin-top: 4px; }
  th { text-align: left; font-weight: 400; color: var(--muted); padding: 4px 0; font-size: 0.8rem; }
  td { text-align: right; padding: 4px 0; font-size: 0.9rem; }
  tr + tr { border-top: 1px solid var(--border); }
  .gr { font-family: Georgia, 'Times New Roman', serif; font-size: 1.05em; }
  .strong { font-weight: 700; font-size: 1.15rem; }
  .foot { margin: 6px 0 0; }
  .sel { margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--rule); font-size: 0.82rem; }
  .sname { margin: 2px 0; }
  @media (max-width: 899px) {
    .scatter { grid-template-columns: 1fr; gap: 10px; height: auto; }
    .plot { flex: none; height: 300px; }
    .stats { border-left: 0; padding-left: 0; border-top: 1px solid var(--rule); padding-top: 8px; }
    .opts { gap: 10px; font-size: 0.74rem; }
  }
</style>
