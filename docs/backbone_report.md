# Backbone validation report

Generated 2026-11-09T22:52 · reference state **2026-01-01** · regenerate with `make validate`.

## Summary

| Check | Result | Detail |
|---|---|---|
| R1 register vs. API snapshot | PASS | 2110 vs. 2110 municipalities |
| R2 geometry for every municipality | PASS | 0 missing of 2110 |
| C1 crosswalk weights sum to 1 | PASS | 0 bad of 6314 versions |
| C2 crosswalk vs. official BFS correspondence 1960→ref | PASS | 3095 agree, 0 differ, 0 missing |
| C3 versions not reaching the reference state | info | 0 |
| T1 population totals preserved (2010–2025) | PASS | national totals per year; canton diffs listed below |
| T1b vs. BFS's own re-projection | info | 33670 of 33760 municipality-years identical |
| T2 votes: reprojected vs. BFS re-aggregation (12 vote dates) | PASS | 66895 of 67270 municipality-proposition rows identical |
| T3 jobs (STATENT) totals preserved | PASS | years 2011, 2018, 2024 |

## Crosswalk weight sources

| Source | Versions |
|---|---|
| single_successor | 3963 |
| identity | 2154 |
| pop_ha_proxy_1990 | 94 |
| pop_ha_1990 | 48 |
| pop_ha_1990_lookthrough | 12 |
| pop_ha_2019 | 10 |
| pop_ha_2014 | 10 |
| equal_no_geometry | 5 |
| pop_ha_2024 | 4 |
| pop_ha_2000 | 4 |
| pop_ha_1990+pop_ha_proxy_1990 | 3 |
| pop_ha_2012 | 2 |
| pop_ha_2023 | 2 |
| pop_ha_proxy_1990_lookthrough | 2 |
| pop_ha_2019+pop_ha_proxy_1990 | 1 |

## C2 differences vs. official correspondence

None.

## C3 versions without a successor in the reference state

None.

## T1 national population totals

| Year | Source | Reprojected | Unmapped rows |
|---|---|---|---|
| 2010 | 7,870,134 | 7,870,134 | 0 |
| 2011 | 7,954,662 | 7,954,662 | 0 |
| 2012 | 8,039,060 | 8,039,060 | 0 |
| 2013 | 8,139,631 | 8,139,631 | 0 |
| 2014 | 8,237,666 | 8,237,666 | 0 |
| 2015 | 8,327,126 | 8,327,126 | 0 |
| 2016 | 8,419,550 | 8,419,550 | 0 |
| 2017 | 8,484,130 | 8,484,130 | 0 |
| 2018 | 8,544,527 | 8,544,527 | 0 |
| 2019 | 8,606,033 | 8,606,033 | 0 |
| 2020 | 8,670,300 | 8,670,300 | 0 |
| 2021 | 8,738,791 | 8,738,791 | 0 |
| 2022 | 8,815,385 | 8,815,385 | 0 |
| 2023 | 8,962,258 | 8,962,258 | 0 |
| 2024 | 9,051,029 | 9,051,029 | 0 |
| 2025 | 9,127,125 | 9,127,125 | 0 |

Canton totals that change through reprojection (expected only for canton changes such as Moutier BE→JU, 2026):

- 2010-BE: -7,514
- 2010-FR: +48
- 2010-JU: +7,466
- 2011-BE: -7,526
- 2011-FR: +46
- 2011-JU: +7,480
- 2012-BE: -7,603
- 2012-FR: +50
- 2012-JU: +7,553
- 2013-BE: -7,657
- 2013-FR: +49
- 2013-JU: +7,608
- 2014-BE: -7,677
- 2014-FR: +48
- 2014-JU: +7,629
- 2015-BE: -7,664
- 2015-FR: +49
- 2015-JU: +7,615
- 2016-BE: -7,635
- 2016-FR: +49
- 2016-JU: +7,586
- 2017-BE: -7,523
- 2017-FR: +46
- 2017-JU: +7,477
- 2018-BE: -7,430
- 2018-FR: +46
- 2018-JU: +7,384
- 2019-BE: -7,433
- 2019-FR: +48
- 2019-JU: +7,385
- 2020-BE: -7,399
- 2020-FR: +51
- 2020-JU: +7,348
- 2021-BE: -7,313
- 2021-FR: +51
- 2021-JU: +7,262
- 2022-BE: -7,189
- 2022-JU: +7,189
- 2023-BE: -7,171
- 2023-JU: +7,171
- 2024-BE: -7,256
- 2024-JU: +7,256
- 2025-BE: -7,053
- 2025-JU: +7,053

