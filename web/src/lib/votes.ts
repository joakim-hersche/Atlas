// Federal votes (D32): the vote index (all votes with titles, national and canton results, Ständemehr)
// and one file per vote with the results at every level. Contract: docs/web_data_contract.md section 5.
// Files are under web/votes/ in the data folder; builds without them keep the single latest vote.
import { getOptionalJSON } from './data';
import { periodTitles } from './classify';

export interface VoteEntry {
  id: string;
  period: string;
  date: string;
  title: Record<string, string>;
  title_source?: string;
  yes_pct: number | null;
  turnout_pct: number | null;
  yes?: number | null;
  no?: number | null;
  accepted: boolean | null;
  cantons_yes: number | null;
  cantons_no: number | null;
  cantons_total: number | null;
  canton_yes_pct: (number | null)[];
  provisional?: boolean;
  file: string;
}
export interface VoteIndex {
  source: string;
  generated?: string;
  cantons: string[];
  half_cantons: string[];
  votes: VoteEntry[];
}
/** levels -> metric -> unit id -> value */
export interface VoteFile {
  period: string;
  levels: Record<string, Record<string, Record<string, number | null>>>;
}

let ixP: Promise<VoteIndex | null> | null = null;
/** The vote index (null when this build has none). Registers the vote titles for period labels. */
export function loadVoteIndex(): Promise<VoteIndex | null> {
  if (!ixP) {
    ixP = getOptionalJSON<VoteIndex>('web/votes/index.json')
      .then((ix) => {
        // an empty title in the index does not replace the title metrics.json gives for the latest vote
        if (ix?.votes) for (const v of ix.votes) if (v.title && Object.keys(v.title).length) periodTitles.set(v.period, v.title);
        return ix?.votes ? ix : null;
      })
      .catch(() => null);
  }
  return ixP;
}

const files = new Map<string, Promise<VoteFile | null>>();
export function loadVoteFile(file: string): Promise<VoteFile | null> {
  let p = files.get(file);
  if (!p) {
    p = getOptionalJSON<VoteFile>(`web/${file}`).catch(() => null);
    files.set(file, p);
  }
  return p;
}

/** Vote id of a per-vote period ('2026-06-14#6870' -> '6870'). */
export const voteIdOf = (period: string) => period.split('#')[1] ?? null;

/** Ständemehr as text: "14½ : 8½" (half cantons count ½). */
export function standText(x: number | null): string {
  if (x === null || x === undefined) return '–';
  const whole = Math.floor(x);
  const half = Math.abs(x - whole - 0.5) < 1e-6;
  return half ? `${whole ? whole : ''}½` : String(whole);
}
