# Data quality report

Generated 2026-11-09T23:14 · reference state 2026-01-01 · regenerate with `make quality`. Plan: [`validation_plan.md`](validation_plan.md).

Metrics: 567 defined (401 base, 166 derived) · rows: 5,650,312

## A. Additivity — municipalities vs. published district/canton/national values

| Source | Level | Metric | Compared | Exact | Explained (transfers / unallocated) | Within 0.5% | Fail | Max rel. residual |
|---|---|---|---|---|---|---|---|---|
| bfs_vehicles | kanton | mfz_cars_diesel | 416 | 192 | 16 | 111 | **97** | 25.818% |
| bfs_vehicles | kanton | mfz_cars | 416 | 192 | 16 | 130 | **78** | 32.140% |
| bfs_vehicles | kanton | mfz_cars_hev | 416 | 215 | 16 | 112 | **73** | 52.334% |
| bfs_vehicles | kanton | mfz_cars_bev | 416 | 243 | 11 | 91 | **71** | 45.882% |
| bfs_vehicles | kanton | mfz_cars_phev | 416 | 259 | 4 | 86 | **67** | 65.933% |
| bfs_vehicles | kanton | mfz_newreg_cars | 416 | 216 | 16 | 121 | **63** | 13.733% |
| bfs_vehicles | kanton | mfz_cars_petrol | 416 | 192 | 16 | 149 | **59** | 29.058% |
| bfs_vehicles | kanton | mfz_newreg_bev | 416 | 301 | 3 | 58 | **54** | 17.297% |
| bfs_vehicles | kanton | mfz_cars_private | 260 | 48 | 4 | 172 | **36** | 18.293% |
| bfs_vehicles | schweiz | mfz_newreg_bev | 16 | 8 | 0 | 0 | **8** | 1.915% |
| bfs_vehicles | schweiz | mfz_cars_diesel | 16 | 7 | 0 | 2 | **7** | 1.440% |
| bfs_vehicles | schweiz | mfz_newreg_cars | 16 | 8 | 0 | 1 | **7** | 0.897% |
| bfs_vehicles | schweiz | mfz_cars_hev | 16 | 8 | 0 | 5 | **3** | 2.452% |
| bfs_vehicles | schweiz | mfz_cars | 16 | 0 | 0 | 14 | **2** | 1.115% |
| bfs_vehicles | schweiz | mfz_cars_bev | 16 | 8 | 0 | 6 | **2** | 2.147% |
| bfs_vehicles | schweiz | mfz_cars_petrol | 16 | 0 | 0 | 14 | **2** | 0.792% |
| bfs_vehicles | schweiz | mfz_cars_phev | 16 | 8 | 0 | 6 | **2** | 3.127% |
| bfs_vehicles | schweiz | mfz_cars_private | 10 | 0 | 0 | 9 | **1** | 0.699% |
| bfe_energy | kanton | en_charging_spots | 834 | 815 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_ecar_count | 1592 | 1592 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_elec_consumption_mwh | 978 | 978 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_heat_nonrenewable_count | 1592 | 1592 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_heat_renewable_count | 1592 | 1592 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_pv_installed_kwp | 1592 | 1592 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_renelec_hydro_mwh | 858 | 858 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_renelec_production_mwh | 858 | 858 | 0 | 0 | 0 | 0.000% |
| bfe_energy | kanton | en_renelec_solar_mwh | 858 | 858 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_charging_spots | 34 | 33 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_ecar_count | 66 | 66 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_elec_consumption_mwh | 40 | 40 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_heat_nonrenewable_count | 66 | 66 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_heat_renewable_count | 66 | 66 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_pv_installed_kwp | 66 | 66 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_renelec_hydro_mwh | 35 | 32 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_renelec_production_mwh | 35 | 32 | 0 | 0 | 0 | 0.000% |
| bfe_energy | schweiz | en_renelec_solar_mwh | 35 | 32 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | bezirk | bevnat_births | 8151 | 4191 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | bezirk | bevnat_divorces | 7886 | 964 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | bezirk | bevnat_marriages | 8150 | 2324 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | kanton | bevnat_births | 1482 | 462 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | kanton | bevnat_divorces | 1477 | 110 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | kanton | bevnat_marriages | 1482 | 305 | 0 | 0 | 0 | 0.000% |
| bfs_bevnat_sdmx | schweiz | bevnat_births | 57 | 0 | 0 | 0 | 0 | nan% |
| bfs_bevnat_sdmx | schweiz | bevnat_divorces | 57 | 0 | 0 | 0 | 0 | nan% |
| bfs_bevnat_sdmx | schweiz | bevnat_marriages | 57 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | bezirk | hh_persons | 2002 | 1988 | 14 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size1 | 2002 | 1970 | 6 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size2 | 2002 | 1981 | 6 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size3 | 2002 | 1867 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size4 | 2002 | 1803 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size5 | 2002 | 1533 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_size6plus | 2002 | 886 | 0 | 0 | 0 | 0.000% |
| bfs_households | bezirk | hh_total | 2002 | 1988 | 14 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_persons | 364 | 336 | 28 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size1 | 364 | 318 | 20 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size2 | 364 | 329 | 20 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size3 | 364 | 260 | 10 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size4 | 364 | 260 | 6 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size5 | 364 | 199 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_size6plus | 364 | 123 | 0 | 0 | 0 | 0.000% |
| bfs_households | kanton | hh_total | 364 | 336 | 28 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_persons | 14 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_size1 | 14 | 2 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_size2 | 14 | 4 | 0 | 0 | 0 | 0.000% |
| bfs_households | schweiz | hh_size3 | 14 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_size4 | 14 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_size5 | 14 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_size6plus | 14 | 0 | 0 | 0 | 0 | nan% |
| bfs_households | schweiz | hh_total | 14 | 14 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_0_19 | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_20_64 | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_65_79 | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_age_80plus | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_divorced | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_female | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_foreign | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_male | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_married | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_nonpermanent | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_single | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_swiss | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_total | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | bezirk | pop_widowed | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_0_19 | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_20_64 | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_65_79 | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_age_80plus | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_divorced | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_female | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_foreign | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_male | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_married | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_nonpermanent | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_single | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_swiss | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_total | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | kanton | pop_widowed | 416 | 384 | 32 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_0_19 | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_20_64 | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_65_79 | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_age_80plus | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_divorced | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_female | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_foreign | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_male | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_married | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_nonpermanent | 16 | 12 | 4 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_single | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_swiss | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_total | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_statpop | schweiz | pop_widowed | 16 | 16 | 0 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_bev | 2288 | 2275 | 13 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_diesel | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_hev | 2288 | 2271 | 16 | 1 | 0 | 0.175% |
| bfs_vehicles | bezirk | mfz_cars_petrol | 2288 | 2272 | 16 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_phev | 2288 | 2278 | 10 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_cars_private | 1430 | 1420 | 10 | 0 | 0 | 0.000% |
| bfs_vehicles | bezirk | mfz_newreg_bev | 2288 | 2277 | 9 | 2 | 0 | 0.389% |
| bfs_vehicles | bezirk | mfz_newreg_cars | 2288 | 2271 | 16 | 1 | 0 | 0.091% |
| geo_identity | kanton | geo_area_land_ha | 26 | 24 | 0 | 2 | 0 | 0.161% |
| geo_identity | schweiz | geo_area_land_ha | 1 | 0 | 0 | 1 | 0 | 0.014% |

