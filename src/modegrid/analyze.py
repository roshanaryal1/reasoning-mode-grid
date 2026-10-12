"""Build the LA-P4 headline table: mode vs model vs residual, per rubric dimension."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from . import DIM_NAMES, DIMS, PRIMARY_MODES
from .anova import cell_spreads, decompose, permutation_p, rank_transform, resample, residualise
from .plan import MAIN, Run
from .scores import Scores

ALPHA_BAR = 0.667  # pre-registered; Krippendorff's lowest bar for tentative conclusions
LOW_VARIANCE_SHARE = 0.9  # pre-registered: >= 90% identical scores -> uninformative


@dataclass(frozen=True)
class Hypothesis:
    dim: str
    predicted: str  # "mode > model" or "model > mode" on delta omega2
    label: str
    role: str  # "confirmatory" (H4 only) or "secondary"
    direction: str | None  # "reasoning > fast" when the rationale predicts reasoning helps


# Pre-registered hypotheses (docs/preregistration.md, section 2).
HYPOTHESES = {
    "H1": Hypothesis("D1", "mode > model", "Constraint reasoning is mode-sensitive", "secondary", "reasoning > fast"),
    "H2": Hypothesis("D9", "mode > model", "Internal consistency is mode-sensitive", "secondary", "reasoning > fast"),
    "H3": Hypothesis("D3", "model > mode", "Tool factuality is mode-stable", "secondary", None),
    "H4": Hypothesis(
        "total",
        "mode > model",
        "Headline: mode explains more of the total than model",
        "confirmatory",
        "reasoning > fast",
    ),
}

ROW_FIELDS = [
    "dimension",
    "name",
    "eta2_family",
    "eta2_mode",
    "eta2_interaction",
    "eta2_residual",
    "omega2_family",
    "omega2_mode",
    "omega2_interaction",
    "delta_omega2",
    "ci_low",
    "ci_high",
    "mode_effect",
    "mode_effect_ci_low",
    "mode_effect_ci_high",
    "p_mode",
    "p_family",
    "within_model_mode",
    "between_model",
    "rank_delta_omega2",
    "length_adj_delta_omega2",
    "verdict",
]


class AnalysisError(ValueError):
    pass


@dataclass
class Design:
    families: list[str]
    modes: list[str]
    replicates: list[int]
    run_ids: np.ndarray  # shape (a, b, n), dtype object


def build_design(runs: list[Run], prompt_id: str) -> Design:
    primary = [r for r in runs if r.set == MAIN and r.primary and r.prompt_id == prompt_id and r.mode in PRIMARY_MODES]
    if not primary:
        raise AnalysisError(f"no primary runs for prompt {prompt_id!r}")
    families = sorted({r.family for r in primary})
    modes = list(PRIMARY_MODES)
    reps = sorted({r.replicate for r in primary})
    ids = np.empty((len(families), len(modes), len(reps)), dtype=object)
    for r in primary:
        ids[families.index(r.family), modes.index(r.mode), reps.index(r.replicate)] = r.run_id
    if any(v is None for v in ids.ravel()):
        raise AnalysisError("manifest is not a balanced family x mode x replicate grid")
    return Design(families, modes, reps, ids)


def score_array(design: Design, scores: Scores, dim: str) -> np.ndarray:
    missing = [rid for rid in design.run_ids.ravel() if rid not in scores]
    if missing:
        raise AnalysisError(
            f"{len(missing)} run(s) have no adjudicated score, e.g. {missing[:3]}. "
            "The analysis needs the full balanced grid. See docs/preregistration.md, exclusions."
        )

    def value(rid: str) -> float:
        row = scores[rid]
        return float(sum(row[d] for d in DIMS)) if dim == "total" else float(row[dim])

    return np.vectorize(value, otypes=[float])(design.run_ids)


def _ci(samples: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    s = samples[~np.isnan(samples)]
    if s.size == 0:
        return (math.nan, math.nan)
    lo, hi = np.percentile(s, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(lo), float(hi)


def verdict(ci_low: float, ci_high: float, ss_total: float, low_variance: bool = False) -> str:
    if ss_total == 0 or math.isnan(ci_low):
        return "no variance"
    if low_variance:
        return "uninformative (low variance)"
    if ci_low > 0:
        return "mode > model"
    if ci_high < 0:
        return "model > mode"
    return "inconclusive"


def analyse_dimension(
    y: np.ndarray,
    dim: str,
    n_boot: int,
    n_perm: int,
    seed: int,
    lengths: np.ndarray | None = None,
    families: list[str] | None = None,
) -> dict[str, object]:
    y = np.asarray(y, dtype=float)
    d = decompose(y)
    resamples = resample(y, n_boot=n_boot, seed=seed)
    boot = decompose(resamples)
    lo, hi = _ci(boot.delta_omega2)
    fast, reasoning = PRIMARY_MODES.index("fast"), PRIMARY_MODES.index("reasoning")
    # signed mode effect: reasoning mean minus fast mean, same resamples as delta
    mode_effect = float(y[:, reasoning, :].mean() - y[:, fast, :].mean())
    me_lo, me_hi = _ci(resamples[:, :, reasoning, :].mean(axis=(1, 2)) - resamples[:, :, fast, :].mean(axis=(1, 2)))
    _, counts = np.unique(y, return_counts=True)
    low_variance = counts.max() / y.size >= LOW_VARIANCE_SHARE
    names = families or [str(i) for i in range(y.shape[0])]
    family_effects = [
        {
            "family": names[i],
            "fast_mean": float(y[i, fast].mean()),
            "reasoning_mean": float(y[i, reasoning].mean()),
            "diff": float(y[i, reasoning].mean() - y[i, fast].mean()),
        }
        for i in range(y.shape[0])
    ]
    spreads = cell_spreads(y)
    rank_d = decompose(rank_transform(y)).delta_omega2
    length_adj: float | str = ""
    if lengths is not None:
        length_adj = float(decompose(residualise(y, np.log(np.maximum(lengths, 1)))).delta_omega2)
    no_var = float(d.ss_total) == 0
    return {
        "dimension": dim,
        "name": DIM_NAMES.get(dim, "sum of D1-D9"),
        "eta2_family": float(d.eta2["family"]),
        "eta2_mode": float(d.eta2["mode"]),
        "eta2_interaction": float(d.eta2["interaction"]),
        "eta2_residual": float(d.eta2["residual"]),
        "omega2_family": float(d.omega2["family"]),
        "omega2_mode": float(d.omega2["mode"]),
        "omega2_interaction": float(d.omega2["interaction"]),
        "delta_omega2": float(d.delta_omega2),
        "ci_low": lo,
        "ci_high": hi,
        "mode_effect": mode_effect,
        "mode_effect_ci_low": me_lo,
        "mode_effect_ci_high": me_hi,
        "p_mode": math.nan if no_var else permutation_p(y, "mode", n_perm=n_perm, seed=seed),
        "p_family": math.nan if no_var else permutation_p(y, "family", n_perm=n_perm, seed=seed + 1),
        "within_model_mode": spreads["within_model_mode"],
        "between_model": spreads["between_model"],
        "rank_delta_omega2": float(rank_d),
        "length_adj_delta_omega2": length_adj,
        "verdict": verdict(lo, hi, float(d.ss_total), bool(low_variance)),
        "family_effects": family_effects,
    }


def hypothesis_status(row: dict[str, object], h: Hypothesis, alphas: dict[str, float] | None = None) -> str:
    """Pre-registered decision for one hypothesis (preregistration sections 2 and 4)."""
    alpha = (alphas or {}).get(h.dim)
    checked = alpha is not None and math.isfinite(alpha)
    if checked and alpha < ALPHA_BAR:  # type: ignore[operator]
        return f"exploratory (alpha {alpha:.2f} below {ALPHA_BAR})"
    if row["verdict"] in ("no variance", "uninformative (low variance)"):
        return f"inconclusive ({row['verdict']})"
    if row["verdict"] != h.predicted:
        return "no"
    if h.direction == "reasoning > fast" and not float(row["mode_effect_ci_low"]) > 0:  # type: ignore[arg-type]
        return "no (mode matters, but reasoning is not better)"
    # support needs a passing reliability gate; without one the result is provisional
    status = "yes" if checked else "yes, pending alpha"
    # a strong interaction does not overturn support for the average effect, but the label says so
    inter = float(row.get("omega2_interaction", math.nan))  # type: ignore[arg-type]
    mains = max(float(row.get("omega2_mode", math.nan)), float(row.get("omega2_family", math.nan)))  # type: ignore[arg-type]
    if inter > mains:
        status += " (average effect only; interaction exceeds both main effects)"
    return status


def run_analysis(
    runs: list[Run],
    scores: Scores,
    prompt_id: str,
    n_boot: int = 5000,
    n_perm: int = 5000,
    seed: int = 20261001,
    lengths: dict[str, float] | None = None,
    families: list[str] | None = None,
) -> tuple[Design, list[dict[str, object]]]:
    if families is not None:
        # pre-registered subset analyses, e.g. families whose fast mode is a true off
        analysable = {
            r.family
            for r in runs
            if r.set == MAIN and r.primary and r.prompt_id == prompt_id and r.mode in PRIMARY_MODES
        }
        unknown = sorted(set(families) - analysable)
        if unknown:
            raise AnalysisError(f"unknown families (no primary runs for prompt {prompt_id!r}): {unknown}")
        if len(set(families)) < 2:
            raise AnalysisError("a family subset needs at least 2 families")
        runs = [r for r in runs if r.family in families]
    design = build_design(runs, prompt_id)
    length_arr = None
    if lengths is not None and all(rid in lengths for rid in design.run_ids.ravel()):
        length_arr = np.vectorize(lambda r: float(lengths[r]), otypes=[float])(design.run_ids)
    rows = [
        analyse_dimension(score_array(design, scores, dim), dim, n_boot, n_perm, seed, length_arr, design.families)
        for dim in (*DIMS, "total")
    ]
    return design, rows


def _fmt(v: object) -> str:
    if isinstance(v, float):
        return "n/a" if math.isnan(v) else f"{v:.3f}"
    return str(v)


def write_outputs(
    design: Design,
    rows: list[dict[str, object]],
    out_dir: str | Path,
    note: str = "",
    alphas: dict[str, float] | None = None,
) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "variance_table.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ROW_FIELDS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: _fmt(v) for k, v in row.items() if k in ROW_FIELDS})
    with (out / "family_mode_effects.csv").open("w", newline="", encoding="utf-8") as fh:
        fw = csv.writer(fh, lineterminator="\n")
        fw.writerow(["dimension", "family", "fast_mean", "reasoning_mean", "reasoning_minus_fast"])
        for row in rows:
            effects = cast(list[dict[str, Any]], row.get("family_effects", []))
            for fe in effects:
                fw.writerow(
                    [row["dimension"], fe["family"], *(_fmt(fe[k]) for k in ("fast_mean", "reasoning_mean", "diff"))]
                )

    by_dim = {r["dimension"]: r for r in rows}
    lines = [
        "# Variance decomposition: mode vs model vs residual",
        "",
        note,
        "",
        f"Design: {len(design.families)} families ({', '.join(design.families)}) x "
        f"{len(design.modes)} modes ({', '.join(design.modes)}) x {len(design.replicates)} replicates "
        f"= {design.run_ids.size} runs, {len(design.families) * len(design.modes)} cells.",
        "",
        "Primary statistic: delta = omega2(mode) - omega2(family), 95% bootstrap CI over replicates.",
        "",
        "| Dim | Name | eta2 family | eta2 mode | eta2 FxM | eta2 resid "
        "| omega2 FxM | delta omega2 | 95% CI | reasoning - fast | 95% CI | p mode | p family | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['dimension']} | {r['name']} | {_fmt(r['eta2_family'])} | {_fmt(r['eta2_mode'])} | "
            f"{_fmt(r['eta2_interaction'])} | {_fmt(r['eta2_residual'])} | {_fmt(r['omega2_interaction'])} | "
            f"{_fmt(r['delta_omega2'])} | [{_fmt(r['ci_low'])}, {_fmt(r['ci_high'])}] | {_fmt(r['mode_effect'])} | "
            f"[{_fmt(r['mode_effect_ci_low'])}, {_fmt(r['mode_effect_ci_high'])}] | "
            f"{_fmt(r['p_mode'])} | {_fmt(r['p_family'])} | {r['verdict']} |"
        )
    lines += [
        "",
        "## Pre-registered hypotheses",
        "",
        "H4 is the single confirmatory test; H1-H3 are pre-specified secondary tests.",
        "",
        "| ID | Role | Dimension | Predicted | Observed | Reasoning - fast (95% CI) | Supported |",
        "|---|---|---|---|---|---|---|",
    ]
    for hid, h in HYPOTHESES.items():
        r = by_dim[h.dim]
        lines.append(
            f"| {hid} | {h.role} | {h.dim} ({h.label}) | {h.predicted}"
            f"{'; ' + h.direction if h.direction else ''} | {r['verdict']} | {_fmt(r['mode_effect'])} "
            f"[{_fmt(r['mode_effect_ci_low'])}, {_fmt(r['mode_effect_ci_high'])}] | {hypothesis_status(r, h, alphas)} |"
        )
    lines += [
        "",
        "## Sensitivity checks",
        "",
        "| Dim | delta omega2 (raw) | delta omega2 (ranks) | delta omega2 (length-adjusted) |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['dimension']} | {_fmt(r['delta_omega2'])} | {_fmt(r['rank_delta_omega2'])} | "
            f"{_fmt(r['length_adj_delta_omega2']) or 'not run'} |"
        )
    (out / "variance_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
