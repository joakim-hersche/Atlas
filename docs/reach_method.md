# Reach (travel time) data: method and results

Build everything with one command: `uv run python -m pipeline.reach.run`. A single hub can be rebuilt with `... run zuerich`. The full run takes about 3 minutes once the inputs are cached; the one-off GTFS preparation adds about 1 minute.

## Outputs
- `data/interim/reach/travel_times.parquet` has 126,600 rows: 20 hubs × 2,110 municipalities × 3 methods.
  - Columns: `hub`, `mode`, `bfs_nr`, `minutes`, `status`, `method`, plus `minutes_incl_wait`, `pop_share_with_stop` and `pop_share_no_car_access`.
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

## Public transport (D10)
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
- `gtfs_csa_popweighted`: each populated STATPOP 2025 hectare uses its **nearest station within 1.5 km**. Only stations with service between 06:30 and 18:00 count. Walk time = straight-line distance × 1.3 ÷ 1.2 m/s. The municipality value is the **population-weighted median** over hectares of each hectare's median journey time.
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

## Validation
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
- **Access to stops.** Walking access uses the *nearest* served stop, not the best one. A resident near a bus stop but 1.2 km from a station is counted via the bus stop.
- **Feed date.** The single date and feed version (2026-11-07) contain whatever construction works were planned for that day (Genève–Lausanne is slower than usual). ToU 5.2: state the feed version in the app.
- **Car times.** NPVM car times are average-weekday model times, and congestion handling is unconfirmed (see above). The hectare weights are 2025 population, while the zones are from 2023.
- **Car drawing.** The car drawing is illustrative.
  - swissTLMRegio includes foreign main roads, so some trees route through France or Italy; for example, Genève → Valais runs along the south shore of Lake Geneva.
  - Car-train shuttles (Lötschberg, Furka, Vereina) are not in the road graph.
  - The rescaling leaves a few minutes of residual at the municipality centroids.
- **PT drawing.** Bus, boat and cableway legs are straight lines, including long PostAuto legs over passes. Funiculars are not in the Schienennetz and are drawn straight.
- **Missing package.** scipy is not installed. Neighbour searches use a numpy grid and shapely STRtree, so no extra package is needed.
