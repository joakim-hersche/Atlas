# Reach (travel time) data: method and results

Build everything with one command: `uv run python -m pipeline.reach.run`. A single hub can be rebuilt with `... run zuerich`. The full run (21 hubs) takes about 7½ minutes once the inputs are cached (per hub: reverse scans on three days 11 s, forward scans 6 s, drawing the rest); the one-off GTFS preparation adds about 70 s per service day (three days).

## Outputs
- `data/interim/reach/travel_times.parquet` has 221,550 rows: 21 hubs × 2,110 municipalities × 5 methods.
  - Methods: `gtfs_rcsa_mainstation` and `gtfs_rcsa_popweighted` (towards the hub, D31, shown in the app), `gtfs_csa_station` and `gtfs_csa_popweighted` (hub-outward, kept for the drawing and comparison), `npvm2023_ttc_popweighted` (car).
  - Columns: `hub`, `mode`, `bfs_nr`, `minutes`, `status`, `method`, plus `minutes_incl_wait`, `pop_share_with_stop`, `pop_share_no_car_access`, and for the main-station rows `main_station`, `main_didok`, `main_inside`, `main_mode` (rail, bus, boat, tram, metro, cableway, funicular), `main_pop_share` (share of residents within 1.5 km of it), `minutes_p10`, `minutes_p90`, `window_start_min`, `minutes_by_day` (the station time on each of the three days).
  - `minutes` is filled only when `status == ok`; otherwise it is NaN and the status gives the reason (D21).
