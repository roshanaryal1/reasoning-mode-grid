"""Blinded rater packets.

Raters must not know which family or which mode produced an answer. Two leaks
are handled here:

1. Self-identification. The study prompt asks the model to state its name,
   cutoff and browsing status at the top. Those header lines are removed.
2. Self-reference in the body ("I'm Claude", "As ChatGPT, ...", "a model
   developed by Google"). Config terms are masked only inside such phrases.

Vendor and model names used as content stay. The prompt asks for a local model
and tool stack, so answers name Qwen, DeepSeek or Gemma models and tools such as
Claude Code; D2 to D4 cannot be scored if those names are masked.

3. Chat-app clutter copied along with an answer (decided 2026-10-15, see the
   Deviations table): ChatGPT's citation chips (favicon image link, source label,
   "+N" count), its diagram style blocks and image embeds, the `&#x20;` entity,
   and Grok's `[web:N]` citation tags. These come from the app, not the model's
   text, and would name the family outright. Captures keep them; only packets
   drop them.

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

# Phrases where a name identifies the answering model rather than a recommendation.
# "developed by X" counts only after one of these cues ("I am an AI developed by X"),
# so "a tool developed by Google" is kept.
_SELF_CUES = (
    r"\bI\s+am\s+",
    r"\bI\s+was\s+",
    r"\bI['’]m\s+",
    r"\bmy\s+name\s+is\s+",
)
# "As X, I ..." at the start of a sentence. Needs the comma and "I", so "tools such as
# DeepSeek" and "As Google explains, ..." are kept.
_AS_CUE = r"(?:^|(?<=[.!?:]\s))As\s+"
_AS_TAIL = r"(?=[^\S\n]*,\s*I\b)"
_FILLER = (
    r"(?:(?:an?|the|AI|model|assistant|language|large)\s+){0,4}"
    r"(?:(?:made|built|developed|trained|created)\s+by\s+)?"
)


_FAVICON_LINE = re.compile(r"^\s*\[image\]\(https://www\.google\.com/s2/favicons\?[^)]*\)\s*$")
_PLUS_COUNT = re.compile(r"^\s*\+\d+\s*$")
_APP_IMAGE_LINE = re.compile(r"^\s*\[[^\]]*\]\(https://images\.openai\.com/[^)]*\)\s*$")
# ChatGPT renders a diagram as one line: a CSS block for #chatgpt-mermaid-<id>, then the
# node labels. Keep the labels (answer content), drop the CSS.
_MERMAID_CSS = re.compile(r"^\\?#chatgpt-mermaid-.*\}(?P<labels>[^}]*)$")
_WEB_TAG = re.compile(r"[^\S\n]*\[web:\d+(?:,\s*web:\d+)*\]")


def strip_app_artifacts(text: str) -> str:
    """Remove chat-app clutter that names the family without being answer text."""
    lines = text.replace("&#x20;", "").splitlines()
    kept: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _FAVICON_LINE.match(line):
            # A citation chip: favicon link, blank lines, a source label, then maybe "+N".
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                j += 1
            k = j
            while k < len(lines) and not lines[k].strip():
                k += 1
            i = k + 1 if k < len(lines) and _PLUS_COUNT.match(lines[k]) else j
            continue
        if _APP_IMAGE_LINE.match(line):
            i += 1
            continue
        m = _MERMAID_CSS.match(line)
        if m:
            labels = m.group("labels").strip()
            if labels:
                kept.append(labels)
            i += 1
            continue
        kept.append(_WEB_TAG.sub("", line))
        i += 1
    return "\n".join(kept)


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
    names = "|".join(re.escape(t) for t in sorted({t for t in terms if t}, key=len, reverse=True))
    if not names:
        return out
    cue = "|".join(_SELF_CUES)
    flags = re.IGNORECASE | re.MULTILINE
    first_person = re.compile(rf"(?P<cue>(?:{cue}){_FILLER})(?P<name>{names})(?![\w-])", flags)
    as_self = re.compile(rf"(?P<cue>{_AS_CUE}{_FILLER})(?P<name>{names})(?![\w-]){_AS_TAIL}", flags)
    for pattern in (first_person, as_self):
        out = pattern.sub(lambda m: m.group("cue") + MASK, out)
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
        body = redact(strip_app_artifacts(cap.final_answer), terms)
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


def _binom_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p). Exact, stdlib only."""
    from math import comb

    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def guess_accuracy(
    sheet: str | Path, key: dict[str, str], truth: dict[str, tuple[str, str]], n_families: int
) -> dict[str, dict[str, float]]:
    """How often a rater's guesses of family and mode were right, against chance.

    `truth` maps run_id -> (family, mode). Blank guesses are skipped, so the
    share of answers the rater was willing to guess is reported too. A small
    one-sided binomial p-value means the rater beat chance, so blinding leaked.
    """
    out: dict[str, dict[str, float]] = {}
    with Path(sheet).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for field, idx, chance in (("guess_family", 0, 1 / n_families), ("guess_mode", 1, 1 / 2)):
        guessed = right = 0
        for row in rows:
            g = (row.get(field) or "").strip().lower()
            run_id = key.get(row["blind_id"])
            if not g or run_id is None:
                continue
            guessed += 1
            right += int(g == truth[run_id][idx].lower())
        out[field] = {
            "items": float(len(rows)),
            "guessed": float(guessed),
            "correct": float(right),
            "accuracy": right / guessed if guessed else float("nan"),
            "chance": chance,
            "p_value": _binom_tail(right, guessed, chance) if guessed else float("nan"),
        }
    return out
