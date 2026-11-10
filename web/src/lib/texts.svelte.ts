// Reactive access to web/texts.json (lib/texts.ts): loaded on first use in German or French; until it arrives,
// and for any text it does not cover, the English text is shown.
import { getOptionalJSON } from './data';
import { app } from './state.svelte';
import { translate, type TextsFile } from './texts';

let file = $state.raw<TextsFile | null>(null);
let pending: Promise<unknown> | null = null;

/** A pipeline text in the UI language (B: R5, E1, C4). */
export function tx(text: string | null | undefined): string {
  if (!text) return text ?? '';
  const lang = app.lang;
  if (lang === 'en') return text;
  if (!file && !pending) pending = getOptionalJSON<TextsFile>('web/texts.json').then((f) => (file = f)).catch(() => null);
  return translate(file, text, lang);
}

/** A source's publisher, translated, without the parenthesised detail ("Computed by ATLAS (pipeline/reach) from …" → "Berechnet von ATLAS"). */
export function pubName(full: string | null | undefined): string {
  return full ? tx(full).split(' (')[0] : '';
}
