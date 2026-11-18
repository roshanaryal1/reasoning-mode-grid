"""Turn the markdown drafts in paper/ into LaTeX for the JAIR and TMLR templates.

The markdown files stay the source of truth. Each target directory holds its own
main file (preamble, abstract, back matter); this script writes the generated body,
appendix and, for TMLR, the BibTeX files next to it.

    python paper/latex_build.py jair    # paper/jair/body.tex, appendix.tex
    python paper/latex_build.py tmlr    # paper/tmlr/body.tex, appendix.tex (named preprint)
                                        # and body-anon.tex, appendix-anon.tex, references*.bib
    python paper/latex_build.py nejlt   # paper/nejlt/body-anon.tex, appendix-anon.tex,
                                        # references-anon.bib (anonymous review copy only)

The anonymous TMLR and NEJLT files drop links that identify the author and cite the author's
own earlier work as "Anonymous", as double-blind review requires.

Needs pandoc on PATH.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

PAPER = Path(__file__).resolve().parent
BODY = ["introduction", "related-work", "methods", "results", "discussion"]
APPENDIX = ["appendix"]
BIB = PAPER / "jair" / "references.bib"  # one checked list of references for every target

# Paragraphs that are notes to the author, not part of the article.
NOTE_STARTS = (
    "Draft written",
    "Skeleton written",
    "Limitations written",
    "This is the full-length version",
)

# Bracketed citations in the markdown, and the bibliography key each one maps to.
PARENTHETICAL = {
    "Aryal, 2026": "aryal2026lap1",
    "Aryal, in preparation": "aryal2026lap2",
    "Atil et al., 2025": "atil2025nondeterminism",
    "Bjarnason et al., 2026": "bjarnason2026randomness",
    "Chen et al., 2026": "chen2026factuality",
    "Haase et al., 2026": "haase2026creative",
    "Heyman and Zylberberg, 2025": "heyman2025hallucinating",
    "K. Wang et al., 2026": "wangk2026margo",
    "Lau, 2026": "lau2026judge",
    "Lei et al., 2026": "lei2026inertia",
    "Li and Ng, 2025": "li2025hallucinate",
    "Madur, 2026": "madur2026moral",
    "Ning et al., 2026": "ning2026hrbench",
    "Potamitis et al., 2025": "potamitis2025reasonbench",
    "S. Wang et al., 2026b": "wangs2026pathlock",
    "Snell et al., 2025": "snell2025scaling",
    "Yuan et al., 2025": "yuan2025numerical",
    "Zhang et al., 2026": "zhang2026harness",
    "Zhao et al., 2026": "zhao2026tts",
}
TEXTUAL = {
    "S. Wang et al. [2026a]": "wangs2026hybrid",
    "Liu and Honavar [2026]": "liu2026leakage",
    "Sahu et al. [2026]": "sahu2026architects",
}

# Parenthetical citation command per target: biblatex (JAIR) or natbib (TMLR, NEJLT).
CITE = {"jair": "cite", "tmlr": "citep", "nejlt": "citep"}
# Targets that use BibTeX, so get a converted copy of the BibLaTeX list.
BIBTEX_TARGETS = ("tmlr", "nejlt")

# Text that identifies the author, and what the anonymous version says instead.
ANONYMISE = {
    "(<https://osf.io/nj2zp/>)": (
        "(link withheld for double-blind review; the frozen plan and its Deviations table are in the "
        "anonymised repository, <https://anonymous.4open.science/r/model-mode-grid-review/>)"
    ),
    "as tag `v1.0.0` of <https://github.com/roshanaryal1/reasoning-mode-grid>, archived on Zenodo "
    "(<https://doi.org/10.5281/zenodo.23674817>)": "at the anonymised repository <https://anonymous.4open.science/r/model-mode-grid-review/>",
    "are in tag `v1.0.0` of <https://github.com/roshanaryal1/reasoning-mode-grid>, archived at "
    "<https://doi.org/10.5281/zenodo.23674817>": "are at the anonymised repository <https://anonymous.4open.science/r/model-mode-grid-review/>",
    # Project codes, the harness name and upstream fingerprints lead to the author's
    # public repositories, so they are replaced in the review version too.
    "An open harness, `modegrid`, that": "An open harness that",
    "modegrid": "harness",
    ", for LA-P5": "",
    "LA-P1": "S1",
    "(`ba2acba8...0370e0`)": "([hash withheld for review])",
    "`d5e39e7`": "[commit withheld for review]",
}
# Nothing in the anonymous files may contain these (checked after every build).
FORBIDDEN = (
    "aryal",
    "roshan",
    "auckland",
    "otago",
    "osf.io/nj2zp",
    "modegrid",
    "la-p",
    "d5e39e7",
    "ba2acba8",
    "llm-architects",
    "zenodo.22245991",
    "23674817",
    "github.com/",
)
# Self-citations shown as anonymous in the review version, with neutral keys, because
# hyperref writes citation keys into the PDF as link targets.
ANONYMOUS_KEYS = {"aryal2026lap1": "anon2026a", "aryal2026lap2": "anon2026b"}

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


def _const(text: str) -> Callable[[re.Match[str]], str]:
    return lambda _m: text


def strip_notes(md: str) -> str:
    paras = re.split(r"\n\s*\n", md)
    kept = [p for p in paras if not p.lstrip().startswith(NOTE_STARTS)]
    md = "\n\n".join(kept)
    # The results draft opens with a table of source files for the author.
    return re.sub(r"Source files after Phase 4.*?(?=\n## )", "", md, flags=re.S)


def anonymise(md: str, used: set[str]) -> str:
    for text, repl in ANONYMISE.items():
        md, n = re.subn(_ws(text), _const(repl), md)
        if n:
            used.add(text)
    return md


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


def cite(md: str, parenthetical: str, used: set[str]) -> str:
    for text, key in TEXTUAL.items():
        md, n = re.subn(_ws(text), _const(f"\\citet{{{key}}}"), md)
        if n:
            used.add(text)
    for text, key in PARENTHETICAL.items():
        md, n = re.subn(r"\[" + _ws(text) + r"\]", _const(f"\\{parenthetical}{{{key}}}"), md)
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


LONGTABLE = re.compile(
    r"(?:\\textbf\{Table (?P<num>\d+)\.\}(?P<caption>.*?)\n\n)?"
    r"(?:\{\\def\\LTcaptype\{none\} % do not increment counter\n)?"
    r"\\begin\{longtable\}\[\]\{(?P<spec>@\{\}.*?@\{\})\}\n(?P<rows>.*?)\\end\{longtable\}(?:\n\})?",
    re.S,
)


def float_tables(tex: str, count: int = 0) -> tuple[str, int]:
    """Longtables as full-width table* floats, for two-column templates (NEJLT).

    longtable cannot run in two-column mode. The bold "Table N." paragraph before a table
    becomes its caption, placed below the table as NEJLT asks. Numbers are checked against
    LaTeX's own count so "Table N" in the text still points at the right table; ``count``
    is the number of captioned tables before this text, and the new total is returned.
    """

    def one(m: re.Match[str]) -> str:
        nonlocal count
        rows = m.group("rows")
        rows = re.sub(r"[ \t]*\\bottomrule\\noalign\{\}\n[ \t]*\\endlastfoot\n", "", rows)
        rows = re.sub(r"[ \t]*\\end(?:first)?head\n", "", rows)
        rows = rows.replace("\\noalign{}", "")
        if "\\endfoot" in rows or "\\endlastfoot" in rows:
            raise SystemExit("longtable footer layout not handled by float_tables")
        caption = ""
        if m.group("num"):
            count += 1
            if int(m.group("num")) != count:
                raise SystemExit(f"Table {m.group('num')} would be numbered {count} by LaTeX")
            caption = f"\\caption{{{m.group('caption').strip()}}}\\label{{tab:{count}}}\n"
        return (
            "\\begin{table*}[tp]\n\\centering\\footnotesize\n"
            f"\\begin{{tabular}}{{{m.group('spec')}}}\n{rows.rstrip()}\n\\bottomrule\n\\end{{tabular}}\n"
            f"{caption}\\end{{table*}}"
        )

    tex = LONGTABLE.sub(one, tex)
    if "longtable" in tex:
        raise SystemExit("a longtable was not converted")
    return tex, count


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


def build(names: list[str], appendix: bool, target: str, anonymous: bool, used: set[str]) -> str:
    parts = []
    tables = 0
    for name in names:
        md = strip_notes((PAPER / f"{name}.md").read_text(encoding="utf-8"))
        if anonymous:
            md = anonymise(md, used)
        md = cite(add_figure(fix_headings(md, appendix)), CITE[target], used)
        if anonymous:
            for key, neutral in ANONYMOUS_KEYS.items():
                md = md.replace(f"{{{key}}}", f"{{{neutral}}}")
        tex = to_latex(md)
        if target == "nejlt" and not appendix:  # the appendix is set in one column
            tex, tables = float_tables(tex, tables)
            tex = tex.replace("{figure}", "{figure*}")
        parts.append(tex)
    return "\n".join(parts)


def bibtex(bib: str, anonymous: bool) -> str:
    """The checked BibLaTeX list, rewritten for plain BibTeX (natbib with tmlr.bst)."""
    bib = re.sub(
        r"eprint = \{([^}]+)\},\n  eprinttype = \{arxiv\}",
        r"howpublished = {arXiv preprint arXiv:\1}",
        bib,
    )
    bib = bib.replace("doi = {10.5281/zenodo.22245991}", "howpublished = {Zenodo, doi:10.5281/zenodo.22245991}")
    if anonymous:
        for key, neutral in ANONYMOUS_KEYS.items():
            entry = (
                f"@misc{{{neutral},\n  author = {{Anonymous}},\n"
                "  title = {Withheld for double-blind review},\n  year = {2026}\n}"
            )
            bib, n = re.subn(r"@\w+\{" + key + r",.*?\n\}", _const(entry), bib, flags=re.S)
            if n != 1:
                raise SystemExit(f"self-citation {key} not found in {BIB}")
    if "eprinttype" in bib:
        raise SystemExit("an eprint entry was not converted for BibTeX")
    return bib


def write(target: str, anonymous: bool) -> list[Path]:
    out = PAPER / target
    suffix = "-anon" if anonymous else ""
    used: set[str] = set()
    body = build(BODY, False, target, anonymous, used)
    appendix = build(APPENDIX, True, target, anonymous, used)
    expected = set(TEXTUAL) | set(PARENTHETICAL) | (set(ANONYMISE) if anonymous else set())
    if missing := sorted(expected - used):
        raise SystemExit(f"in the map but not in the text: {missing}")
    header = "% Generated by paper/latex_build.py from paper/*.md. Do not edit by hand.\n\n"
    paths = [out / f"body{suffix}.tex", out / f"appendix{suffix}.tex"]
    paths[0].write_text(header + body, encoding="utf-8")
    paths[1].write_text(header + appendix, encoding="utf-8")
    if target in BIBTEX_TARGETS:
        if target == "tmlr" and not anonymous:  # the same text serves both versions; it names no one
            impact = strip_notes((PAPER / "broader-impact.md").read_text(encoding="utf-8"))
            impact = re.sub(r"^# .*\n", "", impact.lstrip())
            paths.append(out / "broader-impact.tex")
            paths[-1].write_text(header + to_latex(impact), encoding="utf-8")
        bib = out / f"references{suffix}.bib"
        bib.write_text(header + bibtex(BIB.read_text(encoding="utf-8"), anonymous), encoding="utf-8")
        paths.append(bib)
    if anonymous:
        shared = [out / "broader-impact.tex"] if target == "tmlr" else []
        for path in paths + shared:
            text = path.read_text(encoding="utf-8").lower()
            if leaks := [w for w in FORBIDDEN if w in text]:
                raise SystemExit(f"identifying text left in {path.name}: {leaks}")
    return paths


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in CITE:
        print(f"usage: python paper/latex_build.py {{{'|'.join(CITE)}}}")
        return 2
    target = argv[0]
    paths = [] if target == "nejlt" else write(target, anonymous=False)
    if target in BIBTEX_TARGETS:
        paths += write(target, anonymous=True)
    for p in paths:
        print(f"wrote {p.relative_to(PAPER.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
