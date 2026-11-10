<script lang="ts">
  // Small locator map (SVG, no WebGL): Switzerland's cantons and lakes, the place in red. Very small
  // places get a ring so they stay visible.
  import type { FeatureCollection, Geometry } from 'geojson';
  import { collectionPath, geomBox, geomPath, LOC_H, LOC_W } from '../lib/profile';

  interface Props {
    kanton: FeatureCollection;
    lakes: FeatureCollection;
    shapes: Geometry[];
    label: string;
  }
  let { kanton, lakes, shapes, label }: Props = $props();
  const kt = $derived(collectionPath(kanton));
  const lk = $derived(collectionPath(lakes));
  const hl = $derived(shapes.map((g) => geomPath(g, 0.3)).join(''));
  const ring = $derived.by(() => {
    if (shapes.length !== 1) return null;
    const b = geomBox(shapes[0]);
    if (!b) return null;
    const w = b[2] - b[0], h = b[3] - b[1];
    return w < 9 && h < 9 ? { cx: (b[0] + b[2]) / 2, cy: (b[1] + b[3]) / 2 } : null;
  });
</script>

<svg class="loc" viewBox="-2 -2 {LOC_W + 4} {LOC_H + 4}" role="img" aria-label={label}>
  <path class="kt" d={kt} />
  <path class="lk" d={lk} />
  <path class="hl" d={hl} />
  {#if ring}<circle cx={ring.cx} cy={ring.cy} r="7" />{/if}
</svg>

<style>
  .loc { display: block; width: 100%; height: auto; }
  .kt { fill: var(--panel-2); stroke: var(--ink); stroke-width: 0.5; stroke-linejoin: round; }
  .lk { fill: var(--water); stroke: var(--water-line); stroke-width: 0.4; }
  .hl { fill: var(--accent); stroke: var(--accent); stroke-width: 0.4; }
  circle { fill: none; stroke: var(--accent); stroke-width: 1.6; }
</style>
