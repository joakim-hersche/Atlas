<script lang="ts">
  // Percentile bar: where the value sits among all units with data (0 = lowest, 100 = highest).
  // Tied values: a light band shows the whole tie group, the mark sits at the rank's position.
  interface Props {
    pct: number;
    /** span of a tie group (omit when not tied) */
    lo?: number;
    hi?: number;
    label?: string;
  }
  let { pct, lo, hi, label }: Props = $props();
  const c = (v: number) => Math.max(0, Math.min(100, v));
  const x = $derived(c(pct));
  const band = $derived(lo !== undefined && hi !== undefined && hi - lo >= 0.5 ? { l: c(lo), w: c(hi) - c(lo) } : null);
</script>

<span class="pb" role="img" aria-label={label ?? `Percentile ${Math.round(x)}`} title={label ?? `Percentile ${Math.round(x)}`}>
  <span class="track"></span>{#if band}<span class="band" style="left:{band.l}%; width:{band.w}%"></span>{/if}<span class="mid"></span><span class="mark" style="left:{x}%"></span>
</span>

<style>
  .pb { position: relative; display: inline-block; width: 100%; min-width: 48px; height: 12px; vertical-align: middle; }
  .track { position: absolute; left: 0; right: 0; top: 5px; height: 2px; background: var(--border); }
  .band { position: absolute; top: 4px; height: 4px; background: var(--accent-soft); border: 1px solid var(--accent); border-width: 0 1px; opacity: 0.9; }
  .mid { position: absolute; left: 50%; top: 2px; width: 1px; height: 8px; background: var(--faint); }
  .mark { position: absolute; top: 0; width: 3px; height: 12px; margin-left: -1.5px; background: var(--accent); }
</style>
