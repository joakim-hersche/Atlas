<script lang="ts">
  import '../lib/i18n-r3';
  // Dual-range slider with typed min/max inputs. Log scale for skewed positive metrics (population
  // spans 4 orders of magnitude), linear otherwise. lo/hi are null when that side is unbounded.
  import { t } from '../lib/i18n.svelte';
  import { fmtNumber } from '../lib/classify';

  interface Props {
    label: string;
    min: number;
    max: number;
    lo: number | null;
    hi: number | null;
    /** live count (omit to hide the count line) */
    count?: number | null;
    total?: number;
    log?: boolean;
    decimals?: number;
    hideLabel?: boolean;
    onchange?: (lo: number | null, hi: number | null) => void;
  }
  let {
    label, min, max, lo = $bindable(), hi = $bindable(), count = null, total = 0, log = true, decimals = 0, hideLabel = false, onchange,
  }: Props = $props();

  const STEPS = 1000;
  const useLog = $derived(log && min > 0 && max > min);
  const fmin = $derived(useLog ? Math.log10(min) : min);
  const fmax = $derived(useLog ? Math.log10(max) : max > min ? max : min + 1);
  const fwd = (v: number) => (useLog ? Math.log10(Math.max(min, v)) : v);
  const back = (x: number) => (useLog ? 10 ** x : x);

  function toPos(v: number) {
    return Math.max(0, Math.min(STEPS, Math.round(((fwd(v) - fmin) / (fmax - fmin)) * STEPS)));
  }
  // round to about 2 significant digits (log) or to a step of 1/200 of the range (linear)
  function nice(v: number) {
    if (useLog) {
      if (v < 100) return Math.round(v * 10 ** decimals) / 10 ** decimals;
      const p = 10 ** (Math.floor(Math.log10(v)) - 1);
      return Math.round(v / p) * p;
    }
    const raw = (max - min) / 200;
    const p = 10 ** Math.floor(Math.log10(raw || 1));
    const st = Math.max(raw < 2 * p ? p : raw < 5 * p ? 2 * p : 5 * p, 10 ** -decimals);
    return +(Math.round(v / st) * st).toFixed(Math.max(0, decimals));
  }
  function fromPos(p: number) {
    if (p <= 0) return min;
    if (p >= STEPS) return max;
    return nice(back(fmin + (p / STEPS) * (fmax - fmin)));
  }

  const loPos = $derived(lo === null ? 0 : toPos(lo));
  const hiPos = $derived(hi === null ? STEPS : toPos(hi));

  function set(l: number | null, h: number | null) {
    lo = l;
    hi = h;
    onchange?.(l, h);
  }
  function setLoPos(p: number) {
    p = Math.min(p, hiPos);
    set(p <= 0 ? null : fromPos(p), hi);
  }
  function setHiPos(p: number) {
    p = Math.max(p, loPos);
    set(lo, p >= STEPS ? null : fromPos(p));
  }
  function typed(which: 'lo' | 'hi', raw: string) {
    const v = Number(raw.replace(/[’'\s]/g, '').replace('−', '-').replace(',', '.'));
    if (raw.trim() === '' || !Number.isFinite(v)) {
      if (which === 'lo') set(null, hi);
      else set(lo, null);
      return;
    }
    // F12: a typed bound is kept as typed (500 stays 500 even when the highest value is 195); the slider shows it
    // at its end. Only the slider's own ends mean "no bound".
    if (which === 'lo') set(hi !== null ? Math.min(v, hi) : v, hi);
    else set(lo, lo !== null ? Math.max(v, lo) : v);
  }
  const active = $derived(lo !== null || hi !== null);
  const ph = (x: number) => fmtNumber(x, Math.abs(x) >= 100 ? 0 : decimals);
</script>

<div class="rf">
  {#if !hideLabel || count !== null}
    <div class="head">
      {#if !hideLabel}<span class="label">{label}</span>{/if}
      {#if count !== null}<span class="count" aria-live="polite"><strong>{fmtNumber(count, 0)}</strong> {t('r3.ofMatch', { n: fmtNumber(total, 0) })}</span>{/if}
    </div>
  {/if}
  <div class="slider" style="--a:{(loPos / STEPS) * 100}%; --b:{(hiPos / STEPS) * 100}%">
    <div class="track"></div>
    <input type="range" class="dual" min="0" max={STEPS} value={loPos} aria-label="{label} minimum"
      oninput={(e) => setLoPos(+e.currentTarget.value)} />
    <input type="range" class="dual" min="0" max={STEPS} value={hiPos} aria-label="{label} maximum"
      oninput={(e) => setHiPos(+e.currentTarget.value)} />
  </div>
  <!-- F12: the slider runs over the data range; its ends and scale are labelled -->
  <div class="ends num" title={t('r3.rangeT')}><span>{ph(min)}</span>{#if useLog}<span class="sc">{t('r3.logScale')}</span>{/if}<span>{ph(max)}</span></div>
  <div class="inputs">
    <label>{t('r3.min')}
      <input type="text" inputmode="decimal" placeholder={ph(min)} value={lo === null ? '' : String(lo)}
        onchange={(e) => typed('lo', e.currentTarget.value)} />
    </label>
    <label>{t('r3.max')}
      <input type="text" inputmode="decimal" placeholder={ph(max)} value={hi === null ? '' : String(hi)}
        onchange={(e) => typed('hi', e.currentTarget.value)} />
    </label>
    <button type="button" class="reset" disabled={!active} onclick={() => set(null, null)}>{t('common.clear')}</button>
  </div>
</div>

<style>
  .ends { display: flex; justify-content: space-between; gap: 6px; margin-top: -2px; font-size: var(--fs-cap); color: var(--text-2); }
  .ends .sc { font-style: italic; }
  .head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .label { font-size: var(--fs-cap); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text); }
  .count { color: var(--muted); font-size: var(--fs-small); font-family: var(--font-mono); font-variant-numeric: tabular-nums; margin-left: auto; }
  .count strong { color: var(--text); }
  .slider { position: relative; height: 40px; }
  .track {
    position: absolute; left: 7px; right: 7px; top: 19px; height: 2px; border-radius: 0;
    background: linear-gradient(to right, var(--border) var(--a), var(--ink) var(--a), var(--ink) var(--b), var(--border) var(--b));
  }
  .slider input {
    position: absolute; inset: 0; width: 100%; margin: 0; background: none; pointer-events: none;
    -webkit-appearance: none; appearance: none; height: 40px;
  }
  .slider input::-webkit-slider-runnable-track { background: none; height: 40px; }
  .slider input::-moz-range-track { background: none; }
  .slider input::-webkit-slider-thumb {
    /* D8: the same 14 px black square knob as every slider; a 40 px touch strip */
    -webkit-appearance: none; pointer-events: auto; width: 14px; height: 14px; margin-top: 13px; border-radius: 0;
    background: var(--ink); border: 0; cursor: grab;
  }
  .slider input::-moz-range-thumb {
    pointer-events: auto; width: 14px; height: 14px; border-radius: 0;
    background: var(--ink); border: 0; cursor: grab;
  }
  .inputs { display: flex; gap: 8px; align-items: end; }
  .inputs label { display: flex; flex-direction: column; font-size: var(--fs-meta); color: var(--text); flex: 1; min-width: 0; }
  .inputs input {
    width: 100%; padding: 6px 8px; border: 1px solid var(--ink); background: var(--panel);
    font-size: var(--fs-input); font-family: var(--font-mono); font-variant-numeric: tabular-nums;
  }
  .reset {
    padding: 7px 10px; border: 1px solid var(--ink); background: var(--panel); cursor: pointer; font-weight: 500;
  }
  .reset:disabled { opacity: 0.45; cursor: default; }
</style>
