"""Two-way variance decomposition: family (model) x mode, with replicates.

Input is a balanced array `y` with shape (..., a, b, n):
    a = model families, b = modes, n = replicates per cell.
Leading dimensions are batch dimensions (used by the bootstrap and the power
simulation), so every function here is vectorised.

Outputs per batch element:
    SS, df, MS for family, mode, family x mode, residual
    eta^2   = SS_effect / SS_total                  (descriptive share)
    omega^2 = (SS_effect - df_effect * MS_E) / (SS_total + MS_E)
              (bias-corrected share, fairer when df differ: family has a-1 df,
               mode has b-1 = 1 df, so eta^2 flatters family by chance alone)
    variance components under a random-effects reading (method of moments,
    truncated at zero) as a secondary view.

The pre-registered primary statistic is
    delta_omega2 = omega2_mode - omega2_family
"Mode beats model" on a dimension means delta_omega2 > 0 with a bootstrap CI
that excludes zero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

EFFECTS = ("family", "mode", "interaction", "residual")


@dataclass
class Decomposition:
    ss: dict[str, np.ndarray]
    df: dict[str, int]
    ms: dict[str, np.ndarray]
    ss_total: np.ndarray
    eta2: dict[str, np.ndarray]
    omega2: dict[str, np.ndarray]
    var_components: dict[str, np.ndarray]

    @property
    def delta_omega2(self) -> np.ndarray:
        return self.omega2["mode"] - self.omega2["family"]

    @property
    def delta_eta2(self) -> np.ndarray:
        return self.eta2["mode"] - self.eta2["family"]


def _safe_div(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def decompose(y: np.ndarray) -> Decomposition:
    y = np.asarray(y, dtype=float)
    if y.ndim < 3:
        raise ValueError("y must have shape (..., families, modes, replicates)")
    a, b, n = y.shape[-3:]
    if a < 2 or b < 2 or n < 2:
        raise ValueError(f"need >= 2 families, modes and replicates, got {a}, {b}, {n}")

    grand = y.mean(axis=(-3, -2, -1), keepdims=True)
    cell = y.mean(axis=-1, keepdims=True)
    fam = y.mean(axis=(-2, -1), keepdims=True)
    mode = y.mean(axis=(-3, -1), keepdims=True)

    ss = {
        "family": b * n * ((fam - grand) ** 2).sum(axis=(-3, -2, -1)),
        "mode": a * n * ((mode - grand) ** 2).sum(axis=(-3, -2, -1)),
        "interaction": n * ((cell - fam - mode + grand) ** 2).sum(axis=(-3, -2, -1)),
        "residual": ((y - cell) ** 2).sum(axis=(-3, -2, -1)),
    }
    ss_total = ((y - grand) ** 2).sum(axis=(-3, -2, -1))
    df = {"family": a - 1, "mode": b - 1, "interaction": (a - 1) * (b - 1), "residual": a * b * (n - 1)}
    ms = {k: ss[k] / df[k] for k in EFFECTS}

    eta2 = {k: _safe_div(ss[k], ss_total) for k in EFFECTS}
    omega_den = ss_total + ms["residual"]
    omega2 = {k: _safe_div(ss[k] - df[k] * ms["residual"], omega_den) for k in ("family", "mode", "interaction")}

    vc = {
        "family": np.maximum(0.0, (ms["family"] - ms["interaction"]) / (b * n)),
        "mode": np.maximum(0.0, (ms["mode"] - ms["interaction"]) / (a * n)),
        "interaction": np.maximum(0.0, (ms["interaction"] - ms["residual"]) / n),
        "residual": ms["residual"],
    }
    return Decomposition(ss=ss, df=df, ms=ms, ss_total=ss_total, eta2=eta2, omega2=omega2, var_components=vc)


def bootstrap(y: np.ndarray, n_boot: int = 5000, seed: int = 0) -> Decomposition:
    """Resample replicates with replacement inside every cell.

    Cells (family x mode) are the design and stay fixed. Only the replicate
    noise is resampled, which is the uncertainty the replicates were run to
    measure.
    """
    y = np.asarray(y, dtype=float)
    a, b, n = y.shape
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, a, b, n))
    resampled = np.take_along_axis(np.broadcast_to(y, (n_boot, a, b, n)), idx, axis=-1)
    return decompose(resampled)


def permutation_p(y: np.ndarray, effect: str, n_perm: int = 5000, seed: int = 0) -> float:
    """Permutation p-value for one main effect.

    mode:   shuffle observations across the mode cells within each family
    family: shuffle observations across the family cells within each mode
    The statistic is that effect's SS. Ordinal 0/1/2 data breaks F-test
    assumptions, so the null distribution is built from the data instead.
    """
    y = np.asarray(y, dtype=float)
    a, b, n = y.shape
    rng = np.random.default_rng(seed)
    observed = decompose(y).ss[effect]
    if effect == "mode":
        flat = y.reshape(a, b * n)
        perm = np.stack([rng.permuted(flat, axis=1) for _ in range(n_perm)])
        sims = decompose(perm.reshape(n_perm, a, b, n)).ss["mode"]
    elif effect == "family":
        flat = np.swapaxes(y, 0, 1).reshape(b, a * n)
        perm = np.stack([rng.permuted(flat, axis=1) for _ in range(n_perm)])
        sims = decompose(np.swapaxes(perm.reshape(n_perm, b, a, n), 1, 2)).ss["family"]
    else:
        raise ValueError("effect must be 'mode' or 'family'")
    return float((1 + (sims >= observed - 1e-12).sum()) / (n_perm + 1))


def rank_transform(y: np.ndarray) -> np.ndarray:
    """Average ranks over the whole array. Sensitivity check for ordinal scores."""
    flat = np.asarray(y, dtype=float).ravel()
    order = flat.argsort(kind="mergesort")
    ranks = np.empty_like(flat)
    ranks[order] = np.arange(1, flat.size + 1)
    for v in np.unique(flat):
        mask = flat == v
        ranks[mask] = ranks[mask].mean()
    return ranks.reshape(np.shape(y))


def residualise(y: np.ndarray, covariate: np.ndarray) -> np.ndarray:
    """Remove a linear covariate (for example log output length), keep the mean.

    Reasoning modes write longer answers. If the mode effect disappears once
    length is removed, the honest reading is "longer answers score higher",
    not "reasoning helps".
    """
    yv = np.asarray(y, dtype=float).ravel()
    x = np.asarray(covariate, dtype=float).ravel()
    design = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(design, yv, rcond=None)
    return (yv - design @ beta + yv.mean()).reshape(np.shape(y))


def cell_spreads(y: np.ndarray) -> dict[str, float]:
    """Plain-language descriptive spreads, as named in the LA-P4 idea file.

    within_model_mode: mean over families of the variance of that family's mode cell means
    between_model:     mean over modes of the variance of the family cell means
    """
    cell = np.asarray(y, dtype=float).mean(axis=-1)
    return {
        "within_model_mode": float(cell.var(axis=1, ddof=1).mean()),
        "between_model": float(cell.var(axis=0, ddof=1).mean()),
    }
