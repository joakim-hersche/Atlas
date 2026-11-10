// Metric search (U5): query words match the START of words only ("SP" finds the SP party, not "English"),
// and hits are ranked: the label in the UI language first, then the labels in the other languages, then
// keywords (full party names), the theme and the id. Pure functions, tested in metricsearch.test.ts.
import type { MetricMeta } from './data';

type Lang = 'en' | 'de' | 'fr';

/** Lower case, accents removed, punctuation as spaces. */
export function normWords(s: string): string[] {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/ß/g, 'ss')
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

export interface MetricKey {
  m: MetricMeta;
  /** words of the label in each language */
  label: Record<Lang, string[]>;
  /** the label as one normalised string per language (for "starts with the whole query") */
  flat: Record<Lang, string>;
  kw: string[];
  other: string[];
}

export function metricKey(m: MetricMeta): MetricKey {
  const en = normWords(m.label_en);
  const de = normWords(m.label_de || m.label_en);
  const fr = normWords(m.label_fr || m.label_en);
  return {
    m,
    label: { en, de, fr },
    flat: { en: en.join(' '), de: de.join(' '), fr: fr.join(' ') },
    kw: normWords(m.keywords ?? ''),
    other: [...normWords(m.id), ...normWords(m.theme)],
  };
}

/** Score of one query word against a list of words: exact word, else start of a word. */
function wordScore(w: string, words: string[], exact: number, prefix: number): number {
  let s = 0;
  for (const x of words) {
    if (x === w) return exact;
    if (x.startsWith(w)) s = prefix;
  }
  return s;
}

/** 0 = no match (some query word matches nowhere); higher = better. */
export function scoreMetric(k: MetricKey, words: string[], lang: Lang, anyWord = false): number {
  let total = 0;
  let hits = 0;
  const others = (['en', 'de', 'fr'] as Lang[]).filter((l) => l !== lang);
  for (const w of words) {
    const s = Math.max(
      wordScore(w, k.label[lang], 12, 9),
      ...others.map((l) => wordScore(w, k.label[l], 7, 5)),
      wordScore(w, k.kw, 5, 4),
      wordScore(w, k.other, 3, 2),
    );
    if (!s && !anyWord) return 0;
    if (s) hits++;
    total += s;
  }
  if (!hits) return 0;
  const q = words.join(' ');
  if (k.flat[lang] === q) total += 10;
  else if (k.flat[lang].startsWith(q)) total += 3;
  else if (others.some((l) => k.flat[l] === q)) total += 4;
  // the curated headline metrics come first among equally good matches
  if (k.m.headline !== null && k.m.headline !== undefined) total += 4;
  return total;
}

export interface RankOpts {
  lang: Lang;
  /** available at the current level: listed first */
  ok?: (m: MetricMeta) => boolean;
  limit?: number;
  anyWord?: boolean;
}

/** Metrics matching the query, best first. */
export function rankMetrics(keys: MetricKey[], query: string, o: RankOpts): MetricMeta[] {
  const words = normWords(query);
  if (!words.length) return [];
  const ok = o.ok ?? (() => true);
  const label = (m: MetricMeta) => (o.lang === 'de' ? m.label_de : o.lang === 'fr' ? m.label_fr : null) || m.label_en;
  return keys
    .map((k) => ({ m: k.m, s: scoreMetric(k, words, o.lang, o.anyWord) }))
    .filter((x) => x.s > 0)
    .sort(
      (a, b) =>
        Number(ok(b.m)) - Number(ok(a.m)) ||
        b.s - a.s ||
        (a.m.headline ?? 1e9) - (b.m.headline ?? 1e9) ||
        label(a.m).length - label(b.m).length ||
        label(a.m).localeCompare(label(b.m)),
    )
    .slice(0, o.limit ?? 120)
    .map((x) => x.m);
}

/** One edit (insert, delete, substitute) apart, for "did you mean" when nothing matches. */
function oneEdit(a: string, b: string): boolean {
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0;
  let j = 0;
  let edits = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { i++; j++; continue; }
    if (++edits > 1) return false;
    if (a.length > b.length) i++;
    else if (b.length > a.length) j++;
    else { i++; j++; }
  }
  return edits + (a.length - i) + (b.length - j) <= 1;
}

/** Suggestions when nothing matches: metrics matching some of the words, else a word one typo away. */
export function suggestMetrics(keys: MetricKey[], query: string, o: RankOpts): { kind: 'partial' | 'typo' | 'none'; items: MetricMeta[] } {
  const some = rankMetrics(keys, query, { ...o, anyWord: true, limit: 8 });
  if (some.length) return { kind: 'partial', items: some };
  const words = normWords(query).filter((w) => w.length >= 3);
  const out: MetricMeta[] = [];
  for (const k of keys) {
    const all = [...k.label[o.lang], ...k.label.en];
    if (words.some((w) => all.some((x) => oneEdit(w, x.slice(0, w.length)) || oneEdit(w, x)))) out.push(k.m);
    if (out.length >= 8) break;
  }
  return { kind: out.length ? 'typo' : 'none', items: out };
}
