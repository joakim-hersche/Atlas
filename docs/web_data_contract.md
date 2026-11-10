# Web data contract, round-1 fixes (pipeline → frontend)

Status: **contract for the round-1 defect fixes** (review_round1.md, D31, D32). Written before the
pipeline changes so that the frontend can start in parallel. All changes **add** fields; no existing
field is renamed or removed. Where a field keeps its name but its *meaning* changes, it is marked
**⚠ meaning changes**. Files live in `data/out/web/` and are copied to `web/public/data/web/` by
`web/scripts/copy-data.mjs`.

Conventions: unit indices are positions in the file's `units` array, as today; JSON object keys for
indices are strings. "null" means the field is absent or null when it does not apply.

---

## 1. `metrics.json` (array of metric objects) — new fields per metric

| field | type | meaning |
|---|---|---|
| `label_fr` | string \| null | French label, from `pipeline/i18n/labels.yaml` (research agent; 783 entries) |
| `unit_de`, `unit_fr` | string \| null | unit in German / French (same source); `unit` stays as in metrics.yaml (English) |
| `latest` | string | **⚠ meaning changes (F):** the *default* period = the newest period with near-complete coverage (rule below). Was: newest period with any value |
| `latest_available` | string | newest period with any value at any level (≥ `latest`) |
| `incomplete_periods` | object \| null | periods newer than `latest` with incomplete coverage: `{"2020/25": {"n": 1007, "of": 2110, "level": "gemeinde", "label_en": "incomplete: 1,007 of 2,110 municipalities", "label_de": "unvollständig: 1'007 von 2'110 Gemeinden"}}`. Still in `periods` and in `series/<id>.json` (year slider) |
| `coverage` | string | **⚠ meaning changes (G):** computed from the data shipped for `latest`, same format as before: `"national"` or `"partial:AG,BE,..."` (cantons with data). A canton counts as covered when ≥ 50 % of its municipalities have a value or a suppressed/not-applicable status |
| `native_level` | string | level the source publishes at (`gemeinde`, `bezirk`, `kanton`, `arbeitsmarktgebiet`, …); values of a metric whose native level is above the municipality are regional values (D21), e.g. tax burden by labour-market area `taxb_amr_*` |
| `coverage_meta` | string | the coverage stated in metrics.yaml (old meaning of `coverage`) |
| `coverage_detail` | object | `{"level": "gemeinde", "period": "2025", "n": 45, "of": 2110, "n_cantons": 1}` for `latest` at the lowest level with values |
| `unavailable_levels` | object \| null | `{level: reason_en}` for levels without values, with the real reason, e.g. `"published only at district level (Structural Survey)"`, `"median: cannot be aggregated; no published value at this level"` (D) |
| `reliability` | object \| null | small-number rule (J): `{"count": "<metric id>"\|null, "base": "<metric id>"\|null, "min_count": 20, "min_base": 1000, "rule_en": "...", "rule_de": "..."}`. Units failing it carry flag bit 1/2 in the latest columns (section 3) |
| `pooled` | object \| null | for pooled rates (J): `{"of": "<annual metric id>", "years": 3}`; periods look like `"2023-2025"` |
| `majority_cantons` | object \| null | party shares, blocs and leaning only (D37; not turnout): `{"2023": ["AI","AR","GL","NW","OW","UR"], ...}` cantons with one seat (majority election, Majorz) per election year, from BFS cube px-x-1702020000_103 (seats = 1): UR, OW, NW, GL, AI 1971–2023, AR 2003–2023. Units in them carry flag bit 4 |
| `keywords` | string \| null | D37: search words (full party names DE/FR/IT/EN, e.g. "Grünliberale Partei · Vert'libéraux (PVL)") |
| `until` | number \| null | D37: former party, last election it stood in (picker groups these last, label "(until YYYY)") |
| `vote_index` | string \| null | per-vote metrics only: `"votes/index.json"` (B) |
| `latest_title` | object \| null | per-vote metrics only: title of the `latest` vote `{de, fr, it, en}` — use instead of `#6870` (K) |
| `source` | string | unchanged meaning (source id for the sources page). Car metrics now point to `are_npvm`; PT metrics to `reach_metrics` (computed by Gemeindebank from the `otd_gtfs` timetable) (K) |
| `description` | string \| null | unchanged; texts added/clarified for lake share, area, vacancy, BEV shares, out-commuting (C, E, K) |

