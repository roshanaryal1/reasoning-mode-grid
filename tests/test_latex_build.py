"""float_tables in paper/latex_build.py: pandoc longtables as two-column-safe floats (NEJLT)."""

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "latex_build", Path(__file__).resolve().parents[1] / "paper" / "latex_build.py"
)
assert _SPEC and _SPEC.loader
latex_build = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(latex_build)

CAPTIONED = r"""\textbf{Table 1.} Models and mode settings.

\begin{longtable}[]{@{}ll@{}}
\toprule\noalign{}
Family & Model \\
\midrule\noalign{}
\endhead
\bottomrule\noalign{}
\endlastfoot
Claude & Sonnet \\
\end{longtable}"""

UNCAPTIONED = r"""{\def\LTcaptype{none} % do not increment counter
\begin{longtable}[]{@{}l@{}}
  \toprule\noalign{}
  A \\
  \midrule\noalign{}
  \endhead
    \bottomrule\noalign{}
  \endlastfoot
  x \\
\end{longtable}
}"""


def test_captioned_table_becomes_float_with_caption_below() -> None:
    tex, count = latex_build.float_tables(CAPTIONED)
    assert count == 1
    assert "longtable" not in tex and "endhead" not in tex and "noalign" not in tex
    assert tex.startswith("\\begin{table*}")
    assert tex.index("\\end{tabular}") < tex.index("\\caption{Models and mode settings.}")
    assert tex.index("Claude & Sonnet") < tex.index("\\bottomrule")


def test_uncaptioned_indented_table_keeps_count() -> None:
    tex, count = latex_build.float_tables(UNCAPTIONED, count=4)
    assert count == 4
    assert "\\caption" not in tex and "longtable" not in tex and "LTcaptype" not in tex


def test_numbering_mismatch_is_refused() -> None:
    with pytest.raises(SystemExit, match="would be numbered 3"):
        latex_build.float_tables(CAPTIONED, count=2)
