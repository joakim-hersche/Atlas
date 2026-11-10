<script lang="ts">
  // placeholder: built in the next steps
  import type { Base } from '../lib/data';
  import { app } from '../lib/state.svelte';
  interface Props { base: Base; desktop?: boolean }
  let { base, desktop = false }: Props = $props();
</script>

<main class="pg"><p>{app.route} {app.params.id ?? ''} {base.metrics.length} {desktop}</p></main>
