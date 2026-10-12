"""Synthetic scores with known effects.

Used for three things, never for results:
  1. tests: does the analysis recover an effect that is known to be there?
  2. `modegrid demo`: an end-to-end dry run before any money is spent
  3. `modegrid power`: how many families and replicates the design needs

Scores come from a latent-threshold model:
    latent = family_effect[f] + mode_shift * [mode == reasoning] + noise
    score  = 0 / 1 / 2 by cutting latent at fixed thresholds
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import DIMS, PRIMARY_MODES
from .anova import decompose, resample

CUTS = (-0.5, 0.5)


@dataclass(frozen=True)
class Effect:
    family_sd: float
    mode_shift: float
    noise_sd: float = 0.6


# Demo scenario that mirrors the LA-P4 hypotheses: D1 and D9 move with mode,
# D3 moves with the model family, the rest are mixed.
DEMO_EFFECTS: dict[str, Effect] = {
    "D1": Effect(0.3, 1.4),
    "D2": Effect(0.6, 0.3),
    "D3": Effect(1.2, 0.1),
    "D4": Effect(0.8, 0.4),
    "D5": Effect(0.5, 0.5),
    "D6": Effect(0.9, 0.2),
    "D7": Effect(0.4, 0.6),
    "D8": Effect(0.3, 0.3),
    "D9": Effect(0.3, 1.3),
}


def simulate_cells(effect: Effect, a: int, n: int, rng: np.random.Generator, size: int | None = None) -> np.ndarray:
    shape_prefix = () if size is None else (size,)
    fam = rng.normal(0.0, effect.family_sd, size=(*shape_prefix, a, 1, 1))
    mode = np.array([0.0, effect.mode_shift]).reshape(1, 2, 1) - effect.mode_shift / 2
    noise = rng.normal(0.0, effect.noise_sd, size=(*shape_prefix, a, 2, n))
    latent = fam + mode + noise
    return np.digitize(latent, CUTS).astype(float)


def synthetic_scores(
    families: list[str], replicates: int, prompt_id: str, seed: int, effects: dict[str, Effect] | None = None
) -> dict[str, dict[str, int]]:
    from .plan import make_run_id

    effects = effects or DEMO_EFFECTS
    rng = np.random.default_rng(seed)
    per_dim = {d: simulate_cells(effects[d], len(families), replicates, rng) for d in DIMS}
    out: dict[str, dict[str, int]] = {}
    for i, fam in enumerate(families):
        for j, mode in enumerate(PRIMARY_MODES):
            for k in range(replicates):
                rid = make_run_id(fam, mode, prompt_id, k + 1)
                out[rid] = {d: int(per_dim[d][i, j, k]) for d in DIMS}
    return out


def power(
    effect: Effect, a: int, n: int, sims: int = 300, n_boot: int = 400, seed: int = 0, direction: bool = False
) -> float:
    """Share of simulated studies where the 95% CI for delta omega2 is above zero.

    With `direction`, a study counts only if the reasoning-minus-fast CI from the
    same resamples is also above zero: the pre-registered rule for H4.
    """
    rng = np.random.default_rng(seed)
    data = simulate_cells(effect, a, n, rng, size=sims)
    fast, reasoning = PRIMARY_MODES.index("fast"), PRIMARY_MODES.index("reasoning")
    hits = 0
    for s in range(sims):
        samples = resample(data[s], n_boot=n_boot, seed=seed + s)
        boot = decompose(samples).delta_omega2
        boot = boot[~np.isnan(boot)]
        if not (boot.size and np.percentile(boot, 2.5) > 0):
            continue
        if direction:
            diff = samples[:, :, reasoning, :].mean(axis=(1, 2)) - samples[:, :, fast, :].mean(axis=(1, 2))
            if not np.percentile(diff, 2.5) > 0:
                continue
        hits += 1
    return hits / sims