- `data/out/reach/<hub>_<mode>.json` holds the growing-network lines, 42 files in total. `data/out/reach/index.json` lists the files and their sizes, the hubs (with `nearest_set`) and the reverse-scan days.
- `data/interim/reach/validation.json` holds the spot checks and the GTFS-vs-NPVM agreement.
- Intermediates:
  - `gtfs_20261117/` contains stations, connections, footpaths and trips (also `gtfs_20261125/`, `gtfs_20261203/` for the reverse scans).
  - `pt_station_times/<hub>.parquet` (hub-outward), `pt_station_times_to_hub/<hub>.parquet` (towards the hub, median day plus each day's median)
  - NPVM hub rows
  - hectare links
- Code is in `pipeline/reach/`: `gtfs_prep`, `csa`, `pt`, `npvm`, `draw`, `hubs`, `spread`, `run`.
- Spread over the morning (P10/P90, both directions): `data/out/reach/spread.json`, `data/out/reach/<hub>_spread.json`, see the section below.
- Connectors with `fetch.py` and `meta.yaml`: `pipeline/sources/otd_gtfs`, `are_npvm` and `bav_rail`. The swissTLMRegio download is in `pipeline/reach/fetch.py` (source id `swisstopo_tlmregio`).

## Hubs (D9, D39)
- **Picker: 21 hubs** = the 20 approved stations (D9) plus **Baden** (Baden SBB, didok 8503504, checked in the GTFS stops: parent station `Parentch:1:sloid:3504`, 205 rail departures 06:30–18:00), `pipeline/reach/hubs.py` `HUBS`.
- **Nearest-hub set (D39): 15 hubs**, derived at build time by `hubs.nearest_hubs()`: the core city's main station of every BFS agglomeration (Agglomerationen 2020, backbone column `AGGL2020`) with at least 100,000 residents in the latest STATPOP year (pop_total 2025 summed over the reference-state membership). Each qualifying agglomeration is mapped to its station explicitly (`AGGL_HUB`: Zürich → Zürich HB, Genève (CH) → Genève, Basel (CH) → Basel SBB, Lausanne, Bern, Luzern, St. Gallen, Lugano (CH) → Lugano, Winterthur, Zug, Baden – Brugg → Baden, Aarau, Neuchâtel, Biel/Bienne, Olten – Zofingen → Olten). The build fails if the derived set differs from the 15 approved by the owner, or if an agglomeration ≥ 100,000 has no station.
- STATPOP 2025: Zürich 1,499,457 … Baden – Brugg 117,931, Aarau 117,602, Neuchâtel 114,425, Biel/Bienne 112,538, Olten – Zofingen 109,572; the next ones, Sion (99,805) and Fribourg (95,296), stay below 100,000.
- `reach_*_nearest_hub` = minimum over these 15 only (Bellinzona, Chur, Fribourg, Sion, Schaffhausen, Thun are starting points in the picker but not "hubs" for this metric); the note names the hub, `reach_times.json` carries `nearest_hubs`, `nearest_rule` (EN/DE/FR) and `nearest[mode]` (hub name per unit).

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
arrival have no journey and are left out. This is done on **three weekdays** (see "Service days") and
each station takes the summary of its **median day** (median of the three daily medians; P10, P90 and
the late window come from that same day). Where the hub cannot be reached by 08:30 at all (far hubs:
the first trains of the day arrive later), the hour from the earliest possible arrival is used if
that is by 10:30, and the note says so ("no arrival by 08:30: median over the hour from 08:55");
otherwise the pair has no value ("no arrival at the hub by 10:30"). P10 and P90 over the same
deadlines are stored (`minutes_p10`, `minutes_p90`). Connections are kept from 04:30 for this
(`gtfs_prep.EARLIEST_DEP`); a stop counts as served with a departure or arrival 06:30–18:00 as before.

**Main station (since 2026-11-11: by the population it serves; expert audit MUST 2).** The old rule
(most departures) picked intermediate halts and, without rail, boat or rack-railway halts: Engelberg →
Grafenort, Arosa → St. Peter-Molinis, Poschiavo → Alp Grüm, Locarno → Riazzino, Weggis → Romiti
Felsentor (Rigi railway). New rule (`pt.main_stations()`):
1. Candidates: the stops served 06:30–18:00 inside the municipality (reference polygon).
2. Coverage of a candidate: residents (STATPOP 2025) of the municipality's inhabited hectares within
   1.5 km straight line (the door-to-door access radius).
3. Rail first: if the best-covering rail station covers at least **a third** of what the best stop of
   any mode covers, only rail stations compete; otherwise all modes.
4. Of the competing stops, those covering at least **half** of the best coverage remain, and the one
   with the most departures 06:30–18:00 (rail departures for rail) wins. This keeps the town station
   where it serves the town (Rapperswil SG rather than Jona, Wetzikon ZH rather than Kempten, Solothurn
   rather than Solothurn West, Schwyz station rather than the bus stop "Schwyz, Zentrum") and drops
   outlying halts.
5. A hub municipality takes its hub station (time 0).
6. No served stop inside: the same choice among the stops within 2 km of the population-weighted
   centre (`main_inside = false`, 37 municipalities); 7 have none (status `no stop within 2 km`:
   Häutligen, Oberthal, Oberhünigen, Schelten, Seehof, Ochlenberg BE and Blatten VS).

Thresholds were chosen by inspection: with "≥ 90 % of the best coverage" Wetzikon took Kempten and
Montreux took Belmont-sur-Montreux; with "rail if ≥ half" Kriens and Schwyz took bus stops although
their S-Bahn stations cover a third of the residents. The main station changed for 439 of 2,103
municipalities. Its mode (`main_mode`): rail 860, bus 1,209, tram 20, cableway 10, funicular 3,
metro 1. **A station time from a stop without rail is labelled** in the metric note and in
`reach_times.json` (`main_station[i][3]`, `notes`): "from Weggis, Dorfplatz (bus), not a rail station".

Before → after (station time towards the named hub; both from the same per-station medians; door to door after the slash):

| Municipality → hub | Before (most departures) | After (population served) |
|---|---|---|
| Engelberg → Luzern | Grafenort 32 | Engelberg 47 / 56 |
| Arosa → Chur | St. Peter-Molinis 50 | Arosa 58 / 67 |
| Poschiavo → Chur | Alp Grüm 174 | Poschiavo 177 / 184 |
| Locarno → Bellinzona | Riazzino 16 | Locarno S. Antonio 41 / 42 |
| Weggis → Luzern | Romiti Felsentor 84 | Weggis, Dorfplatz (bus) 45 / 51 |
| Weggis → Bern | Romiti Felsentor 179 | Weggis, Dorfplatz (bus) 112 / 117 |
| Köniz → Bern | Niederwangen 11 | Wabern bei Bern 12 / 21 |
| Meyrin → Genève | Zimeysa 10 | Meyrin 8 / 27 |
| Kloten → Zürich HB | Zürich Flughafen 10 | Kloten 15 / 26 |
| Adliswil → Zürich HB | Sood-Oberleimbach 27 | Adliswil 28 / 33 |
| Arbon → St. Gallen | Arbon Seemoosriet 34 | Arbon 30 / 36 |
| Ebikon → Luzern | Buchrain 14 | Ebikon 11 / 21 |
| Richterswil → Zürich HB | Samstagern 36 | Richterswil 30 / 40 |
| Ecublens VD → Lausanne | Campus des médias 24 | UNIL-Sorge (metro) 17 / 18 |
| Glarus → Zürich HB | Netstal 60 | Glarus 63 / 73 |
| Blonay – Saint-Légier → Lausanne | Hauteville 26 | St-Légier-Gare 28 / 39 |
| Veyrier → Genève | Pont de Sierne 27 | Sierne (bus) 28 / 36 |
| Ittigen → Bern | Worblaufen 5 | Papiermühle 8 / 15 |
| Val de Bagnes → Lausanne | Etiez 84 | Le Châble VS 89 / 113 |
| Val-de-Travers → Neuchâtel | Travers 27 | Fleurier 41 / 46 |
| Münchenbuchsee → Bern | Zollikofen 9 | Münchenbuchsee 12 / 20 |
| Eschenbach SG → Zürich HB | Neuhaus SG, Ochsen 53 | Eschenbach SG, Twirren (bus) 52 / 56 |
| Steinhausen → Zug | Steinhausen Rigiblick 5 | Steinhausen 6 / 18 |
| Widnau → St. Gallen | Rhydorf 35 | Gemeindehaus (bus) 45 / 47 |
| Aadorf → Winterthur | Guntershausen 21 | Aadorf 18 / 29 |
| Fully → Lausanne | Branson, Pont du Rhône 76 | Fully, poste (bus) 81 / 86 |

(The first six are the audit's cases; the others are the 20 most populous municipalities whose main
station changed. `validation.json` → `main_station_before_after`.) Locarno's FFS station lies in
Muralto, so Locarno's own main station is the FART stop S. Antonio in the centre. Their door-to-door value exists except for Schelten,
Seehof and Blatten, which have no served stop within 1.5 km of any inhabited hectare. Examples: Zürich → Zürich HB (1,007 rail departures), Oberweningen → the bus stop
"Oberweningen, Im Hüebli" (the S-Bahn station Schöfflisdorf-Oberweningen lies in Schöfflisdorf).
For a hub's own municipality the station time is 0.

**Blatten VS** (6192): the village was destroyed by the May 2025 landslide. The 2026 GTFS feed has no
stop in the municipality, while STATPOP 2025 still lists 302 residents on 28 hectares, so both
figures are missing with the reason "village destroyed by the landslide of May 2025; no public
transport service in the 2026 timetable".

**Spot checks (station time, median day; P10–P90 in brackets; door to door after the slash; also in
`pipeline/tests/test_reach.py`):**

| From → hub | Station time | Door to door | Expected |
|---|---|---|---|
| Winterthur → Zürich HB | 20 (19–28) | 37 | ~20 |
| Basel SBB → Zürich HB | 53 (53–69) | 74 | ~53 |
| Liestal → Basel SBB | 11 (10–16) | 25 | ~11 |
| Zug → Zürich HB | 26 (24–35) | 41 | ~25 |
| Bern → Zürich HB | 57 (56–60) | 76 | 56–60 |
| Baden → Zürich HB | 16 (16–28) | 32 | ~15 |
| Lugano → Zürich HB | 115 (115–143) | 140 | ~110 (feed: 113–117 min trains all day) |
| Genève → Zürich HB | 190 (190–190) | 197 | ~160 (see "Service days") |
| Engelberg → Luzern | 47 (47–54) | 56 | ~43 (feed: every Engelberg–Luzern train 47 min) |
| Arosa → Chur | 58 (58–58) | 67 | ~60 |
| Oberweningen → Zürich HB | 36 (36–36) | 39 | sensible (was 419 min before the best-stop fix) |

**Long trips checked against the feed (2026-11-10).** The median is taken over arrival *minutes*, so
a journey counts as often as the deadlines it serves (what a traveller who must be at the hub by a
random time between 07:30 and 08:30 experiences). Example Genève Cornavin → Zürich HB on the service
day: the feed has exactly one direct train arriving 06:00–09:00 (05:33 → 08:28, 175 min; slower than
the usual ~2 h 40 because of the works on that date, see Limitations); arrivals 07:56–08:27 need the
04:46 departure with a change (07:56, 190 min), so the median is 190 and P10 175. Lausanne → Zürich
138 (journeys of 164, 142, 138 and 131 min arrive in the window), Lugano → Zürich 115, St. Gallen →
Zürich 60, Chur → Zürich 75, Genève → Bern 113, St. Gallen → Bern 141, Lugano → Bern 206 (only one
journey, 04:32 → 07:58, arrives by 08:30). The main station of Genève is Cornavin (8501008); no
footpath or change-time rule adds time on these trips: the values are the feed's own journeys.

**Agreement with the NPVM PT matrix** (column = zone → hub zone, population-weighted like the car
values; 21 hubs, 42,570 pairs with a value in both, hub zones excluded; before the main-station and
multi-day change: 20 hubs, r 0.985 and 0.980):

| GTFS variant (towards hub) | r | median GTFS/NPVM | median diff | within ±15 % | within ±25 % |
|---|---|---|---|---|---|
| door to door | 0.985 | 0.95 | −6.4 min | 88 % | 98 % |
| station time | 0.981 | 0.91 | −12.6 min | 73 % | 91 % |

Per hub, r is 0.976–0.989 for door to door and 0.971–0.986 for the station time. The station time is
shorter than NPVM by construction (NPVM includes access and egress). Coverage: 42,586 of 44,310 pairs
have a station time (11,577 of them use the late window); 1,577 pairs have no arrival by 10:30 and 147
no stop within 2 km.

**No arrival by 10:30 is not missing data** (expert audit SHOULD 9). These pairs (mostly Lugano,
Bellinzona, Genève and Sion from the far side of the country) get status `not_applicable` in the
metrics, with the reason "no arrival at the hub by 10:30 on a weekday morning (first connections arrive
later)", so the web build counts them as covered and the coverage label stays "national" instead of
"partial:<cantons>".

