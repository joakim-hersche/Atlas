// Copy exactly the data files the skeleton reads from data/out/ into web/public/data/.
// The source files are built by the pipeline (make web, make profile, make reach, make geometry) and are never
// edited here. Run: node scripts/copy-data.mjs  (also part of npm run dev / npm run build).
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const FULL = resolve(here, '../../data/out');
const SAMPLE = resolve(here, '../sample-data');
const DEST = resolve(here, '../public/data');
// Without a pipeline build (a fresh clone), fall back to the small committed sample (web/sample-data,
// made by scripts/make_sample_data.py): a few metrics, all units, the same layout as data/out.
const USE_SAMPLE = process.env.ATLAS_SAMPLE === '1' || !existsSync(join(FULL, 'web/metrics.json'));
const OUT = USE_SAMPLE ? SAMPLE : FULL;
if (USE_SAMPLE) {
  if (!existsSync(join(SAMPLE, 'web/metrics.json'))) {
    console.error('Neither data/out/web (run the pipeline: make data) nor web/sample-data exists.');
    process.exit(1);
  }
  console.warn('Using the sample data in web/sample-data (a few metrics only; no data/out/web build, or ATLAS_SAMPLE=1).');
}

// every *.json file in a directory under data/out (optional entries; missing directory -> none)
const dirFiles = (dir) =>
  existsSync(join(OUT, dir))
    ? readdirSync(join(OUT, dir)).filter((f) => f.endsWith('.json')).sort().map((f) => [`${dir}/${f}`, false])
    : [];
// every level directory under web/latest (gemeinde, bezirk, kanton, typologies, schweiz)
const latestDirs = existsSync(join(OUT, 'web/latest'))
  ? readdirSync(join(OUT, 'web/latest'), { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => `web/latest/${d.name}`)
  : [];

// [path under data/out, required]
const FILES = dedupe([
  ['geo/gemeinde.topojson', true],
  ['geo/kanton.topojson', true],
  ['geo/lakes.topojson', true],
  ['geo/bezirk.topojson', false],
  ['geo/grossregion.topojson', false],
  ['geo/sprachgebiet.topojson', false],
  ['geo/agglomeration.topojson', false],
  ['geo/arbeitsmarktgebiet.topojson', false],
  ['geo/stadt_land.topojson', false],
  // finer outlines of municipalities, districts and cantons, loaded only when the map is zoomed in (make geometry)
  ['geo/gemeinde_fine.topojson', false],
  ['geo/bezirk_fine.topojson', false],
  ['geo/kanton_fine.topojson', false],
  ['web/metrics.json', true],
  ['web/sources.json', true],
  ['web/units.json', true],
  ['web/latest/gemeinde/core.json', true],
  ['web/latest/gemeinde/mobility_accessibility.json', true],
  // profile page and search (make profile)
  ['web/search.json', true],
  ['web/identity.json', true],
  ['web/reach_times.json', false],
  // plain-language glossary (pipeline/i18n/glossary.yaml) and the vote picker index
  ['web/glossary.json', false],
  // German and French for the pipeline's notes, gap reasons and Sources texts (make texts; keyed by the English text)
  ['web/texts.json', false],
  ['web/votes/index.json', false],
  ['web/history.json', true],
  ['web/neighbours.json', true],
  // every theme file of every level (D23, loaded on first use), incl. the national values
  ...latestDirs.flatMap(dirFiles),
  // time series per metric for the year slider (loaded on demand)
  ...dirFiles('web/series'),
  // one file per federal vote (vote picker, loaded on demand)
  ...dirFiles('web/votes'),
  // reach: all hubs, both modes; car reach can be held back by the licence gate (the app handles
  // its absence)
  ['reach/zuerich_pt.json', true],
  ...dirFiles('reach'),
  // older boundary states (make vintages; optional: without them the boundaries switch is hidden)
  ['web/vintages.json', false],
  ...vintageFiles(),
]);

/** geometry, units and value files of every older vintage listed in web/vintages.json */
function vintageFiles() {
  const ix = join(OUT, 'web/vintages.json');
  if (!existsSync(ix)) return [];
  const { vintages = [] } = JSON.parse(readFileSync(ix, 'utf8'));
  return vintages.flatMap((v) => [v.geometry.path, v.units.path, ...Object.values(v.files).map((f) => f.path)].map((p) => [p, true]));
}

function dedupe(list) {
  const seen = new Set();
  return list.filter(([rel]) => !seen.has(rel) && seen.add(rel));
}

rmSync(DEST, { recursive: true, force: true });
let missing = 0;
let copied = 0;
let bytes = 0;
// the sample has no reach, no other themes and fewer levels; those files are optional there
const SAMPLE_OPTIONAL = new Set(['reach/zuerich_pt.json', 'web/latest/gemeinde/mobility_accessibility.json']);
for (const [rel, req] of FILES) {
  const required = req && !(USE_SAMPLE && SAMPLE_OPTIONAL.has(rel));
  const src = join(OUT, rel);
  if (!existsSync(src)) {
    const msg = `${required ? 'missing' : 'skipped (optional)'}: data/out/${rel}`;
    if (required) { console.error(msg); missing++; } else console.warn(msg);
    continue;
  }
  const dst = join(DEST, rel);
  mkdirSync(dirname(dst), { recursive: true });
  copyFileSync(src, dst);
  bytes += statSync(dst).size;
  copied++;
}
if (missing) {
  console.error(`${missing} required file(s) missing; run the pipeline first (make web profile reach geometry).`);
  process.exit(1);
}
console.log(`copied ${copied} ${USE_SAMPLE ? 'SAMPLE ' : ''}data files (${(bytes / 1048576).toFixed(1)} MB) to web/public/data/`);
