// Places: unit references, search (names in all languages, postal codes, BFS numbers) and the
// profile data files (identity, boundary history, neighbours, travel times). Everything here loads on
// demand: nothing is fetched at start.
import { getOptionalJSON, loadUnits, type UnitRow } from './data';

// ---------------------------------------------------------------- unit references
/** A unit at any level as one string: '261' (municipality) or 'kanton:ZH'. */
export interface UnitRef {
  level: string;
  id: string;
}
export function parseRef(s: string): UnitRef {
  const k = s.indexOf(':');
  return k < 0 ? { level: 'gemeinde', id: s } : { level: s.slice(0, k), id: s.slice(k + 1) };
}
export function refOf(level: string, id: string): string {
  return level === 'gemeinde' ? id : `${level}:${id}`;
}

// Zumikon (BFS 160): Wikidata gives the French label "Louta", which looks like a Wikidata error (no
// French exonym is known for Zumikon; "Louta" appears to belong to another item). Until it is fixed at
// the source, no alternative name is shown or searched for this municipality.
const HIDE_ALT_NAMES = new Set(['160']);
export const hideAltNames = (level: string, id: string) => level === 'gemeinde' && HIDE_ALT_NAMES.has(id);

// ---------------------------------------------------------------- search
interface SearchFile {
  fields: string[];
  units: [string, string, string, string | null, string[]][];
  plz_fields: string[];
  plz: Record<string, [string, string, number][]>;
}

export interface SearchUnit {
  ref: string;
  id: string;
  level: string;
  name: string;
  kanton: string | null;
  alts: string[];
  /** normalised name, then normalised alternative names */
  keys: string[];
}

export interface SearchIndex {
  units: SearchUnit[];
  byRef: Map<string, SearchUnit>;
  plz: Record<string, [string, string, number][]>;
  plzKeys: string[];
}

/** Lower case, accents and punctuation removed; 'Sankt'/'Saint' read as 'St'. */
export function norm(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\b(sankt|saint|san)\b/g, 'st')
    .replace(/\bsainte\b/g, 'ste')
    .trim();
}

let searchP: Promise<SearchIndex> | null = null;
export function loadSearch(): Promise<SearchIndex> {
  if (!searchP) {
    searchP = getOptionalJSON<SearchFile>('web/search.json').then((f) => {
      if (!f) throw new Error('search.json missing');
      const units: SearchUnit[] = f.units.map(([id, level, name, kanton, alts]) => {
        const a = hideAltNames(level, id) ? [] : alts;
        return { ref: refOf(level, id), id, level, name, kanton, alts: a, keys: [norm(name), ...a.map(norm)] };
      });
      return { units, byRef: new Map(units.map((u) => [u.ref, u])), plz: f.plz, plzKeys: Object.keys(f.plz).sort() };
    });
    searchP.catch(() => (searchP = null));
  }
  return searchP;
}

export interface SearchHit {
  ref: string;
  name: string;
  level: string;
  kanton: string | null;
  /** alternative name that matched ('Genf' for Genève) */
  via?: string;
  /** postal code hit: the PLZ and locality, and the share of its addresses in this municipality */
  plz?: { code: string; locality: string; share: number };
  /** BFS number hit */
  bfs?: boolean;
}

const LEVEL_BOOST: Record<string, number> = { gemeinde: 4, kanton: 3, bezirk: 2, schweiz: 2, gemeindetyp: 0 };