**Service days (robustness, 2026-11-11).** The station and door-to-door times are the median day of
**Tue 17 Nov, Wed 25 Nov and Thu 3 Dec 2026** (`gtfs_prep.REVERSE_DAYS`; each day is prepared like
the service day). Before choosing them, ten weekdays (12, 17, 18, 19, 24, 25, 26 Nov, 1, 2, 3 Dec)
were compared: trips per day 190.6k–193.4k (11 Nov 186.6k and 8 Dec 180.9k, a holiday, left out);
no trips of route type 714 (rail replacement bus) on any of them; the 420 hub-to-hub station times
(21 × 20) are identical on all ten days except one pair on 12 Nov (+4 min). Across the three chosen
days only 0.4 % of municipality–hub pairs differ at all (max 21 min, local works), and in 0.15 % the
median day differs from 17 Nov. **Genève → Zürich 190 min is therefore not a works artefact of
17 Nov:** every weekday in Nov–Dec 2026 has the same trains. The direct Genève–Zürich trains take
173 min all day in this feed (2026 timetable; Lausanne–Bern 69–72 min), and an arrival at Zürich
07:30–08:30 needs one of the first trains of the day (05:33 → 08:28 direct, 175 min; or 04:46 with a
change, 190 min, which serves most arrival minutes). Runtime: about 11 s of reverse scans per hub for
the three days (4 s per day), about 4 minutes for all 21 hubs.