**Default-period rule (F, revised by D37 and the all-data audit).** One default period per metric,
used at every level. It is chosen on the metric's primary level (its native level, else the lowest
level with values) by covered units: coverage(p) = units with status `ok`, `not_applicable` (party did
not stand), `majority_election` or `suppressed` in period p. Starting from the newest period with any
value, the default steps back while a period has fewer than 95 % of the units of the period before it
(an incomplete newer round: Arealstatistik 2020/25 with 1,007 of 2,110 → 2013/18). A level without a
value for the default period ships an explicit gap column (status `no_data`, note "no value for P at
this level (newest here: Q)") instead of an older year. `latest` ≠ `latest_available` means the newest
period is incomplete; the legend says so. Per-vote metrics: the newest vote. Audit numbers per build
in `data/out/web/default_periods.json` (2026-11-10: metric×level defaults not equal to the newest period
at that level 284 → 161; metrics with different defaults across levels 60 → 0).

**Precision.** Arealstatistik metrics (`area_*`) are now `"survey"` (sample points), not exact (F).

**New metrics** (all in the normal files and series):

| id | level(s) | meaning |
|---|---|---|
| `reach_ptst_<hub>` (20) | gemeinde | **station time towards the hub** (D31 headline figure), minutes. See section 4 |
| `reach_ptst_nearest_hub` | gemeinde | min over hubs of the station time |
| `reach_pt_<hub>` | gemeinde | **⚠ meaning changes (D31):** door-to-door *towards* the hub (was: from the hub outwards) |
| `reach_pt_nearest_hub` | gemeinde | **⚠** min over hubs of the door-to-door time towards the hub |
| `com_leave_unit_share` | all levels | share of employed residents working **outside the unit** (municipality, district, canton, labour-market area, …), from the origin–destination commuter matrix (E) |
| `com_leave_unit` | all levels | count behind it |
| `bevnat_birth_rate_3y`, `bil_net_migration_rate_3y`, `sh_rate_3y` | all levels | pooled 3-year rates (J) |
| `geo_area_total_ha`, `geo_area_lake_ha` at kanton/schweiz | kanton, schweiz | now include lakes outside municipalities (C) |

`com_out_share` keeps its values; its label becomes "Out-commuter share (working outside own
municipality)" at every level (E). `geo_lake_share` is relabelled "Lake area inside the municipal
boundary (share)" (C). Header area for the profile: use **`geo_area_land_ha`** ("Land area, without
lakes"); `geo_area_total_ha` is "Total area incl. lakes" (C).

## 2. `units.json` — new fields (H)

Typology units (levels `grossregion`, `sprachgebiet`, `agglomeration`, `arbeitsmarktgebiet`,
`stadt_land`, `gemeindetyp`) get
`"names": {"de": "Französisch", "fr": "Français", "it": "Francese", "en": "French"}` — the official
BFS labels from the register's spatial-level tables (agvchapp `levels`, columns `<CODE>_de/_fr/_it/_en`).
`name` stays the German label. A label not delivered by BFS in a language is absent from `names`
(nothing is translated by us). The municipality rows keep the codes (`"sprachgebiet": "2"`); look up
the name in the unit of that level.

## 3. `latest/<level>/<file>.json` — new optional fields per column

```jsonc
{"level": "kanton", "units": [...], "status_codes": {...}, "precision_codes": {...},
 "flag_bits": {"small_base": 1, "small_count": 2, "majority_election": 4, "published_value": 8,
               "provisional": 16},
 "metrics": {"edu_share_tertiary": {
    "period": "2023", "v": [...], "s": {...}, "p": {...},
    "f": {"3": 8},                     // NEW: per-unit flag bitmask (absent = no flag)
    "n": {"3": 0, "7": 1},             // NEW: per-unit index into "notes"
    "notes": ["published canton value; municipal values incomplete (3 of 352 suppressed)",
              "3 of 51 municipalities suppressed (small numbers)"]}}}
```

- `n`/`notes` (D): the reason for a gap, or the provenance of a fallback value. Shown in the card
  instead of the generic status text when present. Gaps at higher levels now carry the real reason
  ("N of M municipalities suppressed", "survey published only at district level", "party did not
  stand", "counted with another municipality in the BFS results", …) instead of "no data for this year".
- Bit 8 `published_value` (D): the value is the source's published value for the unit (provenance
  native) because the sum of municipalities is incomplete.
