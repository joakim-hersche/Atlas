# Persona review, round 1 (2026-11-10)

Nine reviewers, each given only a persona and the site address, explored the full app (build of 2026-11-10) without set questions. The personas were:
- a geographer
- a data analyst (real-estate consultancy)
- a statistician (cantonal office)
- an applied mathematician
- a casual iPhone user
- a hobby coder (who also read the repository)
- a regional economist (bank research)
- a family planning a move from Zürich
- a data journalist (Lausanne)

The condensed reports are below the synthesis. Screenshots were kept locally and are not committed.

## What reviewers valued (several independently)
- **Compare metrics** was called the best screen by the economist, journalist and coder. They praised the synced maps, the scatter by language region, and r, ρ and population-weighted r with the ecological-fallacy note.
- **Transparency** came up from almost everyone: hatched gaps with a reason, precision/source/period tags on every value, "partial: N of 26", and the honest sources page.
- **Search** handles Genf, Bienne, Sitten and postal codes with address shares.
- **Profiles** carry ranks in Switzerland and the canton, the hub travel-time table and the boundary history (Glarus Süd, Moutier).
- **The reach Play animation** is the most fun part for the casual user.
- **Links that keep the whole view**: one reviewer scripted scenarios straight into the URL.
- **Checked numbers agree**: canton mean income as a ratio of sums, Matran vacancy 104/1,040, the Wollerau brackets, and Swiss population in 2010.

## Defects found (to fix; no owner decision needed)

| # | Defect | Raised by | Status |
|---|---|---|---|
| 1 | PT outliers: Oberweningen ZH 419 min from Zürich HB; 1,150 pairs over 300 min. Cause: each hectare used its nearest stop (a sparse bus stop), not the best stop within walking distance | mathematician | **Fixed in the pipeline** (ddd8f64): Oberweningen now 38 min; 29,300 pairs shorter, none longer. Not yet in the web build |
| 2 | PT note in the app ("departure 07:59, wait at the hub included") contradicts the method, which is the median over 07:30–08:30 without the initial wait | analyst, mathematician, economist, geographer | open |
| 3 | Majority-election cantons (UR, OW, NW, GL, AR, AI) show 0.0 % for parties that did not stand. This is a **regression** from the `zero_when` fix of the same day: "party did not stand" counts as 0 inside ratios | statistician, geographer, journalist | open |
| 4 | Federal vote: canton BE and 3 districts blank, because 5 small communes are counted with neighbours (same cause as the NRW fix). The national value is shown as "not published". The vote has no title | journalist, economist, mathematician | open |
| 5 | Lakes outside municipalities (9xxx units) are missing from canton area and lake share. The municipal lake share is not comparable across lakes. Lausanne's header area includes the lake. Quantile classes collapse to one class with many ties (lake share) | geographer, analyst, mathematician, journalist, family, casual | open |
| 6 | Higher levels go blank when one municipality is suppressed or missing (tertiary education 14/26 cantons, out-commuter share BE/FR/GR/TI/VS, births per 1,000 for every canton). Published canton/national values are not used as a fallback. The missing-value reasons are wrong ("no data for this year", "not published", "medians cannot be aggregated" for district-only survey data) | statistician, economist, geographer, mathematician | open |
| 7 | Out-commuter share at canton/labour-market level is the sum of people leaving their own municipality (AG 80 %), so it reads as cross-canton commuting | economist | open |
| 8 | Arealstatistik defaults to the incomplete 2020/25 round (1,007 municipalities, ranks "of 1,007"). The Swiss value comes from 2013/18. It is tagged exact although it is a sample survey | statistician, geographer, analyst, family | open |
| 9 | Category values in German in the English UI ("Französisch", "Städtisch"). Units in English in the German UI | analyst, journalist, casual, geographer, coder | open |
| 10 | Coverage labels don't match the data (unemployment "4 of 26" but 2025 is GE only; land price 30 municipalities). Social assistance is "exact · national" although GR is hatched | economist, statistician | open |
| 11 | Ranks: tied values get the best rank in the canton but the worst nationally; percentile uses the midpoint. Compare places marks 11.1 vs 11.5 as highest/lowest | statistician, mathematician | open |
| 12 | Level switch silently swaps the metric (sunshine → renewable heating). On phone, "More" covers the map. The square "fit" button looks like fullscreen | casual | open |
| 13 | BFS-number search fails (cut off behind postal-code hits). On phone, the selection card covers the sheet tabs. Hard-coded "2’110" with a curly apostrophe. Ignored hash parameters stay in the URL | coder | open |
| 14 | Statistics panel ignores filters. Compare metrics drops filters and takes about 8 s | journalist, analyst | open |
| 15 | Small items:<br>- OLS slope without unit and with too many decimals<br>- one tick on log axes<br>- regression line past the plot<br>- sparklines without a zero baseline<br>- lightest class ≈ lake colour<br>- "#6870" in the vote label<br>- metric picker clips units<br>- names break mid-word<br>- "(brief rule 5)" and "UNVERIFIED" on the public sources page<br>- two vacancy and two BEV-share metrics unexplained<br>- car "nearest hub" credited to Gemeindebank instead of ARE NPVM<br>- PLZ 4058 lists Riehen at 0.0 %<br>- "0.50" unexplained in similar places | various | open |
| 16 | Count metric (population) as the default choropleth breaks a cartographic rule; default to density or symbols | geographer | open |
| 17 | Contributor experience:<br>- README stale<br>- no LICENSE file<br>- frontend can't run after cloning (no data)<br>- thin tests<br>- one 1.27 MB JS chunk<br>- Google Fonts as a third party<br>- dead dark-mode code<br>- nav buttons not links<br>- no h1 or skip link | coder | open |

