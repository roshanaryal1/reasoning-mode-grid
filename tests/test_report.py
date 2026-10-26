import csv
from pathlib import Path

from modegrid import DIMS
from modegrid.analyze import ROW_FIELDS
from modegrid.cli import main
from modegrid.config import load_grid
from modegrid.plan import read_manifest
from modegrid.report import build_report
from modegrid.scores import write_scores
from modegrid.synthetic import synthetic_scores


def _write(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _row(dim: str, verdict: str, **over: object) -> dict[str, object]:
    row: dict[str, object] = {k: "0.100" for k in ROW_FIELDS}
    row.update(
        dimension=dim,
        name=dim,
        verdict=verdict,
        omega2_mode="0.300",
        omega2_family="0.100",
        omega2_interaction="0.050",
        delta_omega2="0.200",
        ci_low="0.050",
        ci_high="0.350",
        mode_effect="2.000",
        mode_effect_ci_low="1.000",
        mode_effect_ci_high="3.000",
        p_mode="0.001",
    )
    row.update(over)
    return row


def _table(path: Path, **verdicts: str) -> None:
    rows = [_row(d, verdicts.get(d, "inconclusive")) for d in (*DIMS, "total")]
    _write(path, ROW_FIELDS, rows)


def _agreement(path: Path, total: float, dims: float = 0.9) -> None:
    rows = [{"dimension": d, "alpha": dims, "exact_agreement_1v2": 0.7, "status": "ok"} for d in DIMS]
    rows.append({"dimension": "total", "alpha": total, "exact_agreement_1v2": 0.2, "status": "ok"})
    _write(path, ["dimension", "alpha", "exact_agreement_1v2", "status"], rows)


def _blinding(path: Path, mode_p: dict[str, float]) -> None:
    rows = []
    for rater, p in mode_p.items():
        for guess, pv in (("guess_family", 0.001), ("guess_mode", p)):
            rows.append(
                {
                    "rater": rater,
                    "guess": guess,
                    "items": 60,
                    "guessed": 50,
                    "correct": 30,
                    "accuracy": 0.6,
                    "chance": 0.5,
                    "p_value": pv,
                }
            )
    _write(path, ["rater", "guess", "items", "guessed", "correct", "accuracy", "chance", "p_value"], rows)


def test_report_names_every_missing_file(tmp_path):
    text = build_report(tmp_path / "results", tmp_path / "scores")
    assert text.count("Not run yet") >= 8
    assert "modegrid analyze --agreement results/agreement.csv" in text
    assert "--out results/blinding_check.csv" in text


def test_supported_h4_between_bars_is_tentative(tmp_path):
    res = tmp_path / "results"
    _table(res / "variance_table.csv", total="mode > model")
    _agreement(res / "agreement.csv", total=0.72)
    text = build_report(res, tmp_path)
    assert "H4 stays confirmatory" in text
    assert "- H4 status: yes, tentative (alpha 0.72 below 0.800)" in text


def test_firm_h4_and_blinding_rule(tmp_path):
    res = tmp_path / "results"
    _table(res / "variance_table.csv", total="mode > model")
    _agreement(res / "agreement.csv", total=0.85)
    _blinding(res / "blinding_check.csv", {"human": 0.01, "llm-a": 0.02, "llm-b": 0.03})
    text = build_report(res, tmp_path)
    assert "- H4 status: yes, tentative, mode blinding failed" in text
    assert "All three beat chance" in text

    _blinding(res / "blinding_check.csv", {"human": 0.01, "llm-a": 0.5, "llm-b": 0.5})
    text = build_report(res, tmp_path)
    assert "- H4 status: yes\n" in text
    assert "Beat chance on mode (p < 0.05): human." in text
    assert "Raters who did not beat chance: per-rater runs missing." in text


def test_low_total_alpha_makes_h4_exploratory(tmp_path):
    res = tmp_path / "results"
    _table(res / "variance_table.csv", total="mode > model")
    _agreement(res / "agreement.csv", total=0.5)
    text = build_report(res, tmp_path)
    assert "H4 is exploratory" in text
    assert "- H4 status: exploratory (alpha 0.50 below 0.667)" in text


def test_h3_outcomes_and_ci_p_disagreement(tmp_path):
    res = tmp_path / "results"
    _table(res / "variance_table.csv", D3="model > mode")
    assert "model > mode, which supports H3" in build_report(res, tmp_path)

    rows = [_row(d, "inconclusive") for d in (*DIMS, "total")]
    rows[2] = _row("D3", "mode > model", mode_effect="-1.0", mode_effect_ci_low="-2.0", mode_effect_ci_high="-0.5")
    rows[-1] = _row("total", "inconclusive", p_mode="0.200")
    _write(res / "variance_table.csv", ROW_FIELDS, rows)
    text = build_report(res, tmp_path)
    assert "supports the hallucination account" in text
    assert "disagree: the CI excludes zero but p mode >= 0.05" in text


def test_report_cli_on_a_real_analysis(tmp_path, monkeypatch, grid_path, capsys):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    grid = load_grid(grid_path)
    manifest = tmp_path / "runs.csv"
    assert main(["--manifest", str(manifest), "plan"]) == 0
    runs = read_manifest(manifest)
    scores = synthetic_scores(sorted({r.family for r in runs}), grid.replicates, "p1-v1", seed=7)
    write_scores(scores, tmp_path / "scores" / "adjudicated.csv")
    res = tmp_path / "results"
    common = ["--manifest", str(manifest), "--captures", str(tmp_path / "none")]
    sheet = str(tmp_path / "scores" / "adjudicated.csv")
    assert main([*common, "analyze", "--scores", sheet, "--out", str(res), "--boot", "20", "--perm", "20"]) == 0
    assert main([*common, "cells", "--scores", sheet, "--out", str(res)]) == 0
    assert main(["report", "--results", str(res), "--scores", str(tmp_path / "scores")]) == 0
    text = (res / "report.md").read_text(encoding="utf-8")
    assert "60 of 60 planned answers have a consensus score." in text
    assert "families moved in the same direction as the average" in text
    assert "- H4 status:" in text
    assert "wrote" in capsys.readouterr().out


def test_length_check_uses_mode_effect_and_replaced_h4_is_reported(tmp_path):
    res = tmp_path / "results"
    rows = [_row(d, "inconclusive") for d in (*DIMS, "total")]
    # delta moves away from zero after length adjustment, but the mode effect halves.
    rows[-1] = _row(
        "total",
        "model > mode",
        delta_omega2="-0.500",
        rank_delta_omega2="-0.550",
        length_adj_delta_omega2="-0.600",
        length_adj_mode_effect="1.000",
    )
    _write(res / "variance_table.csv", ROW_FIELDS, rows)
    text = build_report(res, tmp_path)
    assert "| total | -0.500 | -0.550 | yes | -0.600 | 2.000 | 1.000 | yes |" in text
    assert "own-vendor scores replaced" not in text

    _write(res / "own-vendor-replaced" / "variance_table.csv", ROW_FIELDS, rows)
    text = build_report(res, tmp_path)
    assert "Exploratory, not pre-registered: H4 with each LLM rater's own-vendor scores replaced" in text
    assert "- verdict: model > mode (consensus model > mode)" in text
