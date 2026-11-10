<script lang="ts">
  // Dual-range slider on a log scale (population spans 4 orders of magnitude) with typed inputs.
  // lo/hi are null when that side is unbounded.
  import { fmtNumber } from '../lib/classify';

  interface Props {
    label: string;
    min: number;
    max: number;
    lo: number | null;
    hi: number | null;
    count: number;
    total: number;
  }
  let { label, min, max, lo = $bindable(), hi = $bindable(), count, total }: Props = $props();

  const STEPS = 1000;
  const lmin = $derived(Math.log10(Math.max(1, min)));
  const lmax = $derived(Math.log10(Math.max(2, max)));

  function toPos(v: number) {
    return Math.round(((Math.log10(Math.max(1, v)) - lmin) / (lmax - lmin)) * STEPS);
  }
  function nice(v: number) {
    if (v < 100) return Math.round(v);
    const p = 10 ** (Math.floor(Math.log10(v)) - 1);
    return Math.round(v / p) * p;
  }
  function fromPos(p: number) {
    if (p <= 0) return min;
    if (p >= STEPS) return max;
    return nice(10 ** (lmin + (p / STEPS) * (lmax - lmin)));
  }

  const loPos = $derived(lo === null ? 0 : toPos(lo));
  const hiPos = $derived(hi === null ? STEPS : toPos(hi));

  function setLoPos(p: number) {
    p = Math.min(p, hiPos);
    lo = p <= 0 ? null : fromPos(p);
  }
  function setHiPos(p: number) {
    p = Math.max(p, loPos);
    hi = p >= STEPS ? null : fromPos(p);
  }
  function typed(which: 'lo' | 'hi', raw: string) {
    const v = Number(raw.replace(/[’'\s,]/g, ''));
    if (raw.trim() === '' || !Number.isFinite(v)) {
      if (which === 'lo') lo = null;
      else hi = null;
      return;
    }
    if (which === 'lo') lo = v <= min ? null : Math.min(v, hi ?? max);
    else hi = v >= max ? null : Math.max(v, lo ?? min);
  }
  const active = $derived(lo !== null || hi !== null);
</script>

<div class="rf">
  <div class="head">
    <span class="label">{label}</span>
    <span class="count" aria-live="polite"><strong>{fmtNumber(count, 0)}</strong> of {fmtNumber(total, 0)} match</span>
  </div>
  <div class="slider" style="--a:{(loPos / STEPS) * 100}%; --b:{(hiPos / STEPS) * 100}%">
    <div class="track"></div>
    <input type="range" min="0" max={STEPS} value={loPos} aria-label="{label} minimum"
      oninput={(e) => setLoPos(+e.currentTarget.value)} />
    <input type="range" min="0" max={STEPS} value={hiPos} aria-label="{label} maximum"
      oninput={(e) => setHiPos(+e.currentTarget.value)} />
  </div>
  <div class="inputs">
    <label>Min
      <input type="text" inputmode="numeric" placeholder={fmtNumber(min, 0)} value={lo === null ? '' : String(lo)}
        onchange={(e) => typed('lo', e.currentTarget.value)} />
    </label>
    <label>Max
      <input type="text" inputmode="numeric" placeholder={fmtNumber(max, 0)} value={hi === null ? '' : String(hi)}
        onchange={(e) => typed('hi', e.currentTarget.value)} />
    </label>
    <button type="button" class="reset" disabled={!active} onclick={() => { lo = null; hi = null; }}>Clear</button>
  </div>
</div>

<style>
  .head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .label { font-size: 0.72rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted); }
  .count { color: var(--muted); font-size: 0.8rem; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  .count strong { color: var(--text); }
  .slider { position: relative; height: 36px; }
  .track {
    position: absolute; left: 11px; right: 11px; top: 16px; height: 3px; border-radius: 0;
    background: linear-gradient(to right, var(--border) var(--a), var(--accent) var(--a), var(--accent) var(--b), var(--border) var(--b));
  }
  .slider input {
    position: absolute; inset: 0; width: 100%; margin: 0; background: none; pointer-events: none;
    -webkit-appearance: none; appearance: none; height: 36px;
  }
  .slider input::-webkit-slider-runnable-track { background: none; height: 36px; }
  .slider input::-moz-range-track { background: none; }
  .slider input::-webkit-slider-thumb {
    -webkit-appearance: none; pointer-events: auto; width: 18px; height: 18px; margin-top: 9px; border-radius: 50%;
    background: var(--panel); border: 2px solid var(--accent); cursor: grab;
  }
  .slider input::-moz-range-thumb {
    pointer-events: auto; width: 18px; height: 18px; border-radius: 50%;
    background: var(--panel); border: 2px solid var(--accent); cursor: grab;
  }
  .inputs { display: flex; gap: 8px; align-items: end; }
  .inputs label { display: flex; flex-direction: column; font-size: 0.8rem; color: var(--muted); flex: 1; min-width: 0; }
  .inputs input {
    width: 100%; padding: 6px 8px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--panel-2);
    font-size: 16px; font-family: var(--font-mono); font-variant-numeric: tabular-nums;
  }
  .reset {
    padding: 7px 10px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--panel-2); cursor: pointer;
  }
  .reset:disabled { opacity: 0.45; cursor: default; }
</style>
