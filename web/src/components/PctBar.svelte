<script lang="ts">
  // Percentile bar: where the value sits among all units with data (0 = lowest, 100 = highest).
  interface Props {
    pct: number;
    label?: string;
  }
  let { pct, label }: Props = $props();
  const x = $derived(Math.max(0, Math.min(100, pct)));
</script>

<span class="pb" role="img" aria-label={label ?? `Percentile ${Math.round(x)}`} title={label ?? `Percentile ${Math.round(x)}`}>
  <span class="track"></span><span class="mid"></span><span class="mark" style="left:{x}%"></span>
</span>

<style>
  .pb { position: relative; display: inline-block; width: 100%; min-width: 48px; height: 12px; vertical-align: middle; }
  .track { position: absolute; left: 0; right: 0; top: 5px; height: 2px; background: var(--border); }
  .mid { position: absolute; left: 50%; top: 2px; width: 1px; height: 8px; background: var(--faint); }
  .mark { position: absolute; top: 0; width: 3px; height: 12px; margin-left: -1.5px; background: var(--accent); }
</style>