## Feature requests (by number of reviewers asking)

| Request | Who | Count |
|---|---|---|
| PT times people can check against the SBB app: towards the hub in the morning (commute direction), a station-to-station figure next to door-to-door, a spread over the hour, the method stated in one line | family, mathematician, analyst, economist, journalist, casual, geographer | 7 |
| Export: CSV of the ranking/filtered table; PNG/SVG of maps and charts with a source line; full dataset (Parquet) | analyst, economist, journalist, coder, geographer | 5 |
| Tax burden by household type and tax multipliers (currently held back for licence) | family, analyst, economist, casual | 4 |
| Rents / prices beyond ZH and BL | family, analyst, economist, casual | 4 |
| Vote picker for all 511 votes with titles (FR/DE/IT), national and cantonal results, Ständemehr; diverging scale around 50 % | journalist, economist, mathematician | 3 |
| Small-number policy: flag or hide unstable rates, pooled 3–5-year rates, reliability badges or intervals for survey/modelled values | statistician, economist, mathematician | 3 |
| Zoom to matches / selected row | family, analyst | 2 |
| Latest available year as fallback everywhere | family, statistician | 2 |
| Change between two years as a metric | economist, (statistician: small multiples) | 2 |
| Map reference layer (lake/city labels), finer boundaries on zoom | geographer | 1 |
| French UI | journalist | 1 |
| Plain-language summary per place, jargon explained (quantile, P10/P90, z-score…), real fullscreen map | casual | 1 |
| Weighted aggregate for the filtered set ("French-speaking CH: X % yes"), statistics that follow filters | journalist | 1 |
| Custom similarity (choose metrics and weights, per-dimension contribution); "any hub"/k-th nearest hub filter; PT minus car | mathematician | 1 |
| Fixed class breaks across years; series-break markers | statistician | 1 |
| Moran's I / LISA / bivariate choropleth; older-boundary view; GeoPackage download | geographer | 1 |
| Embeddable view (iframe) | journalist | 1 |
| Noise, childcare, school locations | family | 1 |
| Data release + sample data + CI; unit tests; code splitting | coder | 1 |

## Questions reviewers asked, with answers

- **PT destination point and departure** (several): population-weighted over inhabited hectares, each walking to the best stop within 1.5 km. Median over the 61 departure minutes 07:30–08:30, wait at the hub excluded. The app text is wrong (defect 2).
- **Why is the hub's own municipality 18 min?** It is the median trip from the hub station to where people live in that municipality (tram/bus plus walk), not zero.
- **Which 3 municipalities have no PT time?** Schelten and Seehof BE (no stop within walking distance) and Blatten VS (village destroyed by the May 2025 landslide).
- **Where is the tax burden?** ESTV tax burden and multipliers are held back pending licence evidence. The economist points out that the ESTV colophon reads "Wiedergabe unter Angabe der Quelle gestattet"; to re-check.
- **Agglomerations, 84 units?** BFS "Agglomerationen 2020" (the 2012 definition is older); to state on the sources page.
- **Population 2024 provisional or final?** To check and label.
- **Is the September 2026 vote missing?** To check the vote cube vintage. There is no download date in the app (requested by the analyst).
- **Similarity measure**: RMS of z-scores over 11 headline metrics with equal weights. Correlated metrics weigh more. Mahalanobis/PCA is a fair suggestion.

