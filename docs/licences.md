# Licence register

Brief rule 5: every dataset's terms are tracked; anything with unclear or restrictive terms is flagged and **not shipped** until cleared.
Compiled from each connector's `meta.yaml` (2026-11-10); explicit decisions are in `pipeline/licence_review.yaml` (they override the automatic text check in `pipeline/build/web.py`). Regenerate when sources change.

Gemeindebank is a personal, non-commercial, publicly reachable website. A source is **cleared** only with a quoted publisher statement that permits that use with attribution; **needs permission** where the terms require consent; **held back** where the binding terms could not be read.

## Verification pass D22 (2026-11-10)

Terms pages fetched with curl from the allowed hosts; excerpts (URL, date, quoted text) are kept in the session scratchpad `samples/licences/`. Not reachable from the build environment: opendata.swiss, geocat.ch, www.admin.ch / disclaimer.admin.ch, opendata.lu.ch, datenkatalog.statistik.zh.ch.

| Source | Verdict | Binding terms (URL) | Attribution required |
|---|---|---|---|
| `geo_identity` | **cleared** | swisstopo free geodata terms https://www.swisstopo.admin.ch/de/nutzungsbedingungen-kostenlose-geodaten-und-geodienste ("dürfen genutzt, verbreitet ... auch kommerziell genutzt werden. Eine Quellenangabe ist Pflicht"); BFS G1 asset 36390147 OPEN-BY | "© swisstopo – swissBOUNDARIES3D" (swisstopo accepts a central sources page for map apps); "Source: BFS – Generalisierte Gemeindegrenzen G1" with link |
| `bfs_accessibility` | **cleared (non-commercial)** | BFS asset https://statistik.admin.ch/de/asset/32029919: OPEN-BY. Data description PDF in the official zip: "Wiedergabe unter Angabe der Quelle für nichtkommerzielle Nutzung gestattet"; STAC: terms_by_ask. Strictest applied | "Source: BFS – Erreichbarkeit von Dienstleistungen (GEOSTAT)" + link; commercial use would need geostat@bfs.admin.ch |
| `kt_crime` | **cleared** | ZH OGD catalogue (dataset 1202, ReferenceRequired) + ZH OGD terms https://www.zh.ch/de/politik-staat/opendata.html; BS dataset 100508 CC BY 4.0 | "Kantonspolizei Zürich – PKS (OGD Kanton Zürich)"; "Statistisches Amt Basel-Stadt, CC BY 4.0" with licence link and "modified" note |
| `kt_landprice` | **cleared: `land_price_m2`, `land_price_model_m2`**; `land_transactions` held back | ZH catalogue lists indicators 199 and 477 (ReferenceRequired); indicator 402 is not in the catalogue. BL https://data.bl.ch/terms/terms-and-conditions/ ("Lizenz CC-BY (freie Nutzung mit Quellenangabe)") | "Statistisches Amt Kanton Zürich"; "Amt für Daten und Statistik Basel-Landschaft, CC BY" |
| `bfe_energy` (Energiestädte) | **cleared** (`energiestadt_*` added) | STAC ch.bfe.energiestaedte links opendata.swiss terms_by ("Freie Nutzung. Quellenangabe ist Pflicht") | "Source: BFE – Energiestädte" |
| `bfe_energy` (solar potential `en_solar_roof_*`) | held back | Aggregate file on uvek-gis.admin.ch has no licence; its opendata.swiss entry is unreadable. Underlying roof/facade layers are terms_by | – |
| `bafu_protected_areas` (parks, biotopes) | held back | STAC 'proprietary' without licence link for parks, moors, floodplains, dry grasslands; BLN part stays cleared | – |
| `astra_accidents` | held back | STAC licence link is only http://disclaimer.admin.ch (unreadable); ASTRA pages give legal bases, no reuse terms | – |
| `bafu_air` | held back | No licence link; BAFU pages state "kostenloser Download" (availability, not a licence) | – |
| `bag_premiums` | held back (re-checked 2026-11-10) | priminfo: "Prämiendaten sind als Excel- und CSV-Datei unter opendata.swiss verfügbar"; no terms on priminfo/BAG; opendata.swiss unreadable. See re-check below | – |
| `estv_tax_burden` | held back (re-checked 2026-11-10) | Calculator links only https://www.admin.ch/gov/de/start/rechtliches.html (unreadable). The quoted "Wiedergabe unter Angabe der Quelle gestattet" belongs to the DBST files, not to these exports. See re-check below | – |
| `estv_tax_multipliers` | held back (re-checked 2026-11-10) | Same calculator; ESTV Steuerfüsse xlsx carries no colophon | – |
| `kt_finance` | held back (mixed) | See cantonal table: LU, SO, AG, VD need permission; every metric mixes cantons | – |
| `kt_pupils` | held back (mixed) | ZH indicators 143/147/149 are not in the ZH OGD catalogue | – |
| `kt_unemployment` | held back (mixed) | VD needs permission (ZH 107 and GE cleared) | – |

