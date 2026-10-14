import csv
import shutil
from pathlib import Path

import pytest

from modegrid.analyze import AnalysisError, build_design, run_analysis, score_array, write_outputs
from modegrid.blind import build_packets, redact, strip_app_artifacts, strip_self_disclosure
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
    text = grid_path.read_text().replace("model: gemini-3.8-flash", "model: FILL-ME", 1)
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


def test_changed_run_time_needs_a_reason():
    meta = {k: "x" for k in ("run_id", "family", "mode", "native_label", "channel", "model_requested")}
    meta |= {"model_returned": "m", "prompt_id": "p", "prompt_sha256": "h", "replicate": 1, "run_by": "me"}
    meta |= {"date_stamped": "2026-10-13T01:00:00+00:00", "date_run": "2026-10-13T01:00:00+00:00"}
    assert check_capture(Capture(meta=dict(meta), final_answer="a")) == []
    meta["date_run"] = "2026-10-13T05:00:00+00:00"
    assert any("date_note" in p for p in check_capture(Capture(meta=dict(meta), final_answer="a")))
    meta["date_note"] = "template made in the morning, prompt sent after lunch"
    assert check_capture(Capture(meta=dict(meta), final_answer="a")) == []


def test_parse_rejects_missing_section():
    with pytest.raises(CaptureError):
        parse_capture("---\nrun_id: a\n---\n\n## Final answer\n\nhi\n")


def test_redaction_masks_identity():
    text = "Model name: Claude Sonnet 5, knowledge cutoff 2026\n\n# Plan\nUse Claude Code and the DeepSeek API."
    out = redact(text, ["Claude Sonnet 5", "Claude", "DeepSeek"])
    assert "Sonnet" not in out
    assert "REDACTED" not in out and "removed" not in out
    assert out.startswith("# Plan")


@pytest.mark.parametrize(
    "line",
    [
        "**Model:** Claude 3.7 Sonnet (Architecture Review Engine)",
        "**Model**: Claude 3.5 Sonnet (Simulated Instance)  ",
        "- **Model Name & Version:** Claude 3.5 Sonnet",
        "Model: Qwen3.8",
    ],
)
def test_redaction_removes_model_label_lines(line):
    out = redact(f"# Plan\n\n{line}\n\nBody.", [])
    assert out == "# Plan\n\nBody."
    assert "Sonnet" not in out and "Qwen3.8" not in out
    assert "Body." in out


def test_redaction_leaves_no_header_shell():
    # What a removed header leaves at the top would itself hint at the family.
    text = "# Response Header\n\n**Model:** X 1\nKnowledge cutoff: 2025\n\n---\n\n## Decisions\n\nBody."
    assert redact(text, []) == "## Decisions\n\nBody."
    text = "**System Metadata:**\n- Model name: X\n\n---\n\n### Plan\n\n\n\nBody."
    assert redact(text, []) == "### Plan\n\nBody."


def test_redaction_without_header_keeps_top_as_written():
    text = "---\n\n# Response Header\n\nBody."
    assert redact(text, []) == text


def test_redaction_keeps_model_table_rows_in_header():
    text = "| Layer | Choice |\n| --- | --- |\n| Primary model | Qwen3.6-35B-A3B |\n| Model router | rules: first |"
    assert redact(text, []) == text


def test_redaction_keeps_names_used_as_content():
    # D2-D4 need the recommended models and tools visible to raters
    text = "\n" * 12 + (
        "Run Qwen3-Coder via Ollama, use Claude Code, and tools such as DeepSeek or Gemini CLI.\n"
        "Gemma is a model family developed by Google. As Google explains, I think it fits."
    )
    out = redact(text, ["Claude", "DeepSeek", "Gemini", "Qwen", "Google"])
    assert out == text


def test_redaction_masks_self_reference_in_body():
    body = "\n" * 12 + (
        "I'm Claude, so take this with care. As ChatGPT, I cannot browse.\n"
        "I am an AI model developed by Google. My name is Grok. I was trained by Anthropic."
    )
    out = redact(body, ["Claude", "ChatGPT", "Google", "Grok", "Anthropic"])
    for name in ("Claude", "ChatGPT", "Google", "Grok", "Anthropic"):
        assert name not in out
    assert out.count("[REDACTED]") == 5


def test_strip_app_artifacts_removes_chatgpt_citation_chips():
    text = (
        "Both deserve direct testing.&#x20;\n\n"
        "[image](https://www.google.com/s2/favicons?domain=https://github.com\\&sz=32)\n\n"
        "GitHub\n\n+1\n\n\n\n"
        "Next paragraph stays.\n\n"
        "[image](https://www.google.com/s2/favicons?domain=https://ollama.com\\&sz=32)\n\n"
        "Ollama\n\n\n\n"
        "Last paragraph stays."
    )
    out = strip_app_artifacts(text)
    assert "favicons" not in out and "&#x20;" not in out
    assert "GitHub" not in out and "+1" not in out and "\nOllama\n" not in out
    assert "Both deserve direct testing." in out
    assert "Next paragraph stays." in out and "Last paragraph stays." in out


