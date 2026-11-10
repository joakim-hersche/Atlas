// Reactive driver for the spatial statistics (spatial.ts): loads the contiguity file (neighbours.json, the same
// one the profile page uses), runs Moran's I and the LISA in a Web Worker and keeps the latest result.
// Construct it once in a component's script (it registers its own effects).
import { loadNeighbours, type NeighboursFile } from './places';
import type { LevelData } from './data';
import {
  DEFAULT_PERMS, DEFAULT_SEED, flatten, runSpatial,
  type LisaResult, type MoranResult, type SpatialRequest, type SpatialResponse,
} from './spatial';

export interface SpatialInputs {
  ld: LevelData;
  /** values of the shaded metric per unit; null while loading or not available */
  values: (number | null)[] | null;
  /** the panel is open or a spatial map mode is on: compute */
  enabled: boolean;
  /** the cluster map is on: the LISA is needed too */
  lisa: boolean;
}

const adjCache = new WeakMap<LevelData, number[][] | null>();
/** neighbour indices per unit of this level (null: the file has no entry for the level) */
export function adjacency(ld: LevelData, f: NeighboursFile): number[][] | null {
  const hit = adjCache.get(ld);
  if (hit !== undefined) return hit;
  const lv = f.levels[ld.level];
  let out: number[][] | null = null;
  if (lv) {
    out = ld.units.map((id) => {
      const row: number[] = [];
      for (const o of lv[id] ?? []) {
        const k = ld.index.get(o);
        if (k !== undefined) row.push(k);
      }
      return row;
    });
  }
  adjCache.set(ld, out);
  return out;
}

export class SpatialController {
  moran = $state.raw<MoranResult | null>(null);
  lisa = $state.raw<LisaResult | null>(null);
  busy = $state(false);
  error = $state<string | null>(null);
  /** the build has no contiguity for this level */
  noNeighbours = $state(false);
  perms = DEFAULT_PERMS;

  #nbFile = $state.raw<NeighboursFile | null>(null);
  #worker: Worker | null = null;
  #seq = 0;
  #doneFor: { values: unknown; ld: LevelData; lisa: boolean } | null = null;

  constructor(inputs: () => SpatialInputs) {
    $effect(() => {
      if (inputs().enabled && !this.#nbFile) {
        let live = true;
        loadNeighbours()
          .then((f) => {
            if (live && f) this.#nbFile = f;
            else if (live) this.error = 'neighbours.json';
          })
          .catch((e) => live && (this.error = String(e)));
        return () => (live = false);
      }
    });
    $effect(() => {
      const { ld, values, enabled, lisa } = inputs();
      const f = this.#nbFile;
      if (!enabled || !values || !f) return;
      const prev = this.#doneFor;
      // same data and already computed (with the LISA if it is wanted now): keep the result
      if (prev && prev.values === values && prev.ld === ld && (prev.lisa || !lisa)) return;
      const adj = adjacency(ld, f);
      if (!adj) {
        this.noNeighbours = true;
        this.moran = null;
        this.lisa = null;
        return;
      }
      this.noNeighbours = false;
      this.#start(ld, values, adj, lisa);
    });
    $effect(() => () => {
      this.#worker?.terminate();
      this.#worker = null;
    });
  }

  #start(ld: LevelData, values: (number | null)[], adj: number[][], withLisa: boolean) {
    const id = ++this.#seq;
    const prev = this.#doneFor;
    // another column or level: the old result no longer describes the map
    if (!(prev && prev.values === values && prev.ld === ld)) {
      this.moran = null;
      this.lisa = null;
      this.#doneFor = null;
    }
    this.busy = true;
    this.error = null;
    const { off, list } = flatten(adj);
    const req: SpatialRequest = { id, values: values.slice(), off, list, perms: this.perms, seed: DEFAULT_SEED, withLisa };
    const done = (r: SpatialResponse) => {
      if (r.id !== this.#seq) return; // an newer request is running
      this.busy = false;
      if (r.error) {
        this.error = r.error;
        return;
      }
      this.moran = r.moran;
      this.lisa = r.lisa;
      this.#doneFor = { values, ld, lisa: withLisa };
    };
    try {
      this.#worker ??= new Worker(new URL('./spatial.worker.ts', import.meta.url), { type: 'module' });
      this.#worker.onmessage = (e: MessageEvent<SpatialResponse>) => done(e.data);
      this.#worker.onerror = () => {
        // no worker support (or it failed to load): run here
        this.#worker = null;
        setTimeout(() => done(runSpatial(req)), 0);
      };
      this.#worker.postMessage(req);
    } catch {
      setTimeout(() => done(runSpatial(req)), 0);
    }
  }
}
