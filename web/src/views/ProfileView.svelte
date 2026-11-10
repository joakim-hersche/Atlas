<script lang="ts" module>
  import { addStrings, levelWord } from '../lib/i18n.svelte';
  addStrings(
    {
      'p.back': 'Map',
      'p.showOnMap': 'Show on map',
      'p.compareWith': 'Compare with other places',
      'p.notFound': 'No place with the id “{id}”.',
      'p.population': 'Population',
      'p.area': 'Area',
      'p.landArea': 'Land area',
      'p.inclLakes': '{a} incl. lakes',
      'p.noLakes': 'without lakes',
      'p.densSub': 'per km² land area',
      'p.elevation': 'Elevation',
      'p.elevRange': 'lowest {lo} · highest {hi}',
      'p.density': 'Density',
      'p.mean': 'mean',
      'p.canton': 'Canton',
      'p.district': 'District',
      'p.type': 'Municipality type',
      'p.urbanRural': 'Urban / rural',
      'p.agglo': 'Agglomeration',
      'p.amr': 'Labour market area',
      'p.grossregion': 'Major region',
      'p.lang': 'Language region',
      'p.bfs': 'BFS no.',
      'p.members': 'Municipalities',
      'p.website': 'Official website',
      'p.wikipedia': 'Wikipedia',
      'p.coa': 'Coat of arms',
      'p.coaNote': 'Wikimedia Commons, {lic}',
      'p.wikidata': 'Wikidata',
      'p.links': 'Links',
      'p.partOf': 'Part of',
      'p.otherNames': 'Other names',
      'p.metrics': 'All metrics',
      'p.rankNote': 'Rank 1 = highest value (lowest where lower is better). Equal values share the best rank and are marked “tied”. The red mark shows the percentile among all {units} with data; a pale band spans a tie group.',
      'p.showAll': 'All {n} metrics',
      'p.showLess': 'Headline metrics only',
      'p.moreN': '{n} more',
      'p.loadingTheme': 'Loading…',
      'p.noData': 'No data',
      'p.rankCH': 'Rank {r} of {n}',
      'p.rankKt': '{r} of {n} in {kt}',
      'p.withData': 'with data',
      'p.partial': 'partial: {n} of 26 cantons',
      'p.reach': 'Travel time to the hubs',
      'p.reachPT': 'PT',
      'p.reachCar': 'Car',
      'p.reachHub': 'Hub',
      'p.reachSt': 'Station',
      'p.reachDoor': 'Door',
      'p.fromStation': 'Public transport from {st} station towards each hub, in minutes.',
      'p.fromStationOut': 'No station in this municipality: public transport from {st}, the nearest station, towards each hub, in minutes.',
      'p.noStation': 'No stop in this municipality: station times are not available.',
      'p.fromStop': 'Public transport from {st}, the main stop (no rail station serves more residents), towards each hub, in minutes.',
      'p.theHub': 'the hub',
      'p.reachDate': 'Timetable of {d}.',
      'p.reachNone': '–',
      'p.reachNoneNote': '– = no travel time in the data for this municipality.',
      'p.reachHigher': 'Travel times are computed per municipality; open a municipality of this {one} for its times.',
      'p.neighbours': 'Neighbours',
      'p.noNeighbours': 'No neighbours at this level.',
      'p.similar': 'Similar places',
      'p.similarNote': 'Nearest {units} by z-scores of: {list}. Log scale for density, jobs and income; missing values skipped.',
      'p.similarNone': 'Not enough values to compare.',
      'p.distH': 'Number = distance: 0 is identical on these metrics; two places picked at random are about 1.4 apart.',
      'p.distT': 'Distance: root mean square of the z-score differences',
      'p.history': 'Boundary history',
      'p.historyNone': 'No mergers, splits, renames or canton or district changes since 1960.',
      'p.historyOnly': 'Boundary history is recorded for municipalities.',
      'p.historySource': 'Source: BFS historized municipality register, events since {since}.',
      'p.sources': 'Sources and licences',
      'p.gaps': 'How gaps are shown',
      'p.attribution': 'Names and links: Wikidata (CC0). Coats of arms are linked, not shown; licence per file on Wikimedia Commons.',
      'p.contents': 'Contents',
      'p.km2': 'km²',
      'p.notPublished': 'not published at this level',
    },
    {
      'p.back': 'Karte',
      'p.showOnMap': 'Auf der Karte zeigen',
      'p.compareWith': 'Mit anderen Orten vergleichen',
      'p.notFound': 'Kein Ort mit der Kennung «{id}».',
      'p.population': 'Bevölkerung',
      'p.area': 'Fläche',
      'p.landArea': 'Landfläche',
      'p.inclLakes': '{a} mit Seen',
      'p.noLakes': 'ohne Seen',
      'p.densSub': 'Einw. pro km² Landfläche',
      'p.elevation': 'Höhe',
      'p.elevRange': 'tiefster Punkt {lo} · höchster {hi}',
      'p.density': 'Dichte',
      'p.mean': 'Mittel',
      'p.canton': 'Kanton',
      'p.district': 'Bezirk',
      'p.type': 'Gemeindetyp',
      'p.urbanRural': 'Stadt/Land',
      'p.agglo': 'Agglomeration',
      'p.amr': 'Arbeitsmarktgebiet',
      'p.grossregion': 'Grossregion',
      'p.lang': 'Sprachgebiet',
      'p.bfs': 'BFS-Nr.',
      'p.members': 'Gemeinden',
      'p.website': 'Offizielle Website',
      'p.wikipedia': 'Wikipedia',
      'p.coa': 'Wappen',
      'p.coaNote': 'Wikimedia Commons, {lic}',
      'p.wikidata': 'Wikidata',
      'p.links': 'Links',
      'p.partOf': 'Gehört zu',
      'p.otherNames': 'Weitere Namen',
      'p.metrics': 'Alle Kennzahlen',
      'p.rankNote': 'Rang 1 = höchster Wert (tiefster, wo tiefer besser ist). Gleiche Werte teilen sich den besten Rang und sind als «gleichauf» markiert. Die rote Marke zeigt das Perzentil unter allen {units} mit Daten; ein heller Balken umfasst gleichauf liegende Werte.',
      'p.showAll': 'Alle {n} Kennzahlen',
      'p.showLess': 'Nur Hauptkennzahlen',
      'p.moreN': '{n} weitere',
      'p.loadingTheme': 'Wird geladen…',
      'p.noData': 'Keine Daten',
      'p.rankCH': 'Rang {r} von {n}',
      'p.rankKt': '{r} von {n} in {kt}',
      'p.withData': 'mit Daten',
      'p.partial': 'teilweise: {n} von 26 Kantonen',
      'p.reach': 'Reisezeit zu den Zentren',
      'p.reachPT': 'ÖV',
      'p.reachCar': 'Auto',
      'p.reachHub': 'Zentrum',
      'p.reachSt': 'Bahnhof',
      'p.reachDoor': 'Tür',
      'p.fromStation': 'ÖV ab Bahnhof {st} zu jedem Zentrum, in Minuten.',
      'p.fromStationOut': 'Kein Bahnhof in dieser Gemeinde: ÖV ab {st}, dem nächsten Bahnhof, zu jedem Zentrum, in Minuten.',
      'p.noStation': 'Keine Haltestelle in dieser Gemeinde: keine Bahnhofzeiten.',
      'p.fromStop': 'ÖV ab {st}, der wichtigsten Haltestelle (kein Bahnhof erschliesst mehr Einwohner), zu jedem Zentrum, in Minuten.',
      'p.theHub': 'das Zentrum',
      'p.reachDate': 'Fahrplan vom {d}.',
      'p.reachNone': '–',
      'p.reachNoneNote': '– = keine Reisezeit in den Daten für diese Gemeinde.',
      'p.reachHigher': 'Reisezeiten gibt es pro Gemeinde; Gemeinden dieser Einheit ({one}) öffnen.',
      'p.neighbours': 'Nachbarn',
      'p.noNeighbours': 'Keine Nachbarn auf dieser Ebene.',
      'p.similar': 'Ähnliche Orte',
      'p.similarNote': 'Nächste {units} nach z-Werten von: {list}. Dichte, Arbeitsplätze und Einkommen logarithmiert; fehlende Werte übersprungen.',
      'p.similarNone': 'Zu wenige Werte für einen Vergleich.',
      'p.distH': 'Zahl = Abstand: 0 ist auf diesen Kennzahlen identisch; zwei zufällig gewählte Orte liegen etwa 1,4 auseinander.',
      'p.distT': 'Abstand: quadratisches Mittel der Differenzen der z-Werte',
      'p.history': 'Gebietsgeschichte',
      'p.historyNone': 'Seit 1960 keine Fusionen, Teilungen, Umbenennungen, Kantons- oder Bezirkswechsel.',
      'p.historyOnly': 'Die Gebietsgeschichte wird für Gemeinden geführt.',
      'p.historySource': 'Quelle: BFS, Historisiertes Gemeindeverzeichnis, Ereignisse seit {since}.',
      'p.sources': 'Quellen und Lizenzen',
      'p.gaps': 'Wie Lücken gezeigt werden',
      'p.attribution': 'Namen und Links: Wikidata (CC0). Wappen sind verlinkt, nicht eingebunden; Lizenz je Datei auf Wikimedia Commons.',
      'p.contents': 'Inhalt',
      'p.km2': 'km²',
      'p.notPublished': 'auf dieser Ebene nicht publiziert',
    },
  );
  export const HISTORY_DE: Record<string, string> = {
    merger: 'Fusion zu einer neuen Gemeinde',
    absorption: 'Eingemeindung in eine bestehende Gemeinde',
    split: 'Gemeinde geteilt',
    rename: 'umbenannt',
    territory_change: 'Gebietsabtausch zwischen Gemeinden',
    district_change: 'Wechsel in einen anderen Bezirk',
    canton_change: 'Wechsel in einen anderen Kanton',
    renumbering: 'neue BFS-Nummer',
  };
