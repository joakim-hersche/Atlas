<script lang="ts" module>
  import { addStrings } from '../lib/i18n.svelte';
  addStrings(
    {
      'sim.edit': 'Choose metrics and weights',
      'sim.editClose': 'Close the editor',
      'sim.custom': 'Custom',
      'sim.reset': 'Back to the default metrics',
      'sim.metrics': 'Metrics compared',
      'sim.weight': 'Weight of {m}',
      'sim.w': 'Weight',
      'sim.log': 'log',
      'sim.logT': 'Compare on a log scale (for skewed values: density, jobs, income)',
      'sim.remove': 'Remove {m}',
      'sim.add': 'Add a metric',
      'sim.addPh': 'Search metrics to add',
      'sim.addNone': 'No metric matches.',
      'sim.noValue': 'no value here',
      'sim.addMax': 'At most {n} metrics.',
      'sim.addDup': 'already in the list',
      'sim.minTwo': 'At least two metrics are needed.',
      'sim.skipped': 'No value for this place, so not compared: {list}.',
      'sim.corr': 'Move together (|r| ≥ 0.8): {list}. Each pair counts almost twice in the distance; lower a weight to compensate.',
      'sim.method': 'Distance = root mean square of the z-score differences, each metric counted by its weight (weight 2 = twice). z-scores are measured against all {units} with a value.',
      'sim.nearOn': 'Only places near …',
      'sim.within': 'within',
      'sim.of': 'of',
      'sim.self': 'this place',
      'sim.other': 'another place …',
      'sim.hubs': 'Hubs',
      'sim.byPT': 'min by public transport',
      'sim.byCar': 'min by car',
      'sim.km': 'km',
      'sim.anchor': 'Near what',
      'sim.mode': 'Measured by',
      'sim.amount': 'Distance or time',
      'sim.pickPlace': 'Search a {unit} to measure from',
      'sim.pickWrong': 'Pick a {unit} here (this list compares {units}).',
      'sim.change': 'change',
      'sim.nearKmNote': 'Straight-line distance between label points of the {units}.',
      'sim.nearPtNote': 'Timetable time from the main station of the municipality to the hub (as on the map).',
      'sim.nearCarNote': 'Car time to the hub (free-flow estimate, as on the map).',
      'sim.pool': '{n} {units} within {r} of {where}.',
      'sim.nearLoading': 'Loading distances …',
      'sim.nearNone': 'No distances for this choice.',
      'sim.none': 'No similar places found with these settings.',
      'sim.more': 'Show more',
      'sim.fewer': 'Show fewer',
      'sim.why': 'Why',
      'sim.whyOpen': 'Why {name} is similar',
      'sim.alike': 'Alike',
      'sim.differs': 'Differs',
      'sim.driverHead': 'Each metric: this place → {name}, difference in standard deviations, share of the distance.',
      'sim.sd': 'SD',
      'sim.share': 'share of the distance',
      'sim.n': '{n} metrics compared',
      'sim.dist': 'Distance: 0 is identical on these metrics; two places picked at random are about 1.4 apart.',
      'sim.distT': 'Distance: weighted root mean square of the z-score differences',
      'sim.used': 'Compared: {list}.',
      'is.title': 'In short',
      'is.all': 'all other Swiss {units}',
      'is.pct': '{p} % of Swiss {units}',
      'is.size.hi': 'Larger than {than} ({v} residents, {y})',
      'is.size.lo': 'Smaller than {than} ({v} residents, {y})',
      'is.size.mid': 'Close to the median in size ({v} residents, {y}; median {m})',
      'is.age.hi': 'Older population than {than} (aged 65 or over: {v}, {y})',
      'is.age.lo': 'Younger population than {than} (aged 65 or over: {v}, {y})',
      'is.age.mid': 'Close to the median in age (aged 65 or over: {v}, {y}; median {m})',
      'is.l.de': 'German-speaking',
      'is.l.fr': 'French-speaking',
      'is.l.it': 'Italian-speaking',
      'is.lg.de': 'German',
      'is.lg.fr': 'French',
      'is.lg.it': 'Italian',
      'is.lang.one': 'Mostly {l}: {v} named it their main language ({y})',
      'is.lang.mix': 'Several languages: {a} {x}, {b} {z} as main language ({y})',
      'is.g.hi': '{label}: {v} ({y}), higher than in {than}',
      'is.g.lo': '{label}: {v} ({y}), lower than in {than}',
      'is.train': 'train',
      'is.pt': 'public transport',
      'is.travel': '{m} min to {hub} by {mode}',
      'is.travelCar': '{m} min to {hub} by {mode}, {c} min by car',
      'is.travelNote': 'from {st}; nearest of {n} hubs by timetable {d}',
      'is.travelNoteDoor': 'door to door; nearest of {n} hubs by timetable {d}',
      'is.travelOwn': '; {hub} is in this municipality and not counted',
      'is.foot': 'Built from the data below with fixed sentences; each figure carries its year. Where a place is close to the middle of the range, nothing is said about it.',
    },
    {
      'sim.edit': 'Kennzahlen und Gewichte wählen',
      'sim.editClose': 'Editor schliessen',
      'sim.custom': 'Eigene Auswahl',
      'sim.reset': 'Zurück zu den Standard-Kennzahlen',
      'sim.metrics': 'Verglichene Kennzahlen',
      'sim.weight': 'Gewicht von {m}',
      'sim.w': 'Gewicht',
      'sim.log': 'log',
      'sim.logT': 'Auf logarithmischer Skala vergleichen (für schiefe Werte: Dichte, Arbeitsplätze, Einkommen)',
      'sim.remove': '{m} entfernen',
      'sim.add': 'Kennzahl hinzufügen',
      'sim.addPh': 'Kennzahlen suchen',
      'sim.addNone': 'Keine Kennzahl gefunden.',
      'sim.noValue': 'hier ohne Wert',
      'sim.addMax': 'Höchstens {n} Kennzahlen.',
      'sim.addDup': 'schon in der Liste',
      'sim.minTwo': 'Mindestens zwei Kennzahlen nötig.',
      'sim.skipped': 'Für diesen Ort ohne Wert, daher nicht verglichen: {list}.',
      'sim.corr': 'Laufen zusammen (|r| ≥ 0,8): {list}. Jedes Paar zählt fast doppelt im Abstand; ein Gewicht zu senken gleicht das aus.',
      'sim.method': 'Abstand = quadratisches Mittel der z-Wert-Differenzen, jede Kennzahl nach ihrem Gewicht (Gewicht 2 = doppelt). Die z-Werte beziehen sich auf alle {units} mit Wert.',
      'sim.nearOn': 'Nur Orte in der Nähe von …',
      'sim.within': 'innerhalb',
      'sim.of': 'von',
      'sim.self': 'diesem Ort',
      'sim.other': 'anderem Ort …',
      'sim.hubs': 'Zentren',
      'sim.byPT': 'Min. mit dem ÖV',
      'sim.byCar': 'Min. mit dem Auto',
      'sim.km': 'km',
      'sim.anchor': 'In der Nähe von',
      'sim.mode': 'Gemessen in',
      'sim.amount': 'Distanz oder Zeit',
      'sim.pickPlace': '{unit} suchen, von der aus gemessen wird',
      'sim.pickWrong': 'Hier eine {unit} wählen (diese Liste vergleicht {units}).',
      'sim.change': 'ändern',
      'sim.nearKmNote': 'Luftlinie zwischen den Beschriftungspunkten der {units}.',
      'sim.nearPtNote': 'Fahrplanzeit vom Hauptbahnhof der Gemeinde zum Zentrum (wie auf der Karte).',
      'sim.nearCarNote': 'Autozeit zum Zentrum (Schätzung bei freier Fahrt, wie auf der Karte).',
      'sim.pool': '{n} {units} innerhalb {r} von {where}.',
      'sim.nearLoading': 'Distanzen werden geladen …',
      'sim.nearNone': 'Keine Distanzen für diese Wahl.',
      'sim.none': 'Mit diesen Einstellungen keine ähnlichen Orte gefunden.',
      'sim.more': 'Mehr zeigen',
      'sim.fewer': 'Weniger zeigen',
      'sim.why': 'Warum',
      'sim.whyOpen': 'Warum {name} ähnlich ist',
      'sim.alike': 'Ähnlich',
      'sim.differs': 'Unterschied',
      'sim.driverHead': 'Je Kennzahl: dieser Ort → {name}, Differenz in Standardabweichungen, Anteil am Abstand.',
      'sim.sd': 'SD',
      'sim.share': 'Anteil am Abstand',
      'sim.n': '{n} Kennzahlen verglichen',
      'sim.dist': 'Abstand: 0 ist auf diesen Kennzahlen identisch; zwei zufällig gewählte Orte liegen etwa 1,4 auseinander.',
      'sim.distT': 'Abstand: gewichtetes quadratisches Mittel der z-Wert-Differenzen',
      'sim.used': 'Verglichen: {list}.',
      'is.title': 'Kurz gesagt',
      'is.all': 'alle anderen Schweizer {units}',
      'is.pct': '{p} % der Schweizer {units}',
      'is.size.hi': 'Grösser als {than} ({v} Einwohner, {y})',
      'is.size.lo': 'Kleiner als {than} ({v} Einwohner, {y})',
      'is.size.mid': 'Etwa so gross wie der Median ({v} Einwohner, {y}; Median {m})',
      'is.age.hi': 'Ältere Bevölkerung als {than} (ab 65 Jahren: {v}, {y})',
      'is.age.lo': 'Jüngere Bevölkerung als {than} (ab 65 Jahren: {v}, {y})',
      'is.age.mid': 'Altersstruktur nahe beim Median (ab 65 Jahren: {v}, {y}; Median {m})',
      'is.l.de': 'deutschsprachig',
      'is.l.fr': 'französischsprachig',
      'is.l.it': 'italienischsprachig',
      'is.lg.de': 'Deutsch',
      'is.lg.fr': 'Französisch',
      'is.lg.it': 'Italienisch',
      'is.lang.one': 'Mehrheitlich {l}: {v} nannten es als Hauptsprache ({y})',
      'is.lang.mix': 'Mehrere Sprachen: {a} {x}, {b} {z} als Hauptsprache ({y})',
      'is.g.hi': '{label}: {v} ({y}), höher als in {than}',
      'is.g.lo': '{label}: {v} ({y}), tiefer als in {than}',
      'is.train': 'Bahn',
      'is.pt': 'ÖV',
      'is.travel': '{m} Min. nach {hub} mit {mode}',
      'is.travelCar': '{m} Min. nach {hub} mit {mode}, {c} Min. mit dem Auto',
      'is.travelNote': 'ab {st}; nächstes von {n} Zentren, Fahrplan {d}',
      'is.travelNoteDoor': 'Haustür zu Haustür; nächstes von {n} Zentren, Fahrplan {d}',
      'is.travelOwn': '; {hub} liegt in dieser Gemeinde und zählt nicht mit',
      'is.foot': 'Aus den Daten unten mit festen Sätzen gebildet; jede Zahl nennt ihr Jahr. Liegt ein Ort nahe der Mitte der Verteilung, wird dazu nichts gesagt.',
    },
  );
  let uid = 0;
