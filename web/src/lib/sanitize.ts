// Keeps the URL honest: after a link is opened (or the hash changes), state that the app cannot use is
// replaced by what is actually shown, so the hash no longer carries ignored or replaced parameters
// (unknown metric, a year the metric does not have, an unknown tab, page keys on the map ...).
import { LEVELS, seriesPeriods, type Base } from './data';
import { REG_KEYS } from './regmodel';
import { DEFAULT_LEVEL, DEFAULT_METRIC } from './hash';
import { ml, t } from './i18n.svelte';
import { app, replaceNext } from './state.svelte';

const ROUTES = ['map', 'compare', 'regress', 'profile', 'places', 'sources'];
const TABS = ['filters', 'rank', 'stats'];
/** page keys each route reads from params */
const ROUTE_PARAMS: Record<string, string[]> = { map: [], compare: [], regress: REG_KEYS, profile: ['id', 'sm', 'nr'], places: ['ids'], sources: ['src'] };

export function sanitizeState(base: Base): void {
  const M = base.metas;
  const before = JSON.stringify(app.snapshot());
  // U4: what a link asked for and the app cannot show is said in a dismissible banner
  const notes: string[] = [];
  if (!ROUTES.includes(app.route)) app.route = 'map';
  if (!LEVELS.some((l) => l.id === app.level && l.geometry)) {
    notes.push(t('ux.badLevel', { id: app.level }));
    app.level = DEFAULT_LEVEL;
  }
  if (!M.has(app.metric)) {
    const bad = app.metric;
    app.metric = M.has(DEFAULT_METRIC) ? DEFAULT_METRIC : 'pop_total';
    notes.push(t('ux.badMetric', { id: bad, metric: ml(M.get(app.metric)) }));
  }
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
  if (fs.length !== app.filters.length) {
    notes.push(t('ux.badFilter', { n: app.filters.length - fs.length }));
    app.filters = fs;
  }
  if (app.tab !== null && !TABS.includes(app.tab)) app.tab = null;
  const keep = ROUTE_PARAMS[app.route] ?? [];
  const extra = Object.keys(app.params).filter((k) => !keep.includes(k));
  if (extra.length) app.params = Object.fromEntries(Object.entries(app.params).filter(([k]) => keep.includes(k)));
  // tidying a link replaces its history entry instead of adding a step (U2)
  if (JSON.stringify(app.snapshot()) !== before) replaceNext();
  if (notes.length) app.notice = notes.join(' ');
}
