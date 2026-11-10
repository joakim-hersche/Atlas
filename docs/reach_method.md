# Reach (travel time) data: method and results

Build everything with one command: `uv run python -m pipeline.reach.run`. A single hub can be rebuilt with `... run zuerich`. The full run takes about 3 minutes once the inputs are cached; the one-off GTFS preparation adds about 1 minute.

## Outputs
- `data/interim/reach/travel_times.parquet` has 211,000 rows: 20 hubs × 2,110 municipalities × 5 methods.
  - Methods: `gtfs_rcsa_mainstation` and `gtfs_rcsa_popweighted` (towards the hub, D31, shown in the app), `gtfs_csa_station` and `gtfs_csa_popweighted` (hub-outward, kept for the drawing and comparison), `npvm2023_ttc_popweighted` (car).
  - Columns: `hub`, `mode`, `bfs_nr`, `minutes`, `status`, `method`, plus `minutes_incl_wait`, `pop_share_with_stop`, `pop_share_no_car_access`, and for the main-station rows `main_station`, `main_didok`, `main_inside`, `minutes_p10`, `minutes_p90`, `window_start_min`.
  - `minutes` is filled only when `status == ok`; otherwise it is NaN and the status gives the reason (D21).
- `data/out/reach/<hub>_<mode>.json` holds the growing-network lines, 40 files in total. `data/out/reach/index.json` lists the files and their sizes.
- `data/interim/reach/validation.json` holds the spot checks and the GTFS-vs-NPVM agreement.
- Intermediates:
  - `gtfs_20261117/` contains stations, connections, footpaths and trips.
  - `pt_station_times/<hub>.parquet`
  - NPVM hub rows
  - hectare links
- Code is in `pipeline/reach/`: `gtfs_prep`, `csa`, `pt`, `npvm`, `draw`, `hubs`, `run`.
- Connectors with `fetch.py` and `meta.yaml`: `pipeline/sources/otd_gtfs`, `are_npvm` and `bav_rail`. The swissTLMRegio download is in `pipeline/reach/fetch.py` (source id `swisstopo_tlmregio`).

## Public transport towards the hub (D31) — the figures shown in the app
Reviewers compared the hub-outward times with the SBB app and did not trust them (review round 1). Since
2026-11-10 the app shows two figures, both **towards** the hub for **morning arrivals**:

- **Station time** (`reach_ptst_<hub>`, method `gtfs_rcsa_mainstation`): timetable journey from the
  municipality's *main station* to the hub station.
- **Door to door** (`reach_pt_<hub>`, method `gtfs_rcsa_popweighted`): each inhabited STATPOP 2025
  hectare walks (straight line × 1.3, 1.2 m/s) to the best served stop within 1.5 km — the minimum over
  stops of walk + that stop's median journey — and the municipality value is the population-weighted
  median over hectares.

**Reverse scan.** `csa.Network.run_reverse()` is the reverse Connection Scan: for one arrival deadline T
at the hub it scans the connections by descending departure time and returns, for every station, the
latest departure LD(T) that still reaches the hub by T (same rules as the forward scan: minimum change
time at the boarding station, footpaths without change time, in-seat transfers, board/alight flags;
footpaths relaxed once). It runs for every deadline minute 06:00–10:30 (271 runs per hub, about 1 s).
The journey for deadline T actually arrives at the earliest deadline T_a ≤ T with LD(T_a) = LD(T);
**journey time = T_a − LD(T)**, as a journey planner shows it (no initial wait, no wait at the hub).
The value is the **median over the 61 deadlines 07:30–08:30**; deadlines before the earliest possible
arrival have no journey and are left out. Where the hub cannot be reached by 08:30 at all (far hubs:
the first trains of the day arrive later), the hour from the earliest possible arrival is used if
that is by 10:30, and the note says so ("no arrival by 08:30: median over the hour from 08:55");
otherwise the pair has no value ("no arrival at the hub by 10:30"). P10 and P90 over the same
deadlines are stored (`minutes_p10`, `minutes_p90`). Connections are kept from 04:30 for this
(`gtfs_prep.EARLIEST_DEP`); a stop counts as served with a departure or arrival 06:30–18:00 as before.

