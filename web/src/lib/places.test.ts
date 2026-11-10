import { describe, expect, it } from 'vitest';
import { norm, parseRef, refOf, search, searchUnit, type SearchIndex, type SearchUnit } from './places';
import { shortName } from './data';

// a small hand-made index in the shape of web/search.json: [id, level, name, canton, alternative names]
const ROWS: [string, string, string, string | null, string[]][] = [
  ['6621', 'gemeinde', 'Genève', 'GE', ['Genf', 'Geneva', 'Ginevra']],
  ['261', 'gemeinde', 'Zürich', 'ZH', ['Zurich', 'Zurigo']],
  ['3203', 'gemeinde', 'St. Gallen', 'SG', ['Saint-Gall', 'San Gallo']],
  ['3787', 'gemeinde', 'Sankt Moritz', 'GR', []],
  ['371', 'gemeinde', 'Biel/Bienne', 'BE', ['Bienne', 'Bienna']],
  ['2764', 'gemeinde', 'Biel-Benken', 'BL', []],
  ['6748', 'gemeinde', 'Les Genevez (JU)', 'JU', ['Les Genevez']],
  ['112', 'bezirk', 'Bezirk Zürich', 'ZH', []],
  ['2400', 'bezirk', 'Canton de Neuchâtel', 'NE', ['Cant. de Neuchâtel']],
  ['BE', 'kanton', 'Bern / Berne', null, ['Berne']],
  ['351', 'gemeinde', 'Bern', 'BE', ['Berne']],
  ['6458', 'gemeinde', 'Neuchâtel', 'NE', ['Neuenburg']],
  ['2196', 'gemeinde', 'Fribourg', 'FR', ['Freiburg']],
  ['242', 'gemeinde', 'Köniz', 'BE', []],
  ['GE', 'kanton', 'Genève', null, ['Genf']],
  ['ZH', 'kanton', 'Zürich', null, ['Zurich']],
];

function index(): SearchIndex {
  const units: SearchUnit[] = ROWS.map(([id, level, name, kanton, alts]) => searchUnit(id, level, name, kanton, alts));
  return {
    units,
    byRef: new Map(units.map((u) => [u.ref, u])),
    plz: { '8001': [['261', 'Zürich', 1]], '1201': [['6621', 'Genève', 0.9]] },
    plzKeys: ['1201', '8001'],
  };
}

describe('norm', () => {
  it('removes accents and case', () => {
    expect(norm('Genève')).toBe('geneve');
    expect(norm('Zürich')).toBe('zurich');
    expect(norm('ÉCUBLENS')).toBe('ecublens');
  });
  it('folds punctuation and the German sharp s', () => {
    expect(norm('Biel/Bienne')).toBe('biel bienne');
    expect(norm('Buchs (SG)')).toBe('buchs sg');
    expect(norm('Strasse')).toBe(norm('Straße'));
  });
  it('reads Sankt / Saint / San as St', () => {
    expect(norm('Sankt Moritz')).toBe('st moritz');
    expect(norm('Saint-Gall')).toBe('st gall');
    expect(norm('St. Gallen')).toBe('st gallen');
  });
});

