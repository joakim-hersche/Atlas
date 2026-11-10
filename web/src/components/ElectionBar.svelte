<script lang="ts">
  // D37 profile block: the newest National Council election for one place, all parties (adding up to
  // 100 %), with the canton's and Switzerland's party strength as reference ticks.
  import { loadCH, loadTheme, majorityValue, type Base, type ColumnFile } from '../lib/data';
  import { fmtNumber, fmtPeriod } from '../lib/classify';
  import { ml, t } from '../lib/i18n.svelte';
  import { seqRamp } from '../lib/theme';

  interface Props {
    base: Base;
    level: string;
    id: string;
    /** canton code of the place ('' for none or a canton itself) */
    canton: string;
  }
  let { base, level, id, canton }: Props = $props();

  // parties standing in the newest election (former parties have `until`); 'other' last
  const parties = $derived(
    base.metrics.filter((m) => /^nrw_share_[a-z]+$/.test(m.id) && !m.until && !m.id.includes('bloc') && m.levels.includes(level)),
  );
  let got = $state.raw<{ unit: ColumnFile[]; kt: ColumnFile[]; ch: (ColumnFile | null)[] } | null>(null);
  $effect(() => {
    const files = [...new Set(parties.map((m) => m.file))];
    let live = true;
    got = null;
    Promise.all([
      Promise.all(files.map((f) => loadTheme(level, f))),
      canton && level !== 'kanton' ? Promise.all(files.map((f) => loadTheme('kanton', f))) : Promise.resolve([]),
      Promise.all(files.map((f) => loadCH(f))),
    ])
      .then(([unit, kt, ch]) => live && (got = { unit, kt, ch }))
      .catch(() => {});
    return () => (live = false);
  });

  const find = (fs: (ColumnFile | null)[], mid: string) => fs.find((f) => f?.metrics[mid]) ?? null;
  const rows = $derived.by(() => {
    if (!got) return null;
    let period = '';
    let maj = false;
    const out = [];
    for (const m of parties) {
      const f = find(got.unit, m.id);
      const col = f?.metrics[m.id];
      const i = f?.units.indexOf(id) ?? -1;
      if (!col || i < 0) continue;
      period = col.period;
      let v = col.v[i] ?? null;
      if (v === null) {
        v = majorityValue(col, i);
        if (v !== null) maj = true;
      }
      const kf = find(got.kt, m.id);
      const kc = kf?.metrics[m.id];
      const ki = kf ? kf.units.indexOf(canton) : -1;
      const kv = kc && ki >= 0 ? (kc.v[ki] ?? majorityValue(kc, ki)) : null;
      const cf = find(got.ch, m.id);
      const cv = cf?.metrics[m.id]?.v[0] ?? null;
      if (v === null && (kv === null || kv === 0)) continue; // did not stand here
      out.push({ m, v: v ?? 0, kv, cv, other: m.id === 'nrw_share_other' });
    }
    out.sort((a, b) => Number(a.other) - Number(b.other) || b.v - a.v);
    const total = out.reduce((s, r) => s + r.v, 0);
    return { period, maj, rows: out.filter((r) => r.v > 0 || (r.kv ?? 0) > 0), total };
  });
  const ramp = seqRamp();
  const colour = (k: number) => ramp[Math.max(1, ramp.length - 1 - k)];
  const short = (lbl: string) => lbl.replace(/^(Party strength|Parteistärke|Force du parti)\s+/, '').replace(/\s*\((National Council|Nationalrat|Conseil national)\)\s*$/, '');
  const max = $derived(rows ? Math.max(1, ...rows.rows.map((r) => Math.max(r.v, r.kv ?? 0, r.cv ?? 0))) : 1);
</script>