**Main station.** Among the served stations inside the municipality (reference polygon), the one with
the most rail departures 06:30–18:00 on the service day; a municipality without a rail station takes
the stop with the most departures of any mode. A municipality with no served stop inside takes the
station chosen the same way within 2 km of its population-weighted centre (`main_inside = false`, 37
municipalities); 7 have none (status `no stop within 2 km`: Häutligen, Oberthal, Oberhünigen,
Schelten, Seehof, Ochlenberg BE and Blatten VS). Their door-to-door value exists except for Schelten,
Seehof and Blatten, which have no served stop within 1.5 km of any inhabited hectare. Examples: Zürich → Zürich HB (1,007 rail departures), Oberweningen → the bus stop
"Oberweningen, Im Hüebli" (the S-Bahn station Schöfflisdorf-Oberweningen lies in Schöfflisdorf).
For a hub's own municipality the station time is 0.

**Blatten VS** (6192): the village was destroyed by the May 2025 landslide. The 2026 GTFS feed has no
stop in the municipality, while STATPOP 2025 still lists 302 residents on 28 hectares, so both
figures are missing with the reason "village destroyed by the landslide of May 2025; no public
transport service in the 2026 timetable".

**Spot checks (station time, median; P10–P90 in brackets; door to door after the slash):**

| From → hub | Station time | Door to door | Expected |
|---|---|---|---|
| Winterthur → Zürich HB | 20 (19–28) | 37 | 20–25 |
| Basel SBB → Zürich HB | 53 (53–69) | 74 | ~55 |
| Liestal → Basel SBB | 11 (10–16) | 25 | 10–15 |
| Zug → Zürich HB | 26 (24–35) | 41 | ~25 |
| Bern → Zürich HB | 57 (56–60) | 76 | 56–60 |
| Oberweningen → Zürich HB | 36 (36–36) | 39 | sensible (was 419 min before the best-stop fix) |

**Agreement with the NPVM PT matrix** (column = zone → hub zone, population-weighted like the car
values; 20 hubs, 40,473 pairs with a value in both, hub zones excluded):

| GTFS variant (towards hub) | r | median GTFS/NPVM | median diff | within ±15 % | within ±25 % |
|---|---|---|---|---|---|
| door to door | 0.985 | 0.95 | −6.5 min | 88 % | 98 % |
| station time | 0.980 | 0.91 | −12.9 min | 72 % | 91 % |

Per hub, r is 0.96–0.99 for door to door. The station time is shorter than NPVM by construction
(NPVM includes access and egress). Coverage: 40,491 of 42,200 pairs have a station time; 11,110 of
them use the late window (mostly far hubs such as Genève from eastern Switzerland); 1,569 pairs have
no arrival by 10:30.

## Public transport, hub-outward (D10) — growing lines and comparison
**Feed and day.**
- Feed: opentransportdata.swiss GTFS `gtfs_fp2026_20261107.zip`, timetable year 2026.
- Service day: **Tuesday 17 November 2026**.
  - No federal or cantonal holiday falls on it, and it is outside school holidays.
  - It runs 190,968 trips. Other Tuesdays to Thursdays in Nov–Dec 2026 run 186.6k–193.4k; 8 Dec, a Catholic holiday, runs 180.9k.
- The 2027 timetable starts on 13 Dec 2026. The reach data should be rebuilt on a 2027 feed, using a January or March day, once the app ships after that date.

**Network.**
- All modes are included: rail, tram, bus, boat and cableway. Frequency-based trips (frequencies.txt) are expanded at their headway. This gives 203,977 trips and 1,963,071 elementary connections departing 06:30–18:00.
- Platforms are collapsed onto their parent station. There are 32,297 stations, 23,306 of them in Switzerland; each station has exactly one didok number.
- **Minimum change time per station** comes from transfers.txt, in this order:
  1. the station-level rule (7,198 stations);
  2. otherwise the median of the platform-to-platform rules (1,136);
  3. otherwise the same-platform rules, at least 120 s (206);
  4. otherwise the default of 120 s (23,757).
  - Values are capped at 900 s, because one stop carries a rule of 5,940 s.
  - Examples: Zürich HB 7 min, Bern 6 min. Winterthur gets 30 s, which is what the feed states.
- **Transfer rules.** In-seat transfers (transfer_type 4) are honoured. Trip-specific guaranteed-transfer rules (≈700k rows) are not used, which makes the results slightly conservative.
- **Footpaths.**
  - Stations within 400 m are linked, with walk time = straight-line distance × 1.3 ÷ 1.2 m/s. Station-to-station rules in transfers.txt override this (5,524 pairs).
  - A station with no neighbour within 400 m is linked to its nearest station within 1 km (11,780 links). Without this, some cableway valley stations would be cut off; Illgau is one.
  - Footpaths are relaxed once (not transitively closed). pickup_type and drop_off_type = 1 are respected.
- **Algorithm.** The Connection Scan Algorithm (earliest arrival) is implemented in numba (`csa.py`). It takes about 20 ms per run.
- **Hubs** are their main rail station, given as didok number and GTFS station id `Parentch:1:sloid:<n>`:

