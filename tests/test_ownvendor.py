import csv

import pytest

from modegrid import DIMS
from modegrid.cli import main
from modegrid.ownvendor import own_vendor
from modegrid.scores import write_scores
from modegrid.synthetic import synthetic_scores

FAMILIES = ["claude", "deepseek", "gemini", "gpt", "grok", "qwen"]


def _sheets():
    base = synthetic_scores(FAMILIES, 5, "p1-v1", seed=4)
    # llm-a gives Claude answers one extra point on D1 where it can, and is otherwise identical.
    bumped = {
        rid: {d: min(2, v + 1) if (d == "D1" and rid.startswith("claude__")) else v for d, v in row.items()}
        for rid, row in base.items()
    }
    return {"human": base, "llm-a": bumped, "llm-b": base}


def test_identical_raters_show_no_self_preference():
    s = _sheets()
    rows = own_vendor({"human": s["human"], "llm-b": s["llm-b"]}, "llm-b", "gpt", n_boot=200)
    assert all(r["self_preference"] == 0 and r["own_gap"] == 0 for r in rows)
    assert {r["measure"] for r in rows} == {"total", *DIMS}
    assert rows[0]["n_own"] == 10 and rows[0]["n_rest"] == 50


def test_planted_self_preference_is_found():
    s = _sheets()
    by = {r["measure"]: r for r in own_vendor(s, "llm-a", "claude", n_boot=500)}
    bumped = sum(1 for rid, row in s["human"].items() if rid.startswith("claude__") and row["D1"] < 2)
    assert bumped > 0
    expected = bumped / 10  # a full point per bumped answer: the two other raters are unchanged
    assert by["D1"]["own_gap"] == pytest.approx(expected)
    assert by["D1"]["baseline_gap"] == 0
    assert by["total"]["self_preference"] == pytest.approx(expected)
    assert by["D1"]["self_preference_ci_low"] > 0
    assert by["D2"]["self_preference"] == 0


def test_bad_inputs():
    s = _sheets()
    with pytest.raises(ValueError, match="no sheet"):
        own_vendor(s, "llm-c", "claude")
    with pytest.raises(ValueError, match="other rater"):
        own_vendor({"llm-a": s["llm-a"]}, "llm-a", "claude")
    with pytest.raises(ValueError, match="answers both"):
        own_vendor(s, "llm-a", "mistral")


def test_cli_defaults_to_both_llm_raters(tmp_path, capsys):
    files = []
    for name, sheet in _sheets().items():
        path = tmp_path / f"{name}-unblinded.csv"
        write_scores(sheet, path)
        files.append(str(path))
    out = tmp_path / "own.csv"
    assert main(["own-vendor", *files, "--boot", "200", "--out", str(out)]) == 0
    rows = list(csv.DictReader(out.open()))
    assert {(r["rater"], r["family"]) for r in rows} == {("llm-a", "claude"), ("llm-b", "gpt")}
    assert len(rows) == 2 * 10
    assert "self-preference" in capsys.readouterr().out
