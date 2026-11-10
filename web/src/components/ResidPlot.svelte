<script lang="ts">
  // Residual against predicted value (regression panel, D34): one point per unit of the sample,
  // coloured by language region (municipalities), a zero line, hover and tap to select.
  import { fmtNumber, niceTicks } from '../lib/classify';
  import { regionColours, token } from '../lib/theme';
  import { t as tr } from '../lib/i18n.svelte';

  interface Props {
    /** unit index per point */
    idx: number[];
    fitted: ArrayLike<number>;
    resid: ArrayLike<number>;
    /** language region per unit (0..3, -1 unknown) or null */
    region: Int8Array | null;
    regionNames: string[];
    names: string[];
    cantons: string[];
    /** axis titles */
    xTitle: string;
    yTitle: string;
    decimals: number;
    /** tooltip lines for a unit */
    tipLines: (i: number) => string[];
    hover: number | null;
    sel: number | null;
    onhover: (i: number | null) => void;
    onselect: (i: number | null) => void;
  }
  let { idx, fitted, resid, region, regionNames, names, cantons, xTitle, yTitle, decimals, tipLines, hover, sel, onhover, onselect }: Props = $props();

  let w = $state(500);
  let h = $state(260);
  let canvas: HTMLCanvasElement;
  let tip = $state<{ i: number; left: number; top: number } | null>(null);
  const M = { l: 48, r: 10, t: 20, b: 28 };
  const cols = regionColours();

  function dom(v: ArrayLike<number>, sym: boolean) {
    let lo = Infinity, hi = -Infinity;
    for (let k = 0; k < v.length; k++) {
      if (v[k] < lo) lo = v[k];
      if (v[k] > hi) hi = v[k];
    }
    if (sym) {
      const a = Math.max(Math.abs(lo), Math.abs(hi)) || 1;
      lo = -a;
      hi = a;
    }
    if (!(hi > lo)) { lo -= 1; hi += 1; }
    const pad = (hi - lo) * 0.04;
    return { lo: lo - pad, hi: hi + pad };
  }
  const dx = $derived(dom(fitted, false));
  const dy = $derived(dom(resid, true));
  const sx = (v: number) => M.l + ((v - dx.lo) / (dx.hi - dx.lo)) * (w - M.l - M.r);
  const sy = (v: number) => h - M.b - ((v - dy.lo) / (dy.hi - dy.lo)) * (h - M.t - M.b);
  let screen = new Float32Array(0);
  const fmt = (v: number) => fmtNumber(v, Math.abs(v) >= 100 ? 0 : decimals);

  function draw() {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const g = canvas.getContext('2d')!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    const mono = getComputedStyle(document.documentElement).getPropertyValue('--font-mono');
    const sans = getComputedStyle(document.documentElement).getPropertyValue('--font-sans');
    g.font = `10px ${mono}`;
    g.lineWidth = 1;
    g.strokeStyle = token('--plot-grid');
    g.fillStyle = token('--muted');
    g.textAlign = 'center';
    g.textBaseline = 'top';
    for (const v of niceTicks(dx.lo, dx.hi, Math.max(3, Math.round((w - M.l - M.r) / 90)))) {
      const X = Math.round(sx(v)) + 0.5;
      g.beginPath(); g.moveTo(X, M.t); g.lineTo(X, h - M.b); g.stroke();
      g.fillText(fmt(v), X, h - M.b + 5);
    }
    g.textAlign = 'right';
    g.textBaseline = 'middle';
    for (const v of niceTicks(dy.lo, dy.hi, Math.max(3, Math.round((h - M.t - M.b) / 45)))) {
      const Y = Math.round(sy(v)) + 0.5;
      g.beginPath(); g.moveTo(M.l, Y); g.lineTo(w - M.r, Y); g.stroke();
      g.fillText((v > 0 ? '+' : '') + fmt(v), M.l - 6, Y);
    }
    g.strokeStyle = token('--plot-axis');
    g.beginPath(); g.moveTo(M.l - 0.5, M.t); g.lineTo(M.l - 0.5, h - M.b); g.stroke();
    // zero line: the prediction
    const Y0 = Math.round(sy(0)) + 0.5;
    g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(M.l, Y0); g.lineTo(w - M.r, Y0); g.stroke();
    g.fillStyle = token('--text');
    g.font = `500 11px ${sans}`;
    g.textAlign = 'left';
    g.textBaseline = 'alphabetic';
    g.fillText(`↑ ${yTitle}`, 4, 12, w - 8);
    g.textAlign = 'right';
    g.fillText(`${xTitle} →`, w - M.r, h - 2, w - M.l);

    screen = new Float32Array(idx.length * 2);
    const r = w < 500 ? 2.2 : 2.6;
    const muted = token('--muted');
    for (let k = 0; k < idx.length; k++) {
      const X = sx(fitted[k]);
      const Y = sy(resid[k]);
      screen[2 * k] = X;
      screen[2 * k + 1] = Y;
      const reg = region ? region[idx[k]] : -1;
      g.globalAlpha = 0.75;
      g.fillStyle = reg >= 0 ? cols[reg] : muted;
      g.beginPath();
      g.arc(X, Y, r, 0, Math.PI * 2);
      g.fill();
    }
    g.globalAlpha = 1;
    for (const i of [sel, hover]) {
      if (i === null) continue;
      const k = idx.indexOf(i);
      if (k < 0) continue;
      g.lineWidth = 3.5;
      g.strokeStyle = token('--panel');
      g.beginPath(); g.arc(screen[2 * k], screen[2 * k + 1], 5, 0, Math.PI * 2); g.stroke();
      g.lineWidth = 1.8;
      g.strokeStyle = token('--sel-line');
      g.stroke();
    }
  }
  $effect(() => {
    void [idx, fitted, resid, w, h, hover, sel, xTitle, yTitle, region];
    draw();
  });

  function nearest(e: PointerEvent): number | null {
    const b = canvas.getBoundingClientRect();
    const X = e.clientX - b.left;
    const Y = e.clientY - b.top;
    let best = -1;
    let bd = Infinity;
    for (let k = 0; k < idx.length; k++) {
      const d = Math.hypot(screen[2 * k] - X, screen[2 * k + 1] - Y);
      if (d < bd) { bd = d; best = k; }
    }
    return best >= 0 && bd < (e.pointerType === 'touch' ? 14 : 8) ? best : null;
  }
  function move(e: PointerEvent) {
    const k = nearest(e);
    tip = k === null ? null : { i: idx[k], left: screen[2 * k], top: screen[2 * k + 1] };
    onhover(k === null ? null : idx[k]);
  }
  function click(e: PointerEvent) {
    const k = nearest(e);
    onselect(k === null ? null : idx[k]);
  }
  const counts = $derived.by(() => {
    const c = [0, 0, 0, 0];
    if (region) for (const i of idx) if (region[i] >= 0) c[region[i]]++;
    return c;
  });