Worst unexplained differences:

- bfs_vehicles / kanton / mfz_cars: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 22228.0, 'value_agg': 15084.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 23677.0, 'value_agg': 18288.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 61702.0, 'value_agg': 59291.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_bev: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 595.0, 'value_agg': 322.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2025', 'value_pub': 3078.0, 'value_agg': 2765.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2024', 'value_pub': 2426.0, 'value_agg': 2193.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_diesel: [{'unit_id': 'AI', 'period': '2019', 'value_pub': 8409.0, 'value_agg': 6238.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2022', 'value_pub': 5958.0, 'value_agg': 4573.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2019', 'value_pub': 19059.0, 'value_agg': 17946.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_hev: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 2356.0, 'value_agg': 1123.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 614.0, 'value_agg': 428.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 2948.0, 'value_agg': 2673.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_petrol: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 12265.0, 'value_agg': 8701.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 14463.0, 'value_agg': 11459.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 38390.0, 'value_agg': 37457.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_phev: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 1045.0, 'value_agg': 356.0, 'explained': 0.0}, {'unit_id': 'AI', 'period': '2019', 'value_pub': 97.0, 'value_agg': 70.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 762.0, 'value_agg': 686.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_cars_private: [{'unit_id': 'AI', 'period': '2022', 'value_pub': 12852.0, 'value_agg': 10501.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2022', 'value_pub': 50167.0, 'value_agg': 49634.0, 'explained': 0.0}, {'unit_id': 'ZG', 'period': '2022', 'value_pub': 61985.0, 'value_agg': 61346.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_newreg_bev: [{'unit_id': 'NE', 'period': '2024', 'value_pub': 688.0, 'value_agg': 569.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2024', 'value_pub': 651.0, 'value_agg': 558.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2023', 'value_pub': 654.0, 'value_agg': 561.0, 'explained': 0.0}]
- bfs_vehicles / kanton / mfz_newreg_cars: [{'unit_id': 'BS', 'period': '2022', 'value_pub': 2716.0, 'value_agg': 2343.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2024', 'value_pub': 2812.0, 'value_agg': 2455.0, 'explained': 0.0}, {'unit_id': 'BS', 'period': '2023', 'value_pub': 3000.0, 'value_agg': 2633.0, 'explained': 0.0}]
- bfs_vehicles / schweiz / mfz_cars: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 4732121.0, 'value_agg': 4679346.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 4642358.0, 'value_agg': 4603753.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_cars_bev: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 108110.0, 'value_agg': 105789.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 26807.0, 'value_agg': 26630.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_cars_diesel: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 1323421.0, 'value_agg': 1304358.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 1390822.0, 'value_agg': 1372354.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2018', 'value_pub': 1379193.0, 'value_agg': 1368945.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_cars_hev: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 220328.0, 'value_agg': 214925.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 84892.0, 'value_agg': 84077.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2018', 'value_pub': 68769.0, 'value_agg': 68399.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_cars_petrol: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 2998464.0, 'value_agg': 2974723.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 3106071.0, 'value_agg': 3087253.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_cars_phev: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 66048.0, 'value_agg': 63983.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2019', 'value_pub': 16444.0, 'value_agg': 16315.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_cars_private: [{'unit_id': 'CH', 'period': '2022', 'value_pub': 4126791.0, 'value_agg': 4097939.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_newreg_bev: [{'unit_id': 'CH', 'period': '2018', 'value_pub': 5066.0, 'value_agg': 4969.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2023', 'value_pub': 52333.0, 'value_agg': 51649.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2022', 'value_pub': 39868.0, 'value_agg': 39441.0, 'explained': -0.0}]
- bfs_vehicles / schweiz / mfz_newreg_cars: [{'unit_id': 'CH', 'period': '2023', 'value_pub': 250293.0, 'value_agg': 248048.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2018', 'value_pub': 297007.0, 'value_agg': 294419.0, 'explained': -0.0}, {'unit_id': 'CH', 'period': '2024', 'value_pub': 237562.0, 'value_agg': 235566.0, 'explained': -0.0}]

## B. Ranges

All shares within 0–100, no negative counts.

## C. Year-on-year jumps (> 50% and > 200 units)

| Metric | Flags | Series | Largest |
|---|---|---|---|
| pop_nonpermanent | 76 | 2110 | [{'unit_id': '261', 'year': 2022, 'prev': 3560.0, 'value': 7598.0, 'precision': 'exact'}, {'unit_id': '2701', 'year': 2022, 'prev': 2332.0, 'value': 4718.0, 'precision': 'exact'}] |
| mfz_newreg_cars | 23 | 2110 | [{'unit_id': '3101', 'year': 2018, 'prev': 412.0, 'value': 20256.0, 'precision': 'exact'}, {'unit_id': '247', 'year': 2018, 'prev': 7387.0, 'value': 1451.0, 'precision': 'exact'}] |
| mfz_newreg_bev | 7 | 2110 | [{'unit_id': '3101', 'year': 2023, 'prev': 338.0, 'value': 1005.0, 'precision': 'exact'}, {'unit_id': '69', 'year': 2025, 'prev': 270.0, 'value': 724.0, 'precision': 'exact'}] |
| mfz_cars_diesel | 6 | 2110 | [{'unit_id': '3101', 'year': 2018, 'prev': 1710.0, 'value': 7961.0, 'precision': 'exact'}, {'unit_id': '1702', 'year': 2018, 'prev': 7378.0, 'value': 3508.0, 'precision': 'exact'}] |
| mfz_cars | 6 | 2110 | [{'unit_id': '3101', 'year': 2018, 'prev': 5390.0, 'value': 18360.0, 'precision': 'exact'}, {'unit_id': '6253', 'year': 2011, 'prev': 3662.0, 'value': 7808.0, 'precision': 'exact'}] |
| mfz_cars_hev | 6 | 2110 | [{'unit_id': '3101', 'year': 2023, 'prev': 954.0, 'value': 4039.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2021, 'prev': 675.0, 'value': 2255.0, 'precision': 'exact'}] |
| mfz_cars_petrol | 6 | 2110 | [{'unit_id': '3101', 'year': 2018, 'prev': 3589.0, 'value': 10124.0, 'precision': 'exact'}, {'unit_id': '6240', 'year': 2011, 'prev': 4496.0, 'value': 1169.0, 'precision': 'exact'}] |
| mfz_cars_phev | 4 | 2110 | [{'unit_id': '3101', 'year': 2023, 'prev': 326.0, 'value': 969.0, 'precision': 'exact'}, {'unit_id': '3101', 'year': 2020, 'prev': 57.0, 'value': 519.0, 'precision': 'exact'}] |
| mfz_cars_bev | 3 | 2110 | [{'unit_id': '3101', 'year': 2023, 'prev': 245.0, 'value': 898.0, 'precision': 'exact'}, {'unit_id': '86', 'year': 2018, 'prev': 251.0, 'value': 576.0, 'precision': 'exact'}] |
| bevnat_divorces | 3 | 2110 | [{'unit_id': '2701', 'year': 2000, 'prev': 534.0, 'value': 211.0, 'precision': 'exact'}, {'unit_id': '351', 'year': 2000, 'prev': 502.0, 'value': 183.0, 'precision': 'exact'}] |
| bevnat_births | 2 | 2110 | [{'unit_id': '352', 'year': 1983, 'prev': 463.0, 'value': 91.0, 'precision': 'exact'}, {'unit_id': '363', 'year': 1983, 'prev': 0.0, 'value': 248.0, 'precision': 'exact'}] |
| bevnat_marriages | 1 | 2106 | [{'unit_id': '352', 'year': 1983, 'prev': 236.0, 'value': 24.0, 'precision': 'exact'}] |
| mfz_cars_private | 1 | 2110 | [{'unit_id': '905', 'year': 2025, 'prev': 641.0, 'value': 1435.0, 'precision': 'exact'}] |

## D. Coverage (municipality level, latest period)

| Metric | Periods | First | Latest | With value | Gap reasons |
|---|---|---|---|---|---|
| acc_bicycle_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_fatal_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_injury_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_injury_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_motorcycle_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_nonmotorway_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_nonmotorway_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_pedestrian_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_severe_count | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_severe_per_1000 | 15 | 2011 | 2025 | 2110 / 2110 | – |
| acc_severe_share | 15 | 2011 | 2025 | 1762 / 2110 | – |
| bevnat_birth_rate | 16 | 2010 | 2025 | 1829 / 2110 | – |
| bevnat_births | 57 | 1969 | 2025 | 1829 / 2110 | {'suppressed': 281} |
| bevnat_divorce_rate | 16 | 2010 | 2025 | 1300 / 2110 | – |
| bevnat_divorces | 57 | 1969 | 2025 | 1300 / 2110 | {'suppressed': 810} |
| bevnat_marriage_rate | 16 | 2010 | 2025 | 1563 / 2110 | – |
| bevnat_marriages | 57 | 1969 | 2025 | 1563 / 2110 | {'suppressed': 547} |
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
| en_charging_spots | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_ecar_count | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_ecar_share | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_elec_consumption_mwh | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_elec_consumption_per_capita | 40 | 2023-05 | 2026-10 | 2110 / 2110 | – |
| en_heat_nonrenewable_count | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_heat_renewable_count | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_heat_renewable_share | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_pv_installed_kwp | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_pv_kwp_per_capita | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_renelec_hydro_mwh | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_renelec_per_capita | 35 | 2023-10 | 2026-10 | 2110 / 2110 | – |
| en_renelec_production_mwh | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_renelec_solar_mwh | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_solar_potential_used | 66 | 2021-03 | 2026-10 | 2110 / 2110 | – |
| en_solar_roof_facade_potential_gwh | 1 | 2025 | 2025 | 2110 / 2110 | – |
| en_solar_roof_potential_gwh | 1 | 2025 | 2025 | 2110 / 2110 | – |
| energiestadt_gold | 1 | 2026 | 2026 | 2110 / 2110 | – |
| energiestadt_label | 1 | 2026 | 2026 | 2110 / 2110 | – |
| energiestadt_score | 1 | 2026 | 2026 | 465 / 2110 | {'not_applicable': 1645} |
| geo_area_lake_ha | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_area_land_ha | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_area_total_ha | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_elev_max | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_elev_mean | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_elev_median | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_elev_min | 1 | 2026 | 2026 | 2110 / 2110 | – |
| geo_lake_share | 17 | 2010 | 2026 | 2110 / 2110 | – |
| geo_pop_density | 16 | 2010 | 2025 | 2110 / 2110 | – |
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
| mfz_bev_share | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_bev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_diesel | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_hev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_per_1000 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_petrol | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_phev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_private | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_cars_private_per_1000 | 10 | 2016 | 2025 | 2110 / 2110 | – |
| mfz_newreg_bev | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_newreg_bev_share | 16 | 2010 | 2025 | 2098 / 2110 | – |
| mfz_newreg_cars | 16 | 2010 | 2025 | 2110 / 2110 | – |
| mfz_plugin_share | 16 | 2010 | 2025 | 2110 / 2110 | – |
| old_age_dependency | 16 | 2010 | 2025 | 2110 / 2110 | – |
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
| share_age_0_19 | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_age_65plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_age_80plus | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_divorced | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_foreign | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_married | 16 | 2010 | 2025 | 2110 / 2110 | – |
| share_women | 16 | 2010 | 2025 | 2110 / 2110 | – |
| youth_dependency | 16 | 2010 | 2025 | 2110 / 2110 | – |
| zw_dwellings_total | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_primary_dwellings | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_second_home_share | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_second_homes | 18 | 2016-12 | 2026-10 | 2110 / 2110 | – |
| zw_subject_to_law | 16 | 2019-03 | 2026-10 | 2110 / 2110 | – |

## E. Cross-source consistency

- STATPOP population vs. demographic balance stock at 31 Dec: not run (metric missing)
- STATPOP population vs. population used in tax statistics: not run (metric missing)
- GWS dwellings vs. dwelling stock in the vacancy count: not run (metric missing)
