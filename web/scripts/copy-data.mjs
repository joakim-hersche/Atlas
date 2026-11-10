// Copy exactly the data files the skeleton reads from data/out/ into web/public/data/.
// The source files are built by the pipeline (make web, make reach, make geometry) and are never
// edited here. Run: node scripts/copy-data.mjs  (also part of npm run dev / npm run build).
import { copyFileSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(here, '../../data/out');
const DEST = resolve(here, '../public/data');

// [path under data/out, required]
const FILES = [
  ['geo/gemeinde.topojson', true],
  ['geo/kanton.topojson', true],
  ['geo/lakes.topojson', true],
  ['web/metrics.json', true],
  ['web/sources.json', true],
  ['web/latest/gemeinde/core.json', true],
  ['web/latest/gemeinde/mobility_accessibility.json', true],
  ['reach/zuerich_pt.json', true],
  // car reach can be held back by the licence gate; the app handles its absence
  ['reach/zuerich_car.json', false],
];

rmSync(DEST, { recursive: true, force: true });
let missing = 0;
let copied = 0;
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
  copied++;
}
if (missing) {
  console.error(`${missing} required file(s) missing; run the pipeline first (make web reach geometry).`);
  process.exit(1);
}
console.log(`copied ${copied} data files to web/public/data/`);
