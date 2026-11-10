# Data quality report

Generated 2026-11-10T01:01 · reference state 2026-01-01 · regenerate with `make quality`. Plan: [`validation_plan.md`](validation_plan.md).

Metrics: 721 defined (517 base, 204 derived) · rows: 30,794,586

## A. Additivity — municipalities vs. published district/canton/national values

Summary: 633 metric×level comparisons, 517 pass, 116 with failures.

| Source | Level | Metric | Compared | Exact | Explained (transfers / unallocated) | Within 0.5% | Documented difference | Fail | Max rel. residual |
|---|---|---|---|---|---|---|---|---|---|
| bfs_votes_gemeinde | bezirk | vote_valid | 70528 | 67883 | 0 | 776 | 0 | **24331** | 1383.484% |
| bfs_votes_gemeinde | bezirk | vote_yes | 70528 | 67883 | 0 | 776 | 0 | **24331** | 1484.728% |
| bfs_votes_gemeinde | bezirk | vote_no | 70528 | 67883 | 0 | 761 | 0 | **24328** | 1854.217% |
| bfs_votes_gemeinde | bezirk | vote_eligible | 69993 | 67662 | 0 | 776 | 0 | **24115** | 1249.757% |
| bfs_votes_gemeinde | bezirk | vote_ballots | 69974 | 67643 | 0 | 776 | 0 | **24111** | 1364.580% |
| bfs_votes_gemeinde | kanton | vote_valid | 13180 | 8372 | 476 | 601 | 0 | **2826** | 12.884% |
| bfs_votes_gemeinde | kanton | vote_ballots | 13180 | 8372 | 476 | 601 | 0 | **2820** | 12.926% |
| bfs_votes_gemeinde | kanton | vote_yes | 13180 | 8456 | 476 | 527 | 0 | **2816** | 16.225% |
| bfs_votes_gemeinde | kanton | vote_no | 13180 | 8520 | 476 | 535 | 0 | **2744** | 14.944% |
| bfs_votes_gemeinde | kanton | vote_eligible | 13180 | 8992 | 476 | 165 | 0 | **2637** | 12.711% |
| bfs_agriculture | bezirk | agr_area_permanent_crops_ha | 4004 | 1985 | 4 | 383 | 0 ¹ | **1638** | 100.000% |
| bfs_construction | kanton | con_exp_public | 806 | 0 | 0 | 0 | 0 | **806** | 93.856% |
| bfs_construction | kanton | con_exp_total | 806 | 0 | 0 | 0 | 0 | **806** | 82.622% |
| bfs_construction | kanton | con_inv_total | 806 | 0 | 0 | 1 | 0 | **805** | 83.583% |
| bfs_construction | kanton | con_inv_renovation | 806 | 0 | 0 | 8 | 0 | **798** | 71.434% |
| bfs_construction | kanton | con_exp_maintenance | 806 | 9 | 0 | 0 | 0 | **797** | 98.172% |
| bfs_construction | kanton | con_inv_new | 806 | 1 | 0 | 16 | 0 | **789** | 87.643% |
| bfs_nrw | bezirk | nrw_ballots_valid | 1993 | 1908 | 4 | 22 | 0 | **670** | 855.515% |
| bfs_nrw | bezirk | nrw_eligible | 1993 | 1908 | 4 | 22 | 0 | **670** | 816.336% |
| bfs_nrw | bezirk | nrw_voters | 1993 | 1908 | 4 | 22 | 0 | **670** | 855.693% |
| bfs_nrw | bezirk | nrw_ballots_invalid | 1993 | 1908 | 4 | 1 | 0 | **660** | 4800.000% |
| bfs_nrw | bezirk | nrw_ballots_blank | 1993 | 1908 | 4 | 1 | 0 | **655** | 1350.000% |
| bfs_nrw | bezirk | nrw_ballots_unchanged | 1851 | 1776 | 4 | 20 | 0 | **605** | 865.327% |
| bfs_nrw | bezirk | nrw_ballots_changed | 1770 | 1695 | 4 | 20 | 0 | **599** | 667.942% |
| bfs_agriculture | bezirk | agr_area_arable_ha | 4004 | 1824 | 8 | 1642 | 0 ¹ | **530** | 100.000% |
| bfs_construction | kanton | con_exp_private | 806 | 194 | 15 | 261 | 0 | **336** | 71.494% |
| bfs_agriculture | bezirk | agr_area_organic_ha | 3575 | 1813 | 0 | 1485 | 0 ¹ | **279** | 50.000% |
| bfs_agriculture | kanton | agr_area_permanent_crops_ha | 728 | 227 | 6 | 263 | 0 ¹ | **236** | 100.000% |
| bfs_vehicles | kanton | mfz_cars_diesel | 416 | 192 | 16 | 111 | 0 | **97** | 25.818% |
| bfs_agriculture | kanton | agr_area_arable_ha | 728 | 215 | 4 | 426 | 0 ¹ | **83** | 100.000% |
| bfs_arealstatistik | kanton | area_water_ha | 114 | 32 | 0 | 0 | 0 | **82** | 96.176% |
| bfs_arealstatistik | kanton | area_unproductive_ha | 114 | 32 | 0 | 4 | 0 | **78** | 93.342% |
| bfs_vehicles | kanton | mfz_cars | 416 | 192 | 16 | 130 | 0 | **78** | 32.140% |
| bfs_nrw | kanton | nrw_ballots_unchanged | 333 | 222 | 12 | 8 | 0 | **75** | 8.802% |
| bfs_nrw | kanton | nrw_ballots_valid | 357 | 233 | 13 | 16 | 0 | **75** | 9.744% |
| bfs_nrw | kanton | nrw_voters | 357 | 233 | 13 | 16 | 0 | **75** | 9.715% |
| bfs_arealstatistik | kanton | area_total_ha | 114 | 32 | 0 | 8 | 0 | **74** | 13.265% |
| bfs_vehicles | kanton | mfz_cars_hev | 416 | 215 | 16 | 112 | 0 | **73** | 52.334% |
| bfs_nrw | kanton | nrw_fw_total | 357 | 233 | 13 | 16 | 0 | **71** | 9.742% |
| bfs_vehicles | kanton | mfz_cars_bev | 416 | 243 | 11 | 91 | 0 | **71** | 45.882% |
| bfs_nrw | kanton | nrw_ballots_invalid | 357 | 248 | 14 | 5 | 0 | **70** | 16.923% |
| bfs_nrw | kanton | nrw_eligible | 357 | 254 | 13 | 1 | 0 | **69** | 11.926% |
| bfs_vehicles | kanton | mfz_cars_phev | 416 | 259 | 4 | 86 | 0 | **67** | 65.933% |
| bfs_nrw | kanton | nrw_ballots_blank | 357 | 251 | 13 | 10 | 0 | **63** | 23.958% |
| bfs_nrw | kanton | nrw_fw_other | 277 | 188 | 2 | 8 | 0 | **63** | 22.449% |
| bfs_vehicles | kanton | mfz_newreg_cars | 416 | 216 | 16 | 121 | 0 | **63** | 13.733% |
| bfs_nrw | kanton | nrw_fw_sp | 303 | 188 | 11 | 19 | 0 | **62** | 7.576% |
| bfs_vehicles | kanton | mfz_cars_petrol | 416 | 192 | 16 | 149 | 0 | **59** | 29.058% |
| bfs_nrw | kanton | nrw_fw_cvp | 279 | 165 | 12 | 20 | 0 | **58** | 8.805% |
| bfs_nrw | kanton | nrw_fw_fdp | 311 | 199 | 12 | 18 | 0 | **58** | 9.875% |
| bfs_nrw | kanton | nrw_fw_svp | 249 | 143 | 13 | 15 | 0 | **58** | 8.193% |
| bfs_nrw | kanton | nrw_ballots_changed | 264 | 166 | 12 | 16 | 0 | **54** | 12.657% |
| bfs_nrw | kanton | nrw_fw_gruene | 179 | 109 | 6 | 0 | 0 | **54** | 9.644% |
| bfs_vehicles | kanton | mfz_newreg_bev | 416 | 301 | 3 | 58 | 0 | **54** | 17.297% |
| bfs_nrw | kanton | nrw_fw_evp | 131 | 66 | 5 | 1 | 0 | **42** | 14.938% |
| bfs_nrw | kanton | nrw_fw_glp | 72 | 29 | 1 | 2 | 0 | **37** | 8.339% |
| bfs_vehicles | kanton | mfz_cars_private | 260 | 48 | 4 | 172 | 0 | **36** | 18.293% |
| bfs_nrw | kanton | nrw_fw_edu | 95 | 51 | 1 | 0 | 0 | **33** | 12.236% |
| bfs_agriculture | kanton | agr_area_organic_ha | 650 | 177 | 4 | 448 | 0 ¹ | **24** | 3.333% |
| bfs_nrw | kanton | nrw_fw_bdp | 44 | 16 | 0 | 2 | 0 | **24** | 12.170% |
| bfs_nrw | kanton | nrw_fw_sd | 124 | 72 | 5 | 3 | 0 | **24** | 11.562% |
| bfs_nrw | kanton | nrw_fw_pda | 83 | 51 | 3 | 5 | 0 | **19** | 7.384% |
| kt_crime | kanton | crime_stgb_offences | 17 | 0 | 0 | 0 | 0 | **17** | 6.330% |
| kt_crime | kanton | crime_stgb_property | 17 | 0 | 0 | 0 | 0 | **17** | 5.897% |
| bfs_nrw | kanton | nrw_fw_csp | 29 | 14 | 0 | 0 | 0 | **15** | 5.229% |
| bfs_nrw | kanton | nrw_fw_sol | 21 | 7 | 0 | 0 | 0 | **14** | 8.188% |
| bfs_agriculture | bezirk | agr_area_grassland_ha | 4004 | 1670 | 7 | 2314 | 0 ¹ | **13** | 1.010% |
| bfs_nrw | kanton | nrw_fw_lps | 53 | 37 | 0 | 3 | 0 | **12** | 16.646% |
| bfs_nrw | kanton | nrw_fw_mitte | 25 | 11 | 1 | 1 | 0 | **11** | 6.410% |
| kt_crime | kanton | crime_stgb_violent | 17 | 0 | 0 | 6 | 0 | **11** | 1.368% |
| bfs_arealstatistik | bezirk | area_total_ha | 632 | 614 | 0 | 9 | 0 | **9** | 1.777% |
| bfs_arealstatistik | bezirk | area_water_ha | 632 | 623 | 0 | 0 | 0 | **9** | 0.590% |
| bfs_arealstatistik | bezirk | area_wooded_ha | 632 | 619 | 0 | 4 | 0 | **9** | 8.642% |
| bfs_census_1970_2000 | kanton | vz_hh_couple_children | 104 | 92 | 4 | 0 | 0 | **8** | 3.754% |
| bfs_census_1970_2000 | kanton | vz_hh_couple_no_children | 104 | 92 | 4 | 0 | 0 | **8** | 4.291% |
| bfs_census_1970_2000 | kanton | vz_hh_one_person | 104 | 93 | 4 | 0 | 0 | **8** | 4.019% |
| bfs_census_1970_2000 | kanton | vz_hh_private | 104 | 92 | 4 | 0 | 0 | **8** | 3.820% |
| bfs_census_1970_2000 | kanton | vz_hh_single_parent | 104 | 94 | 4 | 0 | 0 | **8** | 3.208% |
| bfs_census_1970_2000 | kanton | vz_hh_size_2 | 104 | 93 | 4 | 0 | 0 | **8** | 4.166% |
| bfs_census_1970_2000 | kanton | vz_hh_size_3 | 104 | 93 | 4 | 0 | 0 | **8** | 4.196% |
| bfs_census_1970_2000 | kanton | vz_hh_size_4 | 104 | 92 | 4 | 0 | 0 | **8** | 3.886% |
| bfs_census_1970_2000 | kanton | vz_hh_size_5plus | 104 | 92 | 4 | 0 | 0 | **8** | 3.226% |
| bfs_census_1970_2000 | kanton | vz_hh_total | 104 | 92 | 4 | 0 | 0 | **8** | 3.815% |
| bfs_census_1970_2000 | kanton | vz_lang_de | 104 | 92 | 4 | 0 | 0 | **8** | 9.000% |
| bfs_census_1970_2000 | kanton | vz_lang_en | 104 | 96 | 4 | 0 | 0 | **8** | 3.400% |
| bfs_census_1970_2000 | kanton | vz_lang_fr | 104 | 93 | 4 | 0 | 0 | **8** | 1.086% |
| bfs_census_1970_2000 | kanton | vz_lang_it | 104 | 96 | 4 | 0 | 0 | **8** | 5.775% |
| bfs_census_1970_2000 | kanton | vz_lang_other | 104 | 95 | 4 | 0 | 0 | **8** | 5.571% |
| bfs_census_1970_2000 | kanton | vz_lang_total | 104 | 92 | 4 | 0 | 0 | **8** | 3.473% |
| bfs_census_1970_2000 | kanton | vz_rel_catholic | 104 | 92 | 4 | 0 | 0 | **8** | 1.297% |
| bfs_census_1970_2000 | kanton | vz_rel_reformed | 104 | 92 | 4 | 0 | 0 | **8** | 18.730% |
| bfs_census_1970_2000 | kanton | vz_rel_total | 104 | 92 | 4 | 0 | 0 | **8** | 3.473% |
| bfs_census_1970_2000 | kanton | vz_hh_collective | 104 | 95 | 4 | 1 | 0 | **7** | 3.320% |
| bfs_census_1970_2000 | kanton | vz_hh_non_family | 104 | 96 | 4 | 1 | 0 | **7** | 3.284% |
| bfs_census_1970_2000 | kanton | vz_hh_with_parents | 104 | 95 | 4 | 1 | 0 | **7** | 3.931% |
| bfs_census_1970_2000 | kanton | vz_lang_rm | 104 | 96 | 4 | 1 | 0 | **7** | 6.838% |
| bfs_census_1970_2000 | kanton | vz_rel_none | 104 | 95 | 4 | 1 | 0 | **7** | 4.706% |
| bfs_construction | kanton | con_inv_residential | 806 | 553 | 35 | 211 | 0 | **7** | 3.813% |
| bfs_census_1970_2000 | kanton | vz_rel_jewish | 104 | 96 | 4 | 2 | 0 | **6** | 6.780% |
| bfs_census_1970_2000 | kanton | vz_rel_muslim | 104 | 96 | 4 | 2 | 0 | **6** | 3.884% |
| bfs_census_1970_2000 | kanton | vz_rel_orthodox | 104 | 96 | 4 | 2 | 0 | **6** | 5.660% |
| bfs_census_1970_2000 | kanton | vz_rel_other_christian | 104 | 92 | 4 | 2 | 0 | **6** | 17.318% |
| bfs_nrw | kanton | nrw_fw_fga | 46 | 33 | 2 | 0 | 0 | **6** | 3.552% |
| bfs_nrw | kanton | nrw_fw_mcr | 6 | 0 | 0 | 0 | 0 | **6** | 3.443% |
| bfs_arealstatistik | kanton | area_wooded_ha | 114 | 62 | 0 | 47 | 0 | **5** | 0.600% |
| bfs_census_1970_2000 | kanton | vz_rel_no_answer | 104 | 94 | 4 | 3 | 0 | **5** | 3.436% |
| bfs_census_1970_2000 | kanton | vz_rel_other | 104 | 96 | 4 | 3 | 0 | **5** | 2.326% |
| bfs_arealstatistik | bezirk | area_agriculture_ha | 632 | 624 | 0 | 4 | 0 | **4** | 0.649% |
| bfs_arealstatistik | bezirk | area_unproductive_ha | 632 | 619 | 0 | 9 | 0 | **4** | 2.764% |
| bfs_arealstatistik | kanton | area_industrial_ha | 114 | 105 | 0 | 5 | 0 | **4** | 1.075% |
| kt_unemployment | kanton | unemp_registered | 70 | 12 | 0 | 40 | 0 | **4** | 1.189% |
| bfs_social_assistance | kanton | sh_recipients | 494 | 11 | 0 | 28 | 123 ¹ | **3** | 14.860% |
| bfs_nrw | kanton | nrw_fw_fps | 48 | 36 | 2 | 0 | 0 | **1** | 1.262% |
| bfs_nrw | kanton | nrw_fw_ldu | 68 | 44 | 5 | 2 | 0 | **1** | 8.128% |
| bfs_nrw | kanton | nrw_fw_psa | 6 | 2 | 0 | 3 | 0 | **1** | 0.798% |
| bfs_nrw | kanton | nrw_fw_rep | 24 | 12 | 0 | 2 | 0 | **1** | 11.989% |
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
| bfs_agriculture | bezirk | agr_area_ha | 4004 | 1636 | 3 | 2365 | 0 ¹ | 0 | 0.249% |
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
| bfs_agriculture | kanton | agr_area_grassland_ha | 728 | 177 | 10 | 541 | 0 ¹ | 0 | 0.498% |
| bfs_agriculture | kanton | agr_area_ha | 728 | 183 | 9 | 536 | 0 ¹ | 0 | 0.241% |
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
| bfs_agriculture | schweiz | agr_area_arable_ha | 28 | 0 | 0 | 28 | 0 ¹ | 0 | 0.017% |
| bfs_agriculture | schweiz | agr_area_grassland_ha | 28 | 0 | 0 | 28 | 0 ¹ | 0 | 0.005% |
| bfs_agriculture | schweiz | agr_area_ha | 28 | 0 | 0 | 28 | 0 ¹ | 0 | 0.002% |
| bfs_agriculture | schweiz | agr_area_organic_ha | 25 | 2 | 0 | 23 | 0 ¹ | 0 | 0.015% |
| bfs_agriculture | schweiz | agr_area_permanent_crops_ha | 28 | 1 | 0 | 27 | 0 ¹ | 0 | 0.232% |
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
| bfs_arealstatistik | kanton | area_agriculture_ha | 114 | 106 | 0 | 8 | 0 | 0 | 0.058% |
| bfs_arealstatistik | kanton | area_building_ha | 114 | 76 | 0 | 38 | 0 | 0 | 0.385% |
| bfs_arealstatistik | kanton | area_glacier_ha | 114 | 114 | 0 | 0 | 0 | 0 | 0.000% |
| bfs_arealstatistik | kanton | area_sealed_ha | 114 | 57 | 0 | 57 | 0 | 0 | 0.447% |
| bfs_arealstatistik | kanton | area_settlement_base_ha | 88 | 45 | 0 | 43 | 0 | 0 | 0.345% |
| bfs_arealstatistik | kanton | area_settlement_ha | 114 | 46 | 0 | 68 | 0 | 0 | 0.345% |
| bfs_arealstatistik | kanton | area_transport_ha | 114 | 99 | 0 | 15 | 0 | 0 | 0.067% |
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
| bfs_nrw | kanton | nrw_fw_lega | 9 | 9 | 0 | 0 | 0 | 0 | 0.006% |
| bfs_nrw | kanton | nrw_fw_poch | 30 | 19 | 3 | 2 | 0 | 0 | 0.045% |
| bfs_nrw | kanton | nrw_fw_sep | 7 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_ballots_blank | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_ballots_changed | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_ballots_invalid | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_ballots_unchanged | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_ballots_valid | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_eligible | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_bdp | 3 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_csp | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_cvp | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_edu | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_evp | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_fdp | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_fga | 12 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_fps | 6 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_glp | 5 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_gruene | 13 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_ldu | 8 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_lega | 9 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_lps | 10 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_mcr | 5 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_mitte | 1 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_other | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_pda | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_poch | 6 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_psa | 6 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_rep | 5 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_sd | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_sep | 7 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_sol | 8 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_sp | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_svp | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_fw_total | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
| bfs_nrw | schweiz | nrw_voters | 14 | 0 | 0 | 0 | 0 | 0 | nan% |
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
| bfs_vehicles | schweiz | mfz_cars | 16 | 0 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_bev | 16 | 8 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_diesel | 16 | 7 | 9 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_hev | 16 | 8 | 7 | 1 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_petrol | 16 | 0 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_phev | 16 | 8 | 8 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_cars_private | 10 | 0 | 10 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | schweiz | mfz_newreg_bev | 16 | 8 | 7 | 1 | 0 | 0 | 0.197% |
| bfs_vehicles | schweiz | mfz_newreg_cars | 16 | 8 | 7 | 1 | 0 | 0 | 0.001% |
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
| kt_finance | kanton | fin_tax_revenue_chf | 30 | 3 | 0 | 27 | 0 | 0 | 0.026% |
| kt_pupils | kanton | pup_compulsory | 23 | 22 | 0 | 0 | 0 | 0 | 0.000% |

