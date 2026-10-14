"""Cell means, cross-rater agreement on how the cells rank, and Figure 1.

LA-P5 needs evidence that the rubric ranks systems the same way whoever scores
(docs/paper-plan.md, "What LA-P5 needs"). This module turns run-level scores into one
mean per family x mode cell, compares raters' cell rankings with Kendall's tau-b, and
summarises all raters with Kendall's W. It also draws Figure 1 of the paper outline:
fast vs reasoning, one line per family, per measure.

Exploratory. None of this is part of the pre-registered confirmatory analysis.
"""

from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import numpy as np

from . import DIM_NAMES, DIMS
from .analyze import Design, score_array
from .scores import Scores

MEASURES: tuple[str, ...] = ("total", *DIMS)

# Fixed colour per family, so a subset (--families) never repaints the survivors.
# Categorical slots 1-6 of the dataviz reference palette, validated for light mode
# (adjacent CVD dE 9.1, normal-vision dE 19.6). Lines cross, so every family also has
# its own marker and a direct label.
FAMILY_STYLE: dict[str, tuple[str, str]] = {
    "claude": ("#2a78d6", "o"),
    "deepseek": ("#eb6834", "s"),
    "gemini": ("#1baf7a", "^"),
    "gpt": ("#eda100", "D"),
    "grok": ("#e87ba4", "v"),
    "qwen": ("#008300", "P"),
}
_FALLBACK_STYLE = ("#52514e", "X")


def cell_means(design: Design, scores: Scores, measures: tuple[str, ...] = MEASURES) -> dict[str, np.ndarray]:
    """measure -> (families, modes) array of cell means."""
    return {m: score_array(design, scores, m).mean(axis=2) for m in measures}


def write_cell_means(design: Design, scores: Scores, path: str | Path) -> Path:
    means = cell_means(design, scores)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        # n_all_zero: answers scored 0 on all nine dimensions, which the refusal rule gives an
        # outright refusal. Pre-registration section 7 reports refusals per family and mode.
        w.writerow(["family", "mode", "n", *DIMS, "total", "n_all_zero"])
        for i, fam in enumerate(design.families):
            for j, mode in enumerate(design.modes):
                vals = [f"{means[m][i, j]:.3f}" for m in (*DIMS, "total")]
                zeros = sum(1 for rid in design.run_ids[i, j] if not any(scores[rid][d] for d in DIMS))
                w.writerow([fam, mode, len(design.replicates), *vals, zeros])
    return path


def _average_ranks(x: np.ndarray) -> np.ndarray:
    """Ranks 1..n, ties given the mean of the ranks they span."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def kendall_tau_b(x: np.ndarray | list[float], y: np.ndarray | list[float]) -> float:
    """Kendall's tau-b with tie correction. NaN when either side is constant."""
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("tau-b needs two vectors of the same length")
    concordant = discordant = ties_a = ties_b = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        da, db = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
        if da == 0 and db == 0:
            continue
        if da == 0:
            ties_a += 1
        elif db == 0:
            ties_b += 1
        elif da == db:
            concordant += 1
        else:
            discordant += 1
    denom = math.sqrt((concordant + discordant + ties_a) * (concordant + discordant + ties_b))
    return (concordant - discordant) / denom if denom else float("nan")


def kendall_w(ratings: np.ndarray) -> float:
    """Kendall's coefficient of concordance W, tie-corrected. Rows are raters, columns items."""
    r = np.asarray(ratings, dtype=float)
    m, n = r.shape
    if m < 2 or n < 2:
        raise ValueError("W needs at least 2 raters and 2 items")
    ranks = np.vstack([_average_ranks(row) for row in r])
    totals = ranks.sum(axis=0)
    s = float(((totals - totals.mean()) ** 2).sum())
    tie_term = 0.0
    for row in r:
        _, counts = np.unique(row, return_counts=True)
        tie_term += float((counts**3 - counts).sum())
    denom = m**2 * (n**3 - n) - m * tie_term
    return 12 * s / denom if denom else float("nan")


def rank_agreement(
    sheets: dict[str, Scores], design: Design, measures: tuple[str, ...] = MEASURES
) -> list[dict[str, str | float]]:
    """Per measure: tau-b for every pair of raters on the cell means, then W across all."""
    names = list(sheets)
    if len(names) < 2:
        raise ValueError("rank agreement needs at least 2 rater sheets")
    vectors = {name: cell_means(design, s, measures) for name, s in sheets.items()}
    rows: list[dict[str, str | float]] = []
    for m in measures:
        flat = {name: vectors[name][m].ravel() for name in names}
        for a, b in itertools.combinations(names, 2):
            tau = kendall_tau_b(flat[a], flat[b])
            rows.append({"measure": m, "comparison": f"{a}~{b}", "statistic": "kendall_tau_b", "value": tau})
        rows.append(
            {
                "measure": m,
                "comparison": "all",
                "statistic": "kendall_w",
                "value": kendall_w(np.vstack([flat[n] for n in names])),
            }
        )
    return rows