</script>

<div class="rp">
  <div class="plot" bind:clientWidth={w} bind:clientHeight={h}>
    <canvas bind:this={canvas} style="width:{w}px;height:{h}px" onpointermove={move} onpointerleave={() => { tip = null; onhover(null); }} onpointerdown={click}
      aria-label={tr('rg.scatter')}></canvas>
    {#if tip}
      <div class="tip" style="left:{tip.left}px; top:{tip.top}px" class:flip={tip.left > w * 0.6}>
        <strong>{names[tip.i]}</strong>{#if cantons[tip.i] && !names[tip.i].includes('(')}&nbsp;<span class="muted">{cantons[tip.i]}</span>{/if}
        {#each tipLines(tip.i) as l}<div class="num">{l}</div>{/each}
      </div>
    {/if}
  </div>
  {#if region}
    <div class="regions">
      {#each regionNames as name, k}
        {#if counts[k]}<span><i style="background:{cols[k]}"></i>{name} <span class="num muted">{fmtNumber(counts[k], 0)}</span></span>{/if}
      {/each}
    </div>
  {/if}
</div>

<style>
  .rp { display: flex; flex-direction: column; flex: none; }
  .plot { position: relative; flex: none; height: 260px; }
  canvas { position: absolute; inset: 0; touch-action: pan-y; cursor: crosshair; }
  .tip {
    position: absolute; transform: translate(12px, -50%); pointer-events: none; background: var(--panel); border: 1px solid var(--ink);
    padding: 6px 9px; font-size: 0.8rem; white-space: nowrap; z-index: 2;
  }
  .tip.flip { transform: translate(calc(-100% - 12px), -50%); }
  .regions { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 0.76rem; margin-top: 4px; }
  .regions i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
  .muted { color: var(--muted); }
</style>
