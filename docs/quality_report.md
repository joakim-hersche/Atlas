# Data quality report

Generated 2026-11-10T11:26 · reference state 2026-01-01 · regenerate with `make quality`. Plan: [`validation_plan.md`](validation_plan.md).

Metrics: 725 defined (518 base, 207 derived) · rows: 31,470,182

## A. Additivity — municipalities vs. published district/canton/national values

Summary: 633 metric×level comparisons, 611 pass, 22 with failures.

| Source | Level | Metric | Compared | Exact | Explained (transfers / unallocated) | Within 0.5% | Documented difference | Fail | Max rel. residual |
|---|---|---|---|---|---|---|---|---|---|
| bfs_votes_gemeinde | kanton | vote_eligible | 13180 | 8992 | 2517 | 383 | 0 | **133** | 3.701% |
| bfs_arealstatistik | bezirk | area_total_ha | 632 | 614 | 0 | 9 | 0 | **9** | 1.777% |
| bfs_arealstatistik | bezirk | area_water_ha | 632 | 623 | 0 | 0 | 0 | **9** | 0.590% |
| bfs_arealstatistik | bezirk | area_wooded_ha | 632 | 619 | 0 | 4 | 0 | **9** | 8.642% |
| bfs_votes_gemeinde | kanton | vote_valid | 13180 | 8372 | 3419 | 233 | 0 | **6** | 7.078% |
| bfs_nrw | kanton | nrw_fw_cvp | 279 | 177 | 82 | 15 | 0 | **5** | 2.348% |
| bfs_nrw | kanton | nrw_fw_fdp | 311 | 211 | 77 | 19 | 0 | **5** | 4.372% |
| bfs_nrw | kanton | nrw_fw_total | 357 | 245 | 97 | 11 | 0 | **5** | 3.488% |
| bfs_arealstatistik | bezirk | area_agriculture_ha | 632 | 624 | 0 | 4 | 0 | **4** | 0.649% |
| bfs_arealstatistik | bezirk | area_unproductive_ha | 632 | 619 | 0 | 9 | 0 | **4** | 2.764% |
| bfs_nrw | kanton | nrw_fw_sp | 303 | 201 | 77 | 22 | 0 | **4** | 5.170% |
| bfs_nrw | schweiz | nrw_fw_fdp | 14 | 0 | 1 | 4 | 0 | **4** | 3.642% |
| bfs_nrw | kanton | nrw_ballots_invalid | 357 | 261 | 92 | 1 | 0 | **3** | 2.941% |
| bfs_votes_gemeinde | kanton | vote_no | 13180 | 8520 | 3288 | 219 | 0 | **3** | 0.763% |
| bfs_census_1970_2000 | kanton | vz_rel_other_christian | 104 | 92 | 4 | 6 | 0 | **2** | 1.747% |
| bfs_construction | kanton | con_exp_maintenance | 806 | 9 | 738 | 57 | 0 | **2** | 2.935% |
| bfs_nrw | kanton | nrw_fw_csp | 29 | 18 | 8 | 1 | 0 | **2** | 2.916% |
| bfs_nrw | kanton | nrw_fw_other | 277 | 195 | 75 | 5 | 0 | **2** | 4.537% |
| bfs_nrw | kanton | nrw_fw_sep | 7 | 0 | 2 | 3 | 0 | **2** | 0.665% |
| bfs_census_1970_2000 | kanton | vz_rel_no_answer | 104 | 94 | 6 | 3 | 0 | **1** | 0.559% |
| bfs_nrw | kanton | nrw_fw_svp | 249 | 155 | 74 | 20 | 0 | **1** | 9.098% |
| bfs_vehicles | kanton | mfz_newreg_bev | 416 | 301 | 113 | 2 | 0 | **1** | 3.265% |
| bfe_energy | kanton | en_charging_spots | 834 | 815 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_ecar_count | 1592 | 1592 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_elec_consumption_mwh | 978 | 978 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_heat_nonrenewable_count | 1592 | 1592 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_heat_renewable_count | 1592 | 1592 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_pv_installed_kwp | 1592 | 1592 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_renelec_hydro_mwh | 858 | 855 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_renelec_production_mwh | 858 | 855 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_renelec_solar_mwh | 858 | 852 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_charging_spots | 34 | 33 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_ecar_count | 66 | 66 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_elec_consumption_mwh | 40 | 40 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_heat_nonrenewable_count | 66 | 66 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_heat_renewable_count | 66 | 66 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_pv_installed_kwp | 66 | 66 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_renelec_hydro_mwh | 35 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_renelec_production_mwh | 35 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_renelec_solar_mwh | 35 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_area_arable_ha | 4004 | 1824 | 8 | 0 | 2172 ¹ | 0 | 100.000% |
| bfs_agriculture | bezirk | agr_area_grassland_ha | 4004 | 1670 | 7 | 0 | 2327 ¹ | 0 | 1.010% |
| bfs_agriculture | bezirk | agr_area_ha | 4004 | 1636 | 3 | 0 | 2365 ¹ | 0 | 0.249% |
| bfs_agriculture | bezirk | agr_area_organic_ha | 3575 | 1813 | 0 | 0 | 1764 ¹ | 0 | 50.000% |
| bfs_agriculture | bezirk | agr_area_permanent_crops_ha | 4004 | 1985 | 4 | 0 | 2021 ¹ | 0 | 100.000% |
| bfs_agriculture | bezirk | agr_cattle | 4004 | 3976 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_farms | 4004 | 3976 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_farms_organic | 3575 | 3568 | 7 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_goats | 4004 | 3976 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_horses | 4004 | 3976 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_pigs | 4004 | 3977 | 27 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_poultry | 4004 | 3976 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_sheep | 4004 | 3976 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_workers | 3718 | 3692 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_workers_family | 3718 | 3692 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_workers_fulltime | 3146 | 3124 | 22 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | bezirk | agr_workers_women | 3718 | 3692 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_area_arable_ha | 728 | 215 | 4 | 0 | 509 ¹ | 0 | 100.000% |
| bfs_agriculture | kanton | agr_area_grassland_ha | 728 | 177 | 10 | 0 | 541 ¹ | 0 | 0.498% |
| bfs_agriculture | kanton | agr_area_ha | 728 | 183 | 9 | 0 | 536 ¹ | 0 | 0.241% |
| bfs_agriculture | kanton | agr_area_organic_ha | 650 | 177 | 4 | 0 | 472 ¹ | 0 | 3.333% |
| bfs_agriculture | kanton | agr_area_permanent_crops_ha | 728 | 227 | 6 | 0 | 499 ¹ | 0 | 100.000% |
| bfs_agriculture | kanton | agr_cattle | 728 | 672 | 56 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_farms | 728 | 672 | 56 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_farms_organic | 650 | 636 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_goats | 728 | 672 | 56 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_horses | 728 | 672 | 56 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_pigs | 728 | 674 | 54 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_poultry | 728 | 672 | 56 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_sheep | 728 | 672 | 56 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_workers | 676 | 624 | 52 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_workers_family | 676 | 624 | 52 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_workers_fulltime | 572 | 528 | 44 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | kanton | agr_workers_women | 676 | 624 | 52 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_area_arable_ha | 28 | 0 | 0 | 0 | 28 ¹ | 0 | 0.017% |
| bfs_agriculture | schweiz | agr_area_grassland_ha | 28 | 0 | 0 | 0 | 28 ¹ | 0 | 0.005% |
| bfs_agriculture | schweiz | agr_area_ha | 28 | 0 | 0 | 0 | 28 ¹ | 0 | 0.002% |
| bfs_agriculture | schweiz | agr_area_organic_ha | 25 | 2 | 0 | 0 | 23 ¹ | 0 | 0.015% |
| bfs_agriculture | schweiz | agr_area_permanent_crops_ha | 28 | 1 | 0 | 0 | 27 ¹ | 0 | 0.232% |
| bfs_agriculture | schweiz | agr_cattle | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_farms | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_farms_organic | 25 | 25 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_goats | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_horses | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_pigs | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_poultry | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_sheep | 28 | 28 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_workers | 26 | 26 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_workers_family | 26 | 26 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_workers_fulltime | 22 | 22 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_agriculture | schweiz | agr_workers_women | 26 | 26 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | bezirk | area_building_ha | 632 | 628 | 0 | 4 | 0 | 0 | 0.143% |
| bfs_arealstatistik | bezirk | area_glacier_ha | 632 | 632 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | bezirk | area_industrial_ha | 632 | 632 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | bezirk | area_settlement_base_ha | 488 | 488 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | bezirk | area_settlement_ha | 632 | 627 | 0 | 5 | 0 | 0 | 0.065% |
| bfs_arealstatistik | bezirk | area_transport_ha | 632 | 632 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_agriculture_ha | 114 | 106 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_building_ha | 114 | 76 | 38 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_glacier_ha | 114 | 114 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_industrial_ha | 114 | 105 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_sealed_ha | 114 | 57 | 57 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_settlement_base_ha | 88 | 45 | 43 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_settlement_ha | 114 | 46 | 68 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_total_ha | 114 | 32 | 82 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_transport_ha | 114 | 99 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_unproductive_ha | 114 | 32 | 82 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_water_ha | 114 | 32 | 82 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_wooded_ha | 114 | 62 | 52 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_agriculture_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_building_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_glacier_ha | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_industrial_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_sealed_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_settlement_base_ha | 3 | 0 | 3 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_settlement_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_total_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_transport_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_unproductive_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_water_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | schweiz | area_wooded_ha | 4 | 0 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | bezirk | bil_births | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.079% |
| bfs_bevnat_bilanz | bezirk | bil_deaths | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.049% |
| bfs_bevnat_bilanz | bezirk | bil_emigration | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.081% |
| bfs_bevnat_bilanz | bezirk | bil_immigration | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.062% |
| bfs_bevnat_bilanz | bezirk | bil_intercant_in | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.054% |
| bfs_bevnat_bilanz | bezirk | bil_intercant_out | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.054% |
| bfs_bevnat_bilanz | bezirk | bil_intracant_in | 6435 | 6308 | 45 | 2 | 0 | 0 | 0.077% |
| bfs_bevnat_bilanz | bezirk | bil_intracant_out | 6435 | 6308 | 45 | 2 | 0 | 0 | 0.079% |
| bfs_bevnat_bilanz | bezirk | bil_natural_balance | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.158% |
| bfs_bevnat_bilanz | bezirk | bil_naturalisations | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | bezirk | bil_net_intercant | 6435 | 6311 | 44 | 0 | 0 | 0 | 17.746% |
| bfs_bevnat_bilanz | bezirk | bil_net_international | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.120% |
| bfs_bevnat_bilanz | bezirk | bil_net_migration | 6435 | 6310 | 45 | 0 | 0 | 0 | 0.113% |
| bfs_bevnat_bilanz | bezirk | bil_pop_dec | 6435 | 6308 | 45 | 2 | 0 | 0 | 0.063% |
| bfs_bevnat_bilanz | bezirk | bil_pop_foreign_jan | 6435 | 6308 | 45 | 2 | 0 | 0 | 0.042% |
| bfs_bevnat_bilanz | bezirk | bil_pop_jan | 6435 | 6308 | 45 | 2 | 0 | 0 | 0.062% |
| bfs_bevnat_bilanz | kanton | bil_births | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_deaths | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_emigration | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_immigration | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_intercant_in | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_intercant_out | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_intracant_in | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_intracant_out | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_natural_balance | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_naturalisations | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_net_intercant | 1170 | 1064 | 76 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_net_international | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_net_migration | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_pop_dec | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_pop_foreign_jan | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | kanton | bil_pop_jan | 1170 | 1062 | 78 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_births | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_deaths | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_emigration | 45 | 12 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_immigration | 45 | 12 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_intercant_in | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_intercant_out | 45 | 21 | 6 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_intracant_in | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_intracant_out | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_natural_balance | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_naturalisations | 45 | 26 | 1 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_net_intercant | 45 | 21 | 6 | 0 | 0 | 0 | nan% |
| bfs_bevnat_bilanz | schweiz | bil_net_international | 45 | 12 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_net_migration | 45 | 12 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_pop_dec | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_pop_foreign_jan | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_bilanz | schweiz | bil_pop_jan | 45 | 27 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | bezirk | bevnat_births | 8151 | 4191 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | bezirk | bevnat_divorces | 7886 | 964 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | bezirk | bevnat_marriages | 8150 | 2324 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | kanton | bevnat_births | 1482 | 462 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | kanton | bevnat_divorces | 1477 | 110 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | kanton | bevnat_marriages | 1482 | 305 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | schweiz | bevnat_births | 57 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_bevnat_sdmx | schweiz | bevnat_divorces | 57 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_bevnat_sdmx | schweiz | bevnat_marriages | 57 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_census_1970_2000 | kanton | vz_hh_collective | 104 | 95 | 7 | 2 | 0 | 0 | 0.081% |
| bfs_census_1970_2000 | kanton | vz_hh_couple_children | 104 | 92 | 4 | 8 | 0 | 0 | 0.028% |
| bfs_census_1970_2000 | kanton | vz_hh_couple_no_children | 104 | 92 | 4 | 8 | 0 | 0 | 0.021% |
| bfs_census_1970_2000 | kanton | vz_hh_non_family | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_hh_one_person | 104 | 93 | 5 | 6 | 0 | 0 | 0.030% |
| bfs_census_1970_2000 | kanton | vz_hh_private | 104 | 92 | 4 | 8 | 0 | 0 | 0.024% |
| bfs_census_1970_2000 | kanton | vz_hh_single_parent | 104 | 94 | 6 | 4 | 0 | 0 | 0.069% |
| bfs_census_1970_2000 | kanton | vz_hh_size_2 | 104 | 93 | 5 | 6 | 0 | 0 | 0.014% |
| bfs_census_1970_2000 | kanton | vz_hh_size_3 | 104 | 93 | 5 | 6 | 0 | 0 | 0.028% |
| bfs_census_1970_2000 | kanton | vz_hh_size_4 | 104 | 92 | 4 | 8 | 0 | 0 | 0.023% |
| bfs_census_1970_2000 | kanton | vz_hh_size_5plus | 104 | 92 | 4 | 8 | 0 | 0 | 0.093% |
| bfs_census_1970_2000 | kanton | vz_hh_total | 104 | 92 | 4 | 8 | 0 | 0 | 0.024% |
| bfs_census_1970_2000 | kanton | vz_hh_with_parents | 104 | 95 | 7 | 2 | 0 | 0 | 0.258% |
| bfs_census_1970_2000 | kanton | vz_lang_de | 104 | 92 | 4 | 8 | 0 | 0 | 0.084% |
| bfs_census_1970_2000 | kanton | vz_lang_en | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_lang_fr | 104 | 93 | 5 | 6 | 0 | 0 | 0.007% |
| bfs_census_1970_2000 | kanton | vz_lang_it | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_lang_other | 104 | 95 | 7 | 2 | 0 | 0 | 0.007% |
| bfs_census_1970_2000 | kanton | vz_lang_rm | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_lang_total | 104 | 92 | 4 | 8 | 0 | 0 | 0.029% |
| bfs_census_1970_2000 | kanton | vz_rel_catholic | 104 | 92 | 4 | 8 | 0 | 0 | 0.003% |
| bfs_census_1970_2000 | kanton | vz_rel_jewish | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_rel_muslim | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_rel_none | 104 | 95 | 7 | 2 | 0 | 0 | 0.007% |
| bfs_census_1970_2000 | kanton | vz_rel_orthodox | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_rel_other | 104 | 96 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | kanton | vz_rel_reformed | 104 | 92 | 4 | 8 | 0 | 0 | 0.164% |
| bfs_census_1970_2000 | kanton | vz_rel_total | 104 | 92 | 4 | 8 | 0 | 0 | 0.029% |
| bfs_census_1970_2000 | schweiz | vz_hh_collective | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_couple_children | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_couple_no_children | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_non_family | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_one_person | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_private | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_single_parent | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_size_2 | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_size_3 | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_size_4 | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_size_5plus | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_total | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_hh_with_parents | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_de | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_en | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_fr | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_it | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_other | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_rm | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_lang_total | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_catholic | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_jewish | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_muslim | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_no_answer | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_none | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_orthodox | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_other | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_other_christian | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_reformed | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_census_1970_2000 | schweiz | vz_rel_total | 4 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_commuting | schweiz | com_employed_residents | 3 | 3 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_construction | kanton | con_exp_private | 806 | 194 | 572 | 40 | 0 | 0 | 0.067% |
| bfs_construction | kanton | con_exp_public | 806 | 0 | 747 | 59 | 0 | 0 | 0.170% |
| bfs_construction | kanton | con_exp_total | 806 | 0 | 741 | 65 | 0 | 0 | 0.100% |
| bfs_construction | kanton | con_inv_new | 806 | 1 | 775 | 30 | 0 | 0 | 0.050% |
| bfs_construction | kanton | con_inv_renovation | 806 | 0 | 770 | 36 | 0 | 0 | 0.279% |
| bfs_construction | kanton | con_inv_residential | 806 | 553 | 231 | 22 | 0 | 0 | 0.039% |
| bfs_construction | kanton | con_inv_total | 806 | 0 | 761 | 45 | 0 | 0 | 0.057% |
| bfs_construction | kanton | con_new_dw_mfh | 780 | 588 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_construction | kanton | con_new_dw_sfh | 780 | 576 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_construction | kanton | con_new_dwellings | 780 | 576 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_construction | kanton | con_new_res_buildings | 780 | 576 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_construction | kanton | con_new_sfh_buildings | 780 | 576 | 26 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_exp_maintenance | 31 | 0 | 23 | 8 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_exp_private | 31 | 0 | 31 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_exp_public | 31 | 0 | 23 | 8 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_exp_total | 31 | 0 | 23 | 8 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_inv_new | 31 | 0 | 31 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_inv_renovation | 31 | 0 | 31 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_inv_residential | 31 | 2 | 29 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_inv_total | 31 | 0 | 31 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_new_dw_mfh | 30 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_new_dw_sfh | 30 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_new_dwellings | 30 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_new_res_buildings | 30 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_construction | schweiz | con_new_sfh_buildings | 30 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_crossborder | bezirk | xb_commuters | 4320 | 4320 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_crossborder | kanton | xb_commuters | 780 | 780 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_crossborder | schweiz | xb_commuters | 30 | 30 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_bld_1919_1945 | 416 | 372 | 20 | 24 | 0 | 0 | 0.063% |
| bfs_gws | kanton | gws_bld_1946_1980 | 416 | 372 | 20 | 24 | 0 | 0 | 0.022% |
| bfs_gws | kanton | gws_bld_1981_2000 | 416 | 372 | 20 | 24 | 0 | 0 | 0.027% |
| bfs_gws | kanton | gws_bld_2001_2010 | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_bld_2011plus | 416 | 386 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_bld_mfh | 416 | 372 | 20 | 24 | 0 | 0 | 0.022% |
| bfs_gws | kanton | gws_bld_partly_res | 416 | 372 | 20 | 24 | 0 | 0 | 0.032% |
| bfs_gws | kanton | gws_bld_pre1919 | 416 | 372 | 20 | 24 | 0 | 0 | 0.040% |
| bfs_gws | kanton | gws_bld_res_mixed | 416 | 372 | 20 | 24 | 0 | 0 | 0.108% |
| bfs_gws | kanton | gws_bld_sfh | 416 | 372 | 20 | 24 | 0 | 0 | 0.013% |
| bfs_gws | kanton | gws_buildings | 416 | 372 | 20 | 24 | 0 | 0 | 0.026% |
| bfs_gws | kanton | gws_dw_2001plus | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_dw_2011plus | 416 | 386 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_dw_area_100_119 | 364 | 326 | 18 | 20 | 0 | 0 | 0.026% |
| bfs_gws | kanton | gws_dw_area_120_159 | 364 | 326 | 18 | 20 | 0 | 0 | 0.008% |
| bfs_gws | kanton | gws_dw_area_160plus | 364 | 326 | 18 | 20 | 0 | 0 | 0.016% |
| bfs_gws | kanton | gws_dw_area_60_79 | 364 | 326 | 18 | 20 | 0 | 0 | 0.019% |
| bfs_gws | kanton | gws_dw_area_80_99 | 364 | 326 | 18 | 20 | 0 | 0 | 0.023% |
| bfs_gws | kanton | gws_dw_area_lt60 | 364 | 326 | 18 | 20 | 0 | 0 | 0.014% |
| bfs_gws | kanton | gws_dw_rooms_1_2 | 416 | 372 | 20 | 24 | 0 | 0 | 0.009% |
| bfs_gws | kanton | gws_dw_rooms_3 | 416 | 372 | 20 | 24 | 0 | 0 | 0.018% |
| bfs_gws | kanton | gws_dw_rooms_4 | 416 | 372 | 20 | 24 | 0 | 0 | 0.019% |
| bfs_gws | kanton | gws_dw_rooms_5plus | 416 | 372 | 20 | 24 | 0 | 0 | 0.024% |
| bfs_gws | kanton | gws_dwellings | 416 | 372 | 20 | 24 | 0 | 0 | 0.017% |
| bfs_gws | kanton | gws_heat_district | 130 | 119 | 9 | 2 | 0 | 0 | 0.137% |
| bfs_gws | kanton | gws_heat_electric | 130 | 120 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_heat_gas | 130 | 120 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_heat_heatpump | 130 | 120 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_heat_none | 130 | 130 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_heat_oil | 130 | 120 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_heat_other | 130 | 120 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_gws | kanton | gws_heat_wood | 130 | 119 | 9 | 2 | 0 | 0 | 0.231% |
| bfs_gws | schweiz | gws_bld_1919_1945 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_1946_1980 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_1981_2000 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_2001_2010 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_2011plus | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_mfh | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_partly_res | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_pre1919 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_res_mixed | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_bld_sfh | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_buildings | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_2001plus | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_2011plus | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_area_100_119 | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_area_120_159 | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_area_160plus | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_area_60_79 | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_area_80_99 | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_area_lt60 | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_rooms_1_2 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_rooms_3 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_rooms_4 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dw_rooms_5plus | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_dwellings | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_district | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_electric | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_gas | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_heatpump | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_none | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_oil | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_other | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_gws | schweiz | gws_heat_wood | 5 | 5 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_persons | 2002 | 1988 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size1 | 2002 | 1970 | 6 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size2 | 2002 | 1981 | 6 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size3 | 2002 | 1867 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size4 | 2002 | 1803 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size5 | 2002 | 1533 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size6plus | 2002 | 886 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_total | 2002 | 1988 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_persons | 364 | 336 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size1 | 364 | 318 | 20 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size2 | 364 | 329 | 20 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size3 | 364 | 260 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size4 | 364 | 260 | 6 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size5 | 364 | 199 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size6plus | 364 | 123 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_total | 364 | 336 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_persons | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_size1 | 14 | 2 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_size2 | 14 | 4 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_size3 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_size4 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_size5 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_size6plus | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_total | 14 | 14 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_emigration_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_emigration_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_immigration_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_immigration_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intercant_in_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intercant_in_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intercant_out_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intercant_out_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intracant_in_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intracant_in_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intracant_out_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_intracant_out_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_net_intercant_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_net_intercant_swiss | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_net_intl_foreign | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | bezirk | mig_net_intl_swiss | 2145 | 2131 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_emigration_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_emigration_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_immigration_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_immigration_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intercant_in_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intercant_in_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intercant_out_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intercant_out_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intracant_in_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intracant_in_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intracant_out_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_intracant_out_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_net_intercant_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_net_intercant_swiss | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_net_intl_foreign | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_migration | kanton | mig_net_intl_swiss | 390 | 362 | 28 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_emigration_foreign | 15 | 0 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_emigration_swiss | 15 | 14 | 1 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_immigration_foreign | 15 | 0 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_immigration_swiss | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intercant_in_foreign | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intercant_in_swiss | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intercant_out_foreign | 15 | 9 | 6 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intercant_out_swiss | 15 | 9 | 6 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intracant_in_foreign | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intracant_in_swiss | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intracant_out_foreign | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_intracant_out_swiss | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_net_intercant_foreign | 15 | 9 | 6 | 0 | 0 | 0 | nan% |
| bfs_migration | schweiz | mig_net_intercant_swiss | 15 | 9 | 6 | 0 | 0 | 0 | nan% |
| bfs_migration | schweiz | mig_net_intl_foreign | 15 | 0 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_migration | schweiz | mig_net_intl_swiss | 15 | 14 | 1 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | bezirk | nat_eu_efta | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | bezirk | nat_other_europe | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | bezirk | nat_outside_europe | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | bezirk | nat_total | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | bezirk | nat_women | 2145 | 2130 | 15 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | kanton | nat_eu_efta | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | kanton | nat_other_europe | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | kanton | nat_outside_europe | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | kanton | nat_total | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | kanton | nat_women | 390 | 360 | 30 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | schweiz | nat_eu_efta | 15 | 14 | 0 | 1 | 0 | 0 | 0.022% |
| bfs_naturalisation | schweiz | nat_other_europe | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | schweiz | nat_outside_europe | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_naturalisation | schweiz | nat_total | 15 | 14 | 0 | 1 | 0 | 0 | 0.012% |
| bfs_naturalisation | schweiz | nat_women | 15 | 15 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_ballots_blank | 1993 | 1979 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_ballots_changed | 1770 | 1757 | 13 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_ballots_invalid | 1993 | 1980 | 13 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_ballots_unchanged | 1851 | 1838 | 13 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_ballots_valid | 1993 | 1979 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_eligible | 1993 | 1979 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | bezirk | nrw_voters | 1993 | 1979 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | kanton | nrw_ballots_blank | 357 | 264 | 93 | 0 | 0 | 0 | 0.020% |
| bfs_nrw | kanton | nrw_ballots_changed | 264 | 176 | 73 | 16 | 0 | 0 | 0.463% |
| bfs_nrw | kanton | nrw_ballots_unchanged | 333 | 232 | 86 | 16 | 0 | 0 | 0.167% |
| bfs_nrw | kanton | nrw_ballots_valid | 357 | 245 | 97 | 16 | 0 | 0 | 0.147% |
| bfs_nrw | kanton | nrw_eligible | 357 | 267 | 75 | 16 | 0 | 0 | 0.115% |
| bfs_nrw | kanton | nrw_fw_bdp | 44 | 16 | 24 | 5 | 0 | 0 | 0.227% |
| bfs_nrw | kanton | nrw_fw_edu | 95 | 51 | 43 | 1 | 0 | 0 | 0.301% |
| bfs_nrw | kanton | nrw_fw_evp | 131 | 72 | 56 | 3 | 0 | 0 | 0.193% |
| bfs_nrw | kanton | nrw_fw_fga | 46 | 33 | 10 | 3 | 0 | 0 | 0.059% |
| bfs_nrw | kanton | nrw_fw_fps | 48 | 38 | 9 | 1 | 0 | 0 | 0.109% |
| bfs_nrw | kanton | nrw_fw_glp | 72 | 29 | 34 | 10 | 0 | 0 | 0.051% |
| bfs_nrw | kanton | nrw_fw_gruene | 179 | 114 | 60 | 5 | 0 | 0 | 0.060% |
| bfs_nrw | kanton | nrw_fw_ldu | 68 | 52 | 15 | 1 | 0 | 0 | 0.045% |
| bfs_nrw | kanton | nrw_fw_lega | 9 | 9 | 0 | 0 | 0 | 0 | 0.006% |
| bfs_nrw | kanton | nrw_fw_lps | 53 | 37 | 15 | 1 | 0 | 0 | 0.064% |
| bfs_nrw | kanton | nrw_fw_mcr | 6 | 0 | 6 | 0 | 0 | 0 | 0.011% |
| bfs_nrw | kanton | nrw_fw_mitte | 25 | 11 | 14 | 0 | 0 | 0 | 0.022% |
| bfs_nrw | kanton | nrw_fw_pda | 83 | 51 | 32 | 0 | 0 | 0 | 0.137% |
| bfs_nrw | kanton | nrw_fw_poch | 30 | 22 | 8 | 0 | 0 | 0 | 0.151% |
| bfs_nrw | kanton | nrw_fw_psa | 6 | 2 | 4 | 0 | 0 | 0 | 0.004% |
| bfs_nrw | kanton | nrw_fw_rep | 24 | 18 | 6 | 0 | 0 | 0 | 0.064% |
| bfs_nrw | kanton | nrw_fw_sd | 124 | 80 | 43 | 1 | 0 | 0 | 0.311% |
| bfs_nrw | kanton | nrw_fw_sol | 21 | 7 | 14 | 0 | 0 | 0 | 0.044% |
| bfs_nrw | kanton | nrw_voters | 357 | 245 | 97 | 16 | 0 | 0 | 0.143% |
| bfs_nrw | schweiz | nrw_ballots_blank | 14 | 1 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_ballots_changed | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_ballots_invalid | 14 | 0 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_ballots_unchanged | 13 | 0 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_ballots_valid | 14 | 0 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_eligible | 14 | 2 | 7 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_fw_bdp | 3 | 0 | 1 | 2 | 0 | 0 | 0.001% |
| bfs_nrw | schweiz | nrw_fw_csp | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_cvp | 13 | 0 | 4 | 4 | 0 | 0 | 0.046% |
| bfs_nrw | schweiz | nrw_fw_edu | 13 | 0 | 5 | 0 | 0 | 0 | 0.001% |
| bfs_nrw | schweiz | nrw_fw_evp | 14 | 0 | 3 | 2 | 0 | 0 | 0.001% |
| bfs_nrw | schweiz | nrw_fw_fga | 12 | 0 | 1 | 0 | 0 | 0 | 0.004% |
| bfs_nrw | schweiz | nrw_fw_fps | 6 | 1 | 0 | 0 | 0 | 0 | 0.011% |
| bfs_nrw | schweiz | nrw_fw_glp | 5 | 0 | 1 | 3 | 0 | 0 | 0.001% |
| bfs_nrw | schweiz | nrw_fw_gruene | 13 | 0 | 5 | 0 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_fw_ldu | 8 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_lega | 9 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_lps | 10 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_mcr | 5 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_mitte | 1 | 0 | 0 | 1 | 0 | 0 | 0.000% |
| bfs_nrw | schweiz | nrw_fw_other | 14 | 0 | 5 | 0 | 0 | 0 | 0.001% |
| bfs_nrw | schweiz | nrw_fw_pda | 14 | 0 | 2 | 1 | 0 | 0 | 0.006% |
| bfs_nrw | schweiz | nrw_fw_poch | 6 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_psa | 6 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_rep | 5 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_sd | 14 | 0 | 5 | 0 | 0 | 0 | 0.008% |
| bfs_nrw | schweiz | nrw_fw_sep | 7 | 1 | 0 | 0 | 0 | 0 | 0.005% |
| bfs_nrw | schweiz | nrw_fw_sol | 8 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_sp | 14 | 0 | 3 | 6 | 0 | 0 | 0.080% |
| bfs_nrw | schweiz | nrw_fw_svp | 14 | 0 | 3 | 4 | 0 | 0 | 0.023% |
| bfs_nrw | schweiz | nrw_fw_total | 14 | 0 | 1 | 8 | 0 | 0 | 0.045% |
| bfs_nrw | schweiz | nrw_voters | 14 | 0 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_de | 1741 | 1741 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_en | 1741 | 1741 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_fr | 1735 | 1735 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_it | 1725 | 1725 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_other | 1741 | 1741 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_pop | 1741 | 1741 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_rm | 1254 | 1254 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | bezirk | lang_se_unknown | 1564 | 1564 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_de | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_en | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_fr | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_it | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_other | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_pop | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_rm | 12 | 12 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_se_language_bezirk | schweiz | lang_se_unknown | 11 | 11 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_social_assistance | kanton | sh_recipients | 494 | 11 | 0 | 23 | 131 ¹ | 0 | 14.860% |
| bfs_statent | schweiz | ent_fte | 14 | 0 | 0 | 10 | 0 | 0 | 0.001% |
| bfs_statent | schweiz | ent_fte_s1 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_fte_s2 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_fte_s3 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_jobs | 14 | 10 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statent | schweiz | ent_jobs_s1 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_jobs_s2 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_jobs_s3 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_jobs_women | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_workplaces | 14 | 2 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statent | schweiz | ent_workplaces_s1 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_workplaces_s2 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statent | schweiz | ent_workplaces_s3 | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_statpop | bezirk | pop_age_0_19 | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_20_64 | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_65_79 | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_80plus | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_divorced | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_female | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_foreign | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_male | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_married | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_nonpermanent | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_single | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_swiss | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_total | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_widowed | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_0_19 | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_20_64 | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_65_79 | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_80plus | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_divorced | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_female | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_foreign | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_male | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_married | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_nonpermanent | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_single | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_swiss | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_total | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_widowed | 416 | 384 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_0_19 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_20_64 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_65_79 | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_80plus | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_divorced | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_female | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_foreign | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_male | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_married | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_nonpermanent | 16 | 12 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_single | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_swiss | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_total | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_widowed | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_dwellings | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_for_rent | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_for_sale | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_new | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_rooms_1_2 | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_rooms_3 | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_rooms_4 | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_rooms_5plus | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | bezirk | vac_sfh | 4608 | 4608 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | kanton | vac_dwelling_stock | 416 | 372 | 20 | 24 | 0 | 0 | 0.017% |
| bfs_vacancy | kanton | vac_dwellings | 832 | 830 | 0 | 2 | 0 | 0 | 0.045% |
| bfs_vacancy | kanton | vac_for_rent | 832 | 830 | 0 | 2 | 0 | 0 | 0.051% |
| bfs_vacancy | kanton | vac_for_sale | 832 | 832 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | kanton | vac_new | 832 | 832 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | kanton | vac_rooms_1_2 | 832 | 830 | 0 | 2 | 0 | 0 | 0.175% |
| bfs_vacancy | kanton | vac_rooms_3 | 832 | 832 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | kanton | vac_rooms_4 | 832 | 832 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | kanton | vac_rooms_5plus | 832 | 832 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | kanton | vac_sfh | 832 | 832 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_dwelling_stock | 16 | 16 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_dwellings | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_for_rent | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_for_sale | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_new | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_rooms_1_2 | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_rooms_3 | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_rooms_4 | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_rooms_5plus | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vacancy | schweiz | vac_sfh | 32 | 32 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_bev | 2288 | 2275 | 13 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_diesel | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_hev | 2288 | 2271 | 16 | 1 | 0 | 0 | 0.175% |
| bfs_vehicles | bezirk | mfz_cars_petrol | 2288 | 2272 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_phev | 2288 | 2278 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_private | 1430 | 1420 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_newreg_bev | 2288 | 2277 | 9 | 2 | 0 | 0 | 0.389% |
| bfs_vehicles | bezirk | mfz_newreg_cars | 2288 | 2271 | 16 | 1 | 0 | 0 | 0.091% |
| bfs_vehicles | kanton | mfz_cars | 416 | 192 | 224 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | kanton | mfz_cars_bev | 416 | 243 | 173 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | kanton | mfz_cars_diesel | 416 | 192 | 224 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | kanton | mfz_cars_hev | 416 | 215 | 200 | 1 | 0 | 0 | 0.005% |
| bfs_vehicles | kanton | mfz_cars_petrol | 416 | 192 | 224 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | kanton | mfz_cars_phev | 416 | 259 | 157 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | kanton | mfz_cars_private | 260 | 48 | 212 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | kanton | mfz_newreg_cars | 416 | 216 | 199 | 1 | 0 | 0 | 0.010% |
| bfs_vehicles | schweiz | mfz_cars | 16 | 0 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_bev | 16 | 8 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_diesel | 16 | 7 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_hev | 16 | 8 | 7 | 1 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_petrol | 16 | 0 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_phev | 16 | 8 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_private | 10 | 0 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_newreg_bev | 16 | 8 | 7 | 1 | 0 | 0 | 0.197% |
| bfs_vehicles | schweiz | mfz_newreg_cars | 16 | 8 | 7 | 1 | 0 | 0 | 0.001% |
| bfs_votes_gemeinde | bezirk | vote_ballots | 69974 | 67643 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_votes_gemeinde | bezirk | vote_eligible | 69993 | 67662 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_votes_gemeinde | bezirk | vote_no | 70528 | 67883 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_votes_gemeinde | bezirk | vote_valid | 70528 | 67883 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_votes_gemeinde | bezirk | vote_yes | 70528 | 67883 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_votes_gemeinde | kanton | vote_ballots | 13180 | 8372 | 3419 | 233 | 0 | 0 | 0.319% |
| bfs_votes_gemeinde | kanton | vote_yes | 13180 | 8456 | 3355 | 219 | 0 | 0 | 0.299% |
| bfs_votes_gemeinde | schweiz | vote_ballots | 511 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_votes_gemeinde | schweiz | vote_eligible | 511 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_votes_gemeinde | schweiz | vote_no | 511 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_votes_gemeinde | schweiz | vote_valid | 511 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_votes_gemeinde | schweiz | vote_yes | 511 | 0 | 0 | 0 | 0 | 0 | nan% |
| estv_dbst | schweiz | tax_np_federal_tax_chf | 20 | 9 | 0 | 6 | 0 | 0 | 0.219% |
| estv_dbst | schweiz | tax_np_net_income_chf | 16 | 1 | 0 | 3 | 0 | 0 | 0.063% |
| estv_dbst | schweiz | tax_np_normal_taxable_100k_plus | 4 | 0 | 0 | 0 | 0 | 0 | nan% |
| estv_dbst | schweiz | tax_np_taxable_income_chf | 16 | 1 | 0 | 3 | 0 | 0 | 0.070% |
| estv_dbst | schweiz | tax_np_taxpayers | 20 | 0 | 0 | 4 | 0 | 0 | 0.008% |
| estv_dbst | schweiz | tax_np_taxpayers_no_federal_tax | 20 | 0 | 0 | 2 | 0 | 0 | 0.013% |
| estv_dbst | schweiz | tax_np_taxpayers_normal | 4 | 3 | 0 | 0 | 0 | 0 | 0.000% |
| geo_identity | kanton | geo_area_land_ha | 26 | 24 | 0 | 2 | 0 | 0 | 0.161% |
| geo_identity | schweiz | geo_area_land_ha | 1 | 0 | 0 | 1 | 0 | 0 | 0.014% |
| kt_crime | kanton | crime_stgb_offences | 38 | 8 | 23 | 0 | 0 | 0 | 0.000% |
| kt_crime | kanton | crime_stgb_property | 17 | 0 | 17 | 0 | 0 | 0 | 0.000% |
| kt_crime | kanton | crime_stgb_violent | 17 | 0 | 17 | 0 | 0 | 0 | 0.000% |
| kt_finance | kanton | fin_tax_revenue_chf | 51 | 11 | 0 | 27 | 0 ¹ | 0 | 0.026% |
| kt_pupils | kanton | pup_compulsory | 23 | 22 | 0 | 0 | 0 | 0 | 0.000% |
| kt_unemployment | kanton | unemp_registered | 87 | 14 | 3 | 57 | 0 | 0 | 0.137% |

