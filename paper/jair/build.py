"""Turn the markdown drafts in paper/ into LaTeX for the JAIR template.

The markdown files stay the source of truth. This script writes body.tex and
appendix.tex next to main.tex; main.tex holds the JAIR preamble, the structured
abstract, the acknowledgements and the reproducibility checklist.

    python paper/jair/build.py        # then compile main.tex with latexmk or Overleaf

Needs pandoc on PATH.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
BODY = ["introduction", "related-work", "methods", "results", "discussion"]
APPENDIX = ["appendix"]

# Paragraphs that are notes to the author, not part of the article.
NOTE_STARTS = (
    "Draft written",
    "Skeleton written",
    "Limitations written",
    "This is the full-length version",
)

# Bracketed citations in the markdown, and the BibLaTeX key each one maps to.
PARENTHETICAL = {
    "Aryal, 2026": "aryal2026lap1",
    "Aryal, in preparation": "aryal2026lap2",
    "Atil et al., 2024": "atil2024nondeterminism",
    "Bjarnason et al., 2026": "bjarnason2026randomness",
    "Chen et al., 2025": "chen2025factuality",
    "Haase et al., 2026": "haase2026creative",
    "Heyman and Zylberberg, 2025": "heyman2025hallucinating",
    "K. Wang et al., 2026": "wangk2026margo",
    "Lau, 2026": "lau2026judge",
    "Lei et al., 2026": "lei2026inertia",
    "Li and Ng, 2025": "li2025hallucinate",
    "Madur, 2026": "madur2026moral",
    "Ning et al., 2026": "ning2026hrbench",
    "Potamitis et al., 2025": "potamitis2025reasonbench",
    "S. Wang et al., 2026": "wangs2026pathlock",
    "Snell et al., 2024": "snell2024scaling",
    "Yuan et al., 2025": "yuan2025numerical",
    "Zhang et al., 2026": "zhang2026harness",
    "Zhao et al., 2025": "zhao2025tts",
}
TEXTUAL = {
    "S. Wang et al. [2025]": "wangs2025hybrid",
    "Liu and Honavar [2026]": "liu2026leakage",
    "Sahu et al. [2026]": "sahu2026architects",
}

FIGURE_1 = r"""
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figure1.pdf}
  \caption{Cell means, fast versus reasoning, one line per family, for the total score and
  for D1, D9 and D3. Consensus scores, five answers per cell.}
  \Description{Line plots of mean scores in fast and reasoning mode for six model families.}
  \label{fig:cells}
\end{figure}
"""


def _ws(text: str) -> str:
    """A regex for text whose spaces may be any whitespace, so wrapped lines still match."""
    return r"\s+".join(re.escape(part) for part in text.split())


def strip_notes(md: str) -> str:
    paras = re.split(r"\n\s*\n", md)
    kept = [p for p in paras if not p.lstrip().startswith(NOTE_STARTS)]
    md = "\n\n".join(kept)
    # The results draft opens with a table of source files for the author.
    return re.sub(r"Source files after Phase 4.*?(?=\n## )", "", md, flags=re.S)


def fix_headings(md: str, appendix: bool) -> str:
    out = []
    for line in md.splitlines():
        m = re.match(r"^(#+)\s+(.*)$", line)
        if not m:
            out.append(line)
            continue
        level, title = len(m.group(1)), re.sub(r"\s*\(draft\)\s*$", "", m.group(2))
        if appendix:
            if level == 1:
                continue  # the "Appendix" title; \appendix starts the lettered sections
            if title.startswith("D2."):
                out.append("## " + title.removeprefix("D2.").strip())
            else:
                out.append("# " + re.sub(r"^[A-Z]\.\s*", "", title))
            continue
        if title.startswith("6. Conclusion"):
            out.append("# Conclusion")
            continue
        out.append("#" * level + " " + re.sub(r"^\d+(\.\d+)?\.?\s+", "", title))
    return "\n".join(out) + "\n"


def _latex(command: str, key: str) -> Callable[[re.Match[str]], str]:
    return lambda _m: f"\\{command}{{{key}}}"


def cite(md: str, used: set[str]) -> str:
    for text, key in TEXTUAL.items():
        md, n = re.subn(_ws(text), _latex("citet", key), md)
        if n:
            used.add(text)
    for text, key in PARENTHETICAL.items():
        md, n = re.subn(r"\[" + _ws(text) + r"\]", _latex("cite", key), md)
        if n:
            used.add(text)
    left = re.findall(r"\[(?:cite\b[^\]]*|[A-Z][^\]]*(?:19|20)\d\d[^\]]*)\]", md)
    if left:
        raise SystemExit(f"unmapped citations: {left}")
    return md


def add_figure(md: str) -> str:
    anchor = "Figure 1 (`results/figure1.pdf`) shows"
    if anchor not in md:
        return md
    head, _, tail = md.partition(anchor)
    para_end = tail.find("\n\n")
    return head + r"Figure\ \ref{fig:cells} shows" + tail[:para_end] + "\n\n" + FIGURE_1 + tail[para_end:]


def to_latex(md: str) -> str:
    result = subprocess.run(
        ["pandoc", "-f", "markdown-auto_identifiers", "-t", "latex", "--wrap=preserve"],
        input=md,
        capture_output=True,
        text=True,
        check=True,
    )
    # Long host names in narrow table cells: allow a break after the first dot.
    return re.sub(r"\b(aistudio|chat)\.(google|deepseek)\.com", r"\1.\\allowbreak{}\2.com", result.stdout)


def build(names: list[str], appendix: bool, used: set[str]) -> str:
    parts = []
    for name in names:
        md = (PAPER / f"{name}.md").read_text(encoding="utf-8")
        md = cite(add_figure(fix_headings(strip_notes(md), appendix)), used)
        parts.append(to_latex(md))
    return "\n".join(parts)


def main() -> int:
    header = "% Generated by paper/jair/build.py from paper/*.md. Do not edit by hand.\n\n"
    used: set[str] = set()
    body = build(BODY, appendix=False, used=used)
    appendix = build(APPENDIX, appendix=True, used=used)
    unused = sorted((set(TEXTUAL) | set(PARENTHETICAL)) - used)
    if unused:
        raise SystemExit(f"citations in the map but not in the text: {unused}")
    (HERE / "body.tex").write_text(header + body, encoding="utf-8")
    (HERE / "appendix.tex").write_text(header + appendix, encoding="utf-8")
    print(f"wrote {HERE / 'body.tex'} and {HERE / 'appendix.tex'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
