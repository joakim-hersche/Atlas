import { describe, expect, it } from 'vitest';
import { translate, type TextsFile } from './texts';

const SMALL: TextsFile = {
  version: 1,
  langs: ['de', 'fr'],
  exact: {
    'published canton value': { de: 'veröffentlichter Wert des Kantons', fr: 'valeur publiée du canton' },
    'no data': { de: 'ohne Daten', fr: 'sans données' },
  },
  patterns: [
    { en: '([\\d,]+) of ([\\d,]+) municipalities without a value: (.+)', de: '{1|n} von {2|n} Gemeinden ohne Wert: {3|l}', fr: '{1|n} communes sur {2|n} sans valeur : {3|l}' },
    { en: '([\\d,]+) no data', de: '{1|n} ohne Daten', fr: '{1|n} sans données' },
    { en: 'share ([\\d.]+) %', de: 'Anteil {1|n} %', fr: 'part {1|n} %' },
  ],
  numbers: { de: { group: "'", decimal: '.' }, fr: { group: ' ', decimal: ',' } },
};

describe('pipeline texts in German and French (texts.json)', () => {
  it('exact keys, patterns with numbers and lists, segments joined with "; "', () => {
    expect(translate(SMALL, 'published canton value', 'de')).toBe('veröffentlichter Wert des Kantons');
    expect(translate(SMALL, '1,234 of 2,110 municipalities without a value: 5 no data', 'de')).toBe("1'234 von 2'110 Gemeinden ohne Wert: 5 ohne Daten");
    expect(translate(SMALL, 'share 3.5 %', 'fr')).toBe('part 3,5 %');
    expect(translate(SMALL, 'published canton value; 7 no data', 'de')).toBe('veröffentlichter Wert des Kantons; 7 ohne Daten');
  });
  it('keeps English where nothing matches, and in English', () => {
    expect(translate(SMALL, 'an unknown note', 'de')).toBe('an unknown note');
    expect(translate(SMALL, 'published canton value; an unknown note', 'de')).toBe('veröffentlichter Wert des Kantons; an unknown note');
    expect(translate(SMALL, 'published canton value', 'en')).toBe('published canton value');
    expect(translate(null, 'published canton value', 'de')).toBe('published canton value');
  });

  // the real file, when a pipeline build is present (same cases as pipeline/tests/test_round3.py)
  it('matches the pipeline reference on the shipped file (when a build is present)', async () => {
    const path = '../../../data/out/web/texts.json';
    let f: TextsFile;
    try {
      f = ((await import(/* @vite-ignore */ path)) as { default: TextsFile }).default;
    } catch {
      return; // no pipeline build in this checkout
    }
    const s = 'published canton value; municipal values incomplete (3 of 352 municipalities without a value: 3 suppressed (small numbers), 1 no data)';
    expect(translate(f, s, 'de')).toBe('veröffentlichter Wert des Kantons; Gemeindewerte unvollständig (3 von 352 Gemeinden ohne Wert: 3 unterdrückt (kleine Zahlen), 1 ohne Daten)');
    expect(translate(f, s, 'fr').replace(/ /g, ' ')).toMatch(/^valeur publiée du canton ; valeurs communales incomplètes \(3 communes sur 352/);
    const v = 'proportional-representation cantons only: excludes 65 of 1,374 municipalities in single-seat cantons (AI, AR; 3.0 % of fictitious voters)';
    expect(translate(f, v, 'de')).toContain("1'374");
    expect(translate(f, v, 'fr').replace(/ /g, ' ')).toContain('3,0 %');
    // one part per moved municipality: needs the "without ((?:(?!; ).)+) …" pattern of pipeline/i18n/texts.yaml
    if (f.patterns.some((p) => p.en.startsWith('without ((?:(?!; ).)+)'))) {
      const b = "on today's boundaries: without Clavaleyres (now canton FR); without Moutier (now canton JU), so it differs from the figure published for the canton at the time";
      expect(translate(f, b, 'de')).toBe('auf dem heutigen Gebietsstand: ohne Clavaleyres (heute Kanton FR); ohne Moutier (heute Kanton JU); deshalb weicht der Wert von der damals für den Kanton veröffentlichten Zahl ab');
    }
  });
});