## Spread over the morning: P10 / median / P90, both directions

Backlog item "Travel-time detail" (2026-11-11). The headline figures keep their definitions (D31); next to each there is
now the spread over the morning window, for public transport only.

**What is computed** (per hub, per station, then per municipality):

| | towards the hub (`to`) | from the hub outwards (`from`) |
|---|---|---|
| scans | reverse scans, arrival deadline every minute (as for D31, `gtfs_rcsa_*`) | forward scans, departure every minute 07:30-08:30, scanned to 09:30 for the latest departure (`gtfs_fcsa_*`) |
| window | 61 arrival minutes 07:30-08:30 (later hour where the hub is out of reach by 08:30, `window_start_min`) | 61 departure minutes 07:30-08:30 |
| journey | arrival - departure of the train actually taken (no initial wait, no wait at the hub) | EA(t) - LD(t): earliest arrival minus the latest departure that gives the same arrival (as in the old hub-outward method) |
| journey incl. wait | deadline T - departure | arrival - departure minute t |
| days | median day of the three weekdays per station (`combine_days`; the P10/P90 come from the same day as the median) | same |
| station time | the municipality's main station (same stop as towards the hub) | same |
| door to door | hectare time = min over stops within 1.5 km of (walk + stop value); population-weighted median over hectares | same |

