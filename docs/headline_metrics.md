# Headline metrics (proposal for review)

Decision D24: these are shown first per theme in the metric picker and are loaded at start (`latest/<level>/core.json`, 259 KB gzipped at municipality level). All other metrics stay under **All metrics** and in search. Edit `pipeline/headline_metrics.yaml` to change the list.

67 metrics. ‡ = source still held back by the licence check (appears once cleared).

**Geography & identity:** Population density (persons per km² land area) ‡; Mean elevation (m a.s.l.) ‡; Lake share of area (%) ‡

**Population & demography:** Population (persons); Population change (10 years) (%); Share aged 65+ (%); Old-age dependency ratio (65+ per 100 aged 20–64); Live births per 1000 residents (per 1000)

**Migration & nationality:** Foreign nationals (share) (%); Net migration rate (per 1000 residents); Naturalisations per 100 foreign residents (per 100 foreign residents)

**Language & religion:** German main language (share, census) (%); French main language (share, census) (%); Italian main language (share, census) (%); Roman Catholic (share, census) (%)

**Households & family:** Average household size (persons per household); One-person households (share) (%); Married (share of residents) (%)

**Economy & jobs:** Jobs per 1000 residents (per 1000 residents); Change in jobs (10 years) (%); Share of jobs in the tertiary sector (%); Cross-border commuters per 100 jobs (per 100 jobs)

**Income & tax:** Mean taxable income per taxpayer (CHF); Share of taxpayers with taxable income above CHF 100 (%); Federal income tax yield per resident (CHF per resident); Tax burden: single, CHF 80,000 (% of gross income) ‡; Tax burden: married, one income, 2 children, CHF 100,000 (% of gross income) ‡

**Public finances:** Net debt per resident* (CHF per resident) ‡; Self-financing ratio* (%) ‡

**Housing & buildings:** Vacancy rate (%); Second-home share (%); Single-family houses (share of buildings) (%); Buildings built 2001 or later (share) (%); Buildings heated by heat pump (share) (%); New dwellings per 1000 residents (per 1000 residents)

**Real estate prices:** Residential building land price* (CHF per m²) ‡

**Land use & built environment:** Settlement area (share) (%); Wooded area (share) (%); Building-zone area per inhabitant (m² per inhabitant)

**Mobility & accessibility:** Public transport to the nearest hub (min); Car to the nearest hub (min); Residents with good or very good PT (class A or B) (% of residents); Passenger cars per 1000 residents (per 1000); Battery-electric share of cars (%); Distance to the nearest supermarket (m) ‡

**Energy & climate:** Electric car share (% of passenger cars); Solar potential used (%); Solar PV capacity per resident (kWp per resident); Renewable heating share (% of heated buildings); Mean annual temperature (where people live) (°C)

**Environment & hazards:** NO₂ exposure (population-weighted annual mean) (µg/m³) ‡; Share of residents in red or blue hazard zones* (%); Share of area in BLN landscapes (%)

**Health & social:** Social assistance rate (%); Mean health insurance premium (adults) (CHF per month) ‡

**Education:** Share with tertiary education (25–64) (%); Matura (baccalaureate) by age 25 (%)

**Safety:** Injury accidents per 1000 residents (per 1000 residents) ‡; Criminal Code offences per 1000 residents* (per 1000 residents) ‡

**Politics:** Turnout (federal vote) (%); Yes share (%); Turnout (National Council) (%); Party strength SVP (National Council) (%); Party strength SP (National Council) (%); Party strength FDP (National Council) (%); Party strength Mitte (National Council) (%); Party strength Grüne (National Council) (%)

**Hidden from the picker** (D28 and technical denominators): `bil_births`, `bil_birth_rate`, `area_settlement_base_ha`, `air_hectare_residents`, `acc_population`, `haz_hectare_residents`, `gk_population`, `edu_imputation_share`
