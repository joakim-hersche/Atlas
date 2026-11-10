"""Sample a large LV95 grid at points without loading it whole (strips of block rows)."""
from __future__ import annotations

import numpy as np
import rasterio
from rasterio.windows import Window


def sample_points(path, e: np.ndarray, n: np.ndarray, neighbourhood: int = 0, strip: int = 1024) -> np.ndarray:
    """Value of band 1 at points (E, N). neighbourhood k > 0: maximum over the (2k+1)^2 cells around the point
    (valid cells only). NaN where the grid has no value (nodata) or the point is outside it."""
    out = np.full(len(e), np.nan, dtype="float32")
    with rasterio.open(path) as r:
        t = r.transform
        col = np.floor((e - t.c) / t.a).astype("int64")
        row = np.floor((n - t.f) / t.e).astype("int64")
        ok = (col >= 0) & (col < r.width) & (row >= 0) & (row < r.height)
        k = neighbourhood
        order = np.argsort(row, kind="stable")
        order = order[ok[order]]
        rs = row[order]
        i = 0
        while i < len(order):
            top = max(int(rs[i]) - k, 0)
            bot = min(top + strip, r.height)
            j = np.searchsorted(rs, bot - k, side="left")  # rows fully inside the strip incl. margin
            j = max(j, i + 1)
            sel = order[i:j]
            top = max(int(row[sel].min()) - k, 0)
            bot = min(int(row[sel].max()) + k + 1, r.height)
            a = r.read(1, window=Window(0, top, r.width, bot - top)).astype("float32")
            if r.nodata is not None:
                a[a == np.float32(r.nodata)] = np.nan
            rr, cc = row[sel] - top, col[sel]
            if k == 0:
                out[sel] = a[rr, cc]
            else:
                best = np.full(len(sel), -np.inf, dtype="float32")
                for dr in range(-k, k + 1):
                    for dc in range(-k, k + 1):
                        r2 = np.clip(rr + dr, 0, a.shape[0] - 1)
                        c2 = np.clip(cc + dc, 0, a.shape[1] - 1)
                        v = a[r2, c2]
                        best = np.fmax(best, np.where(np.isnan(v), -np.inf, v))
                out[sel] = np.where(np.isfinite(best), best, np.nan)
            i = j
    return out
