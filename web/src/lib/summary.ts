// "In short" (profile page): a few plain-language sentences about one place, built from fixed templates
// and the data already loaded for the profile. Every sentence states a value of the place with its year and
// where it stands among all units of the level (share of the other units with a lower value). Nothing is
// said that the data does not support: a fact is left out when the value is missing or not unusual.
// Wording is descriptive (larger, younger, higher), never an assessment.
import { fmtNumber, fmtPeriod, fmtValue } from './classify';
import type { Base, ColumnFile, MetricMeta } from './data';
import { levelWord, ml, t } from './i18n.svelte';
import type { ReachTimes } from './places';
import type { PlaceLevel } from './profile';

export interface Fact {
  text: string;
  /** smaller print after the sentence (where a number comes from) */
  note?: string;
}

interface Stat {
  meta: MetricMeta;
  x: number;
  period: string;
  /** % of the other units with a lower value / with a higher value */
  below: number;
  above: number;
  median: number;
}

function statOf(pl: PlaceLevel, file: ColumnFile, meta: MetricMeta | undefined, i: number, minN = 10): Stat | null {
  if (!meta) return null;
  const col = file.metrics[meta.id];
  const x = col?.v[i];
  if (x === null || x === undefined) return null;
  let lo = 0, hi = 0, n = 0;
  const all: number[] = [];
  for (const y of col.v) {
    if (y === null || y === undefined) continue;
    n++;
    all.push(y);
    if (y < x) lo++;
    else if (y > x) hi++;
  }
  if (n < minN) return null;
  all.sort((a, b) => a - b);
  const median = n % 2 ? all[(n - 1) / 2] : (all[n / 2 - 1] + all[n / 2]) / 2;
  return { meta, x, period: col.period, below: (100 * lo) / (n - 1), above: (100 * hi) / (n - 1), median };
}

/** "90 % of Swiss municipalities" / "all other Swiss municipalities". */
function than(p: number, units: string): string {
  const q = Math.floor(p);
  return q >= 100 ? t('is.all', { units }) : t('is.pct', { p: fmtNumber(q, 0), units });
}

/** Side of the distribution: 'hi' above the median band, 'lo' below it, 'mid' between the 40th and 60th percentile. */
const side = (s: Stat): 'hi' | 'lo' | 'mid' => (s.below >= 60 ? 'hi' : s.above >= 60 ? 'lo' : 'mid');
/** the percentile figure to quote for a side */
const pctFor = (s: Stat, sd: 'hi' | 'lo') => (sd === 'hi' ? s.below : s.above);
/** how far from the middle: 0 (median) to 50 (an extreme) */
const spread = (s: Stat) => Math.abs(s.below - s.above) / 2;

const GENERIC = ['geo_elev_mean', 'geo_pop_density', 'share_foreign', 'tax_np_mean_taxable_income', 'ent_jobs_per_1000'];