def write_rank_agreement(rows: list[dict[str, str | float]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["measure", "comparison", "statistic", "value"])
        for r in rows:
            v = float(r["value"])
            w.writerow([r["measure"], r["comparison"], r["statistic"], "nan" if math.isnan(v) else f"{v:.4f}"])
    return path


def _dodge(values: list[float], gap: float, low: float = -math.inf, high: float = math.inf) -> list[float]:
    """Spread label positions so no two sit closer than `gap`, keeping their order and,
    where the gaps allow, staying inside [low, high]."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    placed = [values[i] for i in order]
    for k in range(1, len(placed)):
        placed[k] = max(placed[k], placed[k - 1] + gap)
    shift = (sum(placed) - sum(values[i] for i in order)) / len(placed)
    placed = [p - shift for p in placed]
    # Pull the stack back inside the range, upper end first so the lower end wins a tie.
    placed = [p - max(0.0, placed[-1] - high) for p in placed]
    placed = [p + max(0.0, low - placed[0]) for p in placed]
    out = [0.0] * len(values)
    for k, i in enumerate(order):
        out[i] = placed[k]
    return out


def plot_cell_means(
    design: Design,
    scores: Scores,
    path: str | Path,
    measures: tuple[str, ...] = ("total", "D1", "D9", "D3"),
    note: str = "",
) -> Path:
    """Figure 1: one panel per measure, fast vs reasoning, one line per family.

    Needs matplotlib (`pip install -e ".[paper]"`). The format follows the file suffix
    (.pdf for the paper, .svg or .png for the repo).
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError('Figure 1 needs matplotlib: pip install -e ".[paper]"') from exc

    means = cell_means(design, scores, measures)
    ink, muted, grid, surface = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    fig, axes = plt.subplots(1, len(measures), figsize=(3.0 * len(measures), 3.4), squeeze=False)
    fig.patch.set_facecolor(surface)
    x = np.arange(len(design.modes))
    for ax, m in zip(axes[0], measures, strict=True):
        top = 18.0 if m == "total" else 2.0
        ax.set_facecolor(surface)
        ends = []
        for i, fam in enumerate(design.families):
            colour, marker = FAMILY_STYLE.get(fam, _FALLBACK_STYLE)
            y = means[m][i]
            ax.plot(x, y, color=colour, linewidth=2, marker=marker, markersize=8, label=fam, zorder=3)
            ax.plot(x, y, linestyle="none", marker=marker, markersize=11, color=surface, zorder=2)
            ends.append(float(y[-1]))
        for fam, pos in zip(design.families, _dodge(ends, gap=top * 0.06, low=0.0, high=top), strict=True):
            ax.annotate(
                fam,
                (x[-1], pos),
                xytext=(10, 0),
                textcoords="offset points",
                va="center",
                fontsize=8,
                color=ink,
                annotation_clip=False,
            )
        ax.set_xticks(x, design.modes, color=muted, fontsize=9)
        ax.set_xlim(-0.25, len(x) - 1 + 0.75)
        # A little room past 0 and the maximum, so markers at the scale ends are not cut.
        ax.set_ylim(-top * 0.05, top * 1.05)
        ax.set_yticks(np.arange(0, top + 1e-9, 3.0 if m == "total" else 0.5))
        ax.set_title("Total (0-18)" if m == "total" else f"{m} {DIM_NAMES[m]}", fontsize=10, color=ink, loc="left")
        ax.tick_params(axis="y", colors=muted, labelsize=8, length=0)
        ax.tick_params(axis="x", length=0)
        ax.grid(axis="y", color=grid, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(grid)
    axes[0][0].set_ylabel("Cell mean score", color=muted, fontsize=9)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=False, fontsize=8, labelcolor=ink)
    if note:
        fig.suptitle(note, fontsize=9, color=muted, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95 if note else 1))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # No creator or date stamps: the same scores give a byte-identical figure, and a PDF
    # carries no tool or author metadata into a double-blind submission.
    meta = {".svg": {"Creator": None, "Date": None}, ".pdf": {"Creator": None, "Producer": None, "CreationDate": None}}
    # A fixed salt gives stable SVG element ids.
    with plt.rc_context({"svg.hashsalt": "modegrid"}):
        fig.savefig(path, facecolor=surface, metadata=meta.get(path.suffix.lower()))
    plt.close(fig)
    return path
