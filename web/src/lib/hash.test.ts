import { describe, expect, it } from 'vitest';
import { DEFAULT_HUB, DEFAULT_LEVEL, DEFAULT_METRIC, emptyFilter, historyKey, parseHash, serializeHash, T_MAX, type ViewState, browserLang } from './hash';

type Shared = Omit<ViewState, 'preset'>;
const withoutPreset = (s: ViewState): Shared => {
  const { preset: _preset, ...rest } = s;
  return rest;
};
/** state -> hash -> state */
const roundTrip = (s: Shared): Shared => withoutPreset(parseHash(serializeHash(s)));

describe('hash defaults', () => {
  const d = parseHash('');
  it('an empty hash is the default map view', () => {
    expect(d.route).toBe('map');
    expect(d.level).toBe(DEFAULT_LEVEL);
    expect(d.hub).toBe(DEFAULT_HUB);
    expect(d.metric).toBeNull();
    expect(d.filters).toEqual([]);
    expect(d.reach).toBe('off');
    expect(d.t).toBe(60);
    expect(d.lang).toBe('en');
    expect(DEFAULT_METRIC).toBe('geo_pop_density');
  });
  it('unreliable small-number values are hidden by default; old links keep their mode', () => {
    expect(d.unstable).toBe('hide');
    expect(parseHash('#ur=s').unstable).toBe('show');
    expect(parseHash('#ur=l').unstable).toBe('light');
    expect(parseHash('#ur=h').unstable).toBe('hide');
  });
  it('the default state serialises to an empty hash', () => {
    expect(serializeHash(withoutPreset(d))).toBe('');
  });
});

describe('hash round trip', () => {
  const full: Shared = {
    ...withoutPreset(parseHash('')),
    route: 'compare',
    level: 'bezirk',
    metric: 'geo_pop_density',
    metricB: 'share_foreign',
    size: 'pop_total',
    display: 'symbols',
    cls: 'equal',
    year: '2015',
    vote: '6890',
    vdiff: true,
    unstable: 'light',
    filters: [
      { kind: 'num', metric: 'pop_total', lo: 1000, hi: 50000 },
      { kind: 'num', metric: 'vac_rate', lo: null, hi: 1.5 },
      { kind: 'cat', field: 'kanton', values: ['ZH', 'BE'] },
      { kind: 'reach', hub: 'bern', mode: 'pt', max: 30 },
    ],
    hub: 'basel',
    reach: 'pt',
    t: 45,
    ptm: 'dd',
    ronly: true,
    maj: true,
    sel: '261',
    tab: 'rank',
    lang: 'de',
    only: true,
    params: { id: 'abc' },
  };

  it('keeps every field of a fully set state', () => {
    expect(roundTrip(full)).toEqual(full);
  });
  it('writes the documented keys', () => {
    const h = serializeHash(full);
    for (const part of ['v=compare', 'l=bezirk', 'm=geo_pop_density', 'b=share_foreign', 's=pop_total', 'd=sym', 'cls=e',
      'y=2015', 'f=n:pop_total:1000:50000', 'f=n:vac_rate::1.5', 'f=c:kanton:ZH,BE', 'f=r:bern:pt:30', 'hub=basel',
      'reach=pt', 't=45', 'ptm=dd', 'ro=1', 'mj=1', 'sel=261', 'tab=rank', 'lang=de', 'only=1']) expect(h).toContain(part);
    // each key once (mj used to be written twice: as a known key and again from params)
    expect(h.match(/mj=1/g)?.length).toBe(1);
    expect(h.startsWith('#')).toBe(true);
  });
  it('serialising twice gives the same hash (stable, shareable)', () => {
    const h = serializeHash(full);
    expect(serializeHash(withoutPreset(parseHash(h)))).toBe(h);
  });
  it('leaves defaults out', () => {
    const h = serializeHash({ ...withoutPreset(parseHash('')), metric: 'vac_rate' });
    expect(h).toBe('#m=vac_rate');
  });
  it('round-trips each continuous-method letter', () => {
    for (const cls of ['quantile', 'equal', 'continuous'] as const)
      expect(roundTrip({ ...full, cls }).cls).toBe(cls);
  });
  it('round-trips each unstable-value mode', () => {
    for (const unstable of ['show', 'light', 'hide'] as const)
      expect(roundTrip({ ...full, unstable }).unstable).toBe(unstable);
  });
  it('round-trips car reach and a city selection at a higher level', () => {
    const s: Shared = { ...withoutPreset(parseHash('')), reach: 'car', t: 90, hub: 'lugano', level: 'kanton', sel: 'ZH' };
    expect(roundTrip(s)).toEqual(s);
  });
  it('keeps unknown keys of later pages in params', () => {
    const s = parseHash('#v=profile&id=261&ids=1,2');
    expect(s.route).toBe('profile');
    expect(s.params).toEqual({ id: '261', ids: '1,2' });
    expect(roundTrip(withoutPreset(s))).toEqual(withoutPreset(s));
  });
});

