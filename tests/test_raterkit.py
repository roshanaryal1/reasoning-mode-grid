import csv

import pytest

from modegrid.raterkit import build_kit, collect_rows, parse_rows, rater_prompt
from modegrid.scores import ScoreError

PROMPT = "# Rater prompt\n\nintro\n\n=== RATER PROMPT START ===\n\nScore one answer.\n\n=== RATER PROMPT END ===\n"


def _packets(tmp_path, ids=("B001", "B002", "B003"), rater="llm-a"):
    p = tmp_path / "packets"
    (p / "answers").mkdir(parents=True)
    for b in ids:
        (p / "answers" / f"{b}.md").write_text(f"# {b}\n\nanswer text {b}\n", encoding="utf-8")
    with (p / f"scoresheet-{rater}.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["blind_id", *[f"D{i}" for i in range(1, 10)], "guess_family", "guess_mode", "notes"])
        for b in reversed(ids):
            w.writerow([b] + [""] * 12)
    for name, text in (("prompt.md", PROMPT), ("rubric.md", "RUBRIC"), ("scoring.md", "PROTO"), ("mb.py", "print(1)")):
        (tmp_path / name).write_text(text, encoding="utf-8")
    return p


def _row(b, scores="2,1,2,1,0,1,2,1,2", fam="qwen", mode="fast", notes='"D1: fits, one reason"'):
    return f"{b},{scores},{fam},{mode},{notes}"


def test_rater_prompt_extracts_block(tmp_path):
    (tmp_path / "p.md").write_text(PROMPT, encoding="utf-8")
    assert rater_prompt(tmp_path / "p.md") == "\nScore one answer.\n".strip("\n")


def test_build_kit_one_file_per_answer_in_sheet_order(tmp_path):
    p = _packets(tmp_path)
    files = build_kit(
        p,
        "llm-a",
        tmp_path / "prompt.md",
        tmp_path / "rubric.md",
        tmp_path / "scoring.md",
        tmp_path / "mb.py",
        tmp_path / "kit",
    )
    assert [f.name for f in files] == ["01_B003.md", "02_B002.md", "03_B001.md"]
    text = files[0].read_text(encoding="utf-8")
    assert text.index("Score one answer.") < text.index("RUBRIC") < text.index("PROTO") < text.index("print(1)")
    assert "answer text B003" in text and "B002" not in text and "RATER PROMPT START" not in text


def test_collect_rows_fills_sheet_and_reports_missing(tmp_path):
    p = _packets(tmp_path)
    reply = tmp_path / "r.txt"
    reply.write_text("Here is my score.\n```csv\nblind_id,D1,D2\n" + _row("B002") + "\n```\n", encoding="utf-8")
    out = tmp_path / "out.csv"
    filled, missing = collect_rows([reply], p / "scoresheet-llm-a.csv", out)
    assert filled == 1 and missing == ["B003", "B001"]
    rows = list(csv.DictReader(out.open()))
    assert [r["blind_id"] for r in rows] == ["B003", "B002", "B001"]
    assert rows[1]["D1"] == "2" and rows[1]["notes"] == "D1: fits, one reason"


def test_collect_rows_rejects_conflicting_rescore(tmp_path):
    p = _packets(tmp_path)
    out = tmp_path / "out.csv"
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text(_row("B001"), encoding="utf-8")
    b.write_text(_row("B001", scores="0,0,0,0,0,0,0,0,0"), encoding="utf-8")
    collect_rows([a], p / "scoresheet-llm-a.csv", out)
    with pytest.raises(ScoreError, match="already scored"):
        collect_rows([b], p / "scoresheet-llm-a.csv", out)


@pytest.mark.parametrize(
    "line,msg",
    [
        (_row("B001", scores="2,1,2,1,0,1,2,1,3"), "must be 0, 1 or 2"),
        (_row("B001", fam="openai"), "guess_family"),
        (_row("B001", mode="slow"), "guess_mode"),
        (_row("B009"), "not on this rater's sheet"),
        ("B001,2,1,2", "columns"),
    ],
)
def test_collect_rows_validates(tmp_path, line, msg):
    p = _packets(tmp_path)
    reply = tmp_path / "r.txt"
    reply.write_text(line, encoding="utf-8")
    with pytest.raises(ScoreError, match=msg):
        collect_rows([reply], p / "scoresheet-llm-a.csv", tmp_path / "out.csv")


def test_parse_rows_allows_blank_guesses():
    rows = parse_rows(_row("B001", fam="", mode=""))
    assert rows[0]["guess_family"] == "" and rows[0]["guess_mode"] == ""


def test_cli_rater_rows_writes_final_sheet_only_when_complete(tmp_path):
    from modegrid.cli import main

    p = _packets(tmp_path)
    final_dir = tmp_path / "scores"
    first = tmp_path / "1.txt"
    first.write_text(_row("B001") + "\n" + _row("B002"), encoding="utf-8")
    args = ["rater-rows", "llm-a", "--packets", str(p), "--final-dir", str(final_dir)]
    assert main([*args, str(first)]) == 0
    assert not (final_dir / "llm-a.csv").exists()
    second = tmp_path / "2.txt"
    second.write_text(_row("B003"), encoding="utf-8")
    assert main([*args, str(second)]) == 0
    rows = list(csv.DictReader((final_dir / "llm-a.csv").open()))
    assert [r["blind_id"] for r in rows] == ["B003", "B002", "B001"]
