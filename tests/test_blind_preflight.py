"""Pre-scoring blinding must fail closed on capture or key integrity errors."""

import csv
from pathlib import Path

from modegrid.capture import Capture, write_capture
from modegrid.cli import main
from modegrid.config import load_grid
from modegrid.plan import MAIN, read_manifest

ROOT = Path(__file__).resolve().parent.parent


def _args(tmp_path: Path, grid_path: Path) -> list[str]:
    return [
        "--config", str(grid_path),
        "--manifest", str(ROOT / "data/manifest/runs.csv"),
        "--captures", str(tmp_path / "captures"),
        "blind", "--out", str(tmp_path / "packets"),
        "--key", str(tmp_path / "secret" / "key.csv"),
        "--raters", "human", "llm-a", "llm-b",
    ]


def _sample_captures(tmp_path: Path, grid_path: Path, pasted_prompt: bool = False) -> None:
    grid = load_grid(grid_path)
    prompt = grid.prompts[0]
    runs = [r for r in read_manifest(ROOT / "data/manifest/runs.csv") if r.set == MAIN]
    for i, run in enumerate(runs):
        answer = prompt.text() if pasted_prompt and i == 0 else f"Test answer for {run.run_id}."
        meta = {
            "run_id": run.run_id,
            "family": run.family,
            "mode": run.mode,
            "native_label": "test",
            "channel": "web",
            "model_requested": "test",
            "model_returned": "test",
            "prompt_id": run.prompt_id,
            "prompt_sha256": prompt.sha256,
            "replicate": run.replicate,
            "date_stamped": "2026-10-13T10:00:00+00:00",
            "date_run": "2026-10-13T10:00:00+00:00",
            "run_by": "fixture",
        }
        write_capture(Capture(meta=meta, final_answer=answer), tmp_path / "captures")


def test_blind_rejects_missing_primary_capture(tmp_path, grid_path, capsys):
    assert main(_args(tmp_path, grid_path)) == 1
    assert "missing primary capture" in capsys.readouterr().out
    assert not (tmp_path / "secret" / "key.csv").exists()


def test_blind_rejects_pasted_study_prompt(tmp_path, grid_path, capsys):
    _sample_captures(tmp_path, grid_path, pasted_prompt=True)
    assert main(_args(tmp_path, grid_path)) == 1
    assert "study prompt" in capsys.readouterr().out
    assert not (tmp_path / "secret" / "key.csv").exists()


def test_blind_preserves_existing_mapping(tmp_path, grid_path, capsys):
    _sample_captures(tmp_path, grid_path)
    args = _args(tmp_path, grid_path)
    assert main(args) == 0
    key_path = tmp_path / "secret" / "key.csv"
    original = key_path.read_bytes()
    assert main(args) == 0
    assert key_path.read_bytes() == original

    with key_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    rows[1][1], rows[2][1] = rows[2][1], rows[1][1]
    with key_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerows(rows)
    changed = key_path.read_bytes()
    assert main(args) == 1
    assert "mapping differs" in capsys.readouterr().out
    assert key_path.read_bytes() == changed
