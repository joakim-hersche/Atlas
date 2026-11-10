<script lang="ts">
  // Time-series sparkline of one unit. The metric's series file loads when the row scrolls into view;
  // no file (or no values for this unit) means no sparkline, silently.
  import { fmtNumber } from '../lib/classify';
  import { loadSeries, type MetricMeta } from '../lib/data';

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
        const y = Number(p.slice(0, 4));
        if (v !== null && v !== undefined && Number.isFinite(y)) out.push({ year: y + (p[4] === '-' ? (Number(p.slice(5, 7)) || 0) / 13 : 0), v, p });
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
    const pad = 2;
    const sx = (y: number) => pad + ((y - x0) / (x1 - x0 || 1)) * (width - 2 * pad);
    const sy = (v: number) => (hi > lo ? pad + (1 - (v - lo) / (hi - lo)) * (height - 2 * pad) : height / 2);
    const d = pts.map((q, k) => `${k ? 'L' : 'M'}${sx(q.year).toFixed(1)} ${sy(q.v).toFixed(1)}`).join('');
    const last = pts[pts.length - 1];
    return { d, cx: sx(last.year), cy: sy(last.v) };
  });
  const title = $derived(pts ? `${pts[0].p}: ${fmtNumber(pts[0].v, meta.decimals)} → ${pts[pts.length - 1].p}: ${fmtNumber(pts[pts.length - 1].v, meta.decimals)} (${pts.length} periods)` : '');
</script>

{#if has}
  <span class="spark" bind:this={el} style="width:{width}px;height:{height}px">
    {#if path}
      <svg {width} {height} viewBox="0 0 {width} {height}" role="img" aria-label={title}><title>{title}</title>
        <path d={path.d} /><circle cx={path.cx} cy={path.cy} r="2" /></svg>
    {/if}
  </span>
{/if}

<style>
  .spark { display: inline-block; vertical-align: middle; }
  svg { display: block; overflow: visible; }
  path { fill: none; stroke: var(--ink); stroke-width: 1.2; stroke-linejoin: round; }
  circle { fill: var(--ink); }
</style>