</script>

<script lang="ts">
  // Profile page (brief 6.1, "don't need Google"): one place at any level. Header facts and links,
  // every metric by theme with rank, percentile, sparkline, source and precision tags (gaps with their
  // reason, D21), neighbours, similar places, travel times to the hubs and the boundary history.
  // Data loads on demand: the level's core file (+ geography for area), other theme files when opened.
  import Locator from '../components/Locator.svelte';
  import Search from '../components/Search.svelte';
  import SimilarPlaces from '../components/SimilarPlaces.svelte';
  import Term from '../components/Term.svelte';
  import { glossKeyOf } from '../lib/glossary.svelte';
  import PctBar from '../components/PctBar.svelte';
  import ElectionBar from '../components/ElectionBar.svelte';
  import Sparkline from '../components/Sparkline.svelte';
  import { fmtNumber, fmtPeriod, fmtValue } from '../lib/classify';
  import { coverageLabel, loadTheme, placeName, precisionText, shortName, type Base, type ColumnFile, type MetricMeta, type UnitRow } from '../lib/data';
  import { historyFr, isDe, levelName, ml, t, themeName, tiedText, unitName } from '../lib/i18n.svelte';
  import { hasMap, hrefFor, profileHref, showOnMap, sourceHref } from '../lib/nav';
  import {
    hideAltNames, loadHistory, loadIdentity, loadNeighbours, loadReachTimes, loadRows, loadSearch, parseRef, refOf,
    type HistoryFile, type Identity, type NeighboursFile, type ReachTimes, type SearchIndex,
  } from '../lib/places';
  import { mainStation, methodText, reasonAt } from '../lib/pt';
  import { entryOf, loadPlaceLevel, themeBlocks, type Entry, type PlaceLevel } from '../lib/profile';
  import { inShort } from '../lib/summary';
  import { app } from '../lib/state.svelte';

  interface Props {
    base: Base;
    desktop?: boolean;
  }
  let { base, desktop = false }: Props = $props();

  const ref = $derived(app.params.id ?? '261');
  const unit = $derived(parseRef(ref));

  let pl = $state.raw<PlaceLevel | null>(null);
  let rows = $state.raw<Map<string, UnitRow> | null>(null);
  let files = $state.raw<Record<string, ColumnFile>>({});
  let identity = $state.raw<Identity | null>(null);
  let history = $state.raw<HistoryFile | null>(null);
  let neighbours = $state.raw<NeighboursFile | null>(null);
  let reach = $state.raw<ReachTimes | null>(null);
  let sx = $state.raw<SearchIndex | null>(null);
  let err = $state<string | null>(null);
  let open = $state<Record<string, boolean>>({});
  let scroller = $state<HTMLElement>();

  // level data and the always-needed files of the place's level
  $effect(() => {
    const level = unit.level;
    let live = true;
    pl = null;
    files = {};
    open = {};
    err = null;
    loadPlaceLevel(level)
      .then((p) => {
        if (!live) return;
        pl = p;
        files = { core: p.core };
        need('geography_identity');
      })
      .catch((e) => live && (err = String(e)));
    return () => (live = false);
  });
  $effect(() => {
    void ref;
    scroller?.scrollTo({ top: 0 });
  });
  loadRows().then((r) => (rows = r)).catch(() => {});
  loadSearch().then((s) => (sx = s)).catch(() => {});
  loadIdentity().then((x) => (identity = x)).catch(() => {});
  loadHistory().then((x) => (history = x)).catch(() => {});
  loadNeighbours().then((x) => (neighbours = x)).catch(() => {});
  $effect(() => {
    if (unit.level === 'gemeinde' && !reach) loadReachTimes().then((x) => (reach = x)).catch(() => {});
  });

  function need(file: string) {
    if (!pl || files[file]) return;
    const level = pl.level;
    loadTheme(level, file, pl.core)
      .then((f) => {
        if (pl?.level === level) files = { ...files, [file]: f };
      })
      .catch(() => {
        // a level without this theme file: its metrics show as not published
        if (pl?.level === level) files = { ...files, [file]: { level, units: [], metrics: {}, status_codes: {}, precision_codes: {} } };
      });
  }

  const idx = $derived(pl ? (pl.index.get(unit.id) ?? null) : null);
  const row = $derived(rows?.get(ref));
  const name = $derived(placeName(unit.level, unit.id, pl && idx !== null ? pl.name[idx] : (row?.name ?? unit.id)));
  const blocks = $derived(themeBlocks(base, unit.level));
  const unitsWord = $derived(levelWord(unit.level));

  function entry(m: MetricMeta): Entry | null | undefined {
    if (!pl || idx === null) return undefined;
    const f = files[m.file];
    if (!f) return undefined;
    return entryOf(pl, f, m, idx);
  }
  const val = (id: string) => {
    const m = base.metas.get(id);
    return m ? entry(m) : undefined;
  };

  // ---------------------------------------------------------------- header
  const facts = $derived.by(() => {
    if (!pl || idx === null) return [];
    const out: { k: string; v: string; sub?: string }[] = [];
    const pop = val('pop_total');
    if (pop?.value != null) out.push({ k: t('p.population'), v: fmtNumber(pop.value, 0), sub: pop.period });
    // header area: land area without lakes (contract C); the total incl. lakes as the second line
    const land = base.metas.has('geo_area_land_ha') ? val('geo_area_land_ha') : undefined;
    const area = val('geo_area_total_ha');
    const km2 = (ha: number) => `${fmtNumber(ha / 100, ha < 1000 ? 2 : 1)} ${t('p.km2')}`;
    if (land?.value != null)
      out.push({ k: t('p.landArea'), v: km2(land.value), sub: area?.value != null && area.value > land.value ? t('p.inclLakes', { a: km2(area.value) }) : t('p.noLakes') });
    else if (area?.value != null) out.push({ k: t('p.area'), v: km2(area.value) });
    const el = val('geo_elev_mean');
    if (el?.value != null) {
      const lo = val('geo_elev_min')?.value;
      const hi = val('geo_elev_max')?.value;
      out.push({
        k: t('p.elevation'), v: `${fmtNumber(el.value, 0)} m`,
        sub: lo != null && hi != null ? t('p.elevRange', { lo: fmtNumber(lo, 0), hi: fmtNumber(hi, 0) }) : t('p.mean'),
      });
    }
    const d = val('geo_pop_density');
    if (d?.value != null) out.push({ k: t('p.density'), v: `${fmtNumber(d.value, 0)}`, sub: t('p.densSub') });
    return out;
  });

  const ident = $derived(unit.level === 'gemeinde' ? identity?.units[unit.id] : undefined);
  const LANG_ORDER = ['de', 'fr', 'it', 'rm', 'en'];
  const altNames = $derived.by(() => {
    if (hideAltNames(unit.level, unit.id)) return [];
    if (ident?.names)
      return LANG_ORDER.filter((l) => ident.names![l]).map((l) => ({ lang: l.toUpperCase(), name: ident.names![l] }));
    return (sx?.byRef.get(ref)?.alts ?? []).map((n) => ({ lang: '', name: n }));
  });
  const partOf = $derived.by(() => {
    if (!row || !rows) return [];
    const r = row as UnitRow & Record<string, unknown>;
    const out: { k: string; ref: string; name: string }[] = [];
    const add = (k: string, level: string, id: unknown) => {
      if (typeof id !== 'string' || !id) return;
      const u = rows!.get(refOf(level, id));
      if (u) out.push({ k, ref: refOf(level, id), name: shortName(level, unitName(u)) });
    };
    if (unit.level !== 'kanton') add(t('p.canton'), 'kanton', r.kanton);
    if (unit.level === 'gemeinde') {
      add(t('p.district'), 'bezirk', r.bezirk);
      add(t('p.agglo'), 'agglomeration', r.agglomeration);
      add(t('p.amr'), 'arbeitsmarktgebiet', r.arbeitsmarktgebiet);
      add(t('p.grossregion'), 'grossregion', r.grossregion);
      add(t('p.lang'), 'sprachgebiet', r.sprachgebiet);
      add(t('p.urbanRural'), 'stadt_land', r.stadt_land);
      add(t('p.type'), 'gemeindetyp', r.gemeindetyp);
    }
    return out;
  });
  const links = $derived.by(() => {
    const out: { label: string; href: string; note?: string }[] = [];
    if (!ident || !identity) return out;
    if (ident.web) out.push({ label: t('p.website'), href: ident.web });
    for (const l of ['de', 'fr', 'it', 'en']) {
      const p = ident.wiki?.[l];
      if (p) out.push({ label: `${t('p.wikipedia')} ${l.toUpperCase()}`, href: identity.wiki_url.replace('{lang}', l).replace('{path}', p) });
    }
    if (ident.coa?.[0]) {
      // Commons file names contain spaces: Commons uses underscores, the rest is percent-encoded
      const file = encodeURIComponent(ident.coa[0].replace(/ /g, '_'));
      out.push({ label: t('p.coa'), href: identity.commons_url.replace('{file}', file), note: t('p.coaNote', { lic: ident.coa[1] }) });
    }
    if (ident.qid) out.push({ label: t('p.wikidata'), href: `https://www.wikidata.org/wiki/${encodeURIComponent(ident.qid)}` });
    return out;
  });

  // locator: the place, or the member municipalities of a municipality type
  let gemGeo = $state.raw<PlaceLevel | null>(null);
  $effect(() => {
    if (unit.level === 'gemeindetyp') loadPlaceLevel('gemeinde').then((g) => (gemGeo = g)).catch(() => {});
  });
  const shapes = $derived.by(() => {
    if (unit.level === 'gemeindetyp' && gemGeo?.geo && rows) {
      const ids = new Set([...rows.values()].filter((r) => r.level === 'gemeinde' && r.gemeindetyp === unit.id).map((r) => r.id));
      return gemGeo.geo.features.filter((f) => ids.has(gemGeo!.units[f.id as number])).map((f) => f.geometry);
    }
    if (!pl?.geo || idx === null) return [];
    const f = pl.geo.features.find((x) => x.id === idx);
    return f ? [f.geometry] : [];
  });

  // ---------------------------------------------------------------- side blocks
  const neigh = $derived.by(() => {
    const ids = neighbours?.levels[unit.level]?.[unit.id];
    if (!ids || !rows) return null;
    return ids.map((id) => ({ ref: refOf(unit.level, id), name: placeName(unit.level, id, rows!.get(refOf(unit.level, id))?.name ?? id), kt: rows!.get(refOf(unit.level, id))?.kanton ?? '' }))
      .sort((a, b) => a.name.localeCompare(b.name, 'de'));
  });
  const short = $derived(pl && idx !== null ? inShort({ pl, idx, base, reach, placeName: name }) : []);
  // D31: station time towards the hub first (when the build has it), then door to door, then car
  const hasSt = $derived(!!reach?.pt_station);
  const reachK = $derived(reach && unit.level === 'gemeinde' ? reach.units.indexOf(unit.id) : -1);
  const reachRows = $derived.by(() => {
    if (!reach || reachK < 0) return null;
    const k = reachK;
    return reach.hubs
      .map(([slug, hub]) => ({
        hub, st: reach!.pt_station?.[slug]?.[k] ?? null, pt: reach!.pt[slug]?.[k] ?? null, car: reach!.car[slug]?.[k] ?? null,
        note: reach!.notes?.pt_station?.[slug]?.[String(k)] ?? null,
      }))
      .sort((a, b) => (hasSt ? (a.st ?? 1e9) - (b.st ?? 1e9) : 0) || (a.pt ?? 1e9) - (b.pt ?? 1e9) || (a.car ?? 1e9) - (b.car ?? 1e9));
  });
  const stationInfo = $derived(reach && reachK >= 0 ? mainStation(reach, unit.id) : null);
  // reasons are per hub (reasons[measure][hub][unit]); the same reason for several hubs is listed once
  const reachWhy = $derived.by(() => {
    if (!reach?.reasons || reachK < 0) return [];
    const out: { what: string; why: string }[] = [];
    for (const [key, what] of [['pt_station', t('pt.st')], ['pt', t(hasSt ? 'pt.dd' : 'rc.pt')], ['car', t('common.car')]] as const) {
      const byWhy = new Map<string, string[]>();
      for (const [slug, hub] of reach.hubs) {
        const why = reasonAt(reach, key, slug, reachK);
        if (why) byWhy.set(why, [...(byWhy.get(why) ?? []), hub]);
      }
      for (const [why, hubs] of byWhy) out.push({ what: `${what} (${hubs.join(', ')})`, why });
    }
    return out;
  });
  const events = $derived(unit.level === 'gemeinde' && history ? (history.units[unit.id] ?? []) : null);
  const evType = (k: string) => (isDe() ? HISTORY_DE[k] : app.lang === 'fr' ? historyFr(k) : history?.types[k]) ?? history?.types[k] ?? k;
  const names = (xs: [string, string][]) => xs.map(([id, n]) => `${n} (${id})`).join(', ');

  const publisher = (m: MetricMeta) => base.sources.get(m.source)?.publisher.split(' (')[0] ?? m.source;
  const precisionLabel = precisionText;
  function jump(id: string) {
    document.getElementById(id)?.scrollIntoView({ block: 'start' });
  }
  function toggle(b: { theme: string; files: string[] }) {
    open = { ...open, [b.theme]: !open[b.theme] };
    if (open[b.theme]) for (const f of b.files) need(f);
  }
  const slug = (s: string) => 'th-' + s.toLowerCase().replace(/[^a-z]+/g, '-');