## T1b comparison with BFS's re-projected STATPOP (PxWeb px-x-0102010000_101)

33670 of 33760 municipality-years identical; 90 differ (max relative difference 8.04%). Differences are expected only where splits or territory exchanges required weights (BFS's method is unpublished).

Municipalities with differences (all years 2010–latest):

| histId | Municipality | Years differing | Max abs. diff (persons) | Max rel. diff |
|---|---|---|---|---|
| 16589 | Verzasca | 10 | 67 | 8.04% |
| 16588 | Lavertezzo | 10 | 40 | 3.34% |
| 16587 | Cugnasco-Gerra | 10 | 31 | 1.10% |
| 15664 | Schenkon | 3 | 12 | 0.47% |
| 15663 | Beromünster | 3 | 12 | 0.21% |
| 16657 | Nürensdorf | 14 | 8 | 0.14% |
| 15513 | Buch am Irchel | 3 | 1 | 0.10% |
| 16668 | Neuendorf | 10 | 2 | 0.10% |
| 16667 | Oberbuchsiten | 10 | 2 | 0.09% |
| 16656 | Kloten | 14 | 8 | 0.04% |
| 15514 | Neftenbach | 3 | 1 | 0.02% |

## T2 federal votes: our reprojection vs. BFS's re-aggregation

Source: BFS JSON per vote on the municipality state of the vote date, reprojected with the crosswalk (sum of eligible voters, ballots, valid, yes, no), compared per municipality and proposition with BFS's file on the latest state. Pseudo-units (Swiss abroad, 9xxx) excluded.

| Vote date | Source state | Propositions | Rows identical | Yes total (source → reprojected) | Pseudo-unit rows |
|---|---|---|---|---|---|
| 1981-06-14 | 1981-01-01 | 2 | 4138 / 4190 | 1,655,102 → 1,655,102 | 6 |
| 1985-09-22 | 1984-01-01 | 3 | 6225 / 6288 | 2,600,458 → 2,600,458 | 9 |
| 1991-03-03 | 1991-01-01 | 2 | 4150 / 4192 | 1,477,891 → 1,477,891 | 4 |
| 1994-09-25 | 1994-09-01 | 2 | 4162 / 4198 | 2,415,801 → 2,415,801 | 6 |
| 1999-02-07 | 1999-01-01 | 4 | 8372 / 8416 | 4,452,060 → 4,452,060 | 12 |
| 2002-09-22 | 2002-01-01 | 4 | 8372 / 8416 | 3,877,472 → 3,877,472 | 12 |
| 2006-11-26 | 2006-10-22 | 2 | 4190 / 4208 | 2,616,561 → 2,616,561 | 10 |
| 2010-11-28 | 2010-11-21 | 4 | 8380 / 8416 | 4,871,863 → 4,871,863 | 36 |
| 2014-09-28 | 2014-05-01 | 2 | 4194 / 4208 | 1,597,490 → 1,597,490 | 22 |
| 2018-06-10 | 2018-04-01 | 2 | 4196 / 4210 | 1,736,172 → 1,736,172 | 24 |
| 2022-05-15 | 2022-05-01 | 3 | 6306 / 6318 | 4,022,684 → 4,022,684 | 36 |
| 2026-09-27 | 2026-01-01 | 2 | 4210 / 4210 | 1,486,099 → 1,486,099 | 24 |

## T3 jobs (STATENT employees, B08EMPT)

| Year | Source units | Target units | Source total | Reprojected | Unmapped |
|---|---|---|---|---|---|
| 2011 | 2212 | 2110 | 4,866,992 | 4,866,992 | 0 |
| 2018 | 2212 | 2110 | 5,252,344 | 5,252,344 | 0 |
| 2024 | 2131 | 2110 | 5,681,022 | 5,681,022 | 0 |

## Notes

- Versions from 1848–1849 have no geometry (the boundary series starts in 1850); their few splits use equal shares (`equal_no_geometry`). No dataset in the catalog is keyed on them.
- `pop_ha_proxy_1990`: splits before 1991 are weighted with the 1990 population grid, the earliest available. Long series before 1990 (census 1850–1980) carry this approximation.
- `_lookthrough`: the successor was a short-lived transitional version without geometry (e.g. Thurgau reform 1994–1998); weights go directly to the next versions with geometry.
- Canton totals change only through canton transfers: Moutier BE→JU (2026) and Clavaleyres BE→FR (2022, merged into Murten).
