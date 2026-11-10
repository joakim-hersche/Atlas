import { describe, expect, it } from 'vitest';
import { fmtRange, fmtSpread, spreadOf, spreadReason, spreadLate, type SpreadFile } from './spread';

const stats = (p10: (number | null)[], p50: (number | null)[], p90: (number | null)[]) => ({ p10, p50, p90 });
const block = () => ({
  pt_station: { journey: stats([35, 37, null], [36, 37, null], [41, 37, null]), with_wait: stats([39, 38, null], [51, 44, null], [62, 53, null]) },
  pt: { journey: stats([null, 40.2, null], [40.4, 40.2, null], [47.6, 40.2, null]), with_wait: stats([41, 41.2, null], [47, 47.2, null], [56, 56.2, null]) },
});
const F: SpreadFile = {
  hub: 'zuerich', to: block(), from: block(),
  late_from: { pt_station: { '1': '08:55' } },
  reasons: { from: { pt_station: { '2': 'no departure from the hub 07:30-09:30 reaches it by 18:00' } } },
};

describe('travel-time spread (C1)', () => {
  it('formats the median with the 10–90 % range', () => {
    expect(fmtSpread(spreadOf(F, 0, 'to', 'pt_station', 'journey'))).toBe('36 min (35–41)');
    expect(fmtRange(spreadOf(F, 0, 'to', 'pt_station', 'with_wait'))).toBe('39–62');
  });
  it('leaves out a range that does not vary', () => {
    expect(fmtSpread(spreadOf(F, 1, 'from', 'pt_station', 'journey'))).toBe('37 min');
    expect(fmtSpread(spreadOf(F, 1, 'to', 'pt', 'journey'))).toBe('40 min');
  });
  it('handles missing values: no median = null, an undefined percentile = …', () => {
    expect(fmtSpread(spreadOf(F, 2, 'from', 'pt_station', 'journey'))).toBeNull();
    expect(fmtRange(spreadOf(F, 2, 'from', 'pt_station', 'journey'))).toBeNull();
    expect(fmtSpread(spreadOf(F, 0, 'to', 'pt', 'journey'))).toBe('40 min (…–48)');
    expect(spreadOf(F, -1, 'to', 'pt', 'journey')).toBeNull();
  });
  it('reads reasons and the late window', () => {
    expect(spreadReason(F, 2, 'from', 'pt_station')).toMatch(/no departure/);
    expect(spreadReason(F, 0, 'from', 'pt_station')).toBeNull();
    expect(spreadLate(F, 1, 'pt_station')).toBe('08:55');
    expect(spreadLate(F, 0, 'pt')).toBeNull();
  });
});
