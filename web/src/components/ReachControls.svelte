<script lang="ts">
  // Reach controls: hub picker, mode (off / public transport / car), time slider and Play.
  import { t as tr } from '../lib/i18n.svelte';
  import type { Snippet } from 'svelte';
  import type { Hub } from '../lib/data';
  import { T_MAX, type ReachMode } from '../lib/hash';

  interface Props {
    hubs: Hub[];
    hub: string;
    mode: ReachMode;
    t: number;
    playing: boolean;
    /** false when the car network is not in this build */
    carAvailable: boolean;
    onhub: (slug: string) => void;
    onmode: (m: ReachMode) => void;
    ont: (t: number) => void;
    onplay: () => void;
    children?: Snippet;
  }
  let { hubs, hub, mode, t, playing, carAvailable, onhub, onmode, ont, onplay, children }: Props = $props();
</script>

<div class="reach">
  <div class="row">
    <label class="caps hl" for="hub-select">{tr('rc.from')}</label>
    <select id="hub-select" class="hub" value={hub} onchange={(e) => onhub(e.currentTarget.value)}>
      {#each hubs as h}<option value={h.slug}>{h.name}</option>{/each}
    </select>
    <div class="seg" role="radiogroup" aria-label={tr('rc.mode')}>
      <button type="button" role="radio" aria-checked={mode === 'off'} onclick={() => onmode('off')}>{tr('rc.off')}</button>
      <button type="button" role="radio" aria-checked={mode === 'pt'} title={tr('rc.pt')} onclick={() => onmode('pt')}>
        <span class="long">{tr('rc.pt')}</span><span class="short">{tr('common.pt')}</span>
      </button>
      <button type="button" role="radio" aria-checked={mode === 'car'} disabled={!carAvailable}
        title={carAvailable ? tr('common.car') : tr('rc.noCar')} onclick={() => onmode('car')}>{tr('common.car')}</button>
    </div>
  </div>
  {#if mode !== 'off'}
    <div class="time">
      <button type="button" class="play" onclick={onplay} aria-label={playing ? tr('rc.pause') : tr('rc.play')}>
        {#if playing}
          <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" /><rect x="9.5" y="2" width="3.5" height="12" /></svg>
        {:else}
          <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M4 2v12l10-6z" /></svg>
        {/if}
      </button>
      <input type="range" min="0" max={T_MAX} step="1" value={t} aria-label={tr('rc.minutes')}
        oninput={(e) => ont(+e.currentTarget.value)} />
      <output class="tval num">{Math.round(t)} min</output>
    </div>
    {#if children}<div class="note">{@render children()}</div>{/if}
  {/if}
</div>

<style>
  .row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; }
  .hl { flex-basis: 100%; }
  .hub {
    flex: 1; min-width: 0; padding: 4px 26px 4px 8px; border: 1px solid var(--ink); border-radius: 0; background: var(--panel);
    font-size: 0.85rem; font-weight: 600; -webkit-appearance: none; appearance: none; cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%23000' stroke-width='1.4'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 7px center; background-size: 12px;
  }
  .seg { flex: none; }
  .short { display: none; }
  .time { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
  .time input { flex: 1; accent-color: var(--ink); min-width: 0; height: 24px; }
  .play {
    width: 28px; height: 28px; border-radius: 0; border: 1px solid var(--ink); background: var(--ink); color: var(--ink-text);
    display: grid; place-items: center; cursor: pointer; flex: none;
  }
  .play svg { fill: currentColor; }
  .tval { min-width: 4.2em; text-align: right; }
  .note { margin: 6px 0 0; font-size: 0.8rem; }
  @media (max-width: 899px) {
    .hl { flex-basis: auto; }
    .hub { font-size: 16px; padding: 2px 24px 2px 6px; font-weight: 500; }
    .long { display: none; }
    .short { display: inline; }
    .seg button { padding: 4px 8px; }
  }
</style>