export function inShort(a: { pl: PlaceLevel; idx: number; base: Base; reach: ReachTimes | null; placeName: string; files?: Record<string, ColumnFile> }): Fact[] {
  const { pl, idx, base, reach } = a;
  /** the loaded theme file of a metric (core first) */
  const fileOf = (id: string): ColumnFile | null => {
    const m = base.metas.get(id);
    if (!m) return null;
    if (pl.core.metrics[id]) return pl.core;
    return a.files?.[m.file] ?? null;
  };
  const core = pl.core;
  const units = levelWord(pl.level);
  const out: Fact[] = [];
  const val = (s: Stat) => fmtValue(s.x, s.meta);
  /** value for a sentence that already names the metric: the unit is dropped where the label contains it */
  const valIn = (s: Stat) => (s.meta.unit && ml(s.meta).toLowerCase().includes(s.meta.unit.toLowerCase()) ? fmtNumber(s.x, s.meta.decimals) : val(s));

  // size
  const pop = statOf(pl, core, base.metas.get('pop_total'), idx);
  if (pop) {
    const sd = side(pop);
    const vars = { v: fmtNumber(pop.x, 0), y: fmtPeriod(pop.period), m: fmtNumber(pop.median, 0), units };
    if (sd === 'mid') out.push({ text: t('is.size.mid', vars) });
    else out.push({ text: t(sd === 'hi' ? 'is.size.hi' : 'is.size.lo', { ...vars, than: than(pctFor(pop, sd), units) }) });
  }

  // age
  const age = statOf(pl, core, base.metas.get('share_age_65plus'), idx);
  if (age) {
    const sd = side(age);
    const vars = { v: val(age), y: fmtPeriod(age.period), m: fmtValue(age.median, age.meta), units };
    if (sd === 'mid') out.push({ text: t('is.age.mid', vars) });
    else out.push({ text: t(sd === 'hi' ? 'is.age.hi' : 'is.age.lo', { ...vars, than: than(pctFor(age, sd), units) }) });
  }

  // language (Swiss-wide shares of the three large languages; left out where other languages dominate).
  // B6 (D10, E13): the Structural Survey shares of the cities (lang_sec_*, recent, pooled years) where they exist,
  // else the census 2000; the sentence names its source and years.
  const langOf = (pre: string) =>
    (['de', 'fr', 'it'] as const)
      .map((k) => {
        const id = `${pre}_${k}_share`;
        const f = fileOf(id);
        return { k, s: f ? statOf(pl, f, base.metas.get(id), idx, 1) : null };
      })
      .filter((q): q is { k: 'de' | 'fr' | 'it'; s: Stat } => q.s !== null);
  const sec = pl.level === 'gemeinde' ? langOf('lang_sec') : [];
  const lg = sec.length === 3 ? sec : langOf('vz_lang');
  if (lg.length === 3) {
    const sum = lg.reduce((p, q) => p + q.s.x, 0);
    lg.sort((p, q) => q.s.x - p.s.x);
    const y = t(sec.length === 3 ? 'r3.langSE' : 'r3.langVZ', { y: fmtPeriod(lg[0].s.period) });
    if (sum >= 80) {
      if (lg[0].s.x >= 60) out.push({ text: t('is.lang.one', { l: t(`is.l.${lg[0].k}`), v: fmtValue(lg[0].s.x, lg[0].s.meta), y }) });
      else
        out.push({
          text: t('is.lang.mix', {
            a: t(`is.lg.${lg[0].k}`), x: fmtValue(lg[0].s.x, lg[0].s.meta), b: t(`is.lg.${lg[1].k}`), z: fmtValue(lg[1].s.x, lg[1].s.meta), y,
          }),
        });
    }
  }

  // up to three more figures where the place stands out (clearly above or below the middle of the units)
  const extra = GENERIC.map((id) => statOf(pl, core, base.metas.get(id), idx))
    .filter((s): s is Stat => s !== null && spread(s) >= 25)
    .sort((p, q) => spread(q) - spread(p))
    .slice(0, 3);
  for (const s of extra) {
    const sd = side(s) as 'hi' | 'lo';
    out.push({ text: t(sd === 'hi' ? 'is.g.hi' : 'is.g.lo', { label: ml(s.meta), v: valIn(s), y: fmtPeriod(s.period), than: than(pctFor(s, sd), units) }) });
  }

  // travel: nearest hub by the timetable (station time when the build has it, else door to door)
  if (pl.level === 'gemeinde' && reach) {
    const k = reach.units.indexOf(pl.units[idx]);
    if (k >= 0) {
      const st = reach.pt_station;
      // D39: "nearest hub" counts only the 15 agglomeration hubs when the build lists them
      const pool = reach.nearest_hubs?.length ? reach.nearest_hubs : reach.hubs;
      const rows = pool
        .map(([slug, hub]) => ({ slug, hub, m: (st ? st[slug]?.[k] : reach.pt[slug]?.[k]) ?? null, car: reach.car[slug]?.[k] ?? null }))
        // a hub whose station is this municipality's main station (0 min) is not "near", it is here
        .filter((h): h is typeof h & { m: number } => h.m !== null && h.m > 0)
        .sort((p, q) => p.m - q.m);
      // B6 (R9, F10): the hub the nearest-hub metric names for the same measure, so the summary and the metric agree
      const named = reach.nearest?.[st ? 'pt_station' : 'pt']?.[k] ?? null;
      const best = (named ? rows.find((r) => r.hub === named) : undefined) ?? rows[0];
      const own = pool.filter(([slug]) => (st ? st[slug]?.[k] : reach.pt[slug]?.[k]) === 0).map(([, hub]) => hub);
      if (best) {
        const stop = reach.main_station?.[k];
        // the data carries the stop's mode as a 4th element ('rail', 'bus', ...) that the shared type does not list yet
        const stopMode = stop?.[3];
        const mode = stopMode === 'rail' ? t('is.train') : t('is.pt');
        const vars = { m: fmtNumber(best.m, 0), hub: best.hub, mode, c: best.car === null ? '' : fmtNumber(best.car, 0) };
        out.push({
          text: t(best.car === null ? 'is.travel' : 'is.travelCar', vars),
          note:
            t(st && stop ? 'is.travelNote' : 'is.travelNoteDoor', { st: stop?.[0] ?? '', n: pool.length, d: reach.service_date.slice(0, 4) }) +
            (own.length ? t('is.travelOwn', { hub: own.join(', ') }) : ''),
        });
      }
    }
  }
  return out;
}
