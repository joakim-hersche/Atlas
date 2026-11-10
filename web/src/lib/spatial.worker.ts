// Web Worker: Moran's I and the LISA permutations off the main thread (see spatial.ts).
import { runSpatial, type SpatialRequest, type SpatialResponse } from './spatial';

self.onmessage = (e: MessageEvent<SpatialRequest>) => {
  let out: SpatialResponse;
  try {
    out = runSpatial(e.data);
  } catch (err) {
    out = { id: e.data.id, moran: null as never, lisa: null, error: String(err) };
  }
  (self as unknown as Worker).postMessage(out);
};
