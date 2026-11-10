<script lang="ts" module>
  import { addStrings } from '../lib/i18n.svelte';
  addStrings(
    {
      'pl.title': 'Compare places',
      'pl.intro': 'Two to four places side by side, at any level. Add places with the search; the selection is part of the link.',
      'pl.add': 'Add a place',
      'pl.full': 'Four places at most: remove one to add another.',
      'pl.remove': 'Remove {name}',
      'pl.try': 'Examples',
      'pl.ex.cities': 'Four largest cities',
      'pl.ex.cantons': 'Zürich, Bern, Vaud, Ticino',
      'pl.ex.lake': 'Lake Zürich, right bank',
      'pl.empty': 'No places yet.',
      'pl.one': 'Add at least one more place to compare.',
      'pl.metric': 'Metric',
      'pl.best': 'best',
      'pl.worst': 'worst',
      'pl.high': 'highest',
      'pl.low': 'lowest',
      'pl.legend': 'Per row, a value is marked best or worst (where higher or lower is better), otherwise highest or lowest, only when it stands at least 10 percentile points apart from all the others; small differences are not marked. Rank and percentile are within each place’s own level.',
      'pl.rank': '{r} of {n}',
    },
    {
      'pl.title': 'Orte vergleichen',
      'pl.intro': 'Zwei bis vier Orte nebeneinander, auf jeder Ebene. Orte über die Suche hinzufügen; die Auswahl steht im Link.',
      'pl.add': 'Ort hinzufügen',
      'pl.full': 'Höchstens vier Orte: einen entfernen, um einen anderen hinzuzufügen.',
      'pl.remove': '{name} entfernen',
      'pl.try': 'Beispiele',
      'pl.ex.cities': 'Vier grösste Städte',
      'pl.ex.cantons': 'Zürich, Bern, Waadt, Tessin',
      'pl.ex.lake': 'Zürichsee, rechtes Ufer',
      'pl.empty': 'Noch keine Orte gewählt.',
      'pl.one': 'Mindestens einen weiteren Ort hinzufügen.',
      'pl.metric': 'Kennzahl',
      'pl.best': 'beste',
      'pl.worst': 'schlechteste',
      'pl.high': 'höchste',
      'pl.low': 'tiefste',
      'pl.legend': 'Pro Zeile wird ein Wert als bester oder schlechtester (wo höher oder tiefer besser ist), sonst als höchster oder tiefster markiert, nur wenn er mindestens 10 Perzentilpunkte von allen anderen entfernt liegt; kleine Unterschiede werden nicht markiert. Rang und Perzentil gelten innerhalb der Ebene des jeweiligen Orts.',
      'pl.rank': '{r} von {n}',
    },
  );
</script>