Per station: median, P10, P90 of the 61 journey times, and the same three for the journey including waiting. The
rows are minute by minute, so a train that serves five consecutive minutes counts five times: the percentiles are those
of "a random minute of the morning", not of "a random train".

- **Door-to-door P10/P90** use the stop's P10 resp. P90 in the same formula as the median (min over stops of walk +
  stop percentile, then the population-weighted median over hectares). This is an approximation of the percentile of
  the per-minute minimum: where two stops alternate it is slightly too high at P10 and too low at P90. It keeps
  P10 <= median <= P90 per hectare and so per municipality (checked in `test_spread_columns_ordered`).
- **Why two ranges (journey and with waiting).** The journey time follows D31 and has no waiting in it, so an hourly bus that always
  takes 36 minutes has a zero-width journey range. The range of the journey *including waiting* is what shows infrequent
  service (Oberweningen -> Zürich HB: journey 36 / 36 / 36 min, with waiting 39 / 51 / 62 min; Winterthur -> Zürich HB:
  journey 19 / 20 / 28, with waiting 20 / 24 / 29).
- **Hub outwards and rare service.** EA - LD is only defined if the vehicle leaves before the last scan (09:30). Where
  the arrival does not change up to 09:30 the vehicle leaves later and the journey is unknown; in the spread
  (`journey_times(ea, cap_unreached=True)`) these departures count as unreached (the journey including waiting stays
  valid). A municipality whose median journey is unknown gets status "no departure from the hub 07:30-09:30 reaches it by
  18:00" (not applicable in the metrics), a P10 or P90 needing such a departure is empty. The older `gtfs_csa_*` methods
  are unchanged and still use the cap as an upper bound (which gave Oberweningen 415 min).
- **Runtime.** The forward scans now run on the three weekdays (two extra days per hub, about 5 s each on a free core) and the per-municipality
  door-to-door medians use `AccessIndex` (one pass over 4.7 million hectare-stop links per vector). Full run (`python -m pipeline.reach.run`, 21 hubs): 12 min wall on a shared 4-core machine (the spread adds
  about 10 s per hub, about 3.5 min in total, of which about 5 s per hub are the two extra forward days).

Sample values (P10 / median / P90, minutes; journey, then including waiting; station time, main station, towards the hub):
Winterthur -> Zürich HB 19 / 20 / 28, with waiting 20 / 24 / 29; Bern -> Zürich HB 56 / 57 / 60, 59 / 67 / 78; Basel SBB -> Zürich HB
53 / 53 / 69, 56 / 67 / 75; Engelberg -> Luzern 47 / 47 / 54, 53 / 65 / 83; Oberweningen -> Zürich HB 36 / 36 / 36, 39 / 51 / 62; Arosa -> Chur
58 / 58 / 58, 64 / 88 / 107. Across all municipalities towards Zürich HB the median width of the journey range (P90 - P10) is 2 min
and that of the range with waiting 24 min (the waiting range is what separates frequent from infrequent service).

**Outputs.** `travel_times.parquet`: new columns `minutes_wait_p10`, `minutes_wait_p90`, `minutes_p10/p90` also for
`gtfs_rcsa_popweighted`; new methods `gtfs_fcsa_mainstation`, `gtfs_fcsa_popweighted` (existing methods and values unchanged).
Station tables `data/interim/reach/pt_station_times_to_hub/<hub>.parquet` gain `wait_p10_s`, `wait_p90_s`;
`pt_station_times_from_hub/<hub>.parquet` is new. For the app: `data/out/reach/spread.json` and `<hub>_spread.json`
(layout in web_data_contract.md section 8) and ten metrics `reach_spread_<to|from>_<ptst|pt>_<p10|p50|p90>_nearest_hub`
in `reach_metrics` (nearest hub among the 15, by the measure's own median). The 210 per-hub metric ids were not created: the
per-hub values are in the JSON files, so the map's metric list stays short (the generator would only need the pattern
`reach_spread_<dir>_<kind>_<stat>_<hub>`).

## Station time above door-to-door (check of 2026-11-11)