¹ Documented differences (from metrics.yaml `additivity_note`):

- agr_area_arable_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_grassland_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_organic_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- agr_area_permanent_crops_ha: BFS rounds every cell of px-x-0702000000_104 to whole hectares independently at each level (all 237,000 area values are integers). Σ rounded municipalities can therefore differ from the rounded district/canton value by up to 0.5 ha per municipality: every non-transfer residual is ≤ 0.5 ha × municipalities (e.g. district 248 arable land 2000: published 1 ha, municipalities 0 ha). Relative differences are large only for tiny totals (permanent crops, arable land in alpine districts).
- sh_recipients: BFS (Map Explorer, indicator description): "Wer im Verlaufe eines Jahres den Wohnort wechselt und sowohl am alten als auch am neuen Ort Sozialhilfe bezieht, wird zweimal ... gezählt. Bei kantonalen Auswertungen wird dieselbe Unterstützungseinheit nur einmal gezählt ... Demzufolge stimmen die Summen ... aller Gemeinden nicht mit dem Kantonstotal überein." Observed for all canton-years with a counted (integer) canton total: municipal sum between +0.0 % and +6.04 % (NW 2012), never below. Non-integer canton totals (GL 2007, AR 2014/15, 2024–2025) are BFS estimates (precision modelled) and are not expected to add up.

Worst unexplained differences:

