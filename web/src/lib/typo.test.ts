import { describe, expect, it } from 'vitest';
import { colon, frTypo, pctSep } from './typo';

describe('French typography (B8, E8)', () => {
  it('narrow no-break space before : ; ! ? and %', () => {
    expect(frTypo('Source : BFS', 'fr')).toBe('Source : BFS');
    expect(frTypo('Barres : ce lieu ; traits', 'fr')).toBe('Barres : ce lieu ; traits');
    expect(frTypo('99 % et 14,5 %', 'fr')).toBe('99 % et 14,5 %');
  });
  it('leaves times, URLs and other languages alone', () => {
    expect(frTypo('départ 08:30, https://atlas.ch', 'fr')).toBe('départ 08:30, https://atlas.ch');
    expect(frTypo("Source : l'OFS", 'de')).toBe("Source : l'OFS");
  });
  it('curly apostrophes between letters', () => {
    expect(frTypo("l'OFS d'après", 'fr')).toBe('l’OFS d’après');
  });
  it('colon and percent separators per language', () => {
    expect(colon('fr')).toBe(' : ');
    expect(colon('de')).toBe(': ');
    expect(pctSep('fr')).toBe(' ');
    expect(pctSep('en')).toBe(' ');
  });
});