---

## Condensed reports

### Hobby coder
Praised: breadth (662 metrics), honest sources page, search (Genf/Bienne/PLZ shares), reach animation + method doc, compare metrics screen, hash state + back button, 1.06 MB gz first load, clean reproducible build.
Bugs: (1) BFS-number search fails: places.ts search() adds BFS hit after ≤13 PLZ-prefix hits then slice cuts it — put BFS hit first. (2) Phone: selection card overlaps sheet tabs (ph-ranking.png). (3) App.svelte:86 hardcodes 2’110 with curly apostrophe vs 2'110 elsewhere. (4) Invalid hash params (m=does_not_exist, y=1990) silently fall back but stay in URL. (5) DE gaps: legend "persons", "Quantile"; sources intro says "(brief rule 5)" jargon.
Contributor issues: can't run frontend after clone (data gitignored, no workflow); README stale (Checkpoint 3, no web-data/web-app); no LICENSE file; FR CC BY-SA only in docs; thin tests (15 pytest, no frontend tests); single 1.27 MB JS chunk; Google Fonts third party (self-host Inter); dead dark-mode code in theme.ts; nav buttons not links (no middle-click), no h1/skip link, radio groups each a tab stop.
Questions: publish data release (observation.parquet + metrics CSV w/ licence)? PT time to own hub city (Genève 17 min) not explained in card.
Requests: (1) data snapshots Parquet/CSV as release assets; (2) sample data so npm run dev works + CI; (3) CSV download of ranking; (4) unit tests search/hash/classify; (5) code splitting + self-hosted fonts; (6) real <a href> nav + arrow-key radios.

### Relocating family (Zürich→ commute HB + Zug)
Got shortlist via two reach filters (HB≤40, Zug≤40 → 10; widened → 27) sorted by share 0–19: Oberrieden, Thalwil, Hedingen/Affoltern a.A., Cham/Steinhausen.
Helped: filter+ranking, hub table on profile, compare places best/worst, partial labels, sources page, phone works, shareable link.
Problems: (1) no tax burden (held back) — most important; "Steuerfuss" finds nothing. (2) no rents/prices outside ZH/BL; "Miete" nothing. (3) profiles show "no data for this year" instead of latest available (Arealstatistik 2020/25 half coverage; wooded share = "green"). (4) pupils metric "not covered by this canton" for Thalwil ZH and Baar ZG though both cantons listed as sources — looks wrong. (5) commute direction: times from hub outward, departure 07:59; they commute to hub; Zug→HB 36, Baar 41 feel long vs ~25 direct. (6) map doesn't zoom to matches / tapped row; phone quick card covers selection. (7) search: "Grün" returns GPs/new enterprises; "Lärm","Kita" nothing; DE units in English. (8) lake share Thalwil 0.0% ranked 3/160. (9) family data thin: couples with children census 2000 only; crime only 37 ZH municipalities, none ZG.
Questions: PT door-to-door to village centre or station? Tax burden coming back?
Wishes: (1) tax burden married couple 2 kids by income; (2) rents/asking prices even district level; (3) commute towards hub + "both commutes" sum/max filter; (4) fall back to latest available year everywhere; (5) zoom to matches/selected row; (6) noise, childcare, school locations.

### Data analyst (consultancy, Power BI)
Praised: URL holds state (wrote scenario into link); ranking adds filter columns (17 rows client-ready); numbers consistent (Matran vacancy 104/1040; CH & Zürich 2010 pop match BFS); precision/source/period + partial N of 26; scatter r/ρ/weighted r.
Problems: (1) NO EXPORT — blocks use. (2) PT times vs common knowledge: Winterthur→HB 38 (known ~20), Bern 75; app says "Weekday departure 07:59 … wait at hub included" reads as single departure, contradicts doc (median 07:30–08:30, avg wait, walk from pop-weighted hectares); car Zürich→Bern 108 looks loaded network. (3) lake share: quantile classes collapse to one ("0–92.3, 2'110") when median 0; values not comparable across lakes (Léman up to 92%, Horgen/Küsnacht/Thalwil 0). (4) Arealstatistik 2020/25 ranks "of 1'007" but tagged exact, no partial flag. (5) Pop 2024 CH 9'051'029 vs remembered definitive ~9'048'900 — provisional? label it. (6) typology labels German in EN UI; "#6870" in vote metric label; metric picker clips unit text at 1440; names break mid-word in ranking; no zoom to matches; compare metrics ~8 s to draw, drops filters; two "Vacancy rate" metrics unexplained; two EV-share metrics (2025 vs 2026-10); sources page shows "UNVERIFIED" to public; headline language metrics from census 2000.
Questions: latest federal vote 2026-06-14 — Sept vote not loaded? no download date anywhere. Can I get observation Parquet? Why no ESTV tax burden?
Requests: (1) CSV/XLSX export of ranking + full dataset Parquet link; (2) build/fetch date per source/metric in app; (3) tax burden + Steuerfuss; (4) journey-planner PT option (no wait, station-to-station) + method stated in app; (5) keep filters in compare metrics, colour/limit scatter to matches; (6) add metric columns to ranking freely; (7) zoom to matches; (8) rent/price beyond ZH/BL.