### Cantonal publishers

| Canton | Used in | Verdict | Terms (URL, quote) |
|---|---|---|---|
| ZH | crime, finance, landprice, pupils, unemployment | cleared for catalogued files (431, 434, 435, 297, 199, 477, 107, KTZH_1202); **unclear** for 143, 147, 149, 402 (not in catalogue) | https://www.web.statistik.zh.ch/ogd/daten/zhweb.json: "NonCommercialAllowed-CommercialAllowed-ReferenceRequired"; https://www.zh.ch/de/politik-staat/opendata.html |
| BS | crime | cleared | data.bs.ch 100508: CC BY 4.0 |
| BL | finance, landprice, pupils | cleared | https://data.bl.ch/terms/terms-and-conditions/: "Alle Datensätze können unter der Lizenz CC-BY (freie Nutzung mit Quellenangabe) weiterverarbeitet und kommerziell genutzt werden." |
| FR | finance, pupils | cleared, **ShareAlike** | opendata.fr.ch 18_02_indicateurs, 15_02_eleves_lieu_domicile: CC BY-SA 4.0 (derived FR values must be offered under CC BY-SA 4.0) |
| GR | finance | cleared | data.gr.ch dfg_afg_econ_20260326: CC0 1.0 |
| TG | finance | cleared | data.tg.ch sk-stat-4: CC0 1.0 (rights: ReferenceRequired) |
| GE | finance, unemployment | cleared | https://statistique.ge.ch/mission/welcome.asp: "L'utilisation ou la reproduction des résultats statistiques ... est libre, pour autant que leur origine et leur source soient indiquées." |
| LU | finance | **needs permission** | https://www.lustat.ch/rechtliche-hinweise: "Ohne schriftliche Zustimmung von LUSTAT ... sind Reproduktionen ... für öffentliche oder kommerzielle Zwecke nicht erlaubt." LU OGD terms (opendata.lu.ch) unreadable |
| SO | finance | **needs permission** | GEFIN states no terms; https://so.ch/rechtliches/: "nur mit vorheriger schriftlicher Zustimmung der Staatskanzlei gestattet" |
| AG | finance | **needs permission** | https://www.ag.ch/de/ueber-uns/rechtliche-hinweise: "Die Verwendung von urheberrechtlich geschütztem, veröffentlichtem Material ist nur mit vorheriger schriftlicher Zustimmung der Staatskanzlei gestattet." |
| VD | finance, unemployment | **needs permission** | https://www.vd.ch/cha/bic/mentions-legales: "Toute reproduction, utilisation ou modification à des fins publiques ou commerciales ... est interdite sans l'autorisation du détenteur des droits" |

`pipeline/licence_review.yaml` can only filter whole metrics, so `kt_finance`, `kt_pupils` and `kt_unemployment` stay out until either the non-cleared cantons are dropped in the connector (per-canton filter) or permission is obtained.

### Profile and search lookups (2026-11-10)