| Hub | didok | Hub | didok |
|---|---|---|---|
| Zürich HB | 8503000 | Lugano | 8505300 |
| Bern | 8507000 | Bellinzona | 8505213 |
| Basel SBB | 8500010 | Chur | 8509000 |
| Genève (Cornavin) | 8501008 | Biel/Bienne | 8504300 |
| Lausanne | 8501120 | Fribourg/Freiburg | 8504100 |
| Luzern | 8505000 | Sion | 8501506 |
| St. Gallen | 8506302 | Zug | 8502204 |
| Winterthur | 8506000 | Aarau | 8502113 |
| Olten | 8500218 | Neuchâtel | 8504221 |
| Schaffhausen | 8503424 | Thun | 8507100 |

  Tram and bus stops near each hub are reached over the footpaths.

**Travel time.**
- One CSA run is made per departure minute from 07:30 to 08:30 (61 departures), and the median is taken.
- The `minutes` value is the **journey time as a journey planner shows it**: arrival minus the latest departure from the hub that still arrives at the same time. Departures are scanned up to 09:30 to find it. It therefore excludes the wait at the hub for the next train.
- `minutes_incl_wait` is the median of arrival minus the departure minute. It includes the wait, which averages half the headway.

Two methods are stored:
- `gtfs_csa_station`: the earliest arrival at **any station inside the municipality**. Stations are assigned to the 2026-01-01 polygon by point-in-polygon. There is no access or egress walk. 44 municipalities have no stop inside them and get status `no stop in municipality`.
- `gtfs_csa_popweighted`: each populated STATPOP 2025 hectare uses the **best station within 1.5 km** (minimum over stations of walk + station time; since 2026-11-10, before that the nearest station). Only stations with service between 06:30 and 18:00 count. Walk time = straight-line distance × 1.3 ÷ 1.2 m/s. The municipality value is the **population-weighted median** over hectares of each hectare's median journey time.
  - 3 municipalities have no station in reach and get status `no PT within walking distance`: Schelten BE, Seehof BE, and Blatten VS (no service after the 2025 landslide).
  - `pop_share_with_stop` gives the share of residents covered: median 1.00, mean 0.98.

## Car (D11)
- The source is the ARE NPVM 2023 matrix `4_TTC_PW_NPVM_2023` ("Reisezeit PW (TTC)"), Zenodo doi:10.5281/zenodo.23009199, CC-BY-4.0.
- The data sheet says all matrices are for the **average weekday (DWV)**.
- It does **not** say whether the times are congested. TTC is the skim of the DWV (whole-day) assignment, so it most likely reflects day-average loaded-network times, not the peak hour. This is my inference and is unverified. Peak-hour (MSP) states exist only as VISUM files.
- **Hub zone** = the NPVM zone polygon that contains the hub's station. For example, Zürich HB is in zone 26101201.
- **Municipality value** = the population-weighted mean of the zone times.
  - NPVM ships no zone population; its structural data are on SWISSUbase behind registration. Weights are therefore **STATPOP 2025 hectares**.
  - Each hectare centre is placed by point-in-polygon both in its NPVM zone and in its **2026 reference municipality**. Boundary changes from the 2023 zone state are handled spatially, without the 2023 ids. This is equivalent to `to_vintage` with `weighted_mean:population`, but exact where a zone is split by a merger.
  - The intrazonal time is not in the matrix and is set to 0 for the hub zone.
  - All 2,110 municipalities have values. The matrix gives times even to car-free resorts such as Zermatt, presumably to the zone's road connector.
- Stored as `method = npvm2023_ttc_popweighted`.

## Growing lines (5.1)
- One compact JSON per hub and mode: `{"hub","name","mode","unit":"min","segments":[[t_start,t_end,kind,[lon,lat,...]],...]}`.
  - Coordinates are WGS84, rounded to 5 decimals.
  - kind codes: 0 = road, 1 = rail, 2 = bus/boat/cableway (straight line), 3 = walk.
  - The frontend interpolates t linearly along each segment's length.
- **PT lines.**
  - They come from the CSA journey tree at a *representative departure*: the minute whose station journey times are closest to the per-station medians. For example, this is 07:59 for Zürich and 07:34 for Genève.
  - The tree is restricted to the journeys to each municipality's earliest-reached station.
  - Rail, tram and funicular legs follow the **BAV Schienennetz**. Stations are projected onto every Netzsegment within 150 m, and the shortest path is taken on the segment graph. In the Zürich tree, 99.3% of rail legs matched; the misses are funiculars, which are absent from the network.
  - Bus, boat and cableway legs are straight lines, simplified to 25 m.
  - PT segment times count from the departure minute, so they include the wait at the hub. The `minutes` values exclude that wait.
