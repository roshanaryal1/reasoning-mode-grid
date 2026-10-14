import csv
from collections import Counter

from modegrid.audit import PROBES, audit, concentration, write_audit
from modegrid.cli import main


def _packets(tmp_path, answers):
    d = tmp_path / "packets" / "answers"
    d.mkdir(parents=True)
    key = {}
    for i, (run_id, text) in enumerate(answers, start=1):
        b = f"B{i:03d}"
        (d / f"{b}.md").write_text(f"# {b}\n\n{text}\n", encoding="utf-8")
        key[b] = run_id
    key_path = tmp_path / "key.csv"
    with key_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["blind_id", "run_id"])
        w.writerows(key.items())
    return key, key_path


def test_audit_counts_cells_and_concentration(tmp_path):
    key, _ = _packets(
        tmp_path,
        [
            ("claude__fast__p1-v1__r1", "I'll start by checking the hardware.\nBody."),
            ("claude__reasoning__p1-v1__r1", "Let me verify.\nBody."),
            ("gpt__fast__p1-v1__r1", "Plain answer. As of my cutoff, MLX was new."),
        ],
    )
    res = audit(tmp_path / "packets" / "answers", key)
    assert res["tool_narration"] == Counter({"claude/fast": 1, "claude/reasoning": 1})
    assert res["cutoff_note"] == Counter({"gpt/fast": 1})
    assert concentration(res["tool_narration"]) == ("claude", 1.0)
    assert concentration(Counter()) == ("", 0.0)
    out = write_audit(res, ["claude/fast", "claude/reasoning", "gpt/fast"], tmp_path / "a.csv")
    rows = {r["probe"]: r for r in csv.DictReader(out.open())}
    assert set(rows) == {p.name for p in PROBES}
    assert rows["tool_narration"]["total"] == "2" and rows["tool_narration"]["top_family"] == "claude"


def test_cli_exits_nonzero_on_a_leak(tmp_path, capsys):
    _, key_path = _packets(tmp_path, [("gpt__fast__p1-v1__r1", "See https://x.org/?utm_source=chatgpt.com")])
    args = ["blinding-audit", "--packets", str(tmp_path / "packets"), "--key", str(key_path), "--out", ""]
    assert main(args) == 1
    assert "1 packet(s) hit a leak probe" in capsys.readouterr().out
    _, key_path = _packets(tmp_path / "clean", [("gpt__fast__p1-v1__r1", "A clean answer.")])
    args = ["blinding-audit", "--packets", str(tmp_path / "clean" / "packets"), "--key", str(key_path), "--out", ""]
    assert main(args) == 0
