# Paper plan

## Target

Full research and dates in [venues.md](venues.md). In short:

- **arXiv** preprint when the analysis is done (January 2027).
- **ICLR 2027 workshop**, 4-page non-archival short paper (submit about 1 Feb 2027).
- **TMLR** for the archival version, submitted at the same time.
- Optional extended version for the **NeurIPS 2027 Evaluations & Datasets** track.

## Dependencies

| Item | Why it matters | State |
|---|---|---|
| LA-P1 citable (Cureus or preprint) | LA-P4 reuses its prompt and rubric | Under review, cite the preprint and Zenodo DOI 10.5281/zenodo.22245991 |
| v2 rubric anchors | Scoring instrument | Done in llm-architects |
| LA-P2 finding on stale raters | Justifies mandatory web verification | Cite as in preparation if not yet public |

## What LA-P5 needs from this paper

LA-P5 (architecture-from-spec benchmark) is gated on proof that the rubric is portable.
From this study, report:

1. Inter-rater alpha per dimension on a grid that LA-P1 never saw.
2. Whether rater rankings of the 12 cells agree (Kendall's tau between raters).
3. Which dimensions showed no variance at all, since a benchmark cannot use them.

## Timeline

| When | Work |
|---|---|
| Oct 2026 | Fill settings, API checks, freeze the pre-registration |
| Nov 2026 | 60 chat captures, blind scoring starts |
| Dec 2026 | Scoring and adjudication locked, unblind, analyse |
| Jan 2027 | Write, arXiv, submit to TMLR |
| about 1 Feb 2027 | Submit the 4-page version to an ICLR 2027 workshop |

## Salami test

Passes. LA-P1 had one family with three modes and no replicates, and scored modes only
as a side note. This paper has a new crossed design, new data, a new statistic and
pre-registered hypotheses. The LA-P1 DeepSeek captures appear only as motivating pilot data.
