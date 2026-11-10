// Plain-language glossary (pipeline/i18n/glossary.yaml -> web/glossary.json): short explanations of
// jargon (quantile, P10/P90, z-score, labour market area ...) behind an ⓘ next to the word. Loaded on
// first use; a build without the file shows no ⓘ.
import { getOptionalJSON, type MetricMeta } from './data';
import { app } from './state.svelte';

export interface GlossEntry {
  term_en: string;
  term_de?: string;
  term_fr?: string;
  en: string;
  de?: string;
  fr?: string;
}

let entries = $state.raw<Record<string, GlossEntry> | null>(null);
let p: Promise<unknown> | null = null;
export function loadGlossary(): void {
  p ??= getOptionalJSON<Record<string, GlossEntry>>('web/glossary.json')
    .then((g) => (entries = g ?? {}))
    .catch(() => (entries = {}));
}

/** Term and explanation in the UI language, or null (unknown key, or no glossary in this build). */
export function gloss(key: string): { term: string; text: string } | null {
  const e = entries?.[key];
  if (!e) return null;
  const l = app.lang;
  return {
    term: (l === 'de' ? e.term_de : l === 'fr' ? e.term_fr : null) ?? e.term_en,
    text: (l === 'de' ? e.de : l === 'fr' ? e.fr : null) ?? e.en,
  };
}

/** Glossary key that explains a metric's label, if any. */
export function glossKeyOf(m: MetricMeta | undefined | null): string | null {
  if (!m) return null;
  if (m.id === 'old_age_dependency') return 'old_age_dependency_ratio';
  if (m.id.startsWith('fin_self_financing')) return 'self_financing_ratio';
  if (m.id.startsWith('tax_np_') && m.id.includes('normal')) return 'normal_cases';
  if (m.unit === 'fictitious voters') return 'fictitious_voters';
  return null;
}
