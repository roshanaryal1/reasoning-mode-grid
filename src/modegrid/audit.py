"""Pre-scoring blinding audit: which family fingerprints survive in the rater packets?

Raters guess family and mode after scoring (`modegrid blinding-check`). This audit runs
before scoring, on the packets themselves, with the key: for each pattern that could hint
at a family or mode, how many packets in each family x mode cell still contain it.

A pattern concentrated in one cell is a leak to fix (if it is app clutter or
self-reference) or to report (if it is the model's own style, which the pre-registration
leaves as written). The audit never changes a packet.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Probe:
    name: str
    pattern: str
    kind: str  # "leak": should be zero after blinding; "style": the model's own text, reported
    note: str

    def compiled(self) -> re.Pattern[str]:
        return re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)


PROBES: tuple[Probe, ...] = (
    Probe("redaction_mask", r"\[REDACTED\]", "leak", "a masked self-reference; the sentence around it may still hint"),
    Probe("self_disclosure", r"\b(?:disclosure|conflict of interest)\s*(?::|noted)", "leak", "conflict of interest"),
    Probe("tracking_param", r"utm_source=", "leak", "chat apps tag links they cite"),
    Probe("citation_marker", r"oaicite|citeturn|turn\d+(?:search|view|news)\d+|【|】", "leak", "app citation markup"),
    Probe("web_tag", r"\[web:\d", "leak", "Grok citation tag"),
    Probe("app_image", r"favicons\?|images\.openai\.com", "leak", "app image or favicon link"),
    Probe("sandbox_file", r"sandbox:/mnt/data", "leak", "ChatGPT tool file link"),
    Probe("tool_narration", r"^(?:I'll|I will|Let me|Starting|Now I'll|Next,? I)\b", "style", "tool progress text"),
    Probe("clock_note", r"\b(?:session|system) (?:clock|date)\b", "style", "real date differs"),
    Probe("cutoff_note", r"\b(?:as of|at|past|before) my (?:knowledge )?cutoff\b", "style", "closed-book answer"),
    Probe("latex_arrow", r"\$\\(?:to|rightarrow)\$", "style", "LaTeX arrows in prose"),
    Probe("download_link", r"\.zip\b", "style", "mentions a downloadable archive"),
)


def audit(answers_dir: str | Path, key: dict[str, str], probes: tuple[Probe, ...] = PROBES) -> dict[str, Counter[str]]:
    """probe name -> Counter of 'family/mode' cells whose packets contain it."""
    out: dict[str, Counter[str]] = {p.name: Counter() for p in probes}
    compiled = [(p, p.compiled()) for p in probes]
    for blind_id, run_id in key.items():
        family, mode = run_id.split("__")[:2]
        text = (Path(answers_dir) / f"{blind_id}.md").read_text(encoding="utf-8")
        for probe, rx in compiled:
            if rx.search(text):
                out[probe.name][f"{family}/{mode}"] += 1
    return out


def concentration(counts: Counter[str]) -> tuple[str, float]:
    """The family holding most hits, and its share of them (1.0 = all in one family)."""
    by_family: Counter[str] = Counter()
    for cell, n in counts.items():
        by_family[cell.split("/")[0]] += n
    total = sum(by_family.values())
    if not total:
        return "", 0.0
    family, n = by_family.most_common(1)[0]
    return family, n / total


def write_audit(
    results: dict[str, Counter[str]], cells: list[str], path: str | Path, probes: tuple[Probe, ...] = PROBES
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["probe", "kind", *cells, "total", "top_family", "top_share", "note"])
        for p in probes:
            c = results[p.name]
            fam, share = concentration(c)
            w.writerow([p.name, p.kind, *(c.get(x, 0) for x in cells), sum(c.values()), fam, f"{share:.2f}", p.note])
    return path
