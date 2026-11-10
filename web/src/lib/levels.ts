// Switching the spatial level (brief 4.3). The user's metric wins: when the shaded metric does not
// exist at the new level, nothing changes and a one-line question offers to show that level with the
// nearest available headline metric of the same theme (else population), or to stay. A size / second
// metric that does not exist there is replaced with a note and "switch back".
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

const MAP_LEVELS = ['gemeinde', 'bezirk', 'kanton', 'grossregion', 'sprachgebiet', 'agglomeration', 'arbeitsmarktgebiet', 'stadt_land'];

/** Map levels where the metric exists (for the level switch and the question text). */
export function levelsOf(m: MetricMeta | undefined): string[] {
  return m ? MAP_LEVELS.filter((l) => availableAt(m, l)) : MAP_LEVELS;
}

/** Level picked in the level switch: switch, or ask first when the shaded metric does not exist there. */
export function requestLevel(base: Base, level: string): void {
  app.levelAsk = null;
  if (level === app.level) return;
  const m = base.metas.get(app.metric);
  if (m && !availableAt(m, level)) {
    app.levelAsk = { level, metric: app.metric, fallback: fallbackMetric(base, m, level)?.id ?? null };
    return;
  }
  switchLevel(base, level);
}

/** The pending question, while the metric it is about is still shaded. */
export function currentAsk(): { level: string; metric: string; fallback: string | null } | null {
  const a = app.levelAsk;
  return a && a.metric === app.metric ? a : null;
}

/** Answer "show that level anyway": swap to the fallback metric and switch (with "switch back"). */
export function confirmAsk(base: Base): void {
  const a = app.levelAsk;
  app.levelAsk = null;
  if (a) switchLevel(base, a.level);
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
