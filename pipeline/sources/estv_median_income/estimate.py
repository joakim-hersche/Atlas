"""Median of a distribution known only through counts in income classes (modelled estimate).

The ESTV federal tax statistics give, per municipality, the number of taxpayers (normal cases) in ten classes of
taxable income: 0 | 1-30,000 | 30,001-40,000 | 40,001-50,000 | 50,001-75,000 | 75,001-100,000 | 100,001-200,000 |
200,001-500,000 | 500,001-1,000,000 | over 1,000,000. The median is the income at which the cumulative count
reaches half of all taxpayers. Inside the class that contains this point the cumulative distribution is
interpolated linearly in the logarithm of income (a log-uniform density inside the class, as incomes are
roughly log-normal in the middle of the distribution); inside the first class (lower bound 0) linearly.

Tax secrecy suppresses cells with fewer than 4 taxpayers; the remainder to the published total is spread over the
suppressed cells (see median_from_classes).
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


MAX_SPREAD = 0.05  # with a hidden larger cell: accept only if the two bounding medians differ by at most 5 %
SUPPRESSED_MAX = 3  # a suppressed cell holds 0-3 taxpayers: the smallest published class count is 4 (2021, 2023)


def median_from_classes(counts: list[float], total: float | None = None) -> float:
    """Estimated median (CHF) from 10 class counts; total defaults to their sum (all must then be known).

    Suppressed cells (NaN): ESTV hides class cells with fewer than 4 taxpayers (checked: the smallest published
    class count is 4 in the 2021 and 2023 workbooks, over about 21,000 cells each). The taxpayers not accounted
    for by the known classes (total minus their sum) are therefore spread over the suppressed cells with at most
    3 each, once filling from the lowest and once from the highest suppressed class. The mean of the two medians
    is returned. If the remainder does not fit (a larger cell was hidden as well, to protect the small one) the whole
    remainder is put into the lowest / highest suppressed class and the result is accepted only if the two medians
    differ by at most 5 %, otherwise NaN."""
    c = np.asarray(counts, dtype=float)
    if not np.isnan(c).any():
        total = float(c.sum())  # all classes known: their own sum (the published total can differ by hidden cells)
    if total is None or not total or math.isnan(total) or total <= 0:
        return math.nan
    miss = np.flatnonzero(np.isnan(c))
    if len(miss):
        rest = total - float(np.nansum(c))
        if rest < -0.5:
            return math.nan
        rest = max(rest, 0.0)
        # remainder beyond 3 per cell: a larger cell was hidden as well (complementary suppression); then the whole
        # remainder is put once into the lowest and once into the highest suppressed class (widest possible range)
        wide = rest > SUPPRESSED_MAX * len(miss) + 0.5
        bounds = []
        for order in (miss, miss[::-1]):
            d = c.copy()
            d[miss] = 0.0
            left = rest
            for i in order:
                d[i] = left if wide and i == order[0] else min(float(SUPPRESSED_MAX), left)
                left -= d[i]
            bounds.append(_median_complete(d, total))
        if any(math.isnan(b) for b in bounds):
            return math.nan
        lo, hi = min(bounds), max(bounds)
        mid = (lo + hi) / 2
        if wide and hi - lo > MAX_SPREAD * mid:
            return math.nan
        return float(mid)
    return _median_complete(c, total)


def _median_complete(c: np.ndarray, total: float) -> float:
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
