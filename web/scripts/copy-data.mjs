// Copy exactly the data files the skeleton reads from data/out/ into web/public/data/.
// The source files are built by the pipeline (make web, make profile, make reach, make geometry) and are never
// edited here. Run: node scripts/copy-data.mjs  (also part of npm run dev / npm run build).
import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(here, '../../data/out');
const DEST = resolve(here, '../public/data');

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
  ['web/metrics.json', true],
  ['web/sources.json', true],
  ['web/units.json', true],
  ['web/latest/gemeinde/core.json', true],
  ['web/latest/gemeinde/mobility_accessibility.json', true],
  // profile page and search (make profile)
  ['web/search.json', true],
  ['web/identity.json', true],
  ['web/history.json', true],
  ['web/neighbours.json', true],
  // every theme file of every level (D23, loaded on first use), incl. the national values
  ...latestDirs.flatMap(dirFiles),
  // time series per metric for the year slider (loaded on demand); votes/ is not copied
  ...dirFiles('web/series'),
  // reach: all hubs, both modes; car reach can be held back by the licence gate (the app handles
  // its absence)
  ['reach/zuerich_pt.json', true],
  ...dirFiles('reach'),
]);

function dedupe(list) {
  const seen = new Set();
  return list.filter(([rel]) => !seen.has(rel) && seen.add(rel));
}

rmSync(DEST, { recursive: true, force: true });
let missing = 0;
let copied = 0;
let bytes = 0;
for (const [rel, required] of FILES) {
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
console.log(`copied ${copied} data files (${(bytes / 1048576).toFixed(1)} MB) to web/public/data/`);