| Source | Verdict | Binding terms (URL) | Attribution required |
|---|---|---|---|
| `swisstopo_plz` (Amtliches Ortschaftenverzeichnis mit PLZ) | **cleared** | STAC collection `ch.swisstopo-vd.ortschaftenverzeichnis_plz` links "Terms of use" https://www.swisstopo.admin.ch/ogd-conditions → https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices: "The free geodata and geoservices of swisstopo may be used, distributed and made accessible. Furthermore, they may be enriched and processed and also used commercially. A reference to the source is mandatory." (STAC licence field: 'proprietary'; the exceptions with other wording are only swissALTI Regio and swissEO) | "© swisstopo – Amtliches Ortschaftenverzeichnis mit PLZ" |
| `wikidata_cantons` (canton names de/fr/it/rm/en) | **cleared** | Wikidata data CC0 1.0, as recorded for `wikidata_identity` (www.wikidata.org blocked by the session proxy, page not re-read 2026-11-10) | none required ("Data: Wikidata" given as courtesy) |

### Attribution obligations for the sources page

- **Federal geodata (FSDI)**: cite each dataset per its own terms; publish processed data under Gemeindebank's own name (FSDI terms 3.3), not as official data.
- **swisstopo**: one of "© swisstopo" / "Federal Office of Topography swisstopo"; may be prefixed "derived from ...".
- **BFS OPEN-BY**: "Quellenangabe ist Pflicht (Autor, Titel und Link zum Datensatz)" — author, title and link per dataset. `bfs_accessibility` and `bfs_education`: non-commercial only.
- **ZH OGD (ReferenceRequired), BL CC-BY, BS CC BY 4.0, GE OCSTAT, TG**: name the publisher; for CC BY give the licence link and note that values were processed.
- **FR CC BY-SA 4.0**: attribution, licence link, and derived FR values under the same licence (relevant once `kt_finance`/`kt_pupils` ship).

### Still open (needs the owner)

- Allow **opendata.swiss**, **geocat.ch** and **www.admin.ch** for one more pass: they hold the binding terms for `bag_premiums`, `en_solar_roof_*`, `astra_accidents`, `bafu_air`, BAFU parks/biotopes and the ESTV calculator.
- Or ask the publishers by email: ESTV (tax calculator export), ASTRA (accidents), BAFU (air maps, inventories), BAG (premiums); cantons LU, SO, AG, VD for municipal finance/unemployment tables.
- Not covered by this pass: cantons being added to the `kt_*` connectors in parallel (ZG pupils and finance, SG unemployment and finance, TI finance). Verify them before any `kt_*` source is cleared.
- Connector option without any request: drop LU/SO/AG/VD rows from `kt_finance`/`kt_unemployment` and replace ZH pupils with the catalogued Bildungsstatistik dataset 3143, then clear them per canton.

### Earlier entries (not part of this pass)

| Source | Status | Terms as recorded |
|---|---|---|
| `are_bauzonen` | cleared (review) | 2022: Open Data, free use, source must be cited (sheet 'Inhalt'). 2012 and 2017 municipal results not ingested |
| `are_zweitwohnungen` | cleared (review) | Open use, must provide the source (opendata.swiss terms_by, linked from the STAC collection) |
| `bfs_census_1970_2000` | cleared (review) | OPEN-BY (BFS DAM asset 284986) |
| `bfs_education` | restricted | Open use, must provide the source (BFS OPEN-BY; STAC links terms_by_ask: commercial use needs permission). Usable while Gemeindebank stays non-commercial |
| `otd_gtfs` | open (stated) | opentransportdata.swiss Terms of Use: commercial and non-commercial use allowed; ToU 5.1 cite opentransportdata.swiss; ToU 5.2 state the feed version |

- **ARE building zones**: 2012 municipal results are not public and 2017 unbuilt reserves may not be published per municipality — both excluded by the connector.
- **Cantonal hazard maps** (`kt_hazards`): NE permits commercial use only with permission; GR and SG carry no licence statement on geodienste.ch.

## Re-check after persona review round 1 (2026-11-10)