def test_strip_app_artifacts_keeps_diagram_labels_and_drops_css():
    line = (
        "\\#chatgpt-mermaid-\\_r_j6\\_{font-family:x;}#chatgpt-mermaid-\\_r_j6\\_ p{margin:0;}Phone / LaptopSupervisor"
    )
    out = strip_app_artifacts(f"## B. Diagram\n\n{line}\n\nAfter.")
    assert "chatgpt" not in out and "font-family" not in out
    assert "Phone / LaptopSupervisor" in out and "After." in out


def test_strip_app_artifacts_removes_app_images_and_grok_tags():
    text = (
        "[Tailscale for iPhone](https://images.openai.com/static-rsc-4/abc?purpose=inline)\n\n"
        "- OpenHands docs, primary [web:40]\n- oMLX site, primary [web:64, web:67]\n"
        "Keep [[evidence_id]] placeholders and [1] footnotes."
    )
    out = strip_app_artifacts(text)
    assert "images.openai.com" not in out and "[web:" not in out
    assert "- OpenHands docs, primary" in out and "- oMLX site, primary" in out
    assert "[[evidence_id]]" in out and "[1]" in out


def test_strip_app_artifacts_leaves_plain_answers_unchanged():
    text = "# Plan\n\nUse llama.cpp and Ollama.\n\n| a | b |\n| - | - |\n| 1 | 2 |"
    assert strip_app_artifacts(text) == text


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


def test_variance_components_are_reported(grid_path, tmp_path):
    # Pre-registration section 5 lists the random-effects components among the statistics
    # reported for every dimension, labelled exploratory.
    grid = load_grid(grid_path)
    runs = build_manifest(grid)
    fams = sorted({r.family for r in runs})
    scores = synthetic_scores(fams, grid.replicates, "p1-v1", seed=7)
    design, rows = run_analysis(runs, scores, "p1-v1", n_boot=50, n_perm=50)
    by = {r["dimension"]: r for r in rows}
    y = score_array(design, scores, "D1")
    a, b, n = y.shape
    cell, fam, grand = y.mean(axis=2), y.mean(axis=(1, 2)), y.mean()
    mode = y.mean(axis=(0, 2))
    ms_inter = n * ((cell - fam[:, None] - mode[None, :] + grand) ** 2).sum() / ((a - 1) * (b - 1))
    ms_fam = b * n * ((fam - grand) ** 2).sum() / (a - 1)
    assert by["D1"]["vc_family"] == pytest.approx(max(0.0, (ms_fam - ms_inter) / (b * n)))
    assert all(by[d][f"vc_{k}"] >= 0 for d in by for k in ("family", "mode", "interaction", "residual"))
    write_outputs(design, rows, tmp_path)
    md = (tmp_path / "variance_table.md").read_text()
    assert "Random-effects variance components (exploratory)" in md
    with (tmp_path / "variance_table.csv").open() as fh:
        header = next(csv.reader(fh))
    assert {"vc_family", "vc_mode", "vc_interaction", "vc_residual"} <= set(header)


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
        "date_stamped": "2026-10-01",
        "date_run": "2026-10-01",
        "run_by": "me",
    }
    return Capture(meta={**base, **meta}, final_answer=" ".join(["word"] * words))


def test_web_capture_needs_date_stamped():
    assert check_capture(_cap("a")) == []
    assert any("date_stamped" in p for p in check_capture(_cap("a", date_stamped="")))


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
    assert [r["dimension"] for r in rows] == [*(f"D{i}" for i in range(1, 10)), "total"]
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


def _grid(fast, reasoning, a=6, n=5):
    # y[family, mode, replicate]; mode 0 = fast, 1 = reasoning
    import numpy as np

    y = np.empty((a, 2, n))
    y[:, 0, :] = fast
    y[:, 1, :] = reasoning
    return y


def test_mode_effect_is_signed_with_a_ci():
    import numpy as np

    from modegrid.analyze import analyse_dimension

    rng = np.random.default_rng(1)
    y = _grid(0.0, 2.0) + rng.integers(0, 2, size=(6, 2, 5)) * 0.0
    y[:, 0, 0] = 1  # some noise so variance is not degenerate
    y[:, 1, 0] = 1
    row = analyse_dimension(y, "D1", n_boot=200, n_perm=50, seed=1, families=list("abcdef"))
    assert row["mode_effect"] > 0 and row["mode_effect_ci_low"] > 0
    assert "omega2_interaction" in row
    assert len(row["family_effects"]) == 6 and all(fe["diff"] > 0 for fe in row["family_effects"])


