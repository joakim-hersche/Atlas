"""Median of a distribution known only through counts in income classes (modelled estimate).

The ESTV federal tax statistics give, per municipality, the number of taxpayers (normal cases) in ten classes of
taxable income: 0 | 1-30,000 | 30,001-40,000 | 40,001-50,000 | 50,001-75,000 | 75,001-100,000 | 100,001-200,000 |
200,001-500,000 | 500,001-1,000,000 | over 1,000,000. The median is the income at which the cumulative count
reaches half of all taxpayers. Inside the class that contains this point the cumulative distribution is
interpolated linearly in the logarithm of income (a log-uniform density inside the class, as incomes are
roughly log-normal in the middle of the distribution); inside the first class (lower bound 0) linearly.

Tax secrecy suppresses small cells. The cumulative count at an upper class bound is taken from below (sum of the
classes up to it) or from above (total minus the classes above it), whichever has no suppressed cell. The
median is only returned when the two bounds of its class are known; otherwise NaN.
"""
from __future__ import annotations

import math

import numpy as np

# upper bounds of the first nine classes (the tenth class is open)
UPPER = [0.0, 30_000.0, 40_000.0, 50_000.0, 75_000.0, 100_000.0, 200_000.0, 500_000.0, 1_000_000.0]


def cumulative(counts: list[float], total: float) -> list[float]:
    """Cumulative count at UPPER[k] (k = 0..8), NaN where neither side is fully known. counts: 10 classes."""
    c = np.asarray(counts, dtype=float)
    out = []
    for k in range(len(UPPER)):
        lower, upper = c[: k + 1], c[k + 1:]
        if not np.isnan(lower).any():
            out.append(float(lower.sum()))
        elif not np.isnan(upper).any() and not math.isnan(total):
            out.append(float(total - upper.sum()))
        else:
            out.append(math.nan)
    return out


def median_from_classes(counts: list[float], total: float | None = None) -> float:
    """Estimated median (CHF) from 10 class counts; total defaults to their sum (all must then be known)."""
    c = np.asarray(counts, dtype=float)
    if total is None:
        total = float(c.sum()) if not np.isnan(c).any() else math.nan
    if not total or math.isnan(total) or total <= 0:
        return math.nan
    half = total / 2.0
    F = cumulative(list(c), total)
    for k, (b, f) in enumerate(zip(UPPER, F)):
        if math.isnan(f) or f < half:
            continue
        if k == 0:
            return 0.0
        prev_F = F[k - 1]
        if math.isnan(prev_F):
            return math.nan  # the median class cannot be bracketed (suppressed cells)
        lo, hi = UPPER[k - 1], b
        width = f - prev_F
        if width <= 0:
            return float(hi)
        frac = (half - prev_F) / width
        if lo <= 0:
            return float(lo + frac * (hi - lo))
        return float(math.exp(math.log(lo) + frac * (math.log(hi) - math.log(lo))))
    return math.nan  # median in the open class above CHF 1,000,000
