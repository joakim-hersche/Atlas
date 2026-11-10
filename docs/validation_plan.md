# Data plausibility sweep (plan)

Owner request (2026-11-09, decision D13): run a detailed data validation sweep that checks the plausibility of every metric, including whether municipalities add up to cantons and to Switzerland.

**When:** at the end of Phase 3, once the datasets are ingested and harmonized, and before Checkpoint 3. The same checks then run on every rebuild (`make validate`) and in the monthly refresh. Failures block a release, warnings go into `docs/quality_report.md`.

The backbone checks (crosswalk, population/votes/jobs totals after reprojection) already exist in `docs/backbone_report.md`. This sweep extends them to every metric.

## 1. Additivity: do the parts add up?

For every count metric (`aggregation = sum`) and every year:

| Check | Compared with | Tolerance |
|---|---|---|
| Σ municipalities = district | our district aggregate and the published district value, where one exists | exact for full counts; ≤ 0.5% where the source suppresses or rounds small cells |
| Σ municipalities = canton | the canton value **published by the source** (e.g. PxWeb canton rows, vote canton results) | as above |
| Σ cantons = Switzerland | the national value published by the source | as above |
| Σ other levels (agglomeration, language region, …) = Switzerland | the national total, after allowing for municipalities outside any unit | exact |

Known, explained differences are listed rather than flagged: canton transfers reprojected to current boundaries (Moutier BE→JU, Clavaleyres BE→FR), pseudo-units (Swiss abroad in votes), STATENT small-cell protection (values < 4 set to 4), suppressed cells.

For ratios (`ratio:num/den`), the parts must reproduce the published canton/national ratio, e.g. the vacancy rate and the social assistance rate.

## 2. Ranges and definitions

- Shares within 0–100%; rates and counts ≥ 0; parts ≤ totals (e.g. foreigners ≤ population, yes + no ≤ valid ≤ ballots ≤ eligible).
- Components sum to their total (age groups = population, sectors = jobs, land-use classes = area within 1 ha).
- Implausible per-capita values flagged against bounds per metric (e.g. jobs per resident > 20 only for known business hubs).

## 3. Change over time

- Year-on-year jumps > 5 SD of the metric's own history, or > 50% for counts above a size threshold, are flagged.
- Each flag is checked against a known cause: merger, method break (census → STATPOP 2010, GWS heating 2021, CVP+BDP → Mitte 2021), or source revision. Unexplained jumps are raised with the owner.

## 4. Cross-source consistency

- The same quantity from two sources agrees: STATPOP population vs. the population used by ESTV, the vote register and the Regionalporträts; STATENT jobs vs. PxWeb sector totals; GWS dwellings vs. the vacancy count's dwelling stock; area from swissBOUNDARIES3D vs. land-use statistics.
- Our reprojection vs. BFS's own, where BFS publishes both (as in the backbone report).

## 5. Spatial plausibility

- Outliers relative to neighbouring municipalities (local Moran / neighbour z-score), reviewed manually for the largest 20 per metric.
- Coverage maps for partial and `*` metrics; check that the coverage label matches the data.

## 6. Coverage and completeness

- Every current municipality has a value or an explicit reason (suppressed, not covered, not applicable) for every metric and year.
- Every row in every source maps to a municipality or is logged as unmapped.

## Output

- `docs/quality_report.md`: per metric, pass/warn/fail for each check, with the largest discrepancies listed.
- Spot-check sample: 20 municipalities (largest cities, smallest municipalities, recent mergers, canton changers, enclaves) compared by hand against the official source pages.