def test_hypothesis_needs_reasoning_better_and_reliable_dimension():
    from modegrid.analyze import HYPOTHESES, hypothesis_status

    h1 = HYPOTHESES["H1"]
    better = {"verdict": "mode > model", "mode_effect_ci_low": 0.3}
    worse = {"verdict": "mode > model", "mode_effect_ci_low": -0.9}
    reliable = {"D1": 0.8, "D3": 0.8}
    assert hypothesis_status(better, h1, reliable) == "yes"
    assert hypothesis_status(worse, h1, reliable).startswith("no")
    assert hypothesis_status(better, h1, {"D1": 0.41}).startswith("exploratory")
    # never "yes" without a passing reliability gate (missing file, missing row, or NaN)
    assert hypothesis_status(better, h1) == "yes, pending alpha"
    assert hypothesis_status(better, h1, {"D3": 0.9}) == "yes, pending alpha"
    assert hypothesis_status(better, h1, {"D1": float("nan")}) == "yes, pending alpha"
    assert HYPOTHESES["H4"].role == "confirmatory" and HYPOTHESES["H1"].role == "secondary"
    assert (
        hypothesis_status({"verdict": "model > mode", "mode_effect_ci_low": 0.0}, HYPOTHESES["H3"], reliable) == "yes"
    )


def test_low_variance_and_interaction_labels():
    from modegrid.analyze import HYPOTHESES, hypothesis_status

    h1, reliable = HYPOTHESES["H1"], {"D1": 0.8}
    flat = {"verdict": "uninformative (low variance)", "mode_effect_ci_low": 0.0}
    assert hypothesis_status(flat, h1, reliable) == "inconclusive (uninformative (low variance))"
    assert hypothesis_status(flat, h1, {"D1": 0.3}).startswith("inconclusive")
    tangled = {
        "verdict": "mode > model",
        "mode_effect_ci_low": 0.3,
        "omega2_mode": 0.2,
        "omega2_family": 0.05,
        "omega2_interaction": 0.3,
    }
    assert hypothesis_status(tangled, h1, reliable).startswith("yes (average effect only")


def test_low_variance_dimension_is_uninformative():
    from modegrid.analyze import analyse_dimension

    y = _grid(2.0, 2.0)
    y[0, 0, 0] = 1  # 1 of 60 differs: 98% identical
    row = analyse_dimension(y, "D5", n_boot=50, n_perm=20, seed=1, families=list("abcdef"))
    assert row["verdict"].startswith("uninformative")


def test_agreement_reports_total_alpha(tmp_path, capsys):
    rows_a = {f"B{i:03d}": {f"D{j}": (i + j) % 3 for j in range(1, 10)} for i in range(1, 9)}
    paths = []
    for name in ("human", "llm-a", "llm-b"):
        p = tmp_path / f"{name}.csv"
        write_scores(rows_a, p, id_col="blind_id")
        paths.append(str(p))
    out = tmp_path / "agreement.csv"
    assert main(["agreement", *paths, "--out", str(out)]) == 0
    dims = [line.split(",")[0] for line in out.read_text().splitlines()[1:]]
    assert dims[-1] == "total"


def test_validate_reads_every_score_sheet_shape(tmp_path, monkeypatch, grid_path, capsys):
    # Rater and consensus sheets use blind_id, unblinded ones run_id. A run-level
    # adjudicated.csv must cover exactly the manifest's main runs.
    g = load_grid(grid_path)
    runs = build_manifest(g)
    manifest = tmp_path / "runs.csv"
    write_manifest(runs, manifest)
    (tmp_path / "captures").mkdir()
    scores_dir = tmp_path / "data" / "scores"
    families = sorted({r.family for r in runs})
    by_run = synthetic_scores(families, g.replicates, g.prompts[0].id, seed=1)
    by_blind = {f"B{i:03d}": s for i, s in enumerate(by_run.values(), start=1)}
    write_scores(by_blind, scores_dir / "human.csv", id_col="blind_id")
    write_scores(by_blind, scores_dir / "adjudicated-blind.csv", id_col="blind_id")
    write_scores(by_run, scores_dir / "human-unblinded.csv")
    write_scores(by_run, scores_dir / "adjudicated.csv")
    monkeypatch.chdir(tmp_path)
    base = ["--config", str(grid_path), "--manifest", str(manifest), "--captures", str(tmp_path / "captures")]
    assert main([*base, "validate"]) == 0
    assert capsys.readouterr().out.strip().endswith("ok")
    write_scores(dict(list(by_run.items())[:-1]), scores_dir / "adjudicated.csv")
    assert main([*base, "validate"]) == 1
    assert "missing" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Disclosure: I am a [REDACTED] model, so discount my view on Claude Code accordingly. The ranking stands.",
            "The ranking stands.",
        ),
        ("A\n\n**Conflict of interest:** I'm built by [REDACTED], so I chose open tools.\n\nB", "A\n\nB"),
        ("A\n\n- **Conflict of interest:** I am built by X.\n- Next item", "A\n\n- Next item"),
        ("| Claude Code | Optional. Conflict of interest noted. |", "| Claude Code | Optional. |"),
        ("Pick Opus 5.5 (disclosure above) or GPT-5.6.", "Pick Opus 5.5 or GPT-5.6."),
        ("  Disclosure: I work for Y. Then text.", "  Then text."),
    ],
)
def test_self_disclosure_is_removed(text, expected):
    assert strip_self_disclosure(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Keep memory separate to reduce accidental disclosure between projects.",
        "Disclosure: none of these tools pay for placement.",
        "Use Claude Code with a local model.",
    ],
)
def test_content_mentions_of_disclosure_stay(text):
    assert strip_self_disclosure(text) == text