### Mathematician (ETH applied maths)
Praised: aggregation honest (ratios of sums; canton mean taxable income ZH 78'792, ZG 127'550 exact; medians refused; yes share = yes/(yes+no)); pop change 10y matches; CH 2010 7'870'134; compare r/ρ/weighted r reproduced; reach method doc excellent.
Wrong: (1) PT OUTLIERS: Oberweningen ZH 419 min from HB (and to nearest hub), Schleinikon 422, Brot-Plamboz NE 471; 1'133 hub–municipality pairs >300 min; La Sonnaz FR (next to Fribourg) 153. Likely window truncation (connections 06:30–18:00, departures to 09:30) or closure → should be no_data. (2) NEAREST STOP not best stop: Albula order broken (Samedan 140, St. Moritz 133, Celerina 125); hectare should take min(walk+ride) over all stops ≤1.5 km. (3) direction hub→municipality (reverse commute); triangle inequality violations up to 200 min. (4) UI note "departure 07:59, wait at hub included" vs counts from median journey time excl wait. (5) quantile classes collapse with ties (lake share one class) → separate zero class. (6) rank vs percentile tie rules differ (Küsnacht lake 0.0% rank 205 · P45). (7) lake share depends on legal boundaries (Meilen/Küsnacht/Stäfa 0, Lausanne 38.8%; CH 2.1% = only municipal lake area; Arealstatistik lakes Lausanne 9 ha vs 2'626 here). (8) wrong explanation for 29 missing metrics at higher levels: note says medians/indices/travel times but they are SE language district-only. (9) federal votes unnamed ("Yes share · vote no. 6870"); "No national value published" false — ratio rule would compute. (10) OLS slope "5'942.55" no unit/too many decimals; two BEV shares diff sources/themes; PV per resident & pop-weighted temperature list weighted-mean rule but limited to municipality level.
Questions: similar places = RMS over equal-weight z-scores (income/tertiary/left bloc correlated → triple weight) — Mahalanobis/PCA? Zürich lacks settlement share → 10 vs 11 dims comparable? hub own municipality 18 min (d(x,x)≠0) needs note.
Requests: (1) PT profile over departure hour (P10/median/P90) + both directions; (2) "any hub"/k-th nearest hub filter + PT minus car; (3) similarity panel choose metrics/weights + per-dimension contribution; (4) interval estimates for survey metrics in rankings; (5) median estimated from income class counts.

