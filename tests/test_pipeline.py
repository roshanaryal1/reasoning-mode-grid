import csv
import shutil
from pathlib import Path

import pytest

from modegrid.analyze import AnalysisError, build_design, run_analysis, write_outputs
from modegrid.blind import build_packets, redact
from modegrid.capture import Capture, CaptureError, check_capture, parse_capture, read_capture, write_capture
from modegrid.cli import main
from modegrid.config import ConfigError, load_grid, unready_families
from modegrid.plan import build_manifest, read_manifest, write_manifest
from modegrid.scores import ScoreError, load_scores, unblind, write_scores
from modegrid.synthetic import synthetic_scores


def test_grid_loads_and_prompt_hash_matches(grid_path):
    grid = load_grid(grid_path)
    assert len(grid.families) >= 5, "LA-P4 needs at least 5 model families"
    assert grid.replicates >= 3
    text = grid.prompts[0].text()
    assert "Mac mini" in text and "=== PROMPT" not in text


def _grid_with_gemini_placeholder(tmp_path, grid_path):
    shutil.copytree(grid_path.parent.parent / "vendor", tmp_path / "vendor")
    (tmp_path / "configs").mkdir()
    text = grid_path.read_text().replace("model: gemini-3.6-flash", "model: FILL-ME", 1)
    assert "model: FILL-ME" in text
    out = tmp_path / "configs" / "grid.yaml"
    out.write_text(text)
    return out


def test_real_grid_has_no_placeholders(grid_path):
    assert unready_families(load_grid(grid_path)) == []


def test_placeholders_are_reported(tmp_path, grid_path):
    unready = unready_families(load_grid(_grid_with_gemini_placeholder(tmp_path, grid_path)))
    assert unready == ["gemini"]


def test_grid_rejects_missing_primary_mode(tmp_path, grid_path):
    root = tmp_path
    shutil.copytree(grid_path.parent.parent / "vendor", root / "vendor")
    (root / "configs").mkdir()
    text = grid_path.read_text().replace(
        '      reasoning:\n        web_label: "claude.ai', '      deep:\n        web_label: "claude.ai', 1
    )
    (root / "configs" / "grid.yaml").write_text(text)
    with pytest.raises(ConfigError):
        load_grid(root / "configs" / "grid.yaml")


def test_manifest_is_complete_and_deterministic(grid_path, tmp_path):
    grid = load_grid(grid_path)
    runs = build_manifest(grid)
    main = [r for r in runs if r.set == "main"]
    checks = [r for r in runs if r.set == "api_check"]
    expected = sum(len(f.modes) for f in grid.families) * len(grid.prompts) * grid.replicates
    assert len(main) == expected
    assert all(r.channel == "web" for r in main), "main runs are chat captures"
    api_families = [f for f in grid.families if f.adapter]
    assert len(checks) == len(api_families) * 2 * grid.api_check_replicates
    assert all(r.channel == "api" for r in checks)
    assert len({r.run_id for r in runs}) == len(runs)
    assert [r.run_id for r in runs] == [r.run_id for r in build_manifest(grid)]
    write_manifest(runs, tmp_path / "runs.csv")
    assert read_manifest(tmp_path / "runs.csv") == runs


def test_capture_round_trip(tmp_path):
    cap = Capture(
        meta={
            "run_id": "x__fast__p1-v1__r1",
            "family": "x",
            "mode": "fast",
            "native_label": "n",
            "channel": "api",
            "model_requested": "m",
            "model_returned": "m",
            "prompt_id": "p1-v1",
            "prompt_sha256": "h",
            "replicate": 1,
            "date_run": "2026-10-01",
            "run_by": "me",
        },
        final_answer="| a | b |\n|---|---|\nverbatim  text with  spaces",
    )
    path = write_capture(cap, tmp_path)
    back = read_capture(path)
    assert back.final_answer == cap.final_answer.strip()
    assert check_capture(back) == []
    with pytest.raises(CaptureError):
        write_capture(cap, tmp_path)


