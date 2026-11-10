// Embedding: the compact, chrome-less view (#…&embed=1) and the iframe code for the current view.
import { serializeHash } from './hash';
import { app } from './state.svelte';

/** Absolute URL of the current view, in the embed form or the full form. */
export function viewUrl(embed: boolean): string {
  const u = new URL(location.href);
  u.hash = '';
  u.search = '';
  const snap = { ...app.snapshot(), embed, tab: null };
  return u.href + serializeHash(snap);
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** iframe markup for the current view. */
export function embedCode(title: string, height: number): string {
  return (
    `<iframe src="${esc(viewUrl(true))}" title="${esc(title)}" width="100%" height="${Math.round(height)}" ` +
    `style="border:0;max-width:100%" loading="lazy" allowfullscreen></iframe>`
  );
}
