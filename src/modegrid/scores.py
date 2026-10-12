"""Read, check and unblind rater score sheets."""

from __future__ import annotations

import csv
from pathlib import Path

from . import DIMS

Scores = dict[str, dict[str, int]]  # id -> {D1: 0..2, ...}


class ScoreError(ValueError):
    pass


def load_scores(path: str | Path, id_col: str = "blind_id", allow_blank: bool = False) -> Scores:
    out: Scores = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            uid = row[id_col]
            cells: dict[str, int] = {}
            for d in DIMS:
                raw = (row.get(d) or "").strip()
                if raw == "":
                    if allow_blank:
                        continue
                    raise ScoreError(f"{path}:{line_no}: {uid} {d} is blank")
                if raw not in {"0", "1", "2"}:
                    raise ScoreError(f"{path}:{line_no}: {uid} {d}={raw!r}, must be 0, 1 or 2")
                cells[d] = int(raw)
            if uid in out:
                raise ScoreError(f"{path}: duplicate id {uid}")
            out[uid] = cells
    return out


def load_key(path: str | Path) -> dict[str, str]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return {r["blind_id"]: r["run_id"] for r in csv.DictReader(fh)}


def unblind(scores: Scores, key: dict[str, str]) -> Scores:
    missing = set(scores) - set(key)
    if missing:
        raise ScoreError(f"blind ids not in key: {sorted(missing)[:5]}")
    return {key[b]: s for b, s in scores.items()}


def write_scores(scores: Scores, path: str | Path, id_col: str = "run_id") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow([id_col, *DIMS, "total"])
        for uid in sorted(scores):
            row = scores[uid]
            w.writerow([uid, *(row[d] for d in DIMS), sum(row[d] for d in DIMS)])


def disagreements(a: Scores, b: Scores) -> list[tuple[str, str, int, int]]:
    """Cells where two raters differ. This is the adjudication queue."""
    out = []
    for uid in sorted(set(a) & set(b)):
        for d in DIMS:
            if d in a[uid] and d in b[uid] and a[uid][d] != b[uid][d]:
                out.append((uid, d, a[uid][d], b[uid][d]))
    return out


def consensus(sheets: list[Scores]) -> Scores:
    """Median score per answer and dimension across an odd number of raters.

    Replaces author adjudication when the author is not blind: the median of three
    blind raters is mechanical and needs no one to see which model wrote what.
    """
    if len(sheets) < 3 or len(sheets) % 2 == 0:
        raise ScoreError(f"consensus needs an odd number of raters (3 or more), got {len(sheets)}")
    ids = set(sheets[0])
    if any(set(s) != ids for s in sheets[1:]):
        raise ScoreError("all raters must score the same answers")
    out: Scores = {}
    for uid in sorted(ids):
        out[uid] = {}
        for d in DIMS:
            values = sorted(s[uid][d] for s in sheets)
            out[uid][d] = values[len(values) // 2]
    return out
