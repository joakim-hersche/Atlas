// Plain-language glossary (pipeline/i18n/glossary.yaml -> web/glossary.json): short explanations of
// jargon (quantile, P10/P90, z-score, labour market area ...) behind an ⓘ next to the word. Loaded on
// first use; a build without the file shows no ⓘ.
import { getOptionalJSON, type MetricMeta } from './data';
import { SPATIAL_GLOSS } from './spatial-gloss';
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

/** Regression terms (D34), kept in the frontend until the pipeline glossary carries them; an entry of the
 *  same key in glossary.json takes precedence. */
const LOCAL: Record<string, GlossEntry> = {
  r_squared: {
    term_en: 'R²', term_de: 'R²', term_fr: 'R²',
    en: 'The share of the differences in the outcome between places that the model accounts for: 0 = none, 1 = all. Adjusted R² takes the number of variables into account.',
    de: 'Der Anteil der Unterschiede in der Zielgrösse zwischen den Orten, den das Modell erfasst: 0 = nichts, 1 = alles. Das korrigierte R² berücksichtigt die Zahl der Variablen.',
    fr: 'La part des différences de la variable expliquée entre les lieux que le modèle reproduit : 0 = aucune, 1 = toutes. Le R² ajusté tient compte du nombre de variables.',
  },
  coefficient: {
    term_en: 'Coefficient', term_de: 'Koeffizient', term_fr: 'Coefficient',
    en: 'How much the outcome changes, on average, when this variable is one unit higher and the other variables stay the same. With log₁₀, one unit means ten times the value.',
    de: 'Um wie viel sich die Zielgrösse im Mittel ändert, wenn diese Variable um eine Einheit höher ist und die übrigen gleich bleiben. Bei log₁₀ heisst eine Einheit: zehnmal so viel.',
    fr: 'De combien la variable expliquée change en moyenne quand cette variable augmente d’une unité, les autres restant égales. Avec log₁₀, une unité signifie dix fois la valeur.',
  },
  standardized_coefficient: {
    term_en: 'Standardized coefficient (β)', term_de: 'Standardisierter Koeffizient (β)', term_fr: 'Coefficient standardisé (β)',
    en: 'The coefficient in standard deviations: by how many standard deviations the outcome moves when the variable moves by one. Makes variables with different units comparable.',
    de: 'Der Koeffizient in Standardabweichungen: um wie viele Standardabweichungen sich die Zielgrösse bewegt, wenn sich die Variable um eine bewegt. Macht Variablen mit verschiedenen Einheiten vergleichbar.',
    fr: 'Le coefficient en écarts types : de combien d’écarts types la variable expliquée varie quand la variable varie d’un écart type. Rend comparables des variables d’unités différentes.',
  },
  confidence_interval: {
    term_en: '95 % confidence interval', term_de: '95 %-Konfidenzintervall', term_fr: 'Intervalle de confiance à 95 %',
    en: 'The range of coefficients that fit the data: if the model’s assumptions hold, ranges built this way contain the true value 95 times out of 100. A range that includes 0 means the direction is uncertain.',
    de: 'Der Bereich von Koeffizienten, die zu den Daten passen: Treffen die Annahmen des Modells zu, enthalten so gebildete Bereiche den wahren Wert 95 von 100 Mal. Enthält der Bereich 0, ist die Richtung unsicher.',
    fr: 'La fourchette des coefficients compatibles avec les données : si les hypothèses du modèle tiennent, des fourchettes ainsi construites contiennent la vraie valeur 95 fois sur 100. Si elle contient 0, le sens de l’effet est incertain.',
  },
  clustered_se: {
    term_en: 'Clustered standard errors', term_de: 'Geclusterte Standardfehler', term_fr: 'Erreurs types groupées',
    en: 'Standard errors that allow places in the same canton to share unexplained ups and downs. They are usually larger, and more honest, than conventional ones. Computed as in Stata (CR1).',
    de: 'Standardfehler, die zulassen, dass Orte im selben Kanton gemeinsame unerklärte Abweichungen haben. Meist grösser, und ehrlicher, als konventionelle. Berechnet wie in Stata (CR1).',
    fr: 'Erreurs types qui admettent que les lieux d’un même canton partagent des écarts inexpliqués. Elles sont en général plus grandes, et plus honnêtes, que les erreurs classiques. Calculées comme dans Stata (CR1).',
  },
  residual: {
    term_en: 'Residual', term_de: 'Residuum', term_fr: 'Résidu',
    en: 'Observed value minus the value the model predicts from the other variables. Positive: higher than expected for a place like this; negative: lower.',
    de: 'Beobachteter Wert minus der Wert, den das Modell aus den übrigen Variablen vorhersagt. Positiv: höher als für einen solchen Ort erwartet; negativ: tiefer.',
    fr: 'Valeur observée moins la valeur que le modèle prédit à partir des autres variables. Positif : plus élevé qu’attendu pour un lieu de ce type ; négatif : plus bas.',
  },
  fixed_effects: {
    term_en: 'Fixed effects (controls)', term_de: 'Fixeffekte (Kontrollen)', term_fr: 'Effets fixes (contrôles)',
    en: 'One extra term per group (language region or canton). The other coefficients then compare places only within the same group, so differences between groups as a whole do not drive them.',
    de: 'Ein zusätzlicher Term je Gruppe (Sprachgebiet oder Kanton). Die übrigen Koeffizienten vergleichen dann nur Orte innerhalb derselben Gruppe; Unterschiede zwischen den Gruppen als Ganzes treiben sie nicht.',
    fr: 'Un terme supplémentaire par groupe (région linguistique ou canton). Les autres coefficients ne comparent alors que des lieux d’un même groupe ; les différences entre groupes dans leur ensemble ne les influencent pas.',
  },
};

/** Term and explanation in the UI language, or null (unknown key, or no glossary in this build). */
export function gloss(key: string): { term: string; text: string } | null {
  const e = entries?.[key] ?? LOCAL[key] ?? SPATIAL_GLOSS[key];
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
