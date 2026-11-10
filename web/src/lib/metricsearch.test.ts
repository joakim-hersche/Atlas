import { describe, expect, it } from 'vitest';
import type { MetricMeta } from './data';
import { metricKey, normWords, rankMetrics, suggestMetrics } from './metricsearch';

const meta = (id: string, en: string, de: string, fr: string, extra: Partial<MetricMeta> = {}): MetricMeta =>
  ({ id, label_en: en, label_de: de, label_fr: fr, theme: 'Politics', keywords: null, headline: null, ...extra }) as unknown as MetricMeta;

const METRICS = [
  meta('lang_se_en', 'Main language English (Structural Survey)', 'Hauptsprache Englisch (SE)', 'Langue principale anglais (relevé structurel)', { theme: 'Language & religion' }),
  meta('nrw_share_sp', 'Party strength SP (National Council)', 'Parteistärke SP (Nationalrat)', 'Force du parti PS (Conseil national)',
    { keywords: 'SP · Sozialdemokratische Partei der Schweiz · Parti socialiste suisse (PS)', headline: 66 }),
  meta('nrw_share_left_bloc', 'SP + Greens (National Council)', 'SP + Grüne (Nationalrat)', 'PS + Verts (Conseil national)'),
  meta('rent_avg', 'Average rent', 'Durchschnittliche Miete', 'Loyer moyen', { theme: 'Housing & buildings', headline: 30 }),
  meta('rent_3room', 'Rent of a 3-room flat', 'Miete 3-Zimmer-Wohnung', 'Loyer d’un 3 pièces', { theme: 'Housing & buildings' }),
  meta('geo_pop_density', 'Population density', 'Bevölkerungsdichte', 'Densité de population', { theme: 'Geography & identity', headline: 1 }),
  meta('pop_total', 'Population', 'Bevölkerung', 'Population', { theme: 'Population & demography', headline: 2 }),
  meta('noise_share_road_day_60', 'Residents with road noise of 60 dB(A) or more by day', 'Anteil Einwohner mit Strassenlärm ab 60 dB(A) tagsüber',
    'Part des habitants exposés au bruit routier', { theme: 'Environment & hazards' }),
  meta('vote_yes_share', 'Yes share', 'Ja-Anteil', 'Part de oui', { per_vote: true, headline: 90 }),
];
const keys = METRICS.map((m) => metricKey(m));
const ids = (q: string, lang: 'en' | 'de' | 'fr' = 'en') => rankMetrics(keys, q, { lang }).map((m) => m.id);

describe('metric search: spellings and topic words (F13, R3)', () => {
  it('reads ae / oe / ue as ä / ö / ü', () => {
    expect(normWords('Zürich')).toEqual(normWords('Zuerich'));
    expect(ids('Laerm', 'de')[0]).toBe('noise_share_road_day_60');
    expect(ids('lärm', 'en')[0]).toBe('noise_share_road_day_60');
  });
  it('finds the yes share with the word for a vote in any language', () => {
    for (const q of ['Abstimmung', 'votation', 'vote']) expect(ids(q, 'de')).toContain('vote_yes_share');
  });
  it('finds metrics by their theme in another language', () => {
    const k = METRICS.map((m) => metricKey(m, m.theme === 'Environment & hazards' ? 'Environment & hazards Umwelt & Naturgefahren Environnement & dangers naturels' : m.theme));
    expect(rankMetrics(k, 'Umwelt', { lang: 'en' }).map((m) => m.id)).toEqual(['noise_share_road_day_60']);
  });
});

describe('metric search (U5)', () => {
  it('normalises words', () => {
    expect(normWords('Bevölkerungsdichte (Einw./km²)')).toEqual(['bevolkerungsdichte', 'einw', 'km']);
  });
  it('matches word starts only: "SP" does not find "Hauptsprache"', () => {
    expect(ids('SP')).not.toContain('lang_se_en');
    expect(ids('SP').slice(0, 2).sort()).toEqual(['nrw_share_left_bloc', 'nrw_share_sp']);
  });
  it('ranks name matches first and the best hit is what Enter takes', () => {
    expect(ids('population')[0]).toBe('pop_total');
    expect(ids('pop dens')[0]).toBe('geo_pop_density');
    expect(ids('rent')[0]).toBe('rent_avg');
  });
  it('uses the labels of the UI language first', () => {
    expect(ids('miete', 'de')[0]).toBe('rent_avg');
    expect(ids('loyer', 'fr')[0]).toBe('rent_avg');
    // F13: a word inside a German compound is found, behind word starts
    expect(ids('dichte', 'de')).toEqual(['geo_pop_density']);
    expect(ids('bevolkerungsdichte', 'de')[0]).toBe('geo_pop_density');
  });
  it('finds a party by its full name in the keywords', () => {
    expect(ids('sozialdemokratische')).toEqual(['nrw_share_sp']);
  });
  it('suggests something when nothing matches', () => {
    expect(ids('rent english')).toEqual([]);
    const s = suggestMetrics(keys, 'rent english', { lang: 'en' });
    expect(s.kind).toBe('partial');
    expect(s.items.map((m) => m.id)).toContain('rent_avg');
    const typo = suggestMetrics(keys, 'populaton', { lang: 'en' });
    expect(typo.items.map((m) => m.id)).toContain('pop_total');
  });
});