</script>

<script lang="ts">
  // "Similar places" of the profile page: nearest units by weighted z-scores. The reader can choose the
  // metrics and their weights (kept in the URL as `sm`), restrict the result to places near a place or hub
  // (`nr`), and open any match to see which metrics make it similar (or different). See lib/similar.ts.
  import Search from './Search.svelte';
  import { fmtNumber, fmtValue } from '../lib/classify';
  import { loadTheme, placeName, type Base, type ColumnFile, type UnitRow } from '../lib/data';
  import { levelName, levelWord, ml, t, themeName } from '../lib/i18n.svelte';
  import { hrefFor } from '../lib/nav';
  import { parseRef, refOf, type ReachTimes } from '../lib/places';
  import type { PlaceLevel } from '../lib/profile';
  import {
    columnOf, correlatedPairs, DEFAULT_SIM, isDefaultSim, looksSkewed, MAX_SIM_METRICS, NEAR_MAX, nearDistances, parseNear, parseSim,
    serializeNear, serializeSim, similarPlaces, simCandidates, W_MAX, W_MIN, W_STEP, type Near, type SimMetric,
  } from '../lib/similar';
  import { app } from '../lib/state.svelte';
  import Term from './Term.svelte';

  interface Props {
    base: Base;
    pl: PlaceLevel;
    idx: number;
    rows: Map<string, UnitRow> | null;
    reach: ReachTimes | null;
  }
  let { base, pl, idx, rows, reach }: Props = $props();

  const level = $derived(pl.level);
  const units = $derived(levelWord(level));
  const unitOne = $derived(levelName(level, false));
  const spec = $derived<SimMetric[]>(parseSim(app.params.sm) ?? DEFAULT_SIM);
  const custom = $derived(!isDefaultSim(spec));
  const near = $derived.by<Near | null>(() => {
    const n = parseNear(app.params.nr);
    // hubs only exist for municipalities
    return n && (n.mode === 'km' || level === 'gemeinde') ? n : null;
  });

  /** theme files loaded for the metrics outside the core file */
  let files = $state.raw<Record<string, ColumnFile>>({});
  let filesLevel = '';
  $effect(() => {
    if (filesLevel !== pl.level) {
      filesLevel = pl.level;
      files = {};
    }
    const lv = pl.level;
    for (const m of spec) {
      const f = base.metas.get(m.id)?.file;
      if (f && f !== 'core' && !files[f]) {
        loadTheme(lv, f, pl.core)
          .then((cf) => {
            if (pl.level === lv) files = { ...files, [f]: cf };
          })
          .catch(() => {});
      }
    }
  });

  function setParams(patch: Record<string, string | null>) {
    const next = { ...app.params };
    for (const [k, v] of Object.entries(patch)) {
      if (v === null) delete next[k];
      else next[k] = v;
    }
    app.params = next;
  }
  function setSpec(s: SimMetric[]) {
    setParams({ sm: isDefaultSim(s) ? null : serializeSim(s) });
  }
  function setNear(n: Near | null) {
    setParams({ nr: n ? serializeNear(n) : null });
  }

  // ---------------------------------------------------------------- near
  const dist = $derived(near ? nearDistances(pl, idx, near, rows, reach) : null);
  const nearReady = $derived(!near || (near.mode === 'km' ? !!rows : !!reach));
  const allow = $derived(near && dist ? (j: number) => dist[j] !== null && (dist[j] as number) <= near.n : undefined);
  const nearWhere = $derived.by(() => {
    if (!near) return '';
    if (near.anchor === 'self') return t('sim.self');
    if (near.anchor.startsWith('h-')) return reach?.hubs.find(([s]) => s === near.anchor.slice(2))?.[1] ?? near.anchor.slice(2);
    const id = near.anchor.slice(2);
    return placeName(level, id, rows?.get(refOf(level, id))?.name ?? id);
  });
  const nearUnit = (n: Near) => (n.mode === 'km' ? t('sim.km') : 'min');

  // ---------------------------------------------------------------- result
  let more = $state(false);
  const sim = $derived(similarPlaces(pl, idx, { spec, files, allow, k: more ? 15 : 6 }));
  const hasMoreRoom = $derived(sim.list.length >= 6);
  const corr = $derived(correlatedPairs(pl, spec, files));
  const lbl = (id: string) => ml(base.metas.get(id)) || id;
  let openRow = $state<number | null>(null);
  $effect(() => {
    void idx; void app.params.sm; void app.params.nr;
    openRow = null;
  });

  const keep = $derived.by(() => {
    const k: Record<string, string> = {};
    if (app.params.sm) k.sm = app.params.sm;
    if (app.params.nr) k.nr = app.params.nr;
    return k;
  });
  const hrefTo = (j: number) => hrefFor('profile', { id: refOf(level, pl.units[j]), ...keep });
  const near1 = (j: number) => (dist && dist[j] !== null ? (dist[j] as number) : null);

  /** per match: the metrics it is closest on, and the one or two that add most to the distance */
  function alike(parts: { id: string; dz: number }[]) {
    return [...parts].sort((a, b) => a.dz - b.dz).slice(0, 3).map((p) => lbl(p.id));
  }
  function differs(parts: { id: string; share: number; dz: number }[]) {
    return [...parts].filter((p) => p.dz >= 0.5).sort((a, b) => b.share - a.share).slice(0, 2).map((p) => lbl(p.id));
  }

  // ---------------------------------------------------------------- editor
  let editing = $state(false);
  let q = $state('');
  let addMsg = $state('');
  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const cands = $derived(simCandidates(base.metrics, level).map((m) => ({ m, key: norm(`${m.label_en} ${m.label_de} ${m.label_fr ?? ''} ${m.id} ${m.theme}`) })));
  const results = $derived.by(() => {
    const words = norm(q).split(/\s+/).filter(Boolean);
    if (!words.length) return [];
    return cands.filter((c) => words.every((w) => c.key.includes(w))).map((c) => c.m)
      .sort((a, b) => (a.headline ?? 1e9) - (b.headline ?? 1e9) || ml(a).localeCompare(ml(b))).slice(0, 12);
  });
  function setW(id: string, w: number) {
    setSpec(spec.map((m) => (m.id === id ? { ...m, w: Math.max(W_MIN, Math.min(W_MAX, w)) } : m)));
  }
  function setLog(id: string, log: boolean) {
    setSpec(spec.map((m) => (m.id === id ? { ...m, log } : m)));
  }
  function remove(id: string) {
    if (spec.length <= 2) {
      addMsg = t('sim.minTwo');
      return;
    }
    addMsg = '';
    setSpec(spec.filter((m) => m.id !== id));
  }
  async function add(id: string) {
    addMsg = '';
    if (spec.some((m) => m.id === id)) {
      addMsg = `${lbl(id)}: ${t('sim.addDup')}`;
      return;
    }
    if (spec.length >= MAX_SIM_METRICS) {
      addMsg = t('sim.addMax', { n: MAX_SIM_METRICS });
      return;
    }
    const meta = base.metas.get(id);
    let log = false;
    if (meta) {
      try {
        const f = meta.file === 'core' ? pl.core : (files[meta.file] ?? (await loadTheme(pl.level, meta.file, pl.core)));
        if (meta.file !== 'core' && !files[meta.file]) files = { ...files, [meta.file]: f };
        const c = f.metrics[id] ?? columnOf(pl, files, id);
        log = !!c && looksSkewed(c.v);
      } catch {
        /* the column loads in the effect; compare linearly until then */
      }
    }
    setSpec([...spec, { id, w: 1, log }]);
    q = '';
  }

  // ---------------------------------------------------------------- near editor
  let picking = $state(false);
  let pickMsg = $state('');
  const hubOptions = $derived(level === 'gemeinde' && reach ? reach.hubs : []);
  const anchorSel = $derived(!near ? 'self' : near.anchor.startsWith('p-') ? 'other' : near.anchor);
  function onAnchor(v: string) {
    pickMsg = '';
    const cur = near;
    if (v === 'other') {
      picking = true;
      return;
    }
    picking = false;
    if (v === 'self') setNear({ anchor: 'self', mode: 'km', n: cur?.mode === 'km' ? cur.n : 20 });
    else setNear({ anchor: v, mode: cur && cur.mode !== 'km' ? cur.mode : 'pt', n: cur && cur.mode !== 'km' ? cur.n : 45 });
  }
  function onPick(ref: string) {
    const r = parseRef(ref);
    if (r.level !== level) {
      pickMsg = t('sim.pickWrong', { units, unit: unitOne });
      return;
    }
    pickMsg = '';
    picking = false;
    setNear({ anchor: `p-${r.id}`, mode: 'km', n: near?.mode === 'km' ? near.n : 20 });
  }
  function onN(v: string) {
    const n = Number(v);
    if (!near || !Number.isFinite(n) || n <= 0) return;
    setNear({ ...near, n: Math.min(n, NEAR_MAX[near.mode]) });
  }
  function toggleNear(on: boolean) {
    picking = false;
    pickMsg = '';
    if (!on) setNear(null);
    else setNear({ anchor: 'self', mode: 'km', n: 20 });
  }
  const nearTip = $derived(near ? (near.mode === 'km' ? t('sim.nearKmNote', { units }) : near.mode === 'pt' ? t('sim.nearPtNote') : t('sim.nearCarNote')) : '');
  const usedLabels = $derived(sim.used.map(lbl).join(', '));
