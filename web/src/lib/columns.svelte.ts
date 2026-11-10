// Reactive cache of metric columns per (level, metric, year). Reading a column that is not loaded
// yet returns undefined and starts the download (theme file, or series file for a past year);
// the value appears once loaded and every $derived that asked for it re-runs.
import { SvelteMap, SvelteSet } from 'svelte/reactivity';
import { loadSeries, loadTheme, seriesPeriods, type Base, type ColRef, type LevelData } from './data';

export interface ColView extends ColRef {
  /** a year was asked for but this metric has no value for it: the latest period is shown */
  yearMissing: string | null;
  /** a year was asked for but the metric's series file is not in this build: the latest period is shown */
  noSeries: boolean;
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
    if (!meta || !meta.levels.includes(ld.level)) return null;
    const periods = seriesPeriods(meta, ld.level);
    const wanted = year && year !== meta.latest && periods.includes(year) ? year : null;
    const noSeries = !!wanted && this.#noSeries.has(id);
    const useYear = noSeries ? null : wanted;
    const yearMissing = year && year !== meta.latest && !wanted ? year : null;
    const key = `${ld.level}|${id}|${useYear ?? ''}`;
    const hit = this.#cache.get(key);
    if (hit !== undefined) return hit && { ...hit, yearMissing, noSeries };
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
            done({ meta, level: ld.level, col: { period: useYear, v }, file: null });
          })
          .catch(fail);
      }
    }
    return undefined;
  }
}
