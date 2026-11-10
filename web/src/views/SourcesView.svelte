<script lang="ts" module>
  import { addStrings } from '../lib/i18n.svelte';
  addStrings(
    {
      's.title': 'Sources and licences',
      's.intro': 'The app uses {n} datasets. {h} more are held back until their terms of use are confirmed. Every number in the app comes from one of the datasets below.',
      's.noDate': '“Latest period” is the most recent year (or vote date) shown from each dataset. Download dates are not listed yet.',
      's.gaps': 'How gaps are shown',
      's.gap1': 'A missing value is never blank and never zero: the map hatches it and the card or profile states why — not published at this level, suppressed (small numbers), not covered by this canton, not applicable, or no data for this year.',
      's.gap2': 'Metrics marked * cover some cantons only; they show “partial: N of 26 cantons”, and ranks count only the units with data.',
      's.gap3': 'Every value carries its precision (exact, survey, modelled, boundary estimate), its source and its period.',
      's.gap4': 'Some values cannot be added up from municipalities to larger areas (medians, indices, travel times, survey results published for districts only): they appear only at the levels where they are published.',
      's.used': 'Used in the app',
      's.held': 'Held back: terms of use not yet confirmed',
      's.heldNote': 'Not shipped: none of its values appear in the app.',
      's.publisher': 'Publisher',
      's.licence': 'Licence',
      's.attribution': 'Attribution',
      's.vintage': 'Boundaries as of',
      's.years': 'Years',
      's.latest': 'Latest period',
      's.metrics': '{n} metrics',
      's.link': 'Source page',
      's.filter': 'Filter sources',
      's.none': 'No source matches “{q}”.',
    },
    {
      's.title': 'Quellen und Lizenzen',
      's.intro': 'Die App verwendet {n} Datensätze. {h} weitere sind zurückgestellt, bis ihre Nutzungsbedingungen bestätigt sind. Jede Zahl in der App stammt aus einem der folgenden Datensätze.',
      's.noDate': '«Letzte Periode» ist das jüngste Jahr (oder Abstimmungsdatum), das aus einem Datensatz gezeigt wird. Downloaddaten sind noch nicht aufgeführt.',
      's.gaps': 'Wie Lücken gezeigt werden',
      's.gap1': 'Ein fehlender Wert ist nie leer und nie null: Die Karte schraffiert ihn, und Karte oder Profil nennen den Grund — auf dieser Ebene nicht publiziert, unterdrückt (kleine Zahlen), von diesem Kanton nicht erfasst, nicht anwendbar oder keine Daten für dieses Jahr.',
      's.gap2': 'Mit * markierte Kennzahlen decken nur einen Teil der Kantone ab; sie zeigen «teilweise: N von 26 Kantonen», und Ränge zählen nur Einheiten mit Daten.',
      's.gap3': 'Jeder Wert trägt seine Genauigkeit (exakt, Erhebung, modelliert, Gebietsschätzung), seine Quelle und seine Periode.',
      's.gap4': 'Manche Werte lassen sich nicht von Gemeinden auf grössere Gebiete hochrechnen (Mediane, Indizes, Reisezeiten, nur für Bezirke publizierte Erhebungen): Sie erscheinen nur auf den Ebenen, auf denen sie publiziert sind.',
      's.used': 'In der App verwendet',
      's.held': 'Zurückgestellt: Nutzungsbedingungen noch nicht bestätigt',
      's.heldNote': 'Nicht ausgeliefert: Keiner ihrer Werte erscheint in der App.',
      's.publisher': 'Herausgeber',
      's.licence': 'Lizenz',
      's.attribution': 'Quellenangabe',
      's.vintage': 'Gebietsstand',
      's.years': 'Jahre',
      's.latest': 'Letzte Periode',
      's.metrics': '{n} Kennzahlen',
      's.link': 'Quellseite',
      's.filter': 'Quellen filtern',
      's.none': 'Keine Quelle passt zu «{q}».',
    },
  );
</script>

