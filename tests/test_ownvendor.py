import csv

import pytest

from modegrid import DIMS
from modegrid.cli import main
from modegrid.ownvendor import own_vendor, replaced_consensus
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


def test_replaced_consensus_removes_planted_self_preference():
    s = _sheets()
    merged = replaced_consensus(s, [("llm-a", "claude"), ("llm-b", "gpt")])
    # llm-a's bump on Claude D1 is replaced by the mean of human and llm-b, which agree.
    for rid, row in merged.items():
        for d in DIMS:
            assert row[d] == s["human"][rid][d]


def test_replaced_consensus_uses_mean_of_the_others():
    a = {"claude__fast__p1-v1__r1": {d: 0 for d in DIMS}, "gpt__fast__p1-v1__r1": {d: 0 for d in DIMS}}
    b = {k: {d: 1 for d in DIMS} for k in a}
    c = {k: {d: 2 for d in DIMS} for k in a}
    merged = replaced_consensus({"human": a, "llm-a": c, "llm-b": b}, [("llm-a", "claude")])
    # Claude: llm-a's 2 becomes mean(0, 1) = 0.5, so the median of (0, 0.5, 1) is 0.5.
    assert merged["claude__fast__p1-v1__r1"]["D1"] == 0.5
    # GPT is untouched: median of (0, 2, 1) is 1.
    assert merged["gpt__fast__p1-v1__r1"]["D1"] == 1


def test_replaced_consensus_bad_inputs():
    s = _sheets()
    with pytest.raises(ValueError, match="odd number"):
        replaced_consensus({"human": s["human"], "llm-a": s["llm-a"]}, [("llm-a", "claude")])
    with pytest.raises(ValueError, match="no sheet"):
        replaced_consensus(s, [("llm-c", "claude")])
    short = {k: v for k, v in list(s["llm-b"].items())[1:]}
    with pytest.raises(ValueError, match="same answers"):
        replaced_consensus({**s, "llm-b": short}, [("llm-a", "claude")])


def test_cli_writes_replaced_analysis(tmp_path, grid_path, monkeypatch):
    from modegrid.config import load_grid
    from modegrid.plan import build_manifest, write_manifest

    manifest = tmp_path / "runs.csv"
    write_manifest(build_manifest(load_grid(grid_path)), manifest)
    files = []
    for name, sheet in _sheets().items():
        path = tmp_path / f"{name}-unblinded.csv"
        write_scores(sheet, path)
        files.append(str(path))
    out_dir = tmp_path / "replaced"
    args = ["--manifest", str(manifest), "--captures", str(tmp_path / "none"), "own-vendor", *files]
    args += ["--boot", "50", "--perm", "50", "--out", str(tmp_path / "own.csv"), "--replaced-out", str(out_dir)]
    assert main(args) == 0
    md = (out_dir / "variance_table.md").read_text()
    assert "Exploratory, not pre-registered" in md
    assert "llm-a on claude" in md
