// Reactive cache of metric columns per (level, metric, year). Reading a column that is not loaded
// yet returns undefined and starts the download (theme file, or series file for a past year);
// the value appears once loaded and every $derived that asked for it re-runs.
import { SvelteMap, SvelteSet } from 'svelte/reactivity';
import { attachedFrom, loadSeries, loadTheme, loadUnits, seriesPeriods, withMajority, type Base, type ColRef, type Column, type LevelData } from './data';
import { app } from './state.svelte';
import { loadVoteFile, loadVoteIndex, voteIdOf } from './votes';

export interface ColView extends ColRef {
  /** a year was asked for but this metric has no value for it: the latest period is shown */
  yearMissing: string | null;
  /** a year was asked for but the metric's series file is not in this build: the latest period is shown */
  noSeries: boolean;
  /** a federal vote was asked for that this build does not have: the latest vote is shown */
  voteMissing?: string | null;
}

export class ColumnStore {
  #cache = new SvelteMap<string, ColRef | null>();
  #pending = new Set<string>();
  /** metrics whose series file is missing from this build (the preview ships headline series only) */
  #noSeries = new SvelteSet<string>();
  error = $state<string | null>(null);

  constructor(private base: Base) {}

  /** undefined = loading, null = not available at this level */
  get(ld: LevelData | null, id: string | null | undefined, year: string | null = null): ColView | null | undefined {
    if (!ld || !id) return null;
    const meta = this.base.metas.get(id);
    if (!meta) return null;
    const parent = attachedFrom(meta, ld.level);
    if (parent) return this.attached(ld, id, parent);
    if (!meta.levels.includes(ld.level)) return null;
    // per-vote metrics (yes share, turnout ...): the vote chosen in the vote picker, from its own file
    const voteId = meta.per_vote && meta.vote_index && app.vote && voteIdOf(meta.latest) !== app.vote ? app.vote : null;
    if (voteId) return this.vote(ld, id, voteId);
    const periods = seriesPeriods(meta, ld.level);
    const wanted = year && year !== meta.latest && periods.includes(year) ? year : null;
    const noSeries = !!wanted && this.#noSeries.has(id);
    const useYear = noSeries ? null : wanted;
    const yearMissing = year && year !== meta.latest && !wanted ? year : null;
    const key = `${ld.level}|${id}|${useYear ?? ''}`;
    const hit = this.#cache.get(key);
    if (hit !== undefined) return hit && { ...hit, col: app.maj ? withMajority(hit.col) : hit.col, yearMissing, noSeries };
    if (!this.#pending.has(key)) {
      this.#pending.add(key);
      const done = (v: ColRef | null) => {
        this.#pending.delete(key);
        this.#cache.set(key, v);
      };
      const fail = (e: unknown) => {
        this.#pending.delete(key);
        this.error = String(e);
      };
      if (!useYear) {
        loadTheme(ld.level, meta.file, ld.core)
          .then((f) => {
            const col = f.metrics[id];
            done(col ? { meta, level: ld.level, col, file: f } : null);
          })
          .catch(fail);
      } else {
        loadSeries(id)
          .catch(() => null)
          .then((s) => {
            if (!s) {
              // no series file in this build: not an error, the latest values are shown instead
              this.#pending.delete(key);
              this.#noSeries.add(id);
              return;
            }
            const k = s.periods.indexOf(useYear);
            const rows = s?.levels[ld.level] ?? {};
            const v = ld.units.map((u) => (k >= 0 ? (rows[u]?.[k] ?? null) : null));
            const col: Column = { period: useYear, v };
            // D37: single-seat-canton values and flags of that election
            const mv = s.m?.[ld.level];
            const fl = s.f?.[ld.level];
            if (k >= 0 && (mv || fl)) {
              const m: Record<string, number> = {};
              const f: Record<string, number> = {};
              ld.units.forEach((u, i) => {
                const x = mv?.[u]?.[String(k)];
                if (x !== undefined) m[String(i)] = x;
                const b = fl?.[u]?.[String(k)];
                if (b) f[String(i)] = b;
              });
              if (Object.keys(m).length) col.m = m;
              if (Object.keys(f).length) col.f = f;
            }
            done({ meta, level: ld.level, col, file: null });
          })
          .catch(fail);
      }
    }
    return undefined;
  }

  /** A regional value on the municipality map: each municipality takes the value of its area (D21).
   *  No series and no year: the latest values of the native level. */
  private attached(ld: LevelData, id: string, parent: string): ColView | null | undefined {
    const meta = this.base.metas.get(id)!;
    const key = `${ld.level}|${id}|from:${parent}`;
    const hit = this.#cache.get(key);
    if (hit !== undefined) return hit && { ...hit, yearMissing: null, noSeries: false };
    if (!this.#pending.has(key)) {
      this.#pending.add(key);
      Promise.all([loadTheme(parent, meta.file), parent === 'kanton' ? Promise.resolve(null) : loadUnits()])
        .then(([f, rows]) => {
          const col = f.metrics[id];
          let v: (number | null)[] | null = null;
          if (col) {
            const at = new Map(f.units.map((u, k) => [u, col.v[k] ?? null]));
            let code: (string | undefined)[];
            if (parent === 'kanton') code = ld.canton.slice();
            else {
              const byId = new Map((rows ?? []).filter((r) => r.level === 'gemeinde').map((r) => [r.id, r]));
              code = ld.units.map((u) => (byId.get(u) as Record<string, unknown> | undefined)?.[parent] as string | undefined);
            }
            v = code.map((c) => (c ? (at.get(c) ?? null) : null));
          }
          this.#pending.delete(key);
          this.#cache.set(key, v ? { meta, level: ld.level, col: { period: col!.period, v }, file: null } : null);
        })
        .catch((e) => {
          this.#pending.delete(key);
          this.error = String(e);
        });
    }
    return undefined;
  }

  /** Column of a per-vote metric for one vote; unknown vote or no vote files: the latest vote, flagged. */
  private vote(ld: LevelData, id: string, voteId: string): ColView | null | undefined {
    const meta = this.base.metas.get(id)!;
    const key = `${ld.level}|${id}|vote:${voteId}`;
    const hit = this.#cache.get(key);
    const flags = { yearMissing: null, noSeries: false };
    if (hit !== undefined) return hit && { ...hit, ...flags, voteMissing: hit.col.period === meta.latest ? voteId : null };
    if (!this.#pending.has(key)) {
      this.#pending.add(key);
      const done = (v: ColRef | null) => {
        this.#pending.delete(key);
        this.#cache.set(key, v);
      };
      const latest = () =>
        loadTheme(ld.level, meta.file, ld.core).then((f) => {
          const col = f.metrics[id];
          done(col ? { meta, level: ld.level, col, file: f } : null);
        });
      loadVoteIndex()
        .then((ix) => {
          const e = ix?.votes.find((v) => v.id === voteId);
          if (!e) return latest();
          return loadVoteFile(e.file).then((vf) => {
            const rows = vf?.levels[ld.level]?.[id];
            if (!vf || !rows) return latest();
            done({ meta, level: ld.level, col: { period: e.period, v: ld.units.map((u) => rows[u] ?? null) }, file: null });
          });
        })
        .catch((e) => {
          this.#pending.delete(key);
          this.error = String(e);
        });
    }
    return undefined;
  }
}