<script lang="ts">
  // Compare places (brief 6.1): 2–4 units side by side with the profile's layout, one aligned row per
  // metric; per row the best/worst (direction-aware) or highest/lowest value is marked. Phones: the
  // table scrolls sideways with the metric column sticky. Selection in the hash: #v=places&ids=261,kanton:GE
  import PctBar from '../components/PctBar.svelte';
  import Search from '../components/Search.svelte';
  import { fmtNumber, fmtPeriod, fmtValue, unitOf } from '../lib/classify';
  import { loadTheme, placeName, precisionText, shortName, type Base, type ColumnFile, type MetricMeta } from '../lib/data';
  import { levelName, ml, t, themeName, tiedText } from '../lib/i18n.svelte';
  import { profileHref, sourceHref } from '../lib/nav';
  import { parseRef, type UnitRef } from '../lib/places';
  import { entryOf, loadPlaceLevel, themeBlocks, themeOrder, type Entry, type PlaceLevel } from '../lib/profile';
  import { app } from '../lib/state.svelte';

  interface Props {
    base: Base;
    desktop?: boolean;
  }
  let { base }: Props = $props();

  const MAX = 4;
  const ids = $derived((app.params.ids ?? '').split(',').filter(Boolean).filter((x, k, a) => a.indexOf(x) === k).slice(0, MAX));
  const units = $derived<(UnitRef & { ref: string })[]>(ids.map((r) => ({ ...parseRef(r), ref: r })));
  const levels = $derived([...new Set(units.map((u) => u.level))]);

  let pls = $state.raw<Record<string, PlaceLevel>>({});
  /** loaded theme files per level: files[level][file] */
  let files = $state.raw<Record<string, Record<string, ColumnFile>>>({});
  let open = $state<Record<string, boolean>>({});

  $effect(() => {
    for (const lv of levels) {
      if (pls[lv]) continue;
      loadPlaceLevel(lv)
        .then((p) => {
          pls = { ...pls, [lv]: p };
          files = { ...files, [lv]: { ...(files[lv] ?? {}), core: p.core } };
        })
        .catch(() => {});
    }
  });
  function need(level: string, file: string) {
    const pl = pls[level];
    if (!pl || files[level]?.[file]) return;
    loadTheme(level, file, pl.core)
      .catch(() => ({ level, units: [], metrics: {}, status_codes: {}, precision_codes: {} }) as ColumnFile)
      .then((f) => (files = { ...files, [level]: { ...(files[level] ?? {}), [file]: f } }));
  }

  function setIds(next: string[]) {
    app.params = next.length ? { ...app.params, ids: next.join(',') } : (({ ids: _, ...rest }) => rest)(app.params);
  }
  const add = (ref: string) => !ids.includes(ref) && ids.length < MAX && setIds([...ids, ref]);
  const remove = (ref: string) => setIds(ids.filter((x) => x !== ref));

  const EXAMPLES = [
    { key: 'pl.ex.cities', ids: ['261', '6621', '2701', '5586'] },
    { key: 'pl.ex.cantons', ids: ['kanton:ZH', 'kanton:BE', 'kanton:VD', 'kanton:TI'] },
    { key: 'pl.ex.lake', ids: ['154', '156', '158', '139'] },
  ];

  const idxOf = (u: UnitRef) => pls[u.level]?.index.get(u.id) ?? null;
  const nameOf = (u: UnitRef) => {
    const pl = pls[u.level];
    const i = idxOf(u);
    return pl && i !== null ? shortName(u.level, placeName(u.level, u.id, pl.name[i])) : u.id;
  };

  // themes: metrics available at any of the chosen levels
  const blocks = $derived.by(() => {
    if (!levels.length) return [];
    const per = levels.map((lv) => themeBlocks(base, lv));
    return themeOrder(base)
      .map((theme) => {
        const head = new Map<string, MetricMeta>();
        const rest = new Map<string, MetricMeta>();
        for (const bs of per) {
          const b = bs.find((x) => x.theme === theme);
          if (!b) continue;
          for (const m of b.head) head.set(m.id, m);
          for (const m of b.rest) rest.set(m.id, m);
        }
        return { theme, head: [...head.values()].sort((a, b) => a.headline! - b.headline!), rest: [...rest.values()] };
      })
      .filter((b) => b.head.length || b.rest.length);
  });
  function toggle(theme: string, rest: MetricMeta[]) {
    open = { ...open, [theme]: !open[theme] };
    if (open[theme]) for (const lv of levels) for (const f of new Set(rest.map((m) => m.file))) need(lv, f);
  }

  /** entry per unit: undefined = loading, null = not at this level */
  function cells(m: MetricMeta): (Entry | null | undefined)[] {
    return units.map((u) => {
      if (!(m.profile_levels ?? m.levels).includes(u.level)) return null;
      const pl = pls[u.level];
      const f = files[u.level]?.[m.file];
      const i = idxOf(u);
      if (!pl || !f || i === null) return undefined;
      return entryOf(pl, f, m, i);
    });
  }
  /** A value is marked as highest / lowest (best / worst) only when it stands clearly apart from every
   *  other value of the row: different at the displayed precision and at least MARK_GAP percentile points
   *  away (percentiles within each place's own level). 11.1 vs 11.5 is not marked. */
  const MARK_GAP = 10;
  function marks(m: MetricMeta, es: (Entry | null | undefined)[]): { hi: number; lo: number } | null {
    const pts = es.flatMap((e, k) => (e && e.value !== null ? [{ k, v: e.value, p: e.rank?.pct ?? null, d: fmtNumber(e.value, m.decimals) }] : []));
    if (pts.length < 2) return null;
    type P = (typeof pts)[number];
    const apart = (a: P, b: P) =>
      a.d !== b.d && (a.p !== null && b.p !== null ? Math.abs(a.p - b.p) >= MARK_GAP : Math.abs(a.v - b.v) >= 0.05 * Math.max(Math.abs(a.v), Math.abs(b.v)));
    const byV = pts.slice().sort((a, b) => a.v - b.v);
    const top = byV[byV.length - 1];
    const bot = byV[0];
    const hi = byV.every((x) => x === top || (x.v < top.v && apart(top, x))) ? top.k : -1;
    const lo = byV.every((x) => x === bot || (x.v > bot.v && apart(bot, x))) ? bot.k : -1;
    return hi < 0 && lo < 0 ? null : { hi, lo };
  }
  function markText(m: MetricMeta, kind: 'hi' | 'lo'): { text: string; good: boolean | null } {
    if (m.direction === 'higher_better') return kind === 'hi' ? { text: t('pl.best'), good: true } : { text: t('pl.worst'), good: false };
    if (m.direction === 'lower_better') return kind === 'lo' ? { text: t('pl.best'), good: true } : { text: t('pl.worst'), good: false };
    return { text: kind === 'hi' ? t('pl.high') : t('pl.low'), good: null };
  }
  const publisher = (m: MetricMeta) => base.sources.get(m.source)?.publisher.split(' (')[0] ?? m.source;