describe('hash parsing', () => {
  it('clamps the reach time to 0..T_MAX', () => {
    expect(parseHash('#t=500').t).toBe(T_MAX);
    expect(parseHash('#t=-5').t).toBe(0);
    expect(parseHash('#f=r:bern:car:999').filters[0]).toMatchObject({ kind: 'reach', max: T_MAX });
  });
  it('ignores malformed filters and unknown classification letters', () => {
    const s = parseHash('#f=n:pop_total&f=c:nonsense:ZH&f=r:bern:boat:30&f=x:1&cls=z');
    expect(s.filters).toEqual([]);
    expect(s.cls).toBe('quantile');
  });
  it('accepts an empty bound of a number filter as open', () => {
    expect(parseHash('#f=n:pop_total:100:').filters[0]).toEqual({ kind: 'num', metric: 'pop_total', lo: 100, hi: null });
  });
  it('reads the old pop=min-max link as a population filter', () => {
    expect(parseHash('#pop=500-2000').filters[0]).toEqual({ kind: 'num', metric: 'pop_total', lo: 500, hi: 2000 });
  });
  it('reads a bare word as a compare preset or a route', () => {
    expect(parseHash('#compare')).toMatchObject({ route: 'compare', preset: '' });
    expect(parseHash('#density-foreigners')).toMatchObject({ route: 'compare', preset: 'density-foreigners' });
    expect(parseHash('#map')).toMatchObject({ route: 'map', preset: null });
  });
  it('a leading # is optional and unknown reach words mean off', () => {
    expect(parseHash('m=vac_rate').metric).toBe('vac_rate');
    expect(parseHash('#reach=boat').reach).toBe('off');
  });
  it('encodes values with special characters and reads them back', () => {
    const s: Shared = { ...withoutPreset(parseHash('')), params: { q: 'Zürich & Bern' } };
    expect(roundTrip(s).params.q).toBe('Zürich & Bern');
  });
});

describe('review fixes (U1-U4)', () => {
  const d = withoutPreset(parseHash(''));
  it('reach as a filter (ro=1) round-trips and is written only while reach is on', () => {
    const s: Shared = { ...d, reach: 'pt', hub: 'lausanne', t: 30, ronly: true };
    expect(serializeHash(s)).toContain('ro=1');
    expect(roundTrip(s).ronly).toBe(true);
    expect(serializeHash({ ...s, reach: 'off' })).not.toContain('ro=');
  });
  it('old links without ro keep reach as a display only', () => {
    expect(parseHash('#hub=lausanne&reach=pt&t=30').ronly).toBe(false);
  });
  it('drops empty conditions from the link (U3)', () => {
    const s: Shared = { ...d, filters: [
      { kind: 'num', metric: 'vac_rate', lo: null, hi: null },
      { kind: 'cat', field: 'kanton', values: [] },
      { kind: 'num', metric: 'pop_total', lo: 1000, hi: null },
    ] };
    const h = serializeHash(s);
    expect(h).toBe('#f=n:pop_total:1000:');
    expect(emptyFilter(s.filters[0])).toBe(true);
    expect(emptyFilter(s.filters[2])).toBe(false);
  });
  it('a step for Back: page, level, metric and selection; not sliders (U2)', () => {
    const k = historyKey(d);
    expect(historyKey({ ...d, sel: '261' })).not.toBe(k);
    expect(historyKey({ ...d, level: 'kanton' })).not.toBe(k);
    expect(historyKey({ ...d, metric: 'vac_rate' })).not.toBe(k);
    expect(historyKey({ ...d, route: 'profile', params: { id: '261' } })).not.toBe(k);
    // the default metric written or not is the same step
    expect(historyKey({ ...d, metric: DEFAULT_METRIC })).toBe(k);
    expect(historyKey({ ...(d as Shared), t: 90, year: '2015' } as Shared)).toBe(k);
  });
  it('keeps old keys readable', () => {
    const s = parseHash('#m=vac_rate&f=c:kanton:VD&hub=lausanne&reach=pt&t=30&tab=rank&mj=1&vd=1');
    expect(s).toMatchObject({ metric: 'vac_rate', hub: 'lausanne', reach: 'pt', t: 30, tab: 'rank', maj: true, vdiff: true });
    expect(s.params).toEqual({});
  });
});

describe('first-visit language (B7)', () => {
  it('follows the browser: German, Swiss German and Romansh read German, French, else English', () => {
    expect(browserLang(['de-CH', 'en'])).toBe('de');
    expect(browserLang(['gsw'])).toBe('de');
    expect(browserLang(['rm-CH'])).toBe('de');
    expect(browserLang(['fr-CH', 'de'])).toBe('fr');
    expect(browserLang(['en-GB'])).toBe('en');
  });
  it('skips Italian (no Italian UI) for the next listed language, else English', () => {
    expect(browserLang(['it-CH', 'de-CH'])).toBe('de');
    expect(browserLang(['it-CH', 'fr'])).toBe('fr');
    expect(browserLang(['it-CH'])).toBe('en');
    expect(browserLang([])).toBe('en');
  });
});