<script lang="ts">
  // Sources page (brief 6.1): every dataset with publisher, licence, attribution, boundary vintage,
  // years and the metrics built from it; the D21 note on gaps. Source tags across the app link here
  // with #v=sources&src=<source_id> (the entry is opened and scrolled into view).
  import { tick, untrack } from 'svelte';
  import { fmtPeriod } from '../lib/classify';
  import type { Base, MetricMeta, Source } from '../lib/data';
  import { ml, t } from '../lib/i18n.svelte';
  import { norm } from '../lib/places';
  import { app } from '../lib/state.svelte';

  interface Props {
    base: Base;
  }
  let { base }: Props = $props();

  type FullSource = Source & { license?: string; vintage?: string; years?: string; shipped?: boolean };
  const all = $derived([...base.sources.values()] as FullSource[]);
  const byMetric = $derived.by(() => {
    const m = new Map<string, MetricMeta[]>();
    for (const x of base.metrics) if (!x.hidden) m.set(x.source, [...(m.get(x.source) ?? []), x]);
    return m;
  });
  const latestOf = (id: string) => {
    const ms = byMetric.get(id) ?? [];
    return ms.map((m) => m.latest.split('#')[0]).sort().pop() ?? null;
  };
  let q = $state('');
  const match = (s: FullSource) => {
    const w = norm(q);
    return !w || norm(`${s.title} ${s.publisher} ${s.source_id} ${s.license ?? ''}`).includes(w);
  };
  const sortKey = (s: FullSource) => `${s.publisher} ${s.title}`;
  const used = $derived(all.filter((s) => s.shipped !== false && match(s)).sort((a, b) => sortKey(a).localeCompare(sortKey(b))));
  const held = $derived(all.filter((s) => s.shipped === false && match(s)).sort((a, b) => sortKey(a).localeCompare(sortKey(b))));
  const nUsed = $derived(all.filter((s) => s.shipped !== false).length);
  const nHeld = $derived(all.filter((s) => s.shipped === false).length);

  const target = $derived(app.params.src ?? null);
  let openIds = $state<Record<string, boolean>>({});
  $effect(() => {
    const id = target;
    if (!id) return;
    if (id !== 'gaps') untrack(() => (openIds = { ...openIds, [id]: true }));
    tick().then(() => document.getElementById(id === 'gaps' ? 'gaps' : `src-${id}`)?.scrollIntoView({ block: 'start' }));
  });
</script>