/** Search names (all languages), postal codes and BFS numbers. `pop` ranks equal matches. */
export function search(ix: SearchIndex, query: string, limit = 12, pop?: Map<string, number>): SearchHit[] {
  const q = norm(query);
  if (!q) return [];
  const out: SearchHit[] = [];
  const digits = /^\d+$/.test(q);
  if (digits) {
    // an exact BFS number comes first (it would otherwise be cut off behind the postal-code prefixes)
    const u = ix.byRef.get(q);
    if (u) out.push({ ref: u.ref, name: u.name, level: 'gemeinde', kanton: u.kanton, bfs: true });
    // postal codes: exact code first (all its municipalities, largest share first), then by prefix
    if (q.length >= 2 && q.length <= 4) {
      const codes = ix.plzKeys.filter((k) => k.startsWith(q)).slice(0, 6);
      for (const code of codes) {
        const seen = new Set<string>();
        const rows = ix.plz[code].slice().sort((a, b) => b[2] - a[2]);
        for (const [gid, locality, share] of rows) {
          if (seen.has(gid)) continue; // several localities (Zusatzziffer) of one code in the same municipality
          seen.add(gid);
          const u = ix.byRef.get(gid);
          if (!u) continue;
          out.push({ ref: u.ref, name: u.name, level: 'gemeinde', kanton: u.kanton, plz: { code, locality, share } });
        }
        if (out.length >= limit) break;
      }
    }
    return out.slice(0, limit);
  }
  const words = q.split(' ');
  const scored: { u: SearchUnit; s: number; via?: string }[] = [];
  for (const u of ix.units) {
    let best = 0;
    let via: string | undefined;
    for (let k = 0; k < u.keys.length; k++) {
      const key = u.keys[k];
      let s = 0;
      if (key === q) s = 100;
      else if (key.startsWith(q)) s = 80;
      else {
        const kw = key.split(' ');
        if (words.every((w) => kw.some((x) => x.startsWith(w)))) s = 60;
        else if (key.includes(q)) s = 40;
      }
      if (s && k === 0) s += 5;
      if (s > best) {
        best = s;
        via = k === 0 ? undefined : u.alts[k - 1];
      }
    }
    if (best) scored.push({ u, s: best + (LEVEL_BOOST[u.level] ?? 1), via });
  }
  scored.sort(
    (a, b) =>
      b.s - a.s ||
      (pop?.get(b.u.ref) ?? 0) - (pop?.get(a.u.ref) ?? 0) ||
      a.u.name.length - b.u.name.length ||
      a.u.name.localeCompare(b.u.name, 'de'),
  );
  for (const x of scored.slice(0, limit))
    out.push({ ref: x.u.ref, name: x.u.name, level: x.u.level, kanton: x.u.kanton, via: x.via });
  return out;
}

// ---------------------------------------------------------------- profile files
export interface Identity {
  wiki_url: string;
  commons_url: string;
  attribution: string;
  units: Record<
    string,
    {
      bezirk?: string;
      kanton?: string;
      names?: Record<string, string>;
      qid?: string;
      web?: string;
      wiki?: Record<string, string>;
      /** [Commons file name, licence, attribution required] */
      coa?: [string, string, boolean];
    }
  >;
}
export interface HistoryEvent {
  d: string;
  t: string;
  from: [string, string][];
  to: [string, string][];
  canton?: [string, string];
  district?: [string, string];
}
export interface HistoryFile {
  types: Record<string, string>;
  source: string;
  since: string;
  units: Record<string, HistoryEvent[]>;
}
export interface NeighboursFile {
  note: string;
  levels: Record<string, Record<string, string[]>>;
}
export interface ReachTimes {
  units: string[];
  hubs: [string, string][];
  service_date: string;
  /** door-to-door public transport (towards the hub once the D31 data is built; hub-outward before) */
  pt: Record<string, (number | null)[]>;
  car: Record<string, (number | null)[]>;
  periods: Record<string, string>;
  /** D31 headline: timetable time from the municipality's main station to the hub station */
  pt_station?: Record<string, (number | null)[]>;
  /** per unit: [stop name, DIDOK number, inside the municipality, mode ('rail', 'bus', …)] or null */
  main_station?: ([string, number, boolean?, string?] | null)[];
  /** mode -> {en, de, fr} names of the stop's mode */
  mode_text?: Record<string, Record<string, string>>;
  /** the hubs counted for "nearest hub" (D39) and the rule, per language */
  nearest_hubs?: [string, string][];
  nearest_rule?: Record<string, string>;
  /** per measure: name of the nearest hub per unit index */
  nearest?: Record<string, (string | null)[]>;
  /** per measure, hub and unit index: how a value was obtained (e.g. no arrival by 08:30) */
  notes?: Record<string, Record<string, Record<string, string>>>;
  /** one-line method texts per measure and language */
  methods?: Record<string, Record<string, string>>;
  /** per measure and hub: unit index -> why there is no time (older builds: per measure only) */
  reasons?: Record<string, Record<string, Record<string, string> | string>>;
}

function once<T>(path: string) {
  let p: Promise<T | null> | null = null;
  return (): Promise<T | null> => {
    if (!p) {
      p = getOptionalJSON<T>(path);
      p.catch(() => (p = null));
    }
    return p;
  };
}
export const loadIdentity = once<Identity>('web/identity.json');
export const loadHistory = once<HistoryFile>('web/history.json');
export const loadNeighbours = once<NeighboursFile>('web/neighbours.json');
export const loadReachTimes = once<ReachTimes>('web/reach_times.json');

/** units.json rows by reference ('261', 'kanton:ZH'). */
let rowsP: Promise<Map<string, UnitRow>> | null = null;
export function loadRows(): Promise<Map<string, UnitRow>> {
  if (!rowsP) {
    rowsP = loadUnits().then((u) => new Map(u.map((r) => [refOf(r.level, r.id), r])));
    rowsP.catch(() => (rowsP = null));
  }
  return rowsP;
}
