"""One self-contained file per answer for each rater, and collection of returned rows.

Each file holds the fixed rater prompt (docs/rater-prompt.md), the rubric, the scoring
protocol, the memory checker and one blinded answer, so every session sees the same
instructions and exactly one answer. Files are numbered in the rater's own reading order
(their score sheet), which spreads fatigue and order effects across raters.

Raters reply with one fenced CSV row. `collect_rows` pulls those rows out of pasted
replies, checks them, and writes the rater's sheet in score-sheet order.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from . import DIMS
from .scores import ScoreError

SHEET_COLS = ["blind_id", *DIMS, "guess_family", "guess_mode", "notes"]
FAMILIES = {"claude", "deepseek", "gemini", "gpt", "grok", "qwen"}
MODES = {"fast", "reasoning"}
_PROMPT_BLOCK = re.compile(r"^=== RATER PROMPT START ===\n(.*?)\n^=== RATER PROMPT END ===", re.S | re.M)
_ROW_START = re.compile(r"^B\d{3},")


def rater_prompt(path: str | Path) -> str:
    m = _PROMPT_BLOCK.search(Path(path).read_text(encoding="utf-8"))
    if not m:
        raise ScoreError(f"{path}: no RATER PROMPT START/END block")
    return m.group(1).strip("\n")


def sheet_order(sheet: str | Path) -> list[str]:
    with Path(sheet).open(newline="", encoding="utf-8") as fh:
        return [row["blind_id"] for row in csv.DictReader(fh)]


def build_kit(
    packets_dir: str | Path,
    rater: str,
    prompt_path: str | Path,
    rubric_path: str | Path,
    protocol_path: str | Path,
    checker_path: str | Path,
    out_dir: str | Path,
) -> list[Path]:
    packets_dir = Path(packets_dir)
    order = sheet_order(packets_dir / f"scoresheet-{rater}.csv")
    head = "\n\n".join(
        [
            rater_prompt(prompt_path),
            "=== RUBRIC ===\n\n" + Path(rubric_path).read_text(encoding="utf-8").strip(),
            "=== SCORING PROTOCOL ===\n\n" + Path(protocol_path).read_text(encoding="utf-8").strip(),
            "=== memory_budget.py ===\n\n```python\n"
            + Path(checker_path).read_text(encoding="utf-8").rstrip()
            + "\n```",
        ]
    )
    out = Path(out_dir) / rater
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for n, blind_id in enumerate(order, start=1):
        answer = (packets_dir / "answers" / f"{blind_id}.md").read_text(encoding="utf-8").strip()
        path = out / f"{n:02d}_{blind_id}.md"
        path.write_text(f"{head}\n\n=== ANSWER TO SCORE ===\n\n{answer}\n", encoding="utf-8")
        written.append(path)
    return written


def parse_rows(text: str) -> list[dict[str, str]]:
    """Every `B###,...` CSV line in pasted replies, header lines ignored."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not _ROW_START.match(line):
            continue
        cells = next(csv.reader(io.StringIO(line)))
        if len(cells) != len(SHEET_COLS):
            raise ScoreError(f"{cells[0]}: {len(cells)} columns, expected {len(SHEET_COLS)}")
        rows.append(dict(zip(SHEET_COLS, cells, strict=True)))
    return rows


def check_row(row: dict[str, str]) -> None:
    b = row["blind_id"]
    for d in DIMS:
        if row[d].strip() not in {"0", "1", "2"}:
            raise ScoreError(f"{b} {d}={row[d]!r}, must be 0, 1 or 2")
    fam = row["guess_family"].strip().lower()
    mode = row["guess_mode"].strip().lower()
    if fam and fam not in FAMILIES:
        raise ScoreError(f"{b} guess_family={fam!r}, must be blank or one of {sorted(FAMILIES)}")
    if mode and mode not in MODES:
        raise ScoreError(f"{b} guess_mode={mode!r}, must be blank, fast or reasoning")


def collect_rows(
    replies: list[str | Path], sheet: str | Path, out: str | Path, existing: bool = True
) -> tuple[int, list[str]]:
    """Merge rows from reply files into the rater's sheet. Returns (rows now filled, ids still missing).

    A blind id already present with different scores is an error, so a second session on
    the same answer cannot silently replace the first.
    """
    order = sheet_order(sheet)
    allowed = set(order)
    out = Path(out)
    have: dict[str, dict[str, str]] = {}
    if existing and out.exists():
        with out.open(newline="", encoding="utf-8") as fh:
            have = {r["blind_id"]: r for r in csv.DictReader(fh) if r.get("D1", "").strip()}
    for reply in replies:
        for row in parse_rows(Path(reply).read_text(encoding="utf-8")):
            check_row(row)
            b = row["blind_id"]
            if b not in allowed:
                raise ScoreError(f"{b} is not on this rater's sheet")
            old = have.get(b)
            if old and [old[d] for d in DIMS] != [row[d] for d in DIMS]:
                raise ScoreError(f"{b} already scored with different values; resolve by hand")
            have[b] = row
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SHEET_COLS, lineterminator="\n")
        w.writeheader()
        for b in order:
            w.writerow(have.get(b, {"blind_id": b}))
    missing = [b for b in order if b not in have]
    return len(order) - len(missing), missing