{#snippet entry(s: FullSource)}
  {@const ms = byMetric.get(s.source_id) ?? []}
  {@const latest = latestOf(s.source_id)}
  <article class="src" id="src-{s.source_id}" class:target={target === s.source_id}>
    <h3>{s.title}</h3>
    <dl>
      <dt>{t('s.publisher')}</dt><dd>{s.publisher}</dd>
      {#if s.license}<dt>{t('s.licence')}</dt><dd>{s.license}</dd>{/if}
      {#if s.attribution}<dt>{t('s.attribution')}</dt><dd class="attr">{s.attribution}</dd>{/if}
      {#if s.vintage}<dt>{t('s.vintage')}</dt><dd>{s.vintage}</dd>{/if}
      {#if s.years}<dt>{t('s.years')}</dt><dd>{s.years}</dd>{/if}
      {#if latest && s.shipped !== false}<dt>{t('s.latest')}</dt><dd class="num">{fmtPeriod(latest)}</dd>{/if}
    </dl>
    <p class="row">
      {#if s.url}<a href={s.url} target="_blank" rel="noopener noreferrer">{t('s.link')} ↗</a>{/if}
      {#if s.shipped === false}<span class="held">{t('s.heldNote')}</span>{/if}
    </p>
    {#if ms.length && s.shipped !== false}
      <details open={!!openIds[s.source_id]} ontoggle={(e) => (openIds = { ...openIds, [s.source_id]: e.currentTarget.open })}>
        <summary>{t('s.metrics', { n: ms.length })}</summary>
        <ul class="ms">
          {#each ms.slice().sort((a, b) => ml(a).localeCompare(ml(b))) as m}<li>{ml(m)} <span class="mp num">{fmtPeriod(m.latest)}</span></li>{/each}
        </ul>
      </details>
    {/if}
  </article>
{/snippet}

<main class="pg" id="main" tabindex="-1">
  <div class="wrap">
    <h1>{t('s.title')}</h1>
    <p class="intro">{t('s.intro', { n: nUsed, h: nHeld })}</p>
    <p class="foot">{t('s.noDate')}</p>

    <section class="gaps" id="gaps" class:target={target === 'gaps'}>
      <h2>{t('s.gaps')}</h2>
      <ul>
        <li><span class="hatch"></span> {t('s.gap1')}</li>
        <li>{t('s.gap2')}</li>
        <li>{t('s.gap3')}</li>
        <li>{t('s.gap4')}</li>
      </ul>
    </section>

    <input class="filter" type="search" bind:value={q} placeholder={t('s.filter')} aria-label={t('s.filter')} />

    <h2>{t('s.used')} <span class="n num">{used.length}</span></h2>
    {#each used as s (s.source_id)}{@render entry(s)}{/each}
    {#if held.length}
      <h2>{t('s.held')} <span class="n num">{held.length}</span></h2>
      {#each held as s (s.source_id)}{@render entry(s)}{/each}
    {/if}
    {#if q && !used.length && !held.length}<p class="foot">{t('s.none', { q })}</p>{/if}
  </div>
</main>

<style>
  .pg:focus { outline: none; }
  .pg { flex: 1; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch; background: var(--bg); }
  .wrap { max-width: 900px; margin: 0 auto; padding: 16px 24px 48px; }
  h1 { margin: 0; font-size: 2rem; letter-spacing: -0.03em; }
  .intro { margin: 6px 0 2px; font-size: 0.9rem; max-width: 720px; }
  h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; margin: 26px 0 0; padding-bottom: 6px; border-bottom: 3px solid var(--rule); }
  h2 .n { color: var(--muted); font-weight: 500; margin-left: 4px; }
  .gaps { margin-top: 10px; scroll-margin-top: 10px; }
  .gaps ul { margin: 8px 0 0; padding-left: 18px; font-size: 0.86rem; display: grid; gap: 5px; }
  .gaps.target h2 { border-bottom-color: var(--accent); }
  .filter { margin-top: 22px; width: 320px; max-width: 100%; padding: 6px 8px; border: 1px solid var(--ink); border-radius: 0; font-size: 0.85rem; }
  .src { padding: 12px 0 10px; border-bottom: 1px solid var(--rule); scroll-margin-top: 10px; }
  .src.target { box-shadow: inset 4px 0 0 var(--accent); padding-left: 12px; }
  h3 { margin: 0 0 6px; font-size: 0.98rem; line-height: 1.3; }
  dl { display: grid; grid-template-columns: 130px minmax(0, 1fr); gap: 3px 12px; margin: 0; font-size: 0.8rem; }
  dt { color: var(--muted); }
  dd { margin: 0; overflow-wrap: anywhere; }
  .attr { font-style: italic; }
  .row { display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 6px 0 0; font-size: 0.78rem; align-items: baseline; }
  .row a { color: var(--text); }
  .held { color: var(--text); font-weight: 600; }
  details { margin-top: 6px; font-size: 0.8rem; }
  summary { cursor: pointer; font-weight: 600; }
  .ms { columns: 2; column-gap: 24px; margin: 6px 0 0; padding-left: 16px; }
  .ms li { break-inside: avoid; }
  .mp { color: var(--faint); font-size: 0.72rem; }
  @media (max-width: 899px) {
    .wrap { padding: 12px 16px calc(32px + env(safe-area-inset-bottom)); }
    h1 { font-size: 1.5rem; }
    dl { grid-template-columns: 1fr; gap: 0; }
    dt { margin-top: 4px; }
    .ms { columns: 1; }
    .filter { font-size: 16px; width: 100%; }
  }
</style>
