"""Blinded rater packets.

Raters must not know which family or which mode produced an answer. Two leaks
are handled here:

1. Self-identification. The study prompt asks the model to state its name,
   cutoff and browsing status at the top. Those header lines are removed.
2. Vendor and model names in the body. Terms from the config are masked.

What cannot be removed: style, length, and formatting habits. A rater may still
guess. Raters record a guess per answer (`guess_family`, `guess_mode`) so the
paper can report how often blinding failed.
"""

from __future__ import annotations

import csv
import random
import re
from pathlib import Path

from . import DIMS
from .capture import Capture

HEADER_PATTERN = re.compile(
    r"(model\s*(name|version)|knowledge\s*cut-?off|browsing|web\s*access|tools?\s*enabled|i\s+am\s+\w+)",
    re.IGNORECASE,
)
MASK = "[REDACTED]"


def redact(text: str, terms: list[str] | tuple[str, ...], header_lines: int = 12) -> str:
    lines = text.splitlines()
    kept = []
    for i, line in enumerate(lines):
        if i < header_lines and HEADER_PATTERN.search(line):
            kept.append(f"{MASK} (self-identification line removed)")
            continue
        kept.append(line)
    out = "\n".join(kept)
    # Longest first so "Claude Sonnet" masks before "Claude".
    for term in sorted({t for t in terms if t}, key=len, reverse=True):
        out = re.sub(rf"(?<![\w-]){re.escape(term)}(?![\w-])", MASK, out, flags=re.IGNORECASE)
    return out


def build_packets(
    captures: list[Capture],
    terms: list[str],
    out_dir: str | Path,
    key_path: str | Path,
    seed: int,
    raters: list[str],
) -> list[tuple[str, str]]:
    """Write one shuffled packet per rater plus a private key file.

    Every rater sees the same blind ids, so their scores line up for agreement,
    but each rater gets a different reading order to spread fatigue effects.
    """
    out_dir = Path(out_dir)
    rng = random.Random(seed)
    order = list(captures)
    rng.shuffle(order)
    key = [(f"B{i:03d}", c.run_id) for i, c in enumerate(order, start=1)]

    answers_dir = out_dir / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)
    for (blind_id, _), cap in zip(key, order, strict=True):
        body = redact(cap.final_answer, terms)
        (answers_dir / f"{blind_id}.md").write_text(f"# {blind_id}\n\n{body}\n", encoding="utf-8")

    for rater in raters:
        ids = [b for b, _ in key]
        random.Random(f"{seed}-{rater}").shuffle(ids)
        sheet = out_dir / f"scoresheet-{rater}.csv"
        with sheet.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["blind_id", *DIMS, "guess_family", "guess_mode", "notes"])
            for b in ids:
                w.writerow([b, *([""] * len(DIMS)), "", "", ""])

    key_path = Path(key_path)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with key_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["blind_id", "run_id"])
        w.writerows(key)
    return key