¹ Documented differences (from metrics.yaml `additivity_note`):

- agr_area_arable_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_grassland_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_organic_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_permanent_crops_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- sh_recipients: BFS (Map Explorer, indicator description): "Wer im Verlaufe eines Jahres den Wohnort wechselt und sowohl am alten als auch am neuen Ort Sozialhilfe bezieht, wird zweimal ... gezählt. Bei kantonalen Auswertungen wird dieselbe Unterstützungseinheit nur einmal gezählt ... Demzufolge stimmen die Summen ... aller Gemeinden nicht mit dem Kantonstotal überein." Observed for all canton-years with a counted (integer) canton total: municipal sum between +0.0 % and +6.04 % (NW 2012), never below. Non-integer canton totals (GL 2007, AR 2014/15, 2024–2025) are BFS estimates (precision modelled) and are not expected to add up.
- fin_tax_revenue_chf: TI canton total (SEL annex TOTALE row) includes communes listed with an earlier accounting year (e.g. 'Rovio (2012)') and, in 2022, the merged commune Val Mara, which are skipped at municipality level: commune sums are 0–1.1% below the total (max 2010: −1.06%); 2015–2021 and 2023–2024 match exactly.

Worst unexplained differences:

- bfs_arealstatistik / bezirk / area_agriculture_ha: [{'unit_id': '2101', 'period': '2013/18', 'value_pub': 2772.0, 'value_agg': 2754.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1979/85', 'value_pub': 3713.0, 'value_agg': 3690.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1992/97', 'value_pub': 3097.0, 'value_agg': 3078.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_total_ha: [{'unit_id': '1005', 'period': '1979/85', 'value_pub': 14573.0, 'value_agg': 14314.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '2013/18', 'value_pub': 14573.0, 'value_agg': 14314.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '2004/09', 'value_pub': 14573.0, 'value_agg': 14314.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_unproductive_ha: [{'unit_id': '2101', 'period': '2004/09', 'value_pub': 1990.0, 'value_agg': 1935.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1992/97', 'value_pub': 2171.0, 'value_agg': 2112.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1979/85', 'value_pub': 2358.0, 'value_agg': 2299.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_water_ha: [{'unit_id': '2101', 'period': '2013/18', 'value_pub': 339.0, 'value_agg': 337.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '2004/09', 'value_pub': 343.0, 'value_agg': 341.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1992/97', 'value_pub': 350.0, 'value_agg': 348.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_wooded_ha: [{'unit_id': '1005', 'period': '1979/85', 'value_pub': 2997.0, 'value_agg': 2738.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '1992/97', 'value_pub': 3021.0, 'value_agg': 2763.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '2020/25', 'value_pub': 3051.0, 'value_agg': 2793.0, 'explained': 0.0}]
- bfs_census_1970_2000 / kanton / vz_rel_no_answer: [{'unit_id': 'FR', 'period': '1990', 'value_pub': 537.0, 'value_agg': 540.0, 'explained': 0.0}]
- bfs_census_1970_2000 / kanton / vz_rel_other_christian: [{'unit_id': 'FR', 'period': '1980', 'value_pub': 744.0, 'value_agg': 757.0, 'explained': 0.0}, {'unit_id': 'FR', 'period': '1970', 'value_pub': 358.0, 'value_agg': 364.0, 'explained': 0.0}]
- bfs_construction / kanton / con_exp_maintenance: [{'unit_id': 'JU', 'period': '1994', 'value_pub': 12945.0, 'value_agg': 12286.0, 'explained': -1039.0}, {'unit_id': 'JU', 'period': '1995', 'value_pub': 10573.0, 'value_agg': 9085.0, 'explained': -1688.0}]
- bfs_nrw / kanton / nrw_ballots_invalid: [{'unit_id': 'JU', 'period': '1987', 'value_pub': 68.0, 'value_agg': 72.0, 'explained': 2.0}, {'unit_id': 'JU', 'period': '1991', 'value_pub': 120.0, 'value_agg': 132.0, 'explained': 11.0}, {'unit_id': 'BE', 'period': '1987', 'value_pub': 394.0, 'value_agg': 387.0, 'explained': -5.0}]
- bfs_nrw / kanton / nrw_fw_csp: [{'unit_id': 'JU', 'period': '1983', 'value_pub': 3028.0, 'value_agg': 2939.7000175018966, 'explained': 0.0}, {'unit_id': 'JU', 'period': '1987', 'value_pub': 1793.0, 'value_agg': 1747.041578544751, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_cvp: [{'unit_id': 'JU', 'period': '1987', 'value_pub': 7351.0, 'value_agg': 7182.634275377565, 'explained': 4.245668978789234}, {'unit_id': 'JU', 'period': '1991', 'value_pub': 7118.0, 'value_agg': 6972.472559877706, 'explained': 8.45936726556872}, {'unit_id': 'JU', 'period': '1983', 'value_pub': 6450.0, 'value_agg': 6317.482561394099, 'explained': 4.905698900663455}]
- bfs_nrw / kanton / nrw_fw_fdp: [{'unit_id': 'JU', 'period': '1983', 'value_pub': 7402.0, 'value_agg': 7777.886471255869, 'explained': 699.496995729353}, {'unit_id': 'JU', 'period': '1979', 'value_pub': 7350.0, 'value_agg': 7856.40161152956, 'explained': 814.7204216193905}, {'unit_id': 'JU', 'period': '1987', 'value_pub': 7439.0, 'value_agg': 7778.200086395098, 'explained': 576.7845709381374}]
- bfs_nrw / kanton / nrw_fw_other: [{'unit_id': 'JU', 'period': '1979', 'value_pub': 7467.0, 'value_agg': 7137.5399986146585, 'explained': 9.295116111977606}, {'unit_id': 'JU', 'period': '1983', 'value_pub': 3739.0, 'value_agg': 3693.379016908547, 'explained': 19.37925026715989}]
- bfs_nrw / kanton / nrw_fw_sep: [{'unit_id': 'BE', 'period': '1987', 'value_pub': 2845.0, 'value_agg': 1982.762213659972, 'explained': -843.3221013360616}, {'unit_id': 'BE', 'period': '1995', 'value_pub': 3948.0, 'value_agg': 2813.6738109990624, 'explained': -1113.659691801661}]
- bfs_nrw / kanton / nrw_fw_sp: [{'unit_id': 'JU', 'period': '1995', 'value_pub': 6394.0, 'value_agg': 6316.414646877877, 'explained': 252.97112756021517}, {'unit_id': 'JU', 'period': '1983', 'value_pub': 4583.0, 'value_agg': 4939.473783005553, 'explained': 549.6818222098009}, {'unit_id': 'JU', 'period': '1987', 'value_pub': 5666.0, 'value_agg': 5880.215381634846, 'explained': 445.8648439036694}]
- bfs_nrw / kanton / nrw_fw_svp: [{'unit_id': 'JU', 'period': '1983', 'value_pub': 520.0, 'value_agg': 795.9472029858425, 'explained': 323.25424458201536}]
- bfs_nrw / kanton / nrw_fw_total: [{'unit_id': 'JU', 'period': '1979', 'value_pub': 23784.0, 'value_agg': 27057.97368113954, 'explained': 4103.58409916491}, {'unit_id': 'JU', 'period': '1995', 'value_pub': 19762.0, 'value_agg': 21206.27255990177, 'explained': 2105.9489065535427}, {'unit_id': 'JU', 'period': '1983', 'value_pub': 25722.0, 'value_agg': 28304.02802366238, 'explained': 3436.876982299561}]
- bfs_nrw / schweiz / nrw_fw_fdp: [{'unit_id': 'CH', 'period': '2011', 'value_pub': 368951.0, 'value_agg': 352850.84724351397, 'explained': -2662.5573756435297}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 366313.0, 'value_agg': 354529.2895707672, 'explained': -3549.481782607711}, {'unit_id': 'CH', 'period': '2023', 'value_pub': 364053.0, 'value_agg': 354399.6297727488, 'explained': -3842.117491501883}]
- bfs_vehicles / kanton / mfz_newreg_bev: [{'unit_id': 'SG', 'period': '2025', 'value_pub': 3124.0, 'value_agg': 3124.0, 'explained': -102.0}]
- bfs_votes_gemeinde / kanton / vote_eligible: [{'unit_id': 'BS', 'period': '2003-05-18#4980', 'value_pub': 116680.0, 'value_agg': 112362.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2003-05-18#4990', 'value_pub': 116680.0, 'value_agg': 112362.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2003-05-18#5000', 'value_pub': 116680.0, 'value_agg': 112362.0, 'explained': 0.0}]
- bfs_votes_gemeinde / kanton / vote_no: [{'unit_id': 'JU', 'period': '1995-03-12#4210', 'value_pub': 2622.0, 'value_agg': 3024.0, 'explained': 382.0}, {'unit_id': 'JU', 'period': '1995-03-12#4190', 'value_pub': 5989.0, 'value_agg': 6983.0, 'explained': 961.0}, {'unit_id': 'JU', 'period': '1996-03-10#4280', 'value_pub': 3838.0, 'value_agg': 4277.0, 'explained': 419.0}]
- bfs_votes_gemeinde / kanton / vote_valid: [{'unit_id': 'SO', 'period': '1972-03-05#2272', 'value_pub': 40437.0, 'value_agg': 37574.0, 'explained': -1.0}, {'unit_id': 'AI', 'period': '1972-12-03#2321', 'value_pub': 3241.0, 'value_agg': 3042.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1972-12-03#2322', 'value_pub': 3235.0, 'value_agg': 3106.0, 'explained': 0.0}]

## B. Ranges

- **ent_share_jobs_accommodation_food**: 1.0 values outside 0–100 — e.g. gemeinde 6109 2018: 114.286

## C. Year-on-year jumps (> 50% and > 200 units)

Metrics marked `volatile` (lumpy series such as construction investment) are excluded.

| Metric | Flags | Series | Largest |
|---|---|---|---|
| gk_pop_d | 798 | 464 | [{'unit_id': '6248', 'year': 2020, 'prev': 1962.0, 'value': 9830.0, 'precision': 'modelled'}, {'unit_id': '2125', 'year': 2018, 'prev': 9375.0, 'value': 4261.0, 'precision': 'modelled'}] |
| gk_pop_c | 768 | 412 | [{'unit_id': '4671', 'year': 2024, 'prev': 5816.0, 'value': 12270.0, 'precision': 'modelled'}, {'unit_id': '5642', 'year': 2023, 'prev': 7708.0, 'value': 2643.0, 'precision': 'modelled'}] |
| gk_pop_none | 717 | 434 | [{'unit_id': '5938', 'year': 2013, 'prev': 7837.0, 'value': 241.0, 'precision': 'modelled'}, {'unit_id': '6248', 'year': 2013, 'prev': 7373.0, 'value': 1563.0, 'precision': 'modelled'}] |
| gk_pop_b | 412 | 230 | [{'unit_id': '6621', 'year': 2014, 'prev': 59025.0, 'value': 16399.0, 'precision': 'modelled'}, {'unit_id': '6621', 'year': 2013, 'prev': 25766.0, 'value': 59025.0, 'precision': 'modelled'}] |
| gk_pop_a | 204 | 104 | [{'unit_id': '5192', 'year': 2021, 'prev': 5004.0, 'value': 16650.0, 'precision': 'modelled'}, {'unit_id': '1054', 'year': 2020, 'prev': 2329.0, 'value': 9670.0, 'precision': 'modelled'}] |
| gws_dw_2011plus | 91 | 82 | [{'unit_id': '261', 'year': 2011, 'prev': 0.0, 'value': 2348.0, 'precision': 'exact'}, {'unit_id': '230', 'year': 2011, 'prev': 0.0, 'value': 1066.0, 'precision': 'exact'}] |
| pop_nonpermanent | 76 | 52 | [{'unit_id': '261', 'year': 2022, 'prev': 3560.0, 'value': 7598.0, 'precision': 'exact'}, {'unit_id': '2701', 'year': 2022, 'prev': 2332.0, 'value': 4718.0, 'precision': 'exact'}] |
| bil_intracant_in | 67 | 49 | [{'unit_id': '5583', 'year': 2024, 'prev': 617.0, 'value': 1734.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2021, 'prev': 494.0, 'value': 1585.0, 'precision': 'exact'}] |
| vac_dwellings | 65 | 43 | [{'unit_id': '6621', 'year': 2001, 'prev': 1004.0, 'value': 452.0, 'precision': 'exact'}, {'unit_id': '361', 'year': 2009, 'prev': 570.0, 'value': 35.0, 'precision': 'exact'}] |
| vac_for_rent | 61 | 39 | [{'unit_id': '6621', 'year': 2001, 'prev': 950.0, 'value': 410.0, 'precision': 'exact'}, {'unit_id': '361', 'year': 2009, 'prev': 570.0, 'value': 35.0, 'precision': 'exact'}] |
| bil_immigration | 37 | 22 | [{'unit_id': '6253', 'year': 2012, 'prev': 300.0, 'value': 1078.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2011, 'prev': 969.0, 'value': 300.0, 'precision': 'exact'}] |
| agr_cattle | 34 | 15 | [{'unit_id': '4506', 'year': 1998, 'prev': 2365.0, 'value': 780.0, 'precision': 'exact'}, {'unit_id': '4511', 'year': 1997, 'prev': 1574.0, 'value': 0.0, 'precision': 'exact'}] |
| bil_intracant_out | 32 | 23 | [{'unit_id': '360', 'year': 1991, 'prev': 1074.0, 'value': 319.0, 'precision': 'exact'}, {'unit_id': '3955', 'year': 1992, 'prev': 955.0, 'value': 264.0, 'precision': 'exact'}] |
| tax_np_taxpayers_no_federal_tax | 27 | 27 | [{'unit_id': '5192', 'year': 2005, 'prev': 2345.0, 'value': 6836.0, 'precision': 'exact'}, {'unit_id': '5002', 'year': 2005, 'prev': 1311.0, 'value': 4173.0, 'precision': 'exact'}] |
| udemo_jobs_active | 25 | 22 | [{'unit_id': '4034', 'year': 2023, 'prev': 4608.0, 'value': 1849.0, 'precision': 'exact'}, {'unit_id': '197', 'year': 2023, 'prev': 1877.0, 'value': 3759.0, 'precision': 'exact'}] |
| bil_emigration | 23 | 13 | [{'unit_id': '5586', 'year': 2010, 'prev': 1847.0, 'value': 4526.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2012, 'prev': 246.0, 'value': 839.0, 'precision': 'exact'}] |
| mig_immigration_foreign | 22 | 17 | [{'unit_id': '6253', 'year': 2012, 'prev': 251.0, 'value': 1043.0, 'precision': 'exact'}, {'unit_id': '56', 'year': 2017, 'prev': 791.0, 'value': 210.0, 'precision': 'exact'}] |
| bil_naturalisations | 21 | 12 | [{'unit_id': '6621', 'year': 2015, 'prev': 847.0, 'value': 2295.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2020, 'prev': 2250.0, 'value': 1071.0, 'precision': 'exact'}] |
| mig_intracant_in_swiss | 19 | 14 | [{'unit_id': '6633', 'year': 2021, 'prev': 303.0, 'value': 1040.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2022, 'prev': 1040.0, 'value': 424.0, 'precision': 'exact'}] |
| gws_bld_pre1919 | 19 | 12 | [{'unit_id': '230', 'year': 2011, 'prev': 3525.0, 'value': 22.0, 'precision': 'exact'}, {'unit_id': '230', 'year': 2012, 'prev': 22.0, 'value': 3420.0, 'precision': 'exact'}] |
| gws_bld_1919_1945 | 18 | 11 | [{'unit_id': '3203', 'year': 2011, 'prev': 497.0, 'value': 1706.0, 'precision': 'exact'}, {'unit_id': '3443', 'year': 2011, 'prev': 55.0, 'value': 848.0, 'precision': 'exact'}] |
| ent_jobs_s2 | 17 | 15 | [{'unit_id': '1707', 'year': 2023, 'prev': 1422.0, 'value': 4523.0, 'precision': 'exact'}, {'unit_id': '1707', 'year': 2022, 'prev': 4369.0, 'value': 1422.0, 'precision': 'exact'}] |
| ent_fte_s2 | 17 | 15 | [{'unit_id': '1707', 'year': 2023, 'prev': 1279.0, 'value': 4261.0, 'precision': 'exact'}, {'unit_id': '1707', 'year': 2022, 'prev': 4131.0, 'value': 1279.0, 'precision': 'exact'}] |
| unemp_registered | 13 | 9 | [{'unit_id': '261', 'year': 1992, 'prev': 2515.1, 'value': 6653.3, 'precision': 'exact'}, {'unit_id': '6621', 'year': 1991, 'prev': 1345.6666666666667, 'value': 2953.75, 'precision': 'exact'}] |
| gws_heat_district | 13 | 12 | [{'unit_id': '355', 'year': 2022, 'prev': 132.0, 'value': 1378.0, 'precision': 'exact'}, {'unit_id': '355', 'year': 2023, 'prev': 1378.0, 'value': 205.0, 'precision': 'exact'}] |
| ent_jobs_ict | 13 | 10 | [{'unit_id': '362', 'year': 2014, 'prev': 198.0, 'value': 1262.0, 'precision': 'exact'}, {'unit_id': '62', 'year': 2021, 'prev': 786.3348671236736, 'value': 1818.4618274016339, 'precision': 'boundary_estimate'}] |
| bil_intercant_in | 12 | 10 | [{'unit_id': '6621', 'year': 1982, 'prev': 4258.0, 'value': 2002.0, 'precision': 'exact'}, {'unit_id': '27', 'year': 1991, 'prev': 594.0, 'value': 119.0, 'precision': 'exact'}] |
| bil_intercant_out | 12 | 11 | [{'unit_id': '1701', 'year': 1990, 'prev': 801.0, 'value': 355.0, 'precision': 'exact'}, {'unit_id': '27', 'year': 1991, 'prev': 530.0, 'value': 96.0, 'precision': 'exact'}] |
| nat_total | 10 | 7 | [{'unit_id': '6621', 'year': 2015, 'prev': 847.0, 'value': 2295.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2020, 'prev': 2250.0, 'value': 1071.0, 'precision': 'exact'}] |
| ent_jobs_finance | 8 | 8 | [{'unit_id': '131', 'year': 2016, 'prev': 3348.0, 'value': 1606.0, 'precision': 'exact'}, {'unit_id': '69', 'year': 2014, 'prev': 993.0, 'value': 2557.0, 'precision': 'exact'}] |
| gws_bld_partly_res | 8 | 7 | [{'unit_id': '567', 'year': 2013, 'prev': 83.0, 'value': 369.0, 'precision': 'exact'}, {'unit_id': '6082', 'year': 2019, 'prev': 27.0, 'value': 290.0, 'precision': 'exact'}] |
| agr_goats | 7 | 6 | [{'unit_id': '5812', 'year': 2012, 'prev': 695.0, 'value': 0.0, 'precision': 'exact'}, {'unit_id': '1214', 'year': 1997, 'prev': 539.0, 'value': 0.0, 'precision': 'exact'}] |
| vac_rooms_1_2 | 7 | 7 | [{'unit_id': '6621', 'year': 2001, 'prev': 790.0, 'value': 314.0, 'precision': 'exact'}, {'unit_id': '2701', 'year': 1997, 'prev': 394.0, 'value': 812.0, 'precision': 'exact'}] |
| gws_heat_wood | 7 | 7 | [{'unit_id': '5192', 'year': 2024, 'prev': 599.0, 'value': 1264.0, 'precision': 'exact'}, {'unit_id': '5050', 'year': 2024, 'prev': 451.0, 'value': 937.0, 'precision': 'exact'}] |
| ent_jobs_health | 7 | 6 | [{'unit_id': '5412', 'year': 2020, 'prev': 131.0, 'value': 1963.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 218.0, 'value': 1304.0, 'precision': 'exact'}] |
| mfz_cars_hev | 6 | 3 | [{'unit_id': '3101', 'year': 2023, 'prev': 954.0, 'value': 4039.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2021, 'prev': 675.0, 'value': 2255.0, 'precision': 'exact'}] |
| ent_jobs | 6 | 6 | [{'unit_id': '5412', 'year': 2020, 'prev': 868.0, 'value': 2775.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 996.0, 'value': 2041.0, 'precision': 'exact'}] |
| agr_area_organic_ha | 6 | 6 | [{'unit_id': '3396', 'year': 1998, 'prev': 201.0, 'value': 634.0, 'precision': 'exact'}, {'unit_id': '6638', 'year': 1997, 'prev': 504.0, 'value': 74.0, 'precision': 'exact'}] |
| ent_fte | 6 | 5 | [{'unit_id': '5412', 'year': 2020, 'prev': 714.0, 'value': 2233.0, 'precision': 'exact'}, {'unit_id': '4065', 'year': 2023, 'prev': 590.0, 'value': 1260.0, 'precision': 'exact'}] |
| agr_area_ha | 6 | 4 | [{'unit_id': '4511', 'year': 1997, 'prev': 859.0, 'value': 0.0, 'precision': 'exact'}, {'unit_id': '4511', 'year': 1998, 'prev': 0.0, 'value': 830.0, 'precision': 'exact'}] |
| mfz_cars | 6 | 6 | [{'unit_id': '3101', 'year': 2018, 'prev': 5390.0, 'value': 18360.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2011, 'prev': 3662.0, 'value': 7808.0, 'precision': 'exact'}] |
| mig_emigration_foreign | 6 | 3 | [{'unit_id': '6253', 'year': 2012, 'prev': 183.0, 'value': 809.0, 'precision': 'exact'}, {'unit_id': '5236', 'year': 2013, 'prev': 360.0, 'value': 80.0, 'precision': 'exact'}] |
| mfz_cars_diesel | 6 | 6 | [{'unit_id': '3101', 'year': 2018, 'prev': 1710.0, 'value': 7961.0, 'precision': 'exact'}, {'unit_id': '1702', 'year': 2018, 'prev': 7378.0, 'value': 3508.0, 'precision': 'exact'}] |
| mfz_cars_petrol | 6 | 6 | [{'unit_id': '3101', 'year': 2018, 'prev': 3589.0, 'value': 10124.0, 'precision': 'exact'}, {'unit_id': '6240', 'year': 2011, 'prev': 4496.0, 'value': 1169.0, 'precision': 'exact'}] |
| agr_area_grassland_ha | 5 | 3 | [{'unit_id': '3961', 'year': 2011, 'prev': 382.0, 'value': 1049.0, 'precision': 'exact'}, {'unit_id': '4506', 'year': 1998, 'prev': 1011.0, 'value': 373.0, 'precision': 'exact'}] |
| ent_jobs_retail | 5 | 5 | [{'unit_id': '540', 'year': 2017, 'prev': 121.0, 'value': 586.0, 'precision': 'exact'}, {'unit_id': '412', 'year': 2013, 'prev': 331.0, 'value': 740.0, 'precision': 'exact'}] |
| vac_new | 5 | 3 | [{'unit_id': '3203', 'year': 2022, 'prev': 365.0, 'value': 103.0, 'precision': 'exact'}, {'unit_id': '3203', 'year': 2017, 'prev': 44.0, 'value': 283.0, 'precision': 'exact'}] |
| ent_jobs_care_social | 5 | 5 | [{'unit_id': '6633', 'year': 2022, 'prev': 418.0, 'value': 994.0, 'precision': 'exact'}, {'unit_id': '5568', 'year': 2018, 'prev': 81.0, 'value': 331.0, 'precision': 'exact'}] |
| udemo_jobs_closures | 4 | 2 | [{'unit_id': '66', 'year': 2019, 'prev': 400.0, 'value': 131.0, 'precision': 'exact'}, {'unit_id': '66', 'year': 2018, 'prev': 135.0, 'value': 400.0, 'precision': 'exact'}] |
| mfz_cars_phev | 4 | 3 | [{'unit_id': '3101', 'year': 2023, 'prev': 326.0, 'value': 969.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2020, 'prev': 57.0, 'value': 519.0, 'precision': 'exact'}] |
| mig_immigration_swiss | 4 | 2 | [{'unit_id': '3673', 'year': 2014, 'prev': 541.0, 'value': 1.0, 'precision': 'exact'}, {'unit_id': '3673', 'year': 2013, 'prev': 5.0, 'value': 541.0, 'precision': 'exact'}] |
| ent_jobs_s3 | 4 | 4 | [{'unit_id': '5412', 'year': 2020, 'prev': 733.0, 'value': 2658.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 580.0, 'value': 1639.0, 'precision': 'exact'}] |
| ent_fte_s3 | 4 | 4 | [{'unit_id': '5412', 'year': 2020, 'prev': 590.0, 'value': 2125.0, 'precision': 'exact'}, {'unit_id': '2527', 'year': 2023, 'prev': 1214.0, 'value': 560.0, 'precision': 'exact'}] |
| mig_intracant_out_swiss | 3 | 3 | [{'unit_id': '5002', 'year': 2017, 'prev': 1319.0, 'value': 637.0, 'precision': 'exact'}, {'unit_id': '3112', 'year': 2013, 'prev': 2.0, 'value': 224.0, 'precision': 'exact'}] |
| mig_intracant_in_foreign | 3 | 3 | [{'unit_id': '5583', 'year': 2024, 'prev': 375.0, 'value': 885.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2021, 'prev': 191.0, 'value': 545.0, 'precision': 'exact'}] |
| tax_np_normal_taxable_class_1_30k | 3 | 3 | [{'unit_id': '843', 'year': 2021, 'prev': 1381.0, 'value': 674.0, 'precision': 'exact'}, {'unit_id': '584', 'year': 2021, 'prev': 824.0, 'value': 309.0, 'precision': 'exact'}] |
| ent_jobs_women | 3 | 3 | [{'unit_id': '5412', 'year': 2020, 'prev': 404.0, 'value': 1813.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 529.0, 'value': 1373.0, 'precision': 'exact'}] |
| bevnat_divorces | 3 | 2 | [{'unit_id': '2701', 'year': 2000, 'prev': 534.0, 'value': 211.0, 'precision': 'exact'}, {'unit_id': '351', 'year': 2000, 'prev': 502.0, 'value': 183.0, 'precision': 'exact'}] |
| agr_horses | 3 | 2 | [{'unit_id': '6248', 'year': 2013, 'prev': 375.0, 'value': 8.0, 'precision': 'exact'}, {'unit_id': '6248', 'year': 2012, 'prev': 16.0, 'value': 375.0, 'precision': 'exact'}] |
| agr_workers | 3 | 2 | [{'unit_id': '4446', 'year': 2015, 'prev': 260.0, 'value': 41.0, 'precision': 'exact'}, {'unit_id': '1146', 'year': 2025, 'prev': 261.0, 'value': 49.0, 'precision': 'exact'}] |
| crime_stgb_property | 3 | 3 | [{'unit_id': '66', 'year': 2011, 'prev': 1622.0, 'value': 707.0, 'precision': 'exact'}, {'unit_id': '2703', 'year': 2012, 'prev': 632.0, 'value': 1300.0, 'precision': 'exact'}] |
| ent_jobs_education | 3 | 3 | [{'unit_id': '5214', 'year': 2021, 'prev': 475.0, 'value': 162.0, 'precision': 'exact'}, {'unit_id': '6623', 'year': 2022, 'prev': 171.0, 'value': 424.0, 'precision': 'exact'}] |
| vac_for_sale | 3 | 3 | [{'unit_id': '6248', 'year': 2020, 'prev': 40.0, 'value': 270.0, 'precision': 'exact'}, {'unit_id': '1024', 'year': 2022, 'prev': 237.0, 'value': 24.0, 'precision': 'exact'}] |
| nat_eu_efta | 3 | 3 | [{'unit_id': '6621', 'year': 2015, 'prev': 404.0, 'value': 1234.0, 'precision': 'exact'}, {'unit_id': '6628', 'year': 2015, 'prev': 102.0, 'value': 319.0, 'precision': 'exact'}] |
| nat_outside_europe | 3 | 1 | [{'unit_id': '6621', 'year': 2020, 'prev': 806.0, 'value': 237.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2015, 'prev': 331.0, 'value': 768.0, 'precision': 'exact'}] |
| mfz_cars_bev | 3 | 2 | [{'unit_id': '3101', 'year': 2023, 'prev': 245.0, 'value': 898.0, 'precision': 'exact'}, {'unit_id': '86', 'year': 2018, 'prev': 251.0, 'value': 576.0, 'precision': 'exact'}] |
| gws_dw_2001plus | 3 | 3 | [{'unit_id': '131', 'year': 2011, 'prev': 353.0, 'value': 988.0, 'precision': 'exact'}, {'unit_id': '5583', 'year': 2020, 'prev': 581.0, 'value': 1212.0, 'precision': 'exact'}] |
| nat_women | 2 | 1 | [{'unit_id': '6621', 'year': 2015, 'prev': 485.0, 'value': 1233.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2020, 'prev': 1182.0, 'value': 563.0, 'precision': 'exact'}] |
| mig_intracant_out_foreign | 2 | 1 | [{'unit_id': '56', 'year': 2017, 'prev': 849.0, 'value': 323.0, 'precision': 'exact'}, {'unit_id': '56', 'year': 2016, 'prev': 337.0, 'value': 849.0, 'precision': 'exact'}] |
| bil_pop_dec | 2 | 2 | [{'unit_id': '4536', 'year': 1999, 'prev': 3082.0, 'value': 1476.0, 'precision': 'exact'}, {'unit_id': '4741', 'year': 1995, 'prev': 2119.0, 'value': 925.0, 'precision': 'exact'}] |
| bil_pop_jan | 2 | 2 | [{'unit_id': '4536', 'year': 1999, 'prev': 3120.0, 'value': 1456.0, 'precision': 'exact'}, {'unit_id': '4741', 'year': 1995, 'prev': 2021.0, 'value': 908.0, 'precision': 'exact'}] |
| bil_pop_foreign_jan | 2 | 2 | [{'unit_id': '564', 'year': 2007, 'prev': 303.0, 'value': 37.0, 'precision': 'exact'}, {'unit_id': '4741', 'year': 1995, 'prev': 338.0, 'value': 106.0, 'precision': 'exact'}] |
| bevnat_births | 2 | 2 | [{'unit_id': '352', 'year': 1983, 'prev': 463.0, 'value': 91.0, 'precision': 'exact'}, {'unit_id': '363', 'year': 1983, 'prev': 0.0, 'value': 248.0, 'precision': 'exact'}] |
| tax_np_taxpayers_normal | 2 | 1 | [{'unit_id': '3790', 'year': 2022, 'prev': 1078.0, 'value': 528.0, 'precision': 'exact'}, {'unit_id': '3790', 'year': 2021, 'prev': 530.0, 'value': 1078.0, 'precision': 'exact'}] |
| mig_emigration_swiss | 2 | 1 | [{'unit_id': '6487', 'year': 2013, 'prev': 442.0, 'value': 42.0, 'precision': 'exact'}, {'unit_id': '6487', 'year': 2012, 'prev': 50.0, 'value': 442.0, 'precision': 'exact'}] |
| sh_recipients | 2 | 2 | [{'unit_id': '131', 'year': 2008, 'prev': 708.0, 'value': 345.0, 'precision': 'exact'}, {'unit_id': '1632', 'year': 2008, 'prev': 87.0, 'value': 306.0, 'precision': 'exact'}] |
| gws_heat_other | 2 | 2 | [{'unit_id': '6205', 'year': 2022, 'prev': 300.0, 'value': 1.0, 'precision': 'exact'}, {'unit_id': '3871', 'year': 2022, 'prev': 1.0, 'value': 215.0, 'precision': 'exact'}] |
| gws_heat_none | 2 | 2 | [{'unit_id': '5226', 'year': 2024, 'prev': 61.0, 'value': 288.0, 'precision': 'exact'}, {'unit_id': '5192', 'year': 2024, 'prev': 114.0, 'value': 321.0, 'precision': 'exact'}] |
| gws_heat_oil | 2 | 2 | [{'unit_id': '4001', 'year': 2025, 'prev': 1551.0, 'value': 763.0, 'precision': 'exact'}, {'unit_id': '3271', 'year': 2025, 'prev': 1126.0, 'value': 478.0, 'precision': 'exact'}] |
| gws_dw_rooms_1_2 | 2 | 2 | [{'unit_id': '5061', 'year': 2013, 'prev': 923.0, 'value': 225.0, 'precision': 'exact'}, {'unit_id': '5633', 'year': 2014, 'prev': 144.0, 'value': 410.0, 'precision': 'exact'}] |
| ent_jobs_accommodation | 1 | 1 | [{'unit_id': '1505', 'year': 2017, 'prev': 83.0, 'value': 284.0, 'precision': 'exact'}] |
| crime_stgb_offences | 1 | 1 | [{'unit_id': '2703', 'year': 2012, 'prev': 869.0, 'value': 1837.0, 'precision': 'exact'}] |
| bevnat_marriages | 1 | 1 | [{'unit_id': '352', 'year': 1983, 'prev': 236.0, 'value': 24.0, 'precision': 'exact'}] |
| agr_workers_fulltime | 1 | 1 | [{'unit_id': '1146', 'year': 2025, 'prev': 236.0, 'value': 23.0, 'precision': 'exact'}] |
| agr_area_permanent_crops_ha | 1 | 1 | [{'unit_id': '5861', 'year': 2023, 'prev': 15.0, 'value': 254.0, 'precision': 'exact'}] |
| gws_bld_2011plus | 1 | 1 | [{'unit_id': '261', 'year': 2011, 'prev': 0.0, 'value': 273.0, 'precision': 'exact'}] |
| gws_bld_mfh | 1 | 1 | [{'unit_id': '5061', 'year': 2013, 'prev': 688.0, 'value': 271.0, 'precision': 'exact'}] |
| gws_bld_1946_1980 | 1 | 1 | [{'unit_id': '6087', 'year': 2015, 'prev': 185.0, 'value': 442.0, 'precision': 'exact'}] |
| gws_heat_electric | 1 | 1 | [{'unit_id': '6205', 'year': 2022, 'prev': 39.0, 'value': 416.0, 'precision': 'exact'}] |
| gws_bld_sfh | 1 | 1 | [{'unit_id': '5061', 'year': 2013, 'prev': 157.0, 'value': 562.0, 'precision': 'exact'}] |
| gws_dw_area_lt60 | 1 | 1 | [{'unit_id': '5633', 'year': 2014, 'prev': 135.0, 'value': 403.0, 'precision': 'exact'}] |
| gws_dw_rooms_3 | 1 | 1 | [{'unit_id': '5192', 'year': 2012, 'prev': 3671.0, 'value': 11549.0, 'precision': 'exact'}] |
| mig_intercant_in_swiss | 1 | 1 | [{'unit_id': '4040', 'year': 2025, 'prev': 186.0, 'value': 403.0, 'precision': 'exact'}] |
| mfz_cars_private | 1 | 1 | [{'unit_id': '905', 'year': 2025, 'prev': 641.0, 'value': 1435.0, 'precision': 'exact'}] |
| tax_np_taxpayers | 1 | 1 | [{'unit_id': '5151', 'year': 2010, 'prev': 3247.0, 'value': 1489.0, 'precision': 'exact'}] |
| xb_commuters | 1 | 1 | [{'unit_id': '2703', 'year': 1997, 'prev': 12.7156015, 'value': 476.728855, 'precision': 'modelled'}] |

## D. Coverage (municipality level, latest period)

| Metric | Periods | First | Latest | With value | Gap reasons |
|---|---|---|---|---|---|
| acc_bicycle_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_dist_bank | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_dentist | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_doctor | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_dist_forest | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_dist_gp | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_dist_grocery | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_nursing_home | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_pharmacy | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_pt_stop | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_pt_stop_cat12 | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_public_admin | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_restaurant | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_school_compulsory | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_school_upper_secondary | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_dist_supermarket | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_fatal_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_injury_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_injury_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_motorcycle_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_nonmotorway_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_nonmotorway_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_pedestrian_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_population | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_severe_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_severe_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_severe_share | 15 | 2011 | 2025 | 1762 / 2110 | – |
| acc_share1000_doctor | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_share1000_gp | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_share1000_grocery | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share1000_pharmacy | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share1000_pt_stop_cat12 | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share1000_school_compulsory | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share1000_supermarket | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share500_gp | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_share500_grocery | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share500_pharmacy | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share500_pt_stop | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share500_school_compulsory | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_share500_supermarket | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within1000_doctor | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_within1000_gp | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_within1000_grocery | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within1000_pharmacy | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within1000_pt_stop_cat12 | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within1000_school_compulsory | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within1000_supermarket | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within500_gp | 2 | 2018 | 2021 | 2110 / 2110 | – |
| acc_within500_grocery | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within500_pharmacy | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within500_pt_stop | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within500_school_compulsory | 4 | 2011 | 2021 | 2110 / 2110 | – |
| acc_within500_supermarket | 4 | 2011 | 2021 | 2110 / 2110 | – |
| agr_area_arable_ha | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_area_grassland_ha | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_area_ha | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_area_organic_ha | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_area_per_farm | 28 | 1975 | 2025 | 2081 / 2110 | – |
| agr_area_permanent_crops_ha | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_cattle | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_farms | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_farms_change_10y | 16 | 1985 | 2025 | 2079 / 2110 | – |
| agr_farms_organic | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_goats | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_horses | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_pigs | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_poultry | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_share_arable | 28 | 1975 | 2025 | 2076 / 2110 | – |
| agr_share_organic_area | 25 | 1990 | 2025 | 2076 / 2110 | – |
| agr_share_organic_farms | 25 | 1990 | 2025 | 2081 / 2110 | – |
| agr_sheep | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_workers | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_workers_family | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_workers_fulltime | 28 | 1975 | 2025 | 2110 / 2110 | – |
| agr_workers_per_1000 | 24 | 1985 | 2025 | 2110 / 2110 | – |
| agr_workers_women | 28 | 1975 | 2025 | 2110 / 2110 | – |
| air_hectare_residents | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_no2_above_limit_residents | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_no2_above_limit_share | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_no2_pop | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_pm10_above_limit_residents | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_pm10_above_limit_share | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_pm10_pop | 4 | 2010 | 2025 | 2110 / 2110 | – |
| air_pm25_above_limit_residents | 3 | 2015 | 2025 | 2110 / 2110 | – |
| air_pm25_above_limit_share | 3 | 2015 | 2025 | 2110 / 2110 | – |
| air_pm25_pop | 3 | 2015 | 2025 | 2110 / 2110 | – |
| area_agriculture_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_building_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_glacier_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_industrial_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_sealed_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_settlement_base_ha | 4 | 1992/97 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_settlement_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_settlement_index | 4 | 1992/97 | 2020/25 | 1007 / 2110 | – |
| area_share_agriculture | 5 | 1979/85 | 2020/25 | 1007 / 2110 | – |
| area_share_sealed | 5 | 1979/85 | 2020/25 | 1007 / 2110 | – |
| area_share_settlement | 5 | 1979/85 | 2020/25 | 1007 / 2110 | – |
| area_share_unproductive | 5 | 1979/85 | 2020/25 | 1007 / 2110 | – |
| area_share_wooded | 5 | 1979/85 | 2020/25 | 1007 / 2110 | – |
| area_total_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_transport_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_unproductive_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_water_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| area_wooded_ha | 5 | 1979/85 | 2020/25 | 1007 / 2110 | {'not_covered': 1103} |
| bevnat_birth_rate | 16 | 2010 | 2025 | 1829 / 2110 | – |
| bevnat_births | 57 | 1969 | 2025 | 1829 / 2110 | {'suppressed': 281} |
| bevnat_divorce_rate | 16 | 2010 | 2025 | 1300 / 2110 | – |
| bevnat_divorces | 57 | 1969 | 2025 | 1300 / 2110 | {'suppressed': 810} |
| bevnat_marriage_rate | 16 | 2010 | 2025 | 1563 / 2110 | – |
| bevnat_marriages | 57 | 1969 | 2025 | 1563 / 2110 | {'suppressed': 547} |
| bil_birth_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_births | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_death_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_deaths | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_emigration | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_immigration | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_intercant_in | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_intercant_out | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_intracant_in | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_intracant_out | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_natural_balance | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_natural_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_naturalisation_rate | 45 | 1981 | 2025 | 2109 / 2110 | – |
| bil_naturalisations | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_net_intercant | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_net_intercant_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_net_international | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_net_international_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_net_migration | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_net_migration_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_pop_dec | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_pop_foreign_jan | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_pop_jan | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bil_turnover_rate | 45 | 1981 | 2025 | 2110 / 2110 | – |
| bz_area_centre_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_mixed_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_other_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_per_inhabitant | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_pt_a_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_pt_b_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_pt_c_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_pt_d_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_pt_none_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_public_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_residential_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_total_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_area_work_ha | 2 | 2017 | 2022 | 2110 / 2110 | – |
| bz_share_pt_good | 2 | 2017 | 2022 | 2101 / 2110 | – |
| bz_share_residential | 2 | 2017 | 2022 | 2101 / 2110 | – |
| bz_share_unbuilt_high | 1 | 2022 | 2022 | 2101 / 2110 | – |
| bz_share_unbuilt_low | 1 | 2022 | 2022 | 2101 / 2110 | – |
| bz_unbuilt_high_ha | 1 | 2022 | 2022 | 2110 / 2110 | – |
| bz_unbuilt_low_ha | 1 | 2022 | 2022 | 2110 / 2110 | – |
| clim_precip_area | 2 | 1961-1990 | 1991-2020 | 2110 / 2110 | – |
| clim_precip_pop | 2 | 1961-1990 | 1991-2020 | 2110 / 2110 | – |
| clim_sunshine_area | 2 | 1961-1990 | 1991-2020 | 2110 / 2110 | – |
| clim_sunshine_pop | 2 | 1961-1990 | 1991-2020 | 2110 / 2110 | – |
| clim_temp_area | 2 | 1961-1990 | 1991-2020 | 2110 / 2110 | – |
| clim_temp_pop | 2 | 1961-1990 | 1991-2020 | 2110 / 2110 | – |
| com_balance | 3 | 2014 | 2020 | 2110 / 2110 | – |
| com_employed_residents | 3 | 2014 | 2020 | 2110 / 2110 | – |
| com_in_commuters | 3 | 2014 | 2020 | 2105 / 2110 | {'suppressed': 5} |
| com_in_share | 3 | 2014 | 2020 | 2105 / 2110 | – |
| com_job_ratio | 3 | 2014 | 2020 | 2110 / 2110 | – |
| com_jobs | 3 | 2014 | 2020 | 2110 / 2110 | – |
| com_out_commuters | 3 | 2014 | 2020 | 2105 / 2110 | {'suppressed': 5} |
| com_out_share | 3 | 2014 | 2020 | 2105 / 2110 | – |
| com_self_containment | 3 | 2014 | 2020 | 2105 / 2110 | – |
| com_work_in_own | 3 | 2014 | 2020 | 2105 / 2110 | {'suppressed': 5} |
| con_exp_maintenance | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_exp_per_capita | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_exp_private | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_exp_public | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_exp_total | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_inv_new | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_inv_per_capita | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_inv_renovation | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_inv_residential | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_inv_residential_per_capita | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_inv_total | 31 | 1994 | 2024 | 2110 / 2110 | – |
| con_new_dw_mfh | 30 | 1995 | 2024 | 2110 / 2110 | – |
| con_new_dw_sfh | 30 | 1995 | 2024 | 2110 / 2110 | – |
| con_new_dwellings | 30 | 1995 | 2024 | 2110 / 2110 | – |
| con_new_dwellings_per_1000 | 30 | 1995 | 2024 | 2110 / 2110 | – |
| con_new_res_buildings | 30 | 1995 | 2024 | 2110 / 2110 | – |
| con_new_sfh_buildings | 30 | 1995 | 2024 | 2110 / 2110 | – |
| con_share_exp_public | 31 | 1994 | 2024 | 2108 / 2110 | – |
| con_share_inv_renovation | 31 | 1994 | 2024 | 2096 / 2110 | – |
| con_share_new_dw_mfh | 30 | 1995 | 2024 | 1528 / 2110 | – |
| crime_burglaries | 17 | 2009 | 2025 | 160 / 2110 | {'not_covered': 1950} |
| crime_burglaries_per_1000 | 16 | 2010 | 2025 | 160 / 2110 | – |
| crime_property_per_1000 | 16 | 2010 | 2025 | 37 / 2110 | – |
| crime_stgb_offences | 17 | 2009 | 2025 | 102 / 2110 | {'not_published': 172, 'not_covered': 1836} |
| crime_stgb_per_1000 | 16 | 2010 | 2025 | 102 / 2110 | – |
| crime_stgb_property | 17 | 2009 | 2025 | 37 / 2110 | {'not_covered': 1947, 'not_published': 126} |
| crime_stgb_violent | 17 | 2009 | 2025 | 37 / 2110 | {'not_covered': 1947, 'not_published': 126} |
| crime_violent_per_1000 | 16 | 2010 | 2025 | 37 / 2110 | – |
| edu_compulsory_25_64 | 9 | 1990 | 2023 | 2035 / 2110 | {'suppressed': 75} |
| edu_imputation_share | 7 | 2017 | 2023 | 2110 / 2110 | – |
| edu_known_25_64 | 9 | 1990 | 2023 | 2035 / 2110 | {'suppressed': 75} |
| edu_labb_matura_rate | 1 | 2010-2014 | 2010-2014 | 975 / 2110 | {'suppressed': 1135} |
| edu_labb_upsec2_after25_rate | 1 | 2010-2014 | 2010-2014 | 989 / 2110 | {'suppressed': 1121} |
| edu_labb_upsec2_rate | 1 | 2010-2014 | 2010-2014 | 989 / 2110 | {'suppressed': 1121} |
| edu_pop_25_64 | 9 | 1990 | 2023 | 2110 / 2110 | – |
| edu_share_compulsory | 9 | 1990 | 2023 | 2035 / 2110 | – |
| edu_share_tertiary | 9 | 1990 | 2023 | 2035 / 2110 | – |
| edu_share_upper_secondary | 9 | 1990 | 2023 | 2035 / 2110 | – |
| edu_tertiary_25_64 | 9 | 1990 | 2023 | 2035 / 2110 | {'suppressed': 75} |
| edu_upper_secondary_25_64 | 9 | 1990 | 2023 | 2035 / 2110 | {'suppressed': 75} |
| en_charging_spots | 34 | 2023-11 | 2026-10 | 2110 / 2110 | – |
| en_ecar_count | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_ecar_share | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_elec_consumption_mwh | 40 | 2023-05 | 2026-10 | 2110 / 2110 | – |
| en_elec_consumption_per_capita | 40 | 2023-05 | 2026-10 | 2110 / 2110 | – |
| en_heat_nonrenewable_count | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_heat_renewable_count | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_heat_renewable_share | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_pv_installed_kwp | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_pv_kwp_per_capita | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_renelec_hydro_mwh | 35 | 2023-10 | 2026-10 | 2110 / 2110 | – |
| en_renelec_per_capita | 35 | 2023-10 | 2026-10 | 2110 / 2110 | – |
| en_renelec_production_mwh | 35 | 2023-10 | 2026-10 | 2110 / 2110 | – |
| en_renelec_solar_mwh | 35 | 2023-10 | 2026-10 | 2110 / 2110 | – |
| en_solar_potential_used | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_solar_roof_facade_potential_gwh | 1 | 2025 | 2025 | 2110 / 2110 | – |
| en_solar_roof_potential_gwh | 1 | 2025 | 2025 | 2110 / 2110 | – |
| energiestadt_gold | 1 | 2026 | 2026 | 2110 / 2110 | – |
| energiestadt_label | 1 | 2026 | 2026 | 2110 / 2110 | – |
| energiestadt_score | 1 | 2026 | 2026 | 465 / 2110 | {'not_applicable': 1645} |
| ent_fte | 14 | 2011 | 2024 | 2106 / 2110 | {'suppressed': 4} |
| ent_fte_per_job | 14 | 2011 | 2024 | 2105 / 2110 | – |
| ent_fte_s1 | 14 | 2011 | 2024 | 1960 / 2110 | {'suppressed': 150} |
| ent_fte_s2 | 14 | 2011 | 2024 | 1942 / 2110 | {'suppressed': 168} |
| ent_fte_s3 | 14 | 2011 | 2024 | 2040 / 2110 | {'suppressed': 70} |
| ent_jobs | 14 | 2011 | 2024 | 2107 / 2110 | {'suppressed': 3} |
| ent_jobs_accommodation | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_care_social | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_change_10y | 4 | 2021 | 2024 | 2107 / 2110 | – |
| ent_jobs_education | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_finance | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_food_service | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_health | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_ict | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_per_1000 | 14 | 2011 | 2024 | 2107 / 2110 | – |
| ent_jobs_per_workplace | 14 | 2011 | 2024 | 2107 / 2110 | – |
| ent_jobs_retail | 14 | 2011 | 2024 | 2110 / 2110 | – |
| ent_jobs_s1 | 14 | 2011 | 2024 | 2027 / 2110 | {'suppressed': 83} |
| ent_jobs_s2 | 14 | 2011 | 2024 | 2017 / 2110 | {'suppressed': 93} |
| ent_jobs_s3 | 14 | 2011 | 2024 | 2074 / 2110 | {'suppressed': 36} |
| ent_jobs_women | 14 | 2011 | 2024 | 2080 / 2110 | {'suppressed': 30} |
| ent_share_jobs_accommodation_food | 14 | 2011 | 2024 | 2107 / 2110 | – |
| ent_share_jobs_health_social | 14 | 2011 | 2024 | 2107 / 2110 | – |
| ent_share_jobs_s1 | 14 | 2011 | 2024 | 2025 / 2110 | – |
| ent_share_jobs_s2 | 14 | 2011 | 2024 | 2016 / 2110 | – |
| ent_share_jobs_s3 | 14 | 2011 | 2024 | 2073 / 2110 | – |
| ent_share_jobs_women | 14 | 2011 | 2024 | 2080 / 2110 | – |
| ent_workplaces | 14 | 2011 | 2024 | 2108 / 2110 | {'suppressed': 2} |
| ent_workplaces_s1 | 14 | 2011 | 2024 | 1840 / 2110 | {'suppressed': 270} |
| ent_workplaces_s2 | 14 | 2011 | 2024 | 1824 / 2110 | {'suppressed': 286} |
| ent_workplaces_s3 | 14 | 2011 | 2024 | 2067 / 2110 | {'suppressed': 43} |
| fin_net_debt_per_capita | 36 | 1990 | 2025 | 548 / 2110 | {'no_data': 605, 'not_applicable': 2, 'not_covered': 955} |
| fin_self_financing_ratio | 36 | 1990 | 2025 | 778 / 2110 | {'not_covered': 700, 'not_applicable': 72, 'no_data': 560} |
| fin_tax_revenue_chf | 36 | 1990 | 2025 | 240 / 2110 | {'not_covered': 1610, 'no_data': 260} |
| fin_tax_revenue_per_capita | 16 | 2010 | 2025 | 240 / 2110 | – |
| geo_area_lake_ha | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_area_land_ha | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_area_total_ha | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_elev_max | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_elev_mean | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_elev_median | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_elev_min | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_lake_share | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_pop_density | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gk_pop_a | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_pop_b | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_pop_c | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_pop_d | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_pop_none | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_population | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_share_a | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_share_ab | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_share_b | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_share_c | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_share_d | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gk_share_none | 15 | 2012 | 2026 | 2110 / 2110 | – |
| gws_bld_1919_1945 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_1946_1980 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_1981_2000 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_2001_2010 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_2011plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_mfh | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_partly_res | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_pre1919 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_res_mixed | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_bld_sfh | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_buildings | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dw_2001plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dw_2011plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dw_area_100_119 | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_dw_area_120_159 | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_dw_area_160plus | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_dw_area_60_79 | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_dw_area_80_99 | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_dw_area_lt60 | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_dw_rooms_1_2 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dw_rooms_3 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dw_rooms_4 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dw_rooms_5plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_dwellings | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_heat_district | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_electric | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_gas | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_heatpump | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_none | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_oil | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_other | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_heat_wood | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_share_bld_2001plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_share_bld_pre1946 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_share_district | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_share_dw_2001plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_share_dw_large | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_share_dw_lt60 | 14 | 2012 | 2025 | 2110 / 2110 | – |
| gws_share_dw_small | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_share_fossil | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_share_gas | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_share_heatpump | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_share_oil | 5 | 2021 | 2025 | 2110 / 2110 | – |
| gws_share_sfh | 16 | 2010 | 2025 | 2110 / 2110 | – |
| gws_share_wood | 5 | 2021 | 2025 | 2110 / 2110 | – |
| haz_hectare_residents | 1 | 2026 | 2026 | 1770 / 2110 | {'not_covered': 340} |
| haz_residents_assessed | 1 | 2026 | 2026 | 1651 / 2110 | {'not_covered': 340, 'no_data': 119} |
| haz_residents_high | 1 | 2026 | 2026 | 1770 / 2110 | {'not_covered': 340} |
| haz_residents_medium | 1 | 2026 | 2026 | 1770 / 2110 | {'not_covered': 340} |
| haz_share_assessed | 1 | 2026 | 2026 | 1651 / 2110 | – |
| haz_share_high | 1 | 2026 | 2026 | 1770 / 2110 | – |
| haz_share_high_medium | 1 | 2026 | 2026 | 1770 / 2110 | – |
| haz_share_medium | 1 | 2026 | 2026 | 1770 / 2110 | – |
| hh_avg_size | 14 | 2012 | 2025 | 2110 / 2110 | – |
| hh_persons | 14 | 2012 | 2025 | 2110 / 2110 | – |
| hh_share_1p | 14 | 2012 | 2025 | 2108 / 2110 | – |
| hh_share_4plus | 14 | 2012 | 2025 | 1748 / 2110 | – |
| hh_size1 | 14 | 2012 | 2025 | 2108 / 2110 | {'suppressed': 2} |
| hh_size2 | 14 | 2012 | 2025 | 2108 / 2110 | {'suppressed': 2} |
| hh_size3 | 14 | 2012 | 2025 | 2098 / 2110 | {'suppressed': 12} |
| hh_size4 | 14 | 2012 | 2025 | 2092 / 2110 | {'suppressed': 18} |
| hh_size5 | 14 | 2012 | 2025 | 2031 / 2110 | {'suppressed': 79} |
| hh_size6plus | 14 | 2012 | 2025 | 1793 / 2110 | {'suppressed': 317} |
| hh_total | 14 | 2012 | 2025 | 2110 / 2110 | – |
| kvg_mean_premium_adult | 1 | 2027 | 2027 | 2110 / 2110 | – |
| kvg_mean_premium_child | 1 | 2027 | 2027 | 2110 / 2110 | – |
| kvg_mean_premium_young | 1 | 2027 | 2027 | 2110 / 2110 | – |
| kvg_std300_mean_adult | 2 | 2026 | 2027 | 2110 / 2110 | – |
| kvg_std300_median_adult | 2 | 2026 | 2027 | 2110 / 2110 | – |
| kvg_std300_min_adult | 2 | 2026 | 2027 | 2110 / 2110 | – |
| land_price_m2 | 52 | 1974 | 2025 | 30 / 2110 | {'not_covered': 1864, 'no_data': 192, 'suppressed': 24} |
| land_price_model_m2 | 51 | 1974 | 2024 | 160 / 2110 | {'not_covered': 1950} |
| land_transactions | 52 | 1974 | 2025 | 62 / 2110 | {'not_covered': 1864, 'no_data': 160, 'suppressed': 24} |
| mfz_bev_share | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_bev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_diesel | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_hev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_per_1000 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_petrol | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_phev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_private | 10 | 2016 | 2025 | 2110 / 2110 | – |
| mfz_cars_private_per_1000 | 10 | 2016 | 2025 | 2110 / 2110 | – |
| mfz_newreg_bev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_newreg_bev_share | 16 | 2010 | 2025 | 2098 / 2110 | – |
| mfz_newreg_cars | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_plugin_share | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mig_emigration_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_emigration_rate | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_emigration_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_immigration_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_immigration_rate | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_immigration_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intercant_in_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intercant_in_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intercant_out_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intercant_out_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intracant_in_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intracant_in_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intracant_out_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_intracant_out_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_net_intercant_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_net_intercant_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_net_intl_foreign | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_net_intl_foreign_rate | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_net_intl_swiss | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_net_intl_swiss_rate | 15 | 2011 | 2025 | 2110 / 2110 | – |
| mig_share_foreign_immigrants | 15 | 2011 | 2025 | 2051 / 2110 | – |
| nat_eu_efta | 15 | 2011 | 2025 | 2110 / 2110 | – |
| nat_other_europe | 15 | 2011 | 2025 | 2110 / 2110 | – |
| nat_outside_europe | 15 | 2011 | 2025 | 2110 / 2110 | – |
| nat_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| nat_rate | 15 | 2011 | 2025 | 2109 / 2110 | – |
| nat_share_eu_efta | 15 | 2011 | 2025 | 1660 / 2110 | – |
| nat_total | 15 | 2011 | 2025 | 2110 / 2110 | – |
| nat_women | 15 | 2011 | 2025 | 2110 / 2110 | – |
| nrw_ballots_blank | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_ballots_changed | 14 | 1971 | 2023 | 2040 / 2110 | {'not_published': 5, 'no_data': 65} |
| nrw_ballots_invalid | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_ballots_unchanged | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_ballots_valid | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_eligible | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_fw_bdp | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_csp | 14 | 1971 | 2023 | 119 / 2110 | {'not_applicable': 1986, 'no_data': 5} |
| nrw_fw_cvp | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_edu | 14 | 1971 | 2023 | 1499 / 2110 | {'not_published': 5, 'not_applicable': 606} |
| nrw_fw_evp | 14 | 1971 | 2023 | 1818 / 2110 | {'not_published': 5, 'not_applicable': 287} |
| nrw_fw_fdp | 14 | 1971 | 2023 | 2078 / 2110 | {'not_published': 5, 'not_applicable': 27} |
| nrw_fw_fga | 14 | 1971 | 2023 | 160 / 2110 | {'not_applicable': 1945, 'no_data': 5} |
| nrw_fw_fps | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_glp | 14 | 1971 | 2023 | 2040 / 2110 | {'not_published': 5, 'not_applicable': 65} |
| nrw_fw_gruene | 14 | 1971 | 2023 | 2040 / 2110 | {'not_published': 5, 'not_applicable': 65} |
| nrw_fw_ldu | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_lega | 14 | 1971 | 2023 | 100 / 2110 | {'not_applicable': 2005, 'no_data': 5} |
| nrw_fw_lps | 14 | 1971 | 2023 | 3 / 2110 | {'not_applicable': 2102, 'no_data': 5} |
| nrw_fw_mcr | 14 | 1971 | 2023 | 45 / 2110 | {'not_applicable': 2060, 'no_data': 5} |
| nrw_fw_mitte | 14 | 1971 | 2023 | 2098 / 2110 | {'not_applicable': 7, 'not_published': 5} |
| nrw_fw_other | 14 | 1971 | 2023 | 1941 / 2110 | {'not_applicable': 164, 'not_published': 5} |
| nrw_fw_pda | 14 | 1971 | 2023 | 802 / 2110 | {'not_applicable': 1303, 'no_data': 5} |
| nrw_fw_poch | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_psa | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_rep | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_sd | 14 | 1971 | 2023 | 644 / 2110 | {'not_published': 5, 'not_applicable': 1461} |
| nrw_fw_sep | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_sol | 14 | 1971 | 2023 | 369 / 2110 | {'not_applicable': 1736, 'no_data': 5} |
| nrw_fw_sp | 14 | 1971 | 2023 | 2043 / 2110 | {'not_applicable': 62, 'not_published': 5} |
| nrw_fw_svp | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_fw_total | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| nrw_share_bdp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_csp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_cvp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_edu | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_evp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_fdp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_fga | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_fps | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_glp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_gruene | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_ldu | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_left_bloc | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_lega | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_lps | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_mcr | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_mitte | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_other | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_pda | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_poch | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_psa | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_rep | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_right_bloc | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_sd | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_sep | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_sol | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_sp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_share_svp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_turnout | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_unchanged_share | 13 | 1975 | 2023 | 2105 / 2110 | – |
| nrw_voters | 14 | 1971 | 2023 | 2105 / 2110 | {'not_published': 5} |
| old_age_dependency | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pa_biotopes_ha | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pa_biotopes_share | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pa_bln_ha | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pa_bln_share | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pa_municipal_area_ha | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pa_parks_ha | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pa_parks_share | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pop_age_0_19 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_age_20_64 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_age_65_79 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_age_80plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_change_10y | 6 | 2020 | 2025 | 2110 / 2110 | – |
| pop_change_1y | 15 | 2011 | 2025 | 2110 / 2110 | – |
| pop_change_5y | 11 | 2015 | 2025 | 2110 / 2110 | – |
| pop_divorced | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_female | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_foreign | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_male | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_married | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_nonpermanent | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_single | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_swiss | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_total | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pop_widowed | 16 | 2010 | 2025 | 2110 / 2110 | – |
| pt_stops_boat | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_bus | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_cableway | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_per_1000 | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_per_km2 | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_rail | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_total | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pt_stops_tram_metro | 1 | 2026 | 2026 | 2110 / 2110 | – |
| pup_compulsory | 28 | 1997 | 2024 | 216 / 2110 | {'no_data': 160, 'not_covered': 1734} |
| pup_compulsory_per_1000 | 15 | 2010 | 2024 | 216 / 2110 | – |
| rail_boardings_daily | 5 | 2018 | 2025 | 1923 / 2110 | {'not_covered': 187} |
| rail_boardings_weekday | 5 | 2018 | 2025 | 1923 / 2110 | {'not_covered': 187} |
| reach_car_aarau | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_basel | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_bellinzona | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_bern | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_biel | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_chur | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_fribourg | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_geneve | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_lausanne | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_lugano | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_luzern | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_nearest_hub | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_neuchatel | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_olten | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_schaffhausen | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_sion | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_stgallen | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_thun | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_winterthur | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_zuerich | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_car_zug | 1 | 2026 | 2026 | 2110 / 2110 | – |
| reach_pt_aarau | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_basel | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_bellinzona | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_bern | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_biel | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_chur | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_fribourg | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_geneve | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_lausanne | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_lugano | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_luzern | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_nearest_hub | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_neuchatel | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_olten | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_schaffhausen | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_sion | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_stgallen | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_thun | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_winterthur | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_zuerich | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| reach_pt_zug | 1 | 2026 | 2026 | 2107 / 2110 | {'no_data': 3} |
| sh_rate | 19 | 2007 | 2025 | 1835 / 2110 | {'no_data': 272, 'not_applicable': 3} |
| sh_recipients | 19 | 2007 | 2025 | 1838 / 2110 | {'no_data': 272} |
| share_age_0_19 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_age_65plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_age_80plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_divorced | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_foreign | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_married | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_women | 16 | 2010 | 2025 | 2110 / 2110 | – |
| tax_burden_married2c_100k | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_100k_cantonal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_100k_church | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_100k_federal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_100k_municipal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_200k | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_200k_cantonal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_200k_church | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_200k_federal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_married2c_200k_municipal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_pensioners_60k | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_pensioners_60k_cantonal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_pensioners_60k_church | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_pensioners_60k_federal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_pensioners_60k_municipal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_150k | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_150k_cantonal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_150k_church | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_150k_federal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_150k_municipal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_80k | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_80k_cantonal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_80k_church | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_80k_federal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_burden_single_80k_municipal | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_mult_cantonal_income | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_mult_cantonal_wealth | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_mult_municipal_income | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_mult_municipal_wealth | 17 | 2010 | 2026 | 2110 / 2110 | – |
| tax_np_federal_tax_chf | 21 | 2003 | 2023 | 2110 / 2110 | – |
| tax_np_federal_tax_per_capita | 14 | 2010 | 2023 | 2110 / 2110 | – |
| tax_np_federal_tax_per_taxpayer | 21 | 2003 | 2023 | 2110 / 2110 | – |
| tax_np_mean_net_income | 16 | 2008 | 2023 | 2110 / 2110 | – |
| tax_np_mean_taxable_income | 16 | 2008 | 2023 | 2110 / 2110 | – |
| tax_np_net_income_chf | 16 | 2008 | 2023 | 2110 / 2110 | – |
| tax_np_normal_taxable_100k_plus | 4 | 2020 | 2023 | 2062 / 2110 | {'suppressed': 48} |
| tax_np_normal_taxable_class_0 | 4 | 2020 | 2023 | 2067 / 2110 | {'suppressed': 43} |
| tax_np_normal_taxable_class_100_200k | 4 | 2020 | 2023 | 2082 / 2110 | {'suppressed': 28} |
| tax_np_normal_taxable_class_1_30k | 4 | 2020 | 2023 | 2108 / 2110 | {'suppressed': 2} |
| tax_np_normal_taxable_class_1m_plus | 4 | 2020 | 2023 | 210 / 2110 | {'suppressed': 1900} |
| tax_np_normal_taxable_class_200_500k | 4 | 2020 | 2023 | 1686 / 2110 | {'suppressed': 424} |
| tax_np_normal_taxable_class_30_40k | 4 | 2020 | 2023 | 2099 / 2110 | {'suppressed': 11} |
| tax_np_normal_taxable_class_40_50k | 4 | 2020 | 2023 | 2103 / 2110 | {'suppressed': 7} |
| tax_np_normal_taxable_class_500k_1m | 4 | 2020 | 2023 | 528 / 2110 | {'suppressed': 1582} |
| tax_np_normal_taxable_class_50_75k | 4 | 2020 | 2023 | 2108 / 2110 | {'suppressed': 2} |
| tax_np_normal_taxable_class_75_100k | 4 | 2020 | 2023 | 2097 / 2110 | {'suppressed': 13} |
| tax_np_share_no_federal_tax | 21 | 2003 | 2023 | 2109 / 2110 | – |
| tax_np_share_taxable_100k_plus | 4 | 2020 | 2023 | 2062 / 2110 | – |
| tax_np_taxable_income_chf | 16 | 2008 | 2023 | 2110 / 2110 | – |
| tax_np_taxpayers | 21 | 2003 | 2023 | 2110 / 2110 | – |
| tax_np_taxpayers_no_federal_tax | 21 | 2003 | 2023 | 2109 / 2110 | {'suppressed': 1} |
| tax_np_taxpayers_normal | 4 | 2020 | 2023 | 2110 / 2110 | – |
| udemo_active | 11 | 2013 | 2023 | 1944 / 2110 | {'suppressed': 166} |
| udemo_active_s2 | 11 | 2013 | 2023 | 1958 / 2110 | {'suppressed': 152} |
| udemo_active_s3 | 11 | 2013 | 2023 | 2081 / 2110 | {'suppressed': 29} |
| udemo_birth_rate | 11 | 2013 | 2023 | 770 / 2110 | – |
| udemo_births | 11 | 2013 | 2023 | 846 / 2110 | {'suppressed': 1264} |
| udemo_births_per_1000 | 11 | 2013 | 2023 | 846 / 2110 | – |
| udemo_births_s2 | 11 | 2013 | 2023 | 1181 / 2110 | {'suppressed': 929} |
| udemo_births_s3 | 11 | 2013 | 2023 | 1550 / 2110 | {'suppressed': 560} |
| udemo_closure_rate | 9 | 2013 | 2021 | 715 / 2110 | – |
| udemo_closures | 11 | 2013 | 2023 | 0 / 2110 | {'no_data': 2110} |
| udemo_jobs_active | 11 | 2013 | 2023 | 2044 / 2110 | {'suppressed': 66} |
| udemo_jobs_births | 11 | 2013 | 2023 | 1032 / 2110 | {'suppressed': 1078} |
| udemo_jobs_closures | 11 | 2013 | 2023 | 0 / 2110 | {'no_data': 2110} |
| udemo_jobs_per_enterprise | 11 | 2013 | 2023 | 1944 / 2110 | – |
| unemp_per_100_20_64 | 16 | 2010 | 2025 | 120 / 2110 | – |
| unemp_registered | 39 | 1990 | 2026-10 | 87 / 2110 | {'suppressed': 213, 'not_covered': 1530, 'no_data': 280} |
| vac_dwelling_stock | 16 | 2011 | 2026 | 2110 / 2110 | – |
| vac_dwellings | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_for_rent | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_for_sale | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_new | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_rate | 16 | 2011 | 2026 | 2110 / 2110 | – |
| vac_rate_bfs | 30 | 1997 | 2026 | 2110 / 2110 | – |
| vac_rate_rent | 16 | 2011 | 2026 | 2110 / 2110 | – |
| vac_rooms_1_2 | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_rooms_3 | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_rooms_4 | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_rooms_5plus | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_sfh | 32 | 1995 | 2026 | 2110 / 2110 | – |
| vac_share_new | 32 | 1995 | 2026 | 1916 / 2110 | – |
| vote_ballots | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | {'not_published': 5} |
| vote_eligible | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | {'not_published': 5} |
| vote_no | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | {'not_published': 5} |
| vote_turnout | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | – |
| vote_valid | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | {'not_published': 5} |
| vote_yes | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | {'not_published': 5} |
| vote_yes_share | 511 | 1960-05-29#1930 | 2026-06-14#6870 | 2105 / 2110 | – |
| vz_hh_collective | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_couple_children | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_couple_children_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_couple_no_children | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_couple_no_children_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_non_family | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_one_person | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_one_person_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_private | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_single_parent | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_single_parent_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_size_2 | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_size_3 | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_size_4 | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_size_5plus | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_size_5plus_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_total | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_hh_with_parents | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_de | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_de_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_en | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_en_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_fr | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_fr_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_it | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_it_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_other | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_other_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_rm | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_rm_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_lang_total | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_catholic | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_catholic_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_jewish | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_jewish_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_muslim | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_muslim_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_no_answer | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_none | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_none_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_orthodox | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_orthodox_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_other | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_other_christian | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_reformed | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_reformed_share | 4 | 1970 | 2000 | 2110 / 2110 | – |
| vz_rel_total | 4 | 1970 | 2000 | 2110 / 2110 | – |
| wiki_sitelinks | 1 | 2026 | 2026 | 2110 / 2110 | – |
| xb_commuters | 30 | 1996 | 2025 | 2110 / 2110 | – |
| xb_per_100_jobs | 14 | 2011 | 2024 | 2107 / 2110 | – |
| youth_dependency | 16 | 2010 | 2025 | 2110 / 2110 | – |
| zw_dwellings_total | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_primary_dwellings | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_second_home_share | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_second_homes | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_subject_to_law | 16 | 2019-03 | 2026-10 | 2110 / 2110 | – |

## E. Cross-source consistency

- STATPOP population vs. demographic balance stock at 31 Dec (2011+; 2010 is ESPOP-based in the balance): 31602 of 31650 within 0.1% — worst: [{'unit_id': '5399', 'period': '2019', 'value_a': 802.0, 'value_b': 640.0}, {'unit_id': '5399', 'period': '2016', 'value_a': 819.0, 'value_b': 655.0}, {'unit_id': '5399', 'period': '2015', 'value_a': 830.0, 'value_b': 665.0}]
- Persons in private households vs. STATPOP population (institutions explain the gap): 29386 of 29540 within 10.0% — worst: [{'unit_id': '5407', 'period': '2012', 'value_a': 2423.0, 'value_b': 3988.0}, {'unit_id': '5407', 'period': '2015', 'value_a': 2674.0, 'value_b': 4224.0}, {'unit_id': '5407', 'period': '2013', 'value_a': 2594.0, 'value_b': 4096.0}]
- GWS dwellings of year t vs. dwelling stock in the vacancy count of year t+1 (BFS's own denominator): 33760 of 33760 within 0.1% — worst: [{'unit_id': '1', 'period': '2010', 'value_a': 856.0, 'value_b': 856.0}, {'unit_id': '1', 'period': '2011', 'value_a': 856.0, 'value_b': 856.0}, {'unit_id': '1', 'period': '2012', 'value_a': 870.0, 'value_b': 870.0}]
- Land area (swissBOUNDARIES3D 2026, without lakes) vs. land-use statistics total area 2013/18: 2104 of 2110 within 5.0% — worst: [{'unit_id': '4651', 'period': '2026', 'value_a': 31.0, 'value_b': 35.0}, {'unit_id': '5187', 'period': '2026', 'value_a': 71.0, 'value_b': 66.0}, {'unit_id': '5206', 'period': '2026', 'value_a': 89.0, 'value_b': 83.0}]
