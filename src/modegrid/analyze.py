"""Build the LA-P4 headline table: mode vs model vs residual, per rubric dimension."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import DIM_NAMES, DIMS, PRIMARY_MODES
from .anova import bootstrap, cell_spreads, decompose, permutation_p, rank_transform, residualise
from .plan import MAIN, Run
from .scores import Scores

# Pre-registered directional hypotheses (docs/preregistration.md).
HYPOTHESES = {
    "H1": ("D1", "mode > model", "Constraint reasoning is mode-sensitive"),
    "H2": ("D9", "mode > model", "Internal consistency is mode-sensitive"),
    "H3": ("D3", "model > mode", "Tool factuality is mode-stable"),
    "H4": ("total", "mode > model", "Headline: mode explains more of the total score than model"),
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
    "delta_omega2",
    "ci_low",
    "ci_high",
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


def verdict(ci_low: float, ci_high: float, ss_total: float) -> str:
    if ss_total == 0 or math.isnan(ci_low):
        return "no variance"
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
) -> dict[str, object]:
    d = decompose(y)
    boot = bootstrap(y, n_boot=n_boot, seed=seed)
    lo, hi = _ci(boot.delta_omega2)
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
        "delta_omega2": float(d.delta_omega2),
        "ci_low": lo,
        "ci_high": hi,
        "p_mode": math.nan if no_var else permutation_p(y, "mode", n_perm=n_perm, seed=seed),
        "p_family": math.nan if no_var else permutation_p(y, "family", n_perm=n_perm, seed=seed + 1),
        "within_model_mode": spreads["within_model_mode"],
        "between_model": spreads["between_model"],
        "rank_delta_omega2": float(rank_d),
        "length_adj_delta_omega2": length_adj,
        "verdict": verdict(lo, hi, float(d.ss_total)),
    }


def run_analysis(
    runs: list[Run],
    scores: Scores,
    prompt_id: str,
    n_boot: int = 5000,
    n_perm: int = 5000,
    seed: int = 20261001,
    lengths: dict[str, float] | None = None,
) -> tuple[Design, list[dict[str, object]]]:
    design = build_design(runs, prompt_id)
    length_arr = None
    if lengths is not None and all(rid in lengths for rid in design.run_ids.ravel()):
        length_arr = np.vectorize(lambda r: float(lengths[r]), otypes=[float])(design.run_ids)
    rows = [
        analyse_dimension(score_array(design, scores, dim), dim, n_boot, n_perm, seed, length_arr)
        for dim in (*DIMS, "total")
    ]
    return design, rows


def _fmt(v: object) -> str:
    if isinstance(v, float):
        return "n/a" if math.isnan(v) else f"{v:.3f}"
    return str(v)


def write_outputs(design: Design, rows: list[dict[str, object]], out_dir: str | Path, note: str = "") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "variance_table.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ROW_FIELDS, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: _fmt(v) for k, v in row.items()})

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
        "| delta omega2 | 95% CI | p mode | p family | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['dimension']} | {r['name']} | {_fmt(r['eta2_family'])} | {_fmt(r['eta2_mode'])} | "
            f"{_fmt(r['eta2_interaction'])} | {_fmt(r['eta2_residual'])} | {_fmt(r['delta_omega2'])} | "
            f"[{_fmt(r['ci_low'])}, {_fmt(r['ci_high'])}] | {_fmt(r['p_mode'])} | {_fmt(r['p_family'])} | "
            f"{r['verdict']} |"
        )
    lines += [
        "",
        "## Pre-registered hypotheses",
        "",
        "| ID | Dimension | Predicted | Observed | Supported |",
        "|---|---|---|---|---|",
    ]
    for hid, (dim, predicted, label) in HYPOTHESES.items():
        observed = str(by_dim[dim]["verdict"])
        lines.append(
            f"| {hid} | {dim} ({label}) | {predicted} | {observed} | {'yes' if observed == predicted else 'no'} |"
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
