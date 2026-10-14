import csv

import numpy as np
import pytest

from modegrid.analyze import build_design
from modegrid.cells import (
    FAMILY_STYLE,
    _dodge,
    cell_means,
    kendall_tau_b,
    kendall_w,
    plot_cell_means,
    rank_agreement,
    write_cell_means,
)
from modegrid.cli import main
from modegrid.config import load_grid
from modegrid.plan import build_manifest, write_manifest
from modegrid.scores import write_scores
from modegrid.synthetic import synthetic_scores


@pytest.fixture()
def grid(grid_path):
    g = load_grid(grid_path)
    runs = build_manifest(g)
    design = build_design(runs, g.prompts[0].id)
    scores = synthetic_scores(design.families, g.replicates, g.prompts[0].id, seed=3)
    return g, runs, design, scores


# Reference values from scipy.stats.kendalltau and friedmanchisquare / (m (n - 1)),
# computed once; scipy is not a dependency.
def test_tau_b_matches_scipy_with_ties():
    x = [1, 2, 2, 3, 4, 5, 5, 6, 7, 8, 9, 9]
    y = [2, 1, 3, 3, 5, 4, 6, 8, 7, 9, 9, 8]
    assert kendall_tau_b(x, y) == pytest.approx(0.8253968253968252)


def test_tau_b_extremes_and_constant():
    x = list(range(12))
    assert kendall_tau_b(x, x) == pytest.approx(1.0)
    assert kendall_tau_b(x, x[::-1]) == pytest.approx(-1.0)
    assert np.isnan(kendall_tau_b(x, [3] * 12))
    with pytest.raises(ValueError):
        kendall_tau_b([1, 2], [1, 2, 3])


def test_kendall_w_matches_friedman():
    no_ties = np.array([[1, 2, 3, 4, 5, 6], [2, 1, 3, 4, 6, 5], [1, 3, 2, 5, 4, 6]])
    ties = np.array([[1, 1, 2, 3, 3, 4], [1, 2, 2, 3, 4, 4], [2, 1, 3, 3, 4, 5]])
    assert kendall_w(no_ties) == pytest.approx(0.873015873015873)
    assert kendall_w(ties) == pytest.approx(0.9333333333333333)
    assert kendall_w(np.vstack([no_ties[0]] * 3)) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        kendall_w(np.array([[1, 2, 3]]))


def test_cell_means_and_csv(grid, tmp_path):
    _, _, design, scores = grid
    means = cell_means(design, scores)
    i, j = design.families.index("qwen"), design.modes.index("reasoning")
    ids = [r for r in scores if r.startswith("qwen__reasoning__")]
    assert means["D1"][i, j] == pytest.approx(np.mean([scores[r]["D1"] for r in ids]))
    assert means["total"][i, j] == pytest.approx(np.mean([sum(scores[r].values()) for r in ids]))
    with write_cell_means(design, scores, tmp_path / "cells.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(design.families) * 2
    assert {r["n"] for r in rows} == {str(len(design.replicates))}


def test_rank_agreement_identical_and_reversed(grid):
    _, _, design, scores = grid
    flipped = {rid: {d: 2 - v for d, v in row.items()} for rid, row in scores.items()}
    rows = rank_agreement({"a": scores, "b": scores, "c": flipped}, design, measures=("total",))
    by = {(r["comparison"], r["statistic"]): float(r["value"]) for r in rows}
    assert by[("a~b", "kendall_tau_b")] == pytest.approx(1.0)
    assert by[("a~c", "kendall_tau_b")] == pytest.approx(-1.0)
    assert 0 <= by[("all", "kendall_w")] < 1
    with pytest.raises(ValueError):
        rank_agreement({"a": scores}, design)


def test_dodge_keeps_order_and_gap():
    out = _dodge([1.0, 1.0, 1.05, 5.0], gap=0.5)
    assert out[0] <= out[1] <= out[2] < out[3]
    assert min(b - a for a, b in zip(sorted(out), sorted(out)[1:], strict=False)) >= 0.5 - 1e-9
    edge = _dodge([0.0, 0.0, 2.0], gap=0.3, low=0.0, high=2.0)
    assert edge[0] >= 0.0 and edge[1] - edge[0] >= 0.3 - 1e-9 and edge[2] <= 2.0


def test_every_family_has_its_own_style(grid):
    g, *_ = grid
    styles = [FAMILY_STYLE[f.id] for f in g.families]
    assert len(set(styles)) == len(styles)


def test_figure_is_reproducible_and_carries_no_metadata(grid, tmp_path):
    pytest.importorskip("matplotlib")
    _, _, design, scores = grid
    a = plot_cell_means(design, scores, tmp_path / "a.svg").read_bytes()
    b = plot_cell_means(design, scores, tmp_path / "b.svg").read_bytes()
    assert a == b
    assert b"Matplotlib" not in a and b"<dc:date>" not in a
    pdf = plot_cell_means(design, scores, tmp_path / "f.pdf").read_bytes()
    assert pdf.startswith(b"%PDF") and b"/Author" not in pdf


def test_cli_cells_and_rank_agreement(grid, tmp_path, capsys):
    pytest.importorskip("matplotlib")
    _, runs, design, scores = grid
    manifest = tmp_path / "runs.csv"
    write_manifest(runs, manifest)
    sheets = []
    for k, name in enumerate(["human", "llm-a", "llm-b"]):
        s = synthetic_scores(design.families, len(design.replicates), "p1-v1", seed=10 + k)
        path = tmp_path / f"{name}-unblinded.csv"
        write_scores(s, path)
        sheets.append(str(path))
    write_scores(scores, tmp_path / "adjudicated.csv")
    base = ["--manifest", str(manifest)]
    out = tmp_path / "results"
    args = ["cells", "--scores", str(tmp_path / "adjudicated.csv"), "--out", str(out), "--figure", "figure1.svg"]
    assert main([*base, *args]) == 0
    assert (out / "cell_means.csv").exists() and (out / "figure1.svg").exists()
    assert main([*base, *args[:-2], "--families", "gpt,qwen"]) == 0
    with (out / "cell_means.csv").open() as fh:
        assert {r["family"] for r in csv.DictReader(fh)} == {"gpt", "qwen"}
    agree = tmp_path / "rank.csv"
    assert main([*base, "rank-agreement", *sheets, "--out", str(agree)]) == 0
    printed = capsys.readouterr().out
    assert "human~llm-a" in printed and "kendall_w" in printed
    with agree.open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 10 * 4  # 10 measures x (3 pairs + W)
