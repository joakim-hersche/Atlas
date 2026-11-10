import { describe, expect, it } from 'vitest';
import { breakNotes, breaksBetween, breakTickX, periodX, seriesBreaksOf } from './breaks';
import { FR_MAPX } from './i18n-mapx-fr';

const sb = {
  '2011': { label_en: 'From 2011 STATPOP', label_de: 'Ab 2011 STATPOP', label_fr: 'Dès 2011 STATPOP' },
  '2018': { label_en: 'Method 2018' },
};

describe('series breaks', () => {
  it('reads the note in the UI language, English as fallback', () => {
    expect(breakNotes(sb, 'de').get('2011')).toBe('Ab 2011 STATPOP');
    expect(breakNotes(sb, 'fr').get('2011')).toBe('Dès 2011 STATPOP');
    expect(breakNotes(sb, 'fr').get('2018')).toBe('Method 2018');
    expect(breakNotes(sb, 'en').get('2018')).toBe('Method 2018');
  });
  it('accepts a plain list of periods and period -> text', () => {
    expect([...breakNotes(['2011', '2013'], 'en')]).toEqual([['2011', null], ['2013', null]]);
    expect(breakNotes({ '2013': 'new cube' }, 'de').get('2013')).toBe('new cube');
    expect(breakNotes(null, 'en').size).toBe(0);
    expect(seriesBreaksOf({ id: 'x' })).toBeNull();
    expect(seriesBreaksOf({ series_breaks: sb })).toBe(sb);
  });
  it('finds the breaks a comparison straddles', () => {
    const ps = ['2005', '2008', '2010', '2011', '2015', '2018', '2020'];
    const isB = (p: string) => p === '2011' || p === '2018';
    expect(breaksBetween(ps, '2005', '2020', isB)).toEqual(['2011', '2018']);
    expect(breaksBetween(ps, '2010', '2011', isB)).toEqual(['2011']);   // 2011 is the first year on the new basis
    expect(breaksBetween(ps, '2011', '2015', isB)).toEqual([]);         // both on the new basis
    expect(breaksBetween(ps, '2018', '2020', isB)).toEqual([]);
    expect(breaksBetween(ps, '2015', '2010', isB)).toEqual([]);         // reversed
    expect(breaksBetween(ps, null, '2020', isB)).toEqual([]);
    expect(breaksBetween(ps, '1999', '2020', isB)).toEqual([]);         // unknown year
  });
  it('places the sparkline tick between the points around the break', () => {
    expect(periodX('2011')).toBe(2011);
    expect(periodX('2024-07')).toBeCloseTo(2024 + 7 / 13);
    expect(periodX('2009-2011')).toBe(2009);
    const xs = [2005, 2008, 2010, 2011, 2015].map(Number);
    expect(breakTickX(xs, 2011)).toBe(2010.5);
    expect(breakTickX(xs, 2012)).toBe(2013);      // no point in 2012: between 2011 and 2015
    expect(breakTickX(xs, 2005)).toBeNull();      // nothing before
    expect(breakTickX(xs, 2030)).toBeNull();      // after the last point
  });
});

describe('series-break strings', () => {
  it('exist in French', () => {
    for (const k of ['yc.break', 'yc.breakShort', 'yc.straddle', 'yc.straddleShort', 'yc.breakAt', 'sp.break', 's.breaks', 's.breakN'])
      expect(FR_MAPX[k], k).toBeTruthy();
    expect(FR_MAPX['yc.straddle']).toContain('{years}');
  });
});
