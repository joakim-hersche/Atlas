# Checkpoint 2 — Backbone review

Status: **closed** (2026-11-09) — decisions D14–D21 in [`decisions.md`](decisions.md). Full numbers: [`backbone_report.md`](backbone_report.md) (regenerate with `make validate`).

## What was built

- **Municipality history engine** (`pipeline/backbone/`): every municipality version since 1848 (6,270 versions, 3,405 distinct BFS numbers) and every mutation (2,985; 2,686 since 1960), each typed: merger, split, territory exchange, rename, renumbering, district/canton reassignment.
- **Crosswalk** from any version to the reference state 2026-01-01 (decision D8). Mergers and renames get weight 1. Splits and territory exchanges get **population weights from the BFS hectare grid on the historized boundaries**, with the method recorded per row.
- **`to_vintage()`** reprojects any dataset (counts: sum; rates: weighted mean; medians: only where 1:1). **`aggregate()`** rolls municipalities up to districts, cantons, Grossregionen, language regions, agglomerations, labour market areas, urban/rural and municipality types.
- **Web geometry** (`data/out/geo/`): TopoJSON per level from BFS's generalized boundaries. Municipalities are 255 KB gzipped; districts 81 KB, cantons 56 KB. Lakes, a Liechtenstein/enclave context layer and label points are included.

## Coverage of the merger history

| Date | Municipalities |
|---|---|
| 1960-01-01 | 3,095 |
| 2000-01-01 | 2,899 |
| 2026-01-01 | 2,110 |

- Every version reaches the 2026 state (0 dead ends).
- 178 versions need weighted mappings (splits or territory exchanges). 93 of them were abolished since 1960.

## Validation results (all must-pass checks pass)

| Check | Result |
|---|---|
| Register vs. official API snapshot | 2,110 = 2,110 |
| Geometry for every current municipality | 0 missing |
| Crosswalk weights sum to 1 | all 6,314 versions |
| Crosswalk vs. BFS's official correspondence table 1960 → 2026 | 3,095 of 3,095 identical |
| Population 2010–2025: national totals preserved | exact, every year |
| Population vs. BFS's own re-projected STATPOP | 33,670 of 33,760 municipality-years identical; 11 municipalities differ, max 67 persons (Verzasca) |
| Federal votes 1981–2026 (12 votes): our reprojection vs. BFS's re-aggregation | 66,895 of 67,270 rows identical; national totals exact |
| Jobs (STATENT 2011, 2018, 2024): totals preserved | exact |

**Unmapped records:** none in population, jobs or votes. The only excluded rows are vote pseudo-units: Swiss abroad and postal-vote districts, BFS codes 9xxx, 4–36 rows per vote.

## Edge cases — decisions needed

1. **Where our reprojection and BFS's differ, which to show?** BFS publishes some series already re-projected (STATPOP, votes). They differ from ours only in 11 municipalities with splits or territory exchanges, by at most 67 persons.
   - **A (recommended):** use BFS's re-projection when one exists, and our engine for everything else. Our version stays as a cross-check in the quality report.
   - **B:** always use our engine, for one consistent method.
2. **Splits before 1991** (about 95 versions, mostly 19th century) are weighted with the 1990 population grid, the earliest available. This only affects long census series (1850–1980) in the few municipalities that were split.
   - **A (recommended):** keep it, labeled "1990 proxy".
   - **B:** use area weights instead.
   - **C:** don't reproject pre-1990 splits; show those series only where the mapping is 1:1.
3. **Canton changes in history.** Moutier (BE→JU, 2026) and Clavaleyres (BE→FR, 2022) are assigned to their current canton for all years. Past canton totals for BE/JU/FR therefore differ from the officially published ones, by about 7,000 persons for BE/JU.
   - **A (recommended):** keep consistent current boundaries everywhere (the project's principle) and add a note on canton pages.
   - **B:** use published canton totals at canton level, and accept that they don't add up from the municipalities.
4. **Vote pseudo-units** (Swiss abroad, postal-vote districts).
   - **A (recommended):** exclude them from the municipality map, but include them in canton and national results so these match the official ones.
   - **B:** exclude them everywhere.
5. **MS regions** (106 regions) are no longer valid at 2026 in the BFS register; their last edition is 2000-based. BFS's successor concept is labour market areas 2018, which are already included.
   - **A (recommended):** drop MS regions from v1.
   - **B:** include the 2000 edition, mapped onto current municipalities.
6. **Map geometry base.** BFS's generalized boundaries (G1) are used for the web. They are already simplified and small, and share their history ids with the register. swissBOUNDARIES3D (full resolution) is kept for area figures only.
   - **A (recommended):** keep it.
   - **B:** derive web geometry from swissBOUNDARIES3D.

The data-delivery format (TopoJSON vs. PMTiles) is decided at Checkpoint 3, as the brief says.

## Open from Checkpoint 1

7. **Cantonal hosts for the `*` sweep** (decisions D4–D6, D12). [`cantonal_sources.md`](cantonal_sources.md) lists 60 candidate hosts found by web search. Best leads:
   - ZH: land prices, unemployment, finances, burglaries per municipality, all as open data.
   - BL: HRM2 finances and land prices since 1979.
   - LU and SO: municipal finance tables.
   - SG: unemployment by municipality 2010–2026.
   - TG: pupils by school municipality.
   - geodienste.ch: cantonal hazard maps.

   Crime per municipality exists mostly as police PDF tables, not as data.
   - **A (recommended):** allow the hosts in one batch and run the sweep.
   - **B:** allow only the ~20 hosts with confirmed data files (ZH, BL, LU, SO, SG, TG, BS, GE, VD, geodienste.ch).
   - **C:** postpone.