def test_parse_rejects_missing_section():
    with pytest.raises(CaptureError):
        parse_capture("---\nrun_id: a\n---\n\n## Final answer\n\nhi\n")


def test_redaction_masks_identity():
    text = "Model name: Claude Sonnet 5, knowledge cutoff 2026\n\n# Plan\nUse Claude Code and the DeepSeek API."
    out = redact(text, ["Claude Sonnet 5", "Claude", "DeepSeek"])
    assert "Sonnet" not in out and "DeepSeek" not in out
    assert "self-identification line removed" in out
    assert "# Plan" in out


def test_blind_unblind_round_trip(tmp_path):
    caps = [Capture(meta={"run_id": f"f{i}__fast__p__r1"}, final_answer=f"answer {i}") for i in range(4)]
    key = build_packets(caps, [], tmp_path / "packets", tmp_path / "key.csv", seed=1, raters=["r1", "r2"])
    assert len(key) == 4
    sheet = tmp_path / "packets" / "scoresheet-r1.csv"
    rows = list(csv.DictReader(sheet.open()))
    assert {r["blind_id"] for r in rows} == {b for b, _ in key}
    with sheet.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["blind_id", *[f"D{i}" for i in range(1, 10)]])
        for b, _ in key:
            w.writerow([b, *[1] * 9])
    from modegrid.scores import load_key

    run_scores = unblind(load_scores(sheet), load_key(tmp_path / "key.csv"))
    assert set(run_scores) == {c.run_id for c in caps}