Question: for how many pairs is the headline station time more than 10 minutes above door-to-door? Of 42,570 municipality-hub pairs
with both values, 814 (1.9 %, 244 municipalities, 1.5 % of the residents) before and after this change (the values towards the hub did not
change). Causes found (`pt_station_times_to_hub`, per-hectare best stops):
1. **Late window per station** (287 of the 814, towards far hubs): a station whose earliest possible arrival at the hub is after 08:30
   uses the hour from that arrival (`window_start_min`), each station its own. A bus stop in the same city that can only just not
   make an earlier arrival starts its hour later and gets the faster daytime trains, while the rail station is still in the slow
   early-morning window (Chur -> Bellinzona: station 180 min, city bus stops 135-140 min in the later window). Not a stop-choice problem;
   it is the per-station window rule. A common window per hub (for example the hub's earliest arrival over the nearest stations)
   would remove it but changes all far values and is an owner decision.
2. **Door-to-door uses any stop within 1.5 km**, also stops of neighbouring municipalities and other modes; the median over hectares can sit on
   a better-connected stop than the main station (Frauenfeld, Yverdon, Meyrin: 10-20 min).
3. Not the stop choice: replacing the main station by the fastest competing stop (serving at least half of the best stop's residents,
   same class) towards the nearest hub changed 145 to 783 main stations but only brought the count from 815 to 715-768; a per-hub best
   competing stop (50 %, same class) gives 416, but it makes the station time a "best stop" instead of the main station and the name
   shown for the municipality would then differ by hub (`reach_times.json` holds one main station per municipality). Not applied.
Weggis (BFS 1069) towards Luzern is 45 min at the main stop (Weggis, Dorfplatz, bus) against 51 min door-to-door; towards Zürich HB 84 / 87.7 min.
No pair above is a case of the boat pier being faster. Engelberg -> Luzern 47 / 56.4, Arosa -> Chur 58 / 66.5, Locarno -> Bellinzona
41 / 42.1 (all station time below door-to-door).

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
- **Hubs** are their main rail station, given as didok number and GTFS station id `Parentch:1:sloid:<n>` (plus Baden 8503504, D39):

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
- **Direction (since 2026-11-11, expert audit SHOULD 8): towards the hub**, the matrix column (every zone → hub zone), the same direction as public transport. The matrix has full columns; row and column agree closely (44,310 pairs: r 0.999, median column − row −0.2 min, 5–95 % range −3.5 to +3.1 min; Zürich → Bern 106.8 vs 107.7, Genève → Zürich 212.5 vs 213.9).
- Labelled **"average weekday model incl. congestion"** (TTC = travel time in the loaded network of the average-weekday assignment). The values are well above free flow (Zürich HB ↔ Bern about 107 min, Olten 68), which is what the audit expected from a loaded network.
- The data sheet says all matrices are for the **average weekday (DWV)**.
- The data sheet does not state the congestion level explicitly. TTC is the skim of the DWV (whole-day) assignment, i.e. day-average loaded-network times, not the peak hour. Peak-hour (MSP) states exist only as VISUM files.
- **Hub zone** = the NPVM zone polygon that contains the hub's station. For example, Zürich HB is in zone 26101201.
- **Municipality value** = the population-weighted mean of the zone → hub-zone times.
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
  - Residual at the anchors: mean absolute error 2.7–3.7 min, 90th percentile 6–8 min.
  - Chains with the same speed are merged into polylines and simplified to 40 m.
- **Sizes.**
  - PT files: **169–179 KB gzipped**.
  - Car files: **200–208 KB gzipped**.
  - All 42 files are under the 300 KB gzip target, 7.9 MB gzipped in total.

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
- **Feed date.** The towards-hub figures use the median day of three weekdays; the hub-outward figures and the drawing use 17 Nov 2026 only. Long-running works that last the whole period (e.g. the slower Lausanne–Bern running times in the 2026 timetable) are in every day and cannot be removed this way. ToU 5.2: state the feed version in the app.
- **Car times.** NPVM car times are average-weekday model times, and congestion handling is unconfirmed (see above). The hectare weights are 2025 population, while the zones are from 2023.
- **Car drawing.** The car drawing is illustrative.
  - swissTLMRegio includes foreign main roads, so some trees route through France or Italy; for example, Genève → Valais runs along the south shore of Lake Geneva.
  - Car-train shuttles (Lötschberg, Furka, Vereina) are not in the road graph.
  - The rescaling leaves a few minutes of residual at the municipality centroids.
- **PT drawing.** Bus, boat and cableway legs are straight lines, including long PostAuto legs over passes. Funiculars are not in the Schienennetz and are drawn straight.
- **Missing package.** scipy is not installed. Neighbour searches use a numpy grid and shapely STRtree, so no extra package is needed.