- bfs_agriculture / bezirk / agr_area_arable_ha: [{'unit_id': '248', 'period': '2000', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}, {'unit_id': '248', 'period': '1998', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}, {'unit_id': '248', 'period': '1997', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}]
- bfs_agriculture / bezirk / agr_area_grassland_ha: [{'unit_id': '2229', 'period': '2022', 'value_pub': 99.0, 'value_agg': 100.0, 'explained': 0.0}, {'unit_id': '2229', 'period': '2023', 'value_pub': 105.0, 'value_agg': 104.0, 'explained': 0.0}, {'unit_id': '2229', 'period': '2021', 'value_pub': 112.0, 'value_agg': 111.0, 'explained': 0.0}]
- bfs_agriculture / bezirk / agr_area_organic_ha: [{'unit_id': '2311', 'period': '1990', 'value_pub': 2.0, 'value_agg': 1.0, 'explained': 0.0}, {'unit_id': '2229', 'period': '2024', 'value_pub': 10.0, 'value_agg': 11.0, 'explained': 0.0}, {'unit_id': '2229', 'period': '2025', 'value_pub': 10.0, 'value_agg': 11.0, 'explained': 0.0}]
- bfs_agriculture / bezirk / agr_area_permanent_crops_ha: [{'unit_id': '316', 'period': '1975', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}, {'unit_id': '316', 'period': '1980', 'value_pub': 1.0, 'value_agg': 2.0, 'explained': 0.0}, {'unit_id': '316', 'period': '1985', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}]
- bfs_agriculture / kanton / agr_area_arable_ha: [{'unit_id': 'AI', 'period': '2000', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2002', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1985', 'value_pub': 4.0, 'value_agg': 3.0, 'explained': 0.0}]
- bfs_agriculture / kanton / agr_area_organic_ha: [{'unit_id': 'NW', 'period': '1990', 'value_pub': 30.0, 'value_agg': 29.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2004', 'value_pub': 67.0, 'value_agg': 66.0, 'explained': 0.0}, {'unit_id': 'SH', 'period': '1990', 'value_pub': 71.0, 'value_agg': 72.0, 'explained': 0.0}]
- bfs_agriculture / kanton / agr_area_permanent_crops_ha: [{'unit_id': 'UR', 'period': '2000', 'value_pub': 1.0, 'value_agg': 0.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1990', 'value_pub': 2.0, 'value_agg': 1.0, 'explained': 0.0}, {'unit_id': 'UR', 'period': '2002', 'value_pub': 2.0, 'value_agg': 1.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_agriculture_ha: [{'unit_id': '2101', 'period': '2013/18', 'value_pub': 2772.0, 'value_agg': 2754.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1979/85', 'value_pub': 3713.0, 'value_agg': 3690.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1992/97', 'value_pub': 3097.0, 'value_agg': 3078.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_total_ha: [{'unit_id': '1005', 'period': '1979/85', 'value_pub': 14573.0, 'value_agg': 14314.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '2013/18', 'value_pub': 14573.0, 'value_agg': 14314.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '2004/09', 'value_pub': 14573.0, 'value_agg': 14314.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_unproductive_ha: [{'unit_id': '2101', 'period': '2004/09', 'value_pub': 1990.0, 'value_agg': 1935.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1992/97', 'value_pub': 2171.0, 'value_agg': 2112.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1979/85', 'value_pub': 2358.0, 'value_agg': 2299.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_water_ha: [{'unit_id': '2101', 'period': '2013/18', 'value_pub': 339.0, 'value_agg': 337.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '2004/09', 'value_pub': 343.0, 'value_agg': 341.0, 'explained': 0.0}, {'unit_id': '2101', 'period': '1992/97', 'value_pub': 350.0, 'value_agg': 348.0, 'explained': 0.0}]
- bfs_arealstatistik / bezirk / area_wooded_ha: [{'unit_id': '1005', 'period': '1979/85', 'value_pub': 2997.0, 'value_agg': 2738.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '1992/97', 'value_pub': 3021.0, 'value_agg': 2763.0, 'explained': 0.0}, {'unit_id': '1005', 'period': '2020/25', 'value_pub': 3051.0, 'value_agg': 2793.0, 'explained': 0.0}]
- bfs_arealstatistik / kanton / area_industrial_ha: [{'unit_id': 'NW', 'period': '1979/85', 'value_pub': 93.0, 'value_agg': 92.0, 'explained': 0.0}, {'unit_id': 'NW', 'period': '1992/97', 'value_pub': 104.0, 'value_agg': 103.0, 'explained': 0.0}, {'unit_id': 'NW', 'period': '2004/09', 'value_pub': 114.0, 'value_agg': 113.0, 'explained': 0.0}]
- bfs_arealstatistik / kanton / area_total_ha: [{'unit_id': 'ZG', 'period': '2004/09', 'value_pub': 23874.0, 'value_agg': 20707.0, 'explained': 0.0}, {'unit_id': 'ZG', 'period': '1992/97', 'value_pub': 23874.0, 'value_agg': 20707.0, 'explained': 0.0}, {'unit_id': 'ZG', 'period': '2013/18', 'value_pub': 23874.0, 'value_agg': 20707.0, 'explained': 0.0}]
- bfs_arealstatistik / kanton / area_unproductive_ha: [{'unit_id': 'NE', 'period': '2020/25', 'value_pub': 9087.0, 'value_agg': 605.0, 'explained': 0.0}, {'unit_id': 'NE', 'period': '2013/18', 'value_pub': 9106.0, 'value_agg': 625.0, 'explained': 0.0}, {'unit_id': 'NE', 'period': '1992/97', 'value_pub': 9160.0, 'value_agg': 679.0, 'explained': 0.0}]
- bfs_arealstatistik / kanton / area_water_ha: [{'unit_id': 'VD', 'period': '1992/97', 'value_pub': 40425.0, 'value_agg': 1546.0, 'explained': 0.0}, {'unit_id': 'VD', 'period': '1979/85', 'value_pub': 40442.0, 'value_agg': 1559.0, 'explained': 0.0}, {'unit_id': 'VD', 'period': '2004/09', 'value_pub': 40445.0, 'value_agg': 1567.0, 'explained': 0.0}]
- bfs_arealstatistik / kanton / area_wooded_ha: [{'unit_id': 'FR', 'period': '1979/85', 'value_pub': 44022.0, 'value_agg': 43758.0, 'explained': 0.0}, {'unit_id': 'FR', 'period': '1992/97', 'value_pub': 44844.0, 'value_agg': 44578.0, 'explained': 0.0}, {'unit_id': 'FR', 'period': '2004/09', 'value_pub': 45137.0, 'value_agg': 44874.0, 'explained': 0.0}]
- bfs_census_1970_2000 / kanton / vz_hh_collective: [{'unit_id': 'FR', 'period': '2000', 'value_pub': 2470.0, 'value_agg': 2472.0, 'explained': 84.0}, {'unit_id': 'FR', 'period': '1970', 'value_pub': 329.0, 'value_agg': 329.0, 'explained': 10.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 300.0, 'value_agg': 300.0, 'explained': 7.0}]
- bfs_census_1970_2000 / kanton / vz_hh_couple_children: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 26402.0, 'value_agg': 26409.0, 'explained': 998.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 28327.0, 'value_agg': 28335.0, 'explained': 975.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 33428.0, 'value_agg': 33435.0, 'explained': 1033.0}]
- bfs_census_1970_2000 / kanton / vz_hh_couple_no_children: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 10115.0, 'value_agg': 10116.0, 'explained': 435.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 13697.0, 'value_agg': 13698.0, 'explained': 583.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 24168.0, 'value_agg': 24173.0, 'explained': 962.0}]
- bfs_census_1970_2000 / kanton / vz_hh_non_family: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 2862.0, 'value_agg': 2862.0, 'explained': 94.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 2247.0, 'value_agg': 2247.0, 'explained': 71.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 1985.0, 'value_agg': 1985.0, 'explained': 53.0}]
- bfs_census_1970_2000 / kanton / vz_hh_one_person: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 7540.0, 'value_agg': 7540.0, 'explained': 303.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 20112.0, 'value_agg': 20114.0, 'explained': 776.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 13403.0, 'value_agg': 13407.0, 'explained': 517.0}]
- bfs_census_1970_2000 / kanton / vz_hh_private: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 50155.0, 'value_agg': 50165.0, 'explained': 1926.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 61359.0, 'value_agg': 61374.0, 'explained': 2265.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 94093.0, 'value_agg': 94110.0, 'explained': 3263.0}]
- bfs_census_1970_2000 / kanton / vz_hh_single_parent: [{'unit_id': 'FR', 'period': '1980', 'value_pub': 3335.0, 'value_agg': 3337.0, 'explained': 109.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 4149.0, 'value_agg': 4149.0, 'explained': 129.0}, {'unit_id': 'FR', 'period': '1970', 'value_pub': 2919.0, 'value_agg': 2921.0, 'explained': 89.0}]
- bfs_census_1970_2000 / kanton / vz_hh_size_2: [{'unit_id': 'FR', 'period': '1980', 'value_pub': 16250.0, 'value_agg': 16252.0, 'explained': 679.0}, {'unit_id': 'FR', 'period': '1970', 'value_pub': 11825.0, 'value_agg': 11825.0, 'explained': 468.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 28176.0, 'value_agg': 28180.0, 'explained': 1083.0}]
- bfs_census_1970_2000 / kanton / vz_hh_size_3: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 9604.0, 'value_agg': 9606.0, 'explained': 405.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 10608.0, 'value_agg': 10609.0, 'explained': 372.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 14131.0, 'value_agg': 14135.0, 'explained': 439.0}]
- bfs_census_1970_2000 / kanton / vz_hh_size_4: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 8879.0, 'value_agg': 8881.0, 'explained': 347.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 11703.0, 'value_agg': 11704.0, 'explained': 440.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 15298.0, 'value_agg': 15299.0, 'explained': 488.0}]
- bfs_census_1970_2000 / kanton / vz_hh_size_5plus: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 12307.0, 'value_agg': 12313.0, 'explained': 403.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 7922.0, 'value_agg': 7925.0, 'explained': 221.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 9395.0, 'value_agg': 9402.0, 'explained': 257.0}]
- bfs_census_1970_2000 / kanton / vz_hh_total: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 50484.0, 'value_agg': 50494.0, 'explained': 1936.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 61659.0, 'value_agg': 61674.0, 'explained': 2272.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 96563.0, 'value_agg': 96582.0, 'explained': 3347.0}]
- bfs_census_1970_2000 / kanton / vz_hh_with_parents: [{'unit_id': 'FR', 'period': '2000', 'value_pub': 865.0, 'value_agg': 865.0, 'explained': 34.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 350.0, 'value_agg': 350.0, 'explained': 10.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 388.0, 'value_agg': 389.0, 'explained': 11.0}]
- bfs_census_1970_2000 / kanton / vz_lang_de: [{'unit_id': 'FR', 'period': '2000', 'value_pub': 70611.0, 'value_agg': 70658.0, 'explained': 6402.0}, {'unit_id': 'FR', 'period': '1970', 'value_pub': 58448.0, 'value_agg': 58497.0, 'explained': 4985.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 59824.0, 'value_agg': 59873.0, 'explained': 5027.0}]
- bfs_census_1970_2000 / kanton / vz_lang_en: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 500.0, 'value_agg': 500.0, 'explained': 17.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 1155.0, 'value_agg': 1155.0, 'explained': 36.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 567.0, 'value_agg': 567.0, 'explained': 17.0}]
- bfs_census_1970_2000 / kanton / vz_lang_fr: [{'unit_id': 'BE', 'period': '2000', 'value_pub': 72646.0, 'value_agg': 65983.0, 'explained': -7452.0}, {'unit_id': 'BE', 'period': '1990', 'value_pub': 74022.0, 'value_agg': 67511.0, 'explained': -7241.0}, {'unit_id': 'BE', 'period': '1970', 'value_pub': 78750.0, 'value_agg': 72364.0, 'explained': -7079.0}]
- bfs_census_1970_2000 / kanton / vz_lang_it: [{'unit_id': 'FR', 'period': '1980', 'value_pub': 4866.0, 'value_agg': 4866.0, 'explained': 281.0}, {'unit_id': 'FR', 'period': '1970', 'value_pub': 7173.0, 'value_agg': 7173.0, 'explained': 311.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 3970.0, 'value_agg': 3970.0, 'explained': 170.0}]
- bfs_census_1970_2000 / kanton / vz_lang_other: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 5439.0, 'value_agg': 5439.0, 'explained': 303.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 6161.0, 'value_agg': 6161.0, 'explained': 290.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 13943.0, 'value_agg': 13944.0, 'explained': 501.0}]
- bfs_census_1970_2000 / kanton / vz_lang_rm: [{'unit_id': 'FR', 'period': '1990', 'value_pub': 117.0, 'value_agg': 117.0, 'explained': 8.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 131.0, 'value_agg': 131.0, 'explained': 8.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 131.0, 'value_agg': 131.0, 'explained': 6.0}]
- bfs_census_1970_2000 / kanton / vz_lang_total: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 180309.0, 'value_agg': 180358.0, 'explained': 6312.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 185246.0, 'value_agg': 185300.0, 'explained': 6278.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 241706.0, 'value_agg': 241759.0, 'explained': 7859.0}]
- bfs_census_1970_2000 / kanton / vz_rel_catholic: [{'unit_id': 'BE', 'period': '2000', 'value_pub': 153357.0, 'value_agg': 149672.0, 'explained': -5674.0}, {'unit_id': 'BE', 'period': '1990', 'value_pub': 161802.0, 'value_agg': 157783.0, 'explained': -5913.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 170069.0, 'value_agg': 170070.0, 'explained': 1990.0}]
- bfs_census_1970_2000 / kanton / vz_rel_jewish: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 177.0, 'value_agg': 177.0, 'explained': 12.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 142.0, 'value_agg': 142.0, 'explained': 7.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 145.0, 'value_agg': 145.0, 'explained': 3.0}]
- bfs_census_1970_2000 / kanton / vz_rel_muslim: [{'unit_id': 'FR', 'period': '2000', 'value_pub': 7389.0, 'value_agg': 7389.0, 'explained': 287.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 3162.0, 'value_agg': 3162.0, 'explained': 108.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 689.0, 'value_agg': 689.0, 'explained': 19.0}]
- bfs_census_1970_2000 / kanton / vz_rel_no_answer: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 291.0, 'value_agg': 291.0, 'explained': 10.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 1323.0, 'value_agg': 1323.0, 'explained': 39.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 9502.0, 'value_agg': 9503.0, 'explained': 277.0}]
- bfs_census_1970_2000 / kanton / vz_rel_none: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 510.0, 'value_agg': 510.0, 'explained': 24.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 2473.0, 'value_agg': 2473.0, 'explained': 114.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 14500.0, 'value_agg': 14501.0, 'explained': 597.0}]
- bfs_census_1970_2000 / kanton / vz_rel_orthodox: [{'unit_id': 'FR', 'period': '2000', 'value_pub': 1961.0, 'value_agg': 1961.0, 'explained': 111.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 882.0, 'value_agg': 882.0, 'explained': 39.0}, {'unit_id': 'BE', 'period': '2000', 'value_pub': 9153.0, 'value_agg': 9103.0, 'explained': -161.0}]
- bfs_census_1970_2000 / kanton / vz_rel_other: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 129.0, 'value_agg': 129.0, 'explained': 3.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 901.0, 'value_agg': 901.0, 'explained': 19.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 285.0, 'value_agg': 285.0, 'explained': 3.0}]
- bfs_census_1970_2000 / kanton / vz_rel_other_christian: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 358.0, 'value_agg': 364.0, 'explained': 68.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 744.0, 'value_agg': 757.0, 'explained': 98.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 1860.0, 'value_agg': 1867.0, 'explained': 215.0}]
- bfs_census_1970_2000 / kanton / vz_rel_reformed: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 23769.0, 'value_agg': 23808.0, 'explained': 4491.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 25054.0, 'value_agg': 25093.0, 'explained': 4272.0}, {'unit_id': 'FR', 'period': '1990', 'value_pub': 30360.0, 'value_agg': 30402.0, 'explained': 4090.0}]
- bfs_census_1970_2000 / kanton / vz_rel_total: [{'unit_id': 'FR', 'period': '1970', 'value_pub': 180309.0, 'value_agg': 180358.0, 'explained': 6312.0}, {'unit_id': 'FR', 'period': '1980', 'value_pub': 185246.0, 'value_agg': 185300.0, 'explained': 6278.0}, {'unit_id': 'FR', 'period': '2000', 'value_pub': 241706.0, 'value_agg': 241759.0, 'explained': 7859.0}]
- bfs_construction / kanton / con_exp_maintenance: [{'unit_id': 'BS', 'period': '2001', 'value_pub': 4704.0, 'value_agg': 86.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2002', 'value_pub': 5005.0, 'value_agg': 105.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '1995', 'value_pub': 49887.0, 'value_agg': 2045.0, 'explained': 0.0}]
- bfs_construction / kanton / con_exp_private: [{'unit_id': 'GL', 'period': '2012', 'value_pub': 464828.0, 'value_agg': 132503.0, 'explained': 0.0}, {'unit_id': 'GL', 'period': '2010', 'value_pub': 456793.0, 'value_agg': 168311.0, 'explained': 0.0}, {'unit_id': 'GL', 'period': '2013', 'value_pub': 484298.0, 'value_agg': 184243.0, 'explained': 0.0}]
- bfs_construction / kanton / con_exp_public: [{'unit_id': 'JU', 'period': '2000', 'value_pub': 1191301.0, 'value_agg': 88012.0, 'explained': 14818.0}, {'unit_id': 'UR', 'period': '2009', 'value_pub': 402884.0, 'value_agg': 30022.0, 'explained': 0.0}, {'unit_id': 'UR', 'period': '2008', 'value_pub': 364220.0, 'value_agg': 28799.0, 'explained': 0.0}]
- bfs_construction / kanton / con_exp_total: [{'unit_id': 'JU', 'period': '2000', 'value_pub': 1355861.0, 'value_agg': 273417.0, 'explained': 37793.0}, {'unit_id': 'JU', 'period': '1997', 'value_pub': 882001.0, 'value_agg': 232582.0, 'explained': 12725.0}, {'unit_id': 'UR', 'period': '2008', 'value_pub': 473146.0, 'value_agg': 137716.0, 'explained': 0.0}]
- bfs_construction / kanton / con_inv_new: [{'unit_id': 'JU', 'period': '2000', 'value_pub': 1250641.0, 'value_agg': 174152.0, 'explained': 19613.0}, {'unit_id': 'JU', 'period': '1997', 'value_pub': 782524.0, 'value_agg': 137478.0, 'explained': 4680.0}, {'unit_id': 'GL', 'period': '2012', 'value_pub': 424015.0, 'value_agg': 89870.0, 'explained': 0.0}]
- bfs_construction / kanton / con_inv_renovation: [{'unit_id': 'UR', 'period': '2007', 'value_pub': 168691.0, 'value_agg': 48189.0, 'explained': 0.0}, {'unit_id': 'UR', 'period': '2006', 'value_pub': 185147.0, 'value_agg': 55195.0, 'explained': 0.0}, {'unit_id': 'UR', 'period': '2008', 'value_pub': 103610.0, 'value_agg': 32117.0, 'explained': 0.0}]
- bfs_construction / kanton / con_inv_residential: [{'unit_id': 'UR', 'period': '2008', 'value_pub': 79849.0, 'value_agg': 76804.0, 'explained': 0.0}, {'unit_id': 'NE', 'period': '2005', 'value_pub': 288039.0, 'value_agg': 278739.0, 'explained': 0.0}, {'unit_id': 'UR', 'period': '2007', 'value_pub': 91681.0, 'value_agg': 89517.0, 'explained': 0.0}]
- bfs_construction / kanton / con_inv_total: [{'unit_id': 'JU', 'period': '2000', 'value_pub': 1335124.0, 'value_agg': 256163.0, 'explained': 36970.0}, {'unit_id': 'JU', 'period': '1997', 'value_pub': 864246.0, 'value_agg': 217693.0, 'explained': 12085.0}, {'unit_id': 'UR', 'period': '2006', 'value_pub': 479107.0, 'value_agg': 145279.0, 'explained': 0.0}]
- bfs_nrw / bezirk / nrw_ballots_blank: [{'unit_id': '1302', 'period': '1983', 'value_pub': 6.0, 'value_agg': 6.0, 'explained': -81.0}, {'unit_id': '111', 'period': '1983', 'value_pub': 14.0, 'value_agg': 14.0, 'explained': -140.0}, {'unit_id': '111', 'period': '1971', 'value_pub': 33.0, 'value_agg': 33.0, 'explained': -314.0}]
- bfs_nrw / bezirk / nrw_ballots_changed: [{'unit_id': '111', 'period': '1975', 'value_pub': 9988.0, 'value_agg': 9988.0, 'explained': -66714.0}, {'unit_id': '111', 'period': '1979', 'value_pub': 9606.0, 'value_agg': 9606.0, 'explained': -61451.0}, {'unit_id': '1841', 'period': '1991', 'value_pub': 1479.0, 'value_agg': 1479.0, 'explained': 8584.0}]
- bfs_nrw / bezirk / nrw_ballots_invalid: [{'unit_id': '2107', 'period': '1999', 'value_pub': 2.0, 'value_agg': 2.0, 'explained': -96.0}, {'unit_id': '111', 'period': '1979', 'value_pub': 15.0, 'value_agg': 15.0, 'explained': -495.0}, {'unit_id': '2107', 'period': '2003', 'value_pub': 6.0, 'value_agg': 6.0, 'explained': -84.0}]
- bfs_nrw / bezirk / nrw_ballots_unchanged: [{'unit_id': '111', 'period': '1975', 'value_pub': 6720.0, 'value_agg': 6720.0, 'explained': -58150.0}, {'unit_id': '111', 'period': '1979', 'value_pub': 6260.0, 'value_agg': 6260.0, 'explained': -50798.0}, {'unit_id': '111', 'period': '1983', 'value_pub': 6424.0, 'value_agg': 6424.0, 'explained': -45671.0}]
- bfs_nrw / bezirk / nrw_ballots_valid: [{'unit_id': '111', 'period': '1971', 'value_pub': 18024.0, 'value_agg': 18024.0, 'explained': -154198.0}, {'unit_id': '111', 'period': '1975', 'value_pub': 17122.0, 'value_agg': 17122.0, 'explained': -127974.0}, {'unit_id': '111', 'period': '1979', 'value_pub': 16360.0, 'value_agg': 16360.0, 'explained': -115391.0}]
- bfs_nrw / bezirk / nrw_eligible: [{'unit_id': '111', 'period': '1971', 'value_pub': 33632.0, 'value_agg': 33632.0, 'explained': -274550.0}, {'unit_id': '111', 'period': '1975', 'value_pub': 37400.0, 'value_agg': 37400.0, 'explained': -261077.0}, {'unit_id': '111', 'period': '1979', 'value_pub': 39353.0, 'value_agg': 39353.0, 'explained': -257002.0}]
- bfs_nrw / bezirk / nrw_voters: [{'unit_id': '111', 'period': '1971', 'value_pub': 18065.0, 'value_agg': 18065.0, 'explained': -154581.0}, {'unit_id': '111', 'period': '1975', 'value_pub': 17160.0, 'value_agg': 17160.0, 'explained': -128224.0}, {'unit_id': '111', 'period': '1979', 'value_pub': 16405.0, 'value_agg': 16405.0, 'explained': -116028.0}]
- bfs_nrw / kanton / nrw_ballots_blank: [{'unit_id': 'BS', 'period': '2023', 'value_pub': 96.0, 'value_agg': 73.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2015', 'value_pub': 152.0, 'value_agg': 125.0, 'explained': 0.0}, {'unit_id': 'FR', 'period': '1999', 'value_pub': 749.0, 'value_agg': 749.0, 'explained': 83.0}]
- bfs_nrw / kanton / nrw_ballots_changed: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 16497.0, 'value_agg': 14409.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 24410.0, 'value_agg': 23304.0, 'explained': 0.0}, {'unit_id': 'FR', 'period': '2019', 'value_pub': 36933.0, 'value_agg': 36739.0, 'explained': 1293.0}]
- bfs_nrw / kanton / nrw_ballots_invalid: [{'unit_id': 'AI', 'period': '1987', 'value_pub': 65.0, 'value_agg': 54.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999', 'value_pub': 12.0, 'value_agg': 11.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1995', 'value_pub': 508.0, 'value_agg': 467.0, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_ballots_unchanged: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 59268.0, 'value_agg': 54051.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 72941.0, 'value_agg': 67573.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2023', 'value_pub': 75126.0, 'value_agg': 69636.0, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_ballots_valid: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 79874.0, 'value_agg': 72091.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 103801.0, 'value_agg': 97023.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999', 'value_pub': 5105.0, 'value_agg': 4780.0, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_eligible: [{'unit_id': 'GE', 'period': '2023', 'value_pub': 277228.0, 'value_agg': 244166.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2019', 'value_pub': 268337.0, 'value_agg': 240490.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 248915.0, 'value_agg': 226881.0, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_bdp: [{'unit_id': 'FR', 'period': '2011', 'value_pub': 1633.0, 'value_agg': 1632.8976691061378, 'explained': 198.63513685012055}, {'unit_id': 'FR', 'period': '2019', 'value_pub': 571.0, 'value_agg': 560.063723222768, 'explained': 37.74405599738714}, {'unit_id': 'FR', 'period': '2015', 'value_pub': 1169.0, 'value_agg': 1155.562045399889, 'explained': 76.17817218703365}]
- bfs_nrw / kanton / nrw_fw_csp: [{'unit_id': 'FR', 'period': '2019', 'value_pub': 2847.0, 'value_agg': 2757.7839683937063, 'explained': 59.66464236510045}, {'unit_id': 'FR', 'period': '2015', 'value_pub': 1654.0, 'value_agg': 1633.4859393489594, 'explained': 29.834037016214698}, {'unit_id': 'FR', 'period': '1999', 'value_pub': 6910.0, 'value_agg': 6909.508904268758, 'explained': 149.90511017146093}]
- bfs_nrw / kanton / nrw_fw_cvp: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 11707.0, 'value_agg': 10676.197972263608, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2011', 'value_pub': 9814.0, 'value_agg': 8995.71301137349, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999', 'value_pub': 3754.0, 'value_agg': 3470.0, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_edu: [{'unit_id': 'BS', 'period': '2023', 'value_pub': 237.0, 'value_agg': 207.99966173210964, 'explained': 0.0}, {'unit_id': 'FR', 'period': '2007', 'value_pub': 722.0, 'value_agg': 721.5354662001571, 'explained': 71.39892384764228}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 233.0, 'value_agg': 211.69727267559196, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_evp: [{'unit_id': 'FR', 'period': '2003', 'value_pub': 522.0, 'value_agg': 522.2284155019588, 'explained': 78.20392245453627}, {'unit_id': 'FR', 'period': '2011', 'value_pub': 602.0, 'value_agg': 602.3318414484538, 'explained': 79.60010998773214}, {'unit_id': 'FR', 'period': '2007', 'value_pub': 631.0, 'value_agg': 631.1258532792606, 'explained': 71.54404361156024}]
- bfs_nrw / kanton / nrw_fw_fdp: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 13261.0, 'value_agg': 11951.528131688268, 'explained': 0.0}, {'unit_id': 'FR', 'period': '1987', 'value_pub': 9931.0, 'value_agg': 9930.905544223571, 'explained': 825.4913147211433}, {'unit_id': 'FR', 'period': '1983', 'value_pub': 12759.0, 'value_agg': 12758.86801735083, 'explained': 978.4117911553111}]
- bfs_nrw / kanton / nrw_fw_fga: [{'unit_id': 'FR', 'period': '1987', 'value_pub': 1012.0, 'value_agg': 1012.0506619989617, 'explained': 35.99378711066603}, {'unit_id': 'LU', 'period': '1995', 'value_pub': 905.0, 'value_agg': 877.9382349853238, 'explained': 0.0}, {'unit_id': 'VS', 'period': '2011', 'value_pub': 797.0, 'value_agg': 777.0690407603847, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_fps: [{'unit_id': 'LU', 'period': '1999', 'value_pub': 406.0, 'value_agg': 400.8777943130437, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_glp: [{'unit_id': 'FR', 'period': '2011', 'value_pub': 3064.0, 'value_agg': 3064.093041160794, 'explained': 255.5966834468463}, {'unit_id': 'FR', 'period': '2015', 'value_pub': 2905.0, 'value_agg': 2853.640123143177, 'explained': 182.62485765750841}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 2356.0, 'value_agg': 2168.514005251414, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_gruene: [{'unit_id': 'GE', 'period': '2015', 'value_pub': 11903.0, 'value_agg': 10755.069716253087, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2011', 'value_pub': 14083.0, 'value_agg': 12858.418077913877, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2023', 'value_pub': 16266.0, 'value_agg': 15027.681306161245, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_ldu: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 1916.0, 'value_agg': 1760.2588738064564, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_lps: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 12801.0, 'value_agg': 10670.095914084537, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2003', 'value_pub': 16839.0, 'value_agg': 15962.203458360898, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2007', 'value_pub': 15867.0, 'value_agg': 15073.213842835898, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_mcr: [{'unit_id': 'GE', 'period': '2023', 'value_pub': 13019.0, 'value_agg': 12570.703302207201, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2007', 'value_pub': 2692.0, 'value_agg': 2619.2682979200354, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 8184.0, 'value_agg': 7970.734245757655, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_mitte: [{'unit_id': 'GE', 'period': '2023', 'value_pub': 8639.0, 'value_agg': 8085.255504412089, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2023', 'value_pub': 3287.0, 'value_agg': 3147.277673429057, 'explained': 0.0}, {'unit_id': 'VD', 'period': '2023', 'value_pub': 8312.0, 'value_agg': 8088.591661396587, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_other: [{'unit_id': 'AI', 'period': '1991', 'value_pub': 49.0, 'value_agg': 38.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999', 'value_pub': 37.0, 'value_agg': 32.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1975', 'value_pub': 867.0, 'value_agg': 782.6351891786152, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_pda: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 14355.0, 'value_agg': 13294.997940779165, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2019', 'value_pub': 1153.0, 'value_agg': 1069.301459208019, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2007', 'value_pub': 1999.0, 'value_agg': 1867.0870798652231, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_psa: [{'unit_id': 'TI', 'period': '1979', 'value_pub': 8147.0, 'value_agg': 8082.025437673577, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_rep: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 5532.0, 'value_agg': 4868.795238905499, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_sd: [{'unit_id': 'FR', 'period': '1999', 'value_pub': 207.0, 'value_agg': 207.09238696373376, 'explained': 24.025423977818793}, {'unit_id': 'VD', 'period': '2007', 'value_pub': 425.0, 'value_agg': 378.3824490477523, 'explained': 0.0}, {'unit_id': 'VD', 'period': '2011', 'value_pub': 148.0, 'value_agg': 135.88159770691573, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_sol: [{'unit_id': 'GE', 'period': '2023', 'value_pub': 2675.0, 'value_agg': 2455.9617789498184, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 6291.0, 'value_agg': 5879.301651637249, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2011', 'value_pub': 5227.0, 'value_agg': 4902.781100896719, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_sp: [{'unit_id': 'GE', 'period': '2015', 'value_pub': 20694.0, 'value_agg': 19126.24004878344, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1975', 'value_pub': 18090.0, 'value_agg': 16822.17247913288, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2011', 'value_pub': 19217.0, 'value_agg': 18044.14409910071, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_fw_svp: [{'unit_id': 'FR', 'period': '1999', 'value_pub': 7246.0, 'value_agg': 7246.034033084827, 'explained': 593.6986812546912}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 18302.0, 'value_agg': 17156.514945922514, 'explained': 0.0}, {'unit_id': 'FR', 'period': '2019', 'value_pub': 17671.0, 'value_agg': 17369.52423110528, 'explained': 760.2523894550634}]
- bfs_nrw / kanton / nrw_fw_total: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 79874.0, 'value_agg': 72092.67390114117, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 103801.0, 'value_agg': 96974.03956414685, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999', 'value_pub': 5105.0, 'value_agg': 4780.0, 'explained': 0.0}]
- bfs_nrw / kanton / nrw_voters: [{'unit_id': 'GE', 'period': '1975', 'value_pub': 80338.0, 'value_agg': 72533.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2015', 'value_pub': 106852.0, 'value_agg': 99943.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999', 'value_pub': 5130.0, 'value_agg': 4803.0, 'explained': 0.0}]
- bfs_social_assistance / kanton / sh_recipients: [{'unit_id': 'GL', 'period': '2007', 'value_pub': 696.50355371562, 'value_agg': 593.0, 'explained': 0.0}, {'unit_id': 'VS', 'period': '2025', 'value_pub': 6402.34724, 'value_agg': 5697.016710000001, 'explained': 0.0}, {'unit_id': 'VD', 'period': '2025', 'value_pub': 37657.68739, 'value_agg': 40597.68739, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 22228.0, 'value_agg': 15084.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 23677.0, 'value_agg': 18288.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 61702.0, 'value_agg': 59291.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_bev: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 595.0, 'value_agg': 322.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2025', 'value_pub': 3078.0, 'value_agg': 2765.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2024', 'value_pub': 2426.0, 'value_agg': 2193.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_diesel: [{'unit_id': 'AI', 'period': '2019', 'value_pub': 8409.0, 'value_agg': 6238.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2022', 'value_pub': 5958.0, 'value_agg': 4573.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2019', 'value_pub': 19059.0, 'value_agg': 17946.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_hev: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 2356.0, 'value_agg': 1123.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 614.0, 'value_agg': 428.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 2948.0, 'value_agg': 2673.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_petrol: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 12265.0, 'value_agg': 8701.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 14463.0, 'value_agg': 11459.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 38390.0, 'value_agg': 37457.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_phev: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 1045.0, 'value_agg': 356.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 97.0, 'value_agg': 70.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 762.0, 'value_agg': 686.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_private: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 12852.0, 'value_agg': 10501.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 50167.0, 'value_agg': 49634.0, 'explained': 0.0}, {'unit_id': 'ZG', 'period': '2022', 'value_pub': 61985.0, 'value_agg': 61346.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_newreg_bev: [{'unit_id': 'NE', 'period': '2024', 'value_pub': 688.0, 'value_agg': 569.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2024', 'value_pub': 651.0, 'value_agg': 558.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2023', 'value_pub': 654.0, 'value_agg': 561.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_newreg_cars: [{'unit_id': 'BS', 'period': '2022', 'value_pub': 2716.0, 'value_agg': 2343.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2024', 'value_pub': 2812.0, 'value_agg': 2455.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2023', 'value_pub': 3000.0, 'value_agg': 2633.0, 'explained': 0.0}]
- bfs_votes_gemeinde / bezirk / vote_ballots: [{'unit_id': '111', 'period': '1960-05-29#1930', 'value_pub': 5943.0, 'value_agg': 5943.0, 'explained': -81097.0}, {'unit_id': '111', 'period': '1962-05-27#2000', 'value_pub': 5759.0, 'value_agg': 5759.0, 'explained': -75842.0}, {'unit_id': '111', 'period': '1962-05-27#2010', 'value_pub': 5759.0, 'value_agg': 5759.0, 'explained': -75803.0}]
- bfs_votes_gemeinde / bezirk / vote_eligible: [{'unit_id': '111', 'period': '1960-05-29#1930', 'value_pub': 10515.0, 'value_agg': 10515.0, 'explained': -131412.0}, {'unit_id': '111', 'period': '1960-12-04#1940', 'value_pub': 10781.0, 'value_agg': 10781.0, 'explained': -131124.0}, {'unit_id': '111', 'period': '1961-03-05#1950', 'value_pub': 10899.0, 'value_agg': 10899.0, 'explained': -130658.0}]
- bfs_votes_gemeinde / bezirk / vote_no: [{'unit_id': '1302', 'period': '1973-05-20#2360', 'value_pub': 249.0, 'value_agg': 249.0, 'explained': -4617.0}, {'unit_id': '111', 'period': '1963-12-08#2040', 'value_pub': 1129.0, 'value_agg': 1129.0, 'explained': -15349.0}, {'unit_id': '111', 'period': '1960-12-04#1940', 'value_pub': 2646.0, 'value_agg': 2646.0, 'explained': -35128.0}]
- bfs_votes_gemeinde / bezirk / vote_valid: [{'unit_id': '111', 'period': '1960-05-29#1930', 'value_pub': 5746.0, 'value_agg': 5746.0, 'explained': -79495.0}, {'unit_id': '111', 'period': '1962-05-27#2000', 'value_pub': 5487.0, 'value_agg': 5487.0, 'explained': -72657.0}, {'unit_id': '111', 'period': '1962-05-27#2010', 'value_pub': 5452.0, 'value_agg': 5452.0, 'explained': -71910.0}]
- bfs_votes_gemeinde / bezirk / vote_yes: [{'unit_id': '111', 'period': '1962-04-01#1990', 'value_pub': 2246.0, 'value_agg': 2246.0, 'explained': -33347.0}, {'unit_id': '111', 'period': '1961-03-05#1960', 'value_pub': 2972.0, 'value_agg': 2972.0, 'explained': -43689.0}, {'unit_id': '111', 'period': '1960-05-29#1930', 'value_pub': 4683.0, 'value_agg': 4683.0, 'explained': -67487.0}]
- bfs_votes_gemeinde / kanton / vote_ballots: [{'unit_id': 'GE', 'period': '1996-12-01#4330', 'value_pub': 88416.0, 'value_agg': 76987.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1996-12-01#4320', 'value_pub': 88418.0, 'value_agg': 77005.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1996-03-10#4280', 'value_pub': 66678.0, 'value_agg': 58586.0, 'explained': 0.0}]
- bfs_votes_gemeinde / kanton / vote_eligible: [{'unit_id': 'GE', 'period': '2025-11-30#6810', 'value_pub': 286403.0, 'value_agg': 249998.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2025-11-30#6800', 'value_pub': 286403.0, 'value_agg': 249998.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2026-03-08#6823', 'value_pub': 285621.0, 'value_agg': 249324.0, 'explained': 0.0}]
- bfs_votes_gemeinde / kanton / vote_no: [{'unit_id': 'GE', 'period': '1979-02-18#2940', 'value_pub': 17164.0, 'value_agg': 14599.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1996-12-01#4320', 'value_pub': 60835.0, 'value_agg': 52348.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1979-02-18#2960', 'value_pub': 24410.0, 'value_agg': 21032.0, 'explained': 0.0}]
- bfs_votes_gemeinde / kanton / vote_valid: [{'unit_id': 'GE', 'period': '1996-12-01#4320', 'value_pub': 87269.0, 'value_agg': 76025.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1996-12-01#4330', 'value_pub': 87114.0, 'value_agg': 75894.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '1996-03-10#4260', 'value_pub': 63605.0, 'value_agg': 55840.0, 'explained': 0.0}]
- bfs_votes_gemeinde / kanton / vote_yes: [{'unit_id': 'AI', 'period': '2000-03-12#4610', 'value_pub': 302.0, 'value_agg': 253.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1994-12-04#4160', 'value_pub': 351.0, 'value_agg': 298.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '1999-06-13#4580', 'value_pub': 684.0, 'value_agg': 581.0, 'explained': 0.0}]
- kt_crime / kanton / crime_stgb_offences: [{'unit_id': 'BS', 'period': '2018', 'value_pub': 20617.0, 'value_agg': 19312.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2017', 'value_pub': 21910.0, 'value_agg': 20534.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2015', 'value_pub': 20961.0, 'value_agg': 19718.0, 'explained': 0.0}]
- kt_crime / kanton / crime_stgb_property: [{'unit_id': 'BS', 'period': '2017', 'value_pub': 15093.0, 'value_agg': 14203.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2018', 'value_pub': 14542.0, 'value_agg': 13772.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2015', 'value_pub': 14931.0, 'value_agg': 14218.0, 'explained': 0.0}]
- kt_crime / kanton / crime_stgb_violent: [{'unit_id': 'BS', 'period': '2023', 'value_pub': 1389.0, 'value_agg': 1370.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2025', 'value_pub': 1510.0, 'value_agg': 1496.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2009', 'value_pub': 1417.0, 'value_agg': 1406.0, 'explained': 0.0}]
- kt_unemployment / kanton / unemp_registered: [{'unit_id': 'GE', 'period': '2019', 'value_pub': 9754.0, 'value_agg': 9638.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2025', 'value_pub': 11926.0, 'value_agg': 11803.0, 'explained': 0.0}, {'unit_id': 'GE', 'period': '2021', 'value_pub': 12360.0, 'value_agg': 12278.0, 'explained': 0.0}]

## B. Ranges

- **ent_share_jobs_accommodation_food**: 1.0 values outside 0–100 — e.g. gemeinde 6109 2018: 114.286

## C. Year-on-year jumps (> 50% and > 200 units)

| Metric | Flags | Series | Largest |
|---|---|---|---|
| con_exp_public | 22298 | 2086 | [{'unit_id': '6628', 'year': 2022, 'prev': 343220.0, 'value': 72595.0, 'precision': 'exact'}, {'unit_id': '242', 'year': 2002, 'prev': 4137.0, 'value': 225075.0, 'precision': 'exact'}] |
| con_inv_new | 20782 | 2073 | [{'unit_id': '6633', 'year': 2005, 'prev': 48348.0, 'value': 612139.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2006, 'prev': 612139.0, 'value': 97936.0, 'precision': 'exact'}] |
| con_inv_renovation | 20495 | 2075 | [{'unit_id': '3203', 'year': 2001, 'prev': 162228.0, 'value': 409002.0, 'precision': 'exact'}, {'unit_id': '6152', 'year': 2004, 'prev': 204295.0, 'value': 20235.0, 'precision': 'exact'}] |
| con_inv_residential | 17678 | 2036 | [{'unit_id': '3203', 'year': 2001, 'prev': 84278.0, 'value': 380963.0, 'precision': 'exact'}, {'unit_id': '3203', 'year': 2002, 'prev': 380963.0, 'value': 132918.0, 'precision': 'exact'}] |
| con_exp_private | 16560 | 2013 | [{'unit_id': '6633', 'year': 2005, 'prev': 57969.0, 'value': 603644.0, 'precision': 'exact'}, {'unit_id': '3203', 'year': 2001, 'prev': 122455.0, 'value': 636806.0, 'precision': 'exact'}] |
| con_inv_total | 15274 | 1983 | [{'unit_id': '3203', 'year': 2001, 'prev': 254259.0, 'value': 831545.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2005, 'prev': 64234.0, 'value': 625352.0, 'precision': 'exact'}] |
| con_exp_total | 14055 | 1964 | [{'unit_id': '3203', 'year': 2001, 'prev': 271270.0, 'value': 849346.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2005, 'prev': 65563.0, 'value': 625975.0, 'precision': 'exact'}] |
| con_exp_maintenance | 10300 | 1869 | [{'unit_id': '2701', 'year': 2003, 'prev': 0.0, 'value': 98863.0, 'precision': 'exact'}, {'unit_id': '250', 'year': 2020, 'prev': 974.0, 'value': 72017.0, 'precision': 'exact'}] |
| agr_poultry | 2580 | 930 | [{'unit_id': '2029', 'year': 2018, 'prev': 261447.0, 'value': 59304.0, 'precision': 'exact'}, {'unit_id': '2029', 'year': 2017, 'prev': 64954.0, 'value': 261447.0, 'precision': 'exact'}] |
| bil_net_migration | 1448 | 334 | [{'unit_id': '261', 'year': 2007, 'prev': 2315.0, 'value': 8902.0, 'precision': 'exact'}, {'unit_id': '261', 'year': 2022, 'prev': 464.0, 'value': 4464.0, 'precision': 'exact'}] |
| gk_pop_d | 798 | 464 | [{'unit_id': '6248', 'year': 2020, 'prev': 1962.0, 'value': 9830.0, 'precision': 'modelled'}, {'unit_id': '2125', 'year': 2018, 'prev': 9375.0, 'value': 4261.0, 'precision': 'modelled'}] |
| gk_pop_c | 768 | 412 | [{'unit_id': '4671', 'year': 2024, 'prev': 5816.0, 'value': 12270.0, 'precision': 'modelled'}, {'unit_id': '5642', 'year': 2023, 'prev': 7708.0, 'value': 2643.0, 'precision': 'modelled'}] |
| gk_pop_none | 717 | 434 | [{'unit_id': '5938', 'year': 2013, 'prev': 7837.0, 'value': 241.0, 'precision': 'modelled'}, {'unit_id': '6248', 'year': 2013, 'prev': 7373.0, 'value': 1563.0, 'precision': 'modelled'}] |
| agr_pigs | 632 | 353 | [{'unit_id': '3422', 'year': 1998, 'prev': 1494.0, 'value': 8558.0, 'precision': 'exact'}, {'unit_id': '360', 'year': 2013, 'prev': 10686.0, 'value': 3744.0, 'precision': 'exact'}] |
| gk_pop_b | 412 | 230 | [{'unit_id': '6621', 'year': 2014, 'prev': 59025.0, 'value': 16399.0, 'precision': 'modelled'}, {'unit_id': '6621', 'year': 2013, 'prev': 25766.0, 'value': 59025.0, 'precision': 'modelled'}] |
| tax_np_federal_tax_chf | 364 | 205 | [{'unit_id': '6602', 'year': 2014, 'prev': 18776239.0, 'value': 219176296.0, 'precision': 'exact'}, {'unit_id': '139', 'year': 2012, 'prev': 185298987.0, 'value': 28490789.0, 'precision': 'exact'}] |
| con_new_dwellings | 322 | 113 | [{'unit_id': '230', 'year': 2012, 'prev': 1561.0, 'value': 301.0, 'precision': 'exact'}, {'unit_id': '230', 'year': 2011, 'prev': 342.0, 'value': 1561.0, 'precision': 'exact'}] |
| bil_net_international | 280 | 88 | [{'unit_id': '261', 'year': 2007, 'prev': 3656.0, 'value': 8853.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 1988, 'prev': 2019.0, 'value': 4455.0, 'precision': 'exact'}] |
| gk_pop_a | 204 | 104 | [{'unit_id': '5192', 'year': 2021, 'prev': 5004.0, 'value': 16650.0, 'precision': 'modelled'}, {'unit_id': '1054', 'year': 2020, 'prev': 2329.0, 'value': 9670.0, 'precision': 'modelled'}] |
| agr_sheep | 198 | 138 | [{'unit_id': '1707', 'year': 2020, 'prev': 148.0, 'value': 3119.0, 'precision': 'exact'}, {'unit_id': '1707', 'year': 2022, 'prev': 2532.0, 'value': 88.0, 'precision': 'exact'}] |
| con_new_dw_mfh | 183 | 82 | [{'unit_id': '261', 'year': 2011, 'prev': 849.0, 'value': 1957.0, 'precision': 'exact'}, {'unit_id': '230', 'year': 2003, 'prev': 116.0, 'value': 1179.0, 'precision': 'exact'}] |
| gws_dw_2011plus | 91 | 82 | [{'unit_id': '261', 'year': 2011, 'prev': 0.0, 'value': 2348.0, 'precision': 'exact'}, {'unit_id': '230', 'year': 2011, 'prev': 0.0, 'value': 1066.0, 'precision': 'exact'}] |
| mig_net_intl_foreign | 86 | 52 | [{'unit_id': '351', 'year': 2023, 'prev': 1450.0, 'value': 3046.0, 'precision': 'exact'}, {'unit_id': '1061', 'year': 2023, 'prev': 898.0, 'value': 2116.0, 'precision': 'exact'}] |
| pop_nonpermanent | 76 | 52 | [{'unit_id': '261', 'year': 2022, 'prev': 3560.0, 'value': 7598.0, 'precision': 'exact'}, {'unit_id': '2701', 'year': 2022, 'prev': 2332.0, 'value': 4718.0, 'precision': 'exact'}] |
| bil_net_intercant | 68 | 26 | [{'unit_id': '261', 'year': 1984, 'prev': -1886.0, 'value': 656.0, 'precision': 'exact'}, {'unit_id': '261', 'year': 1983, 'prev': 52.0, 'value': -1886.0, 'precision': 'exact'}] |
| bil_intracant_in | 67 | 49 | [{'unit_id': '5583', 'year': 2024, 'prev': 617.0, 'value': 1734.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2021, 'prev': 494.0, 'value': 1585.0, 'precision': 'exact'}] |
| vac_dwellings | 65 | 43 | [{'unit_id': '6621', 'year': 2001, 'prev': 1004.0, 'value': 452.0, 'precision': 'exact'}, {'unit_id': '361', 'year': 2009, 'prev': 570.0, 'value': 35.0, 'precision': 'exact'}] |
| vac_for_rent | 61 | 39 | [{'unit_id': '6621', 'year': 2001, 'prev': 950.0, 'value': 410.0, 'precision': 'exact'}, {'unit_id': '361', 'year': 2009, 'prev': 570.0, 'value': 35.0, 'precision': 'exact'}] |
| bil_immigration | 37 | 22 | [{'unit_id': '6253', 'year': 2012, 'prev': 300.0, 'value': 1078.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2011, 'prev': 969.0, 'value': 300.0, 'precision': 'exact'}] |
| tax_np_taxable_income_chf | 35 | 19 | [{'unit_id': '6602', 'year': 2014, 'prev': 218175600.0, 'value': 1963065200.0, 'precision': 'exact'}, {'unit_id': '139', 'year': 2012, 'prev': 1772805899.9999998, 'value': 416653500.0, 'precision': 'exact'}] |
| agr_cattle | 34 | 15 | [{'unit_id': '4506', 'year': 1998, 'prev': 2365.0, 'value': 780.0, 'precision': 'exact'}, {'unit_id': '4511', 'year': 1997, 'prev': 1574.0, 'value': 0.0, 'precision': 'exact'}] |
| tax_np_net_income_chf | 32 | 17 | [{'unit_id': '6602', 'year': 2014, 'prev': 229213700.00000003, 'value': 1974302000.0, 'precision': 'exact'}, {'unit_id': '139', 'year': 2012, 'prev': 1800612200.0, 'value': 444567300.0, 'precision': 'exact'}] |
| bil_intracant_out | 32 | 23 | [{'unit_id': '360', 'year': 1991, 'prev': 1074.0, 'value': 319.0, 'precision': 'exact'}, {'unit_id': '3955', 'year': 1992, 'prev': 955.0, 'value': 264.0, 'precision': 'exact'}] |
| tax_np_taxpayers_no_federal_tax | 27 | 27 | [{'unit_id': '5192', 'year': 2005, 'prev': 2345.0, 'value': 6836.0, 'precision': 'exact'}, {'unit_id': '5002', 'year': 2005, 'prev': 1311.0, 'value': 4173.0, 'precision': 'exact'}] |
| udemo_jobs_active | 25 | 22 | [{'unit_id': '4034', 'year': 2023, 'prev': 4608.0, 'value': 1849.0, 'precision': 'exact'}, {'unit_id': '197', 'year': 2023, 'prev': 1877.0, 'value': 3759.0, 'precision': 'exact'}] |
| bil_emigration | 23 | 13 | [{'unit_id': '5586', 'year': 2010, 'prev': 1847.0, 'value': 4526.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2012, 'prev': 246.0, 'value': 839.0, 'precision': 'exact'}] |
| mfz_newreg_cars | 23 | 14 | [{'unit_id': '3101', 'year': 2018, 'prev': 412.0, 'value': 20256.0, 'precision': 'exact'}, {'unit_id': '247', 'year': 2018, 'prev': 7387.0, 'value': 1451.0, 'precision': 'exact'}] |
| mig_immigration_foreign | 22 | 17 | [{'unit_id': '6253', 'year': 2012, 'prev': 251.0, 'value': 1043.0, 'precision': 'exact'}, {'unit_id': '56', 'year': 2017, 'prev': 791.0, 'value': 210.0, 'precision': 'exact'}] |
| bil_naturalisations | 21 | 12 | [{'unit_id': '6621', 'year': 2015, 'prev': 847.0, 'value': 2295.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2020, 'prev': 2250.0, 'value': 1071.0, 'precision': 'exact'}] |
| gws_bld_pre1919 | 19 | 12 | [{'unit_id': '230', 'year': 2011, 'prev': 3525.0, 'value': 22.0, 'precision': 'exact'}, {'unit_id': '230', 'year': 2012, 'prev': 22.0, 'value': 3420.0, 'precision': 'exact'}] |
| mig_intracant_in_swiss | 19 | 14 | [{'unit_id': '6633', 'year': 2021, 'prev': 303.0, 'value': 1040.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2022, 'prev': 1040.0, 'value': 424.0, 'precision': 'exact'}] |
| gws_bld_1919_1945 | 18 | 11 | [{'unit_id': '3203', 'year': 2011, 'prev': 497.0, 'value': 1706.0, 'precision': 'exact'}, {'unit_id': '3443', 'year': 2011, 'prev': 55.0, 'value': 848.0, 'precision': 'exact'}] |
| ent_fte_s2 | 17 | 15 | [{'unit_id': '1707', 'year': 2023, 'prev': 1279.0, 'value': 4261.0, 'precision': 'exact'}, {'unit_id': '1707', 'year': 2022, 'prev': 4131.0, 'value': 1279.0, 'precision': 'exact'}] |
| ent_jobs_s2 | 17 | 15 | [{'unit_id': '1707', 'year': 2023, 'prev': 1422.0, 'value': 4523.0, 'precision': 'exact'}, {'unit_id': '1707', 'year': 2022, 'prev': 4369.0, 'value': 1422.0, 'precision': 'exact'}] |
| ent_jobs_ict | 13 | 10 | [{'unit_id': '362', 'year': 2014, 'prev': 198.0, 'value': 1262.0, 'precision': 'exact'}, {'unit_id': '62', 'year': 2021, 'prev': 786.3348671236736, 'value': 1818.4618274016339, 'precision': 'boundary_estimate'}] |
| gws_heat_district | 13 | 12 | [{'unit_id': '355', 'year': 2022, 'prev': 132.0, 'value': 1378.0, 'precision': 'exact'}, {'unit_id': '355', 'year': 2023, 'prev': 1378.0, 'value': 205.0, 'precision': 'exact'}] |
| unemp_registered | 13 | 9 | [{'unit_id': '261', 'year': 1992, 'prev': 2515.1, 'value': 6653.3, 'precision': 'exact'}, {'unit_id': '6621', 'year': 1991, 'prev': 1345.6666666666667, 'value': 2953.75, 'precision': 'exact'}] |
| bil_intercant_out | 12 | 11 | [{'unit_id': '1701', 'year': 1990, 'prev': 801.0, 'value': 355.0, 'precision': 'exact'}, {'unit_id': '27', 'year': 1991, 'prev': 530.0, 'value': 96.0, 'precision': 'exact'}] |
| bil_intercant_in | 12 | 10 | [{'unit_id': '6621', 'year': 1982, 'prev': 4258.0, 'value': 2002.0, 'precision': 'exact'}, {'unit_id': '27', 'year': 1991, 'prev': 594.0, 'value': 119.0, 'precision': 'exact'}] |
| nat_total | 10 | 7 | [{'unit_id': '6621', 'year': 2015, 'prev': 847.0, 'value': 2295.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2020, 'prev': 2250.0, 'value': 1071.0, 'precision': 'exact'}] |
| fin_tax_revenue_chf | 10 | 7 | [{'unit_id': '139', 'year': 2012, 'prev': 206300000.0, 'value': 47400000.0, 'precision': 'exact'}, {'unit_id': '139', 'year': 2011, 'prev': 50200000.0, 'value': 206300000.0, 'precision': 'exact'}] |
| ent_jobs_finance | 8 | 8 | [{'unit_id': '131', 'year': 2016, 'prev': 3348.0, 'value': 1606.0, 'precision': 'exact'}, {'unit_id': '69', 'year': 2014, 'prev': 993.0, 'value': 2557.0, 'precision': 'exact'}] |
| gws_bld_partly_res | 8 | 7 | [{'unit_id': '567', 'year': 2013, 'prev': 83.0, 'value': 369.0, 'precision': 'exact'}, {'unit_id': '6082', 'year': 2019, 'prev': 27.0, 'value': 290.0, 'precision': 'exact'}] |
| mig_net_intercant_foreign | 8 | 3 | [{'unit_id': '261', 'year': 2020, 'prev': 869.0, 'value': 86.0, 'precision': 'exact'}, {'unit_id': '261', 'year': 2022, 'prev': -384.0, 'value': 112.0, 'precision': 'exact'}] |
| mig_net_intl_swiss | 7 | 5 | [{'unit_id': '3673', 'year': 2014, 'prev': 536.0, 'value': -2.0, 'precision': 'exact'}, {'unit_id': '3673', 'year': 2013, 'prev': 2.0, 'value': 536.0, 'precision': 'exact'}] |
| vac_rooms_1_2 | 7 | 7 | [{'unit_id': '6621', 'year': 2001, 'prev': 790.0, 'value': 314.0, 'precision': 'exact'}, {'unit_id': '2701', 'year': 1997, 'prev': 394.0, 'value': 812.0, 'precision': 'exact'}] |
| mfz_newreg_bev | 7 | 5 | [{'unit_id': '3101', 'year': 2023, 'prev': 338.0, 'value': 1005.0, 'precision': 'exact'}, {'unit_id': '69', 'year': 2025, 'prev': 270.0, 'value': 724.0, 'precision': 'exact'}] |
| gws_heat_wood | 7 | 7 | [{'unit_id': '5192', 'year': 2024, 'prev': 599.0, 'value': 1264.0, 'precision': 'exact'}, {'unit_id': '5050', 'year': 2024, 'prev': 451.0, 'value': 937.0, 'precision': 'exact'}] |
| ent_jobs_health | 7 | 6 | [{'unit_id': '5412', 'year': 2020, 'prev': 131.0, 'value': 1963.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 218.0, 'value': 1304.0, 'precision': 'exact'}] |
| agr_goats | 7 | 6 | [{'unit_id': '5812', 'year': 2012, 'prev': 695.0, 'value': 0.0, 'precision': 'exact'}, {'unit_id': '1214', 'year': 1997, 'prev': 539.0, 'value': 0.0, 'precision': 'exact'}] |
| ent_fte | 6 | 5 | [{'unit_id': '5412', 'year': 2020, 'prev': 714.0, 'value': 2233.0, 'precision': 'exact'}, {'unit_id': '4065', 'year': 2023, 'prev': 590.0, 'value': 1260.0, 'precision': 'exact'}] |
| mig_net_intercant_swiss | 6 | 6 | [{'unit_id': '261', 'year': 2012, 'prev': 1587.0, 'value': 669.0, 'precision': 'exact'}, {'unit_id': '1061', 'year': 2014, 'prev': 311.0, 'value': 76.0, 'precision': 'exact'}] |
| mfz_cars_hev | 6 | 3 | [{'unit_id': '3101', 'year': 2023, 'prev': 954.0, 'value': 4039.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2021, 'prev': 675.0, 'value': 2255.0, 'precision': 'exact'}] |
| mfz_cars | 6 | 6 | [{'unit_id': '3101', 'year': 2018, 'prev': 5390.0, 'value': 18360.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2011, 'prev': 3662.0, 'value': 7808.0, 'precision': 'exact'}] |
| mfz_cars_petrol | 6 | 6 | [{'unit_id': '3101', 'year': 2018, 'prev': 3589.0, 'value': 10124.0, 'precision': 'exact'}, {'unit_id': '6240', 'year': 2011, 'prev': 4496.0, 'value': 1169.0, 'precision': 'exact'}] |
| mfz_cars_diesel | 6 | 6 | [{'unit_id': '3101', 'year': 2018, 'prev': 1710.0, 'value': 7961.0, 'precision': 'exact'}, {'unit_id': '1702', 'year': 2018, 'prev': 7378.0, 'value': 3508.0, 'precision': 'exact'}] |
| ent_jobs | 6 | 6 | [{'unit_id': '5412', 'year': 2020, 'prev': 868.0, 'value': 2775.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 996.0, 'value': 2041.0, 'precision': 'exact'}] |
| agr_area_organic_ha | 6 | 6 | [{'unit_id': '3396', 'year': 1998, 'prev': 201.0, 'value': 634.0, 'precision': 'exact'}, {'unit_id': '6638', 'year': 1997, 'prev': 504.0, 'value': 74.0, 'precision': 'exact'}] |
| agr_area_ha | 6 | 4 | [{'unit_id': '4511', 'year': 1997, 'prev': 859.0, 'value': 0.0, 'precision': 'exact'}, {'unit_id': '4511', 'year': 1998, 'prev': 0.0, 'value': 830.0, 'precision': 'exact'}] |
| rail_boardings_weekday | 6 | 6 | [{'unit_id': '2761', 'year': 2025, 'prev': 2400.0, 'value': 9200.0, 'precision': 'survey'}, {'unit_id': '756', 'year': 2025, 'prev': 480.0, 'value': 1080.0, 'precision': 'survey'}] |
| mig_emigration_foreign | 6 | 3 | [{'unit_id': '6253', 'year': 2012, 'prev': 183.0, 'value': 809.0, 'precision': 'exact'}, {'unit_id': '5236', 'year': 2013, 'prev': 360.0, 'value': 80.0, 'precision': 'exact'}] |
| rail_boardings_daily | 5 | 5 | [{'unit_id': '2761', 'year': 2025, 'prev': 2800.0, 'value': 8200.0, 'precision': 'survey'}, {'unit_id': '756', 'year': 2025, 'prev': 520.0, 'value': 1100.0, 'precision': 'survey'}] |
| ent_jobs_care_social | 5 | 5 | [{'unit_id': '6633', 'year': 2022, 'prev': 418.0, 'value': 994.0, 'precision': 'exact'}, {'unit_id': '5568', 'year': 2018, 'prev': 81.0, 'value': 331.0, 'precision': 'exact'}] |
| agr_area_grassland_ha | 5 | 3 | [{'unit_id': '3961', 'year': 2011, 'prev': 382.0, 'value': 1049.0, 'precision': 'exact'}, {'unit_id': '4511', 'year': 1998, 'prev': 0.0, 'value': 638.0, 'precision': 'exact'}] |
| vac_new | 5 | 3 | [{'unit_id': '3203', 'year': 2022, 'prev': 365.0, 'value': 103.0, 'precision': 'exact'}, {'unit_id': '3203', 'year': 2017, 'prev': 44.0, 'value': 283.0, 'precision': 'exact'}] |
| ent_jobs_retail | 5 | 5 | [{'unit_id': '540', 'year': 2017, 'prev': 121.0, 'value': 586.0, 'precision': 'exact'}, {'unit_id': '412', 'year': 2013, 'prev': 331.0, 'value': 740.0, 'precision': 'exact'}] |
| mig_immigration_swiss | 4 | 2 | [{'unit_id': '3673', 'year': 2014, 'prev': 541.0, 'value': 1.0, 'precision': 'exact'}, {'unit_id': '3673', 'year': 2013, 'prev': 5.0, 'value': 541.0, 'precision': 'exact'}] |
| ent_jobs_s3 | 4 | 4 | [{'unit_id': '5412', 'year': 2020, 'prev': 733.0, 'value': 2658.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 580.0, 'value': 1639.0, 'precision': 'exact'}] |
| bil_natural_balance | 4 | 4 | [{'unit_id': '6621', 'year': 2021, 'prev': 496.0, 'value': 1020.0, 'precision': 'exact'}, {'unit_id': '261', 'year': 2006, 'prev': -42.0, 'value': 379.0, 'precision': 'exact'}] |
| mfz_cars_phev | 4 | 3 | [{'unit_id': '3101', 'year': 2023, 'prev': 326.0, 'value': 969.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2020, 'prev': 57.0, 'value': 519.0, 'precision': 'exact'}] |
| udemo_jobs_closures | 4 | 2 | [{'unit_id': '66', 'year': 2019, 'prev': 400.0, 'value': 131.0, 'precision': 'exact'}, {'unit_id': '66', 'year': 2018, 'prev': 135.0, 'value': 400.0, 'precision': 'exact'}] |
| ent_fte_s3 | 4 | 4 | [{'unit_id': '5412', 'year': 2020, 'prev': 590.0, 'value': 2125.0, 'precision': 'exact'}, {'unit_id': '2527', 'year': 2023, 'prev': 1214.0, 'value': 560.0, 'precision': 'exact'}] |
| mig_intracant_out_swiss | 3 | 3 | [{'unit_id': '5002', 'year': 2017, 'prev': 1319.0, 'value': 637.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2013, 'prev': 2.0, 'value': 224.0, 'precision': 'exact'}] |
| nat_eu_efta | 3 | 3 | [{'unit_id': '6621', 'year': 2015, 'prev': 404.0, 'value': 1234.0, 'precision': 'exact'}, {'unit_id': '6628', 'year': 2015, 'prev': 102.0, 'value': 319.0, 'precision': 'exact'}] |
| mig_intracant_in_foreign | 3 | 3 | [{'unit_id': '5583', 'year': 2024, 'prev': 375.0, 'value': 885.0, 'precision': 'exact'}, {'unit_id': '6633', 'year': 2021, 'prev': 191.0, 'value': 545.0, 'precision': 'exact'}] |
| vac_for_sale | 3 | 3 | [{'unit_id': '6248', 'year': 2020, 'prev': 40.0, 'value': 270.0, 'precision': 'exact'}, {'unit_id': '1024', 'year': 2022, 'prev': 237.0, 'value': 24.0, 'precision': 'exact'}] |
| bevnat_divorces | 3 | 2 | [{'unit_id': '2701', 'year': 2000, 'prev': 534.0, 'value': 211.0, 'precision': 'exact'}, {'unit_id': '351', 'year': 2000, 'prev': 502.0, 'value': 183.0, 'precision': 'exact'}] |
| ent_jobs_education | 3 | 3 | [{'unit_id': '5214', 'year': 2021, 'prev': 475.0, 'value': 162.0, 'precision': 'exact'}, {'unit_id': '6623', 'year': 2022, 'prev': 171.0, 'value': 424.0, 'precision': 'exact'}] |
| ent_jobs_women | 3 | 3 | [{'unit_id': '5412', 'year': 2020, 'prev': 404.0, 'value': 1813.0, 'precision': 'exact'}, {'unit_id': '3021', 'year': 2024, 'prev': 529.0, 'value': 1373.0, 'precision': 'exact'}] |
| crime_stgb_property | 3 | 3 | [{'unit_id': '66', 'year': 2011, 'prev': 1622.0, 'value': 707.0, 'precision': 'exact'}, {'unit_id': '2703', 'year': 2012, 'prev': 632.0, 'value': 1300.0, 'precision': 'exact'}] |
| agr_workers | 3 | 2 | [{'unit_id': '4446', 'year': 2015, 'prev': 260.0, 'value': 41.0, 'precision': 'exact'}, {'unit_id': '1146', 'year': 2025, 'prev': 261.0, 'value': 49.0, 'precision': 'exact'}] |
| agr_horses | 3 | 2 | [{'unit_id': '6248', 'year': 2013, 'prev': 375.0, 'value': 8.0, 'precision': 'exact'}, {'unit_id': '6248', 'year': 2012, 'prev': 16.0, 'value': 375.0, 'precision': 'exact'}] |
| nat_outside_europe | 3 | 1 | [{'unit_id': '6621', 'year': 2020, 'prev': 806.0, 'value': 237.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2015, 'prev': 331.0, 'value': 768.0, 'precision': 'exact'}] |
| mfz_cars_bev | 3 | 2 | [{'unit_id': '3101', 'year': 2023, 'prev': 245.0, 'value': 898.0, 'precision': 'exact'}, {'unit_id': '86', 'year': 2018, 'prev': 251.0, 'value': 576.0, 'precision': 'exact'}] |
| tax_np_normal_taxable_class_1_30k | 3 | 3 | [{'unit_id': '843', 'year': 2021, 'prev': 1381.0, 'value': 674.0, 'precision': 'exact'}, {'unit_id': '584', 'year': 2021, 'prev': 824.0, 'value': 309.0, 'precision': 'exact'}] |
| gws_dw_2001plus | 3 | 3 | [{'unit_id': '131', 'year': 2011, 'prev': 353.0, 'value': 988.0, 'precision': 'exact'}, {'unit_id': '5583', 'year': 2020, 'prev': 581.0, 'value': 1212.0, 'precision': 'exact'}] |
| sh_recipients | 2 | 2 | [{'unit_id': '131', 'year': 2008, 'prev': 708.0, 'value': 345.0, 'precision': 'exact'}, {'unit_id': '1632', 'year': 2008, 'prev': 87.0, 'value': 306.0, 'precision': 'exact'}] |
| tax_np_taxpayers_normal | 2 | 1 | [{'unit_id': '3790', 'year': 2022, 'prev': 1078.0, 'value': 528.0, 'precision': 'exact'}, {'unit_id': '3790', 'year': 2021, 'prev': 530.0, 'value': 1078.0, 'precision': 'exact'}] |
| bil_pop_jan | 2 | 2 | [{'unit_id': '4536', 'year': 1999, 'prev': 3120.0, 'value': 1456.0, 'precision': 'exact'}, {'unit_id': '4741', 'year': 1995, 'prev': 2021.0, 'value': 908.0, 'precision': 'exact'}] |
| bevnat_births | 2 | 2 | [{'unit_id': '352', 'year': 1983, 'prev': 463.0, 'value': 91.0, 'precision': 'exact'}, {'unit_id': '363', 'year': 1983, 'prev': 0.0, 'value': 248.0, 'precision': 'exact'}] |
| bil_pop_dec | 2 | 2 | [{'unit_id': '4536', 'year': 1999, 'prev': 3082.0, 'value': 1476.0, 'precision': 'exact'}, {'unit_id': '4741', 'year': 1995, 'prev': 2119.0, 'value': 925.0, 'precision': 'exact'}] |
| bil_pop_foreign_jan | 2 | 2 | [{'unit_id': '564', 'year': 2007, 'prev': 303.0, 'value': 37.0, 'precision': 'exact'}, {'unit_id': '4741', 'year': 1995, 'prev': 338.0, 'value': 106.0, 'precision': 'exact'}] |
| gws_heat_oil | 2 | 2 | [{'unit_id': '4001', 'year': 2025, 'prev': 1551.0, 'value': 763.0, 'precision': 'exact'}, {'unit_id': '3271', 'year': 2025, 'prev': 1126.0, 'value': 478.0, 'precision': 'exact'}] |
| mig_intracant_out_foreign | 2 | 1 | [{'unit_id': '56', 'year': 2017, 'prev': 849.0, 'value': 323.0, 'precision': 'exact'}, {'unit_id': '56', 'year': 2016, 'prev': 337.0, 'value': 849.0, 'precision': 'exact'}] |
| nat_women | 2 | 1 | [{'unit_id': '6621', 'year': 2015, 'prev': 485.0, 'value': 1233.0, 'precision': 'exact'}, {'unit_id': '6621', 'year': 2020, 'prev': 1182.0, 'value': 563.0, 'precision': 'exact'}] |
| gws_dw_rooms_1_2 | 2 | 2 | [{'unit_id': '5061', 'year': 2013, 'prev': 923.0, 'value': 225.0, 'precision': 'exact'}, {'unit_id': '5633', 'year': 2014, 'prev': 144.0, 'value': 410.0, 'precision': 'exact'}] |
| gws_heat_none | 2 | 2 | [{'unit_id': '5226', 'year': 2024, 'prev': 61.0, 'value': 288.0, 'precision': 'exact'}, {'unit_id': '5192', 'year': 2024, 'prev': 114.0, 'value': 321.0, 'precision': 'exact'}] |
| mig_emigration_swiss | 2 | 1 | [{'unit_id': '6487', 'year': 2013, 'prev': 442.0, 'value': 42.0, 'precision': 'exact'}, {'unit_id': '6487', 'year': 2012, 'prev': 50.0, 'value': 442.0, 'precision': 'exact'}] |
| gws_heat_other | 2 | 2 | [{'unit_id': '6205', 'year': 2022, 'prev': 300.0, 'value': 1.0, 'precision': 'exact'}, {'unit_id': '3871', 'year': 2022, 'prev': 1.0, 'value': 215.0, 'precision': 'exact'}] |
| ent_jobs_accommodation | 1 | 1 | [{'unit_id': '1505', 'year': 2017, 'prev': 83.0, 'value': 284.0, 'precision': 'exact'}] |
| crime_stgb_offences | 1 | 1 | [{'unit_id': '2703', 'year': 2012, 'prev': 869.0, 'value': 1837.0, 'precision': 'exact'}] |
| agr_workers_fulltime | 1 | 1 | [{'unit_id': '1146', 'year': 2025, 'prev': 236.0, 'value': 23.0, 'precision': 'exact'}] |
| bevnat_marriages | 1 | 1 | [{'unit_id': '352', 'year': 1983, 'prev': 236.0, 'value': 24.0, 'precision': 'exact'}] |
| agr_area_permanent_crops_ha | 1 | 1 | [{'unit_id': '5861', 'year': 2023, 'prev': 15.0, 'value': 254.0, 'precision': 'exact'}] |
| mig_intercant_in_swiss | 1 | 1 | [{'unit_id': '4040', 'year': 2025, 'prev': 186.0, 'value': 403.0, 'precision': 'exact'}] |
| gws_dw_rooms_3 | 1 | 1 | [{'unit_id': '5192', 'year': 2012, 'prev': 3671.0, 'value': 11549.0, 'precision': 'exact'}] |
| gws_heat_electric | 1 | 1 | [{'unit_id': '6205', 'year': 2022, 'prev': 39.0, 'value': 416.0, 'precision': 'exact'}] |
| gws_bld_1946_1980 | 1 | 1 | [{'unit_id': '6087', 'year': 2015, 'prev': 185.0, 'value': 442.0, 'precision': 'exact'}] |
| mfz_cars_private | 1 | 1 | [{'unit_id': '905', 'year': 2025, 'prev': 641.0, 'value': 1435.0, 'precision': 'exact'}] |
| gws_bld_2011plus | 1 | 1 | [{'unit_id': '261', 'year': 2011, 'prev': 0.0, 'value': 273.0, 'precision': 'exact'}] |
| gws_bld_mfh | 1 | 1 | [{'unit_id': '5061', 'year': 2013, 'prev': 688.0, 'value': 271.0, 'precision': 'exact'}] |
| gws_bld_sfh | 1 | 1 | [{'unit_id': '5061', 'year': 2013, 'prev': 157.0, 'value': 562.0, 'precision': 'exact'}] |
| gws_dw_area_lt60 | 1 | 1 | [{'unit_id': '5633', 'year': 2014, 'prev': 135.0, 'value': 403.0, 'precision': 'exact'}] |
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
| crime_property_per_1000 | 16 | 2010 | 2025 | 37 / 2110 | – |
| crime_stgb_offences | 17 | 2009 | 2025 | 37 / 2110 | {'not_published': 126, 'not_covered': 1947} |
| crime_stgb_per_1000 | 16 | 2010 | 2025 | 37 / 2110 | – |
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
| fin_net_debt_per_capita | 36 | 1990 | 2025 | 462 / 2110 | {'not_covered': 1141, 'no_data': 505, 'not_applicable': 2} |
| fin_self_financing_ratio | 36 | 1990 | 2025 | 692 / 2110 | {'no_data': 460, 'not_applicable': 72, 'not_covered': 886} |
| fin_tax_revenue_chf | 36 | 1990 | 2025 | 165 / 2110 | {'no_data': 160, 'not_covered': 1785} |
| fin_tax_revenue_per_capita | 16 | 2010 | 2025 | 165 / 2110 | – |
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
| haz_residents_assessed | 1 | 2026 | 2026 | 1651 / 2110 | {'no_data': 119, 'not_covered': 340} |
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
| land_price_m2 | 52 | 1974 | 2025 | 30 / 2110 | {'no_data': 192, 'not_covered': 1864, 'suppressed': 24} |
| land_price_model_m2 | 51 | 1974 | 2024 | 160 / 2110 | {'not_covered': 1950} |
| land_transactions | 52 | 1974 | 2025 | 62 / 2110 | {'no_data': 160, 'not_covered': 1864, 'suppressed': 24} |
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
| nrw_ballots_blank | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_ballots_changed | 14 | 1971 | 2023 | 2040 / 2110 | {'no_data': 70} |
| nrw_ballots_invalid | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_ballots_unchanged | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_ballots_valid | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_eligible | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_fw_bdp | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_csp | 14 | 1971 | 2023 | 119 / 2110 | {'not_applicable': 1986, 'no_data': 5} |
| nrw_fw_cvp | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_edu | 14 | 1971 | 2023 | 1499 / 2110 | {'no_data': 5, 'not_applicable': 606} |
| nrw_fw_evp | 14 | 1971 | 2023 | 1818 / 2110 | {'no_data': 5, 'not_applicable': 287} |
| nrw_fw_fdp | 14 | 1971 | 2023 | 2078 / 2110 | {'not_applicable': 27, 'no_data': 5} |
| nrw_fw_fga | 14 | 1971 | 2023 | 160 / 2110 | {'not_applicable': 1945, 'no_data': 5} |
| nrw_fw_fps | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_glp | 14 | 1971 | 2023 | 2040 / 2110 | {'not_applicable': 65, 'no_data': 5} |
| nrw_fw_gruene | 14 | 1971 | 2023 | 2040 / 2110 | {'no_data': 5, 'not_applicable': 65} |
| nrw_fw_ldu | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_lega | 14 | 1971 | 2023 | 100 / 2110 | {'not_applicable': 2005, 'no_data': 5} |
| nrw_fw_lps | 14 | 1971 | 2023 | 3 / 2110 | {'not_applicable': 2102, 'no_data': 5} |
| nrw_fw_mcr | 14 | 1971 | 2023 | 45 / 2110 | {'not_applicable': 2060, 'no_data': 5} |
| nrw_fw_mitte | 14 | 1971 | 2023 | 2098 / 2110 | {'no_data': 5, 'not_applicable': 7} |
| nrw_fw_other | 14 | 1971 | 2023 | 1941 / 2110 | {'no_data': 5, 'not_applicable': 164} |
| nrw_fw_pda | 14 | 1971 | 2023 | 802 / 2110 | {'not_applicable': 1303, 'no_data': 5} |
| nrw_fw_poch | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_psa | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_rep | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_sd | 14 | 1971 | 2023 | 644 / 2110 | {'not_applicable': 1461, 'no_data': 5} |
| nrw_fw_sep | 14 | 1971 | 2023 | 0 / 2110 | {'not_applicable': 2105, 'no_data': 5} |
| nrw_fw_sol | 14 | 1971 | 2023 | 369 / 2110 | {'not_applicable': 1736, 'no_data': 5} |
| nrw_fw_sp | 14 | 1971 | 2023 | 2043 / 2110 | {'not_applicable': 62, 'no_data': 5} |
| nrw_fw_svp | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_fw_total | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
| nrw_share_bdp | 3 | 2011 | 2019 | 1600 / 2110 | – |
| nrw_share_csp | 13 | 1971 | 2023 | 119 / 2110 | – |
| nrw_share_cvp | 13 | 1971 | 2019 | 2081 / 2110 | – |
| nrw_share_edu | 13 | 1975 | 2023 | 1499 / 2110 | – |
| nrw_share_evp | 14 | 1971 | 2023 | 1818 / 2110 | – |
| nrw_share_fdp | 14 | 1971 | 2023 | 2078 / 2110 | – |
| nrw_share_fga | 12 | 1979 | 2023 | 160 / 2110 | – |
| nrw_share_fps | 6 | 1987 | 2007 | 488 / 2110 | – |
| nrw_share_glp | 5 | 2007 | 2023 | 2040 / 2110 | – |
| nrw_share_gruene | 13 | 1975 | 2023 | 2040 / 2110 | – |
| nrw_share_ldu | 8 | 1971 | 1999 | 759 / 2110 | – |
| nrw_share_lega | 9 | 1991 | 2023 | 100 / 2110 | – |
| nrw_share_lps | 14 | 1971 | 2023 | 3 / 2110 | – |
| nrw_share_mcr | 5 | 2007 | 2023 | 45 / 2110 | – |
| nrw_share_mitte | 1 | 2023 | 2023 | 2098 / 2110 | – |
| nrw_share_other | 14 | 1971 | 2023 | 1941 / 2110 | – |
| nrw_share_pda | 14 | 1971 | 2023 | 802 / 2110 | – |
| nrw_share_poch | 6 | 1971 | 1991 | 3 / 2110 | – |
| nrw_share_psa | 6 | 1971 | 1991 | 100 / 2110 | – |
| nrw_share_rep | 5 | 1971 | 1987 | 205 / 2110 | – |
| nrw_share_sd | 14 | 1971 | 2023 | 644 / 2110 | – |
| nrw_share_sep | 7 | 1975 | 2003 | 328 / 2110 | – |
| nrw_share_sol | 8 | 1995 | 2023 | 369 / 2110 | – |
| nrw_share_sp | 14 | 1971 | 2023 | 2043 / 2110 | – |
| nrw_share_svp | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_turnout | 14 | 1971 | 2023 | 2105 / 2110 | – |
| nrw_unchanged_share | 13 | 1975 | 2023 | 2105 / 2110 | – |
| nrw_voters | 14 | 1971 | 2023 | 2105 / 2110 | {'no_data': 5} |
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
| pup_compulsory | 24 | 2001 | 2024 | 205 / 2110 | {'not_covered': 1745, 'no_data': 160} |
| pup_compulsory_per_1000 | 15 | 2010 | 2024 | 205 / 2110 | – |
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
| unemp_per_100_20_64 | 16 | 2010 | 2025 | 45 / 2110 | – |
| unemp_registered | 39 | 1990 | 2026-10 | 87 / 2110 | {'suppressed': 213, 'no_data': 205, 'not_covered': 1605} |
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

- STATPOP population vs. demographic balance stock at 31 Dec: 31892 of 33760 within 0.1% — worst: [{'unit_id': '6011', 'period': '2010', 'value_a': 80.0, 'value_b': 102.0}, {'unit_id': '5399', 'period': '2019', 'value_a': 802.0, 'value_b': 640.0}, {'unit_id': '5399', 'period': '2016', 'value_a': 819.0, 'value_b': 655.0}]
- Persons in private households vs. STATPOP population (institutions explain the gap): 29386 of 29540 within 10.0% — worst: [{'unit_id': '5407', 'period': '2012', 'value_a': 2423.0, 'value_b': 3988.0}, {'unit_id': '5407', 'period': '2015', 'value_a': 2674.0, 'value_b': 4224.0}, {'unit_id': '5407', 'period': '2013', 'value_a': 2594.0, 'value_b': 4096.0}]
- GWS dwellings vs. dwelling stock in the vacancy count (stock = GWS of the previous year): 30310 of 31650 within 5.0% — worst: [{'unit_id': '6009', 'period': '2015', 'value_a': 477.0, 'value_b': 263.0}, {'unit_id': '5061', 'period': '2013', 'value_a': 1469.0, 'value_b': 2033.0}, {'unit_id': '1219', 'period': '2015', 'value_a': 516.0, 'value_b': 335.0}]
- Land area (swissBOUNDARIES3D, without lakes) vs. land-use statistics total area: 0 of 0 within 5.0% — worst: []