### Statistician (cantonal office)
Praised: hatched gaps with reasons, precision/source/period tags, vintage per dataset on sources page; weighted r + "across municipalities, not individuals"; distribution panel n/P10/P90/min/max names; diverging centred at 0; boundary history.
Wrong: (1) MAJORITY CANTONS: UR, OW, NW, AR, AI left bloc 0.0% (Rehetobel SP 0.0 Greens 0.0 rank 1 of 20 AR) — should be not applicable; zeros enter classes/ranks/correlations. [REGRESSION from zero_when fix] (2) small numbers: Lütschental 242 residents birth rate 24.8‰ rank 2; net migration −172‰ (Balm b. G.) to +195‰ (Sergey); Romont BE social assistance 18.7%; no pooling/flag/interval. (3) suppression: births 1–3 suppressed but 0 kept → ranking loses small low-nonzero places, tail bias; sparklines draw straight lines across suppressed years. (4) higher levels drop out: tertiary at canton only 14/26 (BE "no data") because suppressed municipalities fail aggregate — use published canton values. (5) "No national value published" wrong for tertiary 25–64 and social assistance. (6) social assistance labelled "exact · national" though GR hatched; Hitzkirch profile says "modelled". (7) settlement area defaults to 2020/25 (incomplete, 1'007 municipalities, west/north), ranks "571 of 1'007", CH value from 2013/18 → default to last complete round. (8) quantile breaks recomputed per year (tertiary 1990 median 13% vs 2023 35% look same); census 1990/2000 vs imputed from 2017 methodological break unflagged. (9) quintiles on 14 cantons → silly shared endpoints. (10) lightest class ≈ lake colour. (11) ties: best rank in canton but worst nationally → say "tied". (12) compare places marks 11.1 vs 11.5 HIGHEST/LOWEST — overstates.
Questions: source of 2025 social assistance rate? STATENT <4→4 rule in rates? tertiary counts rebuilt from rounded shares — rounding error when aggregated?
Requests: (1) small-number policy: threshold flag/hide + 3/5-year pooled rates (births, migration, social assistance); (2) fixed class breaks across years option + series break markers; (3) use published canton/national values when can't aggregate + correct missing reason; (4) CIs or low-reliability badge for modelled/survey, rank intervals; (5) handle majority-election cantons; (6) latest complete period for Arealstatistik; (7) small multiples several years.

### Economist (bank research)
Praised: compare metrics (best thing; would use in report), ESTV income bracket detail adds up (Wollerau 3,812; 39.3%=1,499/3,812), honest gaps, labour market areas as level, profile ranks + hub table.
Wrong: (1) tax burden + multipliers held back — core for tax competition; ESTV colophon "Wiedergabe unter Angabe der Quelle gestattet" → clear it; same for health premiums. (2) out-commuter share at higher levels misleading: AG 80.1%, BL 80.1% = sum of leaving own municipality, not canton/AMR → redefine per level or relabel. (3) five missing municipalities blank whole cantons BE, FR, GR, TI, VS for out-commuter share; card says "no data for this year" (wrong reason). (4) PT single departure 07:59 incl wait (Zürich→Zürich 18, Zug→HB 36); wrong direction; 30-min Zürich filter returns only 36 municipalities w/o Winterthur/Zug. (5) coverage labels mismatch: unemployment "partial 4 of 26" but 2025 only GE 45 municipalities; land price only 30 municipalities. (6) federal vote untitled "vote no. 6870"; CH total "no national value published" though BFS publishes. (7) tiny municipalities dominate mean income ranking (Vaux-sur-Morges, Bedretto), no small-n flag/taxpayer count column; 2008 CH total blank vs 2023 present; OLS slope "−0.0001" per CHF → per 10k; log axes only one tick ("100k"); land-price scatter regression line overshoots plot top.
Questions: when ESTV burden ships? mean taxable income all taxpayers incl special cases? median available? votes selectable from 511?
Requests: (1) ESTV tax burden standard households + multipliers + change since year X; (2) export CSV ranking/scatter + PNG/SVG maps/charts with auto source line; (3) change between two years metric; (4) commuting per level (leaving canton/AMR) + inbound morning PT averaged over window; (5) median income, rents/transaction prices beyond ZH/BL; (6) vote picker with titles; (7) minimum-size filter / small-municipality flag.

### Journalist (Lausanne daily)
Praised: compare-metrics scatter by language region (Röstigraben chart: Yes vs SVP, French below German) — best thing; SVP slider to 1971 spreading; Moutier BE→JU boundary history; search Geneve/Genf/Sitten/Bienne/PLZ; source/precision/period citable; mobile layout good.
Wrong: (1) VOTE: Bern canton Yes share "–" plus districts Seeland, Emmental, Bern-Mittelland — 5 tiny communes no data (Meienried, Hellsau, Deisswil b.M., Oberhünigen, Niedermuhlern) → showstopper (same pooling issue as NRW, votes not fixed). (2) "Switzerland: – (no national value published)" for vote and SVP 1971; SVP 2023 28.0% vs official 27.9% — check. (3) vote untitled "2026-06-14, vote no. 6870"; only one of 511 exposed. (4) Lausanne area 67.6 km² vs official ~41.4 (includes lake); header area vs land-area density mismatch; Lausanne wooded share and lake share both 38.8% — suspicious, check. (5) PT times 20–30 min too long to quote (Lausanne→Genève 61, Fribourg 72, Bern 93, Zürich 158; Lausanne→Lausanne 18). (6) category labels German in EN UI ("Französisch", "Städtisch", "Ländliche Zentrumsgemeinde"); scatter legend says "French" → inconsistent. (7) Statistics panel ignores filters (shows all 2,105 with French-only filter). (8) Yes share uses sequential blue → diverging centred 50%. (9) language data census 2000 only at commune level.
Questions: why does a no-data commune blank its canton (sum existing + flag)? 1971 SVP 0 = did not run vs 0 votes (AI, UR, SP 0.0% cases)? population end-of-year STATPOP provisional/final?
Requests: (1) vote picker all 511 with FR/DE/IT titles, national & cantonal results, Ständemehr count; (2) export PNG/SVG map with credit + CSV; (3) French UI; (4) diverging 50% for votes + difference-from-national metric; (5) embeddable iframe of a view; (6) weighted aggregate for filtered set ("French-speaking CH: X% yes"); (7) station-to-station PT option + one-line method.

### Casual phone user (Basel, parents in Minusio TI)
Loved: quick search (Genf, postcode, Enter → page); town page big numbers, other-language names, trend lines; reach Play animation most fun; sunshine map + ranking (Minusio #11) shareable; compare with sideways swipe.
Annoyed: Basel→Zürich HB 75 min (real <1h), Basel→Basel SBB 18, Liestal 26 (train ~10) → stopped trusting times. Wanted rent + tax, none; "rent" search gave "Adults living with parent(s)"; land price & finances "No data" for Basel. Income & tax "20 more" = bracket counts list in strange order. Switching to Cantons swapped sunshine for "Renewable heating share" unasked. "More" arrow makes panel cover map; Play then invisible. Square button looks like fullscreen but isn't; map small on phone. Language stats 2000.
Jargon: Quantile/Equal/Cont., "axis clipped at P1/P99", n = 2'110, P96, P10/P90, "normal cases", "Old-age dependency ratio", "z-scores", "Labour market area", "Self-financing ratio"; German labels in EN ("Italienisch", "Städtische Gemeinde einer mittelgrossen Agglomeration").
Off: Basel lake share 0.0% ranked 205/2'110 marker mid; Similar places Basel → Morges first with unexplained "0.50"; postcode 4058 shows "Riehen, Basel 0.0% of addresses".
Wishes: rent & tax per town; plain "In short" summary at top of each town; big full-screen map button; travel times matching SBB app; "find places like X near Basel" button.
Would return for sunshine ranking + reach animation; not yet to pick a place to move.

### Geographer (spatial planning)
Praised: Glarus Süd boundary history (2004/2006 absorptions, 2011 merger w/ BFS nos); harmonised series stated; density per land km²; hatched gaps; partial N of 26; tied ranks ok; honest sources page (vintage, UNVERIFIED, boundary estimate); weighted r + ecological note; search Genf/Bienne/Sankt Moritz/PLZ shares.
Wrong: (1) canton areas omit lakes outside municipalities (BE 5,820 vs official ~5,959 km²; ZH 1,665 vs ~1,729); lake share BE 0.0, ZH 0.2 vs VD 12.1 → not comparable. (2) live births per 1,000 "No data" for every canton in compare places though municipalities have 2025. (3) majority-vote cantons UR, OW, NW, GL, AI, AR: FDP/Grüne 0.0% (Glarus Süd), central CH 0% block, ranked vs proportional → flag/exclude. (4) Arealstatistik default 2020/25 half hatched, CH ref 2013/18; log scale for a share; "exact" for sample-point survey. (5) sparklines exaggerate small changes (density 23→22 cliff) — no zero baseline. (6) car-time source disagreement: "Car to nearest hub" credits "Computed by Gemeindebank", hub table says ARE NPVM.
Cartographic: default = absolute population choropleth (breaks rule) → default density or symbols for counts; no finer boundaries on zoom (TI coarse, lake slivers); no labels/reference layer; car mode Lugano routes into Italy over blank background; category values German in EN.
Questions: agglomeration definition with 84 units (St. Moritz smallest) vs BFS 2012 49 + cores? social assistance & Matura rate "not aggregatable" at canton though BFS publishes? PT one 07:53 departure — sensitivity vs window median? destination point? which 3 municipalities no PT? pooled Structural Survey language planned?
Requests: (1) allocate lakes outside municipalities; canton totals match official; (2) light reference layer (lake/city labels) + finer boundaries on zoom; (3) majority-vote flag; (4) Moran's I + LISA + bivariate choropleth; (5) symbols default for counts; (6) download current view CSV + GeoPackage with citation; (7) view on older boundaries (2000) besides harmonised.