def test_scores_reject_out_of_range(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("blind_id,D1,D2,D3,D4,D5,D6,D7,D8,D9\nB001,0,1,2,3,0,0,0,0,0\n")
    with pytest.raises(ScoreError):
        load_scores(p)


def test_analysis_recovers_synthetic_effects(grid_path, tmp_path):
    grid = load_grid(grid_path)
    runs = build_manifest(grid)
    fams = sorted({r.family for r in runs})
    scores = synthetic_scores(fams, grid.replicates, "p1-v1", seed=7)
    design, rows = run_analysis(runs, scores, "p1-v1", n_boot=300, n_perm=200)
    by = {r["dimension"]: r for r in rows}
    assert by["D1"]["verdict"] == "mode > model"
    assert by["D3"]["verdict"] == "model > mode"
    write_outputs(design, rows, tmp_path)
    assert (tmp_path / "variance_table.md").read_text().count("| D") >= 9


def test_analysis_on_a_family_subset(grid_path):
    grid = load_grid(grid_path)
    runs = build_manifest(grid)
    scores = synthetic_scores(sorted({r.family for r in runs}), grid.replicates, "p1-v1", seed=7)
    design, rows = run_analysis(runs, scores, "p1-v1", n_boot=50, n_perm=50, families=["gpt", "qwen", "deepseek"])
    assert design.families == ["deepseek", "gpt", "qwen"]
    assert design.run_ids.shape == (3, 2, grid.replicates)
    assert len(rows) == 10
    with pytest.raises(AnalysisError, match="unknown"):
        run_analysis(runs, scores, "p1-v1", n_boot=10, n_perm=10, families=["gpt", "nope"])
    with pytest.raises(AnalysisError, match="at least 2"):
        run_analysis(runs, scores, "p1-v1", n_boot=10, n_perm=10, families=["gpt"])
    # a family present only as API-check runs is not analysable for this prompt
    no_gemini_main = [r for r in runs if not (r.family == "gemini" and r.set == "main")]
    with pytest.raises(AnalysisError, match="unknown"):
        run_analysis(no_gemini_main, scores, "p1-v1", n_boot=10, n_perm=10, families=["gpt", "qwen", "gemini"])


def test_cli_analyze_accepts_families(tmp_path, monkeypatch, grid_path):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    grid = load_grid(grid_path)
    manifest = tmp_path / "runs.csv"
    assert main(["--manifest", str(manifest), "plan"]) == 0
    runs = read_manifest(manifest)
    scores = synthetic_scores(sorted({r.family for r in runs}), grid.replicates, "p1-v1", seed=7)
    sheet = tmp_path / "adjudicated.csv"
    write_scores(scores, sheet)
    out = tmp_path / "split"
    common = ["--manifest", str(manifest), "--captures", str(tmp_path / "none")]
    args = ["analyze", "--scores", str(sheet), "--out", str(out), "--boot", "20", "--perm", "20"]
    assert main([*common, *args, "--families", "claude,gemini,grok"]) == 0
    assert (out / "variance_table.md").exists()


def test_analysis_refuses_incomplete_grid(grid_path):
    grid = load_grid(grid_path)
    runs = build_manifest(grid)
    scores = synthetic_scores(sorted({r.family for r in runs}), grid.replicates, "p1-v1", seed=7)
    scores.pop(next(iter(scores)))
    with pytest.raises(AnalysisError):
        run_analysis(runs, scores, "p1-v1", n_boot=10, n_perm=10)


def test_design_excludes_non_primary_modes(grid_path):
    grid = load_grid(grid_path)
    design = build_design(build_manifest(grid), "p1-v1")
    assert design.modes == ["fast", "reasoning"]


def test_cli_demo_and_power(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    assert main(["demo", "--out", str(tmp_path), "--boot", "100"]) == 0
    assert "SYNTHETIC" in (tmp_path / "variance_table.md").read_text()
    assert main(["power", "--families", "5", "--replicates", "3", "--sims", "10"]) == 0


def test_cli_run_refuses_placeholders(tmp_path, monkeypatch, capsys, grid_path):
    config = str(_grid_with_gemini_placeholder(tmp_path, grid_path))
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    manifest = tmp_path / "runs.csv"
    base = ["--config", config, "--manifest", str(manifest), "--captures", str(tmp_path / "c")]
    assert main([*base, "plan"]) == 0
    # gemini holds a FILL-ME, so a run that includes it is refused
    assert main([*base, "run", "--dry-run"]) == 2
    assert "gemini" in capsys.readouterr().out
    assert main([*base, "run", "--dry-run", "--family", "claude"]) == 0


def test_write_scores_adds_total(tmp_path):
    write_scores({"r1": {f"D{i}": 1 for i in range(1, 10)}}, tmp_path / "a.csv")
    assert "9" in (tmp_path / "a.csv").read_text().splitlines()[1]


def _cap(run_id, words=3, **meta):
    base = {
        "run_id": run_id,
        "family": "x",
        "mode": "fast",
        "native_label": "n",
        "channel": "web",
        "model_requested": "m",
        "model_returned": "m",
        "prompt_id": "p1-v1",
        "prompt_sha256": "h",
        "replicate": 1,
        "date_run": "2026-10-01",
        "run_by": "me",
    }
    return Capture(meta={**base, **meta}, final_answer=" ".join(["word"] * words))


def test_fill_in_left_in_capture_is_flagged():
    assert check_capture(_cap("a", model_returned="FILL IN: the model name"))


def test_api_check_runs_are_not_analysed(grid_path):
    grid = load_grid(grid_path)
    design = build_design(build_manifest(grid), "p1-v1")
    assert not any("apicheck" in str(rid) for rid in design.run_ids.ravel())


def test_blind_skips_api_check_captures(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(root)
    manifest = tmp_path / "runs.csv"
    caps_dir = tmp_path / "caps"
    assert main(["--manifest", str(manifest), "plan"]) == 0
    runs = read_manifest(manifest)
    main_run = next(r for r in runs if r.set == "main")
    check_run = next(r for r in runs if r.set == "api_check")
    write_capture(_cap(main_run.run_id), caps_dir)
    write_capture(_cap(check_run.run_id), caps_dir)
    out, key = tmp_path / "packets", tmp_path / "key.csv"
    args = ["--manifest", str(manifest), "--captures", str(caps_dir), "blind", "--out", str(out), "--key", str(key)]
    assert main(args) == 0
    assert len(list((out / "answers").glob("*.md"))) == 1


def test_new_capture_refuses_api_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    manifest = tmp_path / "runs.csv"
    assert main(["--manifest", str(manifest), "plan"]) == 0
    check_run = next(r for r in read_manifest(manifest) if r.set == "api_check")
    web_run = next(r for r in read_manifest(manifest) if r.set == "main")
    common = ["--manifest", str(manifest), "--captures", str(tmp_path / "c")]
    assert main([*common, "new-capture", check_run.run_id]) == 2
    assert main([*common, "new-capture", web_run.run_id]) == 0
    created = read_capture(tmp_path / "c" / f"{web_run.run_id}.md")
    assert created.meta["channel"] == "web" and created.meta["set"] == "main"


def test_check_modes_confirms_a_working_switch(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    manifest = tmp_path / "runs.csv"
    assert main(["--manifest", str(manifest), "plan"]) == 0
    caps_dir = tmp_path / "caps"
    for r in read_manifest(manifest):
        if r.set == "api_check" and r.family == "claude":
            rt = 0 if r.mode == "fast" else 900
            write_capture(
                _cap(r.run_id, words=100 if r.mode == "fast" else 300, usage={"reasoning_tokens": rt}), caps_dir
            )
    out = tmp_path / "mode_check.md"
    assert main(["--manifest", str(manifest), "--captures", str(caps_dir), "check-modes", "--out", str(out)]) == 0
    text = out.read_text()
    assert "| claude | 100 | 300 | 0 | 900 |" in text and "switch confirmed" in text
    assert "missing capture(s)" in text  # the other families have no captures yet


def test_check_modes_separates_lowest_available_from_a_broken_switch(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    manifest = tmp_path / "runs.csv"
    assert main(["--manifest", str(manifest), "plan"]) == 0
    caps_dir = tmp_path / "caps"
    # gemini: fast cannot be disabled but uses far fewer tokens; grok: fast uses more
    tokens = {("gemini", "fast"): 200, ("gemini", "reasoning"): 3000, ("grok", "fast"): 500, ("grok", "reasoning"): 300}
    for r in read_manifest(manifest):
        if r.set == "api_check" and (r.family, r.mode) in tokens:
            write_capture(_cap(r.run_id, usage={"reasoning_tokens": tokens[(r.family, r.mode)]}), caps_dir)
    out = tmp_path / "mode_check.md"
    assert main(["--manifest", str(manifest), "--captures", str(caps_dir), "check-modes", "--out", str(out)]) == 0
    rows = {line.split("|")[1].strip(): line for line in out.read_text().splitlines() if line.startswith("| g")}
    assert "lowest available" in rows["gemini"] and "CHECK" not in rows["gemini"]
    assert "switch confirmed" not in rows["gemini"]
    assert "CHECK: reasoning tokens do not separate the modes" in rows["grok"]


def test_agreement_writes_gate_csv(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    sheets = []
    for name, shift in (("r1", 0), ("r2", 1)):
        p = tmp_path / f"{name}.csv"
        with p.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["blind_id", *[f"D{i}" for i in range(1, 10)]])
            for b in range(1, 9):
                w.writerow([f"B{b:03d}", *[(b + shift * (b % 3 == 0)) % 3] * 9])
        sheets.append(str(p))
    out = tmp_path / "alpha.csv"
    assert main(["agreement", *sheets, "--out", str(out)]) == 0
    rows = list(csv.DictReader(out.open()))
    assert [r["dimension"] for r in rows] == [f"D{i}" for i in range(1, 10)]
    assert all(-1.0 <= float(r["alpha"]) <= 1.0 for r in rows)


def test_blinding_check_detects_leak(tmp_path, monkeypatch):
    from modegrid.blind import guess_accuracy

    truth = {f"run{i}": ("claude" if i % 2 else "gpt", "fast" if i < 10 else "reasoning") for i in range(20)}
    key = {f"B{i:03d}": f"run{i}" for i in range(20)}
    perfect = tmp_path / "perfect.csv"
    blank = tmp_path / "blank.csv"
    for path, fill in ((perfect, True), (blank, False)):
        with path.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["blind_id", "guess_family", "guess_mode"])
            for b, rid in key.items():
                fam, mode = truth[rid]
                w.writerow([b, fam if fill else "", mode if fill else ""])
    res = guess_accuracy(perfect, key, truth, n_families=6)
    assert res["guess_mode"]["accuracy"] == 1.0 and res["guess_mode"]["p_value"] < 0.001
    assert res["guess_family"]["p_value"] < 0.001
    empty = guess_accuracy(blank, key, truth, n_families=6)
    assert empty["guess_mode"]["guessed"] == 0


def test_family_max_tokens_override(tmp_path, grid_path):
    grid = load_grid(grid_path)
    assert grid.family("gpt").max_tokens == 6000  # fits a 10,000 tokens-per-minute account limit
    assert grid.family("claude").max_tokens is None  # falls back to the grid-wide limit
    shutil.copytree(grid_path.parent.parent / "vendor", tmp_path / "vendor")
    (tmp_path / "configs").mkdir()
    for value in ("0", "true", "1.5"):
        bad = grid_path.read_text().replace("max_tokens: 6000", f"max_tokens: {value}", 1)
        (tmp_path / "configs" / "grid.yaml").write_text(bad)
        with pytest.raises(ConfigError):
            load_grid(tmp_path / "configs" / "grid.yaml")


def test_empty_answer_allowed_only_for_truncated_api_checks():
    # an API check that spent its whole limit on thinking is still evidence of the switch
    truncated_check = _cap("x__reasoning__p1-v1__apicheck1", words=0, set="api_check", finish_reason="length")
    assert check_capture(truncated_check) == []
    # but a scored chat capture, or an API check that finished normally, must have an answer
    assert check_capture(_cap("x__fast__p1-v1__r1", words=0, set="main", finish_reason="length"))
    assert check_capture(_cap("x__fast__p1-v1__apicheck1", words=0, set="api_check", finish_reason="stop"))


def test_run_retries_flag_limits_attempts(tmp_path, monkeypatch, grid_path):
    # a long reasoning call that times out must not be re-sent (and re-billed) silently
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = {"n": 0}

    class TimesOut:
        def complete(self, *a, **kw):
            calls["n"] += 1
            raise TimeoutError("read timed out")

    monkeypatch.setattr("modegrid.cli.adapter_for", lambda fam: TimesOut())
    manifest = tmp_path / "runs.csv"
    common = ["--manifest", str(manifest), "--captures", str(tmp_path / "c")]
    assert main([*common, "plan"]) == 0
    with pytest.raises(TimeoutError):
        main([*common, "run", "--family", "claude", "--limit", "1", "--retries", "1"])
    assert calls["n"] == 1


def test_consensus_is_the_median_of_three_raters(tmp_path):
    from modegrid.scores import consensus

    row = {f"D{i}": 1 for i in range(1, 10)}
    human = {"B001": {**row, "D1": 2}, "B002": row}
    llm_a = {"B001": {**row, "D1": 0}, "B002": {**row, "D3": 2}}
    llm_b = {"B001": {**row, "D1": 2}, "B002": {**row, "D3": 0}}
    out = consensus([human, llm_a, llm_b])
    assert out["B001"]["D1"] == 2 and out["B002"]["D3"] == 1
    with pytest.raises(ScoreError, match="odd"):
        consensus([human, llm_a])
    with pytest.raises(ScoreError, match="same answers"):
        consensus([human, llm_a, {"B001": row}])


def test_cli_consensus_writes_blind_sheet(tmp_path):
    rows = {"B001": {f"D{i}": i % 3 for i in range(1, 10)}}
    paths = []
    for name in ("human", "llm-a", "llm-b"):
        p = tmp_path / f"{name}.csv"
        write_scores(rows, p, id_col="blind_id")
        paths.append(str(p))
    out = tmp_path / "adjudicated-blind.csv"
    assert main(["consensus", *paths, "--out", str(out)]) == 0
    assert load_scores(out)["B001"]["D2"] == 2
