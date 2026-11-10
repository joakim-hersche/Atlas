# Licence register

Brief rule 5: every dataset's terms are tracked; anything with unclear or restrictive terms is flagged and **not shipped** until cleared.
Compiled from each connector's `meta.yaml` (2026-11-10). Regenerate when sources change.

| Status | Count |
|---|---|
| to verify | 15 |
| open (stated) | 31 |
| restricted | 1 |

## Needs clearing before shipping

| Source | Status | Terms as recorded |
|---|---|---|
| `are_bauzonen` | to verify | 2022: Open Data, free use, source must be cited (sheet 'Inhalt'). 2017: unbuilt-zone results only in aggregated form (not per municipality) -> not ingested. 2012: municipal results |
| `are_zweitwohnungen` | to verify | Open use, must provide the source (opendata.swiss terms_by, linked from the STAC collection; STAC license field 'proprietary') |
| `astra_accidents` | to verify | geo.admin.ch terms of use (STAC license 'proprietary', link disclaimer.admin.ch; UNVERIFIED: free use with source) |
| `bafu_air` | to verify | STAC license 'proprietary', no licence link on the collections (UNVERIFIED: geo.admin.ch free use with source) |
| `bfe_energy` | to verify | Energie Reporter: CC BY 4.0 (README in zip). BFE solar potential: opendata.swiss terms (open use, source required; UNVERIFIED on opendata.swiss, 403 from session). Energiestädte: g |
| `bfs_census_1970_2000` | to verify | OPEN-BY – open use, the source must be provided (BFS termsOfUse; catalog marks licence UNVERIFIED for these cubes) |
| `bfs_education` | restricted | Open use, must provide the source (BFS OPEN-BY; the STAC collection links opendata.swiss terms_by_ask: commercial use needs permission) |
| `estv_tax_burden` | to verify | UNVERIFIED for the web app; ESTV statistics colophon: 'Wiedergabe unter Angabe der Quelle gestattet' |
| `estv_tax_multipliers` | to verify | UNVERIFIED for the web app; ESTV statistics colophon: 'Wiedergabe unter Angabe der Quelle gestattet' |
| `geo_identity` | to verify | swisstopo OGD – free use with source attribution (STAC lists 'proprietary'); BFS OPEN-BY |
| `kt_crime` | to verify | Per publisher (see publishers) |
| `kt_finance` | to verify | Per publisher (see publishers); several UNVERIFIED, all openly downloadable without registration |
| `kt_landprice` | to verify | Per publisher (see publishers) |
| `kt_pupils` | to verify | Per publisher (see publishers) |
| `kt_unemployment` | to verify | Per publisher (see publishers) |
| `otd_gtfs` | to verify | opentransportdata.swiss Terms of Use: commercial and non-commercial use allowed; ToU 5.1 cite opentransportdata.swiss as source; ToU 5.2 derived data must state the feed version us |

### Notes

- **Federal geodata on geo.admin.ch** (ASTRA accidents, BAFU air, ARE, BFE layers, swisstopo): the STAC catalogue lists the licence as 'proprietary', but the layer metadata marks them `chargeable: false` with the federal office as attribution. Federal open geodata are normally free to use with attribution; the binding text is on geo.admin's terms page, which is not reachable from the build environment (host not allowed). **To confirm.**
- **BFS education geodata**: OPEN-BY on BFS's side, but the STAC entry links to 'terms_by_ask' (commercial use needs permission). Gemeindebank is a personal, non-commercial project, so it is usable as long as that stays true.
- **ESTV tax calculator export**: data from ESTV's public tool; ESTV statistics allow reproduction with source. The export itself has no stated licence.
- **Cantonal sources** (`kt_*`): several publishers state no licence; data is openly downloadable without registration. The NE hazard map permits commercial use only with permission. The GR and SG hazard maps carry no licence statement on geodienste.ch.
- **ARE building zones**: 2012 municipal results are not public and 2017 unbuilt reserves may not be published per municipality — both excluded by the connector.

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
