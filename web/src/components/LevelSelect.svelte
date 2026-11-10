<script lang="ts">
  // Spatial level picker (brief 4.3). Municipality types have no geometry: listed, disabled, with
  // a pointer to the municipality-type filter.
  import { LEVELS } from '../lib/data';

  interface Props {
    value: string;
    onchange: (level: string) => void;
  }
  let { value, onchange }: Props = $props();
</script>

<label class="lvl">
  <span class="vh">Spatial level</span>
  <select {value} onchange={(e) => onchange(e.currentTarget.value)} title="Spatial level">
    {#each LEVELS as l}<option value={l.id}>{l.label}</option>{/each}
    <option value="gemeindetyp" disabled>Municipality types (no map)</option>
  </select>
</label>

<style>
  .lvl { display: inline-flex; min-width: 0; }
  .vh { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  select {
    min-width: 0; max-width: 100%; padding: 3px 24px 3px 7px; border: 1px solid var(--ink); border-radius: 0; background: var(--panel);
    font-size: 0.8rem; font-weight: 600; cursor: pointer; -webkit-appearance: none; appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%23000' stroke-width='1.4'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 6px center; background-size: 11px;
  }
  @media (max-width: 899px) {
    select { font-size: 16px; padding: 1px 22px 1px 6px; font-weight: 500; }
  }
</style>
