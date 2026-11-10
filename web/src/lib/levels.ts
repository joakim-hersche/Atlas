// Switching the spatial level (brief 4.3). When the shaded metric (or the size / second metric) does
// not exist at the new level, the map falls back to the nearest available headline metric of the same
// theme (else population) and says so in a one-line note, instead of showing an empty map.
import { availableAt, type Base, type MetricMeta } from './data';
import { levelName, ml, t, levelWord } from './i18n.svelte';
import { app } from './state.svelte';

/** Nearest headline metric available at `level`: same theme first (closest in the headline order),
 *  then population, then any headline metric. */
export function fallbackMetric(base: Base, cur: MetricMeta | undefined, level: string): MetricMeta | null {
  const ok = (m: MetricMeta) => !m.hidden && m.headline !== null && m.levels.includes(level);
  const heads = base.metrics.filter(ok).sort((a, b) => a.headline! - b.headline!);
  if (cur) {
    const same = heads.filter((m) => m.theme === cur.theme);
    if (same.length) {
      const h = cur.headline ?? same[0].headline!;
      return same.slice().sort((a, b) => Math.abs(a.headline! - h) - Math.abs(b.headline! - h))[0];
    }
  }
  const pop = base.metas.get('pop_total');
  if (pop && pop.levels.includes(level)) return pop;
  return heads[0] ?? null;
}

export function switchLevel(base: Base, level: string): void {
  if (level === app.level) return;
  const word = levelWord(level);
  const notes: string[] = [];
  const prev = { level: app.level, metric: app.metric, metricB: app.metricB, size: app.size };
  const swap = (id: string | null, key: 'level.note' | 'level.noteSize'): string | null => {
    const m = id ? base.metas.get(id) : undefined;
    if (!m || availableAt(m, level)) return id;
    const f = fallbackMetric(base, m, level);
    if (!f) return id;
    notes.push(t(key, { metric: ml(m), level: word, fallback: ml(f) }));
    return f.id;
  };
  app.metric = swap(app.metric, 'level.note') ?? app.metric;
  if (app.route === 'compare') app.metricB = swap(app.metricB, 'level.note');
  else if (app.size) app.size = swap(app.size, 'level.noteSize');
  app.setLevel(level);
  app.levelNote = notes.length ? { text: notes.join(' '), level, metric: app.metric, prev } : null;
}

/** The note of the last level switch, while its level and metric are still shown. */
export function currentLevelNote(): string | null {
  const n = app.levelNote;
  return n && n.level === app.level && n.metric === app.metric ? n.text : null;
}

/** Undo the last level switch that replaced a metric: back to the previous level and metrics. */
export function switchBack(): void {
  const n = app.levelNote;
  if (!n) return;
  app.levelNote = null;
  app.metric = n.prev.metric;
  app.metricB = n.prev.metricB;
  app.size = n.prev.size;
  app.setLevel(n.prev.level);
}
