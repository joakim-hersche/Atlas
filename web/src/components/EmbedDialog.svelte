<script lang="ts">
  // "Embed" button and dialog: copyable iframe code for the view as it is now (all of the URL state, in embed mode).
  import { embedCode } from '../lib/embed';
  import { t } from '../lib/i18n.svelte';
  import '../lib/i18n-spatial';

  interface Props {
    /** title of the frame (screen readers), e.g. the shaded metric */
    title: string;
  }
  let { title }: Props = $props();

  let dlg = $state<HTMLDialogElement>();
  let area = $state<HTMLTextAreaElement>();
  let height = $state(520);
  let code = $state('');
  let copied = $state<'' | 'ok' | 'fail'>('');
  let timer: ReturnType<typeof setTimeout> | undefined;

  function open() {
    code = embedCode(t('em.frame', { metric: title }), height);
    copied = '';
    dlg?.showModal();
  }
  // the code follows the height field while the dialog is open
  function setHeight(v: number) {
    height = Math.max(200, Math.min(2000, Math.round(v) || 520));
    code = embedCode(t('em.frame', { metric: title }), height);
  }
  async function copy() {
    clearTimeout(timer);
    try {
      await navigator.clipboard.writeText(code);
      copied = 'ok';
    } catch {
      area?.select();
      copied = 'fail';
    }
    timer = setTimeout(() => (copied = ''), 2500);
  }
  function backdrop(e: MouseEvent) {
    if (e.target === dlg) dlg?.close();
  }
</script>

<button type="button" class="exb" onclick={open} title={t('em.buttonT')}>{t('em.button')}</button>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
<dialog bind:this={dlg} class="emb" aria-labelledby="emb-h" onclick={backdrop}>
  <div class="in">
    <h2 id="emb-h">{t('em.title')}</h2>
    <p class="help">{t('em.help')}</p>
    <label class="code">
      <span class="caps">{t('em.code')}</span>
      <textarea bind:this={area} readonly rows="6" value={code} onfocus={(e) => e.currentTarget.select()} spellcheck="false"></textarea>
    </label>
    <div class="row">
      <label class="h">
        <span class="caps">{t('em.height')}</span>
        <input type="number" min="200" max="2000" step="20" value={height} onchange={(e) => setHeight(e.currentTarget.valueAsNumber)} /> px
      </label>
      <span class="grow"></span>
      <span class="state" role="status">{copied === 'ok' ? t('em.copied') : copied === 'fail' ? t('em.copyFail') : ''}</span>
      <button type="button" class="b primary" onclick={copy}>{t('em.copy')}</button>
      <button type="button" class="b" onclick={() => dlg?.close()}>{t('em.close')}</button>
    </div>
  </div>
</dialog>

<style>
  .exb { border: 1px solid var(--ink); background: var(--panel); padding: 3px 9px; cursor: pointer; font-size: var(--fs-meta); font-weight: 600; color: var(--text); }
  .emb { width: min(520px, calc(100vw - 24px)); padding: 0; border: 1px solid var(--ink); border-top: 3px solid var(--ink); background: var(--panel); color: var(--text); }
  .emb::backdrop { background: rgba(0, 0, 0, 0.35); }
  .in { padding: 14px 16px 16px; }
  h2 { margin: 0 0 6px; font-size: var(--fs-body); }
  .help { margin: 0 0 10px; font-size: var(--fs-small); line-height: 1.4; }
  .code { display: block; }
  textarea { display: block; width: 100%; margin-top: 4px; box-sizing: border-box; font: var(--fs-meta)/1.4 ui-monospace, Menlo, Consolas, monospace; border: 1px solid var(--ink); padding: 6px; resize: vertical; background: var(--panel-2); color: var(--text); }
  .row { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  .h { display: flex; align-items: center; gap: 6px; font-size: var(--fs-small); }
  .h input { width: 64px; padding: 3px 4px; border: 1px solid var(--ink); font: inherit; }
  .grow { flex: 1; }
  .state { font-size: var(--fs-meta); color: var(--muted); }
  .b { border: 1px solid var(--ink); background: var(--panel); padding: 5px 12px; cursor: pointer; font-size: var(--fs-small); font-weight: 600; color: var(--text); }
  .b.primary { background: var(--ink); color: var(--ink-text); }
</style>