describe('search', () => {
  const ix = index();
  const first = (q: string) => search(ix, q)[0];

  it('finds a place by its name with or without accents', () => {
    for (const q of ['Genève', 'Geneve', 'GENEVE', 'geneve']) expect(first(q).ref).toBe('6621');
  });
  it('finds a place by its name in another language and says which name matched', () => {
    const hit = first('Genf');
    expect(hit.ref).toBe('6621');
    expect(hit.via).toBe('Genf');
    expect(first('Freiburg').ref).toBe('2196');
    expect(first('zurigo').ref).toBe('261');
  });
  it('ranks the municipality before the canton of the same name', () => {
    const refs = search(ix, 'Zurich').map((h) => h.ref);
    expect(refs[0]).toBe('261');
    expect(refs).toContain('kanton:ZH');
  });
  it('matches Sankt, Saint and St spellings', () => {
    expect(first('Sankt Gallen').ref).toBe('3203');
    expect(first('St Moritz').ref).toBe('3787');
    expect(first('saint moritz').ref).toBe('3787');
  });
  it('matches prefixes and later words', () => {
    expect(first('Köni').ref).toBe('242');
    expect(first('koniz').ref).toBe('242');
    expect(first('bienne').ref).toBe('371');
    expect(first('gallen').ref).toBe('3203');
  });
  it('finds a municipality by BFS number and by postal code', () => {
    const bfs = search(ix, '261');
    expect(bfs[0]).toMatchObject({ ref: '261', bfs: true });
    const plz = search(ix, '1201');
    expect(plz[0]).toMatchObject({ ref: '6621', plz: { code: '1201', locality: 'Genève' } });
    expect(search(ix, '80').map((h) => h.ref)).toContain('261'); // postal-code prefix
  });
  it('returns nothing for an empty or unknown query and respects the limit', () => {
    expect(search(ix, '')).toEqual([]);
    expect(search(ix, '   ')).toEqual([]);
    expect(search(ix, 'qqqqq')).toEqual([]);
    expect(search(ix, 'e', 2)).toHaveLength(2);
  });
  it('uses population to rank equal matches', () => {
    const pop = new Map([['3203', 1], ['3787', 5]]);
    expect(search(ix, 'st', 5, pop)[0].ref).toBe('3787');
  });
});

describe('search ranking (U14) and short names (U15)', () => {
  const ix = index();
  const refs = (q: string) => search(ix, q).map((h) => h.ref);
  it('exact names come before prefix matches', () => {
    expect(refs('Geneve')[0]).toBe('6621');
    expect(refs('Geneve').indexOf('6748')).toBeGreaterThan(refs('Geneve').indexOf('kanton:GE'));
    expect(refs('Biel')[0]).toBe('371');
    expect(refs('Biel').indexOf('2764')).toBeGreaterThan(0);
    expect(refs('Bern').slice(0, 2)).toEqual(['351', 'kanton:BE']);
  });
  it('districts are found and shown without the administrative prefix', () => {
    const hit = search(ix, 'Zurich').find((h) => h.ref === 'bezirk:112');
    expect(hit?.name).toBe('Zürich');
    expect(search(ix, 'Neuchatel').find((h) => h.ref === 'bezirk:2400')?.name).toBe('Neuchâtel');
  });
  it('strips the prefix of district names only', () => {
    expect(shortName('bezirk', 'Bezirk Zürich')).toBe('Zürich');
    expect(shortName('bezirk', 'Wahlkreis Luzern-Stadt')).toBe('Luzern-Stadt');
    expect(shortName('bezirk', 'District de la Broye')).toBe('Broye');
    expect(shortName('bezirk', "District de l'Ouest lausannois")).toBe('Ouest lausannois');
    expect(shortName('bezirk', 'Distretto di Lugano')).toBe('Lugano');
    expect(shortName('bezirk', 'Arrondissement administratif Jura bernois')).toBe('Jura bernois');
    expect(shortName('bezirk', 'Verwaltungskreis Biel/Bienne')).toBe('Biel/Bienne');
    expect(shortName('bezirk', 'Kanton Uri')).toBe('Uri');
    expect(shortName('gemeinde', 'Region Test')).toBe('Region Test');
  });
});

describe('unit references', () => {
  it('round-trips municipalities and higher levels', () => {
    expect(parseRef('261')).toEqual({ level: 'gemeinde', id: '261' });
    expect(parseRef('kanton:ZH')).toEqual({ level: 'kanton', id: 'ZH' });
    expect(parseRef(refOf('bezirk', '101'))).toEqual({ level: 'bezirk', id: '101' });
    expect(refOf('gemeinde', '261')).toBe('261');
  });
});
