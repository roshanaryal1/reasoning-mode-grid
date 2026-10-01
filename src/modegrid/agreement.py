"""Krippendorff's alpha (nominal, ordinal, interval) for any number of raters.

Implemented from Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability",
using the coincidence-matrix formulation. Missing ratings are allowed.
Cross-checked against the `krippendorff` PyPI package in tests/test_agreement.py.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

Value = int | None


def _delta2(level: str, cats: np.ndarray, n_c: np.ndarray) -> np.ndarray:
    k = len(cats)
    d = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            if level == "nominal":
                d[i, j] = 0.0 if i == j else 1.0
            elif level == "interval":
                d[i, j] = float(cats[i] - cats[j]) ** 2
            elif level == "ordinal":
                lo, hi = min(i, j), max(i, j)
                d[i, j] = (n_c[lo : hi + 1].sum() - (n_c[i] + n_c[j]) / 2.0) ** 2
            else:
                raise ValueError(f"unknown level {level!r}")
    return d


def krippendorff_alpha(data: Sequence[Sequence[Value]], level: str = "ordinal") -> float:
    """`data` is raters x units. None marks a missing rating.

    Returns nan when there is no variation to measure against (all pairable
    values identical), which is the honest answer rather than 1.0.
    """
    arr = [list(r) for r in data]
    if not arr:
        return float("nan")
    n_units = len(arr[0])
    values = sorted({v for r in arr for v in r if v is not None})
    if len(values) < 2:
        return float("nan")
    cats = np.array(values)
    index = {v: i for i, v in enumerate(values)}
    o = np.zeros((len(cats), len(cats)))
    for u in range(n_units):
        unit = [v for r in arr if (v := r[u]) is not None]
        m = len(unit)
        if m < 2:
            continue
        for a in range(m):
            for b in range(m):
                if a != b:
                    i, j = index[unit[a]], index[unit[b]]
                    o[i][j] += 1.0 / (m - 1)
    n_c = o.sum(axis=1)
    n = n_c.sum()
    if n <= 1:
        return float("nan")
    d2 = _delta2(level, cats, n_c)
    observed = (o * d2).sum()
    expected = (np.outer(n_c, n_c) * d2).sum() / (n - 1)
    if expected == 0:
        return float("nan")
    return float(1.0 - observed / expected)


def exact_agreement(a: Sequence[Value], b: Sequence[Value]) -> float:
    pairs = [(x, y) for x, y in zip(a, b, strict=True) if x is not None and y is not None]
    if not pairs:
        return float("nan")
    return sum(x == y for x, y in pairs) / len(pairs)