Four reviewers asked for the tax burden and multipliers; one quoted the ESTV colophon "Wiedergabe unter Angabe der Quelle gestattet". Excerpts are in the session scratchpad `samples/licences/estv_bag_recheck_2026-11-10.txt`. The decisions are in `pipeline/licence_review.yaml` (`status: blocked` with `missing:`).

**ESTV tax burden and multipliers (`estv_tax_burden`, `estv_tax_multipliers`): still held back.**
- The quoted colophon is real, but it is in the **direct federal tax statistics** files (`estv_dbst`, sheet "Erläuterungen": "© Eidgenössische Steuerverwaltung ESTV, Oktober 2025 / Wiedergabe unter Angabe der Quelle für Nutzung gestattet."). It is not in the calculator exports or the tax burden files.
- The calculator (swisstaxcalculator.estv.admin.ch) links only to https://www.admin.ch/gov/de/start/rechtliches.html. www.admin.ch is blocked by the session proxy (CONNECT 403), so the binding text could not be read.
- These carry no reuse statement: https://www.estv.admin.ch/de/steuerbelastung-in-den-gemeinden, https://www.estv.admin.ch/de/steuerfuesse-abzuege-und-tarife-der-schweiz, https://www.estv.admin.ch/de/impressum-estv, the Steckbrief "Steuerbelastung in der Schweiz" (12.06.2025), the exported xlsx files, the 2018 Steuerbelastung xlsx and the Steuerfüsse 1995–2026 xlsx.
- The only colophon in the series is in the 2012 PDF (© BFS 2013): "Abdruck – ausser für kommerzielle Nutzung – unter Angabe der Quelle gestattet". It covers that publication only.
- **admin.ch legal notice, read 2026-11-10** (https://www.admin.ch/gov/de/start/rechtliches.html, now allowed). It is restrictive: "Durch das Herunterladen oder Kopieren von Inhalten, Bildern, Fotos oder anderen Dateien werden keinerlei Rechte bezüglich der Inhalte übertragen. [...] Für die Reproduktion jeglicher Elemente ist die schriftliche Zustimmung der Urheberrechtsträger im Voraus einzuholen." The page links no open-data terms.
- **Missing:** written consent from ESTV. The calculator exports stay blocked. The BFS OPEN-BY republications below replace them (connectors `bfs_ssv_tax_burden`, `bfs_atlas_tax_burden`).
- **Metric caveats once cleared:** keep `precision: modelled`. Values are for one standard case, reformed church member and no wealth. Multipliers are comparable within a canton only (already in the connector). The export rounds tax amounts to whole CHF, so the federal/cantonal/municipal/church split carries up to ±0.001 percentage points of rounding.

**Cleared alternative (BFS OPEN-BY, ESTV as source).** BFS republishes ESTV tax burden figures under its own OPEN-BY terms:
- *Statistik der Schweizer Städte 2026*, dataflows `DF_SSV_TAX_BRDN_*` on disseminate.stats.swiss: 180 cities, tax year 2024, five household types. https://statistik.admin.ch/de/asset/36503269 reads "Nutzungsbedingungen OPEN-BY Freie Nutzung – Quellenangabe ist Pflicht" and "Quelle(n): Eidgenössische Steuerverwaltung".
- BFS Statatlas, estimated average tax burden by labour market region, 2010–2025: https://statistik.admin.ch/de/asset/36679820 is OPEN-BY.

Both are partial (cities or regions only); they are recorded in the catalog as `bfs_ssv_tax_burden` and `bfs_atlas_tax_burden_amr`.

**BAG premiums (`bag_premiums`): still held back.** priminfo says "Prämiendaten sind als Excel- und CSV-Datei unter opendata.swiss verfügbar" and links https://opendata.swiss/de/dataset/health-insurance-premiums (403). priminfo has no imprint or terms page (404), and the BAG pages link "Rechtliches" to admin.ch (403). **Missing:** the opendata.swiss licence of that dataset (one read of opendata.swiss would settle it). The generic admin.ch notice in the BAG footer requires prior written consent, so it does not clear the premiums; only a dataset-specific open licence would.

**Draft permission request (not sent; for the owner).** To steuerstatistik@estv.admin.ch:

> Betreff: Weiterverwendung von Exporten des Steuerrechners (Steuerbelastung, Steuerfüsse)
>
> Guten Tag
>
> Ich betreibe die nichtkommerzielle, öffentlich zugängliche Website «Gemeindebank». Sie vergleicht die Schweizer Gemeinden mit offenen Daten. Ich möchte die Gesamtsteuerbelastung (Exporte «income-tax-values», Steuerjahre 2010–2026, fünf Standardfälle) und die Steuerfüsse (Export «income-tax-rates») je Gemeinde aus dem Steuerrechner der ESTV zeigen, mit der Quellenangabe «Quelle: ESTV – Steuerrechner» und einem Link.
>
> Darf ich diese Werte unter Angabe der Quelle wiedergeben und als Datei zum Herunterladen anbieten? Gilt dafür derselbe Vermerk wie für die Statistik der direkten Bundessteuer («Wiedergabe unter Angabe der Quelle für Nutzung gestattet»)?
>
> Freundliche Grüsse

## Open (licence stated by the publisher)

| Source | Terms as recorded |
|---|---|
| `are_npvm` | CC-BY-4.0 (Zenodo record); zone documentation 'Freie Nutzung. Quellenangabe ist Pflicht' |
| `bav_rail` | Open use, must provide the source (opendata.swiss terms_by) |
| `bfs_agriculture` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_agvch` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_arealstatistik` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, assets https://www.bfs.admin.ch/asset/en/DF_AREA_NOAS, .../DF_AREA_IMPV) |
| `bfs_bevnat_bilanz` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_bevnat_sdmx` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, assets https://www.bfs.admin.ch/asset/en/DF_BEVNAT_MARIAGES_2 etc.) |
| `bfs_construction` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_crossborder` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, DAM asset 36759702 / https://www.bfs.admin.ch/asset/en/DF_GGS_2) |
| `bfs_gws` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, assets https://www.bfs.admin.ch/asset/en/DF_GWS_REG1 etc.) |
| `bfs_hist_boundaries` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, DAM asset 36390147) |
| `bfs_households` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, asset https://www.bfs.admin.ch/asset/en/DF_STATPOP_PHH) |
| `bfs_migration` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_naturalisation` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_nrw` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_sdmx` | OPEN-BY – open use, the source must be provided (termsOfUse of the statistik.admin.ch asset linked from each dataflow's EXT_RESOURCE, checked for 12 flows) |
| `bfs_rents` | OPEN-BY – open use, the source must be provided (statistik.admin.ch assets 36398431, 36398447, 36503090; checked 2026-11-10) |
| `bfs_se_language_bezirk` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_social_assistance` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, DAM 36878678) |
| `bfs_statent` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_statent_geodata` | OPEN-BY – open use, the source must be provided (BFS termsOfUse; confirm per asset) |
| `bfs_statpop` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_statpop_geodata` | OPEN-BY – open use, the source must be provided (BFS termsOfUse; confirm per asset) |
| `bfs_udemo` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_vacancy` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, asset https://www.bfs.admin.ch/asset/en/DF_LWZ_1) |
| `bfs_vehicles` | OPEN-BY – open use, the source must be provided (BFS termsOfUse, assets https://www.bfs.admin.ch/asset/en/DF_MFZ_0_COMMUNE, .../DF_IVS_0_COMMUNE) |
| `bfs_votes` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `bfs_votes_gemeinde` | OPEN-BY – open use, the source must be provided (BFS termsOfUse) |
| `estv_dbst` | Wiedergabe unter Angabe der Quelle für Nutzung gestattet (file colophon, © ESTV) |
| `kt_hazards` | Per canton as listed by geodienste.ch (publishers): mostly 'Freie Nutzung. Quellenangabe ist Pflicht.' |
| `meteoswiss_climate` | CC BY (STAC collection license 'CC-BY') |
| `wikidata_identity` | Wikidata data CC0 1.0; coat-of-arms files: licence per file in identity.csv (license_short_name, attribution_required); images not downloaded |
