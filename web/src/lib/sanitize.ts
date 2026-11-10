// Keeps the URL honest: after a link is opened (or the hash changes), state that the app cannot use is
// replaced by what is actually shown, so the hash no longer carries ignored or replaced parameters
// (unknown metric, a year the metric does not have, an unknown tab, page keys on the map ...).
import { LEVELS, seriesPeriods, type Base } from './data';
import { REG_KEYS } from './regmodel';
import { DEFAULT_LEVEL, DEFAULT_METRIC } from './hash';
import { app } from './state.svelte';

const ROUTES = ['map', 'compare', 'regress', 'profile', 'places', 'sources'];
const TABS = ['filters', 'rank', 'stats'];
/** page keys each route reads from params */
const ROUTE_PARAMS: Record<string, string[]> = { map: [], compare: [], regress: REG_KEYS, profile: ['id', 'sm', 'nr'], places: ['ids'], sources: ['src'] };

export function sanitizeState(base: Base): void {
  const M = base.metas;
  if (!ROUTES.includes(app.route)) app.route = 'map';
  if (!LEVELS.some((l) => l.id === app.level && l.geometry)) app.level = DEFAULT_LEVEL;
  if (!M.has(app.metric)) app.metric = M.has(DEFAULT_METRIC) ? DEFAULT_METRIC : 'pop_total';
  if (app.metricB && !M.has(app.metricB)) app.metricB = null;
  if (app.size && !M.has(app.size)) app.size = null;
  if (app.year) {
    const ids = [app.metric, app.route === 'compare' ? app.metricB : null, app.size].filter((x): x is string => !!x);
    const ok = ids.some((id) => seriesPeriods(M.get(id)!, app.level).includes(app.year!));
    if (!ok) app.year = null;
  }
  const perVote = [app.metric, app.metricB, app.size].some((id) => !!id && !!M.get(id)?.per_vote);
  if (app.vote && !perVote) app.vote = null;
  if (app.vdiff && app.metric !== 'vote_yes_share') app.vdiff = false;
  const fs = app.filters.filter((f) => f.kind !== 'num' || M.has(f.metric));
  if (fs.length !== app.filters.length) app.filters = fs;
  if (app.tab !== null && !TABS.includes(app.tab)) app.tab = null;
  const keep = ROUTE_PARAMS[app.route] ?? [];
  const extra = Object.keys(app.params).filter((k) => !keep.includes(k));
  if (extra.length) app.params = Object.fromEntries(Object.entries(app.params).filter(([k]) => keep.includes(k)));
}