- Bits 1/2 (J): unstable small-number value (base below `min_base`, count below `min_count`). Suggest
  showing a "small numbers" marker; hiding is optional.
- Bit 4 (A): NRW value in a majority-election canton (single seat); label "majority election
  (single seat): party shares not comparable with proportional cantons".
- Bit 16: provisional value (e.g. federal vote of 2026-09-27 from voteinfo, `provisorisch: true`).
- **D37 status `majority_election` (6)** and **`m`** `{unit index: value}`: a party share, bloc or
  leaning value of a single-seat canton (UR, OW, NW, GL, AI; AR from 2003) at municipality, district
  or canton level. `v` is null there, so classes, ranks, histograms, statistics, correlations and
  regressions leave it out; the value is in `m` (card, profile). The frontend's "include single-seat
  cantons" toggle (hash `mj=1`) merges `m` into `v`. Bit 4 is set on every row of those canton-years
  (also where the party did not stand). Regions and typologies are computed from proportional cantons
  only (note "proportional-representation cantons only: excludes k of n municipalities …"); a region of
  single-seat cantons only gets status 6. Switzerland includes them, as BFS (note says so).
- Status `not_applicable` (5) now marks "party did not stand" for the party-share ratios in
  municipalities/districts/cantons where the party had no list (A); these are gaps, not 0 %.
- **Ties (C, frontend):** values are unchanged; the classifier should give exact zeros (or the
  modal tie) their own class when they exceed a class width (e.g. lake share: 1,800 municipalities at 0).

`series/<id>.json` now also contains the incomplete newer periods and the pooled-rate periods. D37:
for metrics with `majority_cantons`, single-seat-canton values are null in `levels` and given in
`"m": {level: {unit: {period index: value}}}`, with `"f": {level: {unit: {period index: 4}}}` on every
row of those canton-years.

## 4. `reach_times.json` — new fields (I, D31)

```jsonc
{"units": [...2110 ids], "hubs": [["zuerich","Zürich HB"], ...], "service_date": "2026-11-17",
 "pt":  {"zuerich": [..]},        // ⚠ door-to-door TOWARDS the hub (was hub-outward)
 "pt_station": {"zuerich": [..]}, // NEW headline figure: main station -> hub station time
 "car": {"zuerich": [..]},        // unchanged
 "periods": {"pt": "2026", "car": "2026", "pt_station": "2026"},
 "main_station": [["Winterthur", 8506000, true], null, ...],   // NEW, per unit: name, didok, inside the municipality (null: no stop within 2 km)
 "methods": {                                                 // NEW one-line method texts
   "pt_station": {"en": "...", "de": "..."}, "pt": {"en": "...", "de": "..."}, "car": {"en": "...", "de": "..."}},
 "main_station_fields": ["name", "didok", "inside_municipality"],
 "reasons": {"pt": {"zuerich": {"<unit idx>": "no stop within walking distance (1.5 km) of where people live"}},  // NEW, per hub
             "pt_station": {"geneve": {"<unit idx>": "no arrival at the hub by 10:30 on the service day"}}, "car": {}},
 "late_from": {"pt_station": {"geneve": {"<unit idx>": "08:55"}}, "pt": {...}},   // value uses the hour from this earliest arrival
 "late_text": {"en": "No arrival by 08:30; median over the hour from the earliest possible arrival ({t}).", "de": "..."}}
```

- **Station time** (`pt_station`, metric `reach_ptst_<hub>`): timetable journey time from the
  municipality's *main station* to the hub station, for arrivals at the hub between 07:30 and 08:30
  on Tuesday 17 Nov 2026: for every arrival minute T, the latest departure that still arrives by T,
  journey = actual arrival − that departure (no initial wait, no wait at the hub); median over the
  61 arrival minutes. Main station = the station inside the municipality with the most rail
  departures 06:30–18:00 on the service day; if it has no rail station, the stop with the most
  departures of any mode. Hub municipalities: 0 for the hub's own station.