{#if rows && rows.rows.length}
  <section class="el" aria-label={t('pf.elTitle', { y: fmtPeriod(rows.period) })}>
    <h3>{t('pf.elTitle', { y: fmtPeriod(rows.period) })}</h3>
    <div class="stack" role="img" aria-label={rows.rows.map((r) => `${short(ml(r.m))} ${fmtNumber(r.v, 1)} %`).join(', ')}>
      {#each rows.rows as r, k}<span style="width:{r.v}%; background:{r.other ? 'var(--nodata-fill)' : colour(k)}" title="{short(ml(r.m))} {fmtNumber(r.v, 1)} %"></span>{/each}
    </div>
    <table>
      <thead><tr><th></th><th class="n">%</th><th class="bar"></th>{#if canton && level !== 'kanton'}<th class="n">{canton}</th>{/if}<th class="n">CH</th></tr></thead>
      <tbody>
        {#each rows.rows as r, k}
          <tr>
            <td class="p"><i style="background:{r.other ? 'var(--nodata-fill)' : colour(k)}"></i>{short(ml(r.m))}</td>
            <td class="n num">{fmtNumber(r.v, 1)}</td>
            <td class="bar"><span class="b" style="width:{(100 * r.v) / max}%"></span>
              {#if r.kv !== null && canton && level !== 'kanton'}<span class="tk kt" style="left:calc(6px + (100% - 12px) * {r.kv / max})" title="{canton} {fmtNumber(r.kv, 1)} %"></span>{/if}
              {#if r.cv !== null}<span class="tk ch" style="left:calc(6px + (100% - 12px) * {r.cv / max})" title="CH {fmtNumber(r.cv, 1)} %"></span>{/if}</td>
            {#if canton && level !== 'kanton'}<td class="n num muted">{r.kv !== null ? fmtNumber(r.kv, 1) : '–'}</td>{/if}
            <td class="n num muted">{r.cv !== null ? fmtNumber(r.cv, 1) : '–'}</td>
          </tr>
        {/each}
        <tr class="tot"><td class="p">{t('pf.total')}</td><td class="n num">{fmtNumber(rows.total, 1)}</td><td></td>{#if canton && level !== 'kanton'}<td></td>{/if}<td></td></tr>
      </tbody>
    </table>
    <p class="note">{t('pf.elNote', { kt: canton || '–' })}</p>
    {#if rows.maj}<p class="note maj">M {t('pf.elMaj')}</p>{/if}
    {#if level === 'kanton' && (id === 'JU' || id === 'BE')}<p class="note maj">{t(id === 'JU' ? 'card.juMoutier' : 'card.beMoutier')}</p>{/if}
  </section>
{/if}

<style>
  .el { margin: 6px 0 12px; }
  h3 { margin: 0 0 6px; font-size: var(--fs-small); text-transform: uppercase; letter-spacing: 0.05em; }
  .stack { display: flex; height: 14px; border: 1px solid var(--ink); margin-bottom: 6px; }
  .stack span { display: block; height: 100%; border-right: 1px solid var(--panel); }
  table { width: 100%; border-collapse: collapse; font-size: var(--fs-small); }
  th { font-weight: 600; font-size: var(--fs-cap); color: var(--muted); text-align: left; }
  td { padding: 2px 0; border-bottom: 1px solid var(--border); }
  .p { white-space: nowrap; padding-right: 6px; }
  .p i { display: inline-block; width: 9px; height: 9px; margin-right: 5px; vertical-align: 0; border: 1px solid var(--rule); }
  .n { text-align: right; width: 3.4em; padding-left: 4px; }
  .bar { position: relative; width: 45%; padding: 0 6px; }
  .b { display: block; height: 8px; background: var(--text-3); }
  .tk { position: absolute; top: 2px; bottom: 2px; width: 2px; margin-left: -1px; }
  .tk.kt { background: var(--ink); box-shadow: 0 0 0 1px var(--panel); }
  .tk.ch { background: var(--ink); width: 1px; margin-left: -0.5px; top: -1px; bottom: -1px; }
  .tot td { font-weight: 700; border-bottom: 0; }
  .muted { color: var(--muted); }
  .note { margin: 4px 0 0; font-size: var(--fs-meta); color: var(--muted); }
  .note.maj { color: var(--text); border-left: 3px solid var(--ink); padding-left: 6px; }
</style>
