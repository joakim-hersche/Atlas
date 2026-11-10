<script lang="ts">
  // U3: share the current view. Phones and tablets get the system share sheet (navigator.share); elsewhere, or
  // when sharing is not offered, the link is copied. The link is built from the state itself, so it is complete
  // even while the debounced hash write is still pending.
  import { t } from '../lib/i18n.svelte';
  import { copyText } from '../lib/export';
  import { serializeHash } from '../lib/hash';
  import { app } from '../lib/state.svelte';

  interface Props {
    /** 'icon': a square icon button (phone header); 'text': an outlined button with a label */
    variant?: 'icon' | 'text';
  }
  let { variant = 'text' }: Props = $props();
  let msg = $state<string | null>(null);
  let timer: ReturnType<typeof setTimeout> | undefined;

  async function share() {
    const u = new URL(location.href);
    u.hash = '';
    const url = u.href.replace(/#$/, '') + serializeHash({ ...app.snapshot(), embed: false });
    const nav = navigator as Navigator & { share?: (d: { url: string; title?: string }) => Promise<void> };
    const touch = window.matchMedia('(pointer: coarse)').matches;
    if (touch && typeof nav.share === 'function') {
      try {
        await nav.share({ url, title: document.title });
        return;
      } catch (e) {
        if ((e as DOMException)?.name === 'AbortError') return;
        // not allowed here: fall back to copying
      }
    }
    const ok = await copyText(url);
    msg = ok ? t('ux.copied') : t('ux.copyFail');
    clearTimeout(timer);
    timer = setTimeout(() => (msg = null), 2200);
  }
</script>

<span class="share">
  <button type="button" class="sb {variant}" title={t('ux.shareT')} aria-label={variant === 'icon' ? t('ux.share') : undefined} onclick={share}>
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M8 10.5V1.8M4.8 4.8 8 1.6l3.2 3.2M3 7.5v6.5h10V7.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" /></svg>
    {#if variant === 'text'}<span>{t('ux.share')}</span>{/if}
  </button>
  {#if msg}<span class="msg" role="status">{msg}</span>{/if}
</span>

<style>
  .share { position: relative; display: inline-flex; }
  .sb {
    display: inline-flex; align-items: center; justify-content: center; gap: var(--sp-2); height: var(--ctl-h); padding: 0 var(--sp-3);
    border: 1px solid var(--ink); background: var(--panel); color: var(--text); cursor: pointer; font-size: var(--fs-body); font-weight: 500;
  }
  .sb:hover { background: var(--surface-2); }
  .sb.icon { width: var(--ctl-h); padding: 0; }
  .msg {
    position: absolute; top: calc(100% + 6px); right: 0; z-index: 80; white-space: nowrap; background: var(--ink); color: var(--ink-text);
    padding: var(--sp-1) var(--sp-2); font-size: var(--fs-meta); line-height: var(--lh-meta);
  }
</style>