- **Door-to-door** (`pt`, metric `reach_pt_<hub>`): towards the hub, same arrival window; each
  inhabited hectare walks (straight line × 1.3, 1.2 m/s) to the best stop within 1.5 km (min over
  stops of walk + stop's median journey); population-weighted median over hectares.
- Far hubs: where the hub cannot be reached by 08:30 at all, the hour from the earliest possible
  arrival is used (if by 10:30) and `late_from` gives that time; otherwise the value is null with a reason.
  About 27 % of hub–municipality pairs use this later window, 4 % have no arrival by 10:30.
- Main station when the municipality has no stop: the station chosen the same way within 2 km of its
  population-weighted centre (`inside_municipality` false; 37 municipalities).
- The growing-lines files `reach/<hub>_<mode>.json` stay hub-outward and unchanged.

## 5. `votes/index.json` — NEW (B)

```jsonc
{"source": "bfs_votes_gemeinde", "generated": "2026-11-10",
 "cantons": ["ZH","BE",...],          // 26 codes, order for canton_yes_pct
 "half_cantons": ["OW","NW","BS","BL","AR","AI"],
 "votes": [{
   "id": "6870", "period": "2026-06-14#6870", "date": "2026-06-14",
   "title": {"de": "...", "fr": "...", "it": "...", "rm": "...", "en": "..."},  // only languages the source has
   "title_source": "voteinfo" | "pxweb_label",
   "yes_pct": 52.46, "turnout_pct": 58.26,      // national, ratio rule incl. Swiss abroad (pseudo-units)
   "yes": 1690622, "no": 1532160,
   "accepted": true | false | null,             // official flag (voteinfo, 1981+); null before
   "cantons_yes": 14.5, "cantons_no": 8.5, "cantons_total": 23,   // Ständemehr count, see below
   "canton_yes_pct": [56.1, 50.2, ...],         // aligned with "cantons"; null where the canton did not exist (JU before 1979)
   "provisional": false,
   "file": "votes/2026-06-14_6870.json"}]}
```

- National and canton values: yes/(yes+no), turnout = ballots/eligible, summed over municipalities
  **plus pseudo-units** (Swiss abroad, postal/other; D17), as BFS counts them.
- Ständemehr: derived from the canton results **as published for the canton territory at the vote
  date** (JU only from 1979): a canton accepts when yes > no; full cantons count 1, the six
  half-cantons ½; `cantons_total` = 22 before 1979, 23 after. Reported for every vote; whether a
  double majority was required is not asserted (`accepted` is the official outcome where known).
- `votes/<date>_<id>.json` keep their shape; canton BE and the BE districts are no longer blank, and
  `levels.schweiz` is filled.
- The latest vote in the BFS cube (checked 2026-11-10) is 2026-06-14. The 2026-09-27 vote is added
  from the voteinfo OGD file (provisional results, municipality state 2026-01-01), flagged `provisional`.

## 6. `sources.json` — new fields (K)

`fetched`: ISO date of the newest download recorded in `data/raw/<source>/manifest.jsonl`
(null if the source has no manifest); `status_text`: plain wording such as
"held back: licence not yet confirmed" instead of "UNVERIFIED" / "brief rule 5".
`excluded_sources.json` `note` uses the same plain wording.

## 7. Other files (added after the first version of this contract)

- `glossary.json` (copied to `web/public/data/web/glossary.json`): `pipeline/i18n/glossary.yaml` as JSON,
  `{key: {term_en, term_de, term_fr, en, de, fr}}` — plain-language explanations (quantile, P10/P90, …).
- `votes/index.json` and every `votes/<date>_<id>.json` are now copied by `copy-data.mjs`.
- Rents (`bfs_rents`, research agent): normal metrics; canton rows have `native_level` kanton, the
  3-/4-room city rents are partial municipality coverage (`coverage: "partial:..."`, 180 cities).
- `sources.json` rows also carry `status_note` where meta.yaml has one (e.g. STATPOP: definitive results).
- Tax burden (`bfs_tax_burden`, research agent): `taxb_city_*` for 179 cities (partial municipal coverage,
  tax years 2023–2024) and `taxb_amr_*` for the 101 labour-market areas (native level
  `arbeitsmarktgebiet`, 2010–2025, in `latest/arbeitsmarktgebiet/*.json` only). Headline: married couple
  with 2 children at CHF 100k and single at 80k (cities), and the two area series.
- `search.json`: postal-code rows with less than 0.5 % of a locality's addresses are left out (Riehen in 4058).