</script>

{#snippet metricRow(m: MetricMeta)}
  {@const e = entry(m)}
  <div class="mrow" class:gap={e && e.value === null}>
    <div class="ml">
      <span class="lbl">{ml(m)}<Term k={glossKeyOf(m)} /></span>
      <span class="tags">
        {#if e}<span class="tag">{precisionLabel(e.precision)}</span><span class="sep">·</span>{/if}
        {#if e?.partial}<span class="tag warn">{coverageLabel(m)}</span><span class="sep">·</span>{/if}
        {#if e?.regional}<span class="tag warn">{t('rg.tag', { level: levelName(e.regional, false) })}</span><span class="sep">·</span>{/if}
        <a class="tag src" href={sourceHref(m.source)} title={base.sources.get(m.source)?.title ?? ''}>{publisher(m)}</a>
      </span>
    </div>
    {#if e === undefined}
      <div class="mv muted">…</div><div class="mr"></div><div class="ms"></div>
    {:else if e === null}
      <div class="mv nd"><span class="hatch"></span> {t('p.noData')}</div>
      <div class="mr reason">{t('p.notPublished')}</div><div class="ms"></div>
    {:else if e.value === null}
      <div class="mv nd"><span class="hatch"></span> {t('p.noData')}<span class="yr">{fmtPeriod(e.period)}</span></div>
      <div class="mr reason">{e.gap}</div><div class="ms"></div>
    {:else}
      <div class="mv"><span class="v">{fmtValue(e.value, m)}{#if e.marks}<sup class="fl" title={e.flags.join('\n')}>{e.marks}</sup>{/if}</span><span class="yr">{fmtPeriod(e.period)}</span>
        {#each e.flags as f}<span class="fx">{f}</span>{/each}{#if e.note}<span class="fx">{e.note}</span>{/if}</div>
      <div class="mr">
        {#if e.rank}
          <span class="rk num">{t('p.rankCH', { r: fmtNumber(e.rank.rank, 0), n: fmtNumber(e.rank.n, 0) })}{e.partial ? ` ${t('p.withData')}` : ''}{tiedText(e.rank)}</span>
          {#if e.rankKt}<span class="rk num muted">{t('p.rankKt', { r: fmtNumber(e.rankKt.rank, 0), n: fmtNumber(e.rankKt.n, 0), kt: pl!.canton[idx!] })}{tiedText(e.rankKt)}</span>{/if}
          <PctBar pct={e.rank.pct} lo={e.rank.pctLo} hi={e.rank.pctHi} label="P{Math.round(e.rank.pct)}{tiedText(e.rank, true)}" />
        {/if}
      </div>
      <div class="ms"><Sparkline meta={m} level={unit.level} id={unit.id} /></div>
    {/if}
  </div>
{/snippet}

<main class="pg" id="main" tabindex="-1" bind:this={scroller}>
  <div class="wrap">
    <nav class="crumbs">
      <a href={hrefFor('map')}>← {t('p.back')}</a>
    </nav>

    {#if err}
      <p role="alert">{err}</p>
    {:else if pl && idx === null}
      <div class="nf">
        <h1>{t('p.notFound', { id: ref })}</h1>
        <p>{t('ux.searchInstead')}</p>
        <Search onpick={(r) => app.go('profile', { id: r })} />
      </div>
    {:else}
      <header class="ph">
        <div class="hmain">
          <div class="caps lvl">{levelName(unit.level, false)}{#if row?.kanton && unit.level !== 'kanton'}{' · '}{row.kanton}{/if}{#if unit.level === 'gemeinde'}{' · '}{t('p.bfs')} {unit.id}{/if}</div>
          <h1>{name}</h1>
          {#if altNames.length}
            <p class="alt"><span class="sr">{t('p.otherNames')}: </span>{#each altNames as a, k}{#if k}<span class="dot">{' · '}</span>{/if}{#if a.lang}<span class="lc">{a.lang}</span>{' '}{/if}{a.name}{/each}</p>
          {/if}
          {#if facts.length}
            <dl class="facts">
              {#each facts as f}
                <div><dt class="caps">{f.k}</dt><dd><span class="fv num">{f.v}</span>{#if f.sub}<span class="fs">{f.sub}</span>{/if}</dd></div>
              {/each}
            </dl>
          {/if}
          {#if partOf.length || row?.n_gemeinden}
            <dl class="part">
              {#each partOf as p}
                <div><dt>{p.k}{#if p.k === t('p.amr')}<Term k="labour_market_area" />{:else if p.k === t('p.agglo')}<Term k="agglomeration" />{/if}</dt><dd><a href={profileHref(p.ref)}>{p.name}</a></dd></div>
              {/each}
              {#if row?.n_gemeinden}<div><dt>{t('p.members')}</dt><dd class="num">{fmtNumber(row.n_gemeinden, 0)}</dd></div>{/if}
            </dl>
          {/if}
          {#if links.length}
            <p class="links">
              {#each links as l}<a href={l.href} target="_blank" rel="noopener noreferrer">{l.label}</a>{#if l.note}<span class="lnote"> ({l.note})</span>{/if}{' '}{/each}
            </p>
          {/if}
          <div class="actions">
            {#if hasMap(unit.level)}<button type="button" class="btn ink" onclick={() => showOnMap(base, ref)}>{t('p.showOnMap')}</button>{/if}
            <a class="btn" href={hrefFor('places', { ids: ref })}>{t('p.compareWith')}</a>
          </div>
        </div>
        {#if shapes.length}
          <figure class="loc"><Locator kanton={base.kanton} lakes={base.lakes} {shapes} label={name} /></figure>
        {/if}
      </header>

      {#if short.length}
        <section class="short" aria-labelledby="in-short">
          <h2 id="in-short">{t('is.title')}</h2>
          <ul>
            {#each short as f}<li>{f.text}{#if f.note}{' '}<span class="sn">({f.note})</span>{/if}</li>{/each}
          </ul>
          <p class="foot">{t('is.foot')}</p>
        </section>
      {/if}

      <nav class="toc" aria-label={t('p.contents')}>
        {#each blocks as b}<button type="button" onclick={() => jump(slug(b.theme))}>{themeName(b.theme)}</button>{/each}
        <button type="button" onclick={() => jump('pf-side')}>{t('p.neighbours')} · {t('p.similar')}</button>
      </nav>

      <div class="cols">
        <div class="main">
          <p class="foot rnote">{t('p.rankNote', { units: unitsWord })}</p>
          {#each blocks as b (b.theme)}
            <section class="theme" id={slug(b.theme)}>
              <h2>{themeName(b.theme)}</h2>
              {#if b.theme === 'Politics' && pl && idx !== null}<ElectionBar {base} level={unit.level} id={unit.id} canton={unit.level === 'kanton' ? '' : pl.canton[idx]} />{/if}
              {#each b.head as m (m.id)}{@render metricRow(m)}{/each}
              {#if b.rest.length}
                {#if open[b.theme]}
                  {#each b.rest as m (m.id)}{@render metricRow(m)}{/each}
                {/if}
                <button type="button" class="more" aria-expanded={!!open[b.theme]} onclick={() => toggle(b)}>
                  {open[b.theme] ? t('p.showLess') : b.head.length ? t('p.moreN', { n: b.rest.length }) : t('p.showAll', { n: b.rest.length })}
                </button>
              {/if}
            </section>
          {/each}
        </div>

        <aside class="side" id="pf-side">
          <section>
            <h2>{t('p.reach')}</h2>
            {#if unit.level !== 'gemeinde'}
              <p class="foot">{t('p.reachHigher', { one: levelName(unit.level, false) })}</p>
            {:else if reachRows}
              {#if hasSt}<p class="st">{stationInfo ? t(stationInfo.mode ? 'p.fromStop' : stationInfo.outside ? 'p.fromStationOut' : 'p.fromStation', { st: stationInfo.name }) : t('p.noStation')}</p>{/if}
              <table class="reach">
                <thead><tr><th>{t('p.reachHub')}</th>
                  {#if hasSt}<th class="n" title={t('pt.st')}>{t('p.reachSt')}</th><th class="n" title={t('pt.dd')}>{t('p.reachDoor')}</th>
                  {:else}<th class="n">{t('p.reachPT')}</th>{/if}
                  <th class="n">{t('p.reachCar')}</th></tr></thead>
                <tbody>
                  {#each reachRows as r}
                    <tr><td>{r.hub}</td>
                      {#if hasSt}<td class="n num strong" title={r.note ?? undefined}>{r.st ?? t('p.reachNone')}{#if r.note}<sup>*</sup>{/if}</td>{/if}
                      <td class="n num">{r.pt ?? t('p.reachNone')}</td><td class="n num">{r.car ?? t('p.reachNone')}</td></tr>
                  {/each}
                </tbody>
              </table>
              <ul class="methods foot">
                {#if hasSt}<li><strong>{t('p.reachSt')}:</strong> {methodText('ptst', t('p.theHub'), reach, true)}</li>{/if}
                <li><strong>{hasSt ? t('p.reachDoor') : t('p.reachPT')}:</strong> {methodText('pt', t('p.theHub'), reach, hasSt)}</li>
                <li><strong>{t('p.reachCar')}:</strong> {methodText('car', t('p.theHub'), reach, hasSt)}</li>
                {#each reachWhy as w}<li>– {w.what}: {w.why}</li>{/each}
                {#each reachRows.filter((r) => r.note) as r}<li>* {r.hub}: {r.note}</li>{/each}
                {#if !reachWhy.length && reachRows.some((r) => r.pt === null || r.car === null || (hasSt && r.st === null))}<li>{t('p.reachNoneNote')}</li>{/if}
              </ul>
              <p class="foot">{t('p.reachDate', { d: reach?.service_date ?? '' })} <a href={sourceHref('reach_metrics')}>{t('p.sources')}</a></p>
            {:else}
              <p class="foot">…</p>
            {/if}
          </section>

          <section>
            <h2>{t('p.neighbours')}</h2>
            {#if neigh && neigh.length}
              <p class="chips">{#each neigh as n}<a href={profileHref(n.ref)}>{n.name}{#if n.kt && unit.level === 'gemeinde' && n.kt !== row?.kanton}{' '}<span class="muted">{n.kt}</span>{/if}</a>{/each}</p>
            {:else if neighbours}
              <p class="foot">{t('p.noNeighbours')}</p>
            {/if}
          </section>

          <section>
            <h2>{t('p.similar')}</h2>
            {#if pl && idx !== null}<SimilarPlaces {base} {pl} {idx} {rows} {reach} />{/if}
          </section>

          <section>
            <h2>{t('p.history')}</h2>
            {#if unit.level !== 'gemeinde'}
              <p class="foot">{t('p.historyOnly')}</p>
            {:else if events && events.length}
              <ol class="hist">
                {#each events as ev}
                  <li>
                    <span class="hd num">{ev.d}</span>
                    <span class="ht">{evType(ev.t)}</span>
                    {#if ev.t === 'canton_change' && ev.canton}<span class="hx">{ev.canton[0]} → {ev.canton[1]}</span>{/if}
                    {#if ev.district}<span class="hx">{ev.district[0]} → {ev.district[1]}</span>{/if}
                    {#if ev.t !== 'district_change'}<span class="hx">{names(ev.from)} → {names(ev.to)}</span>{/if}
                  </li>
                {/each}
              </ol>
              <p class="foot">{t('p.historySource', { since: history?.since ?? '1960' })}</p>
            {:else if events}
              <p class="foot">{t('p.historyNone')}</p>
            {/if}
          </section>
        </aside>
      </div>

      <footer class="pfoot">
        <a href={hrefFor('sources')}>{t('p.sources')}</a>
        <a href={hrefFor('sources', { src: 'gaps' })}>{t('p.gaps')}</a>
        {#if unit.level === 'gemeinde'}<span>{t('p.attribution')}</span>{/if}
      </footer>
    {/if}
  </div>
</main>

<style>
  .pg:focus { outline: none; }
  .pg { flex: 1; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch; background: var(--bg); }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 12px 24px 40px; }
  .crumbs { font-size: 0.82rem; margin-bottom: 10px; }
  a { color: var(--text); text-underline-offset: 2px; }
  .muted { color: var(--muted); }

  .ph { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 24px; padding-bottom: 18px; border-bottom: 3px solid var(--rule); }
  .lvl { color: var(--muted); }
  .nf { max-width: 480px; margin: var(--sp-8) 0; }
  .nf h1 { font-size: var(--fs-h2); line-height: var(--lh-h2); letter-spacing: -0.01em; }
  .nf p { margin: var(--sp-4) 0 var(--sp-2); }
  h1 { margin: 2px 0 2px; font-size: 2.6rem; line-height: 1.05; letter-spacing: -0.03em; font-weight: 700; }
  .alt { margin: 4px 0 0; color: var(--muted); font-size: 0.88rem; }
  .lc { font-size: 0.66rem; font-weight: 700; color: var(--text); letter-spacing: 0.04em; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  .facts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 16px 0 0; border-top: 1px solid var(--rule); }
  .facts > div { padding: 6px 12px 4px 0; }
  .facts > div + div { padding-left: 12px; border-left: 1px solid var(--border); }
  .facts dd { margin: 2px 0 0; display: flex; flex-direction: column; }
  .fv { font-size: 1.45rem; font-weight: 700; letter-spacing: -0.02em; }
  .fs { font-size: 0.72rem; color: var(--muted); }
  .part { display: flex; flex-wrap: wrap; gap: 4px 18px; margin: 12px 0 0; font-size: 0.82rem; }
  .part > div { display: flex; gap: 6px; }
  .part dt { color: var(--muted); }
  .part dd { margin: 0; }
  .links { margin: 10px 0 0; font-size: 0.82rem; display: flex; flex-wrap: wrap; gap: 4px 14px; }
  .lnote { color: var(--faint); }
  .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
  .btn {
    display: inline-flex; align-items: center; padding: 6px 12px; border: 1px solid var(--ink); background: var(--panel); font-size: 0.82rem;
    font-weight: 600; cursor: pointer; text-decoration: none; color: var(--text);
  }
  .btn.ink { background: var(--ink); color: var(--ink-text); }
  .loc { margin: 4px 0 0; align-self: start; }

  .short { padding: 0 0 10px; border-bottom: 1px solid var(--rule); }
  .short h2 { border-bottom: 0; padding-bottom: 4px; }
  .short ul { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 28px; font-size: 0.9rem; line-height: 1.4; }
  .short li { padding: 5px 0; border-bottom: 1px solid var(--border); }
  .sn { color: var(--muted); font-size: 0.76rem; }
  .short .foot { margin: 6px 0 0; }

  .toc { display: flex; flex-wrap: wrap; gap: 4px 6px; padding: 10px 0; border-bottom: 1px solid var(--rule); }
  .toc button { border: 0; background: none; padding: 2px 0; margin-right: 8px; font-size: 0.78rem; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }

  .cols { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 32px; margin-top: 6px; }
  .rnote { margin: 8px 0 0; }
  h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; margin: 0; padding: 18px 0 6px; border-bottom: 2px solid var(--rule); }
  .theme { scroll-margin-top: 8px; }
  .mrow {
    display: grid; grid-template-columns: minmax(0, 1fr) 132px 168px 90px; gap: 2px 14px; align-items: center;
    padding: 6px 0; border-bottom: 1px solid var(--border);
  }
  .ml { min-width: 0; display: flex; flex-direction: column; }
  .lbl { font-weight: 600; font-size: 0.86rem; line-height: 1.25; }
  .tags { display: flex; flex-wrap: wrap; font-size: 0.7rem; color: var(--faint); margin-top: 1px; }
  .sep { margin: 0 5px; }
  .tag.warn { color: var(--text); }
  a.tag { color: var(--faint); }
  .mv { text-align: right; display: flex; flex-direction: column; align-items: flex-end; }
  /* long units (French) wrap inside the value column instead of running into the label */
  .v { font-weight: 700; font-size: 0.98rem; font-variant-numeric: tabular-nums; white-space: normal; text-align: right; min-width: 0; overflow-wrap: break-word; }
  .mv { min-width: 0; }
  .yr { font-size: 0.7rem; color: var(--muted); }
  .fl { font-size: 0.62rem; color: var(--accent); margin-left: 2px; }
  .fx { font-size: 0.68rem; color: var(--text); text-align: right; line-height: 1.25; max-width: 16em; }
  .nd { color: var(--muted); font-size: 0.8rem; flex-direction: row; justify-content: flex-end; align-items: center; gap: 6px; flex-wrap: wrap; }
  .nd .yr { flex-basis: 100%; text-align: right; }
  .mr { display: flex; flex-direction: column; font-size: 0.74rem; line-height: 1.3; min-width: 0; }
  .mr.reason { color: var(--text); font-size: 0.76rem; }
  .ms { min-height: 22px; }
  .more {
    margin: 6px 0 2px; border: 1px solid var(--ink); background: none; padding: 4px 10px; font-size: 0.76rem; font-weight: 600; cursor: pointer;
  }
  .more[aria-expanded='true'] { background: var(--ink); color: var(--ink-text); }

  .side section { margin-bottom: 6px; }
  .reach { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 4px; }
  .reach th { text-align: left; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 0; border-bottom: 1px solid var(--rule); }
  .reach td { padding: 3px 0; border-bottom: 1px solid var(--border); }
  .reach .n { text-align: right; width: 56px; }
  .reach .strong { font-weight: 700; }
  .st { margin: 4px 0 0; font-size: 0.8rem; }
  .methods { list-style: none; padding: 0; margin: 6px 0 0; display: grid; gap: 3px; }
  .chips { display: flex; flex-wrap: wrap; gap: 4px 12px; margin: 8px 0 0; font-size: 0.84rem; }
  .sim, .hist { list-style: none; margin: 6px 0 0; padding: 0; font-size: 0.84rem; }
  .sim li { display: flex; gap: 6px; align-items: baseline; padding: 3px 0; border-bottom: 1px solid var(--border); }
  .dh { margin: 4px 0 0; }
  .sim .d { margin-left: auto; color: var(--muted); font-size: 0.74rem; }
  .hist li { display: flex; flex-direction: column; padding: 6px 0; border-bottom: 1px solid var(--border); }
  .hd { font-weight: 700; font-size: 0.8rem; }
  .hx { color: var(--muted); font-size: 0.78rem; }
  .side .foot { margin: 6px 0 0; }
  .pfoot { display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 28px; padding-top: 10px; border-top: 3px solid var(--rule); font-size: 0.78rem; color: var(--faint); }

  @media (max-width: 899px) {
    .wrap { padding: 10px 16px calc(32px + env(safe-area-inset-bottom)); }
    .ph { grid-template-columns: 1fr; gap: 10px; }
    .loc { order: -1; max-width: 220px; }
    h1 { font-size: 1.9rem; }
    .facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .facts > div:nth-child(3) { padding-left: 0; border-left: 0; }
    .facts > div:nth-child(n + 3) { border-top: 1px solid var(--border); }
    .fv { font-size: 1.2rem; }
    .cols { grid-template-columns: 1fr; gap: 0; }
    .short ul { grid-template-columns: 1fr; }
    .mrow {
      grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: 'l v' 'r s';
      gap: 3px 10px; align-items: start;
    }
    .ml { grid-area: l; }
    .mv { grid-area: v; }
    .mr { grid-area: r; flex-direction: row; flex-wrap: wrap; gap: 0 8px; align-items: center; }
    .mr :global(.pb) { width: 90px; }
    .ms { grid-area: s; align-self: center; min-height: 0; }
    .mv { max-width: 52vw; }
    .v { white-space: normal; text-align: right; }
  }
</style>