</script>

{#snippet row(m: MetricMeta)}
  {@const es = cells(m)}
  {@const mk = marks(m, es)}
  <tr>
    <th scope="row" class="mcol">
      <span class="lbl">{ml(m)}</span>
      <span class="tags">{m.unit ? unitOf(m) + ' · ' : ''}{precisionText(m.precision)}{' · '}<a href={sourceHref(m.source)}>{publisher(m)}</a></span>
    </th>
    {#each es as e, k}
      {@const mark = mk ? (mk.hi === k ? markText(m, 'hi') : mk.lo === k ? markText(m, 'lo') : null) : null}
      <td class:best={mark?.good === true} class:worst={mark?.good === false} class:ext={mark && mark.good === null}>
        {#if e === undefined}
          <span class="muted">…</span>
        {:else if e === null}
          <span class="nd"><span class="hatch"></span> {t('p.noData')}</span>
          <span class="why">{t('p.notPublished')}</span>
        {:else if e.value === null}
          <span class="nd"><span class="hatch"></span> {t('p.noData')}</span>
          <span class="why">{e.gap} · {fmtPeriod(e.period)}</span>
        {:else}
          <!-- D14: the highest / lowest badge after the value, so the values of a row align -->
          <span class="vrow"><span class="v num">{m.unit.startsWith('%') ? fmtValue(e.value, m) : fmtNumber(e.value, m.decimals)}{#if e.marks}<sup class="fl" title={e.flags.join('\n')}>{e.marks}</sup>{/if}</span>{#if mark}<span class="mk">{mark.text}</span>{/if}</span>
          {#each e.flags as f}<span class="why">{f}</span>{/each}
          <span class="yr">{fmtPeriod(e.period)}{#if e.rank}{' · '}{t('pl.rank', { r: fmtNumber(e.rank.rank, 0), n: fmtNumber(e.rank.n, 0) })}{tiedText(e.rank)}{/if}</span>
          {#if e.rank}<PctBar pct={e.rank.pct} lo={e.rank.pctLo} hi={e.rank.pctHi} label="P{Math.round(e.rank.pct)}{tiedText(e.rank, true)}" />{/if}
        {/if}
      </td>
    {/each}
  </tr>
{/snippet}

<main class="pg" id="main" tabindex="-1">
  <div class="wrap">
    <header class="head">
      <h1>{t('pl.title')}</h1>
      <p class="intro">{t('pl.intro')}</p>
      <div class="addrow">
        <div class="add">
          <Search onpick={add} exclude={ids} disabled={ids.length >= MAX} placeholder={ids.length >= MAX ? t('pl.full') : t('pl.add')} />
        </div>
        <span class="caps ex">{t('pl.try')}</span>
        {#each EXAMPLES as ex}
          <button type="button" class="chip" onclick={() => setIds(ex.ids)}>{t(ex.key)}</button>
        {/each}
      </div>
    </header>

    {#if !units.length}
      <!-- U18: an empty comparison says what to do and offers ready-made sets -->
      <section class="empty">
        <p class="eh">{t('ux.placesEmpty')}</p>
        <p class="foot">{t('ux.placesTry')}</p>
        <div class="exs">
          {#each EXAMPLES as ex}<button type="button" class="btn" onclick={() => setIds(ex.ids)}>{t(ex.key)}</button>{/each}
        </div>
      </section>
    {:else}
      {#if units.length === 1}<p class="foot">{t('pl.one')}</p>{/if}
      <p class="foot legend">{t('pl.legend')}</p>
      <div class="scroll">
        <table style="--n:{units.length}">
          <thead>
            <tr>
              <th class="mcol corner" scope="col">{t('pl.metric')}</th>
              {#each units as u (u.ref)}
                <th scope="col" class="uh">
                  <div class="uname"><a href={profileHref(u.ref)}>{nameOf(u)}</a>
                    <button type="button" class="x" aria-label={t('pl.remove', { name: nameOf(u) })} onclick={() => remove(u.ref)}>×</button></div>
                  <div class="usub">{levelName(u.level, false)}{#if pls[u.level] && idxOf(u) !== null && pls[u.level].canton[idxOf(u)!] && u.level !== 'kanton'}{' · '}{pls[u.level].canton[idxOf(u)!]}{/if}</div>
                </th>
              {/each}
            </tr>
          </thead>
          {#each blocks as b (b.theme)}
            <tbody>
              <tr class="th"><th colspan={units.length + 1} scope="colgroup"><span class="thl">{themeName(b.theme)}</span></th></tr>
              {#each b.head as m (m.id)}{@render row(m)}{/each}
              {#if open[b.theme]}{#each b.rest as m (m.id)}{@render row(m)}{/each}{/if}
              {#if b.rest.length}
                <tr class="morer"><td colspan={units.length + 1}>
                  <button type="button" class="more" aria-expanded={!!open[b.theme]} onclick={() => toggle(b.theme, b.rest)}>
                    {open[b.theme] ? t('p.showLess') : t('p.moreN', { n: b.rest.length })}
                  </button>
                </td></tr>
              {/if}
            </tbody>
          {/each}
        </table>
      </div>
    {/if}
  </div>
</main>

<style>
  .empty { margin: var(--sp-6) 0; padding: var(--sp-6) 0; border-top: var(--rule-heavy); }
  .eh { margin: 0 0 var(--sp-2); font-size: var(--fs-lead); line-height: var(--lh-lead); font-weight: 600; }
  .exs { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-2); }
  .pg:focus { outline: none; }
  .pg { flex: 1; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch; background: var(--bg); }
  .wrap { max-width: 1240px; margin: 0 auto; padding: 16px 24px 40px; }
  h1 { margin: 0; font-size: var(--fs-h2); letter-spacing: -0.03em; }
  .intro { margin: 4px 0 0; color: var(--muted); font-size: var(--fs-small); }
  .addrow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 12px 0 4px; padding-bottom: 12px; border-bottom: 3px solid var(--rule); }
  .add { width: 320px; max-width: 100%; }
  .ex { margin-left: 8px; }
  .chip { padding: 4px 10px; border: 1px solid var(--ink); background: none; cursor: pointer; font-size: var(--fs-small); white-space: nowrap; }
  .chip:hover { background: var(--panel-2); }
  .legend { margin: 10px 0 8px; max-width: 760px; }
  a { color: var(--text); text-underline-offset: 2px; }
  .muted { color: var(--muted); }

  .scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  table { border-collapse: separate; border-spacing: 0; width: 100%; min-width: calc(180px + var(--n) * 150px); table-layout: fixed; }
  .mcol { width: 300px; text-align: left; position: sticky; left: 0; z-index: 1; background: var(--panel); padding: 6px 12px 6px 0; vertical-align: top; }
  thead th { position: sticky; top: 0; z-index: 2; background: var(--panel); border-bottom: 1px solid var(--rule); vertical-align: bottom; padding: 6px 10px 6px 0; text-align: left; }
  thead .corner { z-index: 3; font-size: var(--fs-cap); text-transform: uppercase; letter-spacing: 0.06em; }
  .uname { display: flex; align-items: flex-start; justify-content: space-between; gap: 6px; font-size: var(--fs-lead); font-weight: 700; line-height: 1.2; }
  .usub { font-size: var(--fs-meta); color: var(--muted); font-weight: 400; margin-top: 2px; }
  .x { flex: none; border: 1px solid var(--ink); background: var(--panel); width: 22px; height: 22px; line-height: 1; cursor: pointer; font-size: var(--fs-body); padding: 0; }
  .lbl { display: block; font-weight: 600; font-size: var(--fs-small); line-height: 1.25; }
  .tags { display: block; font-size: var(--fs-cap); color: var(--faint); font-weight: 400; margin-top: 1px; }
  .tags a { color: var(--faint); }
  .th th { text-align: left; padding: var(--sec-top) 0 var(--sp-1); border-bottom: 3px solid var(--rule); }
  .thl { position: sticky; left: 0; font-size: var(--fs-meta); text-transform: uppercase; letter-spacing: 0.06em; }
  tbody tr:not(.th):not(.morer) > * { border-bottom: 1px solid var(--border); }
  td { vertical-align: top; padding: 6px 10px 6px 8px; font-size: var(--fs-small); border-left: 1px solid var(--border); }
  .vrow { display: flex; align-items: baseline; flex-wrap: wrap; gap: 2px var(--sp-2); }
  td .v { font-weight: 700; font-size: var(--fs-lead); line-height: var(--lh-lead); font-variant-numeric: tabular-nums; }
  td .yr { display: block; font-size: var(--fs-cap); color: var(--muted); }
  td :global(.pb) { max-width: 120px; }
  .mk { display: inline-block; font-size: var(--fs-cap); line-height: var(--lh-cap); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; padding: 0 var(--sp-1); border: 1px solid var(--ink); }
  td.best { box-shadow: inset 3px 0 0 var(--ink); }
  td.best .mk { background: var(--ink); color: var(--ink-text); }
  td.worst .mk { color: var(--muted); border-color: var(--muted); }
  td.ext { box-shadow: inset 3px 0 0 var(--border); }
  .nd { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); }
  .why { display: block; font-size: var(--fs-meta); margin-top: 2px; }
  .fl { font-size: var(--fs-cap); color: var(--text); margin-left: 2px; }
  .morer td { border-left: 0; padding: 6px 0 2px; }
  .more { border: 1px solid var(--ink); background: none; padding: 4px 10px; font-size: var(--fs-meta); font-weight: 600; cursor: pointer; position: sticky; left: 0; }
  .more[aria-expanded='true'] { background: var(--ink); color: var(--ink-text); }

  @media (max-width: 899px) {
    .wrap { padding: 12px 16px calc(32px + env(safe-area-inset-bottom)); }
    h1 { font-size: var(--fs-stat); }
    .add { width: 100%; }
    .ex { margin-left: 0; }
    .mcol { width: 132px; padding-right: 8px; }
    table { min-width: calc(132px + var(--n) * 128px); }
    .lbl { font-size: var(--fs-meta); }
    .uname { font-size: var(--fs-body); }
    td .v { font-size: var(--fs-small); }
  }
</style>