- **Car lines.**
  - They come from a shortest-path tree on the swissTLMRegio 2026 roads. Footpaths and banned roads are excluded.
  - Assumed speeds (km/h, drawing only):
    - Autobahn 110; motorway ramps 60
    - Autostrasse 90 (ramps 50)
    - Hauptstrasse 70 (≥6 m) / 60
    - Verbindungsstrasse 60 / 50
    - Nebenstrasse 40 / 30
    - Fahrsträsschen 20
  - The tree is pruned to the paths to each municipality's centroid node (2,088 anchors).
  - Edge times are then **rescaled to the NPVM car times** by iterative proportional fitting. Each edge gets a multiplier equal to the mean target/current ratio of the anchors downstream of it (6 passes). Times stay monotone along every path.
  - Residual at the anchors: mean absolute error 2.7–3.8 min, 90th percentile 6–8 min.
  - Chains with the same speed are merged into polylines and simplified to 40 m.
- **Sizes.**
  - PT files: 612–641 KB raw, **169–179 KB gzipped**.
  - Car files: 584–612 KB raw, **200–208 KB gzipped**.
  - All 40 files are under the 300 KB gzip target, 7.5 MB gzipped in total.

## Validation (hub-outward)
**Spot checks** (median journey time, with the fastest in brackets):
- Zürich HB → Bern: **56 min** (56); expected about 56.
- Zürich HB → Basel SBB: **53** (52); expected about 53.
- Genève → Lausanne: **43** (39); expected 33–40. On 17 Nov 2026 the feed's fastest train (IC1) takes 39 min. The median mixes IC, IR (39–46 min) and RE (51 min).
- Other checks, using the station method:
  - Zürich → Luzern 41, Chur 75, Lugano 113, St. Gallen 60 (to any St. Gallen station)
  - Bern → Lausanne 69, Genève 111
  - Basel → Bern 58
  - Bellinzona → Lugano 14

**Comparison with the NPVM PT matrix** (RITA+ACT+EGT, population-weighted like the car matrix), over 20 hubs × 2,107 municipalities = 42,140 pairs, against GTFS `gtfs_csa_popweighted`:

| GTFS variant | r | median GTFS/NPVM | median diff | within ±15% | within ±25% |
|---|---|---|---|---|---|
| journey time (`minutes`) | 0.962 | 0.97 | −4.4 min | 88% | 96% |
| incl. wait (`minutes_incl_wait`) | 0.923 | 1.115 | +16.7 min | 64% | 83% |

- Per hub, r ranges from 0.92 to 0.98, and the median ratio from 0.90 (Zürich) to 1.01 (Genève).
- The NPVM time is a model value (access/egress over zone connectors, a daily-average timetable), so ±15% agreement is about what can be expected.

## Limitations
- **Hub wait.** Journey times exclude the wait at the hub, as in timetables; the variant that includes it is stored too. The line animation includes the wait for the representative departure, so line times and card values can differ by a few minutes.
- **Transfer rules.** Trip-specific transfer rules are not used. The minimum change time is per station, not per platform pair. Footpaths are straight-line × 1.3 and are not transitively closed.
- **Station method.** It uses the earliest station anywhere in the municipality. For large municipalities this can be a small outlying stop; the population-weighted method is the better "typical resident" figure.
- **Access to stops.** Walking access uses the best served stop within 1.5 km (straight line × 1.3); real walking paths and slopes are not modelled.
- **Feed date.** The single date and feed version (2026-11-07) contain whatever construction works were planned for that day (Genève–Lausanne is slower than usual). ToU 5.2: state the feed version in the app.
- **Car times.** NPVM car times are average-weekday model times, and congestion handling is unconfirmed (see above). The hectare weights are 2025 population, while the zones are from 2023.
- **Car drawing.** The car drawing is illustrative.
  - swissTLMRegio includes foreign main roads, so some trees route through France or Italy; for example, Genève → Valais runs along the south shore of Lake Geneva.
  - Car-train shuttles (Lötschberg, Furka, Vereina) are not in the road graph.
  - The rescaling leaves a few minutes of residual at the municipality centroids.
- **PT drawing.** Bus, boat and cableway legs are straight lines, including long PostAuto legs over passes. Funiculars are not in the Schienennetz and are drawn straight.
- **Missing package.** scipy is not installed. Neighbour searches use a numpy grid and shapely STRtree, so no extra package is needed.
