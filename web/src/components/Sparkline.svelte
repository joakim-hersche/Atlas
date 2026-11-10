<script lang="ts">
  // Time-series sparkline of one unit. The metric's series file loads when the row scrolls into view;
  // no file (or no values for this unit) means no sparkline, silently.
  // Honest baselines: counts and shares start at 0; other metrics use their own range, and the y-range
  // is always printed under the line, so a small change never looks like a cliff without saying so.
  // A break in the series (change of method, metrics.json `series_breaks`) is a small dashed tick between
  // the last point before it and the first one on the new basis, named in the title.
  import { breakNotes, breakTickX, periodX, seriesBreaksOf } from '../lib/breaks';
  import { fmtNumber, fmtTick, rangeText } from '../lib/classify';
  import { loadSeries, type MetricMeta } from '../lib/data';
  import { app } from '../lib/state.svelte';
  import { t } from '../lib/i18n.svelte';
  import '../lib/i18n-mapx';

  interface Props {
    meta: MetricMeta;
    level: string;
    id: string;
    width?: number;
    height?: number;
  }
  let { meta, level, id, width = 84, height = 22 }: Props = $props();
  const SERIES_LEVELS = ['gemeinde', 'bezirk', 'kanton', 'schweiz'];
  const has = $derived(SERIES_LEVELS.includes(level) && meta.n_periods >= 2 && !meta.per_vote && meta.levels.includes(level));

  let el = $state<HTMLElement>();
  let seen = $state(false);
  let pts = $state.raw<{ year: number; v: number; p: string }[] | null>(null);

  $effect(() => {
    if (!has || !el || seen) return;
    const io = new IntersectionObserver((es) => {
      if (es.some((e) => e.isIntersecting)) {
        seen = true;
        io.disconnect();
      }
    }, { rootMargin: '200px' });
    io.observe(el);
    return () => io.disconnect();
  });
  $effect(() => {
    if (!seen) return;
    const m = meta.id, lv = level, u = id;
    let live = true;
    loadSeries(m).then((s) => {
      if (!live || !s) return;
      const row = s.levels[lv]?.[u];
      if (!row) return;
      const out: { year: number; v: number; p: string }[] = [];
      s.periods.forEach((p, k) => {
        const v = row[k];
        const y = periodX(p);
        if (v !== null && v !== undefined && Number.isFinite(y)) out.push({ year: y, v, p });
      });
      pts = out.length >= 2 ? out : null;
    }).catch(() => {});
    return () => (live = false);
  });
  const path = $derived.by(() => {
    if (!pts) return null;
    const x0 = pts[0].year, x1 = pts[pts.length - 1].year;
    let lo = Infinity, hi = -Infinity;
    for (const q of pts) { lo = Math.min(lo, q.v); hi = Math.max(hi, q.v); }
    if (zeroBase && lo > 0) lo = 0;
    const pad = 2;
    const sx = (y: number) => pad + ((y - x0) / (x1 - x0 || 1)) * (width - 2 * pad);
    const sy = (v: number) => (hi > lo ? pad + (1 - (v - lo) / (hi - lo)) * (height - 2 * pad) : height / 2);
    const d = pts.map((q, k) => `${k ? 'L' : 'M'}${sx(q.year).toFixed(1)} ${sy(q.v).toFixed(1)}`).join('');
    const last = pts[pts.length - 1];
    const xs = pts.map((q) => q.year);
    const ticks = breaks.flatMap(([p, note]) => {
      const x = breakTickX(xs, periodX(p));
      return x === null ? [] : [{ p, note, x: sx(x) }];
    });
    return { d, cx: sx(last.year), cy: sy(last.v), lo, hi, base: zeroBase ? sy(0) : null, ticks };
  });
  const breaks = $derived([...breakNotes(seriesBreaksOf(meta), app.lang)]);
  const zeroBase = $derived(meta.aggregation === 'sum' || meta.unit.startsWith('%'));
  const brkText = $derived(path?.ticks.length ? path.ticks.map((k) => t('sp.break', { p: k.p }) + (k.note ? ` (${k.note})` : '')).join('; ') : '');
  const title = $derived(pts ? `${pts[0].p}: ${fmtNumber(pts[0].v, meta.decimals)} → ${pts[pts.length - 1].p}: ${fmtNumber(pts[pts.length - 1].v, meta.decimals)} (${pts.length} periods)${brkText ? `; ${brkText}` : ''}` : '');
</script>

{#if has}
  <span class="spark" bind:this={el} style="width:{width}px;height:{height}px">
    {#if path}
      <svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={title}><title>{title}</title>
        {#if path.base !== null}<line class="zero" x1="0" x2={width} y1={path.base} y2={path.base} />{/if}
        {#each path.ticks as k (k.p)}<line class="brk" x1={k.x} x2={k.x} y1="0" y2={height} />{/each}
        <path d={path.d} /><circle cx={path.cx} cy={path.cy} r="2" /></svg>
      <span class="rng num">{path.hi > path.lo ? rangeText(fmtTick(path.lo, meta), fmtTick(path.hi, meta)) : fmtTick(path.lo, meta)}</span>
    {/if}
  </span>
{/if}

<style>
  .spark { display: inline-flex; flex-direction: column; vertical-align: middle; height: auto !important; }
  .rng { font-size: var(--fs-cap); line-height: 1.1; color: var(--faint); white-space: nowrap; }
  .zero { stroke: var(--border); stroke-width: 1; }
  .brk { stroke: var(--muted, var(--faint)); stroke-width: 1; stroke-dasharray: 2 2; }
  svg { display: block; overflow: visible; }
  path { fill: none; stroke: var(--ink); stroke-width: 1.2; stroke-linejoin: round; }
  circle { fill: var(--ink); }
</style>
