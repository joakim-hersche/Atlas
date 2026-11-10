// UI strings (English default, German option). Metric labels come from metrics.json (label_en /
// label_de); place names always stay in their official form. `t()` reads app.lang, so every template
// that calls it re-renders when the language changes.
import type { MetricMeta } from './data';
import { app } from './state.svelte';

type Dict = Record<string, string>;

const EN: Dict = {
  // header and navigation
  'nav.map': 'Map',
  'nav.compare': 'Compare metrics',
  'nav.places': 'Compare places',
  'nav.sources': 'Sources',
  'nav.menu': 'Menu',
  'nav.view': 'View',
  'nav.lang': 'Language',
  'brand.sub': 'Switzerland · {units} · boundaries of 2026',
  'status.loadingMap': 'Loading map…',
  'status.loading': 'Loading…',
  'status.error': 'Could not load data: {e}',
  // levels
  'level.label': 'Level',
  'level.more': 'More',
  'level.types': 'Municipality types (no map)',
  'level.note': '{metric} is not available for {level}; showing {fallback} instead.',
  'level.noteSize': 'Size: {metric} is not available for {level}; showing {fallback}.',
  'map.reset': 'Show all of Switzerland',
  'common.close': 'Close',
  'common.dismiss': 'Dismiss',
  'card.profile': 'Profile',
};

const DE: Dict = {
  'nav.map': 'Karte',
  'nav.compare': 'Kennzahlen vergleichen',
  'nav.places': 'Orte vergleichen',
  'nav.sources': 'Quellen',
  'nav.menu': 'Menü',
  'nav.view': 'Ansicht',
  'nav.lang': 'Sprache',
  'brand.sub': 'Schweiz · {units} · Gebietsstand 2026',
  'status.loadingMap': 'Karte wird geladen…',
  'status.loading': 'Wird geladen…',
  'status.error': 'Daten konnten nicht geladen werden: {e}',
  'level.label': 'Ebene',
  'level.more': 'Weitere',
  'level.types': 'Gemeindetypen (ohne Karte)',
  'level.note': '{metric} gibt es nicht für {level}; stattdessen {fallback}.',
  'level.noteSize': 'Grösse: {metric} gibt es nicht für {level}; stattdessen {fallback}.',
  'map.reset': 'Ganze Schweiz zeigen',
  'common.close': 'Schliessen',
  'common.dismiss': 'Ausblenden',
  'card.profile': 'Profil',
};

/** Add strings from a page module (keeps each page's strings next to it). */
export function addStrings(en: Dict, de: Dict): void {
  Object.assign(EN, en);
  Object.assign(DE, de);
}

export function t(key: string, vars?: Record<string, string | number>): string {
  const s = (app.lang === 'de' ? DE[key] : undefined) ?? EN[key] ?? key;
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`));
}

export const isDe = () => app.lang === 'de';

/** Metric label in the UI language. */
export function ml(m: MetricMeta | undefined | null): string {
  if (!m) return '';
  return app.lang === 'de' && m.label_de ? m.label_de : m.label_en;
}

const THEME_DE: Record<string, string> = {
  'Population & demography': 'Bevölkerung & Demografie',
  'Migration & nationality': 'Migration & Staatsangehörigkeit',
  'Language & religion': 'Sprache & Religion',
  'Households & family': 'Haushalte & Familie',
  'Economy & jobs': 'Wirtschaft & Arbeit',
  'Income & tax': 'Einkommen & Steuern',
  'Public finances': 'Öffentliche Finanzen',
  'Housing & buildings': 'Wohnen & Gebäude',
  'Real estate prices': 'Immobilienpreise',
  'Land use & built environment': 'Bodennutzung & Siedlung',
  'Mobility & accessibility': 'Mobilität & Erreichbarkeit',
  'Energy & climate': 'Energie & Klima',
  'Environment & hazards': 'Umwelt & Naturgefahren',
  'Health & social': 'Gesundheit & Soziales',
  Education: 'Bildung',
  Safety: 'Sicherheit',
  Politics: 'Politik',
  'Geography & identity': 'Geografie & Identität',
};
export function themeName(theme: string): string {
  return app.lang === 'de' ? (THEME_DE[theme] ?? theme) : theme;
}

// spatial levels: [plural, singular] per language
const LEVEL_NAMES: Record<string, { en: [string, string]; de: [string, string] }> = {
  gemeinde: { en: ['Municipalities', 'municipality'], de: ['Gemeinden', 'Gemeinde'] },
  bezirk: { en: ['Districts', 'district'], de: ['Bezirke', 'Bezirk'] },
  kanton: { en: ['Cantons', 'canton'], de: ['Kantone', 'Kanton'] },
  grossregion: { en: ['Major regions', 'major region'], de: ['Grossregionen', 'Grossregion'] },
  sprachgebiet: { en: ['Language regions', 'language region'], de: ['Sprachgebiete', 'Sprachgebiet'] },
  agglomeration: { en: ['Agglomerations', 'agglomeration'], de: ['Agglomerationen', 'Agglomeration'] },
  arbeitsmarktgebiet: { en: ['Labour market areas', 'labour market area'], de: ['Arbeitsmarktgebiete', 'Arbeitsmarktgebiet'] },
  stadt_land: { en: ['Urban / rural', 'urban/rural type'], de: ['Stadt/Land', 'Stadt/Land-Typ'] },
  gemeindetyp: { en: ['Municipality types', 'municipality type'], de: ['Gemeindetypen', 'Gemeindetyp'] },
  schweiz: { en: ['Switzerland', 'country'], de: ['Schweiz', 'Land'] },
};
/** Level name in the UI language: plural (capitalised) or singular (lower case in English). */
export function levelName(id: string, plural = true): string {
  const e = LEVEL_NAMES[id];
  if (!e) return id;
  return e[app.lang][plural ? 0 : 1];
}