</script>

<div class="sp">
  <div class="bar">
    <button type="button" class="more" aria-expanded={editing} onclick={() => (editing = !editing)}>{editing ? t('sim.editClose') : t('sim.edit')}</button>
    {#if custom}<span class="badge">{t('sim.custom')}</span>{/if}
  </div>

  {#if editing}
    <div class="ed">
      <div class="caps">{t('sim.metrics')}</div>
      <ul class="mlist">
        {#each spec as m (m.id)}
          <li>
            <span class="mn">{lbl(m.id)}{#if sim.skipped.includes(m.id)}<span class="miss"> – {t('sim.noValue')}</span>{/if}</span>
            <div class="ctl">
              <input type="range" min={W_MIN} max={W_MAX} step={W_STEP} value={m.w} aria-label={t('sim.weight', { m: lbl(m.id) })}
                oninput={(e) => setW(m.id, Number(e.currentTarget.value))} />
              <output class="num">×{fmtNumber(m.w, m.w % 1 ? 1 : 0)}</output>
              <label class="lg" title={t('sim.logT')}><input type="checkbox" checked={m.log} onchange={(e) => setLog(m.id, e.currentTarget.checked)} />{t('sim.log')}</label>
              <button type="button" class="x" aria-label={t('sim.remove', { m: lbl(m.id) })} onclick={() => remove(m.id)}>
                <svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.5" /></svg>
              </button>
            </div>
          </li>
        {/each}
      </ul>
      <div class="add">
        <input type="search" bind:value={q} placeholder={t('sim.addPh')} aria-label={t('sim.add')} autocomplete="off" />
        {#if q.trim()}
          <ul class="res">
            {#each results as m (m.id)}
              <li><button type="button" onclick={() => add(m.id)}><span>{ml(m)}</span><span class="rm">{themeName(m.theme)}</span></button></li>
            {:else}
              <li class="rm pad">{t('sim.addNone')}</li>
            {/each}
          </ul>
        {/if}
        {#if addMsg}<p class="foot warn" role="status">{addMsg}</p>{/if}
      </div>
      {#if custom}<button type="button" class="link" onclick={() => setSpec(DEFAULT_SIM)}>{t('sim.reset')}</button>{/if}
      {#if sim.skipped.length}
        <p class="foot">{t('sim.skipped', { list: sim.skipped.map(lbl).join(', ') })}</p>
      {/if}
      {#if corr.length}
        <p class="foot">{t('sim.corr', { list: corr.slice(0, 4).map((c) => `${lbl(c.a)} ↔ ${lbl(c.b)} (${fmtNumber(c.r, 2)})`).join('; ') })}</p>
      {/if}
      <p class="foot">{t('sim.method', { units })}<Term k="z_score_similarity" /></p>
    </div>
  {/if}

  <div class="near">
    <label class="on"><input type="checkbox" checked={!!near} onchange={(e) => toggleNear(e.currentTarget.checked)} />{t('sim.nearOn')}</label>
    {#if near || picking}
      <div class="nrow">
        <span class="w">{t('sim.within')}</span>
        {#if near}
          <input class="n num" type="number" inputmode="numeric" min="1" max={NEAR_MAX[near.mode]} value={near.n} aria-label={t('sim.amount')}
            onchange={(e) => onN(e.currentTarget.value)} />
        {/if}
        {#if near && near.mode !== 'km'}
          <select aria-label={t('sim.mode')} value={near.mode} onchange={(e) => near && setNear({ ...near, mode: e.currentTarget.value as 'pt' | 'car' })}>
            <option value="pt">{t('sim.byPT')}</option>
            <option value="car">{t('sim.byCar')}</option>
          </select>
        {:else}
          <span class="w">{t('sim.km')}</span>
        {/if}
        <span class="w">{t('sim.of')}</span>
        <select aria-label={t('sim.anchor')} value={anchorSel} onchange={(e) => onAnchor(e.currentTarget.value)}>
          <option value="self">{t('sim.self')}</option>
          {#if near?.anchor.startsWith('p-')}<option value="other">{nearWhere}</option>{:else}<option value="other">{t('sim.other')}</option>{/if}
          {#if hubOptions.length}
            <optgroup label={t('sim.hubs')}>
              {#each hubOptions as [slug, hub]}<option value={'h-' + slug}>{hub}</option>{/each}
            </optgroup>
          {/if}
        </select>
        {#if near?.anchor.startsWith('p-') && !picking}<button type="button" class="link" onclick={() => (picking = true)}>{t('sim.change')}</button>{/if}
      </div>
      {#if picking}
        <div class="pick">
          <Search variant="inline" onpick={onPick} placeholder={t('sim.pickPlace', { unit: unitOne })} />
          {#if pickMsg}<p class="foot warn" role="status">{pickMsg}</p>{/if}
        </div>
      {/if}
      {#if near}<p class="foot">{nearTip}</p>{/if}
    {/if}
  </div>

  {#if near && !nearReady}
    <p class="foot">{t('sim.nearLoading')}</p>
  {:else if near && !dist}
    <p class="foot">{t('sim.nearNone')}</p>
  {:else}
    {#if near}
      <p class="pool foot">{t('sim.pool', { n: fmtNumber(sim.pool, 0), units, r: `${fmtNumber(near.n, 0)} ${nearUnit(near)}`, where: nearWhere })}</p>
    {/if}
    {#if sim.list.length}
      <p class="dh foot">{t('sim.dist')}</p>
      <ol class="sim">
        {#each sim.list as s (s.i)}
          {@const open = openRow === s.i}
          {@const nm = placeName(level, pl.units[s.i], pl.name[s.i])}
          <li class:open>
            <div class="l1">
              <a href={hrefTo(s.i)}>{nm}</a>{#if pl.canton[s.i] && level === 'gemeinde'}<span class="muted"> {pl.canton[s.i]}</span>{/if}
              {#if near1(s.i) !== null}<span class="nd num muted">{fmtNumber(near1(s.i) as number, near?.mode === 'km' ? 1 : 0)} {near ? nearUnit(near) : ''}</span>{/if}
              <span class="d num" title={t('sim.distT')}>{fmtNumber(s.d, 2)}</span>
            </div>
            <div class="l2 foot">
              {#if alike(s.parts).length}<span><b>{t('sim.alike')}:</b> {alike(s.parts).join(', ')}</span>{/if}
              {#if differs(s.parts).length}<span><b>{t('sim.differs')}:</b> {differs(s.parts).join(', ')}</span>{/if}
              <button type="button" class="why" aria-expanded={open} aria-label={t('sim.whyOpen', { name: nm })} onclick={() => (openRow = open ? null : s.i)}>{t('sim.why')}</button>
            </div>
            {#if open}
              <div class="drv">
                <p class="foot">{t('sim.driverHead', { name: nm })} {t('sim.n', { n: s.n })}.</p>
                <ul>
                  {#each [...s.parts].sort((a, b) => b.share - a.share) as p (p.id)}
                    {@const meta = base.metas.get(p.id)}
                    <li>
                      <span class="pn">{lbl(p.id)}{#if p.w !== 1}<span class="muted"> ×{fmtNumber(p.w, p.w % 1 ? 1 : 0)}</span>{/if}</span>
                      <span class="pv num">{meta ? fmtValue(p.xi, meta) : p.xi} → {meta ? fmtValue(p.xj, meta) : p.xj}</span>
                      <span class="pz num muted">{fmtNumber(p.dz, 1)} {t('sim.sd')}</span>
                      <span class="pbar" role="img" aria-label="{t('sim.share')} {fmtNumber(100 * p.share, 0)} %" title="{t('sim.share')}: {fmtNumber(100 * p.share, 0)} %"><i style="width:{Math.round(100 * p.share)}%"></i></span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}
          </li>
        {/each}
      </ol>
      {#if hasMoreRoom}
        <button type="button" class="link" onclick={() => (more = !more)}>{more ? t('sim.fewer') : t('sim.more')}</button>
      {/if}
      <p class="foot">{t('sim.used', { list: usedLabels })}</p>
    {:else}
      <p class="foot">{sim.used.length < 2 ? t('p.similarNone') : t('sim.none')}</p>
    {/if}
  {/if}
</div>

<style>
  .sp { margin-top: 4px; }
  .bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
  .more {
    border: 1px solid var(--ink); background: none; padding: 4px 10px; font-size: 0.76rem; font-weight: 600; cursor: pointer; color: var(--text);
  }
  .more[aria-expanded='true'] { background: var(--ink); color: var(--ink-text); }
  .badge { font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; background: var(--accent); color: var(--accent-text); padding: 2px 6px; }
  .link { border: 0; background: none; padding: 4px 0; font-size: 0.78rem; text-decoration: underline; text-underline-offset: 2px; cursor: pointer; color: var(--text); }
  .muted { color: var(--muted); }
  .warn { color: var(--accent); }

  .ed { margin-top: 8px; padding: 8px 10px 10px; border: 1px solid var(--border); background: var(--panel-2); }
  .mlist { list-style: none; margin: 4px 0 8px; padding: 0; }
  .mlist li { padding: 6px 0; border-bottom: 1px solid var(--border); }
  .mn { display: block; font-size: 0.8rem; font-weight: 600; line-height: 1.25; }
  .miss { font-weight: 400; color: var(--muted); }
  .ctl { display: flex; align-items: center; gap: 8px; margin-top: 3px; }
  .ctl input[type='range'] { flex: 1; min-width: 0; height: 28px; accent-color: var(--ink); }
  .ctl output { width: 2.6em; text-align: right; font-size: 0.78rem; }
  .lg { display: inline-flex; align-items: center; gap: 3px; font-size: 0.72rem; color: var(--muted); white-space: nowrap; min-height: 32px; }
  .lg input { width: 16px; height: 16px; accent-color: var(--ink); }
  .x { flex: none; display: grid; place-items: center; width: 32px; height: 32px; border: 0; background: none; color: var(--text); cursor: pointer; }
  .add input[type='search'], .nrow select, .nrow input {
    height: 36px; padding: 0 8px; border: 1px solid var(--ink); background: var(--panel); font-size: 16px; color: var(--text); border-radius: 0;
  }
  .add input[type='search'] { width: 100%; box-sizing: border-box; }
  .add input::-webkit-search-cancel-button { display: none; }
  .res { list-style: none; margin: 0; padding: 0; border: 1px solid var(--ink); border-top: 0; background: var(--panel); max-height: 240px; overflow-y: auto; }
  .res button { display: flex; flex-direction: column; align-items: flex-start; width: 100%; min-height: 40px; padding: 5px 10px; border: 0; border-bottom: 1px solid var(--border); background: none; text-align: left; cursor: pointer; font-size: 0.82rem; color: var(--text); }
  .res button:hover { background: var(--panel-2); }
  .rm { font-size: 0.7rem; color: var(--muted); }
  .pad { padding: 8px 10px; }

  .near { margin-top: 10px; }
  .on { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 600; min-height: 32px; cursor: pointer; }
  .on input { width: 18px; height: 18px; accent-color: var(--ink); }
  .nrow { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 2px; font-size: 0.82rem; }
  .nrow .n { width: 4.6em; }
  .nrow select { max-width: 100%; }
  .pick { margin-top: 6px; }

  .pool { margin: 8px 0 0; }
  .dh { margin: 6px 0 0; }
  .sim { list-style: none; margin: 6px 0 0; padding: 0; font-size: 0.84rem; }
  .sim > li { padding: 5px 0; border-bottom: 1px solid var(--border); }
  .l1 { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; }
  .nd { font-size: 0.72rem; }
  .d { margin-left: auto; color: var(--muted); font-size: 0.74rem; }
  .l2 { display: flex; flex-wrap: wrap; gap: 0 10px; margin-top: 1px; align-items: baseline; }
  .l2 b { font-weight: 600; color: var(--text); }
  .why { margin-left: auto; border: 0; background: none; padding: 4px 0; font-size: 0.72rem; text-decoration: underline; text-underline-offset: 2px; cursor: pointer; color: var(--text); min-height: 28px; }
  .why[aria-expanded='true'] { font-weight: 700; }
  .drv { margin: 2px 0 4px; padding: 6px 8px; background: var(--panel-2); }
  .drv p { margin: 0 0 4px; }
  .drv ul { list-style: none; margin: 0; padding: 0; }
  .drv li { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: 'n n' 'v z' 'b b'; gap: 1px 8px; padding: 4px 0; border-top: 1px solid var(--border); font-size: 0.76rem; align-items: center; }
  .pn { grid-area: n; min-width: 0; overflow-wrap: anywhere; }
  .pv { grid-area: v; text-align: left; min-width: 0; overflow-wrap: anywhere; }
  .pz { grid-area: z; text-align: right; font-size: 0.7rem; }
  .pbar { grid-area: b; display: block; height: 6px; background: var(--border); }
  .pbar i { display: block; height: 100%; background: var(--accent); }
  .sp :global(.foot) { margin: 6px 0 0; }
  @media (min-width: 900px) {
    .add input[type='search'], .nrow select, .nrow input { height: 32px; font-size: 0.82rem; }
  }
</style>
